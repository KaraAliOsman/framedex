DO $$
DECLARE
    business_table_count INT;
    rls_table_count INT;
    demo_system_count INT;
    demo_profile_authority_count INT;
    demo_glazing_rule_count INT;
    demo_family_count INT;
    demo_family_profile_count INT;
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
          'infill_articles',
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

    IF business_table_count <> 22 THEN
        RAISE EXCEPTION 'Expected 22 business tables, got %', business_table_count;
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
          'infill_articles',
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

    IF rls_table_count <> 22 THEN
        RAISE EXCEPTION 'Expected RLS on 22 business tables, got %', rls_table_count;
    END IF;

    SELECT count(*)
    INTO demo_system_count
    FROM public.profile_systems
    WHERE code = 'DEMO_60'
      AND version = 1
      AND legacy_authority = TRUE
      AND org_id IS NULL
      AND is_global = TRUE
      AND is_demo = TRUE
      AND central_overlap_mm = 40.00;

    IF demo_system_count <> 1 THEN
        RAISE EXCEPTION 'Expected one canonical global DEMO_60 system, got %', demo_system_count;
    END IF;

    SELECT count(*)
    INTO demo_profile_authority_count
    FROM public.profile_articles AS article
    JOIN public.profile_systems AS profile_system
      ON profile_system.id = article.system_id
    WHERE profile_system.code = 'DEMO_60'
      AND profile_system.version = 1
      AND profile_system.legacy_authority = TRUE
      AND profile_system.org_id IS NULL
      AND article.org_id IS NULL
      AND (
          (article.role = 'FRAME' AND article.face_width_mm = 60.00 AND article.reinforcement_gap_mm = 15.00)
          OR (article.role = 'SASH' AND article.face_width_mm = 75.00 AND article.reinforcement_gap_mm = 15.00)
          OR (article.role = 'MULLION_V' AND article.face_width_mm = 80.00 AND article.reinforcement_gap_mm = 5.00)
          OR (article.role = 'MULLION_H' AND article.face_width_mm = 80.00 AND article.reinforcement_gap_mm = 5.00)
      );

    IF demo_profile_authority_count <> 4 THEN
        RAISE EXCEPTION
            'Expected four canonical DEMO_60 profile authorities, got %',
            demo_profile_authority_count;
    END IF;

    SELECT count(*)
    INTO demo_glazing_rule_count
    FROM public.glazing_bead_matrix AS bead_rule
    JOIN public.profile_systems AS profile_system
      ON profile_system.id = bead_rule.system_id
    WHERE profile_system.code = 'DEMO_60'
      AND profile_system.version = 1
      AND profile_system.legacy_authority = TRUE
      AND profile_system.org_id IS NULL
      AND bead_rule.org_id IS NULL
      AND bead_rule.cut_add_mm = 9.00;

    IF demo_glazing_rule_count <> 5 THEN
        RAISE EXCEPTION
            'Expected five DEMO_60 glazing rules with cut_add_mm 9.00, got %',
            demo_glazing_rule_count;
    END IF;

    SELECT count(*) INTO demo_family_count
    FROM public.profile_systems
    WHERE code = ANY(ARRAY['DEMO_60','DEMO_70','DEMO_CORREDERA_60',
                           'DEMO_ALU_CORREDERA','DEMO_ALU_PRACTICABLE'])
      AND version = 2 AND org_id IS NULL AND is_global AND is_demo
      AND NOT legacy_authority AND system_family IS NOT NULL;
    IF demo_family_count <> 5 THEN
        RAISE EXCEPTION 'Expected five separately declared DEMO v2 families, got %', demo_family_count;
    END IF;

    SELECT count(*) INTO demo_family_profile_count
    FROM public.profile_articles article
    JOIN public.profile_systems profile_system ON profile_system.id = article.system_id
    WHERE profile_system.code = ANY(ARRAY['DEMO_60','DEMO_70','DEMO_CORREDERA_60',
                                         'DEMO_ALU_CORREDERA','DEMO_ALU_PRACTICABLE'])
      AND profile_system.version = 2 AND profile_system.org_id IS NULL
      AND profile_system.is_global AND profile_system.is_demo
      AND NOT profile_system.legacy_authority AND article.org_id IS NULL
      AND article.cut_rule IS NOT NULL;
    IF demo_family_profile_count <> 39 THEN
        RAISE EXCEPTION 'Expected 39 sourced DEMO v2 profile cut authorities, got %', demo_family_profile_count;
    END IF;
END;
$$;
