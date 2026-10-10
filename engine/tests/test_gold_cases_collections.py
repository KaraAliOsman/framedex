import json
from datetime import date
from decimal import Decimal as D
from pathlib import Path

import pytest

from dekopen_engine.collections import CollectionPayment, PaymentMilestone, collection_summary, credit_split
from engine.tests.collection_cases import public_cases


def test_collection_golden() -> None:
    assert public_cases() == json.loads(Path(__file__).with_name("golden_collections.json").read_text())


def test_exact_schedule_conservation_and_declared_date_precedence() -> None:
    result = collection_summary(total=D("1001"), currency="CLP",
        milestones=[PaymentMilestone("Anticipo", D("0.5"), date(2026, 10, 12), "APPROVAL"),
                    PaymentMilestone("Saldo", D("0.5"), due_event="DELIVERY")],
        payments=[CollectionPayment("a", D("100"))], today=date(2026, 10, 10),
        approval_on=date(2026, 10, 1))
    assert result.balance is not None
    assert result.collected + result.balance == result.total
    assert sum(item.amount for item in result.milestones) == result.total
    assert result.milestones[0].amount == D("501")
    assert result.milestones[1].amount == D("500")
    assert result.milestones[0].due_source == "DECLARED"
    assert result.overdue == 0
    assert result.milestones[1].due_on is None
    assert result.percent == D("10.0")


def test_partial_credit_rounds_net_and_preserves_tax() -> None:
    net, tax = credit_split(gross=D("1190"), net=D("1000"), credit=D("1"), currency="CLP")
    assert net + tax == D("1")
    assert (net, tax) == (D("1"), D("0"))
    with pytest.raises(ValueError):
        credit_split(gross=D("1190"), net=D("1000"), credit=D("1191"), currency="CLP")
