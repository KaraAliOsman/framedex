"""Exact stock coverage and declared purchase totals. No catalogue guesses."""
from decimal import Decimal
from collections.abc import Sequence
from typing import Any

from dekopen_engine.documentary_canonical import documentary_sha256_v1
from dekopen_engine.models import EngineResult
from dekopen_engine.purchasing import fitting_selections_v1


def stock_shortfall(*, required: Decimal, own_reserved: Decimal,
                    available: Decimal, incoming: Decimal) -> dict[str, Decimal]:
    values = (required, own_reserved, available, incoming)
    if any(not value.is_finite() or value < 0 for value in values):
        raise ValueError("Stock quantities must be finite and nonnegative")
    reserved = min(required, own_reserved)
    covered = min(required - reserved, available)
    transit = min(required - reserved - covered, incoming)
    return {"reserved": reserved, "stock": covered, "incoming": transit,
            "purchase": required - reserved - covered - transit}


def purchase_total(lines: Sequence[tuple[Decimal, Decimal | None]]) -> Decimal | None:
    if any(price is None for _, price in lines):
        return None
    if any(qty <= 0 or not qty.is_finite() or price is None or price < 0
           or not price.is_finite() for qty, price in lines):
        raise ValueError("Purchase price requires explicit nonnegative authority")
    return sum((qty * price for qty, price in lines if price is not None), Decimal(0))


def purchase_glass_areas(lines: Sequence[tuple[Decimal, Decimal, int]]) -> tuple[list[Decimal], Decimal]:
    if any(not width.is_finite() or not height.is_finite() or width <= 0 or height <= 0 or quantity <= 0
           for width, height, quantity in lines):
        raise ValueError('Glass purchase requires declared positive dimensions and count')
    areas = [width * height * Decimal(quantity) / Decimal('1000000') for width, height, quantity in lines]
    return areas, sum(areas, Decimal(0))


def purchase_source_ledger(snapshot: dict[str, Any]) -> dict[str, tuple[str, Decimal]]:
    """Recover each sealed procurement source's position and exact count.

    Uses the SHOT10 source preimages, including counted hardware components.
    It never prorates a consolidated requirement by the number of open OT.
    Unknown historical sources remain absent so the caller can report a gap.
    """
    sources: dict[str, tuple[str, Decimal]] = {}
    for unit in snapshot.get("manufacturing") or []:
        position = str(unit["position_id"])
        for group, field in (("members", "member_id"), ("reinforcements", "reinforcement_id"),
                             ("infills", "infill_id")):
            for piece in unit.get(group) or []:
                sources[str(piece[field])] = (position, Decimal(1))
    for bom in snapshot.get("bom") or []:
        position = str(bom["position_id"])
        quantity = int(bom["quantity"])
        result = EngineResult.model_validate(bom["engine_result"], strict=False)
        for repetition in range(1, quantity + 1):
            for kit in result.hardware_items:
                if kit.contents and all(c.purchasing_sku is not None for c in kit.contents):
                    for component in kit.contents:
                        source = documentary_sha256_v1({"kind": "hardware_component",
                            "position_id": position, "repetition_index": repetition,
                            "bay_id": kit.bay_id, "leaf_id": kit.leaf_id, "kit_sku": kit.kit_sku,
                            "component": component.model_dump(mode="python")})
                        sources[source] = (position, component.qty * Decimal(kit.qty))
                else:
                    for index in range(1, kit.qty + 1):
                        source = documentary_sha256_v1({"kind": "hardware_kit",
                            "position_id": position, "repetition_index": repetition,
                            "bay_id": kit.bay_id, "leaf_id": kit.leaf_id,
                            "technical_kit_sku": kit.kit_sku, "kit_index": index})
                        sources[source] = (position, Decimal(1))
        for fitting in fitting_selections_v1(result.fittings, quantity):
            for index in range(1, fitting.quantity + 1):
                source = documentary_sha256_v1({"kind": "fitting", "position_id": position,
                    "repetition_index": fitting.repetition_index, "bay_id": fitting.bay_id,
                    "leaf_id": fitting.leaf_id, "technical_sku": fitting.technical_sku,
                    "fitting_kind": fitting.kind, "unit_index": index})
                sources[source] = (position, Decimal(1))
    for position in snapshot.get("positions") or []:
        for accessory in (position.get("accessory_schedule") or {}).get("items") or []:
            for repetition in range(1, int(position["quantity"]) + 1):
                for index in range(1, int(accessory["quantity_per_position_unit"]) + 1):
                    source = documentary_sha256_v1({"kind": "accessory",
                        "position_id": str(position["id"]), "repetition_index": repetition,
                        "obligation_id": accessory["obligation_id"], "unit_index": index})
                    sources[source] = (str(position["id"]), Decimal(1))
    return sources
