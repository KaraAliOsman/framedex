"""Durable native plan changes/cancellation; Flow alone computes monetary proration."""

from datetime import datetime, time
from decimal import Decimal, InvalidOperation
import json
from zoneinfo import ZoneInfo

from django.db import connection
from django.utils import timezone

from billing import lifecycle, wallet
from billing.flow import FlowError
from billing.settlement import _environment
from billing.repository import one, rows


def provider_time(value, timezone_name):
    """The merchant's explicitly configured provider timezone normalizes naive API dates."""
    if not isinstance(value, str):
        raise FlowError('flow_invalid_period')
    try:
        parsed = datetime.fromisoformat(value)
        if timezone.is_naive(parsed):
            parsed = parsed.replace(tzinfo=ZoneInfo(timezone_name))
        return parsed
    except (ValueError, TypeError):
        raise FlowError('flow_invalid_period') from None


def _current(org, client):
    with wallet.financial_transaction(org):
        wallet.locked_org(org)
        intent = one("SELECT * FROM public.flow_subscription_intents WHERE org_id=%s AND state='created'", [org])
        period = one('SELECT * FROM public.billing_periods WHERE org_id=%s AND subscription_id=%s '
                     'AND period_start<=%s AND period_end>%s ORDER BY period_start DESC LIMIT 1',
                     [org, intent['subscription_id'], timezone.now(), timezone.now()])
        if intent['provider_environment'] != _environment(client):
            raise FlowError('flow_subscription_binding_mismatch')
        operations = rows("SELECT o.result FROM public.flow_lifecycle_operations o JOIN public.billing_lifecycle_events e "
                          "ON e.org_id=o.org_id AND e.operation_key='flow:' || o.id::text WHERE o.org_id=%s "
                          "AND o.kind='change' AND o.state='confirmed' AND e.effective_at<=%s "
                          "ORDER BY e.effective_at DESC,e.created_at DESC LIMIT 1", [org, timezone.now()])
        plan_id = operations[0]['result'].get('new_plan_id') if operations else intent['provider_plan_id']
        return intent, period, plan_id


def _remote(intent, period, client, timezone_name, expected_plan):
    remote = client.subscription(intent['provider_subscription_id'])
    if (remote.get('subscriptionId') != intent['provider_subscription_id']
            or remote.get('customerId') != intent['provider_customer_id']
            or remote.get('planId') != expected_plan or remote.get('status') != 1
            or provider_time(remote.get('period_start'), timezone_name) != period['period_start']
            or provider_time(remote.get('period_end'), timezone_name) != period['period_end']):
        raise FlowError('flow_subscription_binding_mismatch')
    return remote


def _money(value):
    try:
        if type(value) not in (int, str, Decimal):
            raise ValueError()
        amount = Decimal(value)
        if not amount.is_finite() or amount != amount.to_integral_value():
            raise ValueError()
        return amount
    except (InvalidOperation, ValueError):
        raise FlowError('flow_invalid_proration') from None


def _read(org, operation_id):
    with wallet.financial_transaction(org):
        return one('SELECT * FROM public.flow_lifecycle_operations WHERE org_id=%s AND id=%s', [org, operation_id])


def _store(org, subscription_id, operation_key, kind, authority, preview=None):
    with wallet.financial_transaction(org):
        wallet.locked_org(org)
        prior = rows('SELECT * FROM public.flow_lifecycle_operations WHERE org_id=%s AND operation_key=%s',
                     [org, operation_key])
        if prior:
            if prior[0]['kind'] != kind or prior[0]['authority'] != authority:
                raise FlowError('flow_operation_replay_conflict')
            return prior[0]
        if rows("SELECT id FROM public.flow_lifecycle_operations WHERE org_id=%s AND kind IN ('change','cancel') "
                "AND state IN ('prepared','dispatching','uncertain')", [org]):
            raise FlowError('flow_operation_pending')
        if rows("SELECT id FROM public.billing_lifecycle_events WHERE org_id=%s AND subscription_id=%s "
                "AND kind IN ('downgrade','frequency','cancel') AND effective_at>%s",
                [org,subscription_id,timezone.now()]):
            raise FlowError('flow_scheduled_operation_pending')
        return one('INSERT INTO public.flow_lifecycle_operations(org_id,subscription_id,operation_key,kind,authority,preview) '
                   'VALUES(%s,%s,%s,%s,%s::jsonb,%s::jsonb) RETURNING *',
                   [org, subscription_id, operation_key, kind, lifecycle.dump(authority),
                    lifecycle.dump(preview) if preview is not None else None])


def prepare_change(org, *, operation_key, target, client, provider_timezone):
    """target is a trusted provisioned plan, never browser price/provider identity."""
    intent, period, old_plan = _current(org, client)
    current = lifecycle.plan_at_in_transaction(org, period, timezone.now())
    if target['plan_tier'] not in lifecycle.ALLOWANCES or target['billing_cycle'] not in ('monthly', 'annual'):
        raise ValueError('Provisioned plan required')
    _remote(intent, period, client, provider_timezone, old_plan)
    plan = client.plan(target['provider_plan_id'])
    if (plan.get('planId') != target['provider_plan_id'] or plan.get('currency') != 'CLP'
            or _money(plan.get('amount')) != Decimal(target['amount'])
            or plan.get('interval') != {'monthly': 3, 'annual': 4}[target['billing_cycle']]
            or plan.get('interval_count') != 1):
        raise FlowError('flow_plan_binding_mismatch')
    if target['billing_cycle'] != period['billing_cycle']:
        kind = 'frequency'
    elif lifecycle.ALLOWANCES[target['plan_tier']] > current['allowance']:
        kind = 'upgrade'
    elif lifecycle.ALLOWANCES[target['plan_tier']] < current['allowance']:
        kind = 'downgrade'
    else:
        raise FlowError('flow_plan_unchanged')
    deferred = kind != 'upgrade'
    # Flow's scheduled API has DATE precision. Never silently truncate a paid boundary.
    boundary = period['period_end'].astimezone(ZoneInfo(provider_timezone))
    if deferred and boundary.time() != time.min:
        raise FlowError('flow_schedule_boundary_requires_reconciliation')
    start = boundary.date().isoformat() if deferred else None
    preview = client.change_plan_preview(intent['provider_subscription_id'], target['provider_plan_id'], start_date=start)
    _validate_preview(preview, target, deferred)
    authority = dict(period_id=str(period['id']), period_start=period['period_start'].isoformat(), period_end=period['period_end'].isoformat(),
                     subscription_id=intent['provider_subscription_id'], customer_id=intent['provider_customer_id'],
                     old_plan_id=old_plan, target={k: str(v) for k, v in target.items()},
                     provider_timezone=provider_timezone, environment=_environment(client), transition=kind, start_date=start)
    return _store(org, intent['subscription_id'], operation_key, 'change', authority, preview)


def _validate_preview(value, target, deferred):
    try:
        if (value['new_plan']['currency'] != 'CLP' or value['old_plan']['currency'] != 'CLP'
                or _money(value['new_plan']['amount']) != Decimal(target['amount'])
                or value['new_plan']['interval'] != {'monthly': 3, 'annual': 4}[target['billing_cycle']]
                or value['new_plan']['interval_count'] != 1
                or (deferred and _money(value['balance']['amount']) != 0)):
            raise FlowError('flow_proration_requires_reconciliation')
        _money(value['balance']['amount'])
    except (KeyError, TypeError):
        raise FlowError('flow_invalid_proration') from None


def prepare_cancel(org, *, operation_key, client, provider_timezone, administrative_authorization=None):
    intent, period, plan_id = _current(org, client)
    _remote(intent, period, client, provider_timezone, plan_id)
    authority = dict(period_id=str(period['id']), period_start=period['period_start'].isoformat(), period_end=period['period_end'].isoformat(),
                     subscription_id=intent['provider_subscription_id'], customer_id=intent['provider_customer_id'],
                     environment=_environment(client), provider_timezone=provider_timezone, old_plan_id=plan_id,
                     at_period_end=administrative_authorization is None,
                     administrative_authorization=administrative_authorization)
    return _store(org, intent['subscription_id'], operation_key, 'cancel', authority)


def dispatch(org, operation_id, client):
    if connection.in_atomic_block:
        raise RuntimeError('Lifecycle dispatch requires outermost transaction boundary')
    operation = _read(org, operation_id)
    if operation['state'] == 'confirmed':
        return operation['result']
    if operation['state'] != 'prepared':
        raise FlowError('flow_operation_reconciliation_required', uncertain=True)
    authority = operation['authority']
    if authority['environment'] != _environment(client) or operation['kind'] not in ('change', 'cancel'):
        raise FlowError('flow_operation_binding_mismatch')
    if provider_time(authority['period_end'], authority['provider_timezone']) <= timezone.now():
        raise FlowError('flow_operation_period_changed')
    remote = client.subscription(authority['subscription_id'])
    if (remote.get('subscriptionId') != authority['subscription_id']
            or remote.get('planId') != authority['old_plan_id'] or remote.get('status') != 1
            or remote.get('customerId') != authority['customer_id']
            or changes_period(remote, authority) is False):
        raise FlowError('flow_operation_authority_changed')
    if operation['kind'] == 'change':
        preview = client.change_plan_preview(authority['subscription_id'], authority['target']['provider_plan_id'],
                                             start_date=authority['start_date'])
        _validate_preview(preview, authority['target'], authority['transition'] != 'upgrade')
        if json.loads(lifecycle.dump(preview)) != operation['preview']:
            raise FlowError('flow_preview_changed')
    with wallet.financial_transaction(org):
        wallet.locked_org(org)
        if not rows("UPDATE public.flow_lifecycle_operations SET state='dispatching' "
                    "WHERE org_id=%s AND id=%s AND state='prepared' RETURNING id", [org, operation_id]):
            raise FlowError('flow_operation_reconciliation_required', uncertain=True)
    try:
        if operation['kind'] == 'change':
            result = client.change_plan(authority['subscription_id'], authority['target']['provider_plan_id'],
                                        start_date=authority['start_date'])
        else:
            result = client.cancel_subscription(authority['subscription_id'], at_period_end=authority['at_period_end'])
        result = _remember(org, operation_id, result)
        return accept(org, operation_id, client, result)
    except FlowError:
        with wallet.financial_transaction(org):
            rows("UPDATE public.flow_lifecycle_operations SET state='uncertain' WHERE org_id=%s AND id=%s "
                 "AND state='dispatching' RETURNING id", [org, operation_id])
        raise


def accept(org, operation_id, client, result):
    """Validate mutation evidence and signed GET before applying entitlement changes."""
    operation = _read(org, operation_id)
    authority = operation['authority']
    if authority['environment'] != _environment(client):
        raise FlowError('flow_operation_binding_mismatch')
    remote = client.subscription(authority['subscription_id'])
    if remote.get('subscriptionId') != authority['subscription_id'] or remote.get('customerId') != authority['customer_id']:
        raise FlowError('flow_operation_binding_mismatch', uncertain=True)
    now = provider_time(result['_observed_at'], authority['provider_timezone'])
    if (provider_time(remote.get('period_start'), authority['provider_timezone']) !=
            provider_time(authority['period_start'], authority['provider_timezone'])
            or provider_time(remote.get('period_end'), authority['provider_timezone']) !=
            provider_time(authority['period_end'], authority['provider_timezone'])):
        raise FlowError('flow_operation_period_changed', uncertain=True)
    if operation['kind'] == 'change':
        target = authority['target']
        if (result.get('new_plan_id') != target['provider_plan_id'] or result.get('old_plan_id') != authority['old_plan_id']
                or result.get('new_currency') != 'CLP' or _money(result.get('new_amount')) != Decimal(target['amount'])
                or _money(result.get('balance')) != _money(operation['preview']['balance']['amount'])):
            raise FlowError('flow_change_evidence_mismatch', uncertain=True)
        kind = authority['transition']
        if kind == 'upgrade':
            if remote.get('planId') != target['provider_plan_id'] or remote.get('status') != 1:
                raise FlowError('flow_change_not_effective', uncertain=True)
            effective = now
        else:
            effective = provider_time(authority['period_end'], authority['provider_timezone'])
            if result.get('start_date_of_new_plan') != authority['start_date'] or _money(result.get('balance')) != 0:
                raise FlowError('flow_deferred_change_mismatch', uncertain=True)
        plan_tier, cycle = target['plan_tier'], target['billing_cycle']
    else:
        kind, plan_tier = 'cancel', 'STARTER'
        if authority['at_period_end']:
            if remote.get('cancel_at_period_end') != 1:
                raise FlowError('flow_cancellation_not_confirmed', uncertain=True)
            effective = provider_time(authority['period_end'], authority['provider_timezone'])
        else:
            if remote.get('status') != 4:
                raise FlowError('flow_cancellation_not_confirmed', uncertain=True)
            effective = now
        with wallet.financial_transaction(org):
            cycle = one('SELECT billing_cycle FROM public.billing_periods WHERE org_id=%s AND id=%s',
                        [org, authority['period_id']])['billing_cycle']
    evidence = {'provider_result': result, 'policy': lifecycle.POLICY,
                'administrative_authorization': authority.get('administrative_authorization')}
    with wallet.financial_transaction(org):
        wallet.locked_org(org)
        current = one('SELECT * FROM public.flow_lifecycle_operations WHERE org_id=%s AND id=%s FOR UPDATE', [org, operation_id])
        if current['state'] == 'confirmed':
            return current['result']
        if current['state'] not in ('dispatching', 'uncertain'):
            raise FlowError('flow_operation_not_dispatched')
        from uuid import UUID
        lifecycle.record_change(org, period_id=UUID(authority['period_id']), operation_key='flow:' + str(operation_id),
                                kind=kind, effective_at=effective, plan_tier=plan_tier, billing_cycle=cycle, evidence=evidence)
        one("UPDATE public.flow_lifecycle_operations SET state='confirmed',result=%s::jsonb "
            'WHERE org_id=%s AND id=%s RETURNING id', [lifecycle.dump(result), org, operation_id])
    return result


_RESULT_KEYS = {'new_plan_id', 'old_plan_id', 'new_currency', 'old_currency', 'new_amount', 'old_amount',
                'balance', 'start_date_of_new_plan', 'cancel_at_period_end', 'cancel_at', 'status',
                'subscriptionId', 'customerId', 'planId', 'period_start', 'period_end'}


def _remember(org, operation_id, result):
    # Persist the response before the second GET. Recovery can then use the same exact
    # observed instant and proration, without another provider mutation or time drift.
    evidence = {key: value for key, value in result.items() if key in _RESULT_KEYS}
    evidence['_observed_at'] = timezone.now().isoformat()
    with wallet.financial_transaction(org):
        wallet.locked_org(org)
        current = one('SELECT * FROM public.flow_lifecycle_operations WHERE org_id=%s AND id=%s FOR UPDATE', [org, operation_id])
        if current['result'] is not None:
            return current['result']
        one('UPDATE public.flow_lifecycle_operations SET result=%s::jsonb WHERE org_id=%s AND id=%s RETURNING id',
            [lifecycle.dump(evidence), org, operation_id])
    return json.loads(lifecycle.dump(evidence))


def recover(org, operation_id, client):
    operation = _read(org, operation_id)
    if operation['state'] == 'confirmed':
        return operation['result']
    if operation['state'] not in ('dispatching', 'uncertain') or operation['result'] is None:
        # GET /subscription/get cannot reconstruct the original monetary proration.
        # A lost POST response needs provider/admin reconciliation; never another POST.
        raise FlowError('flow_operation_reconciliation_required', uncertain=True)
    return accept(org, operation_id, client, operation['result'])



def changes_period(remote, authority):
    return (provider_time(remote.get('period_start'), authority['provider_timezone']) ==
            provider_time(authority['period_start'], authority['provider_timezone']) and
            provider_time(remote.get('period_end'), authority['provider_timezone']) ==
            provider_time(authority['period_end'], authority['provider_timezone']))


def abandon(org, operation_id):
    with wallet.financial_transaction(org):
        wallet.locked_org(org)
        operation = one('SELECT * FROM public.flow_lifecycle_operations WHERE org_id=%s AND id=%s', [org,operation_id])
        if operation['kind'] not in ('change','cancel') or operation['state'] not in ('prepared','abandoned'):
            raise FlowError('flow_operation_already_dispatched')
        one("UPDATE public.flow_lifecycle_operations SET state='abandoned' WHERE org_id=%s AND id=%s RETURNING id", [org,operation_id])
