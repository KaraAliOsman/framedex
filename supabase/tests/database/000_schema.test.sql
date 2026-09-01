BEGIN;

CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;
SET LOCAL search_path = public, extensions;

SELECT plan(47);

SELECT ok(
    to_regclass('public.' || table_name) IS NOT NULL,
    table_name || ' exists'
)
FROM unnest(ARRAY[
    'tenancy_organizations',
    'tenancy_memberships',
    'profile_systems',
    'profile_articles',
    'glazing_bead_matrix',
    'hardware_kits',
    'cost_lists',
    'cost_list_items',
    'pricing_rules',
    'price_audit_logs',
    'projects',
    'project_positions',
    'project_versions',
    'orders',
    'offcut_inventory',
    'ai_audit_logs',
    'payment_customers',
    'subscriptions',
    'payments',
    'payment_events',
    'credit_ledger'
]) AS expected(table_name);

SELECT ok(
    catalog.relrowsecurity,
    expected.table_name || ' has RLS enabled'
)
FROM unnest(ARRAY[
    'tenancy_organizations',
    'tenancy_memberships',
    'profile_systems',
    'profile_articles',
    'glazing_bead_matrix',
    'hardware_kits',
    'cost_lists',
    'cost_list_items',
    'pricing_rules',
    'price_audit_logs',
    'projects',
    'project_positions',
    'project_versions',
    'orders',
    'offcut_inventory',
    'ai_audit_logs',
    'payment_customers',
    'subscriptions',
    'payments',
    'payment_events',
    'credit_ledger'
]) AS expected(table_name)
JOIN pg_class AS catalog
  ON catalog.oid = to_regclass('public.' || expected.table_name);

SELECT is(
    (
        SELECT count(*)
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = ANY (ARRAY[
              'profile_systems',
              'profile_articles',
              'glazing_bead_matrix',
              'hardware_kits',
              'cost_list_items',
              'pricing_rules',
              'price_audit_logs',
              'projects',
              'project_positions',
              'subscriptions',
              'payments'
          ])
          AND data_type IN ('real', 'double precision')
    ),
    0::BIGINT,
    'business numeric columns contain no floating point types'
);

SELECT is(
    (
        SELECT is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'payment_events'
          AND column_name = 'org_id'
    ),
    'YES',
    'payment_events.org_id is an optional tenant index'
);

SELECT ok(
    (
        SELECT procedure.prosecdef
        FROM pg_proc AS procedure
        JOIN pg_namespace AS namespace ON namespace.oid = procedure.pronamespace
        WHERE namespace.nspname = 'public'
          AND procedure.proname = 'current_user_org_ids'
    ),
    'current_user_org_ids is SECURITY DEFINER'
);

SELECT ok(
    to_regprocedure('public.is_platform_superadmin()') IS NOT NULL,
    'JWT superadmin metadata helper exists'
);

SELECT is(
    (
        SELECT count(*)
        FROM pg_class AS catalog
        WHERE catalog.oid = ANY (ARRAY[
            'public.payment_events'::REGCLASS,
            'public.credit_ledger'::REGCLASS,
            'public.hardware_kits'::REGCLASS
        ])
    ),
    3::BIGINT,
    'all nominal SHOT-02 gate tables exist'
);

SELECT * FROM finish();
ROLLBACK;
