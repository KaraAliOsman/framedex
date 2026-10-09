-- Generated from the typed CouplerRule. Additive; NULL preserves history.
BEGIN;
ALTER TABLE public.profile_articles ADD COLUMN coupling_rule JSONB;
CREATE FUNCTION public.coupling_rule_valid(rule JSONB, role TEXT) RETURNS BOOLEAN
LANGUAGE plpgsql IMMUTABLE SET search_path=pg_catalog,public AS $$ BEGIN
    IF rule IS NULL THEN RETURN TRUE; END IF;
    IF role<>'COUPLER' OR NOT public.hardware_schema_valid(rule,'{"additionalProperties": false, "description": "Sourced joint deflection and front-axis contribution, independent of saw angles.\n\nAngles are absolute deflections. development_mm is the distance between\nmodule front endpoints along the joint bisector (zero for a shared pivot).", "properties": {"development_mm": {"anyOf": [{"minimum": 0.0, "type": "number"}, {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "type": "string"}], "title": "Development Mm"}, "max_angle_deg": {"anyOf": [{"maximum": 90.0, "minimum": 0.0, "type": "number"}, {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "type": "string"}], "title": "Max Angle Deg"}, "min_angle_deg": {"anyOf": [{"maximum": 90.0, "minimum": 0.0, "type": "number"}, {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "type": "string"}], "title": "Min Angle Deg"}, "source": {"minLength": 1, "title": "Source", "type": "string"}}, "required": ["min_angle_deg", "max_angle_deg", "development_mm", "source"], "title": "CouplerRule", "type": "object"}'::JSONB,'{"additionalProperties": false, "description": "Sourced joint deflection and front-axis contribution, independent of saw angles.\n\nAngles are absolute deflections. development_mm is the distance between\nmodule front endpoints along the joint bisector (zero for a shared pivot).", "properties": {"development_mm": {"anyOf": [{"minimum": 0.0, "type": "number"}, {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "type": "string"}], "title": "Development Mm"}, "max_angle_deg": {"anyOf": [{"maximum": 90.0, "minimum": 0.0, "type": "number"}, {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "type": "string"}], "title": "Max Angle Deg"}, "min_angle_deg": {"anyOf": [{"maximum": 90.0, "minimum": 0.0, "type": "number"}, {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "type": "string"}], "title": "Min Angle Deg"}, "source": {"minLength": 1, "title": "Source", "type": "string"}}, "required": ["min_angle_deg", "max_angle_deg", "development_mm", "source"], "title": "CouplerRule", "type": "object"}'::JSONB)
       OR length(btrim(rule->>'source'))=0 THEN RETURN FALSE; END IF;
    RETURN (rule->>'min_angle_deg')::NUMERIC >= 0
       AND (rule->>'max_angle_deg')::NUMERIC <= 90
       AND (rule->>'min_angle_deg')::NUMERIC <= (rule->>'max_angle_deg')::NUMERIC
       AND (rule->>'development_mm')::NUMERIC >= 0;
EXCEPTION WHEN OTHERS THEN RETURN FALSE; END; $$;
ALTER TABLE public.profile_articles ADD CONSTRAINT coupling_rule_contract
    CHECK(public.coupling_rule_valid(coupling_rule,role::TEXT));
GRANT SELECT(coupling_rule) ON public.profile_articles TO authenticated,catalog_backend,pricing_backend,documentary_backend;
GRANT INSERT(coupling_rule),UPDATE(coupling_rule) ON public.profile_articles TO authenticated;
COMMENT ON COLUMN public.profile_articles.coupling_rule IS
    'P06 sourced absolute joint deflection and net front-axis width; unrelated to saw cutting angles. NULL preserves historical authority.';
COMMIT;
