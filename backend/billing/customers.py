"""Durable Flow customer creation and registration. Never stores card data or raw tokens."""

import hashlib
import hmac

from django.db import connection

from billing import wallet
from billing.flow import FlowError
from billing.settlement import _environment
from pricing.repository import one, rows


def prepare(org, *, environment, name, email):
    """Inputs must come from verified OWNER identity and organization records."""
    if environment not in ('sandbox', 'production') or not name.strip() or not email.strip():
        raise ValueError('Verified customer identity required')
    with wallet.financial_transaction(org):
        wallet.locked_org(org)
        existing = rows('SELECT * FROM public.flow_customer_operations WHERE org_id=%s AND provider_environment=%s',
                        [org, environment])
        if existing:
            if existing[0]['name'] != name or existing[0]['email'] != email:
                raise FlowError('flow_customer_replay_conflict')
            return existing[0]
        if rows("SELECT id FROM public.payment_customers WHERE org_id=%s AND provider='flow'", [org]):
            raise FlowError('flow_existing_customer_requires_binding')
        return one('INSERT INTO public.flow_customer_operations(org_id,provider_environment,name,email) '
                   'VALUES(%s,%s,%s,%s) RETURNING *', [org, environment, name, email])


def _read(org, operation_id, client):
    with wallet.financial_transaction(org):
        found = rows('SELECT o.*,c.provider_customer_id FROM public.flow_customer_operations o '
                     'LEFT JOIN public.payment_customers c ON(c.org_id=o.org_id AND c.id=o.customer_id) '
                     'WHERE o.org_id=%s AND o.id=%s', [org, operation_id])
        if len(found) != 1 or found[0]['provider_environment'] != _environment(client):
            raise FlowError('flow_customer_binding_mismatch')
        return found[0]


def _accept(org, operation_id, client, value):
    customer = value.get('customerId')
    operation = _read(org, operation_id, client)
    if (not isinstance(customer, str) or not customer or value.get('externalId') != str(org)
            or value.get('email') != operation['email']):
        raise FlowError('flow_customer_binding_mismatch', uncertain=True)
    with wallet.financial_transaction(org):
        wallet.locked_org(org)
        operation = _read(org, operation_id, client)
        if operation['state'] not in ('dispatching', 'uncertain', 'created'):
            raise FlowError('flow_customer_not_dispatched')
        if operation['customer_id'] is not None:
            if operation['provider_customer_id'] != customer:
                raise FlowError('flow_customer_binding_mismatch')
            return operation['customer_id']
        local = one("INSERT INTO public.payment_customers(org_id,provider,provider_customer_id) "
                    "VALUES(%s,'flow',%s) RETURNING id", [org, customer])
        one("UPDATE public.flow_customer_operations SET state='created',customer_id=%s "
            'WHERE org_id=%s AND id=%s RETURNING id', [local['id'], org, operation_id])
        return local['id']


def dispatch(org, operation_id, client):
    if connection.in_atomic_block:
        raise RuntimeError('Customer dispatch requires an outermost transaction boundary')
    operation = _read(org, operation_id, client)
    if operation['state'] == 'created':
        return operation['customer_id']
    with wallet.financial_transaction(org):
        wallet.locked_org(org)
        changed = rows("UPDATE public.flow_customer_operations SET state='dispatching' "
                       "WHERE org_id=%s AND id=%s AND state='prepared' RETURNING id", [org, operation_id])
        if not changed:
            raise FlowError('flow_customer_reconciliation_required', uncertain=True)
    try:
        return _accept(org, operation_id, client, client.create_customer(
            external_id=str(org), name=operation['name'], email=operation['email']))
    except FlowError:
        with wallet.financial_transaction(org):
            rows("UPDATE public.flow_customer_operations SET state='uncertain' "
                 "WHERE org_id=%s AND id=%s AND state='dispatching' RETURNING id", [org, operation_id])
        raise


def recover(org, operation_id, client):
    operation = _read(org, operation_id, client)
    if operation['state'] == 'created':
        return operation['customer_id']
    if operation['state'] not in ('dispatching', 'uncertain'):
        raise FlowError('flow_customer_not_dispatched')
    matches = []
    for start in range(0, 10000, 100):
        page = client.customers(start=start)
        if (not isinstance(page.get('data'), list) or type(page.get('hasMore')) is not int
                or page['hasMore'] not in (0, 1)):
            raise FlowError('flow_invalid_customer_list')
        for item in page['data']:
            if not isinstance(item, dict) or not isinstance(item.get('customerId'), str):
                raise FlowError('flow_invalid_customer_list')
            value = client.customer(item['customerId'])
            if value.get('externalId') == str(org):
                matches.append(value)
        if page['hasMore'] == 0:
            if len(matches) != 1:
                raise FlowError('flow_customer_reconciliation_required', uncertain=True)
            return _accept(org, operation_id, client, matches[0])
    raise FlowError('flow_customer_reconciliation_limit')


def register(org, operation_id, client, *, return_url):
    if connection.in_atomic_block:
        raise RuntimeError('Card registration requires an outermost transaction boundary')
    operation = _read(org, operation_id, client)
    with wallet.financial_transaction(org):
        wallet.locked_org(org)
        changed = rows("UPDATE public.flow_customer_operations SET registration_state='dispatching',registration_token_hash=NULL "
                       "WHERE org_id=%s AND id=%s AND state='created' AND registration_state IN ('none','failed') RETURNING id",
                       [org, operation_id])
        if not changed:
            raise FlowError('flow_registration_reconciliation_required', uncertain=True)
    try:
        value = client.register_customer(operation['provider_customer_id'], return_url)
        redirect = client.redirect_url(value)
        digest = hashlib.sha256(value['token'].encode()).hexdigest()
        with wallet.financial_transaction(org):
            one("UPDATE public.flow_customer_operations SET registration_state='pending',registration_token_hash=%s "
                'WHERE org_id=%s AND id=%s RETURNING id', [digest, org, operation_id])
        return redirect
    except FlowError:
        with wallet.financial_transaction(org):
            rows("UPDATE public.flow_customer_operations SET registration_state='uncertain' "
                 "WHERE org_id=%s AND id=%s AND registration_state='dispatching' RETURNING id", [org, operation_id])
        raise


def confirm_registration(org, operation_id, token, client):
    operation = _read(org, operation_id, client)
    digest = hashlib.sha256(token.encode()).hexdigest()
    if (operation['registration_token_hash'] is None
            or not hmac.compare_digest(operation['registration_token_hash'], digest)):
        raise FlowError('flow_registration_token_mismatch')
    value = client.registration_status(token)
    # API documents status as a string for customer registration, unlike PaymentStatus.
    if value.get('customerId') != operation['provider_customer_id'] or value.get('status') not in ('0', '1'):
        raise FlowError('flow_registration_binding_mismatch')
    state = 'registered' if value['status'] == '1' else 'failed'
    with wallet.financial_transaction(org):
        wallet.locked_org(org)
        current = _read(org, operation_id, client)
        if current['registration_token_hash'] != digest:
            raise FlowError('flow_registration_token_mismatch')
        if current['registration_state'] == 'registered':
            return 'registered'
        one('UPDATE public.flow_customer_operations SET registration_state=%s WHERE org_id=%s AND id=%s RETURNING id',
            [state, org, operation_id])
    return state


def confirm_callback(operation_id, token, client):
    # Privileged routing lookup only; the callback supplies no organization authority.
    found = rows('SELECT org_id FROM public.flow_customer_operations WHERE id=%s', [operation_id])
    if len(found) != 1:
        raise FlowError('flow_unknown_customer_operation')
    return confirm_registration(found[0]['org_id'], operation_id, token, client)
