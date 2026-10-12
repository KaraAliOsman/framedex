-- Keep the commercial read permission identical, evaluate membership once per
-- statement instead of once per cost row. Writes retain their existing gates.
BEGIN;

CREATE FUNCTION private.pricing_read_org_ids() RETURNS SETOF uuid
LANGUAGE sql STABLE SECURITY DEFINER SET search_path='' AS $$
 SELECT m.org_id FROM public.tenancy_memberships m
 WHERE m.user_id=auth.uid() AND m.is_active
   AND m.role::text=ANY(ARRAY['OWNER','ESTIMATOR','WORKSHOP_MANAGER'])
   AND m.org_id IN(SELECT private.current_user_org_ids());
$$;
REVOKE ALL ON FUNCTION private.pricing_read_org_ids() FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION private.pricing_read_org_ids() TO pricing_backend;

DO $$
DECLARE table_name text;
BEGIN
 FOREACH table_name IN ARRAY ARRAY['cost_lists','cost_list_items','pricing_rules',
   'pricing_configurations','pricing_matrix_cells','pricing_fx_snapshots','pricing_operations'] LOOP
  EXECUTE format('DROP POLICY pricing_backend_read ON public.%I',table_name);
  EXECUTE format('CREATE POLICY pricing_backend_read ON public.%I FOR SELECT TO pricing_backend
    USING(org_id IN(SELECT private.pricing_read_org_ids()))',table_name);
 END LOOP;
END $$;

COMMIT;
