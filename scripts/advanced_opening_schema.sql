-- Decimal text + complete finite schema. No authority is inferred from a name.
CREATE FUNCTION private.advanced_recipe_valid(r JSONB, cap JSONB) RETURNS BOOLEAN
LANGUAGE plpgsql STABLE SET search_path=pg_catalog,public AS $$
DECLARE panel_data JSONB; previous JSONB; field_name TEXT; share_total NUMERIC:=0;
  motion TEXT:=cap->>'movement'; moving_count INT:=0; group_name TEXT; group_count INT; start_share NUMERIC:=0; shift_share NUMERIC;
  first_slot INT; last_slot INT; stack TEXT;
BEGIN
  IF NOT public.hardware_schema_valid(r,'__RECIPE_SCHEMA__'::JSONB,'__RECIPE_SCHEMA__'::JSONB)
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
