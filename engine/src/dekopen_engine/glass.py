"""Pure Decimal-only glass thickness, area, and weight calculations.

Composition is the only mass authority: the net thickness comes from the
declared pane composition in `glass_spec`, never from the glazing package
thickness. A spec the parser cannot establish a composition from returns
UNKNOWN (None) — treating the package as monolithic glass would fabricate a
mass several times the real one."""

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


def derive_net_glass_thickness(glass_spec: str) -> Decimal | None:
    """Sum glass panes only; the DVH chamber never contributes to net thickness.

    Returns None when the composition cannot be established — the caller must
    surface UNKNOWN rather than substitute the package thickness."""

    parts = [part.strip() for part in glass_spec.strip().split("-")]
    # "4-16-4" and "4-16-4-16-4": panes sit at even indices, chambers between
    # them. Every pane must parse for a composition to be established — a
    # partial read would silently undercount the mass.
    if len(parts) >= 3 and len(parts) % 2 == 1:
        panes = [
            _parse_pane_thickness(parts[index].split()[0] if parts[index] else "")
            for index in range(0, len(parts), 2)
        ]
        if all(pane is not None for pane in panes):
            return sum((pane for pane in panes if pane is not None), start=Decimal("0"))

    if len(parts) == 1:
        match = _MONOLITHIC_PREFIX.match(glass_spec.strip())
        if match is not None:
            return Decimal(match.group(0))

    return None


def exact_glass_area_m2(width_mm: Decimal, height_mm: Decimal) -> Decimal:
    """Return unquantized area; downstream weight calculations consume this value."""

    return (width_mm * height_mm) / _SQUARE_MILLIMETRES_PER_SQUARE_METRE


def exact_glass_weight(
    width_mm: Decimal, height_mm: Decimal, glass_spec: str,
) -> Decimal | None:
    """Exact mass, or None when the composition authority is unreadable."""
    if width_mm <= Decimal("0") or height_mm <= Decimal("0"):
        raise ValueError("Glass dimensions must be positive")
    net = derive_net_glass_thickness(glass_spec)
    if net is None:
        return None
    return exact_glass_area_m2(width_mm, height_mm) * net * GLASS_WEIGHT_FACTOR_KG_M2_PER_MM


def build_glass_piece(
    *,
    bay_id: str,
    leaf_id: str | None = None,
    width_mm: Decimal,
    height_mm: Decimal,
    glass_spec: str,
    article_sku: str | None = None,
) -> GlassPiece:
    """Build the public glass result while avoiding any double rounding."""

    thickness_net_exact_mm = derive_net_glass_thickness(glass_spec)
    area_m2_exact = exact_glass_area_m2(width_mm, height_mm)
    weight_kg_exact = exact_glass_weight(width_mm, height_mm, glass_spec)

    return GlassPiece(
        bay_id=bay_id,
        leaf_id=leaf_id,
        width_mm=width_mm,
        height_mm=height_mm,
        area_m2=area_m2_exact.quantize(_AREA_OUTPUT_QUANTUM, rounding=ROUND_HALF_UP),
        weight_kg=(
            None if weight_kg_exact is None
            else weight_kg_exact.quantize(_WEIGHT_OUTPUT_QUANTUM, rounding=ROUND_HALF_UP)
        ),
        thickness_net_mm=(
            None if thickness_net_exact_mm is None
            else thickness_net_exact_mm.quantize(_THICKNESS_OUTPUT_QUANTUM, rounding=ROUND_HALF_UP)
        ),
        glass_spec=glass_spec,
        article_sku=article_sku,
    )
