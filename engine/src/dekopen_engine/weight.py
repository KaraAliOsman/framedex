"""Exact mobile-leaf mass; rounding belongs only to the public result.

UNKNOWN is a first-class state: when a catalog authority is missing for a
component the component is None, the total is None, and the reasons say which
authority is missing — no fabricated fallback ever enters a compatibility
decision."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from dekopen_engine.models import (
    FittingPiece, HardwareKitRule, LeafWeight, ProfileCut, ProfileRole,
    ReinforcementPiece, SystemParams,
)

_KG = Decimal("0.01")
_METRE = Decimal("1000")


class MissingWeightAuthority(ValueError):
    pass


class MissingFabricationAuthority(ValueError):
    """A fabrication datum the catalog must declare is absent — refuse with a
    precise reason instead of computing on an invented constant."""


def _accumulate(
    total: Decimal | None, addend: Decimal | None,
) -> Decimal | None:
    if total is None or addend is None:
        return None
    return total + addend


@dataclass(frozen=True, slots=True)
class ExactLeafWeight:
    pvc_weight_kg: Decimal | None
    steel_weight_kg: Decimal | None
    infill_weight_kg: Decimal | None
    hardware_weight_kg: Decimal | None = Decimal("0")
    # Reasons naming the missing authority, e.g.
    # "missing_profile_mass:DEMO-HOJA" — empty when the mass is fully known.
    weight_unknown_reasons: tuple[str, ...] = field(default_factory=tuple)

    @property
    def total_weight_kg(self) -> Decimal | None:
        components = (
            self.pvc_weight_kg, self.steel_weight_kg,
            self.infill_weight_kg, self.hardware_weight_kg,
        )
        if any(component is None for component in components):
            return None
        return sum(
            (component for component in components if component is not None),
            Decimal("0"),
        )

    @staticmethod
    def _quantize(value: Decimal | None) -> Decimal | None:
        return None if value is None else value.quantize(_KG, rounding=ROUND_HALF_UP)

    def public_result(self, bay_id: str, leaf_id: str | None) -> LeafWeight:
        total = self.total_weight_kg
        return LeafWeight(
            bay_id=bay_id, leaf_id=leaf_id,
            pvc_weight_kg=self._quantize(self.pvc_weight_kg),
            steel_weight_kg=self._quantize(self.steel_weight_kg),
            infill_weight_kg=self._quantize(self.infill_weight_kg),
            hardware_weight_kg=self._quantize(self.hardware_weight_kg),
            total_weight_kg=None if total is None else total.quantize(_KG, rounding=ROUND_HALF_UP),
            weight_unknown_reasons=list(self.weight_unknown_reasons),
        )


def base_leaf_weight(
    *, profile_cuts: Sequence[ProfileCut], reinforcements: Sequence[ReinforcementPiece],
    infill_weight_kg: Decimal | None, params: SystemParams,
    infill_unknown_reason: str | None = None,
    fittings: Sequence[FittingPiece] = (),
) -> ExactLeafWeight:
    """Consume one leaf's cuts; frame, beads and threshold never enter its mass."""
    pvc: Decimal | None = Decimal("0")
    steel: Decimal | None = Decimal("0")
    reasons: list[str] = []
    for cut in profile_cuts:
        if cut.role not in (ProfileRole.SASH, ProfileRole.SLIDING_SASH,
                            ProfileRole.DOOR_SASH, ProfileRole.INTERLOCK, ProfileRole.INVERSOR):
            continue
        article = params.effective_profile_articles[cut.role]
        if article.sku != cut.sku:
            raise MissingWeightAuthority(f"Missing profile mass authority: {cut.sku}")
        density = article.weight_kg_m
        if density is None:
            pvc = None
            reason = f"missing_profile_mass:{article.sku}"
            if reason not in reasons:
                reasons.append(reason)
        else:
            pvc = _accumulate(pvc, cut.length_mm / _METRE * cut.qty * density)
    for piece in reinforcements:
        if piece.role not in (ProfileRole.SASH, ProfileRole.SLIDING_SASH,
                              ProfileRole.DOOR_SASH, ProfileRole.INTERLOCK, ProfileRole.INVERSOR):
            continue
        article = params.effective_profile_articles[piece.role]
        if article.sku != piece.parent_profile_sku:
            raise MissingWeightAuthority(f"Missing steel mass authority: {piece.parent_profile_sku}")
        density = article.steel_weight_kg_m
        if density is None:
            steel = None
            reason = f"missing_steel_mass:{article.sku}"
            if reason not in reasons:
                reasons.append(reason)
        else:
            steel = _accumulate(steel, piece.length_mm / _METRE * piece.qty * density)
    if infill_weight_kg is None:
        reasons.append(infill_unknown_reason or "missing_infill_mass")
    screws: Decimal | None = Decimal("0")
    for fitting in fittings:
        rules = [article.reinforcement_rule for article in params.effective_profile_articles.values()
                 if article.reinforcement_rule is not None
                 and article.reinforcement_rule.screw_sku == fitting.sku]
        masses = {rule.screw_weight_kg for rule in rules}
        if len(masses) != 1 or None in masses:
            screws = None
            reasons.append(f"missing_screw_mass:{fitting.sku}")
        else:
            mass = next(iter(masses))
            assert mass is not None
            screws = _accumulate(screws, mass * fitting.qty)
    return ExactLeafWeight(pvc, steel, infill_weight_kg, screws,
                           weight_unknown_reasons=tuple(reasons))


def with_hardware_weight(
    base: ExactLeafWeight, kit: HardwareKitRule, params: SystemParams,
) -> ExactLeafWeight:
    if kit.weight_kg is None:
        return ExactLeafWeight(
            base.pvc_weight_kg, base.steel_weight_kg, base.infill_weight_kg,
            None,
            base.weight_unknown_reasons + (f"missing_hardware_mass:{kit.sku}",),
        )
    return ExactLeafWeight(
        base.pvc_weight_kg, base.steel_weight_kg, base.infill_weight_kg,
        _accumulate(base.hardware_weight_kg, kit.weight_kg), base.weight_unknown_reasons,
    )
