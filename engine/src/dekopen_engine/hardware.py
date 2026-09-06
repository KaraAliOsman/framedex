"""Deterministic kit selection against finished dimensions and exact mass."""

from decimal import Decimal

from dekopen_engine.models import BayOpeningType, HardwareKitRule, SystemParams
from dekopen_engine.weight import ExactLeafWeight, with_hardware_weight


class NoCompatibleHardwareKit(ValueError):
    pass


class AmbiguousHardwareKit(ValueError):
    pass


def normalize_opening_type(opening: BayOpeningType) -> str:
    if opening in (BayOpeningType.TURN_LEFT, BayOpeningType.TURN_RIGHT):
        return "TURN"
    if opening in (BayOpeningType.TILT_TURN_LEFT, BayOpeningType.TILT_TURN_RIGHT):
        return "TILT_TURN"
    if opening in (BayOpeningType.SLIDING_2L, BayOpeningType.SLIDING_3L,
                   BayOpeningType.SLIDING_4L):
        return "SLIDING"
    if opening in (BayOpeningType.DOOR_ENTRY, BayOpeningType.DOOR_DOUBLE):
        return "DOOR"
    return opening.value


def resolve_hardware_kit(
    *, opening: BayOpeningType, width_mm: Decimal, height_mm: Decimal,
    base_weight: ExactLeafWeight, params: SystemParams, explicit_sku: str | None = None,
) -> tuple[HardwareKitRule, ExactLeafWeight]:
    candidates: list[tuple[HardwareKitRule, ExactLeafWeight]] = []
    for kit in params.available_hardware_kits:
        if explicit_sku is not None and kit.sku != explicit_sku:
            continue
        if not (
            kit.opening_type == normalize_opening_type(opening)
            and kit.min_leaf_width_mm <= width_mm <= kit.max_leaf_width_mm
            and kit.min_leaf_height_mm <= height_mm <= kit.max_leaf_height_mm
            and kit.rail_type is params.rail_type
        ):
            continue
        exact = with_hardware_weight(base_weight, kit, params)
        if exact.total_weight_kg <= kit.max_leaf_weight_kg:
            candidates.append((kit, exact))
    if not candidates:
        raise NoCompatibleHardwareKit(f"No compatible hardware kit: {explicit_sku or opening.value}")
    if len(candidates) != 1:
        raise AmbiguousHardwareKit(f"Ambiguous hardware kits: {opening.value}")
    return candidates[0]
