from dataclasses import asdict
from decimal import Decimal as D

from dekopen_engine.quotation import (
    GrossQuotationInput, gross_quotation, payment_amounts, quotation_line, quotation_summary,
)


def quotation_cases() -> dict[str, object]:
    cases: dict[str, object] = {}
    for currency, net, unit, total in [("CLP", "10001", "3704", "11901"), ("USD", "100.01", "37.04", "119.01")]:
        line = quotation_line(quantity=3, net=D(net), currency=currency, original_unit=D(unit), discount=D("0.10"))
        summary = quotation_summary([line], D(net))
        cases[currency] = {
            "line": {key: str(value) if isinstance(value, D) else value for key, value in asdict(line).items()},
            "summary": {key: str(value) if isinstance(value, D) else value for key, value in asdict(summary).items()},
            "payments": [str(value) for value in payment_amounts(D(total), [D("0.50"), D("0.50")], currency)],
        }
    for currency, scale in [("CLP", D("1")), ("USD", D("0.01"))]:
        for with_charges in (False, True):
            entries = [GrossQuotationInput(f"position-{index}", 3, D("10002") * scale)
                       for index in range(12)]
            if with_charges:
                entries += [GrossQuotationInput("service", 1, D("10000") * scale),
                            GrossQuotationInput("charge", 1, D("5000") * scale)]
            gross_net = D("135024" if with_charges else "120024") * scale
            tax = D("25655" if with_charges else "22805") * scale
            value = gross_quotation(entries, currency=currency, sealed_net=gross_net,
                                   sealed_tax=tax, sealed_gross=gross_net + tax)
            cases[f"gross_{currency}_{'services' if with_charges else 'positions'}"] = {
                "lines": [{key: str(item) if isinstance(item, D) else item
                           for key, item in asdict(line).items()} for line in value.lines],
                "sealed_gross": str(value.sealed_gross),
                "display_gross": str(value.display_gross),
                "rounding_adjustment": str(value.rounding_adjustment),
            }
    return cases
