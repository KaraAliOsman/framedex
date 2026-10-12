"""Explicit selling-line oracles: tax is sealed, currency and sums are exact."""

from decimal import Decimal as D

import pytest

from dekopen_engine.commercial import PricingError
from dekopen_engine.quotation import GrossQuotationInput as Input, gross_quotation


@pytest.mark.parametrize("currency,scale", [("CLP", D("1")), ("USD", D("0.01"))])
@pytest.mark.parametrize("charges", [False, True])
def test_twelve_positions_and_declared_charges_reconcile(currency: str, scale: D, charges: bool) -> None:
    entries = [Input(f"position-{i}", 3, D("10002") * scale) for i in range(12)]
    if charges:
        entries += [Input("service", 1, D("10000") * scale), Input("charge", 1, D("5000") * scale)]
    net, tax = (D("135024"), D("25655")) if charges else (D("120024"), D("22805"))
    result = gross_quotation(entries, currency=currency, sealed_net=net * scale,
                             sealed_tax=tax * scale, sealed_gross=(net + tax) * scale)
    assert all(line.gross == D("11902") * scale and line.unit_gross == D("3967") * scale
               and line.unit_adjustment == scale for line in result.lines[:12])
    assert result.rounding_adjustment == D("5") * scale
    assert sum((line.gross for line in result.lines), D("0")) + result.rounding_adjustment == result.display_gross
    assert all(line.unit_gross * line.quantity + line.unit_adjustment == line.gross for line in result.lines)


def test_nonstandard_sealed_tax_and_fractional_historical_debt_are_preserved() -> None:
    result = gross_quotation([Input("historical", 1, D("100.1"))], currency="CLP",
                             sealed_net=D("100.1"), sealed_tax=D("7.021"), sealed_gross=D("107.121"))
    assert result.sealed_gross == D("107.121") and result.display_gross == D("107")
    assert result.lines[0].gross == D("107")
    zero = gross_quotation([Input("free-declared", 1, D("0"))], currency="CLP",
                           sealed_net=D("0"), sealed_tax=D("0"), sealed_gross=D("0"))
    assert zero.lines[0].gross == zero.rounding_adjustment == D("0")


@pytest.mark.parametrize("entries,net,tax,gross", [
    ([], "0", "0", "0"), ([Input("x", True, D("1"))], "1", "0", "1"),
    ([Input("x", 0, D("1"))], "1", "0", "1"),
    ([Input("x", 1, D("1")), Input("x", 1, D("1"))], "2", "0", "2"),
    ([Input("x", 1, D("1"))], "2", "0", "2"),
    ([Input("x", 1, D("1"))], "1", "1", "3"),
    ([Input("x", 1, D("0"))], "0", "1", "1"),
    ([Input("x", 1, D("-1"))], "1", "0", "1"),
])
def test_incomplete_or_conflicting_authority_is_rejected(entries: list[Input], net: str, tax: str, gross: str) -> None:
    with pytest.raises(PricingError):
        gross_quotation(entries, currency="CLP", sealed_net=D(net), sealed_tax=D(tax), sealed_gross=D(gross))
