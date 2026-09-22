-- COUPLER becomes a multi-valued catalog role: an assembly references any
-- coupler SKU the system offers (straight, angled, structural), resolved
-- through load_coupler_articles rather than the one-article-per-role map.
-- All other roles keep their singleton guarantees unchanged.

DROP INDEX uk_tenant_system_singleton_profile_role;
DROP INDEX uk_global_system_singleton_profile_role;

CREATE UNIQUE INDEX uk_tenant_system_singleton_profile_role
ON public.profile_articles(system_id,org_id,role)
WHERE org_id IS NOT NULL
  AND role IN ('FRAME','SASH','MULLION_V','MULLION_H','INVERSOR','ADDITIONAL','THRESHOLD');

CREATE UNIQUE INDEX uk_global_system_singleton_profile_role
ON public.profile_articles(system_id,role)
WHERE org_id IS NULL
  AND role IN ('FRAME','SASH','MULLION_V','MULLION_H','INVERSOR','ADDITIONAL','THRESHOLD');

CREATE OR REPLACE FUNCTION private.guard_singleton_profile_role() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path='' AS $$
BEGIN
    IF NEW.role IN ('FRAME','SASH','MULLION_V','MULLION_H','INVERSOR','ADDITIONAL','THRESHOLD') THEN
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
