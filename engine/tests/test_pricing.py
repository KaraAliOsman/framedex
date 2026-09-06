from decimal import Decimal

import pytest

from dekopen_engine.pricing import gross_margin_pct, price_from_cost_and_margin

D = Decimal


def test_gross_margin_primitives_use_decimal_half_up() -> None:
    assert price_from_cost_and_margin(D("100000.00"), D("0.3500")) == D("153846.15")
    assert gross_margin_pct(D("100000.00"), D("153846.15")) == D("0.3500")
    assert price_from_cost_and_margin(D("1.005"), D("0")) == D("1.01")
    assert gross_margin_pct(D("0.66665"), D("1")) == D("0.3334")
    assert price_from_cost_and_margin(D("0"), D("0.50")) == D("0.00")
    assert gross_margin_pct(D("2"), D("1")) == D("-1.0000")


@pytest.mark.parametrize("cost,margin", [("-1", "0.35"), ("1", "1"), ("1", "-0.01"), ("1", "1.01"), ("NaN", "0.35"), ("1", "Infinity")])
def test_invalid_cost_or_margin_fails(cost: str, margin: str) -> None:
    with pytest.raises(ValueError):
        price_from_cost_and_margin(D(cost), D(margin))


@pytest.mark.parametrize("cost,price", [("1", "0"), ("-1", "1"), ("1", "-1"), ("1", "NaN")])
def test_invalid_gross_margin_fails(cost: str, price: str) -> None:
    with pytest.raises(ValueError):
        gross_margin_pct(D(cost), D(price))
