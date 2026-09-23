BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(14);

SELECT has_table('public', 'ai_routes', 'AI routing table exists');
SELECT has_column('public', 'ai_routes', 'public_name', 'white-label name is stored');
SELECT has_column('public', 'ai_routes', 'provider_model', 'real model stays on the route');
SELECT has_column('public', 'ai_routes', 'credits_cost', 'per-invocation price on the route');
SELECT ok(
    EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.ai_routes'::regclass
          AND pg_get_constraintdef(oid) LIKE '%UNIQUE%(capability)%'
    ),
    'capability names are unique'
);
SELECT ok(
    EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.ai_routes'::regclass
          AND pg_get_constraintdef(oid) LIKE '%credits_cost > 0%'
    ),
    'route prices are strictly positive credits'
);
SELECT ok(
    (SELECT count(*) = 5 FROM public.ai_routes WHERE provider = 'MOCK' AND enabled),
    'five deterministic MOCK capabilities are seeded'
);
SELECT ok(
    (SELECT relrowsecurity FROM pg_class WHERE relname = 'ai_routes'),
    'routing table enforces RLS'
);
SELECT ok(
    EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'ai_routes'
          AND policyname = 'ai_routes_backend_read'
    ),
    'only the billing-scoped backend role may read routes'
);
SELECT ok(
    NOT has_table_privilege('authenticated', 'public.ai_routes', 'SELECT')
    AND NOT has_table_privilege('anon', 'public.ai_routes', 'SELECT')
    AND NOT has_table_privilege('authenticated', 'public.ai_routes', 'INSERT'),
    'tenants can never see provider internals'
);
SELECT ok(
    has_table_privilege('billing_backend', 'public.ai_routes', 'SELECT'),
    'billing backend resolves routes inside the financial transaction'
);
-- Audit hardening: tenants read their own rows, only billing_backend writes.
SELECT ok(
    NOT has_table_privilege('authenticated', 'public.ai_audit_logs', 'INSERT')
    AND NOT has_table_privilege('authenticated', 'public.ai_audit_logs', 'UPDATE')
    AND NOT has_table_privilege('authenticated', 'public.ai_audit_logs', 'DELETE'),
    'tenant roles can never write audit rows'
);
SELECT ok(
    has_table_privilege('billing_backend', 'public.ai_audit_logs', 'INSERT'),
    'billing backend seals each invocation into the audit log'
);
SELECT ok(
    has_table_privilege('authenticated', 'public.ai_audit_logs', 'SELECT'),
    'tenants keep read access to their own audit trail'
);

SELECT * FROM finish();
ROLLBACK;
