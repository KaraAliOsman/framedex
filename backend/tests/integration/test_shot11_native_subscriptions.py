"""Native Flow orchestration with real PostgreSQL and only an HTTP network seam."""

from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from threading import Lock
from urllib.parse import parse_qs
from uuid import uuid4

from django.db import close_old_connections, transaction, DatabaseError
import httpx
import pytest

from billing import native_subscriptions as native, wallet
from billing.flow import FlowClient, FlowError
from pricing.repository import one, rows
from backend.tests.integration.test_shot08_pricing import (
    commercial_rows as commercial_rows, committed_commercial_rows as committed_commercial_rows,
    as_user,
)
from backend.tests.integration.test_shot11_wallet import assert_consistent

pytestmark = pytest.mark.rls_integration


def prepare(org):
    customer = one("INSERT INTO public.payment_customers(org_id,provider,provider_customer_id) "
                   "VALUES(%s,'flow',%s) RETURNING id", [org, 'cus_' + uuid4().hex])
    arguments = dict(operation_key=str(uuid4()), customer_id=customer['id'], provider_plan_id='synthetic-plan',
                     environment='sandbox', plan_tier='STARTER', billing_cycle='monthly', net_usd=Decimal('39'),
                     fx_rate=Decimal('900'), fx_source='Synthetic test observation', fx_observed_on=date(2026, 9, 1),
                     fx_snapshot_id=uuid4(), start_date=date(2026, 10, 1), trial_days=0,
                     policy_reference='synthetic explicit test policy; not an approved production policy')
    intent = native.prepare(org, **arguments)
    return intent, arguments


class Network:
    def __init__(self, org, intent, *, ambiguous=False, plan_override=None, subscription_override=None):
        self.org, self.intent, self.ambiguous = org, intent, ambiguous
        self.plan_override = plan_override or {}
        self.subscription_override = subscription_override or {}
        self.created = []
        self.posts = 0
        self.lock = Lock()
        self.client = FlowClient(api_url='https://sandbox.flow.cl/api', api_key='synthetic', secret_key='synthetic',
                                 transport=httpx.MockTransport(self.handle))

    def subscription(self):
        value = dict(subscriptionId='sus_synthetic', customerId=self.intent['provider_customer_id'],
                    planId=self.intent['provider_plan_id'], subscription_start='2026-10-01 00:00:00',
                    trial_period_days=0)
        value.update(self.subscription_override)
        return value

    def handle(self, request):
        path = request.url.path
        if path == '/api/plans/get':
            value = dict(planId=self.intent['provider_plan_id'], amount=43857, currency='CLP', interval=3, interval_count=1)
            value.update(self.plan_override)
        elif path == '/api/customer/get':
            value = dict(customerId=self.intent['provider_customer_id'], externalId=str(self.org))
        elif path == '/api/customer/getSubscriptions':
            assert request.method == 'GET'
            with self.lock:
                value = dict(hasMore=0, total=len(self.created), data=[dict(subscriptionId=item['subscriptionId']) for item in self.created])
        elif path == '/api/subscription/get':
            value = self.subscription()
        elif path == '/api/invoice/get':
            value = dict(id=765, subscriptionId='sus_synthetic', customerId=self.intent['provider_customer_id'],
                         currency='CLP', amount=43857, payment=self.payment())
        elif path == '/api/payment/getStatusByCommerceId':
            value = self.payment()
        elif path == '/api/subscription/create':
            assert request.method == 'POST'
            data = parse_qs(request.content.decode())
            assert data['planId'] == [self.intent['provider_plan_id']]
            assert data['customerId'] == [self.intent['provider_customer_id']]
            assert data['subscription_start'] == ['2026-10-01']
            assert data['trial_period_days'] == ['0']
            value = self.subscription()
            with self.lock:
                self.posts += 1
                self.created.append(value)
            if self.ambiguous:
                raise httpx.ReadTimeout('synthetic provider committed before connection failed')
        else:
            pytest.fail('Unexpected provider request: ' + path)
        return httpx.Response(200, json=value)

    def payment(self):
        return dict(flowOrder=int(self.intent['id'].hex[:12], 16), commerceOrder=str(self.intent['id']),
                    status=2, currency='CLP', amount=43857)


def test_preparation_replay_preserves_price_and_requires_same_authority(commercial_rows):
    org, _, _ = commercial_rows
    intent, arguments = prepare(org)
    assert native.prepare(org, **arguments)['id'] == intent['id']
    with pytest.raises(FlowError):
        native.prepare(org, **{**arguments, 'fx_rate': Decimal('901')})
    assert one('SELECT status FROM public.subscriptions WHERE org_id=%s', [org])['status'] == 'pending'
    assert_consistent(org, 500)


def test_native_create_replay_never_activates_unpaid_entitlements(committed_commercial_rows):
    org, _, _ = committed_commercial_rows
    intent, _ = prepare(org)
    remote = Network(org, intent)
    assert native.dispatch(org, intent['id'], remote.client) == 'sus_synthetic'
    assert native.dispatch(org, intent['id'], remote.client) == 'sus_synthetic'
    assert remote.posts == 1
    local = one('SELECT * FROM public.subscriptions WHERE org_id=%s', [org])
    assert local['provider_subscription_id'] == 'sus_synthetic' and local['status'] == 'pending'
    assert wallet.summary(org)['plan'] == 'TRIAL'
    assert_consistent(org, 500)
    assert rows('SELECT * FROM public.payments WHERE org_id=%s', [org]) == []


def test_uncertain_native_create_is_recovered_by_get_without_second_subscription(committed_commercial_rows):
    org, _, _ = committed_commercial_rows
    intent, _ = prepare(org)
    remote = Network(org, intent, ambiguous=True)
    for _ in range(2):
        with pytest.raises(FlowError):
            native.dispatch(org, intent['id'], remote.client)
    assert remote.posts == 1
    assert native.recover(org, intent['id'], remote.client) == 'sus_synthetic'
    assert remote.posts == 1
    assert_consistent(org, 500)


def test_concurrent_native_create_claims_only_one_post(committed_commercial_rows):
    org, _, _ = committed_commercial_rows
    intent, _ = prepare(org)
    remote = Network(org, intent)
    def start(_):
        close_old_connections()
        try:
            return native.dispatch(org, intent['id'], remote.client)
        except FlowError:
            return None
        finally:
            close_old_connections()
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(start, range(4)))
    assert 'sus_synthetic' in results and remote.posts == 1


@pytest.mark.parametrize('override', [{'amount': 1}, {'currency': 'USD'}, {'interval': 4}, {'interval_count': 2}])
def test_remote_plan_mismatch_cannot_subscribe(committed_commercial_rows, override):
    org, _, _ = committed_commercial_rows
    intent, _ = prepare(org)
    remote = Network(org, intent, plan_override=override)
    with pytest.raises(FlowError):
        native.dispatch(org, intent['id'], remote.client)
    assert remote.posts == 0


def test_existing_remote_subscription_is_not_duplicated(committed_commercial_rows):
    org, _, _ = committed_commercial_rows
    intent, _ = prepare(org)
    remote = Network(org, intent)
    remote.created.append(remote.subscription())
    with pytest.raises(FlowError, match='flow_subscription_already_exists'):
        native.dispatch(org, intent['id'], remote.client)
    assert remote.posts == 0


def test_intent_tenant_scope_and_immutable_terms(commercial_rows):
    org, other, users = commercial_rows
    intent, _ = prepare(org)
    remote = Network(org, intent)
    with pytest.raises(FlowError):
        native._read(other, intent['id'], remote.client)
    with wallet.financial_transaction(other):
        assert rows('SELECT * FROM public.flow_subscription_intents') == []
    with pytest.raises(DatabaseError), transaction.atomic():
        one('UPDATE public.flow_subscription_intents SET net_usd=1 WHERE id=%s RETURNING id', [intent['id']])
    with as_user(users['OWNER']):
        with pytest.raises(DatabaseError), transaction.atomic():
            rows('SELECT * FROM public.flow_subscription_intents')


def test_empty_recovery_is_not_permission_to_repeat_post(committed_commercial_rows):
    org, _, _ = committed_commercial_rows
    intent, _ = prepare(org)
    remote = Network(org, intent, ambiguous=True)
    with pytest.raises(FlowError):
        native.dispatch(org, intent['id'], remote.client)
    remote.created.clear()  # Simulate delayed read visibility after a remote commit.
    with pytest.raises(FlowError):
        native.recover(org, intent['id'], remote.client)
    with pytest.raises(FlowError):
        native.dispatch(org, intent['id'], remote.client)
    assert remote.posts == 1


def test_verified_native_invoice_settles_once_without_fiscal_receipt_or_invented_credits(committed_commercial_rows):
    org, _, _ = committed_commercial_rows
    intent, _ = prepare(org)
    remote = Network(org, intent)
    native.dispatch(org, intent['id'], remote.client)
    for _ in range(2):
        assert native.reconcile_invoice(org, intent['id'], 765, remote.client, grants=()) == 'succeeded'
    payments = rows('SELECT * FROM public.payments WHERE org_id=%s', [org])
    assert len(payments) == 1 and payments[0]['subscription_id'] == intent['subscription_id']
    assert payments[0]['tax_doc_folio'] is None
    assert_consistent(org, 500)


def test_foreign_native_invoice_is_rejected(committed_commercial_rows):
    org, _, _ = committed_commercial_rows
    intent, _ = prepare(org)
    remote = Network(org, intent)
    native.dispatch(org, intent['id'], remote.client)
    def foreign(request):
        assert request.url.path == '/api/invoice/get'
        return httpx.Response(200, json=dict(id=765, subscriptionId='sus_foreign', customerId=intent['provider_customer_id'],
                                           currency='CLP', amount=43857, payment=remote.payment()))
    client = FlowClient(api_url='https://sandbox.flow.cl/api', api_key='synthetic', secret_key='synthetic',
                        transport=httpx.MockTransport(foreign))
    with pytest.raises(FlowError):
        native.reconcile_invoice(org, intent['id'], 765, client, grants=())
    assert rows('SELECT * FROM public.payments WHERE org_id=%s', [org]) == []


def test_crash_after_remote_create_before_local_commit_is_recoverable(committed_commercial_rows, monkeypatch):
    org, _, _ = committed_commercial_rows
    intent, _ = prepare(org)
    remote = Network(org, intent)
    original = native.one
    def crash(sql, values=None):
        result = original(sql, values)
        if sql.startswith('UPDATE public.subscriptions'):
            raise RuntimeError('synthetic crash after remote success but before local commit')
        return result
    monkeypatch.setattr(native, 'one', crash)
    with pytest.raises(RuntimeError):
        native.dispatch(org, intent['id'], remote.client)
    monkeypatch.setattr(native, 'one', original)
    assert remote.posts == 1
    assert one('SELECT provider_subscription_id FROM public.subscriptions WHERE org_id=%s', [org])['provider_subscription_id'] is None
    assert native.recover(org, intent['id'], remote.client) == 'sus_synthetic'
    assert remote.posts == 1
