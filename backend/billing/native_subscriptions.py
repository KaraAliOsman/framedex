"""Durable native subscription creation for trusted, explicitly approved start terms.

Provisioning owns the plan and customer. No public endpoint accepts these identities
or commercial terms. This boundary creates/reconciles Flow subscriptions only; paid
entitlements and allowance schedules require separately verified invoice settlement.
"""

from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import connection
from django.utils import timezone

from billing import wallet
from billing.flow import FlowError
from billing.settlement import _environment
from dekopen_engine.billing import platform_charge_clp
from pricing.repository import one, rows


def prepare(org, *, operation_key, customer_id, provider_plan_id, environment, plan_tier,
            billing_cycle, net_usd, fx_rate, fx_source, fx_observed_on, fx_snapshot_id,
            start_date, trial_days, policy_reference):
    """Explicit server-authoritative inputs, replay-safe before any remote mutation."""
    if (not operation_key or not provider_plan_id or not policy_reference.strip() or not fx_source.strip()
            or environment not in ('sandbox', 'production') or billing_cycle not in ('monthly', 'annual')
            or plan_tier not in ('STARTER', 'PRO', 'BUSINESS', 'BUSINESS_2X')
            or type(start_date) is not date or type(fx_observed_on) is not date
            or fx_observed_on > timezone.now().date() or type(trial_days) is not int or not 0 <= trial_days <= 7
            or not isinstance(net_usd, Decimal) or not isinstance(fx_rate, Decimal)
            or not net_usd.is_finite() or net_usd != net_usd.quantize(Decimal('.01'))):
        raise ValueError('Explicit valid approved subscription authority required')
    amount = platform_charge_clp(net_usd, fx_rate)
    expected = dict(provider_environment=environment, provider_plan_id=provider_plan_id,
                    customer_id=customer_id, net_usd=net_usd, amount=amount, fx_rate=fx_rate,
                    fx_source=fx_source, fx_observed_on=fx_observed_on, fx_snapshot_id=fx_snapshot_id,
                    start_date=start_date, trial_days=trial_days, policy_reference=policy_reference)
    with wallet.financial_transaction(org):
        wallet.locked_org(org)
        existing = rows('SELECT * FROM public.flow_subscription_intents WHERE org_id=%s AND operation_key=%s',
                        [org, operation_key])
        if existing:
            intent = existing[0]
            local = one('SELECT * FROM public.subscriptions WHERE org_id=%s AND id=%s', [org, intent['subscription_id']])
            if (any(intent[key] != value for key, value in expected.items())
                    or local['plan_tier'] != plan_tier or local['billing_cycle'] != billing_cycle):
                raise FlowError('flow_subscription_replay_conflict')
            return intent
        customers = rows("SELECT * FROM public.payment_customers WHERE org_id=%s AND id=%s AND provider='flow'",
                         [org, customer_id])
        if len(customers) != 1 or rows('SELECT id FROM public.subscriptions WHERE org_id=%s', [org]):
            raise FlowError('flow_subscription_setup_required')
        local = one('INSERT INTO public.subscriptions(org_id,provider,plan_tier,billing_cycle,status,currency,amount) '
                    "VALUES(%s,'flow',%s,%s,'pending','CLP',%s) RETURNING id", [org, plan_tier, billing_cycle, amount])
        return one('INSERT INTO public.flow_subscription_intents(org_id,operation_key,subscription_id,provider_customer_id,'
                   'provider_environment,provider_plan_id,customer_id,net_usd,amount,fx_rate,fx_source,fx_observed_on,'
                   'fx_snapshot_id,start_date,trial_days,policy_reference) '
                   'VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *',
                   [org, operation_key, local['id'], customers[0]['provider_customer_id'], *expected.values()])


def _read(org, intent_id, client):
    with wallet.financial_transaction(org):
        found = rows('SELECT i.*,s.billing_cycle FROM public.flow_subscription_intents i '
                     'JOIN public.subscriptions s ON(s.org_id=i.org_id AND s.id=i.subscription_id) '
                     'WHERE i.org_id=%s AND i.id=%s', [org, intent_id])
        if len(found) != 1 or found[0]['provider_environment'] != _environment(client):
            raise FlowError('flow_subscription_binding_mismatch')
        return found[0]


def _verify_plan_and_customer(intent, client):
    plan = client.plan(intent['provider_plan_id'])
    customer = client.customer(intent['provider_customer_id'])
    try:
        if (plan['planId'] != intent['provider_plan_id'] or plan['currency'] != 'CLP'
                or type(plan['amount']) not in (int, str, Decimal) or Decimal(plan['amount']) != intent['amount']
                or type(plan['interval']) is not int
                or plan['interval'] != {'monthly': 3, 'annual': 4}[intent['billing_cycle']]
                or type(plan['interval_count']) is not int or plan['interval_count'] != 1
                or customer['customerId'] != intent['provider_customer_id']
                or customer['externalId'] != str(intent['org_id'])):
            raise ValueError()
    except (KeyError, ValueError, TypeError, InvalidOperation):
        raise FlowError('flow_subscription_binding_mismatch') from None


def _subscriptions(intent, client):
    """Read complete bounded pagination; never infer absence from an incomplete page."""
    found = []
    for start in range(0, 10000, 100):
        page = client.customer_subscriptions(intent['provider_customer_id'], start=start)
        if (not isinstance(page.get('data'), list) or type(page.get('hasMore')) is not int
                or page['hasMore'] not in (0, 1)):
            raise FlowError('flow_invalid_subscription_list')
        for item in page['data']:
            if not isinstance(item, dict) or not isinstance(item.get('subscriptionId'), str):
                raise FlowError('flow_invalid_subscription_list')
            # Hydrate each result: list representations may omit commercial fields.
            value = client.subscription(item['subscriptionId'])
            if value.get('customerId') != intent['provider_customer_id']:
                raise FlowError('flow_subscription_binding_mismatch')
            if value.get('planId') == intent['provider_plan_id']:
                found.append(value)
        if page['hasMore'] == 0:
            return found
    raise FlowError('flow_subscription_reconciliation_limit')


def _accept(org, intent_id, client, value):
    intent = _read(org, intent_id, client)
    subscription_id = value.get('subscriptionId')
    if (not isinstance(subscription_id, str) or not subscription_id
            or value.get('customerId') != intent['provider_customer_id']
            or value.get('planId') != intent['provider_plan_id']
            or type(value.get('trial_period_days')) is not int or value['trial_period_days'] != intent['trial_days']
            or not isinstance(value.get('subscription_start'), str)
            or value['subscription_start'][:10] != intent['start_date'].isoformat()):
        raise FlowError('flow_subscription_binding_mismatch', uncertain=True)
    with wallet.financial_transaction(org):
        wallet.locked_org(org)
        current = one('SELECT * FROM public.flow_subscription_intents WHERE org_id=%s AND id=%s FOR UPDATE', [org, intent_id])
        if current['state'] not in ('dispatching', 'uncertain', 'created'):
            raise FlowError('flow_subscription_not_dispatched')
        if current['provider_subscription_id'] not in (None, subscription_id):
            raise FlowError('flow_subscription_binding_mismatch')
        one("UPDATE public.flow_subscription_intents SET state='created',provider_subscription_id=%s "
            'WHERE org_id=%s AND id=%s RETURNING id', [subscription_id, org, intent_id])
        one('UPDATE public.subscriptions SET provider_subscription_id=%s,updated_at=now() '
            'WHERE org_id=%s AND id=%s RETURNING id', [subscription_id, org, current['subscription_id']])
        # Keep local status pending: provider subscription creation is not a paid invoice.
        return subscription_id


def dispatch(org, intent_id, client):
    if connection.in_atomic_block:
        raise RuntimeError('Native subscription dispatch requires an outermost transaction boundary')
    intent = _read(org, intent_id, client)
    if intent['state'] == 'created':
        return intent['provider_subscription_id']
    if intent['state'] != 'prepared':
        raise FlowError('flow_subscription_reconciliation_required', uncertain=True)
    _verify_plan_and_customer(intent, client)
    if _subscriptions(intent, client):
        raise FlowError('flow_subscription_already_exists')
    with wallet.financial_transaction(org):
        wallet.locked_org(org)
        changed = rows("UPDATE public.flow_subscription_intents SET state='dispatching' "
                       "WHERE org_id=%s AND id=%s AND state='prepared' RETURNING id", [org, intent_id])
        if not changed:
            raise FlowError('flow_subscription_reconciliation_required', uncertain=True)
    try:
        value = client.create_subscription(customer_id=intent['provider_customer_id'], plan_id=intent['provider_plan_id'],
                                           start_date=intent['start_date'].isoformat(), trial_days=intent['trial_days'])
        return _accept(org, intent_id, client, value)
    except FlowError:
        with wallet.financial_transaction(org):
            rows("UPDATE public.flow_subscription_intents SET state='uncertain' "
                 "WHERE org_id=%s AND id=%s AND state='dispatching' RETURNING id", [org, intent_id])
        raise


def recover(org, intent_id, client):
    intent = _read(org, intent_id, client)
    if intent['state'] == 'created':
        return intent['provider_subscription_id']
    if intent['state'] not in ('dispatching', 'uncertain'):
        raise FlowError('flow_subscription_not_dispatched')
    _verify_plan_and_customer(intent, client)
    matches = _subscriptions(intent, client)
    if len(matches) != 1:
        # Zero is not proof that an in-flight POST was never applied. Never release
        # the dispatch claim or create again; operator reconciliation is required.
        raise FlowError('flow_subscription_reconciliation_required', uncertain=True)
    return _accept(org, intent_id, client, matches[0])


def reconcile_invoice(org, intent_id, invoice_id, client, *, grants):
    """Bind a native invoice to the frozen quote before payment settlement.

    Caller supplies an approved schedule (including an explicitly empty Starter
    schedule). No expiry, rollover, delinquency or entitlement policy is inferred.
    Flow invoice IDs are not fiscal receipt folios and are never shown as such.
    """
    from billing import orders, settlement
    intent = _read(org, intent_id, client)
    if intent['state'] != 'created':
        raise FlowError('flow_subscription_not_created')
    invoice = client.invoice(str(invoice_id))
    try:
        if (str(invoice['id']) != str(invoice_id)
                or invoice['subscriptionId'] != intent['provider_subscription_id']
                or invoice['customerId'] != intent['provider_customer_id']
                or invoice['currency'] != 'CLP' or type(invoice['amount']) not in (str, int, Decimal)
                or Decimal(invoice['amount']) != intent['amount']):
            raise ValueError()
        payment = settlement._payment(invoice['payment'])
        if Decimal(payment['amount']) != intent['amount']:
            raise ValueError()
    except (KeyError, TypeError, ValueError, InvalidOperation):
        raise FlowError('flow_invoice_binding_mismatch') from None
    order = orders.prepare(org, operation_key='flow-invoice:' + str(invoice_id),
                           environment=intent['provider_environment'], net_usd=intent['net_usd'],
                           fx_rate=intent['fx_rate'], fx_source=intent['fx_source'],
                           fx_observed_on=intent['fx_observed_on'], fx_snapshot_id=intent['fx_snapshot_id'],
                           grants=grants, commerce_order=payment['commerceOrder'],
                           subscription_id=intent['subscription_id'], provider_invoice_id=str(invoice_id))
    with wallet.financial_transaction(org):
        wallet.locked_org(org)
        current = one('SELECT * FROM public.billing_orders WHERE org_id=%s AND id=%s FOR UPDATE', [org, order['id']])
        if current['provider_payment_id'] not in (None, payment['flowOrder']):
            raise FlowError('flow_invoice_binding_mismatch')
        one('UPDATE public.billing_orders SET provider_payment_id=%s WHERE org_id=%s AND id=%s RETURNING id',
            [payment['flowOrder'], org, order['id']])
    # A second signed lookup confirms current payment status, rather than trusting a
    # browser return, callback fields or a possibly stale subscription invoice summary.
    return settlement.recover(order['id'], client)
