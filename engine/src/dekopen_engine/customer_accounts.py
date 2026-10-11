"""Exact account totals; currencies and unknown agreements never mix."""

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal, localcontext

from dekopen_engine.collections import CollectionPayment, CollectionSummary


@dataclass(frozen=True)
class CustomerAccount:
    currency: str
    total: Decimal
    collected: Decimal
    balance: Decimal
    simulated_collected: Decimal
    projects: int


def customer_accounts(
    entries: Sequence[tuple[str, CollectionSummary, Sequence[CollectionPayment]]],
) -> tuple[CustomerAccount, ...]:
    """Include only agreements with authority; expose unknowns separately in UI."""
    groups: dict[str, list[tuple[CollectionSummary, Sequence[CollectionPayment]]]] = {}
    for currency, summary, payments in entries:
        if summary.total is not None and summary.balance is not None:
            groups.setdefault(currency, []).append((summary, payments))
    with localcontext() as context:
        context.prec = 80
        zero = Decimal("0")
        return tuple(
            CustomerAccount(
                currency,
                sum((summary.total for summary, _ in group if summary.total is not None), zero),
                sum((summary.collected for summary, _ in group), zero),
                sum((summary.balance for summary, _ in group if summary.balance is not None), zero),
                sum(
                    (
                        p.amount
                        for _, payments in group
                        for p in payments
                        if p.active and p.simulated
                    ),
                    zero,
                ),
                len(group),
            )
            for currency, group in sorted(groups.items())
        )
