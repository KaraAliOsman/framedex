-- A catalog becomes immutable when first referenced by persisted technical work.
-- The monotonic row marker also fences concurrent catalog writes at REPEATABLE READ.
ALTER TABLE public.profile_systems ADD COLUMN technical_locked BOOLEAN NOT NULL DEFAULT FALSE;
UPDATE public.profile_systems system SET technical_locked=TRUE
WHERE EXISTS (SELECT 1 FROM public.project_positions position WHERE position.system_id=system.id);

CREATE FUNCTION private.guard_referenced_system() RETURNS TRIGGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN
    IF TG_OP='DELETE' AND OLD.org_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM public.tenancy_organizations WHERE id=OLD.org_id
    ) THEN RETURN OLD; END IF;
    IF OLD.technical_locked AND (TG_OP='DELETE' OR to_jsonb(NEW) IS DISTINCT FROM to_jsonb(OLD)) THEN
        RAISE EXCEPTION 'catalog_authority_referenced' USING ERRCODE='23514';
    END IF;
    RETURN CASE WHEN TG_OP='DELETE' THEN OLD ELSE NEW END;
END;
$$;
REVOKE ALL ON FUNCTION private.guard_referenced_system() FROM PUBLIC;
CREATE TRIGGER guard_referenced_system BEFORE UPDATE OR DELETE ON public.profile_systems
FOR EACH ROW EXECUTE FUNCTION private.guard_referenced_system();

CREATE FUNCTION private.lock_position_catalog() RETURNS TRIGGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN
    UPDATE public.profile_systems SET technical_locked=TRUE WHERE id=NEW.system_id;
    RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION private.lock_position_catalog() FROM PUBLIC;
CREATE TRIGGER lock_position_catalog BEFORE INSERT OR UPDATE OF system_id ON public.project_positions
FOR EACH ROW EXECUTE FUNCTION private.lock_position_catalog();

CREATE FUNCTION private.reserve_catalog_authority(target UUID, tenant UUID) RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM public.tenancy_memberships
        WHERE org_id=tenant AND user_id=auth.uid() AND is_active
          AND (role='ESTIMATOR' OR (role='OWNER' AND auth.jwt()->>'aal'='aal2'))
    ) OR NOT EXISTS (
        SELECT 1 FROM public.profile_systems WHERE id=target AND is_active
        AND (org_id=tenant OR (org_id IS NULL AND is_global))
    ) THEN
        RAISE EXCEPTION 'catalog_not_found' USING ERRCODE='42501';
    END IF;
    UPDATE public.profile_systems SET technical_locked=TRUE WHERE id=target;
END;
$$;
REVOKE ALL ON FUNCTION private.reserve_catalog_authority(UUID,UUID) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.reserve_catalog_authority(UUID,UUID) TO authenticated,pricing_backend;

CREATE FUNCTION private.guard_referenced_catalog() RETURNS TRIGGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
DECLARE
    payload JSONB;
    target UUID;
    locked BOOLEAN;
BEGIN
    IF TG_OP='DELETE' AND OLD.org_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM public.tenancy_organizations WHERE id=OLD.org_id
    ) THEN RETURN OLD; END IF;
    FOR payload IN SELECT value FROM jsonb_array_elements(
        CASE WHEN TG_OP='INSERT' THEN jsonb_build_array(to_jsonb(NEW))
             WHEN TG_OP='DELETE' THEN jsonb_build_array(to_jsonb(OLD))
             ELSE jsonb_build_array(to_jsonb(OLD),to_jsonb(NEW)) END
    ) LOOP
        IF TG_TABLE_NAME='profile_purchase_mappings' THEN
            SELECT system_id INTO target FROM public.profile_articles
            WHERE id=(payload->>'profile_article_id')::UUID;
        ELSIF TG_TABLE_NAME='hardware_purchase_mappings' THEN
            SELECT system_id INTO target FROM public.hardware_kits
            WHERE id=(payload->>'hardware_kit_id')::UUID;
        ELSIF TG_TABLE_NAME='panel_purchase_authorities' THEN
            SELECT system_id INTO target FROM public.infill_articles
            WHERE id=(payload->>'infill_article_id')::UUID;
        ELSE
            target := (payload->>'system_id')::UUID;
        END IF;
        -- A real UPDATE creates a conflicting row version, including for unlocked
        -- catalogs: a concurrent save cannot commit calculations from an old snapshot.
        UPDATE public.profile_systems SET technical_locked=technical_locked
        WHERE id=target RETURNING technical_locked INTO locked;
        IF locked THEN
            RAISE EXCEPTION 'catalog_authority_referenced' USING ERRCODE='23514';
        END IF;
    END LOOP;
    RETURN CASE WHEN TG_OP='DELETE' THEN OLD ELSE NEW END;
END;
$$;
REVOKE ALL ON FUNCTION private.guard_referenced_catalog() FROM PUBLIC;
DO $$ DECLARE item TEXT; BEGIN
    FOREACH item IN ARRAY ARRAY['profile_articles','glazing_bead_matrix','hardware_kits',
        'infill_articles','profile_purchase_mappings','reinforcement_articles',
        'inspector_rule_configs','glass_purchase_mappings','hardware_purchase_mappings',
        'panel_purchase_authorities'] LOOP
        EXECUTE format('CREATE TRIGGER guard_referenced_catalog BEFORE INSERT OR UPDATE OR DELETE ON public.%I FOR EACH ROW EXECUTE FUNCTION private.guard_referenced_catalog()',item);
    END LOOP;
END $$;

CREATE FUNCTION private.guard_referenced_cutting_profile() RETURNS TRIGGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE target UUID; locked BOOLEAN;
BEGIN
    FOR target IN
        SELECT DISTINCT system_id FROM (
            SELECT article.system_id FROM public.profile_purchase_mappings mapping
            JOIN public.profile_articles article ON article.id=mapping.profile_article_id
            WHERE mapping.cutting_profile_id=OLD.id
            UNION SELECT system_id FROM public.reinforcement_articles WHERE cutting_profile_id=OLD.id
        ) sources ORDER BY system_id
    LOOP
        UPDATE public.profile_systems SET technical_locked=technical_locked
        WHERE id=target RETURNING technical_locked INTO locked;
        IF locked THEN RAISE EXCEPTION 'catalog_authority_referenced' USING ERRCODE='23514'; END IF;
    END LOOP;
    RETURN CASE WHEN TG_OP='DELETE' THEN OLD ELSE NEW END;
END;
$$;
REVOKE ALL ON FUNCTION private.guard_referenced_cutting_profile() FROM PUBLIC;
CREATE TRIGGER guard_referenced_cutting_profile BEFORE UPDATE OR DELETE ON public.cutting_profiles
FOR EACH ROW EXECUTE FUNCTION private.guard_referenced_cutting_profile();
