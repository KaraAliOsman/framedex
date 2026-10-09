"""Presentation addresses for physical placements, derived from sealed facts.

Never write these fields into a plan or its fingerprint. The same deterministic
allocation is used by web, saw CSV, DXF, cut pack and physical labels.
"""

from __future__ import annotations

from copy import deepcopy
from urllib.parse import urlencode

from django.conf import settings

from documents.renderers import (
    _cut_key, _cut_member_map, _cut_piece_ids, _infill_key,
    _infill_spec_index, _piece_labels,
)


def entity_address(path: str, **identity: object) -> str:
    return settings.DEKOPEN_PUBLIC_APP_URL.rstrip("/") + path + "?" + urlencode(identity)


def without_addresses(plan: dict) -> dict:
    """Recover strict engine facts from the presentation copy, without coercion."""
    result = deepcopy(plan)
    for bar in (result.get("bars") or {}).get("workshop_cut_plan") or []:
        bar.pop("remnant_code", None)
        for cut in bar.get("cuts") or []:
            for field in ("piece_code", "piece_stable_id", "piece_qr"):
                cut.pop(field, None)
    for sheet in result.get("sheets") or []:
        sheet.pop("remnant_code", None)
        for piece in sheet.get("placements") or []:
            for field in ("piece_code", "piece_stable_id", "piece_qr"):
                piece.pop(field, None)
    return result


def add_remnant_codes(plan: dict, org_id: object) -> dict:
    from documents.repository import rows

    entries = [*((plan.get("bars") or {}).get("workshop_cut_plan") or []), *(plan.get("sheets") or [])]
    identities = sorted({str(entry["remnant_id"]) for entry in entries if entry.get("remnant_id")})
    if identities:
        codes = {str(row["id"]): row["code"] for row in rows(
            "SELECT id,private.entity_code(org_id,'RT',id) AS code FROM public.inventory_remnants"
            " WHERE org_id=%s AND id=ANY(%s::uuid[])", [str(org_id), identities],
        )}
        for entry in entries:
            if entry.get("remnant_id"):
                entry["remnant_code"] = codes.get(str(entry["remnant_id"]))
    return plan


def plan_fact_scope(snapshot: dict, optimization: dict) -> dict:
    """Index only the positions named by this plan, preserving legacy fallback.

    Labels still come from the complete snapshot so old sequential addresses
    remain stable. Sourced plans do not need sibling machining derivations.
    """
    placements = [cut for bar in (optimization.get("bars") or {}).get("workshop_cut_plan") or []
                  for cut in bar.get("cuts") or []]
    placements.extend(piece for sheet in optimization.get("sheets") or []
                      for piece in sheet.get("placements") or [])
    if not placements or any(not piece.get("source_position_id") for piece in placements):
        return snapshot
    positions = {str(piece["source_position_id"]) for piece in placements}
    return {**snapshot, "manufacturing": [fact for fact in snapshot.get("manufacturing") or []
            if str(fact.get("position_id")) in positions]}


def addressed_plan(snapshot: dict, optimization: dict, *, order_id: object = None) -> dict:
    """Allocate repeated equal specs to physical identities in stable plan order.

    Equal cuts inside one unit consume the frozen ids in label order. The pools
    span all bars/sheets, so moving a cut to the next bar cannot duplicate it.
    Legacy facts without repetition_index use their own unqualified pool.
    """
    result = deepcopy(optimization)
    labels = _piece_labels({"manufacturing": [], "positions": [], **snapshot})
    scoped = plan_fact_scope(snapshot, optimization)
    cut_map = _cut_member_map(scoped, labels)
    pools = {
        key: {str(unit): sorted(ids, key=lambda entity: str(
            labels["member" if key[0] == "PROFILE" else "reinforcement"].get(entity, "")
        )) for unit, ids in units.items()}
        for key, units in _cut_piece_ids(scoped).items()
    }
    infill_homes = {
        item.get("infill_id"): str(fact.get("repetition_index"))
        for fact in scoped.get("manufacturing") or []
        for item in fact.get("infills") or []
    }
    infill_pools = {}
    for key, ids in _infill_spec_index(scoped).items():
        homes = infill_pools.setdefault(key, {})
        for entity in sorted(ids, key=lambda value: str(labels["infill"].get(value, ""))):
            homes.setdefault(infill_homes.get(entity, "None"), []).append(entity)

    def stamp(piece: dict, pool: dict, group: str, fallback: str | None = None) -> None:
        ids = pool.get(str(piece.get("unit_index"))) or pool.get("None") or []
        entity = ids.pop(0) if ids else None
        code = labels[group].get(entity) if entity is not None else (labels[group].get(piece.get("piece_id")) or fallback)
        piece["piece_code"] = code
        piece["piece_stable_id"] = str(entity) if entity is not None else str(piece.get("piece_id") or "")
        piece["piece_qr"] = entity_address("/production", order=order_id,
            piece=code, identity=piece["piece_stable_id"]) if code and order_id else None

    for bar in sorted((result.get("bars") or {}).get("workshop_cut_plan") or [],
                      key=lambda value: int(value.get("bar_index") or 0)):
        for cut in sorted(bar.get("cuts") or [], key=lambda value: int(value.get("sequence") or 0)):
            key = _cut_key(cut)
            group = "member" if key[0] == "PROFILE" else "reinforcement"
            stamp(cut, pools.get(key, {}), group, cut_map.get(key))
    for sheet in sorted(result.get("sheets") or [], key=lambda value: int(value.get("sheet_index") or 0)):
        for piece in sorted(sheet.get("placements") or [], key=lambda value: (
            str(value.get("piece_id") or ""), str(value.get("unit_index") or ""),
        )):
            stamp(piece, infill_pools.get(_infill_key(piece), {}), "infill")
    return result


def physical_labels(plan: dict) -> list[dict]:
    import segno

    pieces = [cut for bar in (plan.get("bars") or {}).get("workshop_cut_plan") or []
              for cut in bar.get("cuts") or []]
    pieces.extend(piece for sheet in plan.get("sheets") or [] for piece in sheet.get("placements") or [])
    return [{"code": piece["piece_code"], "stable_id": piece["piece_stable_id"],
        "qr_payload": piece["piece_qr"],
        "qr_svg": segno.make(piece["piece_qr"], error="m").svg_inline(border=4, scale=4, omitsize=True),
        "length_mm": piece.get("length_mm"), "width_mm": piece.get("width_mm"),
        "height_mm": piece.get("height_mm"), "workshop_sku": piece.get("workshop_sku")}
        for piece in pieces if piece.get("piece_code") and piece.get("piece_qr")]
