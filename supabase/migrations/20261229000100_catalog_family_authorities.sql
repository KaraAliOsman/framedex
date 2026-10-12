BEGIN;

GRANT USAGE ON SCHEMA private TO catalog_backend;

-- Existing referenced catalogs remain byte-for-byte technical authorities.
-- The legacy marker is platform-owned: it cannot be submitted by a tenant.
ALTER TABLE public.profile_systems
    ADD COLUMN legacy_authority BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN system_family VARCHAR(20)
        CHECK (system_family IN ('CASEMENT','SLIDING','LIFT_SLIDE','DOOR','FACADE_FIXED')),
    ADD COLUMN sliding_parameters JSONB,
    ADD COLUMN dimensional_limits JSONB NOT NULL DEFAULT '[]'::JSONB
        CHECK (jsonb_typeof(dimensional_limits) = 'array');
ALTER TABLE public.profile_systems ALTER COLUMN legacy_authority SET DEFAULT FALSE;

DO $$ DECLARE field_name TEXT; BEGIN
    FOREACH field_name IN ARRAY ARRAY[
        'pulley_height_mm','central_overlap_mm','sliding_lateral_clearance_mm',
        'sliding_end_add_mm','sliding_glazing_deduction_width_mm',
        'sliding_glazing_deduction_height_mm','rail_type','rail_count'
    ] LOOP
        EXECUTE format('ALTER TABLE public.profile_systems ALTER COLUMN %I DROP NOT NULL',field_name);
        EXECUTE format('ALTER TABLE public.profile_systems ALTER COLUMN %I DROP DEFAULT',field_name);
    END LOOP;
END $$;

ALTER TABLE public.profile_articles ADD COLUMN cut_rule JSONB,
    ADD COLUMN reinforcement_rule JSONB;

DROP INDEX uk_tenant_system_singleton_profile_role;
DROP INDEX uk_global_system_singleton_profile_role;
CREATE UNIQUE INDEX uk_tenant_system_singleton_profile_role ON public.profile_articles(system_id,org_id,role)
    WHERE org_id IS NOT NULL AND role NOT IN ('GLAZING_BEAD','COUPLER');
CREATE UNIQUE INDEX uk_global_system_singleton_profile_role ON public.profile_articles(system_id,role)
    WHERE org_id IS NULL AND role NOT IN ('GLAZING_BEAD','COUPLER');
CREATE OR REPLACE FUNCTION private.guard_singleton_profile_role() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path='' AS $$ BEGIN
    IF NEW.role NOT IN ('GLAZING_BEAD','COUPLER') THEN
        PERFORM pg_advisory_xact_lock(hashtextextended(NEW.system_id::TEXT || ':' || NEW.role::TEXT,0));
        IF EXISTS(SELECT 1 FROM public.profile_articles a WHERE a.system_id=NEW.system_id AND a.role=NEW.role
            AND a.id IS DISTINCT FROM NEW.id AND (a.org_id IS NULL OR NEW.org_id IS NULL OR a.org_id=NEW.org_id)) THEN
            RAISE EXCEPTION 'catalog_singleton_role_conflict' USING ERRCODE='23505';
        END IF;
    END IF;
    RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION private.guard_singleton_profile_role() FROM PUBLIC;

-- Missing authorities are allowed as UNKNOWN. When supplied, each scalar is
-- exact, finite, bounded and source-backed, including direct PostgREST writes.
CREATE FUNCTION private.catalog_exact(value JSONB, minimum NUMERIC, strict_min BOOLEAN DEFAULT FALSE)
RETURNS BOOLEAN LANGUAGE plpgsql IMMUTABLE SET search_path='' AS $$
DECLARE parsed NUMERIC;
BEGIN
    IF value IS NULL OR jsonb_typeof(value) NOT IN ('string','number') THEN RETURN FALSE; END IF;
    parsed := (value #>> '{}')::NUMERIC;
    RETURN parsed::TEXT NOT IN ('NaN','Infinity','-Infinity')
        AND CASE WHEN strict_min THEN parsed > minimum ELSE parsed >= minimum END;
EXCEPTION WHEN invalid_text_representation OR numeric_value_out_of_range THEN RETURN FALSE;
END $$;
REVOKE ALL ON FUNCTION private.catalog_exact(JSONB,NUMERIC,BOOLEAN) FROM PUBLIC;

CREATE FUNCTION private.guard_catalog_family_authorities() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path='' AS $$
DECLARE rule JSONB; field_name TEXT; count_openings INT;
BEGIN
    IF TG_TABLE_NAME='profile_systems' THEN
        IF TG_OP='INSERT' AND current_user IN ('postgres','service_role')
            AND EXISTS (SELECT 1 FROM public.profile_systems s WHERE s.id=NEW.id AND s.legacy_authority) THEN
            NEW.legacy_authority := TRUE;
        END IF;
        IF TG_OP='INSERT' AND NEW.legacy_authority AND current_user NOT IN ('postgres','service_role') THEN
            RAISE EXCEPTION 'catalog_legacy_platform_only' USING ERRCODE='23514';
        END IF;
        IF TG_OP='UPDATE' AND NEW.legacy_authority IS DISTINCT FROM OLD.legacy_authority THEN
            RAISE EXCEPTION 'catalog_legacy_immutable' USING ERRCODE='23514';
        END IF;
        IF NEW.legacy_authority THEN RETURN NEW; END IF;
        IF NEW.system_family IS NULL OR NEW.pulley_height_mm IS NOT NULL
            OR NEW.central_overlap_mm IS NOT NULL OR NEW.sliding_lateral_clearance_mm IS NOT NULL
            OR NEW.sliding_end_add_mm IS NOT NULL OR NEW.sliding_glazing_deduction_width_mm IS NOT NULL
            OR NEW.sliding_glazing_deduction_height_mm IS NOT NULL OR NEW.rail_type IS NOT NULL
            OR NEW.rail_count IS NOT NULL THEN
            RAISE EXCEPTION 'catalog_family_required' USING ERRCODE='23514';
        END IF;
        IF NEW.system_family IN ('SLIDING','LIFT_SLIDE') THEN
            rule := NEW.sliding_parameters;
            IF rule IS NULL OR jsonb_typeof(rule) <> 'object'
                OR rule - ARRAY['pulley_height_mm','central_overlap_mm','lateral_clearance_mm','end_add_mm',
                    'glazing_deduction_width_mm','glazing_deduction_height_mm','rail_type','rail_count',
                    'separate_rail','interlock_required'] <> '{}'::JSONB
                OR coalesce(rule->>'rail_type','') NOT IN ('mono','dual')
                OR NOT private.catalog_exact(rule->'rail_count',0,TRUE)
                OR (rule->>'rail_count')::NUMERIC <> trunc((rule->>'rail_count')::NUMERIC)
                OR (rule->>'rail_count')::NUMERIC > 2147483647
                OR jsonb_typeof(rule->'separate_rail') IS DISTINCT FROM 'boolean'
                OR jsonb_typeof(rule->'interlock_required') IS DISTINCT FROM 'boolean' THEN
                RAISE EXCEPTION 'catalog_sliding_parameters_invalid' USING ERRCODE='23514';
            END IF;
            FOREACH field_name IN ARRAY ARRAY['pulley_height_mm','central_overlap_mm',
                'lateral_clearance_mm','end_add_mm','glazing_deduction_width_mm','glazing_deduction_height_mm'] LOOP
                IF NOT private.catalog_exact(rule->field_name,0) THEN
                    RAISE EXCEPTION 'catalog_sliding_parameters_invalid' USING ERRCODE='23514';
                END IF;
            END LOOP;
        ELSIF NEW.sliding_parameters IS NOT NULL THEN
            RAISE EXCEPTION 'catalog_sliding_family_only' USING ERRCODE='23514';
        END IF;
        FOR rule IN SELECT value FROM jsonb_array_elements(NEW.dimensional_limits) LOOP
            IF jsonb_typeof(rule) IS DISTINCT FROM 'object' THEN
                RAISE EXCEPTION 'catalog_dimensional_limit_invalid' USING ERRCODE='23514';
            END IF;
            IF rule - ARRAY['opening_type','min_leaf_width_mm','max_leaf_width_mm','min_leaf_height_mm',
                'max_leaf_height_mm','max_leaf_weight_kg','min_aspect_ratio','max_aspect_ratio','source'] <> '{}'::JSONB
                OR jsonb_typeof(rule->'source') IS DISTINCT FROM 'string'
                OR length(btrim(coalesce(rule->>'source','')))=0 OR coalesce(rule->>'opening_type','') NOT IN
                ('FIXED','TURN_LEFT','TURN_RIGHT','TILT_TURN_LEFT','TILT_TURN_RIGHT',
                 'AWNING','SLIDING','SLIDING_2L','SLIDING_3L','SLIDING_4L','DOOR_ENTRY','DOOR_DOUBLE') THEN
                RAISE EXCEPTION 'catalog_dimensional_limit_invalid' USING ERRCODE='23514';
            END IF;
            IF rule->>'opening_type'<>'FIXED' AND NOT (
                (NEW.system_family='CASEMENT' AND rule->>'opening_type' IN ('TURN_LEFT','TURN_RIGHT','TILT_TURN_LEFT','TILT_TURN_RIGHT','AWNING'))
                OR (NEW.system_family IN ('SLIDING','LIFT_SLIDE') AND rule->>'opening_type' IN ('SLIDING','SLIDING_2L','SLIDING_3L','SLIDING_4L'))
                OR (NEW.system_family='DOOR' AND rule->>'opening_type' IN ('DOOR_ENTRY','DOOR_DOUBLE'))) THEN
                RAISE EXCEPTION 'catalog_limit_family_incompatible' USING ERRCODE='23514';
            END IF;
            FOREACH field_name IN ARRAY ARRAY['min_leaf_width_mm','max_leaf_width_mm',
                'min_leaf_height_mm','max_leaf_height_mm','min_aspect_ratio','max_aspect_ratio'] LOOP
                IF NOT private.catalog_exact(rule->field_name,0,TRUE) THEN
                    RAISE EXCEPTION 'catalog_dimensional_limit_invalid' USING ERRCODE='23514';
                END IF;
            END LOOP;
            IF (rule->>'min_leaf_width_mm')::NUMERIC > (rule->>'max_leaf_width_mm')::NUMERIC
                OR (rule->>'min_leaf_height_mm')::NUMERIC > (rule->>'max_leaf_height_mm')::NUMERIC
                OR (rule->>'min_aspect_ratio')::NUMERIC > (rule->>'max_aspect_ratio')::NUMERIC
                OR (rule->'max_leaf_weight_kg' IS NOT NULL AND rule->'max_leaf_weight_kg'<>'null'::JSONB
                    AND NOT private.catalog_exact(rule->'max_leaf_weight_kg',0,TRUE)) THEN
                RAISE EXCEPTION 'catalog_dimensional_limit_invalid' USING ERRCODE='23514';
            END IF;
        END LOOP;
        SELECT count(DISTINCT value->>'opening_type') INTO count_openings
            FROM jsonb_array_elements(NEW.dimensional_limits);
        IF count_openings <> jsonb_array_length(NEW.dimensional_limits) THEN
            RAISE EXCEPTION 'catalog_dimensional_limit_duplicate' USING ERRCODE='23514';
        END IF;
    ELSE
        rule := NEW.cut_rule;
        IF rule IS NOT NULL THEN
            IF jsonb_typeof(rule) IS DISTINCT FROM 'object' THEN
                RAISE EXCEPTION 'catalog_cut_rule_invalid' USING ERRCODE='23514';
            END IF;
            IF rule - ARRAY['angle_degrees','welding_loss_per_end_mm','joint_deduction_per_end_mm',
                'meeting_deduction_mm','cut_step_mm','rounding','source'] <> '{}'::JSONB
                OR jsonb_typeof(rule->'source') IS DISTINCT FROM 'string'
                OR length(btrim(coalesce(rule->>'source','')))=0 OR coalesce(rule->>'angle_degrees','') NOT IN ('45','90')
                OR coalesce(rule->>'rounding','') NOT IN ('UP','NEAREST','DOWN')
                OR NOT private.catalog_exact(rule->'cut_step_mm',0,TRUE) THEN
                RAISE EXCEPTION 'catalog_cut_rule_invalid' USING ERRCODE='23514';
            END IF;
            FOREACH field_name IN ARRAY ARRAY['welding_loss_per_end_mm','joint_deduction_per_end_mm','meeting_deduction_mm'] LOOP
                IF NOT private.catalog_exact(rule->field_name,0) THEN
                    RAISE EXCEPTION 'catalog_cut_rule_invalid' USING ERRCODE='23514';
                END IF;
            END LOOP;
        END IF;
        rule := NEW.reinforcement_rule;
        IF rule IS NOT NULL THEN
            IF jsonb_typeof(rule) IS DISTINCT FROM 'object' THEN
                RAISE EXCEPTION 'catalog_reinforcement_rule_invalid' USING ERRCODE='23514';
            END IF;
            IF rule - ARRAY['reinforcement_sku','reinforcement_type','minimum_length_mm','required_finishes',
                'required_non_white','cut_deduction_mm','screws_per_m','screw_sku','screw_weight_kg','source'] <> '{}'::JSONB
                OR jsonb_typeof(rule->'source') IS DISTINCT FROM 'string'
                OR length(btrim(coalesce(rule->>'source','')))=0 OR coalesce(rule->>'reinforcement_sku','')=''
                OR coalesce(rule->>'reinforcement_type','')='' OR coalesce(rule->>'screw_sku','')=''
                OR jsonb_typeof(rule->'required_non_white') IS DISTINCT FROM 'boolean'
                OR jsonb_typeof(rule->'required_finishes') IS DISTINCT FROM 'array'
                OR NOT private.catalog_exact(rule->'screws_per_m',0,TRUE) THEN
                RAISE EXCEPTION 'catalog_reinforcement_rule_invalid' USING ERRCODE='23514';
            END IF;
            IF EXISTS(SELECT 1 FROM jsonb_array_elements(rule->'required_finishes') finish
                WHERE jsonb_typeof(finish) IS DISTINCT FROM 'string' OR length(btrim(finish #>> '{}'))=0) THEN
                RAISE EXCEPTION 'catalog_reinforcement_rule_invalid' USING ERRCODE='23514';
            END IF;
            FOREACH field_name IN ARRAY ARRAY['minimum_length_mm','cut_deduction_mm'] LOOP
                IF NOT private.catalog_exact(rule->field_name,0) THEN
                    RAISE EXCEPTION 'catalog_reinforcement_rule_invalid' USING ERRCODE='23514';
                END IF;
            END LOOP;
            IF rule->'screw_weight_kg' IS NOT NULL AND rule->'screw_weight_kg'<>'null'::JSONB
                AND NOT private.catalog_exact(rule->'screw_weight_kg',0) THEN
                RAISE EXCEPTION 'catalog_reinforcement_rule_invalid' USING ERRCODE='23514';
            END IF;
        END IF;
    END IF;
    RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION private.guard_catalog_family_authorities() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.catalog_exact(JSONB,NUMERIC,BOOLEAN)
    TO authenticated,catalog_backend,documentary_backend,pricing_backend,service_role;
CREATE TRIGGER guard_catalog_family_authorities BEFORE INSERT OR UPDATE ON public.profile_systems
    FOR EACH ROW EXECUTE FUNCTION private.guard_catalog_family_authorities();
CREATE TRIGGER guard_catalog_family_authorities BEFORE INSERT OR UPDATE ON public.profile_articles
    FOR EACH ROW EXECUTE FUNCTION private.guard_catalog_family_authorities();

GRANT INSERT (system_family,sliding_parameters,dimensional_limits),
      UPDATE (system_family,sliding_parameters,dimensional_limits)
    ON public.profile_systems TO authenticated;
GRANT INSERT (cut_rule,reinforcement_rule), UPDATE (cut_rule,reinforcement_rule)
    ON public.profile_articles TO authenticated;

CREATE TABLE public.catalog_demo_prices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    system_id UUID NOT NULL REFERENCES public.profile_systems(id) ON DELETE CASCADE,
    sku VARCHAR(100) NOT NULL,
    unit VARCHAR(10) NOT NULL CHECK (unit IN ('BAR','M2','KIT','EA')),
    unit_cost NUMERIC(14,4) NOT NULL CHECK (unit_cost >= 0 AND unit_cost::TEXT NOT IN ('NaN','Infinity','-Infinity')),
    currency public.currency_code NOT NULL DEFAULT 'CLP',
    is_demo BOOLEAN NOT NULL DEFAULT TRUE CHECK (is_demo),
    seed INTEGER NOT NULL,
    source TEXT NOT NULL CHECK (length(source)>0),
    UNIQUE (system_id,sku)
);
ALTER TABLE public.catalog_demo_prices ENABLE ROW LEVEL SECURITY;
CREATE POLICY catalog_demo_prices_read ON public.catalog_demo_prices FOR SELECT
    TO authenticated,pricing_backend,documentary_backend,catalog_backend
    USING (org_id IS NULL AND EXISTS (SELECT 1 FROM public.profile_systems s
        WHERE s.id=system_id AND s.is_global AND s.is_demo AND s.is_active));
GRANT SELECT ON public.catalog_demo_prices
    TO authenticated,pricing_backend,documentary_backend,catalog_backend;
GRANT ALL ON public.catalog_demo_prices TO service_role;
REVOKE ALL ON public.catalog_demo_prices FROM anon;
CREATE TRIGGER guard_referenced_catalog BEFORE INSERT OR UPDATE OR DELETE ON public.catalog_demo_prices
    FOR EACH ROW EXECUTE FUNCTION private.guard_referenced_catalog();

COMMIT;
