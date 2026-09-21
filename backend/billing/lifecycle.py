"""OWNER-frozen credit/entitlement policy. All mutations hold the organization's lock.

Provider orchestration must bind evidence before recording a paid period or change.
The lazy reducer is also the worker contract: missing a scheduled wakeup cannot retain
expired AI rights or destroy purchased credits. Manual product access is unaffected.
"""

from calendar import monthrange
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json

from django.utils import timezone

from billing import wallet
from billing.flow import FlowError
from dekopen_engine.billing import upgrade_credits, PLAN_ALLOWANCES
from billing.repository import one, rows

ALLOWANCES = PLAN_ALLOWANCES
POLICY = 'PD-11-02/03 OWNER 2026-09-21'


def dump(value):
    return json.dumps(value, default=str, sort_keys=True)


def _months(anchor, count):
    index = anchor.year * 12 + anchor.month - 1 + count
    year, month = divmod(index, 12)
    return anchor.replace(year=year, month=month + 1, day=min(anchor.day, monthrange(year, month + 1)[1]))


def service_windows(period):
    """Calendar-month anniversaries anchored once; clamp month-end without drift."""
    zone = ZoneInfo(period['provider_evidence'].get('timezone', 'UTC'))
    start, end = period['period_start'].astimezone(zone), period['period_end'].astimezone(zone)
    count = 1 if period['billing_cycle'] == 'monthly' else 12
    for index in range(count):
        left = _months(start, index) if index else start
        if left >= end:
            break
        right = end if index == count - 1 else min(_months(start, index + 1), end)
        yield left, right


def _micros(delta):
    return (delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds


def _grant(org, credits, *, key, origin, expires, reference, action):
    if credits <= 0 or rows('SELECT id FROM public.credit_ledger WHERE org_id=%s AND operation_key=%s', [org, key]):
        return
    entry = wallet.append(org, credits, action, key, reference, expires)
    one('INSERT INTO public.credit_lots(org_id,grant_id,remaining,expires_at,origin) '
        'VALUES(%s,%s,%s,%s,%s) RETURNING id', [org, entry['id'], credits, expires, origin])


def _expire_origin(org, origin, key):
    for lot in rows('SELECT * FROM public.credit_lots WHERE org_id=%s AND origin=%s AND remaining>0 FOR UPDATE',
                    [org, origin]):
        wallet.expire_lot(org, lot, key=key + ':' + str(lot['id']))


def record_paid_period(org, *, order_id, start, end, plan_tier, billing_cycle, evidence):
    """Trusted normalized provider boundaries plus a verified paid native invoice.

    No frontend date/plan is accepted here. The provider adapter owns normalization.
    Generic payment grants must be empty: this reducer owns recurring allowances.
    """
    if (not isinstance(start, datetime) or not isinstance(end, datetime) or timezone.is_naive(start)
            or timezone.is_naive(end) or end <= start or plan_tier not in ALLOWANCES
            or billing_cycle not in ('monthly', 'annual') or not evidence):
        raise ValueError('Authoritative period, plan and provider evidence required')
    with wallet.financial_transaction(org):
        wallet.locked_org(org)
        order = one('SELECT * FROM public.billing_orders WHERE org_id=%s AND id=%s', [org, order_id])
        if order['state'] != 'succeeded' or order['subscription_id'] is None:
            raise FlowError('paid_native_invoice_required')
        if rows('SELECT id FROM public.billing_credit_grants WHERE org_id=%s AND order_id=%s', [org, order_id]):
            raise FlowError('duplicate_allowance_authority')
        previous = rows('SELECT * FROM public.billing_periods WHERE org_id=%s AND order_id=%s', [org, order_id])
        expected = dict(period_start=start, period_end=end, plan_tier=plan_tier, billing_cycle=billing_cycle,
                        allowance=ALLOWANCES[plan_tier], provider_evidence=json.loads(dump(evidence)))
        if previous:
            if any(previous[0][key] != value for key, value in expected.items()):
                raise FlowError('billing_period_replay_conflict')
            return previous[0]
        if rows('SELECT id FROM public.billing_periods WHERE org_id=%s '
                'AND period_start<%s AND period_end>%s', [org, end, start]):
            raise FlowError('billing_period_overlap')
        period = one('INSERT INTO public.billing_periods(org_id,subscription_id,order_id,period_start,period_end,'
                     'plan_tier,billing_cycle,allowance,provider_evidence) '
                     'VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb) RETURNING *',
                     [org, order['subscription_id'], order_id, start, end, plan_tier, billing_cycle,
                      ALLOWANCES[plan_tier], dump(evidence)])
        wallet.reconcile(org)
        return period


def record_change(org, *, period_id, operation_key, kind, effective_at, plan_tier, billing_cycle, evidence):
    """Record a provider-confirmed transition; scheduling alone grants no new rights."""
    if (kind not in ('upgrade', 'downgrade', 'frequency', 'cancel', 'refund')
            or plan_tier not in ALLOWANCES or billing_cycle not in ('monthly', 'annual')
            or timezone.is_naive(effective_at) or not operation_key or not evidence):
        raise ValueError('Explicit confirmed transition required')
    with wallet.financial_transaction(org):
        wallet.locked_org(org)
        period = one('SELECT * FROM public.billing_periods WHERE org_id=%s AND id=%s', [org, period_id])
        expected = dict(period_id=period_id, kind=kind, effective_at=effective_at, plan_tier=plan_tier,
                        billing_cycle=billing_cycle, allowance=ALLOWANCES[plan_tier], evidence=json.loads(dump(evidence)))
        previous = rows('SELECT * FROM public.billing_lifecycle_events WHERE org_id=%s AND operation_key=%s',
                        [org, operation_key])
        if previous:
            if any(previous[0][key] != value for key, value in expected.items()):
                raise FlowError('billing_change_replay_conflict')
            wallet.reconcile(org)
            return previous[0]
        if kind in ('downgrade', 'frequency') and effective_at != period['period_end']:
            raise FlowError('billing_change_requires_renewal')
        if kind == 'cancel' and effective_at != period['period_end'] and not evidence.get('administrative_authorization'):
            raise FlowError('immediate_cancellation_requires_administrator')
        if kind == 'refund' and not evidence.get('administrative_authorization'):
            raise FlowError('refund_requires_administrator')
        if kind == 'upgrade':
            current = plan_at(org, period, effective_at)
            if (not period['period_start'] <= effective_at < period['period_end']
                    or billing_cycle != period['billing_cycle'] or ALLOWANCES[plan_tier] <= current['allowance']):
                raise FlowError('invalid_upgrade')
        event = one('INSERT INTO public.billing_lifecycle_events(org_id,subscription_id,operation_key,period_id,'
                    'kind,effective_at,plan_tier,billing_cycle,allowance,evidence) '
                    'VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb) RETURNING *',
                    [org, period['subscription_id'], operation_key, period_id, kind, effective_at,
                     plan_tier, billing_cycle, ALLOWANCES[plan_tier], dump(evidence)])
        wallet.reconcile(org)
        return event


def plan_at(org, period, instant):
    upgrades = rows("SELECT * FROM public.billing_lifecycle_events WHERE org_id=%s AND period_id=%s "
                    "AND kind='upgrade' AND effective_at<=%s ORDER BY effective_at DESC,created_at DESC LIMIT 1",
                    [org, period['id'], instant])
    return upgrades[0] if upgrades else period


def reconcile(org):
    now = timezone.now()
    periods = rows('SELECT * FROM public.billing_periods WHERE org_id=%s AND period_start<=%s '
                   'ORDER BY period_start', [org, now])
    if not periods:
        return
    # Even a late first observation of payment terminates trial; never stack balances.
    _expire_origin(org, 'trial', 'paid-trial-end')
    current = None
    for period in periods:
        stops = rows("SELECT * FROM public.billing_lifecycle_events WHERE org_id=%s AND period_id=%s "
                     "AND kind IN ('cancel','refund') ORDER BY effective_at LIMIT 1", [org, period['id']])
        stop = min(period['period_end'], stops[0]['effective_at']) if stops else period['period_end']
        for left, right in service_windows(period):
            if left > now or left >= stop:
                continue
            plan = plan_at(org, period, left - timedelta(microseconds=1))
            _grant(org, plan['allowance'], key='monthly:' + str(period['id']) + ':' + left.isoformat(),
                   origin='monthly', expires=min(right, stop), reference=period['id'], action='MONTHLY_GRANT')
        upgrades = rows("SELECT * FROM public.billing_lifecycle_events WHERE org_id=%s AND period_id=%s "
                        "AND kind='upgrade' AND effective_at<=%s ORDER BY effective_at,created_at", [org, period['id'], now])
        previous_allowance = period['allowance']
        for event in upgrades:
            instant = event['effective_at']
            delta = upgrade_credits(previous_allowance, event['allowance'],
                                    remaining=_micros(period['period_end'] - instant),
                                    total=_micros(period['period_end'] - period['period_start']))
            window = next(((left, right) for left, right in service_windows(period) if left <= instant < right), None)
            if window and instant < stop:
                _grant(org, delta, key='upgrade:' + str(event['id']), origin='monthly',
                       expires=min(window[1], stop), reference=event['id'], action='UPGRADE_GRANT')
            previous_allowance = event['allowance']
        if stops and stop <= now:
            affected = rows('SELECT l.* FROM public.credit_lots l JOIN public.credit_ledger e '
                            'ON e.org_id=l.org_id AND e.id=l.grant_id WHERE l.org_id=%s AND l.remaining>0 '
                            "AND l.origin='monthly' AND (e.reference_id=%s OR e.reference_id IN "
                            '(SELECT id FROM public.billing_lifecycle_events WHERE org_id=%s AND period_id=%s)) FOR UPDATE OF l',
                            [org, period['id'], org, period['id']])
            for lot in affected:
                wallet.expire_lot(org, lot, key='period-stop:' + str(lot['id']))
        if period['period_start'] <= now < stop:
            current = (period, plan_at(org, period, now))
    if current:
        period, plan = current
        one('UPDATE public.tenancy_organizations SET subscription_tier=%s,subscription_active=true,'
            'billing_cycle=%s,updated_at=now() WHERE id=%s RETURNING id',
            [plan['plan_tier'], period['billing_cycle'], org])
        charge = one('SELECT amount FROM public.billing_orders WHERE org_id=%s AND id=%s',
                     [org, period['order_id']])['amount']
        if 'evidence' in plan:
            charge = plan['evidence'].get('provider_result', {}).get('new_amount', charge)
        one("UPDATE public.subscriptions SET status='active',plan_tier=%s,billing_cycle=%s,amount=%s,"
            'current_period_start=%s,current_period_end=%s,updated_at=now() WHERE org_id=%s AND id=%s RETURNING id',
            [plan['plan_tier'], period['billing_cycle'], charge, period['period_start'], period['period_end'], org, period['subscription_id']])
    else:
        # No verified paid period remains. Packs remain owned, but Starter cannot use AI.
        _expire_origin(org, 'monthly', 'ended-monthly')
        one("UPDATE public.tenancy_organizations SET subscription_tier='STARTER',subscription_active=true,"
            'updated_at=now() WHERE id=%s RETURNING id', [org])
        ended = rows("SELECT id FROM public.billing_lifecycle_events WHERE org_id=%s AND kind IN ('cancel','refund') "
                     'AND effective_at<=%s ORDER BY effective_at DESC LIMIT 1', [org, now])
        one('UPDATE public.subscriptions SET status=%s,updated_at=now() WHERE org_id=%s RETURNING id',
            ['cancelled' if ended else 'past_due', org])


def plan_at_in_transaction(org, period, instant):
    with wallet.financial_transaction(org):
        return plan_at(org, period, instant)
