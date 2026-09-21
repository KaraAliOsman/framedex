"""Verified Flow payment → immutable evidence and due credit grants, in one transaction.

Order preparation requires frozen, approved commercial authority. This module does
not select a price, grant policy, subscription entitlement or cancellation policy.
No provider mutation is retried after an uncertain outcome.
"""

from decimal import Decimal, InvalidOperation
import hashlib
import json

from django.db import connection

from billing import wallet
from billing.flow import FlowError
from pricing.repository import one, rows


def _environment(client):
    return 'sandbox' if client.api_url == 'https://sandbox.flow.cl/api' else 'production'


def _payment(value):
    """Reduce provider data to required authority; never retain payer data or tokens."""
    try:
        if type(value['flowOrder']) is not int or value['flowOrder'] <= 0:
            raise ValueError()
        if type(value['status']) is not int or value['status'] not in (1, 2, 3, 4):
            raise ValueError()
        if not isinstance(value['commerceOrder'], str) or not value['commerceOrder']:
            raise ValueError()
        if type(value['amount']) not in (str, int, Decimal):
            raise ValueError()
        amount = Decimal(value['amount'])
        if (value['currency'] != 'CLP' or not amount.is_finite() or amount <= 0
                or amount != amount.to_integral_value()):
            raise ValueError()
        return {'flowOrder': str(value['flowOrder']), 'commerceOrder': value['commerceOrder'],
                'status': value['status'], 'currency': 'CLP', 'amount': format(amount, '.0f')}
    except (KeyError, TypeError, ValueError, InvalidOperation):
        raise FlowError('flow_invalid_payment') from None


def _order_scope(order_id):
    # Narrow privileged routing lookup by opaque server-created UUID, before assuming
    # tenant capability. It is NOT payment authority; all provider bindings follow.
    with connection.cursor() as cursor:
        cursor.execute('SELECT org_id FROM public.billing_orders WHERE id=%s', [order_id])
        found = cursor.fetchone()
    if found is None:
        raise FlowError('flow_unknown_order')
    return found[0]


def grant_due(org):
    """Caller holds the org lock. Replayed/late jobs cannot create duplicate credit."""
    schedules = rows('SELECT g.* FROM public.billing_credit_grants g '
                     'JOIN public.billing_orders o ON (o.org_id=g.org_id AND o.id=g.order_id) '
                     "WHERE g.org_id=%s AND o.state='succeeded' AND g.ledger_id IS NULL "
                     'AND g.available_at<=statement_timestamp() ORDER BY g.available_at,g.id FOR UPDATE OF g', [org])
    for grant in schedules:
        entry = wallet.append(org, grant['credits'], 'PAYMENT_GRANT', 'payment-grant:' + str(grant['id']),
                              grant['order_id'], grant['expires_at'])
        one('INSERT INTO public.credit_lots(org_id,grant_id,remaining,expires_at) '
            'VALUES(%s,%s,%s,%s) RETURNING id', [org, entry['id'], grant['credits'], grant['expires_at']])
        one('UPDATE public.billing_credit_grants SET ledger_id=%s WHERE org_id=%s AND id=%s RETURNING id',
            [entry['id'], org, grant['id']])


def confirm(order_id, token, client):
    """Public callback only supplies token + opaque routing ID. GET is safe to repeat."""
    org = _order_scope(order_id)
    # Network outside the row lock. Concurrent observations are folded monotonically.
    verified = _payment(client.payment_status(token))
    return _settle(org, order_id, verified, _environment(client))


def recover(order_id, client):
    """Recover a lost callback or an ambiguous create without issuing another charge."""
    org = _order_scope(order_id)
    with wallet.financial_transaction(org):
        order = one('SELECT * FROM public.billing_orders WHERE org_id=%s AND id=%s', [org, order_id])
    verified = _payment(client.payment_by_order(order['commerce_order']))
    return _settle(org, order_id, verified, _environment(client))


def _settle(org, order_id, verified, environment):
    with wallet.financial_transaction(org):
        wallet.locked_org(org)
        order = one('SELECT * FROM public.billing_orders WHERE org_id=%s AND id=%s FOR UPDATE', [org, order_id])
        if (order['provider_environment'] != environment or order['commerce_order'] != verified['commerceOrder']
                or order['amount'] != Decimal(verified['amount'])
                or order['provider_payment_id'] not in (None, verified['flowOrder'])):
            raise FlowError('flow_payment_binding_mismatch')
        # Flow supplies no webhook event ID: derive a stable observation identity from
        # the verified order/status, NOT a browser-supplied field or transient token.
        payload = json.dumps(verified, sort_keys=True, separators=(',', ':'))
        event_id = environment + ':' + hashlib.sha256(payload.encode()).hexdigest()
        if rows("SELECT id FROM public.payment_events WHERE org_id=%s AND provider='flow' AND event_id=%s",
                [org, event_id]):
            wallet.reconcile(org)
            return order['state']
        state = {1: 'pending', 2: 'succeeded', 3: 'failed', 4: 'failed'}[verified['status']]
        # A late pending/failed observation cannot undo a captured payment. A later
        # verified success can repair an earlier rejection; Flow supports payment retries.
        if order['state'] == 'succeeded' or (order['state'] == 'failed' and state == 'pending'):
            state = order['state']
        payment_id = order['payment_id']
        if payment_id is None:
            payment_id = one('INSERT INTO public.payments(org_id,subscription_id,provider,provider_payment_id,'
                             'amount,currency,status) VALUES(%s,%s,\'flow\',%s,%s,\'CLP\',%s) RETURNING id',
                             [org, order['subscription_id'], verified['flowOrder'], order['amount'], state])['id']
        else:
            one('UPDATE public.payments SET status=%s WHERE org_id=%s AND id=%s RETURNING id', [state, org, payment_id])
        one('UPDATE public.billing_orders SET state=%s,provider_payment_id=%s,payment_id=%s,updated_at=now() '
            'WHERE org_id=%s AND id=%s RETURNING id', [state, verified['flowOrder'], payment_id, org, order_id])
        one("INSERT INTO public.payment_events(org_id,provider,event_id,event_type,payload,processed_at) "
            "VALUES(%s,'flow',%s,'verified_payment_status',%s::jsonb,now()) RETURNING id", [org, event_id, payload])
        wallet.reconcile(org)
        return state


def dispatch_payment(order_id, client, *, email, subject, confirmation_url, return_url):
    """One durable dispatch claim. Crash/timeouts require GET recovery, never POST retry.

    Do not call inside an outer transaction: the claim must commit before network I/O.
    This one-time payment primitive is for packs; subscriptions use Flow's native API.
    """
    if connection.in_atomic_block:
        raise RuntimeError('Payment dispatch requires an outermost transaction boundary')
    org = _order_scope(order_id)
    with wallet.financial_transaction(org):
        wallet.locked_org(org)
        order = one('SELECT * FROM public.billing_orders WHERE org_id=%s AND id=%s FOR UPDATE', [org, order_id])
        if order['subscription_id'] is not None or order['provider_environment'] != _environment(client):
            raise FlowError('flow_payment_binding_mismatch')
        if order['state'] != 'prepared':
            raise FlowError('flow_reconciliation_required', uncertain=True)
        one("UPDATE public.billing_orders SET state='dispatching',updated_at=now() "
            'WHERE org_id=%s AND id=%s RETURNING id', [org, order_id])
    try:
        created = client.create_payment(order=order['commerce_order'], subject=subject, amount=order['amount'],
                                       email=email, confirmation_url=confirmation_url, return_url=return_url)
        redirect = client.redirect_url(created)
        if type(created.get('flowOrder')) is not int or created['flowOrder'] <= 0:
            raise FlowError('flow_invalid_payment', uncertain=True)
        with wallet.financial_transaction(org):
            wallet.locked_org(org)
            current = one('SELECT * FROM public.billing_orders WHERE org_id=%s AND id=%s', [org, order_id])
            if current['provider_payment_id'] not in (None, str(created['flowOrder'])):
                raise FlowError('flow_payment_binding_mismatch', uncertain=True)
            one('UPDATE public.billing_orders SET provider_payment_id=%s,'
                "state=CASE WHEN state='dispatching' THEN 'pending' ELSE state END,updated_at=now() "
                'WHERE org_id=%s AND id=%s RETURNING id', [str(created['flowOrder']), org, order_id])
        return redirect
    except FlowError:
        with wallet.financial_transaction(org):
            rows("UPDATE public.billing_orders SET state='uncertain',updated_at=now() "
                 "WHERE org_id=%s AND id=%s AND state='dispatching' RETURNING id", [org, order_id])
        raise
