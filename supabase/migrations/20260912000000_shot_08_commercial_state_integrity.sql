BEGIN;

CREATE FUNCTION private.project_has_applied_commercial_state(target_project UUID)
RETURNS BOOLEAN
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = '' AS $$
  SELECT EXISTS(
    SELECT 1
    FROM public.projects AS project
    WHERE project.id = target_project
      AND (
        project.total_cost_net <> 0 OR project.total_price_net <> 0
        OR project.total_price_tax <> 0 OR project.total_price_gross <> 0
        OR EXISTS(
          SELECT 1 FROM public.project_positions AS position
          WHERE position.project_id = project.id
            AND (position.cost_net <> 0 OR position.price_net <> 0
              OR position.discount_pct <> 0)
        )
        OR EXISTS(
          SELECT 1 FROM public.pricing_operations AS operation
          WHERE operation.project_id = project.id AND operation.state = 'APPLIED'
        )
      )
  );
$$;
REVOKE ALL ON FUNCTION private.project_has_applied_commercial_state(UUID) FROM PUBLIC;

CREATE OR REPLACE FUNCTION private.guard_commercial_write() RETURNS TRIGGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
DECLARE
  project_is_priced BOOLEAN;
BEGIN
  IF current_setting('role') = 'pricing_backend' THEN
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
  END IF;
  IF TG_OP = 'DELETE' THEN
    IF (session_user IN ('postgres', 'supabase_admin') OR
        (session_user = 'authenticator' AND current_setting('role') = 'service_role'))
       AND auth.uid() IS NULL AND pg_trigger_depth() > 1
       AND NOT EXISTS(SELECT 1 FROM public.tenancy_organizations WHERE id = OLD.org_id)
       THEN RETURN OLD; END IF;
  END IF;
  IF TG_TABLE_NAME = 'project_positions' THEN
    IF TG_OP = 'INSERT' THEN
      project_is_priced := private.project_has_applied_commercial_state(NEW.project_id);
      IF NEW.cost_net <> 0 OR NEW.price_net <> 0 OR NEW.discount_pct <> 0
         OR project_is_priced THEN
        RAISE EXCEPTION 'pricing_service_required' USING ERRCODE = '42501';
      END IF;
    ELSIF TG_OP = 'UPDATE' THEN
      project_is_priced := private.project_has_applied_commercial_state(OLD.project_id)
        OR (NEW.project_id IS DISTINCT FROM OLD.project_id
            AND private.project_has_applied_commercial_state(NEW.project_id));
      IF (NEW.cost_net, NEW.price_net, NEW.discount_pct)
           IS DISTINCT FROM (OLD.cost_net, OLD.price_net, OLD.discount_pct)
         OR project_is_priced THEN
        RAISE EXCEPTION 'pricing_service_required' USING ERRCODE = '42501';
      END IF;
    ELSE
      project_is_priced := private.project_has_applied_commercial_state(OLD.project_id);
      IF OLD.cost_net <> 0 OR OLD.price_net <> 0 OR OLD.discount_pct <> 0
         OR project_is_priced THEN
        RAISE EXCEPTION 'pricing_service_required' USING ERRCODE = '42501';
      END IF;
      RETURN OLD;
    END IF;
  ELSE
    IF TG_OP = 'INSERT' THEN
      IF NEW.total_cost_net <> 0 OR NEW.total_price_net <> 0
         OR NEW.total_price_tax <> 0 OR NEW.total_price_gross <> 0 THEN
        RAISE EXCEPTION 'pricing_service_required' USING ERRCODE = '42501';
      END IF;
    ELSIF TG_OP = 'UPDATE' THEN
      project_is_priced := private.project_has_applied_commercial_state(OLD.id);
      IF (NEW.total_cost_net, NEW.total_price_net, NEW.total_price_tax, NEW.total_price_gross)
           IS DISTINCT FROM (OLD.total_cost_net, OLD.total_price_net,
                             OLD.total_price_tax, OLD.total_price_gross)
         OR project_is_priced THEN
        RAISE EXCEPTION 'pricing_service_required' USING ERRCODE = '42501';
      END IF;
    ELSE
      project_is_priced := private.project_has_applied_commercial_state(OLD.id);
      IF project_is_priced THEN
        RAISE EXCEPTION 'pricing_service_required' USING ERRCODE = '42501';
      END IF;
      RETURN OLD;
    END IF;
  END IF;
  RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION private.guard_commercial_write() FROM PUBLIC;

DROP TRIGGER guard_commercial_write ON public.projects;
CREATE TRIGGER guard_commercial_write BEFORE INSERT OR UPDATE OR DELETE ON public.projects
FOR EACH ROW EXECUTE FUNCTION private.guard_commercial_write();
DROP TRIGGER guard_commercial_write ON public.project_positions;
CREATE TRIGGER guard_commercial_write BEFORE INSERT OR UPDATE OR DELETE ON public.project_positions
FOR EACH ROW EXECUTE FUNCTION private.guard_commercial_write();

COMMIT;
