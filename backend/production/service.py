"""Production orchestration: release sealed versions to workshop orders.

A work order is an ``orders`` row with ``order_type='WORKSHOP_OT'`` — the
substrate the schema already reserves for the shop floor (free-form status,
org-scoped access). Its ``payload_json`` carries the per-position cut list
straight from the sealed version snapshot, so nothing is re-entered between
the commercial and the workshop departments. Routing lives in
``production_steps``; every transition appends to ``production_step_events``
so the floor has a paperless trail."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any
from uuid import UUID

from django.db import connection, transaction

from documents.repository import DocumentaryError, documentary_backend, one, rows


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
    "START": ("IN_PROGRESS", {"PENDING", "READY", "BLOCKED"}),
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
        centers = _ensure_work_centers(org_id)
        created_ids: list[UUID] = []
        order_ids: list[UUID] = []
        for index, position in enumerate(bom):
            payload = _work_order_payload(position)
            order_code = f"OT-{version['revision_code']}-{index + 1:02d}"
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
                    """,
                    [str(org_id), str(version_id), payload["position_id"]],
                    "work_order_not_found",
                )["id"]
            order_ids.append(order_id)
            if inserted:
                center_by_step = {
                    code: centers.get(_STEP_CODE_FOR_CENTER[code]) for code in set(_STEP_CODE_FOR_CENTER)
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
    output = _public_order(order, include_payload=True)
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
    elif new_status == "HOLD":
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
) -> dict[str, object]:
    if action not in _TRANSITIONS:
        raise DocumentaryError("step_action_unknown")
    with transaction.atomic():
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
        order = one(
            """
            SELECT status::text FROM public.orders
            WHERE id = %s AND org_id = %s AND order_type = 'WORKSHOP_OT'
            """,
            [str(step["order_id"]), str(org_id)],
            "work_order_not_found",
        )
        if str(order["status"]) == "COMPLETED":
            raise DocumentaryError("work_order_completed")
        new_status, allowed = _TRANSITIONS[action]
        if str(step["status"]) not in allowed:
            raise DocumentaryError("step_transition_invalid")
        now = datetime.now(timezone.utc)
        if new_status is not None:
            updates = {
                "status": new_status,
                "updated_at": now,
                "note": note if note is not None else step.get("note"),
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
                _EVENTS[action],
                str(actor_id),
                json.dumps({"note": note} if note else {}),
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


def list_work_centers(*, org_id: UUID) -> dict[str, object]:
    centers = _ensure_work_centers(org_id)
    return {
        "centers": rows(
            """
            SELECT id, code, name, kind, display_order, active
            FROM public.work_centers WHERE org_id = %s ORDER BY display_order
            """,
            [str(org_id)],
        )
    }


def create_work_center(
    *, org_id: UUID, code: str, name: str, kind: str, display_order: int
) -> dict[str, object]:
    if kind not in _STEP_CODE_FOR_CENTER:
        raise DocumentaryError("work_center_kind_unknown")
    center = one(
        """
        INSERT INTO public.work_centers(org_id, code, name, kind, display_order)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (org_id, code) DO UPDATE SET
            name = EXCLUDED.name, kind = EXCLUDED.kind,
            display_order = EXCLUDED.display_order, active = TRUE
        RETURNING id, code, name, kind, display_order, active
        """,
        [str(org_id), code, name, kind, display_order],
    )
    return center
