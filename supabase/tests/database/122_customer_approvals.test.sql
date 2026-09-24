BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(10);

SELECT has_table('public', 'customer_approvals', 'customer approvals table exists');
SELECT has_column('public', 'customer_approvals', 'token_hash', 'token stored hashed only');
SELECT has_column('public', 'customer_approvals', 'decided_by', 'decider captured');
SELECT ok(
    EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'customer_approvals'
          AND policyname = 'customer_approvals_portal_read'
    ),
    'portal role reaches approvals without org claims'
);
SELECT ok(
    EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'projects'
          AND policyname = 'projects_portal_decide'
    ),
    'portal role can transition the shared project'
);
SELECT ok(
    (SELECT relrowsecurity FROM pg_class WHERE relname = 'customer_approvals'),
    'approvals enforce RLS'
);
SELECT ok(
    has_table_privilege('portal_backend', 'public.customer_approvals', 'SELECT')
    AND has_table_privilege('portal_backend', 'public.customer_approvals', 'UPDATE')
    AND has_table_privilege('portal_backend', 'public.projects', 'UPDATE')
    AND has_table_privilege('portal_backend', 'public.document_artifacts', 'SELECT'),
    'portal backend holds the capability surface'
);
SELECT ok(
    NOT has_table_privilege('authenticated', 'public.customer_approvals', 'INSERT')
    AND NOT has_table_privilege('authenticated', 'public.customer_approvals', 'UPDATE'),
    'tenant roles cannot forge or rewrite approvals'
);
SELECT ok(
    has_table_privilege('authenticated', 'public.customer_approvals', 'SELECT'),
    'tenant roles can read their approvals'
);
SELECT ok(
    NOT has_table_privilege('anon', 'public.customer_approvals', 'SELECT'),
    'anonymous role cannot read approvals'
);

SELECT * FROM finish();
ROLLBACK;
