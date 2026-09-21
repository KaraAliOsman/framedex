"""Trusted merchant provisioning and read-only offers. Not a tenant price-writing API."""

from datetime import date
from zoneinfo import ZoneInfo
from urllib.parse import urlsplit

from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone

from billing import wallet
from billing.flow import FlowClient, FlowError
from billing.repository import one, rows
from dekopen_engine.billing import platform_charge_clp, product_terms


def runtime():
    callback = settings.BILLING_CALLBACK_ORIGIN.rstrip('/')
    frontend = settings.BILLING_FRONTEND_ORIGIN.rstrip('/')
    zone = settings.FLOW_MERCHANT_TIMEZONE
    for origin in (callback, frontend):
        parsed = urlsplit(origin)
        if parsed.scheme != 'https' or not parsed.netloc or parsed.path or parsed.query or parsed.fragment or parsed.username:
            raise FlowError('billing_callback_configuration_required')
    if not zone:
        raise FlowError('flow_merchant_timezone_required')
    ZoneInfo(zone)
    return FlowClient(api_url=settings.FLOW_API_URL, api_key=settings.FLOW_API_KEY,
                      secret_key=settings.FLOW_SECRET_KEY), callback, frontend, zone


def provision(org, *, product_code, billing_cycle, environment, provider_plan_id, fx_rate, fx_source,
              fx_observed_on, fx_snapshot_id, reason):
    """CLI operator supplies explicit observed FX; before-insert price audit is mandatory."""
    if (environment not in ('sandbox','production') or not reason.strip() or not fx_source.strip()
            or type(fx_observed_on) is not date or fx_observed_on > timezone.now().date()):
        raise ValueError('Explicit audited merchant configuration required')
    price, credits = product_terms(product_code, billing_cycle)
    kind = 'subscription' if billing_cycle else 'pack'
    if (kind == 'subscription') != bool(provider_plan_id):
        raise ValueError('Native subscription requires a provisioned Flow plan')
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.execute("SELECT set_config('app.pricing_reason',%s,true)", [reason])
        # This operation intentionally uses the trusted operator DB session. The
        # billing_backend role and authenticated customers cannot provision prices.
        return one('INSERT INTO public.billing_offers(org_id,product_code,kind,plan_tier,billing_cycle,credits,'
                   'provider_environment,provider_plan_id,net_usd,amount,fx_rate,fx_source,fx_observed_on,fx_snapshot_id) '
                   'VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *',
                   [org,product_code,kind,product_code if billing_cycle else None,billing_cycle,credits,environment,
                    provider_plan_id,price,platform_charge_clp(price,fx_rate),fx_rate,fx_source,fx_observed_on,fx_snapshot_id])


def get(org, offer_id, environment, *, active=True):
    with wallet.financial_transaction(org):
        offer = one('SELECT * FROM public.billing_offers WHERE org_id=%s AND id=%s', [org,offer_id])
        if offer['provider_environment'] != environment or (active and not offer['active']):
            raise FlowError('billing_offer_unavailable')
        price, credits = product_terms(offer['product_code'], offer['billing_cycle'])
        if (offer['credits'] != credits or offer['net_usd'] != price
                or offer['amount'] != platform_charge_clp(price,offer['fx_rate'])):
            raise FlowError('billing_offer_authority_mismatch')
        return offer


def public(org):
    with wallet.financial_transaction(org):
        environment = 'sandbox' if settings.FLOW_API_URL == 'https://sandbox.flow.cl/api' else 'production'
        values = rows('SELECT id,product_code,kind,plan_tier,billing_cycle,credits,amount,fx_source,fx_observed_on '
                      'FROM public.billing_offers WHERE org_id=%s AND provider_environment=%s AND active '
                      'ORDER BY kind,amount,id', [org,environment])
    for value in values:
        value['amount'] = format(value['amount'], '.0f')
    return values
