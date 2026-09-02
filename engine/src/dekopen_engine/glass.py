"""Pure Decimal-only glass thickness, area, and weight calculations."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
import re

from dekopen_engine.models import GlassPiece

FLOAT_GLASS_DENSITY_KG_M3 = Decimal("2500")
GLASS_WEIGHT_FACTOR_KG_M2_PER_MM = Decimal("2.50")

_AREA_OUTPUT_QUANTUM = Decimal("0.0001")
_WEIGHT_OUTPUT_QUANTUM = Decimal("0.01")
_THICKNESS_OUTPUT_QUANTUM = Decimal("0.01")
_SQUARE_MILLIMETRES_PER_SQUARE_METRE = Decimal("1000000")
_MONOLITHIC_PREFIX = re.compile(r"^\d+(?:\.\d+)?")
_PANE_TOKEN = re.compile(r"^\d+(?:\.\d+)?$")


def _parse_pane_thickness(pane: str) -> Decimal | None:
    components = pane.split("+")
    if not components or any(_PANE_TOKEN.fullmatch(part) is None for part in components):
        return None
    return sum((Decimal(part) for part in components), start=Decimal("0"))


def derive_net_glass_thickness(
    glass_spec: str,
    fallback_thickness: Decimal,
) -> Decimal:
    """Sum glass panes only; the DVH chamber never contributes to net thickness."""

    parts = [part.strip() for part in glass_spec.strip().split("-")]
    if len(parts) >= 3:
        first_token = parts[0].split()[0] if parts[0] else ""
        third_token = parts[2].split()[0] if parts[2] else ""
        first_pane = _parse_pane_thickness(first_token)
        third_pane = _parse_pane_thickness(third_token)
        if first_pane is not None and third_pane is not None:
            return first_pane + third_pane

    if len(parts) == 1:
        match = _MONOLITHIC_PREFIX.match(glass_spec.strip())
        if match is not None:
            return Decimal(match.group(0))

    return fallback_thickness


def exact_glass_area_m2(width_mm: Decimal, height_mm: Decimal) -> Decimal:
    """Return unquantized area; downstream weight calculations consume this value."""

    return (width_mm * height_mm) / _SQUARE_MILLIMETRES_PER_SQUARE_METRE


def build_glass_piece(
    *,
    bay_id: str,
    width_mm: Decimal,
    height_mm: Decimal,
    glass_spec: str,
    fallback_thickness_mm: Decimal,
) -> GlassPiece:
    """Build the public glass result while avoiding any double rounding."""

    thickness_net_exact_mm = derive_net_glass_thickness(
        glass_spec,
        fallback_thickness_mm,
    )
    area_m2_exact = exact_glass_area_m2(width_mm, height_mm)
    weight_kg_exact = (
        area_m2_exact
        * thickness_net_exact_mm
        * GLASS_WEIGHT_FACTOR_KG_M2_PER_MM
    )

    return GlassPiece(
        bay_id=bay_id,
        width_mm=width_mm,
        height_mm=height_mm,
        area_m2=area_m2_exact.quantize(_AREA_OUTPUT_QUANTUM, rounding=ROUND_HALF_UP),
        weight_kg=weight_kg_exact.quantize(
            _WEIGHT_OUTPUT_QUANTUM,
            rounding=ROUND_HALF_UP,
        ),
        thickness_net_mm=thickness_net_exact_mm.quantize(
            _THICKNESS_OUTPUT_QUANTUM,
            rounding=ROUND_HALF_UP,
        ),
    )
