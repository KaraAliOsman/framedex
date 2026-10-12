from decimal import Decimal as D

import pytest

from dekopen_engine.commercial import PricingError
from dekopen_engine.quotation import payment_amounts, quotation_line, quotation_summary


@pytest.mark.parametrize("currency,amount", [("CLP", "10001"), ("USD", "100.01")])
def test_sealed_net_and_payment_total_survive_indivisible_units(currency: str, amount: str) -> None:
    net = D(amount)
    line = quotation_line(quantity=3, net=net, currency=currency)
    assert line.unit_net * line.quantity + line.adjustment == net
    assert sum(payment_amounts(net, [D("0.33"), D("0.33"), D("0.34")], currency)) == net
    assert quotation_summary([line], net).before_discount is None


def test_missing_original_price_never_fabricates_a_discount_amount() -> None:
    line = quotation_line(quantity=2, net=D("1000"), currency="CLP", discount=D("0.10"))
    assert line.before_discount is None
    assert quotation_summary([line], D("1000")).discount is None


@pytest.mark.parametrize("parts", [[D("0.4"), D("0.5")], [D("0"), D("1")], [D("-0.1"), D("1.1")]])
def test_incomplete_or_invalid_calendar_is_rejected(parts: list[D]) -> None:
    with pytest.raises(PricingError):
        payment_amounts(D("1000"), parts, "CLP")


def test_no_discount_does_not_invent_currency_rounding_as_discount() -> None:
    line = quotation_line(quantity=3, net=D("10001"), original_unit=D("3333.6667"), currency="CLP")
    assert quotation_summary([line], D("10001")).discount == D("0")
