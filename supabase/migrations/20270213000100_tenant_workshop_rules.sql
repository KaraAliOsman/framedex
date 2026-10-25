-- P12d · Workshop rules for a workshop's own series. Placement, handle and
-- reinforcement-cut policies and the fourteen inspector rules existed only for
-- the global reference families, so a series a workshop created could quote
-- but never reach the workshop. The owner now confirms them for their series
-- through catalog_backend: policies stay immutable and versioned (a change is
-- a new version), inspector rules are one row per rule and system.
BEGIN;

DO $$
DECLARE
    table_name TEXT;
BEGIN
    FOREACH table_name IN ARRAY ARRAY[
        'manufacturing_placement_policies',
        'handle_requirement_policies',
        'reinforcement_cut_policies'
    ] LOOP
        EXECUTE format(
            'CREATE POLICY %I ON public.%I FOR SELECT TO catalog_backend '
            'USING (org_id IS NULL OR org_id IN (SELECT private.current_user_org_ids()))',
            table_name || '_catalog_read', table_name);
        EXECUTE format(
            'CREATE POLICY %I ON public.%I FOR INSERT TO catalog_backend '
            'WITH CHECK (org_id IS NOT NULL AND private.can_manage_catalog(org_id) AND EXISTS ('
            'SELECT 1 FROM public.profile_systems s WHERE s.id = system_id AND s.org_id = %I.org_id))',
            table_name || '_catalog_insert', table_name, table_name);
        EXECUTE format('GRANT SELECT, INSERT ON public.%I TO catalog_backend', table_name);
    END LOOP;
END;
$$;

CREATE POLICY inspector_rule_configs_catalog_read ON public.inspector_rule_configs
    FOR SELECT TO catalog_backend
    USING (org_id IS NULL OR org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY inspector_rule_configs_catalog_insert ON public.inspector_rule_configs
    FOR INSERT TO catalog_backend
    WITH CHECK (org_id IS NOT NULL AND private.can_manage_catalog(org_id) AND EXISTS (
        SELECT 1 FROM public.profile_systems s
        WHERE s.id = inspector_rule_configs.system_id AND s.org_id = inspector_rule_configs.org_id));
CREATE POLICY inspector_rule_configs_catalog_update ON public.inspector_rule_configs
    FOR UPDATE TO catalog_backend
    USING (org_id IS NOT NULL AND private.can_manage_catalog(org_id))
    WITH CHECK (org_id IS NOT NULL AND private.can_manage_catalog(org_id) AND EXISTS (
        SELECT 1 FROM public.profile_systems s
        WHERE s.id = inspector_rule_configs.system_id AND s.org_id = inspector_rule_configs.org_id));
GRANT SELECT, INSERT, UPDATE ON public.inspector_rule_configs TO catalog_backend;

COMMIT;
