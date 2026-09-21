"""Real database operations, mocking only signed provider HTTP responses."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from urllib.parse import parse_qs
from uuid import uuid4

from django.db import close_old_connections
from django.utils import timezone
import httpx
import pytest

from billing import changes, refunds, wallet, orders, settlement
from billing.flow import FlowClient, FlowError
from billing.repository import one
from backend.tests.integration.test_shot08_pricing import (
    committed_commercial_rows as committed_commercial_rows,
)
from backend.tests.integration.test_shot11_lifecycle import paid_period, allocations_consistent
from backend.tests.integration.test_shot11_wallet import audit, assert_consistent
from backend.tests.integration.test_shot11_native_subscriptions import prepare, Network
from billing import native_subscriptions

pytestmark = pytest.mark.rls_integration


class LifecycleNetwork:
    def __init__(self, intent, period):
        self.intent, self.period = intent, period
        self.new_plan = 'business-fixture'
        self.plan = intent['provider_plan_id']
        self.posts = 0
        self.cancel = False
        self.ambiguous = False
        self.client = FlowClient(api_url='https://sandbox.flow.cl/api', api_key='fixture', secret_key='fixture',
                                 transport=httpx.MockTransport(self.handle))

    def handle(self, request):
        path = request.url.path
        if path == '/api/plans/get':
            value = dict(planId=self.new_plan, amount=145068, currency='CLP', interval=3, interval_count=1)
        elif path == '/api/subscription/get':
            value = dict(subscriptionId=self.intent['provider_subscription_id'], customerId=self.intent['provider_customer_id'],
                         planId=self.plan, status=1, period_start=self.period['period_start'].isoformat(),
                         period_end=self.period['period_end'].isoformat(), cancel_at_period_end=int(self.cancel))
        elif path == '/api/subscription/changePlanPreview':
            assert request.method == 'POST'
            value = dict(balance={'amount': 30000}, old_plan={'currency': 'CLP'},
                         new_plan={'currency': 'CLP', 'amount': '145068', 'interval': 3, 'interval_count': 1})
        elif path == '/api/subscription/changePlan':
            self.posts += 1
            data = parse_qs(request.content.decode())
            assert data['newPlanId'] == [self.new_plan]
            self.plan = self.new_plan
            if self.ambiguous:
                raise httpx.ReadTimeout('synthetic lost mutation response')
            value = dict(new_plan_id=self.new_plan, old_plan_id=self.intent['provider_plan_id'],
                         new_currency='CLP', new_amount='145068', balance=30000, start_date_of_new_plan='2026-09-21')
        elif path == '/api/subscription/cancel':
            self.posts += 1
            assert parse_qs(request.content.decode())['at_period_end'] == ['1']
            self.cancel = True
            value = {'cancel_at_period_end': 1}
        else:
            pytest.fail(path)
        return httpx.Response(200, json=value)


def active(org):
    intent, _ = prepare(org)
    native_subscriptions.dispatch(org, intent['id'], Network(org, intent).client)
    intent = one('SELECT * FROM public.flow_subscription_intents WHERE org_id=%s', [org])
    now = timezone.now()
    period, _ = paid_period(org, now-timedelta(days=15), now+timedelta(days=15))
    return intent, period


def test_flow_upgrade_preview_confirm_and_single_dispatch(committed_commercial_rows):
    org, _, _ = committed_commercial_rows
    intent, period = active(org)
    remote = LifecycleNetwork(intent, period)
    op = changes.prepare_change(org, operation_key='upgrade', target=dict(provider_plan_id=remote.new_plan,
                                 plan_tier='BUSINESS', billing_cycle='monthly', amount='145068'),
                                 client=remote.client, provider_timezone='UTC')
    assert wallet.summary(org)['plan'] == 'PRO'
    def dispatch(_):
        close_old_connections()
        try:
            return changes.dispatch(org, op['id'], remote.client)
        except FlowError:
            return None
        finally:
            close_old_connections()
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(dispatch, range(4)))
    assert remote.posts == 1
    changes.dispatch(org, op['id'], remote.client)
    assert remote.posts == 1 and wallet.summary(org)['plan'] == 'BUSINESS'
    assert 3998 <= wallet.summary(org)['balance'] <= 4000
    allocations_consistent(org)
    stored = one('SELECT preview,result FROM public.flow_lifecycle_operations WHERE id=%s', [op['id']])
    assert stored['preview']['balance']['amount'] == 30000 and stored['result']['balance'] == 30000


def test_ambiguous_change_never_posts_twice_or_grants_unconfirmed_credits(committed_commercial_rows):
    org, _, _ = committed_commercial_rows
    intent, period = active(org)
    remote = LifecycleNetwork(intent, period)
    remote.ambiguous = True
    op = changes.prepare_change(org, operation_key='lost', target=dict(provider_plan_id=remote.new_plan,
                                 plan_tier='BUSINESS', billing_cycle='monthly', amount='145068'),
                                 client=remote.client, provider_timezone='UTC')
    for _ in range(2):
        with pytest.raises(FlowError):
            changes.dispatch(org, op['id'], remote.client)
    assert remote.posts == 1
    assert wallet.summary(org)['plan'] == 'PRO'
    assert_consistent(org, 2000)


def test_flow_cancel_uses_period_end_and_retains_entitlements(committed_commercial_rows):
    org, _, _ = committed_commercial_rows
    intent, period = active(org)
    remote = LifecycleNetwork(intent, period)
    op = changes.prepare_cancel(org, operation_key='cancel', client=remote.client, provider_timezone='UTC')
    changes.dispatch(org, op['id'], remote.client)
    changes.dispatch(org, op['id'], remote.client)
    assert remote.posts == 1 and wallet.summary(org)['plan'] == 'PRO'
    event = one("SELECT * FROM public.billing_lifecycle_events WHERE org_id=%s AND kind='cancel'", [org])
    assert event['effective_at'] == period['period_end']


@pytest.mark.parametrize('spent,expected_state,expected_balance', [(0, 'confirmed', 2000), (2100, 'needs_admin', 900)])
def test_refund_compensation_is_bound_idempotent_and_never_creates_credit_debt(committed_commercial_rows, spent, expected_state, expected_balance):
    org, _, _ = committed_commercial_rows
    active(org)
    now = timezone.now()
    order = orders.prepare(org, operation_key=uuid4().hex, environment='sandbox', net_usd=Decimal('15'),
                           fx_rate=Decimal('900'), fx_source='fixture', fx_observed_on=now.date(), fx_snapshot_id=uuid4(),
                           grants=(orders.Grant(1000,now-timedelta(seconds=1),None,'PD-11-02'),), commerce_order=uuid4().hex)
    post_count = []
    refund_id = uuid4().hex
    def handle(request):
        if '/payment/' in request.url.path:
            return httpx.Response(200, json=dict(flowOrder=int(order['id'].hex[:12], 16),
                    commerceOrder=order['commerce_order'], status=2, currency='CLP', amount=int(order['amount'])))
        value = dict(token='refund-fixture',flowRefundOrder=refund_id,amount=int(order['amount']),status='refunded')
        if request.url.path == '/api/refund/create':
            post_count.append(1)
            data = parse_qs(request.content.decode())
            assert data['flowTrxId'] == [str(int(order['id'].hex[:12],16))]
            assert 'urlCallBack' in data
        else:
            assert request.url.path == '/api/refund/getStatus'
        return httpx.Response(200,json=value)
    client = FlowClient(api_url='https://sandbox.flow.cl/api',api_key='fixture',secret_key='fixture',transport=httpx.MockTransport(handle))
    settlement.confirm(order['id'],'fixture',client)
    grant = one('SELECT ledger_id FROM public.billing_credit_grants WHERE order_id=%s',[order['id']])['ledger_id']
    if spent:
        wallet.debit(org,spent,audit(org,spent))
    op = refunds.prepare(org,operation_key='refund',order_id=order['id'],amount=order['amount'],reason='duplicate_charge',
                         authorization='admin-case-fixture',grant_ids=[grant])
    refunds.dispatch(org,op['id'],client,receiver_email='fixture@example.test',callback_url='https://api.example.test/refund')
    for _ in range(3):
        refunds.confirm(org,op['id'],'refund-fixture',client)
    assert len(post_count)==1
    assert one('SELECT state FROM public.flow_lifecycle_operations WHERE id=%s',[op['id']])['state']==expected_state
    assert_consistent(org,expected_balance)
    allocations_consistent(org)
    assert one('SELECT status FROM public.payments WHERE id=%s',
               [one('SELECT payment_id FROM public.billing_orders WHERE id=%s',[order['id']])['payment_id']])['status']=='succeeded'
    with pytest.raises(FlowError):
        refunds.prepare(org,operation_key='over-refund',order_id=order['id'],amount=Decimal(1),reason='duplicate_charge',
                        authorization='admin',grant_ids=[grant])
