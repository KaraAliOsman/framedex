BEGIN;

-- Additive authorities: existing versions and sealed positions are untouched.
ALTER TABLE public.profile_systems ADD COLUMN opening_capabilities JSONB,
    ADD COLUMN paired_leaf_rule JSONB;
ALTER TABLE public.hardware_kits DROP CONSTRAINT chk_kits_opening_type;
ALTER TABLE public.hardware_kits ADD CONSTRAINT chk_kits_opening_type
    CHECK(opening_type IN ('AWNING','DOOR','SLIDING','TILT','TILT_TURN','TURN'));

CREATE FUNCTION private.guard_opening_authorities() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path='' AS $$
DECLARE cap JSONB; rule JSONB; hinge JSONB; field_name TEXT; signatures TEXT[] := '{}'; signature TEXT;
BEGIN
    IF NEW.paired_leaf_rule IS NOT NULL THEN
        rule := NEW.paired_leaf_rule;
        IF jsonb_typeof(rule) IS DISTINCT FROM 'object'
            OR rule - ARRAY['meeting_overlap_mm','meeting_gap_mm','inversor_end_deduction_mm','source'] <> '{}'
            OR jsonb_typeof(rule->'source') IS DISTINCT FROM 'string'
            OR length(btrim(coalesce(rule->>'source','')))=0 THEN
            RAISE EXCEPTION 'opening_meeting_rule_invalid' USING ERRCODE='23514';
        END IF;
        FOREACH field_name IN ARRAY ARRAY['meeting_overlap_mm','meeting_gap_mm','inversor_end_deduction_mm'] LOOP
            IF NOT private.catalog_exact(rule->field_name,0) THEN
                RAISE EXCEPTION 'opening_meeting_rule_exact_required' USING ERRCODE='23514';
            END IF;
        END LOOP;
    END IF;
    IF NEW.opening_capabilities IS NULL THEN RETURN NEW; END IF;
    IF jsonb_typeof(NEW.opening_capabilities) IS DISTINCT FROM 'array'
        OR jsonb_array_length(NEW.opening_capabilities)>100 THEN
        RAISE EXCEPTION 'opening_capabilities_invalid' USING ERRCODE='23514';
    END IF;
    FOR cap IN SELECT value FROM jsonb_array_elements(NEW.opening_capabilities) LOOP
        IF jsonb_typeof(cap) IS DISTINCT FROM 'object'
            OR cap - ARRAY['use','movement','direction','leaf_role','fixed_in_sash','hinge_sides','hardware_kit_skus','handle_rule','source'] <> '{}'
            OR coalesce(cap->>'use','') NOT IN ('WINDOW','DOOR')
            OR coalesce(cap->>'movement','') NOT IN ('FIXED','TURN','TILT','TILT_TURN','TOP_HUNG','SLIDE')
            OR coalesce(cap->>'direction','') NOT IN ('INWARD','OUTWARD')
            OR coalesce(cap->>'leaf_role','') NOT IN ('SINGLE','ACTIVE','PASSIVE')
            OR jsonb_typeof(cap->'fixed_in_sash') IS DISTINCT FROM 'boolean'
            OR jsonb_typeof(cap->'hinge_sides') IS DISTINCT FROM 'array'
            OR jsonb_typeof(cap->'hardware_kit_skus') IS DISTINCT FROM 'array'
            OR jsonb_typeof(cap->'source') IS DISTINCT FROM 'string'
            OR length(btrim(coalesce(cap->>'source','')))=0 THEN
            RAISE EXCEPTION 'opening_capability_invalid' USING ERRCODE='23514';
        END IF;
        IF NEW.system_family IS NULL OR (cap->>'use'='DOOR') IS DISTINCT FROM (NEW.system_family='DOOR')
            OR (cap->>'movement'='SLIDE' AND NEW.system_family<>'SLIDING')
            OR (cap->>'movement' NOT IN ('FIXED','SLIDE') AND NEW.system_family NOT IN ('CASEMENT','DOOR'))
            OR (cap->>'use'='DOOR' AND cap->>'movement' NOT IN ('FIXED','TURN')) THEN
            RAISE EXCEPTION 'opening_capability_family_incompatible' USING ERRCODE='23514';
        END IF;
        IF jsonb_array_length(cap->'hinge_sides') NOT BETWEEN 1 AND 2
            OR EXISTS(SELECT 1 FROM jsonb_array_elements(cap->'hinge_sides') h
                WHERE jsonb_typeof(h) IS DISTINCT FROM 'string')
            OR EXISTS(SELECT 1 FROM jsonb_array_elements(cap->'hardware_kit_skus') k
                WHERE jsonb_typeof(k) IS DISTINCT FROM 'string' OR length(btrim(k #>> '{}'))=0)
            OR (SELECT count(DISTINCT value) FROM jsonb_array_elements(cap->'hardware_kit_skus'))
                <> jsonb_array_length(cap->'hardware_kit_skus') THEN
            RAISE EXCEPTION 'opening_capability_members_invalid' USING ERRCODE='23514';
        END IF;
        FOR hinge IN SELECT value FROM jsonb_array_elements(cap->'hinge_sides') LOOP
            IF (cap->>'movement' IN ('FIXED','SLIDE') AND hinge #>> '{}' <> 'NONE')
                OR (cap->>'movement' IN ('TURN','TILT_TURN') AND hinge #>> '{}' NOT IN ('LEFT','RIGHT'))
                OR (cap->>'movement'='TILT' AND (hinge #>> '{}' <> 'BOTTOM' OR cap->>'direction'<>'INWARD'))
                OR (cap->>'movement'='TOP_HUNG' AND (hinge #>> '{}' <> 'TOP' OR cap->>'direction'<>'OUTWARD')) THEN
                RAISE EXCEPTION 'opening_capability_hinge_invalid' USING ERRCODE='23514';
            END IF;
            signature := (cap->>'use')||':'||(cap->>'movement')||':'||(cap->>'direction')||':'||
                (cap->>'leaf_role')||':'||(cap->>'fixed_in_sash')||':'||(hinge #>> '{}');
            IF signature=ANY(signatures) THEN
                RAISE EXCEPTION 'opening_capability_ambiguous' USING ERRCODE='23514';
            END IF;
            signatures := array_append(signatures,signature);
        END LOOP;
        IF (cap->>'fixed_in_sash'='true' AND cap->>'movement'<>'FIXED')
            OR (cap->>'movement' IN ('FIXED','SLIDE') AND cap->>'leaf_role'<>'SINGLE')
            OR (cap->>'movement'='FIXED' AND jsonb_array_length(cap->'hardware_kit_skus')<>0)
            OR (cap->>'movement'<>'FIXED' AND jsonb_array_length(cap->'hardware_kit_skus')=0)
            OR (cap->>'leaf_role' IN ('ACTIVE','PASSIVE') AND NEW.paired_leaf_rule IS NULL) THEN
            RAISE EXCEPTION 'opening_capability_hardware_required' USING ERRCODE='23514';
        END IF;
        rule := nullif(cap->'handle_rule','null');
        IF cap->>'movement'='FIXED' OR cap->>'leaf_role'='PASSIVE' THEN
            IF rule IS NOT NULL THEN RAISE EXCEPTION 'opening_capability_handle_forbidden' USING ERRCODE='23514'; END IF;
        ELSIF cap->>'movement'<>'SLIDE' AND rule IS NULL THEN
            RAISE EXCEPTION 'opening_capability_handle_required' USING ERRCODE='23514';
        END IF;
        IF rule IS NOT NULL THEN
            IF jsonb_typeof(rule) IS DISTINCT FROM 'object'
                OR rule - ARRAY['vertical_reference','default_height_mm','minimum_from_top_mm','minimum_from_bottom_mm','closing_edge_offset_mm','source'] <> '{}'
                OR coalesce(rule->>'vertical_reference','') NOT IN ('CENTER','LEAF_BOTTOM','LEAF_TOP')
                OR jsonb_typeof(rule->'source') IS DISTINCT FROM 'string'
                OR length(btrim(coalesce(rule->>'source','')))=0
                OR (rule->>'vertical_reference'<>'CENTER' AND NOT private.catalog_exact(rule->'default_height_mm',0))
                OR (nullif(rule->'default_height_mm','null') IS NOT NULL AND NOT private.catalog_exact(rule->'default_height_mm',0)) THEN
                RAISE EXCEPTION 'opening_handle_rule_invalid' USING ERRCODE='23514';
            END IF;
            FOREACH field_name IN ARRAY ARRAY['minimum_from_top_mm','minimum_from_bottom_mm','closing_edge_offset_mm'] LOOP
                IF NOT private.catalog_exact(rule->field_name,0) THEN
                    RAISE EXCEPTION 'opening_handle_rule_exact_required' USING ERRCODE='23514';
                END IF;
            END LOOP;
        END IF;
    END LOOP;
    RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION private.guard_opening_authorities() FROM PUBLIC;
CREATE TRIGGER guard_opening_authorities BEFORE INSERT OR UPDATE ON public.profile_systems
    FOR EACH ROW EXECUTE FUNCTION private.guard_opening_authorities();

-- Deferred binding lets a reviewed import create the system and its kits in
-- one transaction, while rejecting foreign/missing/deactivated kit authority.
CREATE FUNCTION private.check_opening_catalog_bindings() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path='' AS $$
DECLARE target UUID; targets UUID[]; system_row public.profile_systems%ROWTYPE; cap JSONB; kit_sku TEXT; expected_type TEXT;
BEGIN
    IF TG_TABLE_NAME='profile_systems' THEN targets := ARRAY[NEW.id];
    ELSIF TG_OP='UPDATE' THEN targets := ARRAY[OLD.system_id,NEW.system_id];
    ELSE targets := ARRAY[CASE WHEN TG_OP='DELETE' THEN OLD.system_id ELSE NEW.system_id END]; END IF;
    FOREACH target IN ARRAY targets LOOP
    SELECT * INTO system_row FROM public.profile_systems WHERE id=target;
    IF NOT FOUND OR NOT system_row.is_active OR system_row.opening_capabilities IS NULL THEN CONTINUE; END IF;
    FOR cap IN SELECT value FROM jsonb_array_elements(system_row.opening_capabilities) LOOP
        expected_type := CASE WHEN cap->>'use'='DOOR' THEN 'DOOR'
            WHEN cap->>'movement'='TOP_HUNG' THEN 'AWNING'
            WHEN cap->>'movement'='SLIDE' THEN 'SLIDING' ELSE cap->>'movement' END;
        FOR kit_sku IN SELECT jsonb_array_elements_text(cap->'hardware_kit_skus') LOOP
            IF NOT EXISTS(SELECT 1 FROM public.hardware_kits k WHERE k.system_id=target
                AND k.org_id IS NOT DISTINCT FROM system_row.org_id AND k.sku=kit_sku AND k.is_active
                AND k.opening_type=expected_type
                AND (cap->>'leaf_role'<>'PASSIVE' OR NOT EXISTS(SELECT 1 FROM jsonb_array_elements(k.contents) c
                    WHERE c->>'category'='HANDLE'))) THEN
                RAISE EXCEPTION 'opening_capability_kit_incompatible' USING ERRCODE='23514';
            END IF;
        END LOOP;
        IF cap->>'leaf_role' IN ('ACTIVE','PASSIVE') AND NOT EXISTS(SELECT 1 FROM public.profile_articles a
            WHERE a.system_id=target AND a.org_id IS NOT DISTINCT FROM system_row.org_id AND a.role='INVERSOR') THEN
            RAISE EXCEPTION 'opening_inversor_authority_required' USING ERRCODE='23514';
        END IF;
    END LOOP;
    END LOOP;
    RETURN NULL;
END $$;
REVOKE ALL ON FUNCTION private.check_opening_catalog_bindings() FROM PUBLIC;
CREATE CONSTRAINT TRIGGER check_opening_system_bindings AFTER INSERT OR UPDATE ON public.profile_systems
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION private.check_opening_catalog_bindings();
CREATE CONSTRAINT TRIGGER check_opening_kit_bindings AFTER INSERT OR UPDATE OR DELETE ON public.hardware_kits
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION private.check_opening_catalog_bindings();
CREATE CONSTRAINT TRIGGER check_opening_profile_bindings AFTER INSERT OR UPDATE OR DELETE ON public.profile_articles
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION private.check_opening_catalog_bindings();

GRANT SELECT(opening_capabilities,paired_leaf_rule) ON public.profile_systems
    TO authenticated,catalog_backend,pricing_backend,documentary_backend;
GRANT INSERT(opening_capabilities,paired_leaf_rule),UPDATE(opening_capabilities,paired_leaf_rule)
    ON public.profile_systems TO catalog_backend;
-- The existing clearance guard reads inspector authority on system updates.
-- Catalog writes need that read under the same tenant predicate, never writes.
ALTER POLICY inspector_rule_configs_select ON public.inspector_rule_configs
    TO authenticated,catalog_backend;
GRANT SELECT ON public.inspector_rule_configs TO catalog_backend;
COMMIT;
