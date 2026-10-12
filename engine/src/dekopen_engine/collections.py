"""Pure projections of a sealed agreement and its immutable collection ledger."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, localcontext

from dekopen_engine.commercial import number, quantize_currency
from dekopen_engine.quotation import payment_amounts

ZERO = Decimal("0")


@dataclass(frozen=True)
class PaymentMilestone:
    label: str
    share: Decimal
    due_on: date | None = None
    due_event: str | None = None


@dataclass(frozen=True)
class CollectionPayment:
    identity: str
    amount: Decimal
    active: bool = True
    simulated: bool = False


@dataclass(frozen=True)
class CollectionMilestone:
    label: str
    share: Decimal
    amount: Decimal
    collected: Decimal
    remaining: Decimal
    due_on: date | None
    due_source: str
    status: str


@dataclass(frozen=True)
class CollectionSummary:
    total: Decimal | None
    collected: Decimal
    balance: Decimal | None
    excess: Decimal
    percent: Decimal | None
    overdue: Decimal
    oldest_due_on: date | None
    status: str
    milestones: tuple[CollectionMilestone, ...]
    includes_simulation: bool


def credit_split(*, gross: Decimal, net: Decimal, credit: Decimal, currency: str) -> tuple[Decimal, Decimal]:
    """Allocate an explicit partial gross credit; its net+tax stays exact."""
    number(gross, positive=True)
    number(net)
    number(credit, positive=True)
    if credit > gross or not ZERO <= net <= gross:
        raise ValueError("Credit must fit the sealed invoice")
    with localcontext() as context:
        context.prec = 80
        credited_net = quantize_currency(credit * net / gross, currency)
        return credited_net, credit - credited_net


def tax_percent(*, net: Decimal, tax: Decimal) -> Decimal | None:
    number(net)
    number(tax)
    with localcontext() as context:
        context.prec = 80
        return (tax / net * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP) if net > ZERO else None


def collection_summary(
    *, total: Decimal | None, currency: str, milestones: Sequence[PaymentMilestone],
    payments: Sequence[CollectionPayment], today: date,
    approval_on: date | None = None, delivery_on: date | None = None,
) -> CollectionSummary:
    """Assign valid receipts in agreement order; missing dates stay unknown.

    A declared date takes precedence over the explicit approval/delivery event.
    Voided receipts contribute nothing. Genuine provider overpayments remain
    visible as excess, never disappear by clamping the ledger balance.
    """
    if total is not None:
        number(total)
        if total < ZERO:
            raise ValueError("Nonnegative sealed total required")
    for payment in payments:
        number(payment.amount, positive=True)
    for milestone in milestones:
        if not milestone.label.strip() or milestone.due_event not in (None, "APPROVAL", "DELIVERY"):
            raise ValueError("Declared milestone and event required")
    with localcontext() as context:
        context.prec = 80
        collected = sum((p.amount for p in payments if p.active), ZERO)
        includes_simulation = any(p.active and p.simulated for p in payments)
        if total is None:
            return CollectionSummary(None, collected, None, ZERO, None, ZERO, None,
                                     "NO_DEAL", (), includes_simulation)
        balance = total - collected
        excess = max(ZERO, -balance)
        percent = (min(Decimal("100"), collected / total * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
                   if total > ZERO else Decimal("100"))
        amounts = payment_amounts(total, [m.share for m in milestones], currency)
        available, overdue, oldest = collected, ZERO, None
        result = []
        for milestone, amount in zip(milestones, amounts, strict=True):
            paid = min(available, amount)
            available -= paid
            remaining = amount - paid
            due = milestone.due_on
            source = "DECLARED" if due else "UNKNOWN"
            if due is None and milestone.due_event == "APPROVAL":
                due, source = approval_on, "APPROVAL" if approval_on else "APPROVAL_PENDING"
            elif due is None and milestone.due_event == "DELIVERY":
                due, source = delivery_on, "DELIVERY" if delivery_on else "DELIVERY_PENDING"
            status = ("PAID" if remaining == ZERO else "OVERDUE" if due and due < today
                      else "DUE" if due == today else "PENDING")
            if status == "OVERDUE" and due is not None:
                overdue += remaining
                oldest = min(oldest, due) if oldest else due
            result.append(CollectionMilestone(milestone.label, milestone.share, amount, paid,
                                              remaining, due, source, status))
        status = "PAID" if balance <= ZERO else "PARTIAL" if collected > ZERO else "PENDING"
        return CollectionSummary(total, collected, balance, excess, percent, overdue, oldest,
                                 status, tuple(result), includes_simulation)
