"""Server-only construction of frozen payment expectations.

Commercial orchestration must supply an approved schedule explicitly. No public
endpoint accepts prices, FX, grants or policy references from a tenant browser.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from django.utils import timezone

from billing import wallet
from dekopen_engine.billing import platform_charge_clp
from pricing.repository import one, rows


@dataclass(frozen=True)
class Grant:
    credits: int
    available_at: datetime
    expires_at: datetime | None
    policy_reference: str


def prepare(org: UUID, *, operation_key: str, environment: str, net_usd: Decimal,
            fx_rate: Decimal, fx_source: str, fx_observed_on: date, fx_snapshot_id: UUID,
            grants: tuple[Grant, ...], commerce_order: str,
            subscription_id: UUID | None = None, provider_invoice_id: str | None = None):
    if (not operation_key or not commerce_order or not fx_source.strip()
            or environment not in ('sandbox', 'production') or not isinstance(net_usd, Decimal)
            or not isinstance(fx_rate, Decimal) or net_usd != net_usd.quantize(Decimal('.01'))
            or fx_observed_on > timezone.now().date()):
        raise ValueError('Explicit valid server-side price and FX authority required')
    for grant in grants:
        if (type(grant.credits) is not int or grant.credits <= 0 or not grant.policy_reference.strip()
                or timezone.is_naive(grant.available_at)
                or (grant.expires_at is not None and (timezone.is_naive(grant.expires_at)
                                                     or grant.expires_at <= grant.available_at))):
            raise ValueError('Explicit valid grant schedule and approved policy reference required')
    amount = platform_charge_clp(net_usd, fx_rate)
    expected = dict(provider_environment=environment, commerce_order=commerce_order, amount=amount,
                    net_usd=net_usd, fx_rate=fx_rate, fx_source=fx_source, fx_observed_on=fx_observed_on,
                    fx_snapshot_id=fx_snapshot_id, subscription_id=subscription_id,
                    provider_invoice_id=provider_invoice_id)
    with wallet.financial_transaction(org):
        wallet.locked_org(org)
        previous = rows('SELECT * FROM public.billing_orders WHERE org_id=%s AND operation_key=%s', [org, operation_key])
        if previous:
            order = previous[0]
            schedules = rows('SELECT credits,available_at,expires_at,policy_reference '
                             'FROM public.billing_credit_grants WHERE org_id=%s AND order_id=%s '
                             'ORDER BY installment', [org, order['id']])
            if any(order[key] != value for key, value in expected.items()) or schedules != [vars(grant) for grant in grants]:
                raise ValueError('Payment operation replay conflicts with frozen authority')
            return order
        order = one('INSERT INTO public.billing_orders(org_id,operation_key,provider,provider_environment,commerce_order,'
                    'amount,net_usd,fx_rate,fx_source,fx_observed_on,fx_snapshot_id,subscription_id,provider_invoice_id) '
                    "VALUES(%s,%s,'flow',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *",
                    [org, operation_key, *expected.values()])
        for installment, grant in enumerate(grants):
            one('INSERT INTO public.billing_credit_grants(org_id,order_id,installment,credits,available_at,expires_at,policy_reference) '
                'VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING id', [org, order['id'], installment, grant.credits,
                                                         grant.available_at, grant.expires_at, grant.policy_reference])
        return order
