BEGIN;

ALTER TABLE public.pricing_operations
    ADD COLUMN revision_code TEXT CHECK (
        revision_code IS NULL OR revision_code ~ '^REV-[A-Z]+$'
    );
CREATE INDEX pricing_operations_project_revision_state_idx
    ON public.pricing_operations(project_id, revision_code, state);

CREATE OR REPLACE FUNCTION private.project_has_applied_commercial_state(target_project UUID)
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
          WHERE operation.project_id = project.id
            AND operation.state = 'APPLIED'
            AND COALESCE(operation.revision_code, 'REV-A') = project.current_revision
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
    IF current_setting('role') = 'documentary_backend'
       AND TG_TABLE_NAME = 'project_positions' THEN
        IF TG_OP = 'UPDATE'
           AND (to_jsonb(NEW) - ARRAY['location_tag', 'updated_at'])
               = (to_jsonb(OLD) - ARRAY['location_tag', 'updated_at'])
           AND NOT EXISTS (
               SELECT 1
               FROM public.projects project
               JOIN public.project_versions version
                 ON version.project_id = project.id
                AND version.revision_code = project.current_revision
               WHERE project.id = OLD.project_id
           ) THEN
            RETURN NEW;
        END IF;
        RAISE EXCEPTION 'documentary_position_update_forbidden' USING ERRCODE = '42501';
    END IF;
    IF TG_OP = 'DELETE' THEN
        IF (session_user IN ('postgres', 'supabase_admin') OR
            (session_user = 'authenticator' AND current_setting('role') = 'service_role'))
           AND auth.uid() IS NULL AND pg_trigger_depth() > 1
           AND NOT EXISTS (
               SELECT 1 FROM public.tenancy_organizations WHERE id = OLD.org_id
           ) THEN
            RETURN OLD;
        END IF;
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
            IF (NEW.total_cost_net, NEW.total_price_net,
                NEW.total_price_tax, NEW.total_price_gross)
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
END;
$$;
REVOKE ALL ON FUNCTION private.guard_commercial_write() FROM PUBLIC;

CREATE OR REPLACE FUNCTION private.guard_documentary_input_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
    IF (TG_OP <> 'INSERT' AND EXISTS (
        SELECT 1
        FROM public.projects project
        JOIN public.project_versions version
          ON version.project_id = project.id
         AND version.revision_code = project.current_revision
        WHERE project.id = OLD.project_id
    )) OR (TG_OP <> 'DELETE' AND EXISTS (
        SELECT 1
        FROM public.projects project
        JOIN public.project_versions version
          ON version.project_id = project.id
         AND version.revision_code = project.current_revision
        WHERE project.id = NEW.project_id
    )) THEN
        RAISE EXCEPTION 'sealed_documentary_inputs_immutable' USING ERRCODE = '42501';
    END IF;
    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END;
$$;
REVOKE ALL ON FUNCTION private.guard_documentary_input_mutation() FROM PUBLIC;

ALTER TABLE public.purchase_projections
    DROP CONSTRAINT IF EXISTS purchase_projections_projection_hash_key;

ALTER TABLE public.project_versions
    DROP CONSTRAINT project_versions_authority_kind,
    DROP CONSTRAINT project_versions_initial_revision,
    DROP CONSTRAINT project_versions_v1_authority,
    ALTER COLUMN authority_version SET DEFAULT 'SHOT10_V1',
    ADD CONSTRAINT project_versions_authority_kind
        CHECK (authority_version IN ('PRE_SHOT09', 'SHOT09_V1', 'SHOT10_V1')),
    ADD CONSTRAINT project_versions_initial_revision
        CHECK (authority_version <> 'SHOT09_V1' OR revision_code = 'REV-A'),
    ADD CONSTRAINT project_versions_v1_authority
        CHECK (authority_version NOT IN ('SHOT09_V1', 'SHOT10_V1') OR (
            pricing_operation_id IS NOT NULL
            AND canonical_version = 'DOCUMENTARY_CANONICAL_V1'
            AND bom_hash IS NOT NULL
            AND snapshot_sha256 IS NOT NULL
            AND production_allowed IS NOT NULL
            AND documentary_complete IS NOT NULL
        ));

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
          AND COALESCE(revision_code, 'REV-A') = NEW.revision_code
    ) THEN
        RAISE EXCEPTION 'applied_pricing_authority_required' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION private.require_applied_pricing_authority() FROM PUBLIC;

CREATE FUNCTION private.guard_project_revision_state()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
    IF (NEW.status, NEW.current_revision) IS DISTINCT FROM (OLD.status, OLD.current_revision)
       AND current_setting('role') <> 'pricing_backend' THEN
        RAISE EXCEPTION 'project_revision_service_required' USING ERRCODE = '42501';
    END IF;
    RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION private.guard_project_revision_state() FROM PUBLIC;
CREATE TRIGGER guard_project_revision_state
BEFORE UPDATE OF status, current_revision ON public.projects
FOR EACH ROW EXECUTE FUNCTION private.guard_project_revision_state();

COMMIT;
