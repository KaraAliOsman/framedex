from datetime import date
from decimal import Decimal, localcontext
from typing import Any

from dekopen_engine.work_queue import consequence, money_sum, outstanding, queue_order


def test_balance_preserves_small_receipts_and_large_sale_exactly() -> None:
    total = Decimal("123456789012345678901234567890.123456789")
    receipts = [Decimal(".000000001"), Decimal(".000000009")]
    with localcontext() as context:
        context.prec = 6
        collected = money_sum(receipts)
        assert collected == Decimal(".000000010")
        assert outstanding(total, collected) == Decimal("123456789012345678901234567890.123456779")
        assert outstanding(Decimal("12.50"), Decimal("13")) == Decimal("0")


def test_consequence_and_stable_order_prioritize_overdue_before_blockers() -> None:
    today = date(2026, 10, 9)
    assert consequence(date(2026, 10, 8), today=today, blocking=True) == "overdue"
    assert consequence(None, today=today, blocking=True) == "blocking"
    assert consequence(today, today=today, blocking=False) == "today"
    actions: list[dict[str, Any]] = [
        {"key": "viewed:P-2", "entity_code": "P-2", "due_on": None},
        {"key": "blocked:OT-2", "entity_code": "OT-2", "blocking": True},
        {"key": "due:OT-1", "entity_code": "OT-1", "due_on": "2026-10-08"},
        {"key": "due:P-1", "entity_code": "P-1", "due_on": "2026-10-09"},
    ]
    expected = ["due:OT-1", "blocked:OT-2", "due:P-1", "viewed:P-2"]
    assert [row["key"] for row in queue_order(actions, today=today)] == expected
    assert [row["key"] for row in queue_order(reversed(actions), today=today)] == expected
    assert "consequence" not in actions[0]
