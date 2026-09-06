"""Exact mobile-leaf mass; rounding belongs only to the public result."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from dekopen_engine.models import (
    HardwareKitRule, LeafWeight, MaterialType, ProfileCut, ProfileRole,
    ReinforcementPiece, SystemParams,
)

WEIGHT_FALLBACK_FACTOR = Decimal("1.10")
_KG = Decimal("0.01")
_METRE = Decimal("1000")


class MissingWeightAuthority(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ExactLeafWeight:
    pvc_weight_kg: Decimal
    steel_weight_kg: Decimal
    infill_weight_kg: Decimal
    hardware_weight_kg: Decimal = Decimal("0")
    used_fallback: bool = False

    @property
    def total_weight_kg(self) -> Decimal:
        return (
            self.pvc_weight_kg + self.steel_weight_kg
            + self.infill_weight_kg + self.hardware_weight_kg
        )

    def public_result(self, bay_id: str, leaf_id: str | None) -> LeafWeight:
        return LeafWeight(
            bay_id=bay_id, leaf_id=leaf_id,
            pvc_weight_kg=self.pvc_weight_kg.quantize(_KG, rounding=ROUND_HALF_UP),
            steel_weight_kg=self.steel_weight_kg.quantize(_KG, rounding=ROUND_HALF_UP),
            infill_weight_kg=self.infill_weight_kg.quantize(_KG, rounding=ROUND_HALF_UP),
            hardware_weight_kg=self.hardware_weight_kg.quantize(_KG, rounding=ROUND_HALF_UP),
            total_weight_kg=self.total_weight_kg.quantize(_KG, rounding=ROUND_HALF_UP),
            used_fallback=self.used_fallback,
        )


def base_leaf_weight(
    *, profile_cuts: Sequence[ProfileCut], reinforcements: Sequence[ReinforcementPiece],
    infill_weight_kg: Decimal, params: SystemParams,
) -> ExactLeafWeight:
    """Consume one leaf's cuts; frame, beads and threshold never enter its mass."""
    pvc = Decimal("0")
    steel = Decimal("0")
    used_fallback = False
    for cut in profile_cuts:
        if cut.role is not ProfileRole.SASH:
            continue
        article = params.effective_profile_articles[cut.role]
        if article.sku != cut.sku:
            raise MissingWeightAuthority(f"Missing profile mass authority: {cut.sku}")
        density = article.weight_kg_m
        if density is None:
            if article.material is not MaterialType.PVC:
                raise MissingWeightAuthority(f"Missing non-PVC mass authority: {article.sku}")
            density = params.pvc_weight_kg_m * WEIGHT_FALLBACK_FACTOR
            used_fallback = True
        pvc += cut.length_mm / _METRE * cut.qty * density
    for piece in reinforcements:
        if piece.role is not ProfileRole.SASH:
            continue
        article = params.effective_profile_articles[piece.role]
        if article.sku != piece.parent_profile_sku:
            raise MissingWeightAuthority(f"Missing steel mass authority: {piece.parent_profile_sku}")
        density = article.steel_weight_kg_m
        if density is None:
            density = params.steel_weight_kg_m * WEIGHT_FALLBACK_FACTOR
            used_fallback = True
        steel += piece.length_mm / _METRE * piece.qty * density
    return ExactLeafWeight(pvc, steel, infill_weight_kg, used_fallback=used_fallback)


def with_hardware_weight(
    base: ExactLeafWeight, kit: HardwareKitRule, params: SystemParams,
) -> ExactLeafWeight:
    fallback = kit.weight_kg is None
    weight = (
        params.hardware_kit_weight_kg * WEIGHT_FALLBACK_FACTOR
        if fallback else kit.weight_kg
    )
    assert weight is not None
    return ExactLeafWeight(
        base.pvc_weight_kg, base.steel_weight_kg, base.infill_weight_kg,
        weight, base.used_fallback or fallback,
    )
