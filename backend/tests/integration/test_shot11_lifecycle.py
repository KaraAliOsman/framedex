"""Owner lifecycle policy against real PostgreSQL, locks, ledger and RLS."""

from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone as utc
from decimal import Decimal
from uuid import uuid4

from django.db import close_old_connections, transaction, DatabaseError
from django.utils import timezone
import httpx
import pytest

from billing import lifecycle, orders, settlement, wallet
from billing.flow import FlowClient, FlowError
from billing.repository import one, rows
from backend.tests.integration.test_shot08_pricing import (
    commercial_rows as commercial_rows, committed_commercial_rows as committed_commercial_rows, as_user,
)
from backend.tests.integration.test_shot11_wallet import audit, assert_consistent

pytestmark = pytest.mark.rls_integration


def paid_period(org, start, end, *, tier='PRO', cycle='monthly'):
    sub = rows('SELECT id FROM public.subscriptions WHERE org_id=%s', [org])
    if not sub:
        sub = [one("INSERT INTO public.subscriptions(org_id,provider,provider_subscription_id,plan_tier,billing_cycle,"
                   "status,currency,amount) VALUES(%s,'flow',%s,%s,%s,'active','CLP',77596) RETURNING id",
                   [org, uuid4().hex, tier, cycle])]
    order = orders.prepare(org, operation_key=uuid4().hex, environment='sandbox', net_usd=Decimal('69'),
                           fx_rate=Decimal('900'), fx_source='Synthetic fixture', fx_observed_on=date(2026, 9, 1),
                           fx_snapshot_id=uuid4(), grants=(), commerce_order=uuid4().hex,
                           subscription_id=sub[0]['id'], provider_invoice_id=uuid4().hex)
    payment = dict(flowOrder=int(order['id'].hex[:12], 16), commerceOrder=order['commerce_order'], currency='CLP',
                   amount=int(order['amount']), status=2)
    client = FlowClient(api_url='https://sandbox.flow.cl/api', api_key='fixture', secret_key='fixture',
                        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=payment)))
    settlement.confirm(order['id'], 'fixture', client)
    evidence = {'timezone': 'UTC', 'invoice_id': order['provider_invoice_id']}
    period = lifecycle.record_paid_period(org, order_id=order['id'], start=start, end=end, plan_tier=tier,
                                         billing_cycle=cycle, evidence=evidence)
    return period, order


def pack(org, credits=1000):
    with wallet.financial_transaction(org):
        wallet.locked_org(org)
        entry = wallet.append(org, credits, 'PAYMENT_GRANT', uuid4().hex)
        return one("INSERT INTO public.credit_lots(org_id,grant_id,remaining,origin) VALUES(%s,%s,%s,'pack') RETURNING *",
                   [org, entry['id'], credits])


def allocations_consistent(org):
    for lot in rows('SELECT * FROM public.credit_lots WHERE org_id=%s', [org]):
        assert one('SELECT sum(amount) AS total FROM public.credit_lot_movements WHERE org_id=%s AND lot_id=%s',
                   [org, lot['id']])['total'] == lot['remaining']
    assert_consistent(org, wallet.summary(org)['balance'])


def test_paid_activation_expires_trial_and_spends_monthly_before_pack(commercial_rows):
    org, _, _ = commercial_rows
    wallet.debit(org, 100, audit(org, 100))
    purchased = pack(org)
    now = timezone.now()
    period, order = paid_period(org, now - timedelta(days=15), now + timedelta(days=15))
    assert wallet.summary(org)['plan'] == 'PRO'
    assert_consistent(org, 3000)
    assert one("SELECT sum(remaining) AS total FROM public.credit_lots WHERE org_id=%s AND origin='trial'", [org])['total'] == 0
    wallet.debit(org, 2100, audit(org, 2100))
    assert one('SELECT remaining FROM public.credit_lots WHERE id=%s', [purchased['id']])['remaining'] == 900
    assert lifecycle.record_paid_period(org, order_id=order['id'], start=period['period_start'], end=period['period_end'],
                                        plan_tier='PRO', billing_cycle='monthly', evidence=period['provider_evidence'])['id'] == period['id']
    assert_consistent(org, 900)
    allocations_consistent(org)


def test_upgrade_delta_once_and_full_allowance_at_next_renewal(committed_commercial_rows, monkeypatch):
    org, _, _ = committed_commercial_rows
    now = timezone.now()
    monkeypatch.setattr(timezone, 'now', lambda: now)
    period, _ = paid_period(org, now - timedelta(days=15), now + timedelta(days=15))
    def upgrade(_):
        close_old_connections()
        try:
            return lifecycle.record_change(org, period_id=period['id'], operation_key='upgrade-once', kind='upgrade',
                                            effective_at=now, plan_tier='BUSINESS', billing_cycle='monthly',
                                            evidence={'flow': 'verified fixture'})['id']
        finally:
            close_old_connections()
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert len(set(pool.map(upgrade, range(4)))) == 1
    assert wallet.summary(org)['plan'] == 'BUSINESS'
    assert_consistent(org, 4000)
    assert len(rows("SELECT id FROM public.credit_ledger WHERE org_id=%s AND action_type='UPGRADE_GRANT'", [org])) == 1
    monkeypatch.setattr(timezone, 'now', lambda: period['period_end'])
    paid_period(org, period['period_end'], period['period_end'] + timedelta(days=30), tier='BUSINESS')
    assert_consistent(org, 6000)
    allocations_consistent(org)


def test_downgrade_and_frequency_are_deferred_and_preserve_packs(commercial_rows, monkeypatch):
    org, _, _ = commercial_rows
    now = timezone.now()
    monkeypatch.setattr(timezone, 'now', lambda: now)
    period, _ = paid_period(org, now - timedelta(days=1), now + timedelta(days=29), tier='BUSINESS')
    purchased = pack(org)
    for kind in ('downgrade', 'frequency'):
        with pytest.raises(FlowError):
            lifecycle.record_change(org, period_id=period['id'], operation_key=kind+'invalid', kind=kind,
                                    effective_at=now, plan_tier='PRO', billing_cycle='annual', evidence={'flow': 'fixture'})
    lifecycle.record_change(org, period_id=period['id'], operation_key='downgrade', kind='downgrade',
                            effective_at=period['period_end'], plan_tier='STARTER', billing_cycle='monthly', evidence={'flow': 'fixture'})
    assert wallet.summary(org)['plan'] == 'BUSINESS'
    assert_consistent(org, 7000)
    monkeypatch.setattr(timezone, 'now', lambda: period['period_end'])
    paid_period(org, period['period_end'], period['period_end']+timedelta(days=30), tier='STARTER')
    summary = wallet.summary(org)
    assert summary['plan'] == 'STARTER' and not summary['ai_available'] and summary['balance'] == 1000
    assert one('SELECT remaining FROM public.credit_lots WHERE id=%s', [purchased['id']])['remaining'] == 1000
    allocations_consistent(org)


def test_annual_monthly_delivery_and_cancel_expire_without_deleting_packs(commercial_rows, monkeypatch):
    org, _, _ = commercial_rows
    now = datetime(2026, 9, 21, tzinfo=utc.utc)
    monkeypatch.setattr(timezone, 'now', lambda: now)
    period, _ = paid_period(org, now, datetime(2027, 9, 21, tzinfo=utc.utc), cycle='annual')
    pack(org)
    assert_consistent(org, 3000)
    monkeypatch.setattr(timezone, 'now', lambda: datetime(2026, 10, 21, tzinfo=utc.utc))
    assert wallet.summary(org)['balance'] == 3000
    lifecycle.record_change(org, period_id=period['id'], operation_key='cancel', kind='cancel',
                            effective_at=period['period_end'], plan_tier='STARTER', billing_cycle='annual', evidence={'flow': 'fixture'})
    assert wallet.summary(org)['plan'] == 'PRO'
    monkeypatch.setattr(timezone, 'now', lambda: period['period_end'])
    for _ in range(3):
        assert wallet.summary(org)['balance'] == 1000
        assert wallet.summary(org)['plan'] == 'STARTER'
    assert len(rows("SELECT id FROM public.credit_ledger WHERE org_id=%s AND action_type='MONTHLY_GRANT'", [org])) == 12
    allocations_consistent(org)


def test_lifecycle_evidence_rls_immutable_and_replay_conflict(commercial_rows):
    org, other, users = commercial_rows
    now = timezone.now()
    period, _ = paid_period(org, now-timedelta(days=1), now+timedelta(days=29))
    with wallet.financial_transaction(other):
        assert rows('SELECT id FROM public.billing_periods WHERE id=%s', [period['id']]) == []
    with as_user(users['OWNER']):
        with pytest.raises(DatabaseError), transaction.atomic():
            rows('SELECT id FROM public.billing_periods WHERE org_id=%s', [org])
    with pytest.raises(DatabaseError), transaction.atomic():
        one('UPDATE public.billing_periods SET allowance=99999 WHERE id=%s RETURNING id', [period['id']])
    with pytest.raises(FlowError):
        lifecycle.record_paid_period(org, order_id=period['order_id'], start=period['period_start'], end=period['period_end'],
                                     plan_tier='BUSINESS', billing_cycle='monthly', evidence=period['provider_evidence'])


def test_upgrade_failure_rolls_back_entitlement_grant_and_evidence(commercial_rows, monkeypatch):
    org, _, _ = commercial_rows
    now = timezone.now()
    paid, _ = paid_period(org, now-timedelta(days=15), now+timedelta(days=15))
    original = wallet.append
    def fail(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError('injected after ledger append')
    monkeypatch.setattr(wallet, 'append', fail)
    with pytest.raises(RuntimeError):
        lifecycle.record_change(org, period_id=paid['id'], operation_key='rollback', kind='upgrade', effective_at=now,
                                plan_tier='BUSINESS', billing_cycle='monthly', evidence={'flow': 'fixture'})
    assert_consistent(org, 2000)
    assert rows('SELECT id FROM public.billing_lifecycle_events WHERE org_id=%s', [org]) == []
