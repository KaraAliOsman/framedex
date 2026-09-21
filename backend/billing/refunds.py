"""Exceptional, explicitly authorized refunds with immutable compensation evidence."""

from decimal import Decimal
import hashlib
import hmac

from django.db import connection
from django.utils import timezone

from billing import changes, lifecycle, wallet
from billing.flow import FlowError
from billing.settlement import _environment
from billing.repository import one, rows

REASONS = {'duplicate_charge', 'incorrect_amount', 'activation_failed', 'legal_obligation', 'administrative'}


def prepare(org, *, operation_key, order_id, amount, reason, authorization, grant_ids, revoke_period=False):
    """Administrative service only: explicit amount and affected grants, never debt inference."""
    if (reason not in REASONS or not isinstance(authorization, str) or not authorization.strip()
            or not isinstance(amount, Decimal) or not amount.is_finite() or amount <= 0 or amount != amount.to_integral_value()):
        raise ValueError('Explicit administrative refund authority required')
    with wallet.financial_transaction(org):
        wallet.locked_org(org)
        order = one('SELECT * FROM public.billing_orders WHERE org_id=%s AND id=%s', [org, order_id])
        if order['state'] != 'succeeded':
            raise FlowError('refund_paid_order_required')
        authority = dict(order_id=str(order_id), payment_id=order['provider_payment_id'], amount=str(amount),
                         environment=order['provider_environment'], reason=reason, authorization=authorization,
                         grant_ids=sorted(str(value) for value in set(grant_ids)), revoke_period=revoke_period)
        previous = rows('SELECT * FROM public.flow_lifecycle_operations WHERE org_id=%s AND operation_key=%s',
                        [org, operation_key])
        if previous:
            if previous[0]['kind'] != 'refund' or previous[0]['authority'] != authority:
                raise FlowError('refund_replay_conflict')
            return previous[0]
        reserved = rows("SELECT authority FROM public.flow_lifecycle_operations WHERE org_id=%s AND kind='refund' "
                        "AND authority->>'order_id'=%s", [org, str(order_id)])
        if sum((Decimal(r['authority']['amount']) for r in reserved), Decimal(0)) + amount > order['amount']:
            raise FlowError('refund_exceeds_paid_amount')
        # A refund cannot remove an unrelated grant, including one in the same tenant.
        for grant_id in authority['grant_ids']:
            if not rows('SELECT l.id FROM public.credit_lots l JOIN public.credit_ledger e ON e.id=l.grant_id '
                        'WHERE l.org_id=%s AND l.grant_id=%s AND (e.reference_id=%s OR e.reference_id IN '
                        '(SELECT id FROM public.billing_periods WHERE org_id=%s AND order_id=%s))',
                        [org, grant_id, order_id, org, order_id]):
                raise FlowError('refund_grant_binding_mismatch')
        return one('INSERT INTO public.flow_lifecycle_operations(org_id,subscription_id,operation_key,kind,authority) '
                   "VALUES(%s,%s,%s,'refund',%s::jsonb) RETURNING *",
                   [org, order['subscription_id'], operation_key, lifecycle.dump(authority)])


def dispatch(org, operation_id, client, *, receiver_email, callback_url):
    if connection.in_atomic_block:
        raise RuntimeError('Refund dispatch requires outermost transaction boundary')
    with wallet.financial_transaction(org):
        wallet.locked_org(org)
        op = one('SELECT * FROM public.flow_lifecycle_operations WHERE org_id=%s AND id=%s FOR UPDATE', [org, operation_id])
        if op['kind'] != 'refund' or op['authority']['environment'] != _environment(client):
            raise FlowError('refund_binding_mismatch')
        if op['state'] != 'prepared':
            raise FlowError('refund_reconciliation_required', uncertain=True)
        one("UPDATE public.flow_lifecycle_operations SET state='dispatching' WHERE org_id=%s AND id=%s RETURNING id",
            [org, operation_id])
    try:
        value = client.create_refund(order=str(operation_id), payment_id=op['authority']['payment_id'],
                                     amount=Decimal(op['authority']['amount']), email=receiver_email, callback_url=callback_url)
        token = value.get('token')
        if not isinstance(token, str) or not token:
            raise FlowError('refund_token_missing', uncertain=True)
        # Establish the binding from our POST response; callback tokens cannot invent it.
        observation = _observation(value)
        if Decimal(observation['amount']) != Decimal(op['authority']['amount']):
            raise FlowError('refund_amount_mismatch', uncertain=True)
        with wallet.financial_transaction(org):
            one('UPDATE public.flow_lifecycle_operations SET preview=%s::jsonb WHERE org_id=%s AND id=%s RETURNING id',
                [lifecycle.dump({'token_hash': hashlib.sha256(token.encode()).hexdigest(),
                                 'provider_refund_id': observation['flowRefundOrder']}), org, operation_id])
        return confirm(org, operation_id, token, client)
    except FlowError:
        with wallet.financial_transaction(org):
            rows("UPDATE public.flow_lifecycle_operations SET state='uncertain' WHERE org_id=%s AND id=%s "
                 "AND state='dispatching' RETURNING id", [org, operation_id])
        raise


def _observation(value):
    if (value.get('status') not in ('created', 'accepted', 'rejected', 'refunded', 'canceled')
            or not isinstance(value.get('flowRefundOrder'), str) or not value['flowRefundOrder']):
        raise FlowError('refund_invalid_response')
    return {'flowRefundOrder': value['flowRefundOrder'], 'status': value['status'],
            'amount': format(changes._money(value.get('amount')), '.0f')}


def confirm(org, operation_id, token, client):
    op = changes._read(org, operation_id)
    if (op['kind'] != 'refund' or op['authority']['environment'] != _environment(client) or op['preview'] is None
            or not hmac.compare_digest(op['preview']['token_hash'], hashlib.sha256(token.encode()).hexdigest())):
        raise FlowError('refund_binding_mismatch')
    observation = _observation(client.refund_status(token))
    if (observation['flowRefundOrder'] != op['preview']['provider_refund_id']
            or Decimal(observation['amount']) != Decimal(op['authority']['amount'])):
        raise FlowError('refund_binding_mismatch')
    with wallet.financial_transaction(org):
        wallet.locked_org(org)
        current = one('SELECT * FROM public.flow_lifecycle_operations WHERE org_id=%s AND id=%s FOR UPDATE', [org, operation_id])
        if current['state'] in ('confirmed', 'needs_admin'):
            return current['result']
        payload = lifecycle.dump(observation)
        event_id = 'refund:' + _environment(client) + ':' + hashlib.sha256(payload.encode()).hexdigest()
        rows("INSERT INTO public.payment_events(org_id,provider,event_id,event_type,payload,processed_at) "
             "VALUES(%s,'flow',%s,'verified_refund_status',%s::jsonb,now()) ON CONFLICT(provider,event_id) DO NOTHING RETURNING id",
             [org, event_id, payload])
        state = 'dispatching'
        if observation['status'] == 'refunded':
            state = 'confirmed' if _compensate(org, current) else 'needs_admin'
        one('UPDATE public.flow_lifecycle_operations SET state=%s,result=%s::jsonb WHERE org_id=%s AND id=%s RETURNING id',
            [state, payload, org, operation_id])
    return observation


def _compensate(org, op):
    authority = op['authority']
    lots = []
    for grant_id in authority['grant_ids']:
        lot = one('SELECT * FROM public.credit_lots WHERE org_id=%s AND grant_id=%s FOR UPDATE', [org, grant_id])
        spent = rows("SELECT m.id FROM public.credit_lot_movements m JOIN public.credit_ledger e ON e.id=m.ledger_id "
                     "WHERE m.org_id=%s AND m.lot_id=%s AND e.action_type='AI_DEBIT'", [org, lot['id']])
        if spent:
            return False
        lots.append(lot)
    periods = rows('SELECT * FROM public.billing_periods WHERE org_id=%s AND order_id=%s', [org, authority['order_id']])
    if authority['revoke_period'] and periods:
        period = periods[0]
        # Upgrade benefits are a separate monetary authority; do not undo them implicitly.
        if rows("SELECT id FROM public.billing_lifecycle_events WHERE org_id=%s AND period_id=%s AND kind='upgrade'",
                [org, period['id']]):
            return False
        # Revoke only if all remaining grants for this period were explicitly authorized.
        extra = rows('SELECT l.grant_id FROM public.credit_lots l JOIN public.credit_ledger e ON e.id=l.grant_id '
                     'WHERE l.org_id=%s AND e.reference_id=%s AND l.remaining>0', [org, period['id']])
        if any(str(row['grant_id']) not in authority['grant_ids'] for row in extra):
            return False
    for lot in lots:
        wallet.expire_lot(org, lot, key='refund:' + str(op['id']) + ':' + str(lot['id']), action='REFUND_REVERSAL')
    if authority['revoke_period'] and periods:
        lifecycle.record_change(org, period_id=periods[0]['id'], operation_key='refund:' + str(op['id']), kind='refund',
                                effective_at=timezone.now(), plan_tier='STARTER', billing_cycle=periods[0]['billing_cycle'],
                                evidence={'administrative_authorization': authority['authorization'],
                                          'refund_operation': str(op['id'])})
    return True


def confirm_callback(operation_id, token, client):
    with connection.cursor() as cursor:
        cursor.execute("SELECT org_id FROM public.flow_lifecycle_operations WHERE id=%s AND kind='refund'", [operation_id])
        found = cursor.fetchone()
    if not found:
        raise FlowError('refund_unknown_operation')
    return confirm(found[0], operation_id, token, client)
