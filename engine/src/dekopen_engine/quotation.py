"""Read projections of sealed selling prices and declared payment milestones.

No repricing: a line's sealed net and a revision's sealed totals always win.
The unit display may need a visible currency adjustment for indivisible cents.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal, localcontext

from dekopen_engine.commercial import PricingError, fraction, number, quantize_currency

ZERO = Decimal("0")
ONE = Decimal("1")


@dataclass(frozen=True)
class QuotationLine:
    quantity: int
    net: Decimal
    unit_net: Decimal
    adjustment: Decimal
    before_discount: Decimal | None


def quotation_line(
    *, quantity: int, net: Decimal, currency: str,
    original_unit: Decimal | None = None, discount: Decimal = ZERO,
) -> QuotationLine:
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
        raise PricingError("invalid_positions")
    number(net)
    fraction(discount)
    with localcontext() as context:
        context.prec = 80
        unit = quantize_currency(net / quantity, currency)
        before = None
        if original_unit is not None:
            before = quantize_currency(number(original_unit) * quantity, currency)
            # Allocation and four-decimal historical unit presentation can
            # differ by one currency unit. Zero discount never invents one.
            if discount == ZERO:
                before = net
            elif before < net:
                raise PricingError("quotation_price_authority_inconsistent")
        return QuotationLine(quantity, net, unit, net - unit * quantity, before)


@dataclass(frozen=True)
class QuotationSummary:
    net: Decimal
    before_discount: Decimal | None
    discount: Decimal | None


def quotation_summary(lines: Sequence[QuotationLine], sealed_net: Decimal) -> QuotationSummary:
    number(sealed_net)
    with localcontext() as context:
        context.prec = 80
        if any(line.before_discount is None for line in lines):
            return QuotationSummary(sealed_net, None, None)
        line_net = sum((line.net for line in lines), ZERO)
        if line_net > sealed_net:
            raise PricingError("quotation_price_authority_inconsistent")
        before = sum((line.before_discount or ZERO for line in lines), ZERO) + sealed_net - line_net
        return QuotationSummary(sealed_net, before, before - sealed_net)


def payment_amounts(total: Decimal, proportions: Sequence[Decimal], currency: str) -> tuple[Decimal, ...]:
    """Allocate rounding to the last declared milestone; sum stays exact."""
    number(total)
    if not proportions:
        return ()
    for proportion in proportions:
        fraction(proportion)
        if proportion == ZERO:
            raise PricingError("payment_schedule_invalid")
    with localcontext() as context:
        context.prec = 80
        if sum(proportions, ZERO) != ONE:
            raise PricingError("payment_schedule_invalid")
        amounts = [quantize_currency(total * value, currency) for value in proportions[:-1]]
        remainder = total - sum(amounts, ZERO)
        if remainder < ZERO:
            raise PricingError("payment_schedule_rounding_invalid")
        return (*amounts, remainder)


def representative_index(dimensions: Sequence[tuple[Decimal, Decimal]]) -> int:
    if not dimensions:
        raise PricingError("invalid_positions")
    for width, height in dimensions:
        number(width, positive=True)
        number(height, positive=True)
    with localcontext() as context:
        context.prec = 80
        return max(range(len(dimensions)), key=lambda index: dimensions[index][0] * dimensions[index][1])


@dataclass(frozen=True)
class GrossQuotationInput:
    key: str
    quantity: int
    net: Decimal


@dataclass(frozen=True)
class GrossQuotationLine:
    key: str
    quantity: int
    net: Decimal
    gross: Decimal
    unit_gross: Decimal
    unit_adjustment: Decimal


@dataclass(frozen=True)
class GrossQuotation:
    lines: tuple[GrossQuotationLine, ...]
    sealed_gross: Decimal
    display_gross: Decimal
    rounding_adjustment: Decimal


def gross_quotation(
    entries: Sequence[GrossQuotationInput], *, currency: str,
    sealed_net: Decimal, sealed_tax: Decimal, sealed_gross: Decimal,
) -> GrossQuotation:
    """Distribute the sealed tax without repricing or assuming a tax rate.

    Positions, services and declared charges remain separate selling lines.
    Currency rounding is explicit at unit and document level. Fractional
    historical amounts keep their exact debt; the display never rewrites it.
    """
    number(sealed_net)
    number(sealed_tax)
    number(sealed_gross)
    display_gross = quantize_currency(sealed_gross, currency)
    if not entries:
        raise PricingError("quotation_lines_incomplete")
    keys: set[str] = set()
    for entry in entries:
        if (not isinstance(entry.key, str) or not entry.key.strip() or entry.key in keys
            or isinstance(entry.quantity, bool) or not isinstance(entry.quantity, int)
            or entry.quantity < 1):
            raise PricingError("invalid_positions")
        keys.add(entry.key)
        number(entry.net)
    with localcontext() as context:
        context.prec = 80
        if (sum((entry.net for entry in entries), ZERO) != sealed_net
            or sealed_net + sealed_tax != sealed_gross
            or (sealed_net == ZERO and sealed_tax != ZERO)):
            raise PricingError("quotation_price_authority_inconsistent")
        lines = []
        for entry in entries:
            tax = sealed_tax * entry.net / sealed_net if sealed_net else ZERO
            gross = quantize_currency(entry.net + tax, currency)
            unit = quantize_currency(gross / entry.quantity, currency)
            lines.append(GrossQuotationLine(entry.key, entry.quantity, entry.net, gross,
                                           unit, gross - unit * entry.quantity))
        return GrossQuotation(tuple(lines), sealed_gross, display_gross,
                              display_gross - sum((line.gross for line in lines), ZERO))
