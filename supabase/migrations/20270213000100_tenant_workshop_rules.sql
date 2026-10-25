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

-- Inspector rules keep their narrow write path: catalog_backend still has no
-- table write privilege. The owner's confirmation goes through one function
-- that checks catalog authority and ownership; the freeze guard still runs.
CREATE FUNCTION private.declare_inspector_rule(p_system uuid, p_org uuid, p_rule text, p_params jsonb)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$ BEGIN
 IF p_org IS NULL OR NOT private.can_manage_catalog(p_org) OR NOT EXISTS(
     SELECT 1 FROM public.profile_systems WHERE id=p_system AND org_id=p_org) THEN
  RAISE EXCEPTION 'inspector_rule_denied' USING ERRCODE='42501';
 END IF;
 IF EXISTS(SELECT 1 FROM public.inspector_rule_configs WHERE system_id=p_system AND org_id=p_org AND rule_id=p_rule) THEN
  UPDATE public.inspector_rule_configs SET params=p_params,is_active=TRUE,updated_at=clock_timestamp()
   WHERE system_id=p_system AND org_id=p_org AND rule_id=p_rule;
 ELSE
  INSERT INTO public.inspector_rule_configs(system_id,org_id,rule_id,params) VALUES(p_system,p_org,p_rule,p_params);
 END IF;
END $$;
REVOKE ALL ON FUNCTION private.declare_inspector_rule(uuid,uuid,text,jsonb) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.declare_inspector_rule(uuid,uuid,text,jsonb) TO catalog_backend;

-- A series already used in a work may still receive the workshop facts it
-- never had. Declaring the chamber clearance where it was NULL changes no
-- computed number (the inspector refused the series without it); changing a
-- declared clearance, or any other technical column, stays frozen.
CREATE OR REPLACE FUNCTION private.guard_referenced_system() RETURNS TRIGGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
DECLARE
    audit CONSTANT TEXT[] := '{data_provenance,technical_reviewed_at,technical_reviewed_by,review_pending}';
BEGIN
    IF TG_OP='DELETE' AND OLD.org_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM public.tenancy_organizations WHERE id=OLD.org_id
    ) THEN RETURN OLD; END IF;
    IF OLD.technical_locked AND (TG_OP='DELETE' OR (
        to_jsonb(NEW) - audit - 'chamber_clearance_mm' IS DISTINCT FROM to_jsonb(OLD) - audit - 'chamber_clearance_mm'
        OR (OLD.chamber_clearance_mm IS NOT NULL
            AND NEW.chamber_clearance_mm IS DISTINCT FROM OLD.chamber_clearance_mm))) THEN
        RAISE EXCEPTION 'catalog_authority_referenced' USING ERRCODE='23514';
    END IF;
    RETURN CASE WHEN TG_OP='DELETE' THEN OLD ELSE NEW END;
END;
$$;
REVOKE ALL ON FUNCTION private.guard_referenced_system() FROM PUBLIC;

CREATE OR REPLACE FUNCTION private.guard_referenced_catalog() RETURNS TRIGGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
DECLARE
    payload JSONB;
    target UUID;
    locked BOOLEAN;
BEGIN
    -- A new tenant-only SKU on a global series is additive: no existing
    -- immutable mapping or sealed recipe is superseded. Reusing a SKU or
    -- changing any existing authority still follows the original freeze gate.
    IF TG_OP='INSERT' AND TG_TABLE_NAME='glass_purchase_mappings' THEN
        PERFORM pg_advisory_xact_lock(hashtextextended(NEW.system_id::TEXT||':'||NEW.technical_sku,0));
        IF NEW.org_id IS NOT NULL AND EXISTS(SELECT 1 FROM public.profile_systems
            WHERE id=NEW.system_id AND org_id IS NULL AND is_global)
            AND NOT EXISTS(SELECT 1 FROM public.glass_purchase_mappings
                WHERE system_id=NEW.system_id AND technical_sku=NEW.technical_sku
                AND (org_id=NEW.org_id OR org_id IS NULL)) THEN
            RETURN NEW;
        END IF;
    END IF;
    -- The first declaration of an inspector rule a series never had fills an
    -- honest unknown: the inspector refused every position of that series, so
    -- no sealed result depended on it. Changing a declared rule stays frozen.
    IF TG_OP='INSERT' AND TG_TABLE_NAME='inspector_rule_configs' AND NEW.org_id IS NOT NULL THEN
        PERFORM pg_advisory_xact_lock(hashtextextended(NEW.system_id::TEXT||':inspector:'||NEW.rule_id,0));
        IF NOT EXISTS(SELECT 1 FROM public.inspector_rule_configs
            WHERE system_id=NEW.system_id AND rule_id=NEW.rule_id
            AND (org_id=NEW.org_id OR org_id IS NULL)) THEN
            RETURN NEW;
        END IF;
    END IF;
    IF TG_OP='DELETE' AND OLD.org_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM public.tenancy_organizations WHERE id=OLD.org_id
    ) THEN RETURN OLD; END IF;
    FOR payload IN SELECT value FROM jsonb_array_elements(
        CASE WHEN TG_OP='INSERT' THEN jsonb_build_array(to_jsonb(NEW))
             WHEN TG_OP='DELETE' THEN jsonb_build_array(to_jsonb(OLD))
             ELSE jsonb_build_array(to_jsonb(OLD),to_jsonb(NEW)) END
    ) LOOP
        -- Provenance-only edits to locked rows are audit writes, not technical
        -- edits: let review and re-labeling through, keep everything else frozen.
        -- review_pending rides the same exemption: it changes only as part of
        -- a technical edit or a review write.
        IF TG_OP='UPDATE' AND
            to_jsonb(NEW) - '{data_provenance,technical_reviewed_at,technical_reviewed_by,review_pending}'::TEXT[]
            IS NOT DISTINCT FROM
            to_jsonb(OLD) - '{data_provenance,technical_reviewed_at,technical_reviewed_by,review_pending}'::TEXT[]
        THEN CONTINUE; END IF;
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

-- Saving the first window of a work locks its series (technical_locked), and
-- declaring the chamber clearance fills a workshop fact; neither changes the
-- geometry a test window verified. Only technical edits invalidate it now —
-- before, every series lost its verification the moment it was first used.
CREATE OR REPLACE FUNCTION private.invalidate_catalog_series_verification() RETURNS TRIGGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE data JSONB; system UUID;
    unrelated CONSTANT TEXT[] := ARRAY['technical_reviewed_at','technical_reviewed_by','review_pending',
        'data_provenance','technical_locked','chamber_clearance_mm'];
BEGIN
    IF TG_OP='UPDATE' AND to_jsonb(NEW)-unrelated IS NOT DISTINCT FROM to_jsonb(OLD)-unrelated THEN
        RETURN NEW;
    END IF;
    data:=CASE WHEN TG_OP='DELETE' THEN to_jsonb(OLD) ELSE to_jsonb(NEW) END;
    system:=(CASE WHEN TG_TABLE_NAME='profile_systems' THEN data->>'id' ELSE data->>'system_id' END)::uuid;
    UPDATE public.catalog_series_setup SET verified_at=NULL,verified_by=NULL,verified_hash=NULL
        WHERE system_id=system AND org_id=(data->>'org_id')::uuid AND verified_at IS NOT NULL;
    IF TG_OP='DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION private.invalidate_catalog_series_verification() FROM PUBLIC;

COMMIT;
