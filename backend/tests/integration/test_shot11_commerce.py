"""Complete OWNER-selected checkout/renewal boundary; only Flow HTTP is simulated."""

from datetime import date, timedelta
from decimal import Decimal
from urllib.parse import parse_qs
from uuid import uuid4

from django.db import transaction, DatabaseError
from django.utils import timezone
import httpx
import pytest

from billing import commerce, customers, offers, settlement, wallet
from billing.flow import FlowClient, FlowError
from billing.repository import one, rows
from backend.tests.integration.test_shot08_pricing import (
    commercial_rows as commercial_rows, committed_commercial_rows as committed_commercial_rows, as_user,
)
from backend.tests.integration.test_shot11_wallet import assert_consistent
from backend.tests.integration.test_shot11_lifecycle import allocations_consistent

pytestmark=pytest.mark.rls_integration


def offer(org,code='PRO',cycle='monthly'):
    return offers.provision(org,product_code=code,billing_cycle=cycle,environment='sandbox',
        provider_plan_id=uuid4().hex if cycle else None,fx_rate=Decimal('900'),fx_source='Fixture observed FX',
        fx_observed_on=date(2026,9,1),fx_snapshot_id=uuid4(),reason='Explicit synthetic provisioning')


class CheckoutNetwork:
    def __init__(self,org,offer):
        self.org,self.offer=org,offer
        self.customer_id=uuid4().hex
        self.subscription_id=uuid4().hex
        self.token=uuid4().hex
        self.start=timezone.now().replace(hour=0,minute=0,second=0,microsecond=0)
        self.end=self.start+timedelta(days=30)
        self.invoice_id=int(uuid4().hex[:10],16)
        self.payment_id=int(uuid4().hex[:12],16)
        self.status=1
        self.email='owner@example.test'
        self.subscribed=False
        self.posts=[]
        self.client=FlowClient(api_url='https://sandbox.flow.cl/api',api_key='fixture',secret_key='fixture',
                               transport=httpx.MockTransport(self.handle))

    def payment(self):
        return dict(flowOrder=self.payment_id,commerceOrder=str(self.invoice_id),status=self.status,
                    amount=int(self.offer['amount']),currency='CLP')

    def invoice(self):
        return dict(id=self.invoice_id,subscriptionId=self.subscription_id,customerId=self.customer_id,
                    currency='CLP',amount=int(self.offer['amount']),period_start=self.start.isoformat(),
                    period_end=self.end.isoformat(),payment=self.payment())

    def subscription(self):
        return dict(subscriptionId=self.subscription_id,customerId=self.customer_id,planId=self.offer['provider_plan_id'],
                    trial_period_days=0,subscription_start=self.start.date().isoformat(),period_start=self.start.isoformat(),
                    period_end=self.end.isoformat(),invoices=[self.invoice()])

    def handle(self,request):
        path=request.url.path
        if request.method=='POST':
            self.posts.append(path)
        if path in ('/api/customer/create','/api/customer/get'):
            value=dict(customerId=self.customer_id,externalId=str(self.org),email=self.email)
        elif path=='/api/customer/register':
            assert 'registration-return' in parse_qs(request.content.decode())['url_return'][0]
            value=dict(token=self.token,url='https://sandbox.flow.cl/app/customer/disclaimer.php')
        elif path=='/api/customer/getRegisterStatus':
            value=dict(customerId=self.customer_id,status='1')
        elif path=='/api/customer/getSubscriptions':
            value=dict(hasMore=0,data=[self.subscription()] if self.subscribed else [])
        elif path=='/api/plans/get':
            value=dict(planId=self.offer['provider_plan_id'],currency='CLP',amount=int(self.offer['amount']),
                       interval=3,interval_count=1)
        elif path=='/api/subscription/create':
            self.subscribed=True
            value=self.subscription()
        elif path=='/api/subscription/get':
            value=self.subscription()
        elif path=='/api/invoice/get':
            value=self.invoice()
        elif path in ('/api/payment/getStatusByCommerceId','/api/payment/getStatus'):
            value=self.payment()
        else:
            pytest.fail(path)
        return httpx.Response(200,json=value)


def begin(org,user,offer,remote,key):
    return commerce.checkout(org,user,operation_key=key,offer_id=offer['id'],customer_name='Fixture owner',
        customer_email='owner@example.test',client=remote.client,callback_origin='https://api.example.test',
        frontend_origin='https://app.example.test',provider_timezone='UTC')


def test_registration_checkout_pending_confirmation_and_renewal(committed_commercial_rows,monkeypatch):
    org,_,users=committed_commercial_rows
    plan=offer(org)
    remote=CheckoutNetwork(org,plan)
    key=uuid4()
    result=begin(org,users['OWNER'],plan,remote,key)
    assert result['state']=='redirect' and remote.token in result['redirect_url']
    customer=one('SELECT id FROM public.flow_customer_operations WHERE org_id=%s',[org])
    customers.confirm_registration(org,customer['id'],remote.token,remote.client)
    assert begin(org,users['OWNER'],plan,remote,key)['state']=='pending'
    assert_consistent(org,500)
    remote.status=2
    for _ in range(3):
        commerce.callback(plan['id'],'verified-payment-token',remote.client,'UTC')
    assert wallet.summary(org)['plan']=='PRO'
    assert_consistent(org,2000)
    assert remote.posts.count('/api/subscription/create')==1
    assert remote.posts.count('/api/customer/create')==1
    allocations_consistent(org)
    remote.start=remote.end
    remote.end+=timedelta(days=30)
    remote.invoice_id+=1
    remote.payment_id+=1
    monkeypatch.setattr(timezone,'now',lambda:remote.start)
    commerce.sync(org,remote.client,provider_timezone='UTC')
    assert_consistent(org,2000)
    assert len(rows('SELECT id FROM public.billing_periods WHERE org_id=%s',[org]))==2
    assert begin(org,users['OWNER'],plan,remote,key)['state']=='succeeded'
    assert remote.posts.count('/api/subscription/create')==1


def test_offers_are_audited_frozen_and_tenant_scoped(commercial_rows):
    org,other,users=commercial_rows
    plan=offer(org)
    assert one("SELECT count(*) AS n FROM public.price_audit_logs WHERE org_id=%s AND entity='billing_offers'",[org])['n']==1
    with wallet.financial_transaction(other):
        assert rows('SELECT id FROM public.billing_offers WHERE id=%s',[plan['id']])==[]
    with as_user(users['OWNER']):
        with pytest.raises(DatabaseError),transaction.atomic():
            one('UPDATE public.billing_offers SET amount=1 WHERE id=%s RETURNING id',[plan['id']])
    with pytest.raises(DatabaseError),transaction.atomic():
        one('UPDATE public.billing_offers SET amount=1 WHERE id=%s RETURNING id',[plan['id']])
    assert offers.public(org)[0]['amount']==str(int(plan['amount']))


def test_checkout_changed_selection_conflicts_before_provider_mutation(committed_commercial_rows):
    org,_,users=committed_commercial_rows
    first=offer(org)
    second=offer(org,'BUSINESS')
    remote=CheckoutNetwork(org,first)
    key=uuid4()
    begin(org,users['OWNER'],first,remote,key)
    before=list(remote.posts)
    with pytest.raises(FlowError):
        begin(org,users['OWNER'],second,remote,key)
    assert before==remote.posts


def test_public_commerce_owner_mfa_tenant_and_checkout_price_boundary(committed_commercial_rows,monkeypatch):
    from backend.tests.integration.test_shot08_pricing import owner_client
    from authentication.types import SupabaseUser, VerifiedSupabaseToken
    from rest_framework.test import APIClient
    org,other,users=committed_commercial_rows
    plan=offer(org)
    foreign=offer(other)
    owner=owner_client(users['OWNER'])
    visible=owner.get('/api/v1/billing/commerce/')
    assert visible.status_code==200 and len(visible.json()['offers'])==1
    assert 'provider_plan_id' not in visible.json()['offers'][0]
    estimator=owner_client(users['ESTIMATOR'])
    assert estimator.get('/api/v1/billing/commerce/').status_code==403
    assert owner.get('/api/v1/billing/commerce/',HTTP_X_ORGANIZATION_ID=str(other)).status_code==403
    weak=APIClient()
    weak.force_authenticate(user=SupabaseUser(users['OWNER'],'owner@example.test'),token=VerifiedSupabaseToken(
        access_token='fixture',claims={'sub':str(users['OWNER']),'role':'authenticated','aal':'aal1'},
        user_id=users['OWNER'],email='owner@example.test',aal='aal1'))
    assert weak.get('/api/v1/billing/commerce/').status_code==403
    remote=CheckoutNetwork(org,plan)
    monkeypatch.setattr('billing.offers.runtime',lambda:(remote.client,'https://api.example.test','https://app.example.test','UTC'))
    remote.email='owner@fixture.local'
    denied=owner.post('/api/v1/billing/checkout/',{'offer_id':str(foreign['id']),'operation_key':str(uuid4())},format='json')
    assert denied.status_code==404 and remote.posts==[]
    # Public selection cannot set amount, grants, organization or provider identity.
    result=owner.post('/api/v1/billing/checkout/',{'offer_id':str(plan['id']),'operation_key':str(uuid4()),
        'amount':'1','credits':999999,'org_id':str(other),'provider_plan_id':'foreign'},format='json')
    # Unknown fields are ignored by DRF; persisted authority still comes only from offer.
    assert result.status_code==200 and result.json()['state']=='redirect'
    selected=one('SELECT o.amount,o.credits FROM public.billing_offers o JOIN public.billing_checkouts c '
                 'ON c.offer_id=o.id WHERE c.org_id=%s',[org])
    assert selected['amount']==plan['amount'] and selected['credits']==2000


def test_adjustment_evidence_does_not_block_renewal_or_grant_twice(committed_commercial_rows,monkeypatch):
    org,other,users=committed_commercial_rows
    plan=offer(org)
    remote=CheckoutNetwork(org,plan)
    key=uuid4()
    begin(org,users['OWNER'],plan,remote,key)
    customer=one('SELECT id FROM public.flow_customer_operations WHERE org_id=%s',[org])
    customers.confirm_registration(org,customer['id'],remote.token,remote.client)
    remote.status=2
    begin(org,users['OWNER'],plan,remote,key)
    adjustment=remote.invoice()
    adjustment['id']+=2
    adjustment['amount']=1234
    adjustment['payment']={**adjustment['payment'],'flowOrder':remote.payment_id+2,
                           'commerceOrder':str(adjustment['id']),'amount':1234}
    remote.start=remote.end
    remote.end+=timedelta(days=30)
    remote.invoice_id+=1
    remote.payment_id+=1
    original=remote.handle
    def with_adjustment(request):
        if request.url.path=='/api/subscription/get':
            return httpx.Response(200,json={**remote.subscription(),'invoices':[adjustment,remote.invoice()]})
        if request.url.path=='/api/invoice/get' and request.url.params['invoiceId']==str(adjustment['id']):
            return httpx.Response(200,json=adjustment)
        return original(request)
    remote.client=FlowClient(api_url='https://sandbox.flow.cl/api',api_key='fixture',secret_key='fixture',
                             transport=httpx.MockTransport(with_adjustment))
    monkeypatch.setattr(timezone,'now',lambda:remote.start)
    for _ in range(3):
        commerce.sync(org,remote.client,provider_timezone='UTC')
    assert_consistent(org,2000)
    assert len(rows('SELECT id FROM public.billing_periods WHERE org_id=%s',[org]))==2
    observation=one('SELECT * FROM public.billing_invoice_observations WHERE org_id=%s',[org])
    assert observation['evidence']['amount']==1234
    with wallet.financial_transaction(other):
        assert rows('SELECT id FROM public.billing_invoice_observations WHERE id=%s',[observation['id']])==[]
    with pytest.raises(DatabaseError),transaction.atomic():
        one('DELETE FROM public.billing_invoice_observations WHERE id=%s RETURNING id',[observation['id']])


def test_pack_checkout_paid_replay_and_expiry_preserve_purchased_lot(committed_commercial_rows,monkeypatch):
    org,_,users=committed_commercial_rows
    pack=offer(org,'PACK_1000',None)
    key=uuid4()
    posts=[]
    selected={}
    paid=False
    def handle(request):
        if request.url.path=='/api/payment/create':
            posts.append(request.url.path)
            selected.update({name:values[0] for name,values in parse_qs(request.content.decode()).items()})
            assert Decimal(selected['amount'])==pack['amount']
            return httpx.Response(200,json=dict(flowOrder=987654,url='https://sandbox.flow.cl/app/web/pay.php',token='fixture'))
        assert request.url.path in ('/api/payment/getStatus','/api/payment/getStatusByCommerceId')
        return httpx.Response(200,json=dict(flowOrder=987654,commerceOrder=selected['commerceOrder'],
                                           amount=int(pack['amount']),currency='CLP',status=2 if paid else 1))
    remote=type('PackNetwork',(),{'client':FlowClient(api_url='https://sandbox.flow.cl/api',api_key='fixture',
                              secret_key='fixture',transport=httpx.MockTransport(handle))})()
    assert begin(org,users['OWNER'],pack,remote,key)['state']=='redirect'
    assert begin(org,users['OWNER'],pack,remote,key)['state']=='pending'
    assert_consistent(org,500)
    paid=True
    order=one('SELECT id FROM public.billing_orders WHERE org_id=%s',[org])
    for _ in range(3):
        settlement.confirm(order['id'],'fixture',remote.client)
        assert begin(org,users['OWNER'],pack,remote,key)['state']=='succeeded'
    assert len(posts)==1
    assert_consistent(org,1500)
    end=timezone.now()+timedelta(days=8)
    monkeypatch.setattr(timezone,'now',lambda:end)
    summary=wallet.summary(org)
    assert summary['balance']==1000 and summary['plan']=='STARTER' and not summary['ai_available']
    assert [(lot['remaining'],lot['expires_at']) for lot in summary['lots'] if lot['origin']=='pack']==[(1000,None)]
    from django.core.management import call_command
    from io import StringIO
    output=StringIO()
    grant=next(lot['grant_id'] for lot in summary['lots'] if lot['origin']=='pack')
    call_command('prepare_billing_refund','--org',str(org),'--operation-key','admin-refund-fixture',
                 '--order',str(order['id']),'--amount',str(pack['amount']),'--reason','duplicate_charge',
                 '--authorization','approved-fixture-case','--grant',str(grant),stdout=output)
    assert one('SELECT state FROM public.flow_lifecycle_operations WHERE id=%s',[output.getvalue().strip()])['state']=='prepared'
    assert_consistent(org,1000)
