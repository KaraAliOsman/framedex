"""Production orchestration: release sealed versions to workshop orders.

A work order is an ``orders`` row with ``order_type='WORKSHOP_OT'`` — the
substrate the schema already reserves for the shop floor (free-form status,
org-scoped access). Its ``payload_json`` carries the per-position cut list
straight from the sealed version snapshot, so nothing is re-entered between
the commercial and the workshop departments. Routing lives in
``production_steps``; every transition appends to ``production_step_events``
so the floor has a paperless trail."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import json
from uuid import UUID

from django.db import transaction
import segno

from dekopen_engine.cutting import optimize_cut, pieces_from_result
from dekopen_engine.models import EngineResult
from dekopen_engine.nesting import NestPiece, SheetRule, nest_rects
from documents.repository import DocumentaryError, documentary_backend, one, rows
from engine_api.cutting_repository import CuttingRepository
from production.confirmations import confirmation_summary
from production.dispatch_notes import issue_dispatch_note
from projects.service import project_row


_STEP_CODE_FOR_CENTER = {
    "CUT": "CUT",
    "ASSEMBLY": "ASSEMBLE",
    "GLAZING": "GLAZE",
    "QC": "QC",
    "PACK": "PACK",
}

_DEFAULT_CENTERS = [
    ("CUT_SAW", "Sierra de corte", "CUT", 10),
    ("ASSEMBLY_BENCH", "Banco de armado", "ASSEMBLY", 20),
    ("GLAZING_BENCH", "Banco de vidriado", "GLAZING", 30),
    ("QC_STATION", "Puesto de control", "QC", 40),
    ("PACK_STATION", "Puesto de embalaje", "PACK", 50),
]

_STEP_LABELS = {
    "CUT": "Corte de perfiles",
    "ASSEMBLE": "Armado y herrajes",
    "GLAZE": "Vidriado y paneles",
    "QC": "Control de calidad",
    "PACK": "Embalaje",
}

_EVENTS = {
    "START": "STEP_STARTED",
    "COMPLETE": "STEP_COMPLETED",
    "BLOCK": "STEP_BLOCKED",
    "UNBLOCK": "STEP_UNBLOCKED",
    "NOTE": "NOTE",
}

_TRANSITIONS = {
    "START": ("IN_PROGRESS", {"PENDING", "READY"}),
    "COMPLETE": ("DONE", {"IN_PROGRESS"}),
    "BLOCK": ("BLOCKED", {"PENDING", "READY", "IN_PROGRESS"}),
    "UNBLOCK": ("READY", {"BLOCKED"}),
    "NOTE": (None, {"PENDING", "READY", "IN_PROGRESS", "DONE", "BLOCKED"}),
}


def _ensure_work_centers(org_id: UUID) -> dict[str, dict[str, object]]:
    existing = rows(
        "SELECT id, code, kind FROM public.work_centers WHERE org_id = %s ORDER BY display_order",
        [str(org_id)],
    )
    if not existing:
        with transaction.atomic(), documentary_backend():
            for code, name, kind, order in _DEFAULT_CENTERS:
                rows(
                    """
                    INSERT INTO public.work_centers(org_id, code, name, kind, display_order)
                    VALUES (%s, %s, %s, %s, %s) ON CONFLICT (org_id, code) DO NOTHING
                    RETURNING id
                    """,
                    [str(org_id), code, name, kind, order],
                )
            existing = rows(
                "SELECT id, code, kind FROM public.work_centers WHERE org_id = %s ORDER BY display_order",
                [str(org_id)],
            )
    return {str(center["kind"]): center for center in existing}


def _routing(engine_result: dict[str, object]) -> list[str]:
    routing: list[str] = []
    if engine_result.get("profile_cuts") or engine_result.get("reinforcements"):
        routing.append("CUT")
    routing.append("ASSEMBLE")
    if engine_result.get("glasses") or engine_result.get("panels"):
        routing.append("GLAZE")
    routing += ["QC", "PACK"]
    return routing


def _work_order_payload(position: dict[str, object]) -> dict[str, object]:
    engine = position.get("engine_result") or {}
    return {
        "schema": "production_wo_v1",
        "position_id": str(position.get("position_id") or ""),
        "system_id": str(position.get("system_id") or ""),
        "quantity": position.get("quantity", 1),
        "materials": {
            key: engine.get(key) or []
            for key in ("profile_cuts", "reinforcements", "glasses", "panels", "hardware_items")
        },
        "routing": _routing(engine),
    }


def _public_step(step: dict[str, object]) -> dict[str, object]:
    return {
        "id": str(step["id"]),
        "sequence": step["sequence"],
        "code": step["code"],
        "label": step["label"],
        "status": step["status"],
        "work_center_id": str(step["work_center_id"]) if step.get("work_center_id") else None,
        "work_center_code": step.get("work_center_code"),
        "started_at": step["started_at"],
        "finished_at": step["finished_at"],
        "actor_id": str(step["actor_id"]) if step.get("actor_id") else None,
        "note": step.get("note"),
    }


def _public_order(order: dict[str, object], *, include_payload: bool = False) -> dict[str, object]:
    payload = order.get("payload_json")
    if isinstance(payload, str):
        payload = json.loads(payload)
    output = {
        "id": str(order["id"]),
        "order_code": order["order_code"],
        "order_type": str(order["order_type"]),
        "status": str(order["status"]),
        "position_id": (payload or {}).get("position_id"),
        "quantity": (payload or {}).get("quantity"),
        "steps_done": order.get("steps_done", 0),
        "steps_total": order.get("steps_total", 0),
        "created_at": order["created_at"],
    }
    if include_payload:
        output["payload"] = payload
        output["project_version_id"] = str(order["project_version_id"]) if order.get("project_version_id") else None
    return output


def release_production(*, org_id: UUID, version_id: UUID, actor_id: UUID) -> dict[str, object]:
    """Create one WORKSHOP_OT order per sealed position. Idempotent via the
    orders_workshop_position_uq index: a replay returns the existing orders."""
    with transaction.atomic(), documentary_backend():
        version = one(
            """
            SELECT id, project_id, revision_code, snapshot_json, production_allowed
            FROM public.project_versions WHERE id = %s AND org_id = %s
            """,
            [str(version_id), str(org_id)],
            "version_not_found",
        )
        if not version["production_allowed"]:
            raise DocumentaryError("version_not_releasable")
        snapshot = version["snapshot_json"]
        if isinstance(snapshot, str):
            snapshot = json.loads(snapshot)
        bom = snapshot.get("bom") or []
        project_code = str(
            (snapshot.get("project") or {}).get("code") or version["project_id"]
        )
        position_systems = {
            str(pos.get("id")): str(pos.get("system_id"))
            for pos in snapshot.get("positions") or []
            if pos.get("id") and pos.get("system_id")
        }
        for position in bom:
            position["system_id"] = position_systems.get(str(position.get("position_id") or ""))
        centers = _ensure_work_centers(org_id)
        created_ids: list[UUID] = []
        order_ids: list[UUID] = []
        for index, position in enumerate(bom):
            payload = _work_order_payload(position)
            order_code = f"OT-{project_code}-{version['revision_code']}-{index + 1:02d}"[:50]
            inserted = rows(
                """
                INSERT INTO public.orders(
                    org_id, project_id, order_type, order_code, status,
                    payload_json, project_version_id)
                VALUES (%s, %s, 'WORKSHOP_OT', %s, 'RELEASED', %s::jsonb, %s)
                ON CONFLICT (org_id, project_version_id, (payload_json->>'position_id'))
                WHERE order_type = 'WORKSHOP_OT'
                  AND project_version_id IS NOT NULL
                  AND payload_json ? 'position_id'
                  AND NOT (payload_json ? 'remake_of')
                DO NOTHING
                RETURNING id
                """,
                [
                    str(org_id),
                    str(version["project_id"]),
                    order_code,
                    json.dumps(payload),
                    str(version_id),
                ],
            )
            if inserted:
                order_id = inserted[0]["id"]
                created_ids.append(order_id)
            else:
                order_id = one(
                    """
                    SELECT id FROM public.orders
                    WHERE org_id = %s AND project_version_id = %s
                      AND order_type = 'WORKSHOP_OT'
                      AND payload_json->>'position_id' = %s
                      AND NOT (payload_json ? 'remake_of')
                    """,
                    [str(org_id), str(version_id), payload["position_id"]],
                    "work_order_not_found",
                )["id"]
            order_ids.append(order_id)
            if inserted:
                center_by_step = {
                    step_code: centers.get(center_kind)
                    for center_kind, step_code in _STEP_CODE_FOR_CENTER.items()
                }
                for seq, code in enumerate(payload["routing"], start=1):
                    center = center_by_step.get(code)
                    rows(
                        """
                        INSERT INTO public.production_steps(
                            org_id, order_id, sequence, work_center_id, code, label, status)
                        VALUES (%s, %s, %s, %s, %s, %s, 'READY')
                        RETURNING id
                        """,
                        [
                            str(org_id),
                            str(order_id),
                            seq,
                            str(center["id"]) if center else None,
                            code,
                            _STEP_LABELS[code],
                        ],
                    )
                rows(
                    """
                    INSERT INTO public.production_step_events(org_id, order_id, event, actor_id, payload)
                    VALUES (%s, %s, 'WO_RELEASED', %s, %s::jsonb)
                    RETURNING id
                    """,
                    [
                        str(org_id),
                        str(order_id),
                        str(actor_id),
                        json.dumps({"order_code": order_code, "position_id": payload["position_id"]}),
                    ],
                )
        orders = rows(
            """
            SELECT o.id, o.order_code, o.order_type::text, o.status::text, o.payload_json,
                   o.project_version_id, o.created_at,
                   COUNT(s.id) AS steps_total,
                   COUNT(s.id) FILTER (WHERE s.status = 'DONE') AS steps_done
            FROM public.orders o
            LEFT JOIN public.production_steps s ON s.order_id = o.id
            WHERE o.id = ANY(%s::uuid[])
            GROUP BY o.id ORDER BY o.order_code
            """,
            [[str(order_id) for order_id in order_ids]],
        )
        return {
            "version_id": str(version_id),
            "released": len(order_ids),
            "created": len(created_ids),
            "orders": [_public_order(order) for order in orders],
        }


def list_production_orders(*, org_id: UUID) -> dict[str, object]:
    orders = rows(
        """
        SELECT o.id, o.order_code, o.order_type::text, o.status::text, o.payload_json,
               o.project_version_id, o.created_at,
               COUNT(s.id) AS steps_total,
               COUNT(s.id) FILTER (WHERE s.status = 'DONE') AS steps_done
        FROM public.orders o
        LEFT JOIN public.production_steps s ON s.order_id = o.id
        WHERE o.org_id = %s AND o.order_type = 'WORKSHOP_OT'
        GROUP BY o.id ORDER BY o.created_at DESC
        """,
        [str(org_id)],
    )
    return {"orders": [_public_order(order) for order in orders]}


def confirm_installation(
    org_id: str, order_id: str, actor_id: str, note: str | None = None
) -> dict:
    """Mark a dispatched order installed — the physical install is done.

    Idempotent: replaying on an INSTALLED order returns the current state.
    """
    with transaction.atomic(), documentary_backend():
        order = one(
            "SELECT id, order_code, status, payload_json FROM public.orders "
            "WHERE id = %s AND org_id = %s FOR UPDATE",
            [str(order_id), str(org_id)],
            "work_order_not_found",
        )
        if order["status"] == "INSTALLED":
            return get_work_order(org_id=org_id, order_id=order_id)
        if order["status"] != "DISPATCHED":
            raise DocumentaryError("installation_requires_dispatched")
        delivery = rows(
            "SELECT status FROM public.deliveries WHERE order_id = %s AND org_id = %s",
            [str(order_id), str(org_id)],
        )
        if delivery and str(delivery[0]["status"]) != "DELIVERED":
            raise DocumentaryError("installation_requires_delivered")
        rows(
            "UPDATE public.orders SET status = 'INSTALLED', updated_at = %s "
            "WHERE id = %s AND org_id = %s RETURNING id",
            [datetime.now(timezone.utc), str(order_id), str(org_id)],
        )
        rows(
            """INSERT INTO public.production_step_events
                   (org_id, order_id, event, actor_id, payload)
                   VALUES (%s, %s, 'WO_INSTALLED', %s, %s) RETURNING id""",
            [
                str(org_id),
                str(order_id),
                str(actor_id),
                json.dumps(
                    {
                        "order_code": order["order_code"],
                        "note": (note or "").strip() or None,
                    }
                ),
            ],
        )
    return get_work_order(org_id=org_id, order_id=order_id)


def get_work_order(*, org_id: UUID, order_id: UUID) -> dict[str, object]:
    order = one(
        """
        SELECT o.id, o.order_code, o.order_type::text, o.status::text, o.payload_json,
               o.project_version_id, o.created_at,
               COUNT(s.id) AS steps_total,
               COUNT(s.id) FILTER (WHERE s.status = 'DONE') AS steps_done
        FROM public.orders o
        LEFT JOIN public.production_steps s ON s.order_id = o.id
        WHERE o.id = %s AND o.org_id = %s AND o.order_type = 'WORKSHOP_OT'
        GROUP BY o.id
        """,
        [str(order_id), str(org_id)],
        "work_order_not_found",
    )
    steps = rows(
        """
        SELECT s.id, s.sequence, s.code, s.label, s.status, s.work_center_id,
               w.code AS work_center_code, s.started_at, s.finished_at, s.actor_id, s.note
        FROM public.production_steps s
        LEFT JOIN public.work_centers w ON w.id = s.work_center_id
        WHERE s.order_id = %s ORDER BY s.sequence
        """,
        [str(order_id)],
    )
    events = rows(
        """
        SELECT id, step_id, event, actor_id, payload, created_at
        FROM public.production_step_events
        WHERE order_id = %s AND org_id = %s
        ORDER BY created_at
        """,
        [str(order_id), str(org_id)],
    )
    dispatch_note = rows(
        "SELECT note_code FROM public.dispatch_notes "
        "WHERE org_id=%s AND work_order_id=%s",
        [str(org_id), str(order_id)],
    )
    output = _public_order(order, include_payload=True)
    output["dispatch_note_code"] = (
        dispatch_note[0]["note_code"] if dispatch_note else None
    )
    output["steps"] = [_public_step(step) for step in steps]
    output["events"] = [
        {
            "id": str(event["id"]),
            "step_id": str(event["step_id"]) if event["step_id"] else None,
            "event": event["event"],
            "actor_id": str(event["actor_id"]) if event["actor_id"] else None,
            "payload": event["payload"],
            "created_at": event["created_at"],
        }
        for event in events
    ]
    return output


def _refresh_order_status(*, org_id: UUID, order_id: UUID, actor_id: UUID) -> str:
    previous = one(
        """
        SELECT status::text AS status FROM public.orders
        WHERE id = %s AND org_id = %s
        """,
        [str(order_id), str(org_id)],
        "work_order_not_found",
    )
    totals = one(
        """
        SELECT COUNT(*) AS total,
               COUNT(*) FILTER (WHERE status = 'DONE') AS done,
               COUNT(*) FILTER (WHERE status = 'BLOCKED') AS blocked,
               COUNT(*) FILTER (WHERE status = 'IN_PROGRESS') AS in_progress
        FROM public.production_steps WHERE order_id = %s AND org_id = %s
        """,
        [str(order_id), str(org_id)],
        "production_steps_missing",
    )
    if totals["total"] == 0:
        new_status = "RELEASED"
    elif totals["done"] == totals["total"]:
        new_status = "COMPLETED"
    elif totals["blocked"] > 0:
        new_status = "HOLD"
    elif totals["done"] > 0 or totals["in_progress"] > 0:
        new_status = "IN_PROGRESS"
    else:
        new_status = "RELEASED"
    updated = one(
        """
        UPDATE public.orders SET status = %s::order_status, updated_at = %s
        WHERE id = %s AND org_id = %s AND order_type = 'WORKSHOP_OT'
        RETURNING status::text
        """,
        [new_status, datetime.now(timezone.utc), str(order_id), str(org_id)],
        "work_order_not_found",
    )
    if new_status == "COMPLETED":
        rows(
            """
            INSERT INTO public.production_step_events(org_id, order_id, event, actor_id)
            SELECT %s, %s, 'WO_COMPLETED', %s
            WHERE NOT EXISTS (
                SELECT 1 FROM public.production_step_events
                WHERE order_id = %s AND event = 'WO_COMPLETED')
            RETURNING id
            """,
            [str(org_id), str(order_id), str(actor_id), str(order_id)],
        )
    elif new_status == "HOLD" and str(previous["status"]) != "HOLD":
        rows(
            """
            INSERT INTO public.production_step_events(org_id, order_id, event, actor_id)
            VALUES (%s, %s, 'WO_HOLD', %s)
            RETURNING id
            """,
            [str(org_id), str(order_id), str(actor_id)],
        )
    return str(updated["status"])


def transition_step(
    *,
    org_id: UUID,
    step_id: UUID,
    action: str,
    actor_id: UUID,
    note: str | None,
    qc_result: str | None = None,
) -> dict[str, object]:
    if action not in _TRANSITIONS:
        raise DocumentaryError("step_action_unknown")
    if action == "NOTE" and not (note or "").strip():
        raise DocumentaryError("step_note_required")
    with transaction.atomic(), documentary_backend():
        step_ref = one(
            """
            SELECT order_id FROM public.production_steps
            WHERE id = %s AND org_id = %s
            """,
            [str(step_id), str(org_id)],
            "production_step_not_found",
        )
        # Lock the parent order before any step mutation so all transitions on
        # this order serialize — the status aggregate then sees prior commits.
        order = one(
            """
            SELECT id, status::text FROM public.orders
            WHERE id = %s AND org_id = %s AND order_type = 'WORKSHOP_OT'
            FOR UPDATE
            """,
            [str(step_ref["order_id"]), str(org_id)],
            "work_order_not_found",
        )
        step = one(
            """
            SELECT s.id, s.order_id, s.status, s.sequence, s.code, s.label,
                   s.work_center_id, s.started_at, s.finished_at, s.actor_id, s.note,
                   w.code AS work_center_code
            FROM public.production_steps s
            LEFT JOIN public.work_centers w ON w.id = s.work_center_id
            WHERE s.id = %s AND s.org_id = %s FOR UPDATE OF s
            """,
            [str(step_id), str(org_id)],
            "production_step_not_found",
        )
        if str(order["status"]) == "INSTALLED":
            raise DocumentaryError("work_order_installed")
        if str(order["status"]) == "DISPATCHED":
            raise DocumentaryError("work_order_dispatched")
        if str(order["status"]) == "COMPLETED":
            raise DocumentaryError("work_order_completed")
        if qc_result is not None and not (
            action == "COMPLETE" and str(step["code"]) == "QC"
        ):
            raise DocumentaryError("step_transition_invalid")
        new_status, allowed = _TRANSITIONS[action]
        if action == "COMPLETE" and qc_result == "FAIL":
            new_status = "BLOCKED"
        if str(step["status"]) not in allowed:
            raise DocumentaryError("step_transition_invalid")
        event_name = "QC_FAILED" if (
            action == "COMPLETE" and qc_result == "FAIL"
        ) else _EVENTS[action]
        now = datetime.now(timezone.utc)
        if new_status is not None:
            updates = {
                "status": new_status,
                "updated_at": now,
                "note": note.strip() if note is not None else step.get("note"),
            }
            if new_status == "IN_PROGRESS":
                updates["started_at"] = step.get("started_at") or now
                updates["actor_id"] = actor_id
            elif new_status == "DONE":
                updates["finished_at"] = now
                updates["actor_id"] = actor_id
            elif new_status == "BLOCKED":
                updates["actor_id"] = actor_id
            rows(
                """
                UPDATE public.production_steps
                SET status = %(status)s, updated_at = %(updated_at)s, note = %(note)s,
                    started_at = COALESCE(%(started_at)s, started_at),
                    finished_at = COALESCE(%(finished_at)s, finished_at),
                    actor_id = COALESCE(%(actor_id)s, actor_id)
                WHERE id = %(id)s
                RETURNING id
                """,
                {
                    "status": updates["status"],
                    "updated_at": updates["updated_at"],
                    "note": updates["note"],
                    "started_at": updates.get("started_at"),
                    "finished_at": updates.get("finished_at"),
                    "actor_id": updates.get("actor_id"),
                    "id": str(step_id),
                },
            )
        elif note is not None:
            rows(
                "UPDATE public.production_steps SET note = %s, updated_at = %s WHERE id = %s RETURNING id",
                [note, now, str(step_id)],
            )
        rows(
            """
            INSERT INTO public.production_step_events(org_id, order_id, step_id, event, actor_id, payload)
            VALUES (%s, %s, %s, %s, %s, %s::jsonb)
            RETURNING id
            """,
            [
                str(org_id),
                str(step["order_id"]),
                str(step_id),
                event_name,
                str(actor_id),
                json.dumps({
                    **({"note": note.strip()} if note else {}),
                    **({"qc_result": qc_result} if qc_result else {}),
                }),
            ],
        )
        order_status = _refresh_order_status(
            org_id=org_id, order_id=step["order_id"], actor_id=actor_id
        )
        fresh = one(
            """
            SELECT s.id, s.sequence, s.code, s.label, s.status, s.work_center_id,
                   w.code AS work_center_code, s.started_at, s.finished_at, s.actor_id, s.note
            FROM public.production_steps s
            LEFT JOIN public.work_centers w ON w.id = s.work_center_id
            WHERE s.id = %s
            """,
            [str(step_id)],
        )
        return {"step": _public_step(fresh), "order_status": order_status}


def create_remake(
    *, org_id: UUID, order_id: UUID, actor_id: UUID, note: str | None = None
) -> dict[str, object]:
    """Remake work order for a unit that failed QC: copies the sealed material
    projection and routing from a HOLD order into a new ``-RM-`` order. The
    unique release index excludes remakes (``remake_of`` in payload)."""
    with transaction.atomic(), documentary_backend():
        source = one(
            """
            SELECT id, order_code, status::text, payload_json, project_id,
                   project_version_id
            FROM public.orders
            WHERE id = %s AND org_id = %s AND order_type = 'WORKSHOP_OT'
            FOR UPDATE
            """,
            [str(order_id), str(org_id)],
            "work_order_not_found",
        )
        if str(source["status"]) != "HOLD":
            raise DocumentaryError("remake_requires_hold")
        payload = _decoded(source["payload_json"])
        payload.pop("optimization", None)  # stale plan — re-optimize the remake
        payload.pop("cnc_export", None)
        payload.pop("packing", None)  # labels carry the source order code
        payload["remake_of"] = str(source["id"])
        prior = one(
            """
            SELECT COUNT(*) AS n FROM public.orders
            WHERE org_id = %s AND payload_json->>'remake_of' = %s
            """,
            [str(org_id), str(source["id"])],
            "remake_count_unknown",
        )
        # Truncate the source portion, not the suffix — the -RM-nn counter is
        # what distinguishes remakes under the org-unique order_code. When the
        # source fills the 50-char bound, embed a stable id fragment so two
        # long sources sharing the retained prefix still get distinct codes.
        suffix = f"-RM-{int(prior['n']) + 1:02d}"
        source_code = str(source["order_code"])
        if len(source_code) + len(suffix) <= 50:
            order_code = f"{source_code}{suffix}"
        else:
            marker = str(source["id"]).replace("-", "").upper()
            order_code = f"{source_code[: 50 - len(suffix) - 33]}-{marker}{suffix}"
        remake = one(
            """
            INSERT INTO public.orders(
                org_id, project_id, order_type, order_code, status,
                payload_json, project_version_id)
            VALUES (%s, %s, 'WORKSHOP_OT', %s, 'RELEASED', %s::jsonb, %s)
            RETURNING id, order_code
            """,
            [
                str(org_id),
                str(source["project_id"]),
                order_code,
                json.dumps(payload),
                str(source["project_version_id"]) if source["project_version_id"] else None,
            ],
            "remake_not_created",
        )
        rows(
            """
            INSERT INTO public.production_steps(
                org_id, order_id, sequence, work_center_id, code, label)
            SELECT %s, %s, sequence, work_center_id, code, label
            FROM public.production_steps
            WHERE order_id = %s AND org_id = %s ORDER BY sequence
            RETURNING id
            """,
            [str(org_id), str(remake["id"]), str(source["id"]), str(org_id)],
        )
        rows(
            """
            INSERT INTO public.production_step_events(
                org_id, order_id, event, actor_id, payload)
            VALUES (%s, %s, 'WO_REMADE', %s, %s::jsonb)
            RETURNING id
            """,
            [
                str(org_id),
                str(remake["id"]),
                str(actor_id),
                json.dumps({
                    "remake_of": str(source["id"]),
                    "source_order_code": source["order_code"],
                    "note": (note or "").strip() or None,
                }),
            ],
        )
        return get_work_order(org_id=org_id, order_id=UUID(str(remake["id"])))


def list_work_centers(*, org_id: UUID) -> dict[str, object]:
    _ensure_work_centers(org_id)
    return {
        "centers": rows(
            """
            SELECT id, code, name, kind, display_order, active
            FROM public.work_centers WHERE org_id = %s ORDER BY display_order
            """,
            [str(org_id)],
        )
    }


def _reinforcement_angle_map(
    version_snapshot: dict[str, object], position_id: str | None
) -> dict[tuple[str, str, str, str | None, str | None], tuple[str, str] | None]:
    """Authoritative reinforcement end angles from the sealed manufacturing
    facts: fact -> parent member gives (role, bay, leaf); the key joins on
    (workshop_sku, cut_length_mm, role, bay_id, leaf_id). A key reached by
    conflicting facts is marked ambiguous (None) so the export refuses to
    invent an angle."""
    angle_map: dict[
        tuple[str, str, str, str | None, str | None], tuple[str, str] | None
    ] = {}
    for unit in version_snapshot.get("manufacturing") or []:
        if position_id and str(unit.get("position_id")) != position_id:
            continue
        members = {
            str(member.get("member_id")): member
            for member in unit.get("members") or []
        }
        for reinforcement in unit.get("reinforcements") or []:
            parent = members.get(str(reinforcement.get("parent_member_id")))
            if parent is None:
                continue
            key = (
                str(reinforcement.get("workshop_sku")),
                str(reinforcement.get("cut_length_mm")),
                str((parent.get("identity") or {}).get("role")),
                parent.get("bay_id"),
                parent.get("leaf_id"),
            )
            angles = (
                str(reinforcement.get("angle_left")),
                str(reinforcement.get("angle_right")),
            )
            if key in angle_map and angle_map[key] != angles:
                angle_map[key] = None  # ambiguous — must not be guessed
            else:
                angle_map[key] = angles
    return angle_map


def _csv_cell(value: object) -> str:
    text = "" if value is None else str(value)
    escaped = text.replace('"', '""')
    return f'"{escaped}"' if any(c in text for c in '",\n') else text


def _cnc_bars_csv(optimization: dict[str, object]) -> str:
    """DEKOPEN-CNC-BARS-V1: one row per cut placement, ordered by bar then
    position inside the bar — deterministic output for the saw operator."""
    rows_out = [
        "bar_index,stock_sku,stock_length_mm,sequence_in_bar,piece_id,"
        "cut_length_mm,angle_left_deg,angle_right_deg,"
        "unit_index,bay_id,leaf_id,source_position_id"
    ]
    bars = (optimization.get("bars") or {}).get("workshop_cut_plan") or []
    for bar in sorted(bars, key=lambda b: int(b.get("bar_index") or 0)):
        for cut in sorted(
            bar.get("cuts") or [],
            key=lambda c: int(c.get("sequence") or 0),
        ):
            if (
                str(cut.get("source_kind") or "") == "REINFORCEMENT"
                and (cut.get("angle_left") is None or cut.get("angle_right") is None)
            ):
                raise DocumentaryError("cnc_incomplete_cut_angles")
            rows_out.append(",".join(_csv_cell(v) for v in (
                bar.get("bar_index"),
                bar.get("commercial_sku"),
                bar.get("stock_length_mm"),
                cut.get("sequence"),
                cut.get("piece_id"),
                cut.get("length_mm"),
                cut.get("angle_left"),
                cut.get("angle_right"),
                cut.get("unit_index"),
                cut.get("bay_id"),
                cut.get("leaf_id"),
                cut.get("source_position_id"),
            )))
    return "\n".join(rows_out) + "\n"


def _cnc_sheets_csv(optimization: dict[str, object]) -> str:
    """DEKOPEN-CNC-SHEETS-V1: one row per nested placement, ordered by sheet
    then Y then X — deterministic input for a panel saw / glass table."""
    rows_out = [
        "sheet_index,purchasing_sku,sheet_width_mm,sheet_height_mm,"
        "x_mm,y_mm,width_mm,height_mm,rotated,piece_id,unit_index,bay_id,leaf_id"
    ]
    for sheet in sorted(
        optimization.get("sheets") or [], key=lambda s: int(s.get("sheet_index") or 0)
    ):
        for placement in sorted(
            sheet.get("placements") or [],
            key=lambda p: (
                Decimal(str(p.get("y_mm") or 0)), Decimal(str(p.get("x_mm") or 0))
            ),
        ):
            rows_out.append(",".join(_csv_cell(v) for v in (
                sheet.get("sheet_index"),
                sheet.get("purchasing_sku"),
                sheet.get("sheet_width_mm"),
                sheet.get("sheet_height_mm"),
                placement.get("x_mm"),
                placement.get("y_mm"),
                placement.get("width_mm"),
                placement.get("height_mm"),
                placement.get("rotated"),
                placement.get("piece_id"),
                placement.get("unit_index"),
                placement.get("bay_id"),
                placement.get("leaf_id"),
            )))
    return "\n".join(rows_out) + "\n"


def _optimization_fingerprint(optimization: dict[str, object]) -> str:
    canonical = json.dumps(optimization, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def export_cnc_files(
    *, org_id: UUID, order_id: UUID, actor_id: UUID
) -> dict[str, object]:
    """Machine handoff: renders the stored optimization plan into deterministic
    CSV cut files (bars + sheets), stores them on the order, and records a
    ``WO_CNC_EXPORTED`` event. Requires a prior optimization run."""
    with transaction.atomic(), documentary_backend():
        order = one(
            """
            SELECT id, order_code, status::text, payload_json FROM public.orders
            WHERE id = %s AND org_id = %s AND order_type = 'WORKSHOP_OT'
            FOR UPDATE
            """,
            [str(order_id), str(org_id)],
            "work_order_not_found",
        )
        if str(order["status"]) == "INSTALLED":
            raise DocumentaryError("work_order_installed")
        if str(order["status"]) == "DISPATCHED":
            raise DocumentaryError("work_order_dispatched")
        payload = _decoded(order["payload_json"])
        optimization = payload.get("optimization")
        if not isinstance(optimization, dict) or not optimization.get("bars"):
            raise DocumentaryError("cnc_requires_optimization")
        files = {"bars.csv": _cnc_bars_csv(optimization)}
        if optimization.get("sheets"):
            files["sheets.csv"] = _cnc_sheets_csv(optimization)
        export = {
            "schema": "work_order_cnc_export_v2",
            "optimization_fingerprint": _optimization_fingerprint(optimization),
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "actor_id": str(actor_id),
            "files": files,
        }
        new_payload = {**payload, "cnc_export": export}
        rows(
            """
            UPDATE public.orders SET payload_json = %s::jsonb, updated_at = %s
            WHERE id = %s AND org_id = %s
            RETURNING id
            """,
            [json.dumps(new_payload), datetime.now(timezone.utc),
             str(order_id), str(org_id)],
        )
        rows(
            """
            INSERT INTO public.production_step_events(org_id, order_id, event, actor_id, payload)
            VALUES (%s, %s, 'WO_CNC_EXPORTED', %s, %s::jsonb)
            RETURNING id
            """,
            [
                str(org_id),
                str(order_id),
                str(actor_id),
                json.dumps({
                    "order_code": order["order_code"],
                    "files": sorted(files),
                }),
            ],
        )
        return {
            "order_id": str(order_id),
            "order_code": order["order_code"],
            "exported_at": export["exported_at"],
            "files": files,
        }


def cnc_file_content(
    *, org_id: UUID, order_id: UUID, filename: str
) -> tuple[str, str] | None:
    order = one(
        """
        SELECT order_code, payload_json FROM public.orders
        WHERE id = %s AND org_id = %s AND order_type = 'WORKSHOP_OT'
        """,
        [str(order_id), str(org_id)],
        "work_order_not_found",
    )
    payload = _decoded(order["payload_json"])
    export = payload.get("cnc_export") or {}
    optimization = payload.get("optimization")
    if (
        export.get("optimization_fingerprint")
        and _optimization_fingerprint(optimization if isinstance(optimization, dict) else {})
        != export["optimization_fingerprint"]
    ):
        return None
    files = export.get("files") or {}
    content = files.get(filename)
    if content is None:
        return None
    return f"{order['order_code']}-{filename}", content


def generate_packing_manifest(
    *, org_id: UUID, order_id: UUID, actor_id: UUID
) -> dict[str, object]:
    """Per-unit packing manifest: deterministic label codes
    ``<order_code>-U<nn>`` plus piece counts per material kind, so each
    finished unit gets a scannable label and the pack step has a checklist."""
    with transaction.atomic(), documentary_backend():
        order = one(
            """
            SELECT id, order_code, status::text, payload_json FROM public.orders
            WHERE id = %s AND org_id = %s AND order_type = 'WORKSHOP_OT'
            FOR UPDATE
            """,
            [str(order_id), str(org_id)],
            "work_order_not_found",
        )
        if str(order["status"]) == "INSTALLED":
            raise DocumentaryError("work_order_installed")
        if str(order["status"]) == "DISPATCHED":
            raise DocumentaryError("work_order_dispatched")
        payload = _decoded(order["payload_json"])
        materials = payload.get("materials") or {}
        quantity = int(payload.get("quantity") or 1)
        kind_counts = {
            "profiles": sum(
                int(item.get("qty") or 1)
                for item in materials.get("profile_cuts") or []
            ),
            "reinforcements": sum(
                int(item.get("qty") or 1)
                for item in materials.get("reinforcements") or []
            ),
            "glasses": len(materials.get("glasses") or []),
            "panels": len(materials.get("panels") or []),
            "hardware": sum(
                int(item.get("qty") or 1)
                for item in materials.get("hardware_items") or []
            ),
        }
        units = [
            {
                "unit_index": unit,
                "label_code": f"{str(order['order_code'])[: 50 - len(f'-U{unit:02d}')]}-U{unit:02d}",
                "position_id": payload.get("position_id"),
                **kind_counts,
            }
            for unit in range(1, quantity + 1)
        ]
        packing = {
            "schema": "work_order_packing_v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "actor_id": str(actor_id),
            "units": units,
        }
        new_payload = {**payload, "packing": packing}
        rows(
            """
            UPDATE public.orders SET payload_json = %s::jsonb, updated_at = %s
            WHERE id = %s AND org_id = %s
            RETURNING id
            """,
            [json.dumps(new_payload), datetime.now(timezone.utc),
             str(order_id), str(org_id)],
        )
        rows(
            """
            INSERT INTO public.production_step_events(org_id, order_id, event, actor_id, payload)
            VALUES (%s, %s, 'WO_PACKED', %s, %s::jsonb)
            RETURNING id
            """,
            [
                str(org_id),
                str(order_id),
                str(actor_id),
                json.dumps({
                    "order_code": order["order_code"],
                    "units": len(units),
                }),
            ],
        )
        return {
            "order_id": str(order_id),
            "order_code": order["order_code"],
            "packing": packing,
        }


def packing_labels(*, org_id: UUID, order_id: UUID) -> dict[str, object]:
    """Printable unit labels: the stored manifest plus a QR per unit.

    The QR encodes ``DEKOPEN|<order_code>|<label_code>|<piece_count>`` so a
    scanned label identifies the order, the unit, and its checklist even
    without a terminal at hand. Rendered on read — the manifest is already
    sealed, so labels never drift from it."""
    with transaction.atomic(), documentary_backend():
        order = one(
            """
            SELECT id, order_code, status::text, payload_json FROM public.orders
            WHERE id = %s AND org_id = %s AND order_type = 'WORKSHOP_OT'
            """,
            [str(order_id), str(org_id)],
            "work_order_not_found",
        )
        packing = (_decoded(order["payload_json"]) or {}).get("packing")
        if not packing or not packing.get("units"):
            raise DocumentaryError("packing_required")
        labels = []
        for unit in packing["units"]:
            pieces = (
                int(unit.get("profiles") or 0)
                + int(unit.get("reinforcements") or 0)
                + int(unit.get("glasses") or 0)
                + int(unit.get("panels") or 0)
                + int(unit.get("hardware") or 0)
            )
            qr_payload = (
                f"DEKOPEN|{order['order_code']}|{unit['label_code']}|{pieces}"
            )
            labels.append(
                {
                    "unit_index": int(unit["unit_index"]),
                    "label_code": unit["label_code"],
                    "pieces": pieces,
                    "profiles": int(unit.get("profiles") or 0),
                    "reinforcements": int(unit.get("reinforcements") or 0),
                    "glasses": int(unit.get("glasses") or 0),
                    "panels": int(unit.get("panels") or 0),
                    "hardware": int(unit.get("hardware") or 0),
                    "qr_payload": qr_payload,
                    "qr_svg": segno.make(qr_payload, error="m").svg_inline(
                        border=2, scale=6
                    ),
                }
            )
        return {
            "order_id": str(order_id),
            "order_code": order["order_code"],
            "status": str(order["status"]),
            "labels": labels,
        }


def dispatch_work_order(
    *, org_id: UUID, order_id: UUID, actor_id: UUID, note: str | None = None
) -> dict[str, object]:
    """Ship the finished order: requires COMPLETED (all routing done); sets
    DISPATCHED and records WO_DISPATCHED. Idempotent — re-dispatching an
    already dispatched order returns its current state."""
    with transaction.atomic(), documentary_backend():
        order = one(
            """
            SELECT id, order_code, status::text, payload_json, project_id
            FROM public.orders
            WHERE id = %s AND org_id = %s AND order_type = 'WORKSHOP_OT'
            FOR UPDATE
            """,
            [str(order_id), str(org_id)],
            "work_order_not_found",
        )
        if str(order["status"]) == "DISPATCHED":
            return get_work_order(org_id=org_id, order_id=order_id)
        if str(order["status"]) != "COMPLETED":
            raise DocumentaryError("dispatch_requires_completed")
        rows(
            """
            UPDATE public.orders SET status = 'DISPATCHED', updated_at = %s
            WHERE id = %s AND org_id = %s
            RETURNING id
            """,
            [datetime.now(timezone.utc), str(order_id), str(org_id)],
        )
        note_row = issue_dispatch_note(
            org_id=org_id,
            order=order,
            project=project_row(org_id, order["project_id"]),
            actor_id=actor_id,
            note=(note or "").strip() or None,
        )
        rows(
            """
            INSERT INTO public.production_step_events(org_id, order_id, event, actor_id, payload)
            VALUES (%s, %s, 'WO_DISPATCHED', %s, %s::jsonb)
            RETURNING id
            """,
            [
                str(org_id),
                str(order_id),
                str(actor_id),
                json.dumps({
                    "order_code": order["order_code"],
                    "note": (note or "").strip() or None,
                    "dispatch_note": note_row["note_code"],
                }),
            ],
        )
        return get_work_order(org_id=org_id, order_id=order_id)


def create_work_center(
    *, org_id: UUID, code: str, name: str, kind: str, display_order: int
) -> dict[str, object]:
    if kind not in _STEP_CODE_FOR_CENTER:
        raise DocumentaryError("work_center_kind_unknown")
    with transaction.atomic(), documentary_backend():
        center = one(
            """
            INSERT INTO public.work_centers(org_id, code, name, kind, display_order)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (org_id, code) DO UPDATE SET
                name = EXCLUDED.name, kind = EXCLUDED.kind,
                display_order = EXCLUDED.display_order, active = TRUE
            RETURNING id, code, name, kind, display_order, active, (xmax = 0) AS created
            """,
            [str(org_id), code, name, kind, display_order],
        )
    created = bool(center.pop("created"))
    return center, created


def _sheet_rules(org_id: UUID) -> dict[str, list[SheetRule]]:
    """Sheet stock declared by the shop: ``inventory_items.attributes`` carrying
    ``sheet_width_mm``/``sheet_height_mm``. Panels match a rule by sku; glass by
    ``sheet_thickness_mm``. No inferred compatibility — undeclared groups fall
    through to ``unnested`` in the plan."""
    items = rows(
        """
        SELECT sku, name, attributes FROM public.inventory_items
        WHERE org_id = %s
          AND attributes ? 'sheet_width_mm'
          AND attributes ? 'sheet_height_mm'
        """,
        [str(org_id)],
    )
    by_sku: dict[str, SheetRule] = {}
    by_thickness: dict[str, SheetRule] = {}
    for item in items:
        attributes = item.get("attributes") or {}
        if isinstance(attributes, str):
            attributes = json.loads(attributes)
        try:
            rule = SheetRule(
                workshop_sku=str(item["sku"]),
                purchasing_sku=str(attributes.get("purchasing_sku") or item["sku"]),
                manufacturer_name=attributes.get("manufacturer_name"),
                supplier_name=attributes.get("supplier_name") or item.get("name"),
                sheet_width_mm=Decimal(str(attributes["sheet_width_mm"])),
                sheet_height_mm=Decimal(str(attributes["sheet_height_mm"])),
                edge_trim_mm=Decimal(str(attributes.get("sheet_edge_trim_mm") or 0)),
            )
        except Exception:
            continue
        by_sku.setdefault(rule.workshop_sku, []).append(rule)
        thickness = attributes.get("sheet_thickness_mm")
        if thickness is not None:
            by_thickness.setdefault(str(Decimal(str(thickness))), []).append(rule)
    # Deterministic authority order: smallest physical sheet first, sku as the
    # tiebreak, so variants never depend on database row order.
    for group in (by_sku, by_thickness):
        for candidates in group.values():
            candidates.sort(
                key=lambda r: (r.sheet_width_mm * r.sheet_height_mm, r.workshop_sku)
            )
    return {"by_sku": by_sku, "by_thickness": by_thickness}


def _pick_sheet_rule(
    candidates: list[SheetRule], width_mm: Decimal, height_mm: Decimal
) -> SheetRule | None:
    """Smallest declared sheet that holds the piece (either orientation, since
    sheet pieces allow rotation); falls back to the largest sheet so oversized
    pieces still land honestly under ``unnested``."""
    if not candidates:
        return None
    for rule in candidates:
        usable_w = rule.sheet_width_mm - rule.edge_trim_mm * 2
        usable_h = rule.sheet_height_mm - rule.edge_trim_mm * 2
        if (width_mm <= usable_w and height_mm <= usable_h) or (
            height_mm <= usable_w and width_mm <= usable_h
        ):
            return rule
    return candidates[-1]


def _decoded(payload: object) -> dict[str, object]:
    if isinstance(payload, str):
        payload = json.loads(payload)
    return payload if isinstance(payload, dict) else {}


def optimize_work_order(
    *,
    org_id: UUID,
    order_id: UUID,
    actor_id: UUID,
    color: str,
    cutting_profile_code: str | None = None,
) -> dict[str, object]:
    """Bar cutting plan (1D best-fit) + sheet nesting (2D guillotine) for one
    work order. Replaces any previous plan in ``payload_json.optimization`` and
    appends a ``WO_OPTIMIZED`` event. Sealed materials are never mutated."""
    color = (color or "").strip()
    if not color:
        raise DocumentaryError("optimize_color_required")
    with transaction.atomic(), documentary_backend():
        order = one(
            """
            SELECT id, order_code, status::text, payload_json FROM public.orders
            WHERE id = %s AND org_id = %s AND order_type = 'WORKSHOP_OT'
            FOR UPDATE
            """,
            [str(order_id), str(org_id)],
            "work_order_not_found",
        )
        if str(order["status"]) == "INSTALLED":
            raise DocumentaryError("work_order_installed")
        if str(order["status"]) == "DISPATCHED":
            raise DocumentaryError("work_order_dispatched")
        if str(order["status"]) == "COMPLETED":
            raise DocumentaryError("work_order_completed")
        payload = _decoded(order["payload_json"])
        materials = payload.get("materials") or {}
        position_id = payload.get("position_id")
        system_id = payload.get("system_id")
        # The frozen version snapshot is the only honest source for both the
        # system mapping and the sealed manufacturing facts (reinforcement cut
        # angles live there, not in the BOM rows).
        version_row = one(
            """
            SELECT pv.snapshot_json FROM public.project_versions pv
            JOIN public.orders o ON o.project_version_id = pv.id
            WHERE o.id = %s AND o.org_id = %s
            """,
            [str(order_id), str(org_id)],
            "work_order_missing_system",
        )
        version_snapshot = _decoded(version_row["snapshot_json"])
        if not system_id:
            # Old orders lack system_id: recover the frozen mapping from the
            # referenced version's immutable snapshot, never the live position.
            for pos in version_snapshot.get("positions") or []:
                if str(pos.get("id")) == str(position_id) and pos.get("system_id"):
                    system_id = str(pos["system_id"])
                    break
            if not system_id:
                raise DocumentaryError("work_order_missing_system")
        quantity = int(payload.get("quantity") or 1)
        # payload was produced by model_dump(mode="json") — Decimals are strings,
        # so validate non-strictly to round them back.
        result = EngineResult.model_validate(
            {
                "profile_cuts": materials.get("profile_cuts") or [],
                "reinforcements": materials.get("reinforcements") or [],
                "glasses": materials.get("glasses") or [],
                "panels": materials.get("panels") or [],
                "hardware_items": materials.get("hardware_items") or [],
                "leaf_weights": materials.get("leaf_weights") or [],
            },
            strict=False,
        )
        stocks = CuttingRepository()
        authorities = stocks.for_result(result, UUID(str(system_id)), org_id, color)
        profile = stocks.cutting_profile(org_id, cutting_profile_code)
        per_unit = pieces_from_result(
            result,
            color=color,
            source_position_id=str(position_id) if position_id else None,
            reinforcement_skus=authorities.reinforcement_skus,
            reinforcement_angles=_reinforcement_angle_map(
                version_snapshot, str(position_id) if position_id else None
            ),
        )
        # pieces_from_result already expands each unit's qty via unit_index;
        # offset by the per-unit count so the identity stays unique per unit.
        pieces = [
            piece.model_copy(
                update={"unit_index": (repetition - 1) * len(per_unit) + piece.unit_index}
            )
            for repetition in range(1, quantity + 1)
            for piece in per_unit
        ]
        bars = optimize_cut(pieces, authorities.stocks, profile).model_dump(mode="json")

        rules = _sheet_rules(org_id)
        sheets: list[dict[str, object]] = []
        sheet_purchases: list[dict[str, object]] = []
        unnested: list[dict[str, object]] = []
        sheet_groups: list[tuple[SheetRule, list[NestPiece]]] = []
        for group_key, entries, kind in (
            ("by_thickness", result.glasses, "GLASS"),
            ("by_sku", result.panels, "PANEL"),
        ):
            for index, entry in enumerate(entries, start=1):
                group = (
                    str(entry.thickness_net_mm) if kind == "GLASS" else entry.sku
                )
                rule = _pick_sheet_rule(
                    rules[group_key].get(group) or [], entry.width_mm, entry.height_mm
                )
                label = f"V-{index:02d}" if kind == "GLASS" else f"PAN-{index:02d}"
                if rule is None:
                    unnested.append({
                        "kind": kind, "group": group,
                        "width_mm": str(entry.width_mm),
                        "height_mm": str(entry.height_mm), "quantity": quantity,
                        "bay_id": entry.bay_id, "leaf_id": entry.leaf_id,
                        "reason": "no_declared_sheet",
                    })
                    continue
                sheet_groups.append((
                    rule,
                    [
                        NestPiece(
                            piece_id=label,
                            workshop_sku=rule.workshop_sku,
                            width_mm=entry.width_mm,
                            height_mm=entry.height_mm,
                            source_position_id=str(position_id) if position_id else None,
                            bay_id=entry.bay_id,
                            leaf_id=entry.leaf_id,
                            unit_index=repetition,
                        )
                        for repetition in range(1, quantity + 1)
                    ],
                ))
        # Group by the full selected rule identity (format + trim + purchasing
        # identity), never just the SKU — pieces picked for different variants
        # of one SKU keep separate layouts and purchase lines.
        merged: dict[tuple, tuple[SheetRule, list[NestPiece]]] = {}
        for rule, pieces_group in sheet_groups:
            key = (
                rule.workshop_sku,
                str(rule.sheet_width_mm),
                str(rule.sheet_height_mm),
                str(rule.edge_trim_mm),
                rule.purchasing_sku,
            )
            merged.setdefault(key, (rule, []))[1].extend(pieces_group)
        for rule, group_pieces in merged.values():
            outcome = nest_rects(group_pieces, rule)
            for layout in outcome.layouts:
                dumped = layout.model_dump(mode="json")
                # sheet_index restarts per bin — renumber across the whole plan
                # so layouts keep a stable globally-unique identity.
                dumped["sheet_index"] = len(sheets) + 1
                sheets.append(dumped)
            sheet_purchases.extend(
                purchase.model_dump(mode="json") for purchase in outcome.purchase_list
            )
            for piece in outcome.unplaced:
                unnested.append({
                    "kind": "SHEET", "group": rule.workshop_sku,
                    "width_mm": str(piece.width_mm), "height_mm": str(piece.height_mm),
                    "quantity": 1, "bay_id": piece.bay_id, "leaf_id": piece.leaf_id,
                    "reason": "piece_larger_than_usable_sheet",
                })

        optimization = {
            "schema": "work_order_optimization_v1",
            "optimized_at": datetime.now(timezone.utc).isoformat(),
            "actor_id": str(actor_id),
            "color": color,
            "units": quantity,
            "bars": bars,
            "sheets": sheets,
            "sheet_purchases": sheet_purchases,
            "unnested": unnested,
        }
        # A fresh plan invalidates any machine files rendered from the old one.
        new_payload = {**payload, "optimization": optimization}
        new_payload.pop("cnc_export", None)
        rows(
            """
            UPDATE public.orders SET payload_json = %s::jsonb, updated_at = %s
            WHERE id = %s AND org_id = %s
            RETURNING id
            """,
            [json.dumps(new_payload), datetime.now(timezone.utc),
             str(order_id), str(org_id)],
        )
        rows(
            """
            INSERT INTO public.production_step_events(org_id, order_id, event, actor_id, payload)
            VALUES (%s, %s, 'WO_OPTIMIZED', %s, %s::jsonb)
            RETURNING id
            """,
            [
                str(org_id),
                str(order_id),
                str(actor_id),
                json.dumps({
                    "order_code": order["order_code"],
                    "color": color,
                    "bars": len(bars.get("workshop_cut_plan") or []),
                    "sheets": len(sheets),
                    "unnested": len(unnested),
                }),
            ],
        )
        return {
            "order_id": str(order_id),
            "order_code": order["order_code"],
            "optimization": optimization,
        }


_DELIVERY_WINDOWS = ("AM", "PM", "JORNADA")
_DELIVERY_NEXT = {
    "ON_ROUTE": {"SCHEDULED"},
    "DELIVERED": {"ON_ROUTE"},
    "FAILED": {"ON_ROUTE"},
}
_DELIVERY_EVENT = {
    "ON_ROUTE": "WO_DELIVERY_ON_ROUTE",
    "DELIVERED": "WO_DELIVERY_DELIVERED",
    "FAILED": "WO_DELIVERY_FAILED",
}


def _public_delivery(
    delivery: dict[str, object], *, confirmation: dict | None = None
) -> dict[str, object]:
    return {
        "id": str(delivery["id"]),
        "order_id": str(delivery["order_id"]),
        "order_code": str(delivery["order_code"]),
        "scheduled_date": str(delivery["scheduled_date"]),
        "time_window": str(delivery["time_window"]),
        "address": str(delivery["address"]),
        "contact_name": delivery["contact_name"],
        "contact_phone": delivery["contact_phone"],
        "installer_name": delivery["installer_name"],
        "notes": delivery["notes"],
        "status": str(delivery["status"]),
        "confirmation": confirmation,
        "scheduled_by": str(delivery["scheduled_by"]) if delivery["scheduled_by"] else None,
        "created_at": delivery["created_at"].isoformat(),
        "updated_at": delivery["updated_at"].isoformat(),
    }


def get_delivery(*, org_id: UUID, order_id: UUID) -> dict[str, object]:
    """Delivery for a valid WORKSHOP_OT — `delivery: null` only when the order
    genuinely exists but was never scheduled; bad ids raise work_order_not_found."""
    with documentary_backend():
        found = rows(
            """
            SELECT d.*, o.order_code FROM public.orders o
            LEFT JOIN public.deliveries d ON d.order_id = o.id
            WHERE o.id = %s AND o.org_id = %s AND o.order_type = 'WORKSHOP_OT'
            """,
            [str(order_id), str(org_id)],
        )
        if not found:
            raise DocumentaryError("work_order_not_found")
    delivery = found[0]
    if not delivery.get("id"):
        return {"delivery": None}
    return {
        "delivery": _public_delivery(
            delivery,
            confirmation=confirmation_summary(
                org_id=org_id, order_id=order_id
            ),
        )
    }


def schedule_delivery(
    *,
    org_id: UUID,
    order_id: UUID,
    actor_id: UUID,
    scheduled_date: str,
    time_window: str | None,
    address: str,
    contact_name: str | None = None,
    contact_phone: str | None = None,
    installer_name: str | None = None,
    notes: str | None = None,
) -> dict[str, object]:
    """Create or update the order's single delivery — rescheduling is an
    upsert so retries and edits stay idempotent on the same row."""
    window = (time_window or "AM").strip().upper()
    if window not in _DELIVERY_WINDOWS:
        raise DocumentaryError("delivery_window_invalid")
    if not (address or "").strip():
        raise DocumentaryError("delivery_address_required")
    try:
        day = date.fromisoformat(str(scheduled_date))
    except (TypeError, ValueError):
        raise DocumentaryError("delivery_date_invalid")
    with transaction.atomic(), documentary_backend():
        order = one(
            """
            SELECT id, order_code, status::text FROM public.orders
            WHERE id = %s AND org_id = %s AND order_type = 'WORKSHOP_OT'
            FOR UPDATE
            """,
            [str(order_id), str(org_id)],
            "work_order_not_found",
        )
        if str(order["status"]) not in ("COMPLETED", "DISPATCHED"):
            raise DocumentaryError("delivery_requires_completed")
        existing = rows(
            "SELECT * FROM public.deliveries WHERE order_id = %s AND org_id = %s",
            [str(order_id), str(org_id)],
        )
        if existing and str(existing[0]["status"]) == "DELIVERED":
            raise DocumentaryError("delivery_already_delivered")
        normalized = {
            "scheduled_date": day,
            "time_window": window,
            "address": address.strip(),
            "contact_name": (contact_name or "").strip() or None,
            "contact_phone": (contact_phone or "").strip() or None,
            "installer_name": (installer_name or "").strip() or None,
            "notes": (notes or "").strip() or None,
        }
        if (
            existing
            and str(existing[0]["status"]) == "SCHEDULED"
            and all(existing[0][key] == value for key, value in normalized.items())
        ):
            # Identical schedule replay — one row, no duplicate audit event.
            return get_delivery(org_id=org_id, order_id=order_id)
        delivery = one(
            """
            INSERT INTO public.deliveries(
                org_id, order_id, scheduled_date, time_window, address,
                contact_name, contact_phone, installer_name, notes, scheduled_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (order_id) DO UPDATE SET
                scheduled_date = EXCLUDED.scheduled_date,
                time_window = EXCLUDED.time_window,
                address = EXCLUDED.address,
                contact_name = EXCLUDED.contact_name,
                contact_phone = EXCLUDED.contact_phone,
                installer_name = EXCLUDED.installer_name,
                notes = EXCLUDED.notes,
                scheduled_by = EXCLUDED.scheduled_by,
                status = 'SCHEDULED',
                updated_at = %s
            RETURNING *
            """,
            [
                str(org_id),
                str(order_id),
                str(day),
                window,
                address.strip(),
                (contact_name or "").strip() or None,
                (contact_phone or "").strip() or None,
                (installer_name or "").strip() or None,
                (notes or "").strip() or None,
                str(actor_id),
                datetime.now(timezone.utc),
            ],
        )
        rows(
            """
            INSERT INTO public.production_step_events(org_id, order_id, event, actor_id, payload)
            VALUES (%s, %s, 'WO_DELIVERY_SCHEDULED', %s, %s::jsonb)
            RETURNING id
            """,
            [
                str(org_id),
                str(order_id),
                str(actor_id),
                json.dumps({
                    "order_code": order["order_code"],
                    "scheduled_date": str(day),
                    "time_window": window,
                    "installer_name": delivery["installer_name"],
                }),
            ],
        )
    return get_delivery(org_id=org_id, order_id=order_id)


def transition_delivery(
    *, org_id: UUID, order_id: UUID, actor_id: UUID, to_status: str
) -> dict[str, object]:
    """Move the delivery forward; guarded by both its own state and the
    order's — a truck can't leave before the order is DISPATCHED."""
    target = str(to_status or "").upper()
    if target not in _DELIVERY_NEXT:
        raise DocumentaryError("delivery_transition_invalid")
    with transaction.atomic(), documentary_backend():
        order = one(
            """
            SELECT id, order_code, status::text FROM public.orders
            WHERE id = %s AND org_id = %s AND order_type = 'WORKSHOP_OT'
            FOR UPDATE
            """,
            [str(order_id), str(org_id)],
            "work_order_not_found",
        )
        if str(order["status"]) == "INSTALLED":
            raise DocumentaryError("order_already_installed")
        delivery = one(
            """
            SELECT * FROM public.deliveries
            WHERE order_id = %s AND org_id = %s FOR UPDATE
            """,
            [str(order_id), str(org_id)],
            "delivery_not_found",
        )
        current = str(delivery["status"])
        if current == target:
            return get_delivery(org_id=org_id, order_id=order_id)
        if current not in _DELIVERY_NEXT[target]:
            raise DocumentaryError("delivery_transition_invalid")
        if target == "ON_ROUTE" and str(order["status"]) != "DISPATCHED":
            raise DocumentaryError("delivery_requires_dispatched")
        rows(
            """
            UPDATE public.deliveries SET status = %s, updated_at = %s
            WHERE id = %s AND org_id = %s RETURNING id
            """,
            [target, datetime.now(timezone.utc), str(delivery["id"]), str(org_id)],
        )
        rows(
            """
            INSERT INTO public.production_step_events(org_id, order_id, event, actor_id, payload)
            VALUES (%s, %s, %s, %s, %s::jsonb)
            RETURNING id
            """,
            [
                str(org_id),
                str(order_id),
                _DELIVERY_EVENT[target],
                str(actor_id),
                json.dumps({"order_code": order["order_code"]}),
            ],
        )
    return get_delivery(org_id=org_id, order_id=order_id)
