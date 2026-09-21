"""Real database customer idempotency and token-binding proofs; HTTP only is simulated."""

from concurrent.futures import ThreadPoolExecutor
import hashlib
from uuid import uuid4

from django.db import close_old_connections, transaction, DatabaseError
import httpx
import pytest
from rest_framework.test import APIClient

from billing import customers, wallet
from billing.flow import FlowClient, FlowError
from pricing.repository import one, rows
from backend.tests.integration.test_shot08_pricing import (
    commercial_rows as commercial_rows, committed_commercial_rows as committed_commercial_rows, as_user,
)
from backend.tests.integration.test_shot11_wallet import assert_consistent

pytestmark = pytest.mark.rls_integration


class Network:
    def __init__(self, org, operation, *, timeout=False):
        self.org, self.operation, self.timeout = org, operation, timeout
        self.posts = 0
        self.registrations = 0
        self.present = False
        self.customer_id = 'cus_' + uuid4().hex
        self.token = 'register_' + uuid4().hex
        self.registered_customer = self.customer_id
        self.status = '1'
        self.client = FlowClient(api_url='https://sandbox.flow.cl/api', api_key='synthetic', secret_key='synthetic',
                                 transport=httpx.MockTransport(self.handle))

    def customer(self):
        return dict(customerId=self.customer_id, externalId=str(self.org), email=self.operation['email'])

    def handle(self, request):
        path = request.url.path
        if path == '/api/customer/create':
            assert request.method == 'POST'
            self.posts += 1
            self.present = True
            if self.timeout:
                raise httpx.ReadTimeout('synthetic lost successful create response')
            value = self.customer()
        elif path == '/api/customer/list':
            value = dict(hasMore=0, data=[self.customer()] if self.present else [])
        elif path == '/api/customer/get':
            value = self.customer()
        elif path == '/api/customer/register':
            assert request.method == 'POST'
            self.registrations += 1
            value = dict(url='https://sandbox.flow.cl/app/customer/disclaimer.php', token=self.token)
        elif path == '/api/customer/getRegisterStatus':
            assert request.url.params['token'] == self.token
            value = dict(status=self.status, customerId=self.registered_customer,
                         cardNumber='SYNTHETIC-DO-NOT-STORE', last4CardDigits='0000')
        else:
            pytest.fail('Unexpected provider call: ' + path)
        return httpx.Response(200, json=value)


def prepare(org):
    return customers.prepare(org, environment='sandbox', name='Synthetic verified owner', email='synthetic@example.invalid')


def test_customer_create_replay_and_registration_store_no_card_or_raw_token(committed_commercial_rows):
    org, _, _ = committed_commercial_rows
    operation = prepare(org)
    remote = Network(org, operation)
    first = customers.dispatch(org, operation['id'], remote.client)
    assert customers.dispatch(org, operation['id'], remote.client) == first
    assert remote.posts == 1
    redirect = customers.register(org, operation['id'], remote.client, return_url='https://example.invalid/return')
    assert redirect.endswith('?token=' + remote.token)
    for _ in range(2):
        assert customers.confirm_registration(org, operation['id'], remote.token, remote.client) == 'registered'
    saved = one('SELECT * FROM public.flow_customer_operations WHERE id=%s', [operation['id']])
    assert saved['registration_token_hash'] == hashlib.sha256(remote.token.encode()).hexdigest()
    assert remote.token not in str(saved) and 'SYNTHETIC-DO-NOT-STORE' not in str(saved)
    assert_consistent(org, 500)


def test_customer_timeout_recovers_without_repeating_create(committed_commercial_rows):
    org, _, _ = committed_commercial_rows
    operation = prepare(org)
    remote = Network(org, operation, timeout=True)
    for _ in range(2):
        with pytest.raises(FlowError):
            customers.dispatch(org, operation['id'], remote.client)
    assert remote.posts == 1
    local = customers.recover(org, operation['id'], remote.client)
    assert one('SELECT provider_customer_id FROM public.payment_customers WHERE id=%s', [local])['provider_customer_id'] == remote.customer_id


def test_concurrent_customer_creation_claims_one_post(committed_commercial_rows):
    org, _, _ = committed_commercial_rows
    operation = prepare(org)
    remote = Network(org, operation)
    def create(_):
        close_old_connections()
        try:
            return customers.dispatch(org, operation['id'], remote.client)
        except FlowError:
            return None
        finally:
            close_old_connections()
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(create, range(4)))
    assert any(results) and remote.posts == 1


def test_registration_rejects_wrong_token_customer_and_duplicate_dispatch(committed_commercial_rows):
    org, _, _ = committed_commercial_rows
    operation = prepare(org)
    remote = Network(org, operation)
    customers.dispatch(org, operation['id'], remote.client)
    customers.register(org, operation['id'], remote.client, return_url='https://example.invalid/return')
    with pytest.raises(FlowError):
        customers.register(org, operation['id'], remote.client, return_url='https://example.invalid/return')
    assert remote.registrations == 1
    with pytest.raises(FlowError):
        customers.confirm_registration(org, operation['id'], 'forged', remote.client)
    remote.registered_customer = 'cus_foreign'
    with pytest.raises(FlowError):
        customers.confirm_registration(org, operation['id'], remote.token, remote.client)


def test_customer_identity_is_frozen_and_inaccessible_to_other_tenants(commercial_rows):
    org, other, users = commercial_rows
    operation = prepare(org)
    assert prepare(org)['id'] == operation['id']
    with pytest.raises(FlowError):
        customers.prepare(org, environment='sandbox', name='Different owner', email='synthetic@example.invalid')
    with wallet.financial_transaction(other):
        assert rows('SELECT * FROM public.flow_customer_operations') == []
    with as_user(users['OWNER']):
        with pytest.raises(DatabaseError), transaction.atomic():
            rows('SELECT * FROM public.flow_customer_operations')


def test_negative_registration_cannot_downgrade_verified_registration(committed_commercial_rows):
    org, _, _ = committed_commercial_rows
    operation = prepare(org)
    remote = Network(org, operation)
    customers.dispatch(org, operation['id'], remote.client)
    customers.register(org, operation['id'], remote.client, return_url='https://example.invalid/return')
    assert customers.confirm_registration(org, operation['id'], remote.token, remote.client) == 'registered'
    remote.status = '0'
    assert customers.confirm_registration(org, operation['id'], remote.token, remote.client) == 'registered'


def test_public_registration_callback_uses_provider_identity_and_ignores_body_status(committed_commercial_rows, monkeypatch):
    org, other, _ = committed_commercial_rows
    operation = prepare(org)
    remote = Network(org, operation)
    customers.dispatch(org, operation['id'], remote.client)
    customers.register(org, operation['id'], remote.client, return_url='https://example.invalid/return')
    monkeypatch.setattr('billing.views.FlowClient', lambda **kwargs: remote.client)
    remote.status = '0'
    result = APIClient().post(f"/api/v1/billing/flow/register/{operation['id']}/",
                              f'token={remote.token}&status=1&org_id={other}',
                              content_type='application/x-www-form-urlencoded')
    assert result.status_code == 200
    saved = one('SELECT registration_state FROM public.flow_customer_operations WHERE id=%s', [operation['id']])
    assert saved['registration_state'] == 'failed'
