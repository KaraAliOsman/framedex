"""OWNER commerce orchestration. Browser inputs are selections, never money authority."""

from decimal import Decimal
import hashlib
from uuid import UUID
from zoneinfo import ZoneInfo

from django.utils import timezone

from billing import changes, customers, lifecycle, native_subscriptions as native, offers, orders, settlement, wallet
from billing.flow import FlowError
from billing.repository import one, rows


def _environment(client):
    return settlement._environment(client)


def checkout(org, user_id, *, operation_key, offer_id, customer_name, customer_email, client,
             callback_origin, frontend_origin, provider_timezone):
    environment = _environment(client)
    with wallet.financial_transaction(org):
        wallet.locked_org(org)
        existing = rows('SELECT * FROM public.billing_checkouts WHERE org_id=%s AND operation_key=%s', [org,operation_key])
        offer = offers.get(org,offer_id,environment,active=not existing)
        if existing:
            purchase = existing[0]
            if purchase['offer_id'] != offer_id:
                raise FlowError('billing_checkout_replay_conflict')
        else:
            purchase = one('INSERT INTO public.billing_checkouts(org_id,user_id,operation_key,offer_id,start_date) '
                           'VALUES(%s,%s,%s,%s,%s) RETURNING *', [org,user_id,operation_key,offer_id,
                            timezone.now().astimezone(ZoneInfo(provider_timezone)).date()])
    key = 'checkout:' + str(purchase['id'])
    if offer['kind'] == 'pack':
        order = orders.prepare(org, operation_key=key, environment=environment, net_usd=offer['net_usd'],
                               fx_rate=offer['fx_rate'],fx_source=offer['fx_source'],fx_observed_on=offer['fx_observed_on'],
                               fx_snapshot_id=offer['fx_snapshot_id'],commerce_order=str(purchase['id']),
                               grants=(orders.Grant(offer['credits'],purchase['created_at'],None,lifecycle.POLICY),))
        if order['state'] == 'prepared':
            redirect = settlement.dispatch_payment(order['id'],client,email=customer_email,subject=offer['product_code'],
                                                  confirmation_url=callback_origin+'/api/v1/billing/flow/confirm/'+str(order['id'])+'/',
                                                  return_url=frontend_origin+'/settings/billing')
            return dict(id=purchase['id'],operation_key=operation_key,state='redirect',redirect_url=redirect)
        state = settlement.recover(order['id'],client)
        return dict(id=purchase['id'],operation_key=operation_key,state=state,redirect_url=None)
    with wallet.financial_transaction(org):
        known = rows('SELECT * FROM public.flow_customer_operations WHERE org_id=%s AND provider_environment=%s',
                     [org,environment])
    customer = known[0] if known else customers.prepare(org,environment=environment,name=customer_name,email=customer_email)
    if customer['state'] in ('dispatching','uncertain'):
        customers.recover(org,customer['id'],client)
    else:
        customers.dispatch(org,customer['id'],client)
    customer = customers._read(org,customer['id'],client)
    if customer['registration_state'] in ('none','failed'):
        redirect = customers.register(org,customer['id'],client,
                    return_url=callback_origin+'/api/v1/billing/flow/registration-return/'+str(customer['id'])+'/')
        return dict(id=purchase['id'],operation_key=operation_key,state='redirect',redirect_url=redirect)
    if customer['registration_state'] != 'registered':
        return dict(id=purchase['id'],operation_key=operation_key,state='registration_pending',redirect_url=None)
    with wallet.financial_transaction(org):
        wallet.locked_org(org)
        prior_intents = rows('SELECT * FROM public.flow_subscription_intents WHERE org_id=%s AND operation_key=%s', [org,key])
        if prior_intents:
            intent = prior_intents[0]
        else:
            # Card registration can finish days after selection. Freeze the start
            # only when preparing the native subscription, under the org lock so
            # concurrent resumptions (including across midnight) reuse one intent.
            intent = native.prepare(org,operation_key=key,customer_id=customer['customer_id'],
                            provider_plan_id=offer['provider_plan_id'],environment=environment,
                            plan_tier=offer['plan_tier'],billing_cycle=offer['billing_cycle'],net_usd=offer['net_usd'],
                            fx_rate=offer['fx_rate'],fx_source=offer['fx_source'],fx_observed_on=offer['fx_observed_on'],
                            fx_snapshot_id=offer['fx_snapshot_id'],
                            start_date=timezone.now().astimezone(ZoneInfo(provider_timezone)).date(),trial_days=0,
                            policy_reference=lifecycle.POLICY)
    if intent['state'] in ('dispatching','uncertain'):
        native.recover(org,intent['id'],client)
    else:
        native.dispatch(org,intent['id'],client)
    sync(org,client,provider_timezone=provider_timezone)
    with wallet.financial_transaction(org):
        status = one('SELECT status FROM public.subscriptions WHERE org_id=%s AND id=%s', [org,intent['subscription_id']])['status']
    return dict(id=purchase['id'],operation_key=operation_key,state='succeeded' if status=='active' else 'pending',redirect_url=None)


def _invoice_offer(org,intent,start,client):
    with wallet.financial_transaction(org):
        transitions = rows("SELECT o.authority FROM public.flow_lifecycle_operations o JOIN public.billing_lifecycle_events e "
                           "ON e.org_id=o.org_id AND e.operation_key='flow:' || o.id::text WHERE o.org_id=%s "
                          "AND o.subscription_id=%s AND o.kind='change' AND o.state='confirmed' AND e.effective_at<=%s "
                           'ORDER BY e.effective_at DESC,e.created_at DESC LIMIT 1', [org,intent['subscription_id'],start])
        if transitions:
            return offers.get(org,UUID(transitions[0]['authority']['target']['id']),_environment(client),active=False)
        records = rows('SELECT o.* FROM public.billing_offers o JOIN public.billing_checkouts c '
                       'ON c.org_id=o.org_id AND c.offer_id=o.id WHERE c.org_id=%s AND %s=\'checkout:\' || c.id::text',
                       [org,intent['operation_key']])
        if len(records)!=1:
            raise FlowError('billing_subscription_offer_required')
        return records[0]


def sync(org,client,*,provider_timezone,only_payment=None):
    """GET-only renewal recovery. An invoice's own period binds its frozen commercial terms."""
    with wallet.financial_transaction(org):
        intents = rows("SELECT * FROM public.flow_subscription_intents WHERE org_id=%s AND state='created'",[org])
    matched=False
    for intent in intents:
        if intent['provider_environment'] != _environment(client):
            continue
        remote=client.subscription(intent['provider_subscription_id'])
        if (remote.get('subscriptionId')!=intent['provider_subscription_id'] or remote.get('customerId')!=intent['provider_customer_id']
                or not isinstance(remote.get('invoices'),list)):
            raise FlowError('flow_subscription_binding_mismatch')
        for summary in remote['invoices']:
            if not isinstance(summary,dict) or type(summary.get('id')) not in (int,str):
                raise FlowError('flow_invalid_invoice')
            invoice=client.invoice(str(summary['id']))
            if invoice.get('payment') is None:
                continue
            payment=settlement._payment(invoice['payment'])
            if only_payment is not None and payment['flowOrder']!=only_payment:
                continue
            matched=True
            if (str(invoice.get('id'))!=str(summary['id']) or invoice.get('subscriptionId')!=intent['provider_subscription_id']
                    or invoice.get('customerId')!=intent['provider_customer_id'] or invoice.get('currency')!='CLP'):
                raise FlowError('flow_invoice_binding_mismatch')
            start=changes.provider_time(invoice.get('period_start'),provider_timezone)
            end=changes.provider_time(invoice.get('period_end'),provider_timezone)
            if end<=start:
                raise FlowError('flow_invalid_period')
            offer=_invoice_offer(org,intent,start,client)
            if changes._money(invoice.get('amount'))!=offer['amount'] or Decimal(payment['amount'])!=offer['amount']:
                # Upgrade proration is a distinct Flow operation; never misclassify its
                # adjustment invoice as another full subscription allowance.
                evidence = {key: invoice.get(key) for key in
                            ('id','subscriptionId','customerId','currency','amount','period_start','period_end')}
                evidence['payment'] = payment
                encoded = lifecycle.dump(evidence)
                with wallet.financial_transaction(org):
                    wallet.locked_org(org)
                    rows('INSERT INTO public.billing_invoice_observations(org_id,subscription_id,provider_environment,'
                         'provider_invoice_id,evidence,evidence_hash) VALUES(%s,%s,%s,%s,%s::jsonb,%s) '
                         'ON CONFLICT(org_id,provider_environment,provider_invoice_id,evidence_hash) DO NOTHING RETURNING id',
                         [org,intent['subscription_id'],_environment(client),str(invoice['id']),encoded,
                          hashlib.sha256(encoded.encode()).hexdigest()])
                continue
            order=orders.prepare(org,operation_key='flow-invoice:'+str(invoice['id']),environment=_environment(client),
                                  net_usd=offer['net_usd'],fx_rate=offer['fx_rate'],fx_source=offer['fx_source'],
                                  fx_observed_on=offer['fx_observed_on'],fx_snapshot_id=offer['fx_snapshot_id'],grants=(),
                                  commerce_order=payment['commerceOrder'],subscription_id=intent['subscription_id'],
                                  provider_invoice_id=str(invoice['id']))
            current=settlement._payment(client.payment_by_order(payment['commerceOrder']))
            if current['flowOrder']!=payment['flowOrder']:
                raise FlowError('flow_invoice_binding_mismatch')
            with wallet.financial_transaction(org):
                wallet.locked_org(org)
                state=settlement._settle(org,order['id'],current,_environment(client))
                if state=='succeeded':
                    lifecycle.record_paid_period(org,order_id=order['id'],start=start,end=end,plan_tier=offer['plan_tier'],
                        billing_cycle=offer['billing_cycle'],evidence={'invoice_id':str(invoice['id']),
                        'subscription_id':intent['provider_subscription_id'],'timezone':provider_timezone,
                        'period_start':invoice['period_start'],'period_end':invoice['period_end'],'offer_id':str(offer['id'])})
    if only_payment is not None and not matched:
        raise FlowError('flow_subscription_payment_not_bound')
    return wallet.billing_summary(org)


def callback(offer_id,token,client,provider_timezone):
    # Privileged lookup of an opaque merchant callback route, then signed status.
    offer=one('SELECT org_id,provider_environment FROM public.billing_offers WHERE id=%s',[offer_id])
    if offer['provider_environment']!=_environment(client):
        raise FlowError('flow_callback_environment_mismatch')
    payment=settlement._payment(client.payment_status(token))
    return sync(offer['org_id'],client,provider_timezone=provider_timezone,only_payment=payment['flowOrder'])


def checkouts(org):
    with wallet.financial_transaction(org):
        return rows('SELECT c.id,c.operation_key,c.offer_id,c.created_at,o.product_code FROM public.billing_checkouts c '
                    'JOIN public.billing_offers o ON o.org_id=c.org_id AND o.id=c.offer_id '
                    'WHERE c.org_id=%s ORDER BY c.created_at DESC LIMIT 20',[org])
