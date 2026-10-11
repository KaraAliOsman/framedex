from datetime import date
from decimal import Decimal as D, localcontext

from dekopen_engine.collections import CollectionPayment, CollectionSummary, collection_summary
from dekopen_engine.customer_accounts import customer_accounts


def entry(
    currency: str, total: D | None, payments: list[CollectionPayment]
) -> tuple[str, CollectionSummary, list[CollectionPayment]]:
    return (
        currency,
        collection_summary(
            total=total,
            currency=currency,
            payments=payments,
            milestones=[],
            today=date(2026, 10, 1),
        ),
        payments,
    )


def test_currencies_unknowns_voids_and_simulation_remain_distinct() -> None:
    entries = [
        entry("CLP", D("100"), [CollectionPayment("one", D("120"), simulated=True)]),
        entry("CLP", D("50"), [CollectionPayment("void", D("500"), active=False)]),
        entry("USD", D("10.01"), [CollectionPayment("two", D("0.01"))]),
        entry("", None, [CollectionPayment("unknown", D("999"))]),
    ]
    accounts = customer_accounts(entries)
    assert [
        (a.currency, a.total, a.collected, a.balance, a.simulated_collected, a.projects)
        for a in accounts
    ] == [
        ("CLP", D("150"), D("120"), D("30"), D("120"), 2),
        ("USD", D("10.01"), D("0.01"), D("10"), D("0"), 1),
    ]
    assert customer_accounts([]) == ()


def test_exact_aggregation_survives_small_caller_context_and_retains_excess() -> None:
    rows = [
        entry("USD", D("999999999999.99"), []),
        entry("USD", D("0.02"), [CollectionPayment("over", D("0.03"))]),
    ]
    with localcontext() as context:
        context.prec = 6
        total = customer_accounts(rows)[0]
    assert total.total == D("1000000000000.01")
    assert total.balance == D("999999999999.98")
    assert customer_accounts([rows[1]])[0].balance == D("-0.01")
