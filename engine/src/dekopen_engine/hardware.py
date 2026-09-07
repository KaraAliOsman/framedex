"""Deterministic kit selection against finished dimensions and exact mass."""

from decimal import Decimal
from dataclasses import dataclass

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


@dataclass(frozen=True, slots=True)
class HardwareCandidateEvaluation:
    kit: HardwareKitRule
    opening_match: bool
    rail_match: bool
    width_match: bool
    height_match: bool
    exact_total_weight: ExactLeafWeight
    weight_match: bool

    @property
    def compatible(self) -> bool:
        return (self.opening_match and self.rail_match and self.width_match
                and self.height_match and self.weight_match)


def evaluate_hardware_candidates(
    *, opening: BayOpeningType, width_mm: Decimal, height_mm: Decimal,
    base_weight: ExactLeafWeight, params: SystemParams, explicit_sku: str | None = None,
) -> list[HardwareCandidateEvaluation]:
    candidates: list[HardwareCandidateEvaluation] = []
    for kit in params.available_hardware_kits:
        if explicit_sku is not None and kit.sku != explicit_sku:
            continue
        exact = with_hardware_weight(base_weight, kit, params)
        candidates.append(HardwareCandidateEvaluation(
            kit=kit, opening_match=kit.opening_type == normalize_opening_type(opening),
            rail_match=kit.rail_type is params.rail_type,
            width_match=kit.min_leaf_width_mm <= width_mm <= kit.max_leaf_width_mm,
            height_match=kit.min_leaf_height_mm <= height_mm <= kit.max_leaf_height_mm,
            exact_total_weight=exact, weight_match=exact.total_weight_kg <= kit.max_leaf_weight_kg,
        ))
    return candidates


def resolve_hardware_evaluations(
    evaluations: list[HardwareCandidateEvaluation], *, opening: BayOpeningType,
    explicit_sku: str | None = None,
) -> tuple[HardwareKitRule, ExactLeafWeight]:
    candidates = [candidate for candidate in evaluations if candidate.compatible]
    if not candidates:
        raise NoCompatibleHardwareKit(f"No compatible hardware kit: {explicit_sku or opening.value}")
    if len(candidates) != 1:
        raise AmbiguousHardwareKit(f"Ambiguous hardware kits: {opening.value}")
    return candidates[0].kit, candidates[0].exact_total_weight


def resolve_hardware_kit(
    *, opening: BayOpeningType, width_mm: Decimal, height_mm: Decimal,
    base_weight: ExactLeafWeight, params: SystemParams, explicit_sku: str | None = None,
) -> tuple[HardwareKitRule, ExactLeafWeight]:
    return resolve_hardware_evaluations(evaluate_hardware_candidates(
        opening=opening, width_mm=width_mm, height_mm=height_mm, base_weight=base_weight,
        params=params, explicit_sku=explicit_sku,
    ), opening=opening, explicit_sku=explicit_sku)
