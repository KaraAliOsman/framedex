-- Existing data must not already hold an ambiguous effective role: the engine
-- resolves exactly one article per non-bead role for every viewer, and picking
-- a winner here would silently rewrite catalog authority.
DO $$
BEGIN
    IF EXISTS(
        SELECT 1
        FROM public.profile_articles AS existing
        JOIN public.profile_articles AS other
          ON other.system_id = existing.system_id
         AND other.role = existing.role
         AND other.id <> existing.id
         AND (existing.org_id IS NULL OR other.org_id IS NULL
              OR other.org_id = existing.org_id)
        WHERE existing.role IN ('FRAME','SASH','MULLION_V','MULLION_H',
                                'INVERSOR','COUPLER','ADDITIONAL','THRESHOLD')
    ) THEN
        RAISE EXCEPTION 'catalog_singleton_role_existing_conflict' USING ERRCODE = '23505';
    END IF;
END
$$;

CREATE UNIQUE INDEX uk_tenant_system_singleton_profile_role
ON public.profile_articles(system_id,org_id,role)
WHERE org_id IS NOT NULL
  AND role IN ('FRAME','SASH','MULLION_V','MULLION_H','INVERSOR','COUPLER','ADDITIONAL','THRESHOLD');

CREATE UNIQUE INDEX uk_global_system_singleton_profile_role
ON public.profile_articles(system_id,role)
WHERE org_id IS NULL
  AND role IN ('FRAME','SASH','MULLION_V','MULLION_H','INVERSOR','COUPLER','ADDITIONAL','THRESHOLD');

-- Partial indexes cannot express co-visibility: a global row is effective for
-- every tenant, so it also conflicts with tenant rows of the same role. The
-- trigger serializes writers per (system, role) and rejects any pair a single
-- viewer could resolve ambiguously, including direct table writes.
CREATE FUNCTION private.guard_singleton_profile_role() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path='' AS $$
BEGIN
    IF NEW.role IN ('FRAME','SASH','MULLION_V','MULLION_H','INVERSOR','COUPLER','ADDITIONAL','THRESHOLD') THEN
        PERFORM pg_advisory_xact_lock(hashtextextended(NEW.system_id::text || ':' || NEW.role::text, 0));
        IF EXISTS(
            SELECT 1
            FROM public.profile_articles AS other
            WHERE other.system_id = NEW.system_id
              AND other.role = NEW.role
              AND other.id IS DISTINCT FROM NEW.id
              AND (other.org_id IS NULL OR NEW.org_id IS NULL OR other.org_id = NEW.org_id)
        ) THEN
            RAISE EXCEPTION 'catalog_singleton_role_conflict' USING ERRCODE = '23505';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION private.guard_singleton_profile_role() FROM PUBLIC;

CREATE TRIGGER guard_singleton_profile_role
    BEFORE INSERT OR UPDATE ON public.profile_articles
    FOR EACH ROW EXECUTE FUNCTION private.guard_singleton_profile_role();
