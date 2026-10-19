-- Commercial numbering under the documentary role (v1 06).
--
-- 20270130000300 granted documentary_backend UPDATE(commercial_number) on
-- projects so `documents.numbering.assign_commercial_number` can give a work
-- its quotation number when the first issuable preview is prepared, but
-- private.guard_commercial_write still refused every documentary project
-- write except the production release (documentary_project_update_forbidden).
--
-- This redefines the guard with one more sanctioned write, bounded like the
-- release: commercial_number NULL → value, nothing else changed. Every other
-- branch is the definition from 20261226000000 unchanged.

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
    IF current_setting('role') = 'documentary_backend'
       AND TG_TABLE_NAME = 'projects' THEN
        -- Commercial numbering: the work receives its quotation number once
        -- (NULL → N) when its first issuable preview is prepared; no other
        -- column moves and an assigned number is never rewritten.
        IF TG_OP = 'UPDATE'
           AND OLD.commercial_number IS NULL
           AND NEW.commercial_number IS NOT NULL
           AND (to_jsonb(NEW) - ARRAY['commercial_number', 'updated_at'])
               = (to_jsonb(OLD) - ARRAY['commercial_number', 'updated_at']) THEN
            RETURN NEW;
        END IF;
        -- Production release: the only project write the documentary role may
        -- perform — status QUOTED|APPROVED → IN_PRODUCTION, no other column.
        IF TG_OP = 'UPDATE'
           AND (to_jsonb(NEW) - ARRAY['status', 'updated_at'])
               = (to_jsonb(OLD) - ARRAY['status', 'updated_at'])
           AND OLD.status IN ('QUOTED', 'APPROVED')
           AND NEW.status = 'IN_PRODUCTION' THEN
            RETURN NEW;
        END IF;
        RAISE EXCEPTION 'documentary_project_update_forbidden' USING ERRCODE = '42501';
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
