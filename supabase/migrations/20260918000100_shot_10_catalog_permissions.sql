BEGIN;

CREATE FUNCTION private.can_manage_catalog(target_org UUID)
RETURNS BOOLEAN
LANGUAGE SQL STABLE SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.tenancy_memberships AS membership
        WHERE membership.org_id = target_org
          AND membership.user_id = auth.uid()
          AND membership.is_active
          AND (
              membership.role = 'WORKSHOP_MANAGER'
              OR (
                  membership.role = 'OWNER'
                  AND auth.jwt() ->> 'aal' = 'aal2'
              )
          )
    );
$$;

REVOKE ALL ON FUNCTION private.can_manage_catalog(UUID) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.can_manage_catalog(UUID) TO authenticated;

-- Fail visibly if historical rows violate the binding this migration secures.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM (
            SELECT system_id, org_id FROM public.profile_articles
            UNION ALL
            SELECT system_id, org_id FROM public.glazing_bead_matrix
            UNION ALL
            SELECT system_id, org_id FROM public.hardware_kits
        ) AS child
        WHERE child.system_id IS NOT NULL
          AND NOT EXISTS (
              SELECT 1
              FROM public.profile_systems AS parent
              WHERE parent.id = child.system_id
                AND (
                    (parent.org_id IS NULL AND parent.is_global)
                    OR (
                        child.org_id IS NOT NULL
                        AND parent.org_id = child.org_id
                    )
                )
          )
    ) OR EXISTS (
        SELECT 1
        FROM public.glazing_bead_matrix AS matrix
        WHERE NOT EXISTS (
            SELECT 1
            FROM public.profile_articles AS article
            JOIN public.profile_systems AS parent
              ON parent.id = article.system_id
            WHERE article.id = matrix.bead_article_id
              AND article.system_id = matrix.system_id
              AND article.role = 'GLAZING_BEAD'
              AND (
                  (
                      matrix.org_id IS NOT NULL
                      AND article.org_id = matrix.org_id
                  )
                  OR (
                      article.org_id IS NULL
                      AND parent.org_id IS NULL
                      AND parent.is_global
                  )
              )
        )
    ) THEN
        RAISE EXCEPTION 'catalog_existing_binding_invalid'
            USING ERRCODE = '23514';
    END IF;
END;
$$;

DROP POLICY profile_systems_select ON public.profile_systems;

CREATE POLICY profile_systems_select ON public.profile_systems
FOR SELECT TO authenticated
USING (
    org_id IN (SELECT private.current_user_org_ids())
    OR (
        auth.uid() IS NOT NULL
        AND org_id IS NULL
        AND is_global
    )
);

DROP POLICY profile_systems_modify ON public.profile_systems;

CREATE POLICY catalog_system_insert ON public.profile_systems
FOR INSERT TO authenticated
WITH CHECK (
    private.can_manage_catalog(org_id)
    AND NOT is_global AND NOT is_demo
);

CREATE POLICY catalog_system_update ON public.profile_systems
FOR UPDATE TO authenticated
USING (private.can_manage_catalog(org_id) AND NOT is_global AND NOT is_demo)
WITH CHECK (private.can_manage_catalog(org_id) AND NOT is_global AND NOT is_demo);

CREATE POLICY catalog_system_delete ON public.profile_systems
FOR DELETE TO authenticated
USING (private.can_manage_catalog(org_id) AND NOT is_global AND NOT is_demo);

DO $$
DECLARE
    table_name TEXT;
    binding TEXT;
BEGIN
    FOREACH table_name IN ARRAY ARRAY[
        'profile_articles', 'glazing_bead_matrix', 'hardware_kits'
    ]
    LOOP
        EXECUTE format(
            'DROP POLICY %I ON public.%I',
            table_name || '_modify', table_name
        );
        EXECUTE format(
            'DROP POLICY %I ON public.%I',
            table_name || '_select', table_name
        );

        -- Preserve global visibility without leaking a tenant child attached
        -- to a global system by an older unsafe policy.
        EXECUTE format(
            'CREATE POLICY catalog_read ON public.%I
             FOR SELECT TO authenticated USING (
                 org_id IN (SELECT private.current_user_org_ids())
                 OR (
                     auth.uid() IS NOT NULL
                     AND org_id IS NULL
                     AND system_id IN (
                         SELECT id FROM public.profile_systems
                         WHERE org_id IS NULL AND is_global
                     )
                 )
             )',
            table_name
        );

        binding := format(
    'EXISTS (
        SELECT 1 FROM public.profile_systems AS parent
        WHERE parent.id = %I.system_id
          AND (
              parent.org_id = %I.org_id
              OR (parent.org_id IS NULL AND parent.is_global)
          )
    )',
    table_name, table_name
);
        IF table_name = 'hardware_kits' THEN
            binding := '(system_id IS NULL OR ' || binding || ')';
        END IF;

        EXECUTE format(
            'CREATE POLICY catalog_insert ON public.%I
             FOR INSERT TO authenticated
             WITH CHECK (private.can_manage_catalog(org_id) AND %s)',
            table_name, binding
        );
        EXECUTE format(
            'CREATE POLICY catalog_update ON public.%I
             FOR UPDATE TO authenticated
             USING (private.can_manage_catalog(org_id) AND %s)
             WITH CHECK (private.can_manage_catalog(org_id) AND %s)',
            table_name, binding, binding
        );
        EXECUTE format(
            'CREATE POLICY catalog_delete ON public.%I
             FOR DELETE TO authenticated
             USING (private.can_manage_catalog(org_id) AND %s)',
            table_name, binding
        );
    END LOOP;
END;
$$;

CREATE FUNCTION private.guard_manual_catalog()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = ''
AS $$
DECLARE
    parent_org UUID;
    parent_global BOOLEAN;
    bead_org UUID;
    component JSONB;
    quantity NUMERIC;
BEGIN
    -- Privileged fixture/maintenance paths retain their existing authority.
    -- Every direct authenticated write, including PostgREST, passes here.
    IF current_user <> 'authenticated' THEN
        RETURN NEW;
    END IF;

    IF TG_OP = 'UPDATE' THEN
        IF NEW.id IS DISTINCT FROM OLD.id
           OR NEW.org_id IS DISTINCT FROM OLD.org_id THEN
            RAISE EXCEPTION 'catalog_identity_immutable' USING ERRCODE = '23514';
        END IF;
        IF TG_TABLE_NAME <> 'profile_systems' THEN
            IF NEW.system_id IS DISTINCT FROM OLD.system_id THEN
                RAISE EXCEPTION 'catalog_parent_immutable' USING ERRCODE = '23514';
            END IF;
        END IF;
    END IF;

    IF TG_TABLE_NAME = 'profile_systems' THEN
        RETURN NEW;
    END IF;

    IF NEW.system_id IS NOT NULL THEN
    SELECT org_id, is_global INTO parent_org, parent_global
    FROM public.profile_systems
    WHERE id = NEW.system_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'catalog_parent_invalid' USING ERRCODE = '23514';
    END IF;

    IF NOT (
        (parent_org IS NULL AND parent_global)
        OR (
            NEW.org_id IS NOT NULL
            AND parent_org IS NOT DISTINCT FROM NEW.org_id
        )
    ) THEN
        RAISE EXCEPTION 'catalog_parent_invalid' USING ERRCODE = '23514';
    END IF;
    -- Authenticated callers cannot edit global references. Lock only tenant
    -- references through the caller's existing UPDATE policy.
    IF parent_org IS NOT NULL THEN
        PERFORM id FROM public.profile_systems
        WHERE id = NEW.system_id AND org_id = NEW.org_id
        FOR SHARE;
        IF NOT FOUND THEN
            RAISE EXCEPTION 'catalog_parent_invalid' USING ERRCODE = '23514';
        END IF;
    END IF;
ELSIF TG_TABLE_NAME <> 'hardware_kits' THEN
    RAISE EXCEPTION 'catalog_parent_required' USING ERRCODE = '23514';
END IF;

    IF TG_TABLE_NAME = 'glazing_bead_matrix' THEN
    SELECT org_id INTO bead_org
    FROM public.profile_articles
    WHERE id = NEW.bead_article_id
      AND system_id = NEW.system_id
      AND role = 'GLAZING_BEAD'
      AND (
          org_id = NEW.org_id
          OR (
              org_id IS NULL
              AND parent_org IS NULL
              AND parent_global
          )
      );

    IF NOT FOUND THEN
        RAISE EXCEPTION 'catalog_bead_invalid' USING ERRCODE = '23514';
    END IF;
    IF bead_org IS NOT NULL THEN
        PERFORM id FROM public.profile_articles
        WHERE id = NEW.bead_article_id AND system_id = NEW.system_id
          AND org_id = NEW.org_id AND role = 'GLAZING_BEAD'
        FOR SHARE;
        IF NOT FOUND THEN
            RAISE EXCEPTION 'catalog_bead_invalid' USING ERRCODE = '23514';
        END IF;
    END IF;
END IF;

    IF TG_TABLE_NAME = 'profile_articles' AND TG_OP = 'UPDATE' THEN
        IF NEW.role <> 'GLAZING_BEAD' AND EXISTS (
            SELECT 1 FROM public.glazing_bead_matrix
            WHERE bead_article_id = NEW.id
        ) THEN
            RAISE EXCEPTION 'catalog_bead_in_use' USING ERRCODE = '23514';
        END IF;
    END IF;

    IF TG_TABLE_NAME = 'hardware_kits' THEN
        IF jsonb_typeof(NEW.contents) IS DISTINCT FROM 'array' THEN
            RAISE EXCEPTION 'catalog_contents_invalid' USING ERRCODE = '23514';
        END IF;
        FOR component IN SELECT value FROM jsonb_array_elements(NEW.contents)
        LOOP
            IF jsonb_typeof(component) IS DISTINCT FROM 'object' THEN
                RAISE EXCEPTION 'catalog_component_invalid' USING ERRCODE = '23514';
            END IF;
            IF NOT (component ?& ARRAY['sku', 'name', 'qty', 'unit'])
               OR component - ARRAY['sku', 'name', 'qty', 'unit'] <> '{}'::jsonb
               OR jsonb_typeof(component -> 'sku') IS DISTINCT FROM 'string'
               OR jsonb_typeof(component -> 'name') IS DISTINCT FROM 'string'
               OR jsonb_typeof(component -> 'unit') IS DISTINCT FROM 'string'
               OR jsonb_typeof(component -> 'qty') IS DISTINCT FROM 'number'
               OR btrim(component ->> 'sku') = ''
               OR btrim(component ->> 'name') = ''
               OR btrim(component ->> 'unit') = '' THEN
                RAISE EXCEPTION 'catalog_component_invalid' USING ERRCODE = '23514';
            END IF;
            quantity := (component ->> 'qty')::numeric;
            IF quantity <= 0 THEN
                RAISE EXCEPTION 'catalog_quantity_invalid' USING ERRCODE = '23514';
            END IF;
        END LOOP;
    END IF;
    RETURN NEW;
END;
$$;

REVOKE ALL ON FUNCTION private.guard_manual_catalog() FROM PUBLIC;

DO $$
DECLARE table_name TEXT;
BEGIN
    FOREACH table_name IN ARRAY ARRAY[
        'profile_systems', 'profile_articles',
        'glazing_bead_matrix', 'hardware_kits'
    ]
    LOOP
        EXECUTE format(
            'CREATE TRIGGER catalog_guard BEFORE INSERT OR UPDATE ON public.%I
             FOR EACH ROW EXECUTE FUNCTION private.guard_manual_catalog()',
            table_name
        );
    END LOOP;
END;
$$;

COMMIT;
