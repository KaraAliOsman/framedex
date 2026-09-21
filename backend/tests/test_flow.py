"""Network-seam contract tests, never presented as a Flow sandbox pass."""

from decimal import Decimal
import hashlib
import hmac
from urllib.parse import parse_qs

import httpx
import pytest

from billing.flow import FlowClient, FlowError, signed_parameters


def client(handler):
    return FlowClient(api_url='https://sandbox.flow.cl/api', api_key='merchant-fixture',
                      secret_key='secret-fixture', transport=httpx.MockTransport(handler))


def test_signature_matches_independent_flow_algorithm():
    value = signed_parameters({'currency': 'CLP', 'amount': '5000'}, 'XXXX', 'test-key')
    expected = hmac.new(b'test-key', b'amount5000apiKeyXXXXcurrencyCLP', hashlib.sha256).hexdigest()
    assert value['s'] == expected
    with pytest.raises(ValueError):
        signed_parameters({'s': 'spoofed'}, 'XXXX', 'test-key')


def test_confirmation_token_is_looked_up_with_signed_get_and_exact_money():
    def handler(request):
        assert request.method == 'GET'
        assert request.url.path == '/api/payment/getStatus'
        assert request.url.params['token'] == 'callback-token'
        assert request.url.params['s'] == signed_parameters(
            {'token': 'callback-token'}, 'merchant-fixture', 'secret-fixture')['s']
        return httpx.Response(200, content=b'{"amount":43857.00,"status":2,"flowOrder":123}')
    assert client(handler).payment_status('callback-token')['amount'] == Decimal('43857.00')


def test_checkout_form_uses_integral_clp():
    def handler(request):
        assert request.headers['content-type'] == 'application/x-www-form-urlencoded'
        data = parse_qs(request.content.decode())
        assert data['amount'] == ['43857']
        assert data['commerceOrder'] == ['persisted-operation']
        assert data['currency'] == ['CLP']
        return httpx.Response(200, json={'token': 'checkout', 'url': 'https://sandbox.flow.cl/pay.php'})
    flow = client(handler)
    response = flow.create_payment(order='persisted-operation', subject='Plan', amount=Decimal('43857'),
                                   email='fixture@example.com', confirmation_url='https://api.example/callback',
                                   return_url='https://app.example/settings/billing')
    assert flow.redirect_url(response) == 'https://sandbox.flow.cl/pay.php?token=checkout'


@pytest.mark.parametrize('operation,path,parameters', [
    (lambda f: f.create_subscription(customer_id='customer', plan_id='plan'),
     '/api/subscription/create', {'customerId': ['customer'], 'planId': ['plan']}),
    (lambda f: f.cancel_subscription('subscription', at_period_end=True),
     '/api/subscription/cancel', {'subscriptionId': ['subscription'], 'at_period_end': ['1']}),
    (lambda f: f.register_customer('customer', 'https://api.example/register'),
     '/api/customer/register', {'customerId': ['customer'], 'url_return': ['https://api.example/register']}),
])
def test_native_subscription_contract(operation, path, parameters):
    def handler(request):
        assert request.url.path == path
        assert request.method == 'POST'
        data = parse_qs(request.content.decode())
        assert all(data[key] == value for key, value in parameters.items())
        return httpx.Response(200, json={'status': 1})
    operation(client(handler))


def test_ambiguous_create_never_retries_or_exposes_provider_secrets():
    calls = []
    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout('a secret might appear in transport errors')
    with pytest.raises(FlowError) as error:
        client(handler).create_subscription(customer_id='customer', plan_id='plan')
    assert error.value.uncertain
    assert str(error.value) == 'flow_unavailable'
    assert len(calls) == 1


@pytest.mark.parametrize('url', ['http://sandbox.flow.cl/pay', 'https://evil.example/pay',
                                'https://sandbox.flow.cl@evil.example/pay',
                                'https://www.flow.cl/pay', 'https://sandbox.flow.cl/pay?token=x'])
def test_rejects_redirect_to_untrusted_or_wrong_environment_origin(url):
    with pytest.raises(FlowError):
        client(lambda _: None).redirect_url({'url': url, 'token': 'token'})


@pytest.mark.parametrize('body', [b'[]', b'{"amount":NaN}', b'not json'])
def test_rejects_invalid_provider_response(body):
    with pytest.raises(FlowError):
        client(lambda _: httpx.Response(200, content=body)).payment_status('token')


@pytest.mark.parametrize('operation,path,parameters', [
    (lambda f: f.change_plan_preview('sus','plan'), '/api/subscription/changePlanPreview', {'subscriptionId':['sus'],'newPlanId':['plan']}),
    (lambda f: f.change_plan('sus','plan',start_date='2026-10-01'), '/api/subscription/changePlan', {'startDateOfNewPlan':['2026-10-01']}),
    (lambda f: f.create_refund(order='refund',payment_id='123',amount=Decimal('100'),email='test@example.test',callback_url='https://example.test/callback'),
     '/api/refund/create', {'flowTrxId':['123'],'amount':['100'],'urlCallBack':['https://example.test/callback']}),
])
def test_lifecycle_native_endpoints(operation,path,parameters):
    def handler(request):
        assert request.method=='POST' and request.url.path==path
        data=parse_qs(request.content.decode())
        assert all(data[key]==value for key,value in parameters.items())
        return httpx.Response(200,json={})
    operation(client(handler))
