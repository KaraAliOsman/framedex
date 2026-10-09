from dataclasses import asdict
from decimal import Decimal as D

from dekopen_engine.quotation import payment_amounts, quotation_line, quotation_summary


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
    return cases
