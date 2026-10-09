"""Pure read projections for the daily work queue; no repricing or I/O."""

from collections.abc import Iterable, Mapping
from datetime import date
from decimal import Decimal, localcontext
from typing import Any

from dekopen_engine.commercial import number


def money_sum(values: Iterable[Decimal]) -> Decimal:
    with localcontext() as context:
        context.prec = 256
        return sum((number(value) for value in values), Decimal("0"))


def outstanding(total: Decimal, collected: Decimal) -> Decimal:
    """A credit is not a receivable; do not hide it in the source ledger."""
    with localcontext() as context:
        context.prec = 256
        return max(Decimal("0"), number(total) - number(collected))


def consequence(due_on: date | None, *, today: date, blocking: bool) -> str:
    if due_on is not None and due_on < today:
        return "overdue"
    if blocking:
        return "blocking"
    if due_on is not None and due_on <= today:
        return "today"
    return "follow_up"


def queue_order(actions: Iterable[Mapping[str, Any]], *, today: date) -> list[Mapping[str, Any]]:
    """Past commitments, downstream blockers, today's work, then follow-up.

    Money never ranks one currency against another. Stable entity addresses
    break ties, so equal inputs produce the same queue on every refresh.
    """
    ranks = {"overdue": 0, "blocking": 1, "today": 2, "follow_up": 3}

    def key(action: Mapping[str, Any]) -> tuple[int, date, str, str]:
        due = date.fromisoformat(action["due_on"]) if action.get("due_on") else None
        tier = consequence(due, today=today, blocking=bool(action.get("blocking")))
        return ranks[tier], due or date.max, str(action["entity_code"]), str(action["key"])

    return sorted(actions, key=key)
