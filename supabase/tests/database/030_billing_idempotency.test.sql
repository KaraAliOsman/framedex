BEGIN;

CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;
SET LOCAL search_path = public, extensions;

SELECT plan(7);

INSERT INTO public.tenancy_organizations (id, name, tax_id)
VALUES
    ('11111111-1111-4111-8111-111111111111', 'Tenant A', 'A-1'),
    ('22222222-2222-4222-8222-222222222222', 'Tenant B', 'B-1');

INSERT INTO public.tenancy_memberships (org_id, user_id, role)
VALUES (
    '11111111-1111-4111-8111-111111111111',
    'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    'OWNER'
);

INSERT INTO public.payment_events (org_id, provider, event_id, payload)
VALUES (
    '11111111-1111-4111-8111-111111111111',
    'flow',
    'event-1',
    '{}'::JSONB
);

CREATE FUNCTION pg_temp.duplicate_event_is_blocked()
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO public.payment_events (provider, event_id, payload)
    VALUES ('flow', 'event-1', '{}'::JSONB);
    RETURN FALSE;
EXCEPTION WHEN unique_violation THEN
    RETURN TRUE;
END;
$$;

SELECT ok(pg_temp.duplicate_event_is_blocked(), 'provider events are idempotent');

INSERT INTO public.payments (
    org_id,
    provider,
    provider_payment_id,
    amount,
    currency
)
VALUES (
    '11111111-1111-4111-8111-111111111111',
    'flow',
    'payment-1',
    1000.00,
    'CLP'
);

CREATE FUNCTION pg_temp.duplicate_payment_is_blocked()
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO public.payments (
        org_id,
        provider,
        provider_payment_id,
        amount,
        currency
    )
    VALUES (
        '11111111-1111-4111-8111-111111111111',
        'flow',
        'payment-1',
        1000.00,
        'CLP'
    );
    RETURN FALSE;
EXCEPTION WHEN unique_violation THEN
    RETURN TRUE;
END;
$$;

SELECT ok(pg_temp.duplicate_payment_is_blocked(), 'provider payments are idempotent');

CREATE FUNCTION pg_temp.negative_balance_is_blocked()
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO public.credit_ledger (org_id, amount, balance_after, action_type)
    VALUES ('11111111-1111-4111-8111-111111111111', -1, -1, 'test');
    RETURN FALSE;
EXCEPTION WHEN check_violation THEN
    RETURN TRUE;
END;
$$;

SELECT ok(pg_temp.negative_balance_is_blocked(), 'ledger balance cannot become negative');

INSERT INTO public.credit_ledger (org_id, amount, balance_after, action_type)
VALUES
    ('11111111-1111-4111-8111-111111111111', 10, 10, 'test'),
    ('22222222-2222-4222-8222-222222222222', 20, 20, 'test');

SET LOCAL ROLE authenticated;
SELECT set_config(
    'request.jwt.claims',
    '{"sub":"aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa","role":"authenticated"}',
    TRUE
);
SELECT set_config(
    'request.jwt.claim.sub',
    'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    TRUE
);

SELECT is((SELECT count(*) FROM public.credit_ledger), 1::BIGINT, 'tenant A sees its ledger');
SELECT is(
    (
        SELECT count(*)
        FROM public.credit_ledger
        WHERE org_id = '22222222-2222-4222-8222-222222222222'
    ),
    0::BIGINT,
    'tenant A cannot see tenant B ledger'
);

RESET ROLE;
SELECT ok(
    NOT has_table_privilege('authenticated', 'public.payment_events', 'SELECT'),
    'authenticated users have no payment event privilege'
);
SELECT is(
    (
        SELECT count(*)
        FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'payment_events'
          AND policyname = 'payment_events_service_role'
          AND cmd = 'ALL'
          AND qual LIKE '%service_role%'
          AND with_check LIKE '%service_role%'
    ),
    1::BIGINT,
    'payment events expose only the service role policy'
);

SELECT * FROM finish();
ROLLBACK;
