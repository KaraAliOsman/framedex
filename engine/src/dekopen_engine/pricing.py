"""Pure gross-margin primitives; commercial pricing belongs to SHOT-08."""

from decimal import ROUND_HALF_UP, Decimal


def _require_nonnegative(value: Decimal) -> None:
    if not isinstance(value, Decimal) or not value.is_finite() or value < Decimal("0"):
        raise ValueError("Expected a finite non-negative Decimal")


def price_from_cost_and_margin(direct_cost: Decimal, margin_pct: Decimal) -> Decimal:
    _require_nonnegative(direct_cost)
    _require_nonnegative(margin_pct)
    if margin_pct >= Decimal("1"):
        raise ValueError("Margin must be less than one")
    return (direct_cost / (Decimal("1") - margin_pct)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP,
    )


def gross_margin_pct(cost: Decimal, price: Decimal) -> Decimal:
    _require_nonnegative(cost)
    _require_nonnegative(price)
    if price == Decimal("0"):
        raise ValueError("Gross margin is undefined for zero price")
    return ((price - cost) / price).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
