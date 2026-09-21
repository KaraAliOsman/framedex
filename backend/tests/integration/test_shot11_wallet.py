"""Real PostgreSQL ledger, row-lock concurrency, RLS and rollback proofs."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import uuid4

from django.db import connection, transaction, DatabaseError, close_old_connections
from django.utils import timezone
import pytest

from authentication.errors import ContractAPIException
from billing import wallet
from pricing.repository import one, rows
from backend.tests.integration.test_shot08_pricing import (
    commercial_rows as commercial_rows, committed_commercial_rows as committed_commercial_rows,
    as_user,
)

pytestmark = pytest.mark.rls_integration


def audit(org, credits):
    return one("INSERT INTO public.ai_audit_logs(org_id,user_id,tool_name,model_used,prompt_version,"
               "retention_until,input_payload,output_payload,state_hash_before,points_debited) "
               "VALUES(%s,%s,'contract-fixture','network-not-called','fixture',now()+interval '1 day',"
               "'{}','{}','fixture',%s) RETURNING id", [org, uuid4(), credits])['id']


def assert_consistent(org, balance):
    assert one('SELECT credits_balance FROM public.tenancy_organizations WHERE id=%s', [org])['credits_balance'] == balance
    assert one('SELECT sum(amount) AS total FROM public.credit_ledger WHERE org_id=%s', [org])['total'] == balance
    assert one('SELECT sum(remaining) AS total FROM public.credit_lots WHERE org_id=%s', [org])['total'] == balance


def test_trial_has_seven_days_exactly_one_grant_and_starter_zero(commercial_rows):
    org, _, users = commercial_rows
    record = one('SELECT * FROM public.tenancy_organizations WHERE id=%s', [org])
    assert record['trial_ends_at'] - record['created_at'] == timedelta(days=7)
    with as_user(users['OWNER']):
        assert wallet.summary(org)['balance'] == 500
        assert wallet.summary(org)['balance'] == 500
    with connection.cursor() as cursor:
        cursor.execute('RESET ROLE')
    assert_consistent(org, 500)
    starter = one("INSERT INTO public.tenancy_organizations(name,tax_id,subscription_tier) "
                  "VALUES('Starter','fixture','STARTER') RETURNING id")['id']
    assert one('SELECT credits_balance FROM public.tenancy_organizations WHERE id=%s', [starter])['credits_balance'] == 0
    assert rows('SELECT * FROM public.credit_ledger WHERE org_id=%s', [starter]) == []


def test_expiry_is_lazy_and_idempotent(commercial_rows):
    org, _, _ = commercial_rows
    # Advance both persisted expiry authorities to model a seven-day-old signup.
    past = timezone.now() - timedelta(days=1)
    one('UPDATE public.tenancy_organizations SET trial_ends_at=%s WHERE id=%s RETURNING id', [past, org])
    one('UPDATE public.credit_lots SET expires_at=%s WHERE org_id=%s RETURNING id', [past, org])
    for _ in range(3):
        summary = wallet.summary(org)
        assert summary['plan'] == 'STARTER'
        assert not summary['ai_available']
        assert summary['balance'] == 0
    assert_consistent(org, 0)
    assert len(rows('SELECT * FROM public.credit_ledger WHERE org_id=%s', [org])) == 2


def test_debit_audit_binding_replay_and_zero_balance(commercial_rows):
    org, other, _ = commercial_rows
    foreign = audit(other, 500)
    with pytest.raises(ContractAPIException):
        wallet.debit(org, 500, foreign)
    reference = audit(org, 500)
    first = wallet.debit(org, 500, reference)
    assert wallet.debit(org, 500, reference)['id'] == first['id']
    with pytest.raises(ContractAPIException):
        wallet.debit(org, 499, reference)
    assert_consistent(org, 0)
    next_reference = audit(org, 1)
    with pytest.raises(ContractAPIException):
        wallet.debit(org, 1, next_reference)
    assert_consistent(org, 0)


def test_injected_failure_rolls_back_lots_balance_and_ledger(commercial_rows, monkeypatch):
    org, _, _ = commercial_rows
    reference = audit(org, 100)
    original = wallet.append
    def fail_after_append(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError('injected after ledger insertion')
    monkeypatch.setattr(wallet, 'append', fail_after_append)
    with pytest.raises(RuntimeError):
        wallet.debit(org, 100, reference)
    assert_consistent(org, 500)


def test_owner_client_cannot_mutate_ledger_or_assume_backend_role(commercial_rows):
    org, other, users = commercial_rows
    with as_user(users['ESTIMATOR']):
        assert rows('SELECT * FROM public.credit_ledger WHERE org_id=%s', [org]) == []
    with as_user(users['OWNER']):
        assert rows('SELECT * FROM public.credit_ledger WHERE org_id=%s', [other]) == []
        with pytest.raises(DatabaseError), transaction.atomic():
            one("INSERT INTO public.credit_ledger(org_id,amount,balance_after,action_type) "
                "VALUES(%s,999,1499,'spoof') RETURNING id", [org])
    # Backend scope is still RLS-bound even though it can mutate financial tables.
    with wallet.financial_transaction(org):
        assert rows('SELECT * FROM public.credit_ledger WHERE org_id=%s', [other]) == []
    assert not one("SELECT pg_has_role('authenticated','billing_backend','MEMBER') AS permitted")['permitted']


def test_concurrent_duplicate_and_distinct_debits_serialize(committed_commercial_rows):
    org, _, _ = committed_commercial_rows
    reference = audit(org, 300)
    def debit(reference_id, amount):
        close_old_connections()
        try:
            return wallet.debit(org, amount, reference_id)['id']
        except ContractAPIException:
            return None
        finally:
            close_old_connections()
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: debit(reference, 300), range(4)))
    assert len(set(results)) == 1 and results[0] is not None
    assert_consistent(org, 200)
    references = [audit(org, 150), audit(org, 150)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda ref: debit(ref, 150), references))
    assert results.count(None) == 1
    assert_consistent(org, 50)
