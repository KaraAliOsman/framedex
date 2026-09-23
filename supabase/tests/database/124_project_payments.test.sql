BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(9);

SELECT has_table('public', 'project_payments', 'project payments table exists');
SELECT has_column('public', 'project_payments', 'operation_key', 'idempotency key captured');
SELECT has_column('public', 'project_payments', 'voided_at', 'void state captured');
SELECT ok(
    EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE schemaname = 'public' AND tablename = 'project_payments'
          AND indexdef LIKE '%UNIQUE%(org_id, operation_key)%'
    ),
    'recording is idempotent per operation key'
);
SELECT ok(
    (SELECT relrowsecurity FROM pg_class WHERE relname = 'project_payments'),
    'payments enforce RLS'
);
SELECT ok(
    EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'project_payments'
          AND policyname = 'project_payments_isolation'
    ),
    'tenant isolation policy in place'
);
SELECT ok(
    has_table_privilege('documentary_backend', 'public.project_payments', 'SELECT')
    AND has_table_privilege('documentary_backend', 'public.project_payments', 'INSERT')
    AND has_column_privilege(
        'documentary_backend', 'public.project_payments', 'voided_at', 'UPDATE')
    AND NOT has_table_privilege('documentary_backend', 'public.project_payments', 'UPDATE')
    AND NOT has_table_privilege('documentary_backend', 'public.project_payments', 'DELETE'),
    'backend role records and voids only, never deletes'
);
SELECT ok(
    has_table_privilege('authenticated', 'public.project_payments', 'SELECT')
    AND NOT has_table_privilege('authenticated', 'public.project_payments', 'INSERT')
    AND NOT has_table_privilege('authenticated', 'public.project_payments', 'UPDATE'),
    'tenant roles read payments only'
);
SELECT ok(
    NOT has_table_privilege('anon', 'public.project_payments', 'SELECT'),
    'anonymous role cannot read payments'
);

SELECT * FROM finish();
ROLLBACK;
