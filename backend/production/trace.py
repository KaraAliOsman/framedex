"""§11 work-order traceability — assemble the sealed chain in both directions.

Forward: project → version → position → module/bay/leaf → article → cut
piece → stock source → plan → work order. Backward: any cut ``piece_id``
resolves to the work order, plan location and routing progress it lives in.

Everything returned here is read-only evidence: the chain is decoded from the
sealed ``orders.payload_json`` plan and the append-only step/movement ledgers
— nothing is recomputed or inferred. IDs are the stable identities the sealed
artifacts already carry (``piece_id`` hashes, position/bay/leaf uuids,
``stock_authority_id``, remnant and movement ids)."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from documents.repository import DocumentaryError, one, rows

from dekopen_engine.cutting import CutBar
from dekopen_engine.manufacturing import ManufacturingFactsV1
from dekopen_engine.operations import operations_from_plan


def _decoded(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            loaded = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return loaded if isinstance(loaded, dict) else {}
    return {}


def _trace_piece(cut: dict[str, Any]) -> dict[str, Any]:
    """The stable identity of one cut piece — everything needed to walk
    backward from the physical label to its origin member."""
    return {
        "piece_id": cut.get("piece_id"),
        "sequence": cut.get("sequence"),
        "role": cut.get("role"),
        "length_mm": cut.get("length_mm"),
        "width_mm": cut.get("width_mm"),
        "height_mm": cut.get("height_mm"),
        "angle_left": cut.get("angle_left"),
        "angle_right": cut.get("angle_right"),
        "sagitta_mm": cut.get("sagitta_mm"),
        "workshop_sku": cut.get("workshop_sku"),
        "source_kind": cut.get("source_kind"),
        "x_mm": cut.get("x_mm"),
        "y_mm": cut.get("y_mm"),
        "rotated": cut.get("rotated"),
        "source_position_id": cut.get("source_position_id"),
        "module_id": cut.get("module_id"),
        "bay_id": cut.get("bay_id"),
        "leaf_id": cut.get("leaf_id"),
        "unit_index": cut.get("unit_index"),
        "machining": cut.get("machining"),
    }


def _plan_bars(optimization: dict[str, Any]) -> list[dict[str, Any]]:
    bars = (optimization.get("bars") or {}).get("workshop_cut_plan") or []
    plan = []
    for bar in bars:
        plan.append({
            "bar_index": bar.get("bar_index"),
            "commercial_sku": bar.get("commercial_sku"),
            "material": bar.get("material"),
            "color": bar.get("color"),
            "source": bar.get("source"),
            "stock_authority_id": bar.get("stock_authority_id"),
            "stock_length_mm": bar.get("stock_length_mm"),
            "remainder_mm": bar.get("remainder_mm"),
            "yield_pct": bar.get("yield_pct"),
            "cuts": [_trace_piece(cut) for cut in bar.get("cuts") or []],
        })
    return plan


def _plan_sheets(optimization: dict[str, Any]) -> list[dict[str, Any]]:
    sheets = optimization.get("sheets") or []
    plan = []
    for sheet in sheets:
        plan.append({
            "sheet_index": sheet.get("sheet_index"),
            "workshop_sku": sheet.get("workshop_sku"),
            "material": sheet.get("material"),
            "width_mm": sheet.get("sheet_width_mm"),
            "height_mm": sheet.get("sheet_height_mm"),
            "purchasing_sku": sheet.get("purchasing_sku"),
            "remnant_id": sheet.get("remnant_id"),
            "yield_pct": sheet.get("yield_pct"),
            "source": sheet.get("source"),
            "pieces": [_trace_piece(piece) for piece in sheet.get("placements") or []],
        })
    return plan


def trace_work_order(*, org_id: UUID, order_id: UUID) -> dict[str, Any]:
    """The full forward chain for one work order."""
    order = one(
        """
        SELECT id::text, order_code, status::text, project_id::text,
               project_version_id::text, order_type::text,
               payload_json::text, created_at, updated_at
        FROM public.orders WHERE id = %s AND org_id = %s
        """,
        [str(order_id), str(org_id)],
        "work_order_not_found",
    )
    payload = _decoded(order["payload_json"])
    optimization = _decoded(payload.get("optimization")) or {}

    project = None
    if order["project_id"]:
        project = one(
            """
            SELECT id::text, code, name, client_name, current_revision
            FROM public.projects WHERE id = %s AND org_id = %s
            """,
            [order["project_id"], str(org_id)],
            "work_order_not_found",
        )

    version = None
    version_snapshot: dict[str, Any] = {}
    if order["project_version_id"]:
        version = one(
            """
            SELECT id::text, revision_code, snapshot_sha256, bom_hash,
                   emitted_at, production_allowed, snapshot_json::text
            FROM public.project_versions WHERE id = %s AND org_id = %s
            """,
            [order["project_version_id"], str(org_id)],
            "work_order_not_found",
        )
        version_snapshot = _decoded(version.pop("snapshot_json", None))

    steps = rows(
        """
        SELECT step.id::text, step.sequence, step.code, step.label,
               step.status, step.work_center_id::text,
               work_center.code AS work_center_code,
               work_center.name AS work_center_name,
               step.started_at, step.finished_at, step.actor_id::text,
               step.note
        FROM public.production_steps step
        LEFT JOIN public.work_centers work_center
          ON work_center.id = step.work_center_id
        WHERE step.order_id = %s AND step.org_id = %s
        ORDER BY step.sequence
        """,
        [str(order_id), str(org_id)],
    )

    events = rows(
        """
        SELECT id::text, step_id::text, event, actor_id::text,
               payload::text, created_at
        FROM public.production_step_events
        WHERE order_id = %s AND org_id = %s
        ORDER BY created_at
        """,
        [str(order_id), str(org_id)],
    )
    for event in events:
        event["payload"] = _decoded(event["payload"])

    movements = rows(
        """
        SELECT movement.id::text, movement.movement_type::text,
               movement.quantity, movement.note,
               movement.created_at, movement.actor_id::text,
               item.id::text AS item_id, item.sku, item.variant_key,
               item.name AS item_name
        FROM public.inventory_movements movement
        JOIN public.inventory_items item ON item.id = movement.item_id
        WHERE movement.order_id = %s AND movement.org_id = %s
        ORDER BY movement.created_at
        """,
        [str(order_id), str(org_id)],
    )

    remnants = rows(
        """
        SELECT id::text, kind, status, material, color,
               stock_authority_id::text, sheet_workshop_sku,
               physical_stock_identity::text,
               length_mm, width_mm, height_mm, origin,
               origin_order_id::text, reserved_order_id::text,
               consumed_order_id::text, rack_location
        FROM public.inventory_remnants
        WHERE org_id = %s AND (
            origin_order_id = %s OR reserved_order_id = %s
            OR consumed_order_id = %s)
        ORDER BY created_at
        """,
        [str(org_id), str(order_id), str(order_id), str(order_id)],
    )

    position_id = payload.get("position_id")
    return {
        "work_order": {
            "id": order["id"],
            "order_code": order["order_code"],
            "order_type": order["order_type"],
            "status": order["status"],
            "created_at": order["created_at"],
            "updated_at": order["updated_at"],
        },
        "project": project,
        "version": version,
        "position_id": position_id,
        "plan": {
            "optimized_at": optimization.get("optimized_at"),
            "strategy": optimization.get("strategy"),
            "color": optimization.get("color"),
            "units": optimization.get("units"),
            "bars": _plan_bars(optimization),
            "sheets": _plan_sheets(optimization),
            "unnested": optimization.get("unnested") or [],
        },
        "stock": {
            "reservations": optimization.get("stock_reservations") or [],
            "unmapped_stock_skus": optimization.get("unmapped_stock_skus") or [],
            "movements": movements,
            "remnants": remnants,
        },
        "steps": steps,
        "events": events,
        "operations": _trace_operations(
            payload=payload,
            optimization=optimization,
            version_snapshot=version_snapshot,
        ),
    }


def _trace_operations(
    *,
    payload: dict[str, Any],
    optimization: dict[str, Any],
    version_snapshot: dict[str, Any],
) -> dict[str, Any]:
    """The sealed plan's machining operations, reconstructed deterministically
    — the same derivation ``export_operations`` uses, computed at read time so
    the operator sees them without sealing an export. Empty when the order has
    not been optimized or the frozen snapshot carries no manufacturing facts."""
    raw_bars = (optimization.get("bars") or {}).get("workshop_cut_plan") or []
    raw_units = [
        unit
        for unit in (version_snapshot.get("manufacturing") or [])
        if not payload.get("position_id")
        or str(unit.get("position_id")) == str(payload["position_id"])
    ]
    if not raw_bars:
        return {"count": 0, "items": [], "unemitted_kinds": []}
    try:
        bars = [
            CutBar.model_validate_json(json.dumps(bar)) for bar in raw_bars
        ]
        fact_units = [
            ManufacturingFactsV1.model_validate_json(json.dumps(unit))
            for unit in raw_units
        ]
    except Exception:
        return {"count": 0, "items": [], "unemitted_kinds": [],
                "unavailable": "operations_underivable"}
    ops = [
        op.model_dump(mode="json")
        for op in operations_from_plan(bars=bars, fact_units=fact_units)
    ]
    by_kind: dict[str, int] = {}
    for op in ops:
        by_kind[str(op["kind"])] = by_kind.get(str(op["kind"]), 0) + 1
    return {"count": len(ops), "by_kind": by_kind, "items": ops}


def _piece_hits(order_row: dict[str, Any], piece_id: str) -> list[dict[str, Any]]:
    """Locate ``piece_id`` inside one order's sealed plan."""
    payload = _decoded(order_row["payload_json"])
    optimization = _decoded(payload.get("optimization")) or {}
    hits: list[dict[str, Any]] = []
    for bar in _plan_bars(optimization):
        for cut in bar["cuts"]:
            if cut["piece_id"] == piece_id:
                hits.append({
                    "kind": "BAR",
                    "bar_index": bar["bar_index"],
                    "commercial_sku": bar["commercial_sku"],
                    "piece": cut,
                })
    for sheet in _plan_sheets(optimization):
        for piece in sheet["pieces"]:
            if piece["piece_id"] == piece_id:
                hits.append({
                    "kind": "SHEET",
                    "sheet_index": sheet["sheet_index"],
                    "workshop_sku": sheet["workshop_sku"],
                    "piece": piece,
                })
    return hits


def trace_piece(*, org_id: UUID, piece_id: str) -> dict[str, Any]:
    """Backward lookup: which work order(s) and plan location carry a
    physical piece — walk from the piece back to order → version → project."""
    if not piece_id or len(piece_id) > 128:
        raise DocumentaryError("work_order_piece_invalid")
    orders = rows(
        """
        SELECT id::text, order_code, status::text,
               project_id::text, project_version_id::text, payload_json::text
        FROM public.orders
        WHERE org_id = %s AND payload_json::text LIKE %s
        ORDER BY created_at
        """,
        [str(org_id), f"%{piece_id}%"],
    )
    matches: list[dict[str, Any]] = []
    for order in orders:
        hits = _piece_hits(order, piece_id)
        if not hits:
            continue
        steps = rows(
            """
            SELECT sequence, code, label, status
            FROM public.production_steps
            WHERE order_id = %s AND org_id = %s
            ORDER BY sequence
            """,
            [order["id"], str(org_id)],
        )
        project = None
        if order["project_id"]:
            project = one(
                """
                SELECT id::text, code, name FROM public.projects
                WHERE id = %s AND org_id = %s
                """,
                [order["project_id"], str(org_id)],
                "work_order_not_found",
            )
        for hit in hits:
            matches.append({
                "work_order": {
                    "id": order["id"],
                    "order_code": order["order_code"],
                    "status": order["status"],
                },
                "project": project,
                "project_version_id": order["project_version_id"],
                "location": hit,
                "steps": steps,
            })
    return {"piece_id": piece_id, "matches": matches}


def trace_version(*, org_id: UUID, version_id: UUID) -> dict[str, Any]:
    """Forward chain from a frozen version to every work order released
    from it — plus, per order, the positions and piece counts its plan cut."""
    version = one(
        """
        SELECT id::text, project_id::text, revision_code, snapshot_sha256,
               bom_hash, emitted_at, production_allowed
        FROM public.project_versions WHERE id = %s AND org_id = %s
        """,
        [str(version_id), str(org_id)],
        "version_not_found",
    )
    project = one(
        """
        SELECT id::text, code, name, client_name
        FROM public.projects WHERE id = %s AND org_id = %s
        """,
        [version["project_id"], str(org_id)],
        "version_not_found",
    )
    orders = rows(
        """
        SELECT id::text, order_code, status::text, order_type::text,
               payload_json::text, created_at
        FROM public.orders
        WHERE org_id = %s AND project_version_id = %s
        ORDER BY created_at
        """,
        [str(org_id), str(version_id)],
    )
    work_orders = []
    for order in orders:
        payload = _decoded(order["payload_json"])
        optimization = _decoded(payload.get("optimization")) or {}
        bars = _plan_bars(optimization)
        sheets = _plan_sheets(optimization)
        positions = sorted({
            str(cut["source_position_id"])
            for bar in bars for cut in bar["cuts"]
            if cut["source_position_id"]
        } | {
            str(piece["source_position_id"])
            for sheet in sheets for piece in sheet["pieces"]
            if piece["source_position_id"]
        })
        work_orders.append({
            "work_order": {
                "id": order["id"],
                "order_code": order["order_code"],
                "order_type": order["order_type"],
                "status": order["status"],
                "created_at": order["created_at"],
            },
            "position_id": payload.get("position_id"),
            "positions_cut": positions,
            "bars": len(bars),
            "sheets": len(sheets),
            "pieces": sum(len(bar["cuts"]) for bar in bars)
            + sum(len(sheet["pieces"]) for sheet in sheets),
        })
    return {
        "version": version,
        "project": project,
        "work_orders": work_orders,
    }
