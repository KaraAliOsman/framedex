BEGIN;
SELECT plan(6);

-- The verified settlement runs under billing_backend pinned to the org — every
-- object it touches needs a billing-scoped policy pair, or the public Flow
-- callback rolls the ledger write back.

SELECT ok(
    has_table_privilege('billing_backend', 'public.projects', 'SELECT')
    AND has_table_privilege('billing_backend', 'public.project_versions', 'SELECT')
    AND has_table_privilege('billing_backend', 'public.tenancy_organizations', 'SELECT'),
    'billing scope reads the project, its sealed versions and the org currency'
);
SELECT ok(
    has_table_privilege('billing_backend', 'public.payment_receipts', 'SELECT')
    AND has_table_privilege('billing_backend', 'public.payment_receipts', 'INSERT')
    AND NOT has_table_privilege('billing_backend', 'public.payment_receipts', 'UPDATE')
    AND NOT has_table_privilege('billing_backend', 'public.payment_receipts', 'DELETE'),
    'billing scope seals comprobantes but never amends them'
);
SELECT ok(
    has_function_privilege('billing_backend', 'private.applied_pricing_currency(uuid,uuid)', 'EXECUTE'),
    'billing scope can resolve an applied-pricing live deal'
);
SELECT ok(
    EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'projects'
          AND policyname = 'billing_backend_scope'
    ) AND EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'projects'
          AND policyname = 'billing_backend_restrict'
    ),
    'projects rows stay pinned to the billing org on both policy halves'
);
SELECT ok(
    EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'project_versions'
          AND policyname = 'billing_backend_scope'
    ) AND EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'tenancy_organizations'
          AND policyname = 'billing_backend_scope'
    ),
    'sealed versions and the org row are billing-readable'
);
SELECT ok(
    NOT has_table_privilege('authenticated', 'public.payment_receipts', 'INSERT')
    AND NOT has_table_privilege('authenticated', 'public.payment_receipts', 'UPDATE'),
    'receipt writes stay behind the backend roles'
);

SELECT * FROM finish();
ROLLBACK;
