BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(9);

SELECT has_table('public', 'job_runs', 'durable job queue table exists');
SELECT has_column('public', 'job_runs', 'org_id', 'jobs are tenant scoped');
SELECT ok(
    EXISTS (
        SELECT 1
        FROM pg_attribute a
        JOIN pg_class c ON a.attrelid = c.oid
        JOIN pg_namespace n ON c.relnamespace = n.oid
        WHERE n.nspname = 'public'
          AND c.relname = 'job_runs'
          AND a.attname = 'progress'
          AND format_type(a.atttypid, a.atttypmod) = 'numeric(5,2)'
    ),
    'progress keeps 0-100 fixed precision'
);
SELECT table_privs_are(
    'public',
    'job_runs',
    'authenticated',
    ARRAY[]::text[],
    'authenticated role has no direct job access'
);
SELECT policies_are(
    'public',
    'job_runs',
    ARRAY['job_runs_service_role'],
    'service role is the only job policy'
);
SELECT ok(
    EXISTS (
        SELECT 1
        FROM pg_indexes
        WHERE schemaname = 'public'
          AND tablename = 'job_runs'
          AND indexname = 'job_runs_claim_idx'
    ),
    'claim index is present for the worker'
);
SELECT ok(
    EXISTS (
        SELECT 1
        FROM pg_indexes
        WHERE schemaname = 'public'
          AND tablename = 'job_runs'
          AND indexname = 'uk_org_job_idempotency'
    ),
    'idempotency unique index is present'
);
SELECT throws_ok(
    $$INSERT INTO public.job_runs (org_id, type, state)
      VALUES ('00000000-0000-0000-0000-000000000000', 'x', 'BROKEN')$$,
    '23514',
    NULL,
    'job state accepts only the enumerated lifecycle'
);
SELECT ok(
    EXISTS (
        SELECT 1
        FROM pg_tables
        WHERE schemaname = 'public'
          AND tablename = 'job_runs'
          AND rowsecurity = true
    ),
    'job_runs enforces row level security'
);
SELECT * FROM finish();
ROLLBACK;
