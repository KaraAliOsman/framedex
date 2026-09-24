"""Panel geometry and mass use panel catalog authority, never glass density."""

from decimal import ROUND_HALF_UP, Decimal

from dekopen_engine.models import PanelPiece, PanelRule


def exact_panel_weight(width_mm: Decimal, height_mm: Decimal, rule: PanelRule) -> Decimal | None:
    """Exact panel mass, or None when the catalog declares no areal density."""
    if rule.weight_kg_m2 is None:
        return None
    if width_mm <= Decimal("0") or height_mm <= Decimal("0"):
        raise ValueError("Panel dimensions must be positive")
    return width_mm * height_mm / Decimal("1000000") * rule.weight_kg_m2


def build_panel_piece(
    *, bay_id: str, leaf_id: str | None, width_mm: Decimal, height_mm: Decimal,
    rule: PanelRule,
) -> PanelPiece:
    exact_weight = exact_panel_weight(width_mm, height_mm, rule)
    return PanelPiece(
        sku=rule.sku, name=rule.name, bay_id=bay_id, leaf_id=leaf_id,
        width_mm=width_mm, height_mm=height_mm,
        area_m2=(width_mm * height_mm / Decimal("1000000")).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP,
        ),
        weight_kg=None if exact_weight is None else exact_weight.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP,
        ),
    )
