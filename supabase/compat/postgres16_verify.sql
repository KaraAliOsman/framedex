DO $$
DECLARE
    business_table_count INT;
    rls_table_count INT;
    demo_system_count INT;
BEGIN
    IF current_setting('server_version_num')::INT < 160000
        OR current_setting('server_version_num')::INT >= 170000 THEN
        RAISE EXCEPTION 'Expected PostgreSQL 16, got %', current_setting('server_version');
    END IF;

    SELECT count(*)
    INTO business_table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
      AND table_name = ANY (ARRAY[
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
      ]);

    IF business_table_count <> 21 THEN
        RAISE EXCEPTION 'Expected 21 business tables, got %', business_table_count;
    END IF;

    SELECT count(*)
    INTO rls_table_count
    FROM pg_class AS catalog
    JOIN pg_namespace AS namespace ON namespace.oid = catalog.relnamespace
    WHERE namespace.nspname = 'public'
      AND catalog.relname = ANY (ARRAY[
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
      ])
      AND catalog.relrowsecurity = TRUE;

    IF rls_table_count <> 21 THEN
        RAISE EXCEPTION 'Expected RLS on 21 business tables, got %', rls_table_count;
    END IF;

    SELECT count(*)
    INTO demo_system_count
    FROM public.profile_systems
    WHERE code = 'DEMO_60'
      AND org_id IS NULL
      AND is_global = TRUE
      AND is_demo = TRUE
      AND central_overlap_mm = 40.00;

    IF demo_system_count <> 1 THEN
        RAISE EXCEPTION 'Expected one canonical global DEMO_60 system, got %', demo_system_count;
    END IF;
END;
$$;
