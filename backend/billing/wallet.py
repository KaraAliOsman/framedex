"""Atomic wallet primitives. AI consumers remain SHOT-13; only their contract lives here."""

from contextlib import contextmanager
from uuid import UUID

from django.db import connection, transaction
from django.utils import timezone

from authentication.errors import contract_error
from pricing.repository import one, rows


@contextmanager
def financial_transaction(org: UUID):
    # Call only with an organization resolved from verified membership or persisted
    # server-side provider state. The browser never chooses this capability.
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_setting('role'), current_setting('app.billing_org',true)")
            previous_role, previous_org = cursor.fetchone()
            cursor.execute("SET LOCAL ROLE billing_backend")
            cursor.execute("SELECT set_config('app.billing_org',%s,true)", [str(org)])
        yield
        # An exception rolls this savepoint back, including its SET LOCAL changes.
        with connection.cursor() as cursor:
            from psycopg import sql
            cursor.execute(sql.SQL('SET LOCAL ROLE {}').format(
                sql.SQL('NONE') if previous_role == 'none' else sql.Identifier(previous_role)))
            cursor.execute("SELECT set_config('app.billing_org',%s,true)", [previous_org or ''])


def locked_org(org):
    return one('SELECT * FROM public.tenancy_organizations WHERE id=%s FOR UPDATE', [org])


def append(org, amount, action, key, reference=None, expires=None):
    balance = locked_org(org)['credits_balance']
    return one('INSERT INTO public.credit_ledger '
               '(org_id,amount,balance_after,action_type,operation_key,reference_id,expires_at) '
               'VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING *',
               [org, amount, balance + amount, action, key, reference, expires])


def consume_lot(org, lot, credits, entry):
    """Caller holds the org lock; each debit is attributable to its grant lot."""
    changed = one('UPDATE public.credit_lots SET remaining=remaining-%s '
                  'WHERE org_id=%s AND id=%s AND remaining>=%s RETURNING remaining',
                  [credits, org, lot['id'], credits])
    one('INSERT INTO public.credit_lot_movements(org_id,lot_id,ledger_id,amount,remaining_after) '
        'VALUES(%s,%s,%s,%s,%s) RETURNING id',
        [org, lot['id'], entry['id'], -credits, changed['remaining']])


def expire_lot(org, lot, *, key=None, action='CREDIT_EXPIRY'):
    if lot['remaining']:
        entry = append(org, -lot['remaining'], action, key or 'expiry:' + str(lot['id']), lot['grant_id'])
        consume_lot(org, lot, lot['remaining'], entry)


def reconcile(org):
    """Lazy and repeatable; no perfectly timed cron is required for entitlement safety."""
    organization = locked_org(org)
    from billing import lifecycle
    lifecycle.reconcile(org)
    from billing.settlement import grant_due
    grant_due(org)
    expired = rows('SELECT * FROM public.credit_lots WHERE org_id=%s AND remaining>0 '
                   'AND expires_at<=%s ORDER BY expires_at,id FOR UPDATE', [org, timezone.now()])
    for lot in expired:
        expire_lot(org, lot)
    organization = locked_org(org)
    if organization['subscription_tier'] == 'TRIAL':
        rows("UPDATE public.tenancy_organizations SET subscription_tier='STARTER',updated_at=now() "
             'WHERE id=%s AND trial_ends_at<=statement_timestamp() RETURNING id', [org])
    return locked_org(org)


def debit(org, credits: int, audit_id: UUID):
    """One audit → one debit. Lock, audit binding, lot consumption and ledger are atomic."""
    if type(credits) is not int or credits <= 0:
        raise ValueError('Debit requires positive integral credits')
    with financial_transaction(org):
        organization = reconcile(org)
        key = 'ai:' + str(audit_id)
        previous = rows('SELECT * FROM public.credit_ledger WHERE org_id=%s AND operation_key=%s',
                        [org, key])
        if previous:
            if previous[0]['amount'] != -credits:
                raise contract_error(409, 'wallet_replay_conflict', 'El consumo ya fue registrado con otro valor.')
            return previous[0]
        audit = rows('SELECT id FROM public.ai_audit_logs WHERE org_id=%s AND id=%s '
                     'AND points_debited=%s', [org, audit_id, credits])
        if not audit:
            raise contract_error(409, 'wallet_audit_required', 'Falta la auditoría del consumo.')
        if organization['subscription_tier'] == 'STARTER' or not organization['subscription_active']:
            raise contract_error(409, 'ai_entitlement_required', 'Tu plan conserva todas las funciones manuales.')
        if organization['credits_balance'] < credits:
            raise contract_error(409, 'insufficient_credits', 'No quedan créditos suficientes para esta operación de IA.')
        entry = append(org, -credits, 'AI_DEBIT', key, audit_id)
        remaining = credits
        lots = rows('SELECT * FROM public.credit_lots WHERE org_id=%s AND remaining>0 '
                    'ORDER BY expires_at NULLS LAST,created_at,id FOR UPDATE', [org])
        for lot in lots:
            consumed = min(remaining, lot['remaining'])
            consume_lot(org, lot, consumed, entry)
            remaining -= consumed
            if remaining == 0:
                break
        if remaining:
            raise contract_error(409, 'wallet_lots_inconsistent', 'La billetera requiere conciliación.')
        return entry


def summary(org):
    with financial_transaction(org):
        organization = reconcile(org)
        ledger = rows('SELECT id,amount,balance_after,action_type,reference_id,expires_at,created_at '
                      'FROM public.credit_ledger WHERE org_id=%s ORDER BY entry_number DESC LIMIT 100', [org])
        lots = rows('SELECT id,grant_id,origin,remaining,expires_at FROM public.credit_lots '
                    'WHERE org_id=%s ORDER BY expires_at NULLS LAST,created_at,id', [org])
        return {'lots': lots, 'plan': organization['subscription_tier'], 'balance': organization['credits_balance'],
                'trial_ends_at': organization['trial_ends_at'], 'billing_cycle': organization['billing_cycle'],
                'ai_available': organization['subscription_tier'] != 'STARTER'
                    and organization['subscription_active'] and organization['credits_balance'] > 0,
                'ledger': ledger}


def billing_summary(org):
    with financial_transaction(org):
        organization = reconcile(org)
        subscriptions = rows('SELECT plan_tier,billing_cycle,status,currency,amount,current_period_end '
                             'FROM public.subscriptions WHERE org_id=%s', [org])
        payments = rows('SELECT id,amount,currency,status,tax_doc_type,tax_doc_folio,created_at '
                        'FROM public.payments WHERE org_id=%s ORDER BY created_at DESC,id DESC LIMIT 100', [org])
        for record in [*subscriptions, *payments]:
            record['amount'] = format(record['amount'], '.0f' if record['currency'] == 'CLP' else '.2f')
        return {'plan': organization['subscription_tier'], 'trial_ends_at': organization['trial_ends_at'],
                'subscription': subscriptions[0] if subscriptions else None, 'payments': payments}
