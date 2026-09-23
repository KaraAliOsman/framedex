BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(16);

SELECT has_table('public', 'org_payment_integrations', 'org payment integrations table exists');
SELECT has_table('public', 'project_payment_links', 'project payment links table exists');
SELECT has_column('public', 'project_payment_links', 'operation_key', 'claim carries the ledger idempotency key');
SELECT has_column('public', 'project_payment_links', 'flow_token', 'provider token captured');
SELECT has_column('public', 'project_payment_links', 'flow_api_url', 'dispatch credential snapshot: url');
SELECT has_column('public', 'project_payment_links', 'flow_api_key', 'dispatch credential snapshot: key');
SELECT has_column('public', 'project_payment_links', 'flow_secret_key', 'dispatch credential snapshot: secret');
SELECT ok(
    EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE schemaname = 'public' AND tablename = 'project_payment_links'
          AND indexdef LIKE '%UNIQUE%(org_id, operation_key)%'
    ),
    'link claims are idempotent per operation key'
);
SELECT ok(
    EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.project_payment_links'::regclass
          AND pg_get_constraintdef(oid) LIKE '%amount > (0)%'
          AND pg_get_constraintdef(oid) LIKE '%amount = trunc(amount)%'
    ),
    'link amounts are positive integral CLP'
);
SELECT ok(
    (SELECT relrowsecurity FROM pg_class WHERE relname = 'project_payment_links')
    AND (SELECT relrowsecurity FROM pg_class WHERE relname = 'org_payment_integrations'),
    'both tables enforce RLS'
);
SELECT ok(
    EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'project_payment_links'
          AND policyname = 'project_payment_links_isolation'
    ),
    'tenant isolation policy in place'
);
SELECT ok(
    has_table_privilege('authenticated', 'public.project_payment_links', 'SELECT')
    AND NOT has_table_privilege('authenticated', 'public.project_payment_links', 'INSERT')
    AND NOT has_table_privilege('authenticated', 'public.project_payment_links', 'UPDATE'),
    'tenant roles read links only'
);
SELECT ok(
    NOT has_table_privilege('authenticated', 'public.org_payment_integrations', 'SELECT')
    AND NOT has_table_privilege('authenticated', 'public.org_payment_integrations', 'INSERT'),
    'flow credentials are invisible to tenant roles'
);
SELECT ok(
    NOT has_table_privilege('anon', 'public.org_payment_integrations', 'SELECT')
    AND NOT has_table_privilege('anon', 'public.project_payment_links', 'SELECT'),
    'anonymous role cannot reach payments data'
);
SELECT ok(
    has_table_privilege('documentary_backend', 'public.project_payment_links', 'INSERT')
    AND has_table_privilege('documentary_backend', 'public.project_payment_links', 'UPDATE')
    AND has_table_privilege('documentary_backend', 'public.org_payment_integrations', 'INSERT')
    AND has_table_privilege('documentary_backend', 'public.org_payment_integrations', 'UPDATE'),
    'backend role manages links and credentials'
);
SELECT ok(
    NOT has_table_privilege('anon', 'public.project_payment_links', 'INSERT')
    AND NOT has_table_privilege('anon', 'public.project_payment_links', 'UPDATE'),
    'anonymous role cannot write link claims'
);

SELECT * FROM finish();
ROLLBACK;
