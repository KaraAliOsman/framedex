"""Only HTTP is simulated. PostgreSQL locks, triggers, RLS and rollback are real."""

from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from decimal import Decimal
from urllib.parse import parse_qs
from uuid import uuid4

from django.db import close_old_connections, connection, transaction, DatabaseError
from django.utils import timezone
import httpx
import pytest
from rest_framework.test import APIClient

from billing import wallet, settlement, orders
from billing.flow import FlowClient, FlowError
from pricing.repository import one, rows
from backend.tests.integration.test_shot08_pricing import (
    commercial_rows as commercial_rows, committed_commercial_rows as committed_commercial_rows, as_user,
)
from backend.tests.integration.test_shot11_wallet import assert_consistent

pytestmark = pytest.mark.rls_integration


def prepare(org, *, grants=None):
    now = timezone.now()
    return orders.prepare(org, operation_key=str(uuid4()), environment='sandbox', net_usd=Decimal('15'),
                          fx_rate=Decimal('900'), fx_source='Synthetic test observation',
                          fx_observed_on=date(2026, 9, 1), fx_snapshot_id=uuid4(), commerce_order=str(uuid4()),
                          grants=grants if grants is not None else (
                              orders.Grant(1000, now-timedelta(seconds=1), now+timedelta(days=1), 'synthetic-test-policy'),))


def network(order, status=2, **overrides):
    body = dict(flowOrder=987654, commerceOrder=order['commerce_order'], currency='CLP', amount=16868, status=status)
    body.update(overrides)
    calls = []
    def handle(request):
        calls.append(request)
        assert request.method == 'GET'
        assert parse_qs(request.url.query.decode())['s']
        return httpx.Response(200, json=body)
    return FlowClient(api_url='https://sandbox.flow.cl/api', api_key='synthetic', secret_key='synthetic',
                      transport=httpx.MockTransport(handle)), calls


def test_confirm_replays_and_out_of_order_observations(commercial_rows):
    org, _, _ = commercial_rows
    order = prepare(org)
    client, calls = network(order)
    assert settlement.confirm(order['id'], 'callback-token', client) == 'succeeded'
    for status in (1, 3, 4, 2, 2):
        delayed, _ = network(order, status)
        assert settlement.confirm(order['id'], 'rotated-token', delayed) == 'succeeded'
    assert calls[0].url.path == '/api/payment/getStatus'
    assert_consistent(org, 1500)
    assert len(rows('SELECT * FROM public.payments WHERE org_id=%s', [org])) == 1
    assert len(rows('SELECT * FROM public.payment_events WHERE org_id=%s', [org])) == 4
    assert len(rows('SELECT * FROM public.credit_ledger WHERE org_id=%s', [org])) == 2
    assert 'callback-token' not in str(rows('SELECT payload FROM public.payment_events WHERE org_id=%s', [org]))


@pytest.mark.parametrize('override', [{'amount': 16867}, {'currency': 'USD'}, {'commerceOrder': 'foreign'},
                                     {'flowOrder': True}, {'status': True}, {'amount': 'NaN'}, {'amount': 16868.1}])
def test_provider_mismatch_never_records_payment_or_grant(commercial_rows, override):
    org, _, _ = commercial_rows
    order = prepare(org)
    client, _ = network(order, **override)
    with pytest.raises(FlowError):
        settlement.confirm(order['id'], 'token', client)
    assert_consistent(org, 500)
    assert rows('SELECT * FROM public.payments WHERE org_id=%s', [org]) == []
    assert rows('SELECT * FROM public.payment_events WHERE org_id=%s', [org]) == []


def test_failure_after_ledger_rolls_back_payment_event_grant_and_balance(commercial_rows, monkeypatch):
    org, _, _ = commercial_rows
    order = prepare(org)
    client, _ = network(order)
    original = wallet.append
    def injected(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError('injected after ledger insertion')
    monkeypatch.setattr(wallet, 'append', injected)
    with pytest.raises(RuntimeError):
        settlement.confirm(order['id'], 'token', client)
    assert_consistent(org, 500)
    assert rows('SELECT * FROM public.payments WHERE org_id=%s', [org]) == []
    assert rows('SELECT * FROM public.payment_events WHERE org_id=%s', [org]) == []
    assert one('SELECT state FROM public.billing_orders WHERE id=%s', [order['id']])['state'] == 'prepared'
    monkeypatch.setattr(wallet, 'append', original)
    settlement.confirm(order['id'], 'token', client)
    assert_consistent(org, 1500)


def test_concurrent_callbacks_grant_once(committed_commercial_rows):
    org, _, _ = committed_commercial_rows
    order = prepare(org)
    client, _ = network(order)
    def confirm(_):
        close_old_connections()
        try:
            return settlement.confirm(order['id'], 'token', client)
        finally:
            close_old_connections()
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(confirm, range(4))) == ['succeeded'] * 4
    assert_consistent(org, 1500)
    assert len(rows('SELECT * FROM public.payments WHERE org_id=%s', [org])) == 1
    assert len(rows('SELECT * FROM public.payment_events WHERE org_id=%s', [org])) == 1


def test_pending_does_not_grant_and_late_expired_grant_is_unusable(commercial_rows):
    org, _, _ = commercial_rows
    now = timezone.now()
    order = prepare(org, grants=(orders.Grant(1000, now-timedelta(days=2), now-timedelta(days=1), 'synthetic'),
                                 orders.Grant(1000, now+timedelta(days=2), None, 'synthetic')))
    client, _ = network(order, 1)
    assert settlement.confirm(order['id'], 'token', client) == 'pending'
    assert_consistent(org, 500)
    client, _ = network(order, 2)
    assert settlement.confirm(order['id'], 'token', client) == 'succeeded'
    # Record the late credit and expiry as evidence, without creating spendable balance.
    assert_consistent(org, 500)
    assert len(rows('SELECT * FROM public.credit_ledger WHERE org_id=%s', [org])) == 3
    assert len(rows('SELECT * FROM public.billing_credit_grants WHERE org_id=%s AND ledger_id IS NULL', [org])) == 1


def test_order_authority_is_immutable_and_tenant_inaccessible(commercial_rows):
    org, other, users = commercial_rows
    order = prepare(org)
    with as_user(users['OWNER']):
        for table in ('billing_orders', 'billing_credit_grants'):
            with pytest.raises(DatabaseError), transaction.atomic():
                rows(f'SELECT * FROM public.{table}')
    with connection.cursor() as cursor:
        cursor.execute('RESET ROLE')
    with wallet.financial_transaction(other):
        assert rows('SELECT * FROM public.billing_orders WHERE id=%s', [order['id']]) == []
    with pytest.raises(DatabaseError), transaction.atomic():
        one('UPDATE public.billing_orders SET amount=1 WHERE id=%s RETURNING id', [order['id']])
    with pytest.raises(DatabaseError), transaction.atomic():
        one('UPDATE public.billing_credit_grants SET credits=1 WHERE order_id=%s RETURNING id', [order['id']])


def test_dispatch_timeout_cannot_repeat_charge_and_get_recovers(committed_commercial_rows):
    org, _, _ = committed_commercial_rows
    order = prepare(org)
    calls = []
    def timeout(request):
        calls.append(request)
        raise httpx.ReadTimeout('synthetic ambiguous remote commit')
    client = FlowClient(api_url='https://sandbox.flow.cl/api', api_key='synthetic', secret_key='synthetic',
                        transport=httpx.MockTransport(timeout))
    arguments = dict(email='fixture@example.invalid', subject='Synthetic pack',
                     confirmation_url='https://example.invalid/confirm', return_url='https://example.invalid/return')
    for _ in range(2):
        with pytest.raises(FlowError):
            settlement.dispatch_payment(order['id'], client, **arguments)
    assert len(calls) == 1
    assert one('SELECT state FROM public.billing_orders WHERE id=%s', [order['id']])['state'] == 'uncertain'
    status_client, requests = network(order)
    assert settlement.recover(order['id'], status_client) == 'succeeded'
    assert requests[0].url.path == '/api/payment/getStatusByCommerceId'
    assert_consistent(org, 1500)


def test_callback_ignores_forged_body_authority(commercial_rows, monkeypatch):
    org, other, _ = commercial_rows
    order = prepare(org)
    client, _ = network(order, 1)
    monkeypatch.setattr('billing.views.FlowClient', lambda **kwargs: client)
    response = APIClient().post(f"/api/v1/billing/flow/confirm/{order['id']}/",
                                f'token=opaque&status=2&amount=1&credits=99999&org_id={other}',
                                content_type='application/x-www-form-urlencoded')
    assert response.status_code == 200
    assert_consistent(org, 500)
    assert_consistent(other, 500)
    assert one('SELECT status FROM public.payments WHERE org_id=%s', [org])['status'] == 'pending'
