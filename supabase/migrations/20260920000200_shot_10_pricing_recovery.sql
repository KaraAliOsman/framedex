-- An explicit, audited draft reset retires live pricing without rewriting operations.
ALTER TABLE public.projects ADD COLUMN pricing_reset_at TIMESTAMPTZ;

CREATE FUNCTION private.guard_pricing_reset() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path='' AS $$
BEGIN
    IF (TG_OP='INSERT' AND NEW.pricing_reset_at IS NOT NULL) OR
       (TG_OP='UPDATE' AND NEW.pricing_reset_at IS DISTINCT FROM OLD.pricing_reset_at) THEN
        IF current_setting('role') <> 'pricing_backend' OR NEW.status <> 'DRAFT' THEN
            RAISE EXCEPTION 'pricing_service_required' USING ERRCODE='42501';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION private.guard_pricing_reset() FROM PUBLIC;
CREATE TRIGGER guard_pricing_reset BEFORE INSERT OR UPDATE ON public.projects
FOR EACH ROW EXECUTE FUNCTION private.guard_pricing_reset();

CREATE OR REPLACE FUNCTION private.project_has_applied_commercial_state(target_project UUID)
RETURNS BOOLEAN LANGUAGE sql STABLE SECURITY DEFINER SET search_path='' AS $$
  SELECT EXISTS(SELECT 1 FROM public.projects project WHERE project.id=target_project AND (
    project.total_cost_net <> 0 OR project.total_price_net <> 0
    OR project.total_price_tax <> 0 OR project.total_price_gross <> 0
    OR EXISTS(SELECT 1 FROM public.project_positions position WHERE position.project_id=project.id
      AND (position.cost_net <> 0 OR position.price_net <> 0 OR position.discount_pct <> 0))
    OR EXISTS(SELECT 1 FROM public.pricing_operations operation WHERE operation.project_id=project.id
      AND operation.state='APPLIED' AND COALESCE(operation.revision_code,'REV-A')=project.current_revision
      AND (project.pricing_reset_at IS NULL OR operation.approved_at > project.pricing_reset_at))
  ));
$$;
REVOKE ALL ON FUNCTION private.project_has_applied_commercial_state(UUID) FROM PUBLIC;

CREATE OR REPLACE FUNCTION private.require_applied_pricing_authority()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    IF NEW.authority_version NOT IN ('SHOT09_V1', 'SHOT10_V1') THEN
        RAISE EXCEPTION 'legacy_version_insert_forbidden' USING ERRCODE = '23514';
    END IF;
    IF NOT EXISTS (
        SELECT 1
        FROM public.pricing_operations
        WHERE id = NEW.pricing_operation_id
          AND project_id = NEW.project_id
          AND org_id = NEW.org_id
          AND state = 'APPLIED'
          AND ((SELECT pricing_reset_at FROM public.projects WHERE id=NEW.project_id) IS NULL
               OR approved_at > (SELECT pricing_reset_at FROM public.projects WHERE id=NEW.project_id))
          AND COALESCE(revision_code, 'REV-A') = NEW.revision_code
    ) THEN
        RAISE EXCEPTION 'applied_pricing_authority_required' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;
