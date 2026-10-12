from dataclasses import asdict
from datetime import date
from decimal import Decimal as D
from collections.abc import Sequence
from typing import Any

from dekopen_engine.collections import CollectionPayment, PaymentMilestone, collection_summary, credit_split


def collection_cases() -> dict[str, object]:
    milestones = [PaymentMilestone("Anticipo", D("0.5"), due_event="APPROVAL"),
                  PaymentMilestone("Saldo", D("0.5"), due_event="DELIVERY")]
    def summary(total: D | None, payments: Sequence[CollectionPayment] = (),
                approval_on: date | None = None, delivery_on: date | None = None) -> dict[str, object]:
        return asdict(collection_summary(total=total, currency="CLP", milestones=milestones,
            payments=payments, today=date(2026, 10, 10), approval_on=approval_on, delivery_on=delivery_on))
    return {
        "odd_clp_pending": summary(D("1001")),
        "overdue_approval": summary(D("1001"), approval_on=date(2026, 10, 1)),
        "deposit_received": summary(D("1001"), [CollectionPayment("deposit", D("501"))],
                                    approval_on=date(2026, 10, 1)),
        "simulated_balance": summary(D("1001"), [CollectionPayment("deposit", D("501")),
                                      CollectionPayment("flow", D("500"), simulated=True)]),
        "void_ignored": summary(D("1001"), [CollectionPayment("void", D("501"), active=False)]),
        "provider_excess": summary(D("1001"), [CollectionPayment("real", D("1100"))]),
        "no_deal": summary(None),
        "partial_credit": credit_split(gross=D("1190"), net=D("1000"), credit=D("357"), currency="CLP"),
    }


def public_cases() -> Any:
    def encode(value: Any) -> Any:
        if isinstance(value, (D, date)):
            return str(value)
        if isinstance(value, dict):
            return {key: encode(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [encode(item) for item in value]
        return value
    return encode(collection_cases())
