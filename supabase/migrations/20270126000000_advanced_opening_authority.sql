-- Generated additive D08 contract; historical rows and snapshots are untouched.
BEGIN;
ALTER TABLE public.hardware_kits DROP CONSTRAINT chk_kits_opening_type;
ALTER TABLE public.hardware_kits ADD CONSTRAINT chk_kits_opening_type CHECK(opening_type IN ('AWNING','DOOR','SLIDING','TILT','TILT_TURN','TURN','LIFT_SLIDE','PARALLEL_SLIDE','FOLD','PIVOT_V','PIVOT_H','VERTICAL_SLIDE'));
-- Decimal text + complete finite schema. No authority is inferred from a name.
CREATE FUNCTION private.advanced_recipe_valid(r JSONB, cap JSONB) RETURNS BOOLEAN
LANGUAGE plpgsql STABLE SET search_path=pg_catalog,public AS $$
DECLARE panel_data JSONB; previous JSONB; field_name TEXT; share_total NUMERIC:=0;
  motion TEXT:=cap->>'movement'; moving_count INT:=0; group_name TEXT; group_count INT; start_share NUMERIC:=0; shift_share NUMERIC;
  first_slot INT; last_slot INT; stack TEXT;
BEGIN
  IF NOT public.hardware_schema_valid(r,'{"$defs": {"AdvancedPanel": {"additionalProperties": false, "description": "One panel in a sourced recipe, ordered in the interior elevation.", "properties": {"balance": {"anyOf": [{"enum": ["SPRING", "COUNTERWEIGHT"], "type": "string"}, {"type": "null"}], "default": null, "title": "Balance"}, "closing_side": {"$ref": "#/$defs/HingeSide"}, "fixed_in_sash": {"title": "Fixed In Sash", "type": "boolean"}, "fold_group": {"anyOf": [{"type": "string"}, {"type": "null"}], "default": null, "title": "Fold Group"}, "fold_index": {"anyOf": [{"maximum": 15, "minimum": 0, "type": "integer"}, {"type": "null"}], "default": null, "title": "Fold Index"}, "kind": {"enum": ["MOVING", "FIXED"], "title": "Kind", "type": "string"}, "pass_through": {"default": false, "title": "Pass Through", "type": "boolean"}, "pivot_fraction": {"anyOf": [{"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "type": "string"}, {"type": "null"}], "default": null, "title": "Pivot Fraction"}, "plane_offset_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Plane Offset Mm", "type": "string"}, "share": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Share", "type": "string"}, "slot": {"maxLength": 32, "minLength": 1, "title": "Slot", "type": "string"}, "stack_side": {"anyOf": [{"enum": ["LEFT", "RIGHT"], "type": "string"}, {"type": "null"}], "default": null, "title": "Stack Side"}, "track": {"anyOf": [{"maximum": 15, "minimum": 0, "type": "integer"}, {"type": "null"}], "title": "Track"}, "travel": {"anyOf": [{"enum": ["LEFT", "RIGHT", "UP", "DOWN"], "type": "string"}, {"type": "null"}], "title": "Travel"}, "travel_fraction": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Travel Fraction", "type": "string"}}, "required": ["slot", "kind", "share", "fixed_in_sash", "track", "plane_offset_mm", "travel", "travel_fraction", "closing_side"], "title": "AdvancedPanel", "type": "object"}, "HingeSide": {"enum": ["LEFT", "RIGHT", "TOP", "BOTTOM", "NONE"], "title": "HingeSide", "type": "string"}}, "additionalProperties": false, "description": "Catalog authority, never an executable formula or an editable drawing.", "properties": {"code": {"maxLength": 64, "minLength": 1, "title": "Code", "type": "string"}, "distribution_axis": {"enum": ["X", "Y"], "title": "Distribution Axis", "type": "string"}, "glazing_deduction_height_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Glazing Deduction Height Mm", "type": "string"}, "glazing_deduction_width_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Glazing Deduction Width Mm", "type": "string"}, "hardware_kit_skus": {"items": {"type": "string"}, "minItems": 1, "title": "Hardware Kit Skus", "type": "array"}, "inset_bottom_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Inset Bottom Mm", "type": "string"}, "inset_left_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Inset Left Mm", "type": "string"}, "inset_right_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Inset Right Mm", "type": "string"}, "inset_top_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Inset Top Mm", "type": "string"}, "interlock_end_deduction_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Interlock End Deduction Mm", "type": "string"}, "interlock_required": {"title": "Interlock Required", "type": "boolean"}, "leaf_profile_role": {"enum": ["SASH", "SLIDING_SASH", "DOOR_SASH"], "title": "Leaf Profile Role", "type": "string"}, "lift_mm": {"anyOf": [{"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "type": "string"}, {"type": "null"}], "default": null, "title": "Lift Mm"}, "max_leaf_height_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Max Leaf Height Mm", "type": "string"}, "max_leaf_weight_kg": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Max Leaf Weight Kg", "type": "string"}, "max_leaf_width_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Max Leaf Width Mm", "type": "string"}, "meeting_gap_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Meeting Gap Mm", "type": "string"}, "meeting_overlap_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Meeting Overlap Mm", "type": "string"}, "min_leaf_height_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Min Leaf Height Mm", "type": "string"}, "min_leaf_width_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Min Leaf Width Mm", "type": "string"}, "name": {"maxLength": 160, "minLength": 1, "title": "Name", "type": "string"}, "opening_angle_deg": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Opening Angle Deg", "type": "string"}, "packet_pitch_mm": {"anyOf": [{"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "type": "string"}, {"type": "null"}], "default": null, "title": "Packet Pitch Mm"}, "panels": {"items": {"$ref": "#/$defs/AdvancedPanel"}, "maxItems": 16, "minItems": 1, "title": "Panels", "type": "array"}, "parallel_offset_mm": {"anyOf": [{"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "type": "string"}, {"type": "null"}], "default": null, "title": "Parallel Offset Mm"}, "pass_through_hardware_kit_skus": {"default": [], "items": {"type": "string"}, "title": "Pass Through Hardware Kit Skus", "type": "array"}, "rail_count": {"maximum": 16, "minimum": 0, "title": "Rail Count", "type": "integer"}, "rail_end_deduction_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Rail End Deduction Mm", "type": "string"}, "rail_profile_role": {"anyOf": [{"const": "RAIL", "type": "string"}, {"type": "null"}], "default": null, "title": "Rail Profile Role"}, "rail_sides": {"items": {"enum": ["TOP", "BOTTOM", "LEFT", "RIGHT"], "type": "string"}, "title": "Rail Sides", "type": "array"}, "schema_version": {"const": 1, "default": 1, "title": "Schema Version", "type": "integer"}, "scheme": {"maxLength": 32, "minLength": 1, "title": "Scheme", "type": "string"}, "source": {"minLength": 1, "title": "Source", "type": "string"}, "starter_height_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Starter Height Mm", "type": "string"}, "starter_width_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Starter Width Mm", "type": "string"}, "synthetic": {"title": "Synthetic", "type": "boolean"}, "threshold_height_mm": {"anyOf": [{"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "type": "string"}, {"type": "null"}], "default": null, "title": "Threshold Height Mm"}}, "required": ["code", "name", "scheme", "source", "synthetic", "distribution_axis", "panels", "leaf_profile_role", "inset_left_mm", "inset_right_mm", "inset_top_mm", "inset_bottom_mm", "meeting_overlap_mm", "meeting_gap_mm", "glazing_deduction_width_mm", "glazing_deduction_height_mm", "rail_count", "rail_sides", "rail_end_deduction_mm", "interlock_required", "interlock_end_deduction_mm", "opening_angle_deg", "hardware_kit_skus", "min_leaf_width_mm", "max_leaf_width_mm", "min_leaf_height_mm", "max_leaf_height_mm", "max_leaf_weight_kg", "starter_width_mm", "starter_height_mm"], "title": "AdvancedOpeningRecipe", "type": "object"}'::JSONB,'{"$defs": {"AdvancedPanel": {"additionalProperties": false, "description": "One panel in a sourced recipe, ordered in the interior elevation.", "properties": {"balance": {"anyOf": [{"enum": ["SPRING", "COUNTERWEIGHT"], "type": "string"}, {"type": "null"}], "default": null, "title": "Balance"}, "closing_side": {"$ref": "#/$defs/HingeSide"}, "fixed_in_sash": {"title": "Fixed In Sash", "type": "boolean"}, "fold_group": {"anyOf": [{"type": "string"}, {"type": "null"}], "default": null, "title": "Fold Group"}, "fold_index": {"anyOf": [{"maximum": 15, "minimum": 0, "type": "integer"}, {"type": "null"}], "default": null, "title": "Fold Index"}, "kind": {"enum": ["MOVING", "FIXED"], "title": "Kind", "type": "string"}, "pass_through": {"default": false, "title": "Pass Through", "type": "boolean"}, "pivot_fraction": {"anyOf": [{"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "type": "string"}, {"type": "null"}], "default": null, "title": "Pivot Fraction"}, "plane_offset_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Plane Offset Mm", "type": "string"}, "share": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Share", "type": "string"}, "slot": {"maxLength": 32, "minLength": 1, "title": "Slot", "type": "string"}, "stack_side": {"anyOf": [{"enum": ["LEFT", "RIGHT"], "type": "string"}, {"type": "null"}], "default": null, "title": "Stack Side"}, "track": {"anyOf": [{"maximum": 15, "minimum": 0, "type": "integer"}, {"type": "null"}], "title": "Track"}, "travel": {"anyOf": [{"enum": ["LEFT", "RIGHT", "UP", "DOWN"], "type": "string"}, {"type": "null"}], "title": "Travel"}, "travel_fraction": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Travel Fraction", "type": "string"}}, "required": ["slot", "kind", "share", "fixed_in_sash", "track", "plane_offset_mm", "travel", "travel_fraction", "closing_side"], "title": "AdvancedPanel", "type": "object"}, "HingeSide": {"enum": ["LEFT", "RIGHT", "TOP", "BOTTOM", "NONE"], "title": "HingeSide", "type": "string"}}, "additionalProperties": false, "description": "Catalog authority, never an executable formula or an editable drawing.", "properties": {"code": {"maxLength": 64, "minLength": 1, "title": "Code", "type": "string"}, "distribution_axis": {"enum": ["X", "Y"], "title": "Distribution Axis", "type": "string"}, "glazing_deduction_height_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Glazing Deduction Height Mm", "type": "string"}, "glazing_deduction_width_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Glazing Deduction Width Mm", "type": "string"}, "hardware_kit_skus": {"items": {"type": "string"}, "minItems": 1, "title": "Hardware Kit Skus", "type": "array"}, "inset_bottom_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Inset Bottom Mm", "type": "string"}, "inset_left_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Inset Left Mm", "type": "string"}, "inset_right_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Inset Right Mm", "type": "string"}, "inset_top_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Inset Top Mm", "type": "string"}, "interlock_end_deduction_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Interlock End Deduction Mm", "type": "string"}, "interlock_required": {"title": "Interlock Required", "type": "boolean"}, "leaf_profile_role": {"enum": ["SASH", "SLIDING_SASH", "DOOR_SASH"], "title": "Leaf Profile Role", "type": "string"}, "lift_mm": {"anyOf": [{"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "type": "string"}, {"type": "null"}], "default": null, "title": "Lift Mm"}, "max_leaf_height_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Max Leaf Height Mm", "type": "string"}, "max_leaf_weight_kg": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Max Leaf Weight Kg", "type": "string"}, "max_leaf_width_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Max Leaf Width Mm", "type": "string"}, "meeting_gap_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Meeting Gap Mm", "type": "string"}, "meeting_overlap_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Meeting Overlap Mm", "type": "string"}, "min_leaf_height_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Min Leaf Height Mm", "type": "string"}, "min_leaf_width_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Min Leaf Width Mm", "type": "string"}, "name": {"maxLength": 160, "minLength": 1, "title": "Name", "type": "string"}, "opening_angle_deg": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Opening Angle Deg", "type": "string"}, "packet_pitch_mm": {"anyOf": [{"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "type": "string"}, {"type": "null"}], "default": null, "title": "Packet Pitch Mm"}, "panels": {"items": {"$ref": "#/$defs/AdvancedPanel"}, "maxItems": 16, "minItems": 1, "title": "Panels", "type": "array"}, "parallel_offset_mm": {"anyOf": [{"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "type": "string"}, {"type": "null"}], "default": null, "title": "Parallel Offset Mm"}, "pass_through_hardware_kit_skus": {"default": [], "items": {"type": "string"}, "title": "Pass Through Hardware Kit Skus", "type": "array"}, "rail_count": {"maximum": 16, "minimum": 0, "title": "Rail Count", "type": "integer"}, "rail_end_deduction_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Rail End Deduction Mm", "type": "string"}, "rail_profile_role": {"anyOf": [{"const": "RAIL", "type": "string"}, {"type": "null"}], "default": null, "title": "Rail Profile Role"}, "rail_sides": {"items": {"enum": ["TOP", "BOTTOM", "LEFT", "RIGHT"], "type": "string"}, "title": "Rail Sides", "type": "array"}, "schema_version": {"const": 1, "default": 1, "title": "Schema Version", "type": "integer"}, "scheme": {"maxLength": 32, "minLength": 1, "title": "Scheme", "type": "string"}, "source": {"minLength": 1, "title": "Source", "type": "string"}, "starter_height_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Starter Height Mm", "type": "string"}, "starter_width_mm": {"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "title": "Starter Width Mm", "type": "string"}, "synthetic": {"title": "Synthetic", "type": "boolean"}, "threshold_height_mm": {"anyOf": [{"pattern": "^(?!^[-+.]*$)[+-]?0*\\d*\\.?\\d*$", "type": "string"}, {"type": "null"}], "default": null, "title": "Threshold Height Mm"}}, "required": ["code", "name", "scheme", "source", "synthetic", "distribution_axis", "panels", "leaf_profile_role", "inset_left_mm", "inset_right_mm", "inset_top_mm", "inset_bottom_mm", "meeting_overlap_mm", "meeting_gap_mm", "glazing_deduction_width_mm", "glazing_deduction_height_mm", "rail_count", "rail_sides", "rail_end_deduction_mm", "interlock_required", "interlock_end_deduction_mm", "opening_angle_deg", "hardware_kit_skus", "min_leaf_width_mm", "max_leaf_width_mm", "min_leaf_height_mm", "max_leaf_height_mm", "max_leaf_weight_kg", "starter_width_mm", "starter_height_mm"], "title": "AdvancedOpeningRecipe", "type": "object"}'::JSONB)
    OR (SELECT count(DISTINCT value->>'slot') FROM jsonb_array_elements(r->'panels'))<>jsonb_array_length(r->'panels')
    OR (SELECT count(DISTINCT value) FROM jsonb_array_elements(r->'hardware_kit_skus'))<>jsonb_array_length(r->'hardware_kit_skus')
    OR EXISTS(SELECT 1 FROM jsonb_array_elements(r->'hardware_kit_skus') k WHERE NOT (cap->'hardware_kit_skus' @> jsonb_build_array(k)))
    OR EXISTS(SELECT 1 FROM jsonb_array_elements(r->'pass_through_hardware_kit_skus') k WHERE NOT (cap->'hardware_kit_skus' @> jsonb_build_array(k)))
    OR (SELECT count(DISTINCT value) FROM jsonb_array_elements(r->'pass_through_hardware_kit_skus'))<>jsonb_array_length(r->'pass_through_hardware_kit_skus')
    OR (jsonb_array_length(r->'pass_through_hardware_kit_skus')>0) IS DISTINCT FROM
        EXISTS(SELECT 1 FROM jsonb_array_elements(r->'panels') p WHERE (p->>'pass_through')::BOOLEAN)
    OR (r->>'min_leaf_width_mm')::NUMERIC>(r->>'max_leaf_width_mm')::NUMERIC
    OR (r->>'min_leaf_height_mm')::NUMERIC>(r->>'max_leaf_height_mm')::NUMERIC
    OR ((r->>'rail_profile_role' IS NULL) IS DISTINCT FROM ((r->>'rail_count')::INT=0))
    OR jsonb_array_length(r->'rail_sides')<>(r->>'rail_count')::INT THEN RETURN FALSE; END IF;
  FOREACH field_name IN ARRAY ARRAY['meeting_overlap_mm','meeting_gap_mm','glazing_deduction_width_mm',
      'glazing_deduction_height_mm','rail_end_deduction_mm','interlock_end_deduction_mm'] LOOP
    IF NOT private.catalog_exact(r->field_name,0) THEN RETURN FALSE; END IF;
  END LOOP;
  FOREACH field_name IN ARRAY ARRAY['inset_left_mm','inset_right_mm','inset_top_mm','inset_bottom_mm'] LOOP
    IF (r->>field_name)::NUMERIC::TEXT IN ('NaN','Infinity','-Infinity') THEN RETURN FALSE; END IF;
  END LOOP;
  FOREACH field_name IN ARRAY ARRAY['min_leaf_width_mm','max_leaf_width_mm','min_leaf_height_mm',
      'max_leaf_height_mm','max_leaf_weight_kg','starter_width_mm','starter_height_mm','opening_angle_deg'] LOOP
    IF NOT private.catalog_exact(r->field_name,0,TRUE) THEN RETURN FALSE; END IF;
  END LOOP;
  FOREACH field_name IN ARRAY ARRAY['threshold_height_mm','lift_mm','parallel_offset_mm','packet_pitch_mm'] LOOP
    IF r->>field_name IS NOT NULL AND NOT private.catalog_exact(r->field_name,0,TRUE) THEN RETURN FALSE; END IF;
  END LOOP;
  IF (r->>'opening_angle_deg')::NUMERIC>90 THEN RETURN FALSE; END IF;
  IF (motion='LIFT_SLIDE' AND (r->>'lift_mm' IS NULL OR r->>'threshold_height_mm' IS NULL))
    OR (motion='PARALLEL_SLIDE' AND r->>'parallel_offset_mm' IS NULL)
    OR (motion='SLIDE' AND cap->>'use'='DOOR' AND r->>'threshold_height_mm' IS NULL)
    OR (motion<>'LIFT_SLIDE' AND r->>'lift_mm' IS NOT NULL)
    OR (motion<>'PARALLEL_SLIDE' AND r->>'parallel_offset_mm' IS NOT NULL)
    OR (motion='FOLD' AND (r->>'distribution_axis'<>'X' OR r->>'rail_profile_role' IS NULL OR r->>'packet_pitch_mm' IS NULL))
    OR (motion IN ('PIVOT_V','PIVOT_H') AND jsonb_array_length(r->'panels')<>1)
    OR (motion='VERTICAL_SLIDE' AND r->>'distribution_axis'<>'Y')
    OR (motion NOT IN ('PIVOT_V','PIVOT_H') AND r->>'rail_profile_role' IS NULL)
    OR (motion<>'FOLD' AND r->>'packet_pitch_mm' IS NOT NULL)
    OR (motion IN ('LIFT_SLIDE','PARALLEL_SLIDE','SLIDE') AND r->>'distribution_axis'<>'X') THEN RETURN FALSE; END IF;
  FOR panel_data IN SELECT value FROM jsonb_array_elements(r->'panels') LOOP
    IF (panel_data->>'plane_offset_mm')::NUMERIC::TEXT IN ('NaN','Infinity','-Infinity') THEN RETURN FALSE; END IF;
    IF NOT private.catalog_exact(panel_data->'share',0,TRUE) OR (panel_data->>'share')::NUMERIC>1
      OR NOT private.catalog_exact(panel_data->'travel_fraction',0) OR (panel_data->>'travel_fraction')::NUMERIC>1
      OR ((panel_data->>'travel' IS NULL) IS DISTINCT FROM ((panel_data->>'travel_fraction')::NUMERIC=0))
      OR (panel_data->>'pivot_fraction' IS NOT NULL AND (NOT private.catalog_exact(panel_data->'pivot_fraction',0,TRUE)
          OR (panel_data->>'pivot_fraction')::NUMERIC>=1)) THEN RETURN FALSE; END IF;
    share_total:=share_total+(panel_data->>'share')::NUMERIC;
    shift_share:=(panel_data->>'travel_fraction')::NUMERIC*CASE WHEN panel_data->>'travel' IN ('LEFT','UP') THEN -1 ELSE 1 END;
    IF panel_data->>'travel' IS NOT NULL AND (start_share+shift_share<0 OR share_total+shift_share>1) THEN RETURN FALSE; END IF;
    start_share:=share_total;
    IF panel_data->>'kind'='FIXED' THEN
      IF panel_data->>'track' IS NOT NULL OR panel_data->>'travel' IS NOT NULL OR panel_data->>'closing_side'<>'NONE'
        OR panel_data->>'pivot_fraction' IS NOT NULL OR panel_data->>'fold_group' IS NOT NULL OR panel_data->>'balance' IS NOT NULL
        OR panel_data->>'fold_index' IS NOT NULL OR panel_data->>'stack_side' IS NOT NULL
        OR (panel_data->>'pass_through')::BOOLEAN THEN RETURN FALSE; END IF;
    ELSE
      moving_count:=moving_count+1;
      IF (panel_data->>'fixed_in_sash')::BOOLEAN OR panel_data->>'closing_side'='NONE' THEN RETURN FALSE; END IF;
      IF motion IN ('LIFT_SLIDE','PARALLEL_SLIDE','SLIDE') AND (panel_data->>'track' IS NULL OR coalesce(panel_data->>'travel','') NOT IN ('LEFT','RIGHT')) THEN RETURN FALSE; END IF;
      IF motion='VERTICAL_SLIDE' AND (panel_data->>'track' IS NULL OR coalesce(panel_data->>'travel','') NOT IN ('UP','DOWN') OR panel_data->>'balance' IS NULL) THEN RETURN FALSE; END IF;
      IF motion<>'VERTICAL_SLIDE' AND panel_data->>'balance' IS NOT NULL THEN RETURN FALSE; END IF;
      IF motion IN ('PIVOT_V','PIVOT_H') AND (panel_data->>'pivot_fraction' IS NULL OR panel_data->>'track' IS NOT NULL OR panel_data->>'travel' IS NOT NULL) THEN RETURN FALSE; END IF;
      IF motion NOT IN ('PIVOT_V','PIVOT_H') AND panel_data->>'pivot_fraction' IS NOT NULL THEN RETURN FALSE; END IF;
      IF motion='FOLD' THEN
        IF panel_data->>'fold_group' IS NULL OR panel_data->>'fold_index' IS NULL OR panel_data->>'stack_side' IS NULL
          OR panel_data->>'track' IS NOT NULL OR panel_data->>'travel' IS NOT NULL THEN RETURN FALSE; END IF;
      ELSIF panel_data->>'fold_group' IS NOT NULL OR panel_data->>'fold_index' IS NOT NULL OR panel_data->>'stack_side' IS NOT NULL
          OR (panel_data->>'pass_through')::BOOLEAN THEN RETURN FALSE; END IF;
      IF previous->>'kind'='MOVING' AND previous->>'travel' IS NOT NULL AND panel_data->>'travel' IS NOT NULL
          AND previous->'track'=panel_data->'track' THEN RETURN FALSE; END IF;
    END IF;
    previous:=panel_data;
  END LOOP;
  IF share_total<>1 OR moving_count=0 THEN RETURN FALSE; END IF;
  IF (SELECT count(DISTINCT (p->>'plane_offset_mm')::NUMERIC) FROM jsonb_array_elements(r->'panels') p WHERE p->>'track' IS NOT NULL)
    < (SELECT count(DISTINCT p->>'track') FROM jsonb_array_elements(r->'panels') p WHERE p->>'track' IS NOT NULL) THEN RETURN FALSE; END IF;
  IF EXISTS(SELECT 1 FROM jsonb_array_elements(r->'panels') p WHERE p->>'track' IS NOT NULL
    GROUP BY p->>'track' HAVING count(DISTINCT (p->>'plane_offset_mm')::NUMERIC)>1) THEN RETURN FALSE; END IF;
  IF motion='FOLD' THEN
    FOR group_name IN SELECT DISTINCT p->>'fold_group' FROM jsonb_array_elements(r->'panels') p WHERE p->>'kind'='MOVING' LOOP
      SELECT count(*) INTO group_count FROM jsonb_array_elements(r->'panels') p WHERE p->>'fold_group'=group_name;
      SELECT min(ordinality),max(ordinality),min(p->>'stack_side') INTO first_slot,last_slot,stack
        FROM jsonb_array_elements(r->'panels') WITH ORDINALITY a(p,ordinality) WHERE p->>'fold_group'=group_name;
      IF last_slot-first_slot+1<>group_count OR EXISTS(SELECT 1 FROM jsonb_array_elements(r->'panels') WITH ORDINALITY a(p,ordinality)
          WHERE p->>'fold_group'=group_name AND ((p->>'fold_index')::INT<>
            CASE WHEN stack='RIGHT' THEN last_slot-ordinality ELSE ordinality-first_slot END
            OR (p->>'pass_through')::BOOLEAN AND (p->>'fold_index')::INT<>group_count-1)) THEN RETURN FALSE; END IF;
      IF (SELECT count(DISTINCT p->>'stack_side') FROM jsonb_array_elements(r->'panels') p WHERE p->>'fold_group'=group_name)<>1
        OR EXISTS(SELECT 1 FROM generate_series(0,group_count-1) i WHERE
          (SELECT count(*) FROM jsonb_array_elements(r->'panels') p WHERE p->>'fold_group'=group_name AND (p->>'fold_index')::INT=i)<>1) THEN RETURN FALSE; END IF;
    END LOOP;
  END IF;
  RETURN TRUE;
EXCEPTION WHEN OTHERS THEN RETURN FALSE;
END $$;
REVOKE ALL ON FUNCTION private.advanced_recipe_valid(JSONB,JSONB) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.advanced_recipe_valid(JSONB,JSONB) TO catalog_backend;

CREATE OR REPLACE FUNCTION private.guard_opening_authorities() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path='' AS $$
DECLARE cap JSONB; rule JSONB; hinge JSONB; field_name TEXT; signatures TEXT[] := '{}'; signature TEXT; advanced BOOLEAN; recipe JSONB;
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
            OR cap - ARRAY['use','movement','direction','leaf_role','fixed_in_sash','hinge_sides','hardware_kit_skus','handle_rule','source','advanced_recipes'] <> '{}'
            OR coalesce(cap->>'use','') NOT IN ('WINDOW','DOOR')
            OR coalesce(cap->>'movement','') NOT IN ('FIXED','TURN','TILT','TILT_TURN','TOP_HUNG','SLIDE','LIFT_SLIDE','PARALLEL_SLIDE','FOLD','PIVOT_V','PIVOT_H','VERTICAL_SLIDE')
            OR coalesce(cap->>'direction','') NOT IN ('INWARD','OUTWARD')
            OR coalesce(cap->>'leaf_role','') NOT IN ('SINGLE','ACTIVE','PASSIVE')
            OR jsonb_typeof(cap->'fixed_in_sash') IS DISTINCT FROM 'boolean'
            OR jsonb_typeof(cap->'hinge_sides') IS DISTINCT FROM 'array'
            OR jsonb_typeof(cap->'hardware_kit_skus') IS DISTINCT FROM 'array'
            OR jsonb_typeof(cap->'source') IS DISTINCT FROM 'string'
            OR length(btrim(coalesce(cap->>'source','')))=0 THEN
            RAISE EXCEPTION 'opening_capability_invalid' USING ERRCODE='23514';
        END IF;
        advanced := cap->>'movement' IN ('LIFT_SLIDE','PARALLEL_SLIDE','FOLD','PIVOT_V','PIVOT_H','VERTICAL_SLIDE')
            OR (cap->>'movement'='SLIDE' AND cap->>'use'='DOOR');
        IF (advanced AND (cap->>'leaf_role'<>'SINGLE' OR cap->>'fixed_in_sash'='true' OR cap->'hinge_sides'<>'["NONE"]'::JSONB
                OR jsonb_typeof(cap->'advanced_recipes') IS DISTINCT FROM 'array' OR jsonb_array_length(cap->'advanced_recipes')=0
                OR nullif(cap->'handle_rule','null') IS NULL))
            OR (NOT advanced AND coalesce(cap->'advanced_recipes','[]'::JSONB)<>'[]'::JSONB) THEN
            RAISE EXCEPTION 'opening_capability_invalid' USING ERRCODE='23514';
        END IF;
        IF advanced THEN
            IF (SELECT count(DISTINCT value->>'code') FROM jsonb_array_elements(cap->'advanced_recipes'))<>jsonb_array_length(cap->'advanced_recipes') THEN
                RAISE EXCEPTION 'advanced_opening_recipe_ambiguous' USING ERRCODE='23514';
            END IF;
            FOR recipe IN SELECT value FROM jsonb_array_elements(cap->'advanced_recipes') LOOP
                IF NOT private.advanced_recipe_valid(recipe,cap) THEN
                    RAISE EXCEPTION 'advanced_opening_recipe_invalid' USING ERRCODE='23514';
                END IF;
            END LOOP;
        END IF;
        IF NEW.system_family IS NULL OR (cap->>'use'='DOOR') IS DISTINCT FROM (NEW.system_family='DOOR')
            OR (cap->>'movement'='SLIDE' AND NEW.system_family NOT IN ('SLIDING','DOOR'))
            OR (cap->>'movement'='LIFT_SLIDE' AND NEW.system_family<>'LIFT_SLIDE')
            OR (cap->>'movement'='VERTICAL_SLIDE' AND NEW.system_family<>'SLIDING')
            OR (cap->>'movement'='FOLD' AND NEW.system_family<>'DOOR')
            OR (cap->>'movement' IN ('PARALLEL_SLIDE','PIVOT_V','PIVOT_H') AND NEW.system_family<>'CASEMENT')
            OR (cap->>'movement' IN ('TURN','TILT','TILT_TURN','TOP_HUNG') AND NEW.system_family NOT IN ('CASEMENT','DOOR'))
            OR (cap->>'use'='DOOR' AND cap->>'movement' NOT IN ('FIXED','TURN','SLIDE','FOLD')) THEN
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
            IF (cap->>'movement' IN ('FIXED','SLIDE','LIFT_SLIDE','PARALLEL_SLIDE','FOLD','PIVOT_V','PIVOT_H','VERTICAL_SLIDE') AND hinge #>> '{}' <> 'NONE')
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
            OR (cap->>'movement' IN ('FIXED','SLIDE','LIFT_SLIDE','PARALLEL_SLIDE','FOLD','PIVOT_V','PIVOT_H','VERTICAL_SLIDE') AND cap->>'leaf_role'<>'SINGLE')
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

CREATE OR REPLACE FUNCTION private.check_opening_catalog_bindings() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path='' AS $$
DECLARE target UUID; targets UUID[]; system_row public.profile_systems%ROWTYPE; cap JSONB; kit_sku TEXT; expected_type TEXT; recipe JSONB; profile_role TEXT;
BEGIN
    IF TG_TABLE_NAME='profile_systems' THEN targets := ARRAY[NEW.id];
    ELSIF TG_OP='UPDATE' THEN targets := ARRAY[OLD.system_id,NEW.system_id];
    ELSE targets := ARRAY[CASE WHEN TG_OP='DELETE' THEN OLD.system_id ELSE NEW.system_id END]; END IF;
    FOREACH target IN ARRAY targets LOOP
    SELECT is_active,opening_capabilities,org_id
      INTO system_row.is_active,system_row.opening_capabilities,system_row.org_id
      FROM public.profile_systems WHERE id=target;
    IF NOT FOUND OR NOT system_row.is_active OR system_row.opening_capabilities IS NULL THEN CONTINUE; END IF;
    FOR cap IN SELECT value FROM jsonb_array_elements(system_row.opening_capabilities) LOOP
        expected_type := CASE WHEN cap->>'use'='DOOR' AND cap->>'movement'='TURN' THEN 'DOOR'
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
        FOR recipe IN SELECT value FROM jsonb_array_elements(coalesce(cap->'advanced_recipes','[]'::JSONB)) LOOP
            FOR kit_sku IN SELECT jsonb_array_elements_text(recipe->'hardware_kit_skus')
                UNION SELECT jsonb_array_elements_text(recipe->'pass_through_hardware_kit_skus') LOOP
                IF NOT EXISTS(SELECT 1 FROM public.hardware_kits k WHERE k.system_id=target
                    AND k.org_id IS NOT DISTINCT FROM system_row.org_id AND k.sku=kit_sku AND k.is_active
                    AND k.opening_type=expected_type AND k.class_authority IS NOT NULL
                    AND (cap->>'movement' NOT IN ('LIFT_SLIDE','PARALLEL_SLIDE','FOLD','SLIDE')
                        OR k.carriages_qty>0 AND k.carriage_capacity_kg>0
                           AND k.max_leaf_weight_kg<=k.carriages_qty*k.carriage_capacity_kg)
                    AND (cap->>'movement'<>'PARALLEL_SLIDE' OR k.stay_arms_qty>0)) THEN
                    RAISE EXCEPTION 'advanced_opening_kit_authority_required' USING ERRCODE='23514';
                END IF;
            END LOOP;
            FOR profile_role IN SELECT value FROM unnest(ARRAY[recipe->>'leaf_profile_role',recipe->>'rail_profile_role',
                CASE WHEN recipe->>'threshold_height_mm' IS NOT NULL THEN 'THRESHOLD' END,
                CASE WHEN recipe->>'interlock_required'='true' THEN 'INTERLOCK' END]) value WHERE value IS NOT NULL LOOP
                IF NOT EXISTS(SELECT 1 FROM public.profile_articles a WHERE a.system_id=target
                    AND a.org_id IS NOT DISTINCT FROM system_row.org_id AND a.role::TEXT=profile_role) THEN
                    RAISE EXCEPTION 'advanced_opening_profile_required' USING ERRCODE='23514';
                END IF;
            END LOOP;
        END LOOP;
        IF cap->>'leaf_role' IN ('ACTIVE','PASSIVE') AND NOT EXISTS(SELECT 1 FROM public.profile_articles a
            WHERE a.system_id=target AND a.org_id IS NOT DISTINCT FROM system_row.org_id AND a.role='INVERSOR') THEN
            RAISE EXCEPTION 'opening_inversor_authority_required' USING ERRCODE='23514';
        END IF;
    END LOOP;
    END LOOP;
    RETURN NULL;
END $$;

COMMIT;
