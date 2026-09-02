BEGIN;

CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;
SET LOCAL search_path = public, extensions;

SELECT plan(55);

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
    EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'tenancy_organizations'
          AND column_name = 'credits_balance'
    ),
    'organizations expose the canonical credits balance'
);

SELECT ok(
    EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'profile_systems'
          AND column_name = 'is_demo'
    ),
    'profile systems identify isolated demo catalogs'
);

SELECT ok(
    to_regclass('public.uk_tenant_system_code') IS NOT NULL,
    'tenant system codes use the canonical partial unique index'
);

SELECT ok(
    EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'profile_articles'
          AND column_name = 'welding_loss_mm'
    )
    AND NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'profile_systems'
          AND column_name = 'welding_loss_mm'
    ),
    'profile articles are the only welding loss authority'
);

SELECT ok(
    (
        SELECT procedure.prosecdef
        FROM pg_proc AS procedure
        JOIN pg_namespace AS namespace ON namespace.oid = procedure.pronamespace
        WHERE namespace.nspname = 'private'
          AND procedure.proname = 'current_user_org_ids'
    ),
    'private.current_user_org_ids is SECURITY DEFINER'
);

SELECT is(
    (
        SELECT procedure.proconfig
        FROM pg_proc AS procedure
        JOIN pg_namespace AS namespace ON namespace.oid = procedure.pronamespace
        WHERE namespace.nspname = 'private'
          AND procedure.proname = 'current_user_org_ids'
    ),
    ARRAY['search_path=""']::TEXT[],
    'current_user_org_ids has an empty search_path'
);

SELECT ok(
    has_schema_privilege('authenticated', 'private', 'USAGE'),
    'authenticated can resolve the private RLS helper'
);

SELECT ok(
    has_function_privilege(
        'authenticated',
        'private.current_user_org_ids()',
        'EXECUTE'
    ),
    'authenticated can execute the private RLS helper'
);

SELECT ok(
    NOT has_function_privilege('anon', 'private.current_user_org_ids()', 'EXECUTE'),
    'anonymous cannot execute the private RLS helper'
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
