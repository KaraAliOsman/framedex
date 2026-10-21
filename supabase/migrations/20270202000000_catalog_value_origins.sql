BEGIN;

-- Current cells remain in the existing typed catalog tables. This ledger is
-- append-only: changing a number or confirming its origin adds a new version.
CREATE TABLE public.catalog_value_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id),
    system_id UUID NOT NULL,
    authority_table TEXT NOT NULL CHECK(authority_table IN
        ('profile_systems','profile_articles','glazing_bead_matrix','hardware_kits')),
    row_id UUID NOT NULL,
    field_name TEXT NOT NULL CHECK(length(field_name) BETWEEN 1 AND 250),
    version BIGINT NOT NULL,
    previous_id UUID,
    value_numeric NUMERIC,
    value_json JSONB,
    previous_numeric NUMERIC,
    previous_json JSONB,
    origin TEXT NOT NULL CHECK(origin IN ('MANUAL','WORKSHOP','SUGGESTED')),
    source_ref TEXT NOT NULL CHECK(length(btrim(source_ref)) BETWEEN 1 AND 1000),
    evidence_id UUID REFERENCES public.catalog_parameter_evidence(id),
    set_by UUID NOT NULL,
    set_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CHECK((value_numeric IS NULL) <> (value_json IS NULL)),
    CHECK(value_numeric IS NULL OR value_numeric::text NOT IN ('NaN','Infinity','-Infinity')),
    CHECK(origin <> 'MANUAL' OR evidence_id IS NOT NULL),
    UNIQUE(id,org_id),
    UNIQUE(org_id,authority_table,row_id,field_name,version),
    FOREIGN KEY(previous_id,org_id) REFERENCES public.catalog_value_history(id,org_id)
);
CREATE INDEX catalog_value_history_system ON public.catalog_value_history
    (org_id,system_id,authority_table,row_id,field_name,version DESC);

CREATE TABLE public.catalog_series_setup (
    system_id UUID PRIMARY KEY REFERENCES public.profile_systems(id) ON DELETE CASCADE,
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id),
    template_id TEXT,
    template_version INTEGER CHECK(template_version > 0),
    verified_at TIMESTAMPTZ,
    verified_by UUID,
    verified_hash TEXT CHECK(verified_hash IS NULL OR verified_hash ~ '^sha256:[0-9a-f]{64}$'),
    CHECK((template_id IS NULL) = (template_version IS NULL)),
    CHECK((verified_at IS NULL AND verified_by IS NULL AND verified_hash IS NULL) OR
          (verified_at IS NOT NULL AND verified_by IS NOT NULL AND verified_hash IS NOT NULL))
);

ALTER TABLE public.catalog_value_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.catalog_series_setup ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.catalog_value_history,public.catalog_series_setup FROM anon,authenticated;
GRANT SELECT ON public.catalog_value_history,public.catalog_series_setup
    TO authenticated,catalog_backend,documentary_backend;
GRANT INSERT ON public.catalog_value_history TO catalog_backend;
GRANT INSERT,UPDATE ON public.catalog_series_setup TO catalog_backend;
GRANT ALL ON public.catalog_value_history,public.catalog_series_setup TO service_role;
CREATE POLICY catalog_value_history_read ON public.catalog_value_history FOR SELECT
    TO authenticated,catalog_backend,documentary_backend
    USING(org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY catalog_value_history_insert ON public.catalog_value_history FOR INSERT TO catalog_backend
    WITH CHECK(private.can_manage_catalog(org_id) AND set_by=auth.uid());
CREATE POLICY catalog_series_setup_read ON public.catalog_series_setup FOR SELECT
    TO authenticated,catalog_backend,documentary_backend
    USING(org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY catalog_series_setup_write ON public.catalog_series_setup FOR ALL TO catalog_backend
    USING(private.can_manage_catalog(org_id)) WITH CHECK(private.can_manage_catalog(org_id));

-- Canonical evidence may spell an exact decimal as a JSON string. Comparison
-- accepts that representation, never a rounded or otherwise different value.
CREATE FUNCTION private.catalog_values_equal(a JSONB,b JSONB) RETURNS BOOLEAN
LANGUAGE plpgsql IMMUTABLE SET search_path='' AS $$
DECLARE k TEXT; i INTEGER; av TEXT; bv TEXT;
BEGIN
    IF a IS NOT DISTINCT FROM b THEN RETURN TRUE; END IF;
    IF a IS NULL OR b IS NULL THEN RETURN FALSE; END IF;
    IF jsonb_typeof(a)='object' AND jsonb_typeof(b)='object' THEN
        IF (SELECT array_agg(key ORDER BY key) FROM jsonb_object_keys(a) key) IS DISTINCT FROM
           (SELECT array_agg(key ORDER BY key) FROM jsonb_object_keys(b) key) THEN RETURN FALSE; END IF;
        FOR k IN SELECT jsonb_object_keys(a) LOOP
            IF NOT private.catalog_values_equal(a->k,b->k) THEN RETURN FALSE; END IF;
        END LOOP;
        RETURN TRUE;
    END IF;
    IF jsonb_typeof(a)='array' AND jsonb_typeof(b)='array' THEN
        IF jsonb_array_length(a)<>jsonb_array_length(b) THEN RETURN FALSE; END IF;
        FOR i IN 0..jsonb_array_length(a)-1 LOOP
            IF NOT private.catalog_values_equal(a->i,b->i) THEN RETURN FALSE; END IF;
        END LOOP;
        RETURN TRUE;
    END IF;
    IF jsonb_typeof(a) IN ('number','string') AND jsonb_typeof(b) IN ('number','string') THEN
        av:=a#>>'{}'; bv:=b#>>'{}';
        IF av ~ '^[+-]?[0-9]+([.][0-9]+)?$' AND bv ~ '^[+-]?[0-9]+([.][0-9]+)?$' THEN
            RETURN av::numeric=bv::numeric;
        END IF;
    END IF;
    RETURN FALSE;
END $$;

CREATE FUNCTION private.guard_catalog_value_version() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path='' AS $$
DECLARE target JSONB; previous public.catalog_value_history; actual JSONB; declared JSONB;
    actor UUID:=COALESCE(NULLIF(current_setting('request.jwt.claim.sub',TRUE),''),
        NULLIF(current_setting('request.jwt.claims',TRUE),'')::jsonb->>'sub')::UUID;
BEGIN
    IF NEW.authority_table NOT IN ('profile_systems','profile_articles','glazing_bead_matrix','hardware_kits') THEN
        RAISE EXCEPTION 'catalog_value_target_invalid' USING ERRCODE='23514';
    END IF;
    EXECUTE format('SELECT to_jsonb(t) FROM public.%I t WHERE id=$1 AND org_id=$2',NEW.authority_table)
        INTO target USING NEW.row_id,NEW.org_id;
    IF target IS NULL OR
       (CASE WHEN NEW.authority_table='profile_systems' THEN target->>'id' ELSE target->>'system_id' END)::uuid
       IS DISTINCT FROM NEW.system_id THEN
        RAISE EXCEPTION 'catalog_value_target_invalid' USING ERRCODE='23514';
    END IF;
    actual:=target#>string_to_array(NEW.field_name,'.');
    declared:=COALESCE(to_jsonb(NEW.value_numeric),NEW.value_json);
    IF NOT private.catalog_values_equal(COALESCE(actual,'null'::jsonb),declared) THEN
        RAISE EXCEPTION 'catalog_value_mismatch' USING ERRCODE='23514';
    END IF;
    IF NEW.origin='MANUAL' AND NOT EXISTS (
        SELECT 1 FROM public.catalog_parameter_evidence e WHERE e.id=NEW.evidence_id
        AND e.org_id=NEW.org_id AND e.row_id=NEW.row_id AND e.authority_table=NEW.authority_table
        AND e.review_state='REVIEWED' AND e.extraction_method IS DISTINCT FROM 'HUMAN_CORRECTION'
        AND (e.source_page IS NOT NULL OR e.source_ref IS NOT NULL OR e.source_url IS NOT NULL)
        AND private.catalog_values_equal(target#>string_to_array(e.field_name,'.'),
            COALESCE(e.canonical_value,to_jsonb(e.value_text)))
        AND (NEW.field_name=e.field_name OR starts_with(NEW.field_name,e.field_name || '.'))) THEN
        RAISE EXCEPTION 'catalog_manual_evidence_required' USING ERRCODE='23514';
    END IF;
    IF NEW.origin='MANUAL' AND (target->>'data_provenance'='SEED_SYNTHETIC' OR EXISTS(
        SELECT 1 FROM public.profile_systems WHERE id=NEW.system_id AND is_demo)) THEN
        RAISE EXCEPTION 'catalog_synthetic_not_manual' USING ERRCODE='23514';
    END IF;
    IF current_user='catalog_backend' AND NEW.set_by IS DISTINCT FROM actor THEN
        RAISE EXCEPTION 'catalog_value_actor_required' USING ERRCODE='42501';
    END IF;
    PERFORM pg_advisory_xact_lock(hashtextextended(
        NEW.org_id::text||NEW.authority_table||NEW.row_id::text||NEW.field_name,0));
    SELECT * INTO previous FROM public.catalog_value_history WHERE org_id=NEW.org_id
        AND authority_table=NEW.authority_table AND row_id=NEW.row_id AND field_name=NEW.field_name
        ORDER BY version DESC LIMIT 1;
    NEW.previous_id:=previous.id;
    NEW.version:=COALESCE(previous.version,0)+1;
    IF previous.id IS NOT NULL THEN
        NEW.previous_numeric:=previous.value_numeric;
        NEW.previous_json:=previous.value_json;
    END IF;
    NEW.set_at:=clock_timestamp();
    RETURN NEW;
END $$;
CREATE TRIGGER guard_catalog_value_version BEFORE INSERT ON public.catalog_value_history
    FOR EACH ROW EXECUTE FUNCTION private.guard_catalog_value_version();
CREATE TRIGGER immutable_catalog_value_history BEFORE UPDATE OR DELETE ON public.catalog_value_history
    FOR EACH ROW EXECUTE FUNCTION private.reject_immutable_evidence();
CREATE TRIGGER immutable_catalog_value_truncate BEFORE TRUNCATE ON public.catalog_value_history
    FOR EACH STATEMENT EXECUTE FUNCTION private.reject_immutable_evidence();

CREATE FUNCTION private.guard_catalog_series_setup() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path='' AS $$
DECLARE actor UUID:=COALESCE(NULLIF(current_setting('request.jwt.claim.sub',TRUE),''),
    NULLIF(current_setting('request.jwt.claims',TRUE),'')::jsonb->>'sub')::UUID;
BEGIN
    IF NOT EXISTS(SELECT 1 FROM public.profile_systems s WHERE s.id=NEW.system_id AND s.org_id=NEW.org_id) THEN
        RAISE EXCEPTION 'catalog_setup_tenant_mismatch' USING ERRCODE='23514';
    END IF;
    IF TG_OP='UPDATE' AND (NEW.org_id,NEW.system_id,NEW.template_id,NEW.template_version)
        IS DISTINCT FROM (OLD.org_id,OLD.system_id,OLD.template_id,OLD.template_version) THEN
        RAISE EXCEPTION 'catalog_setup_identity_immutable' USING ERRCODE='23514';
    END IF;
    IF current_user='catalog_backend' AND NEW.verified_at IS NOT NULL
        AND NEW.verified_by IS DISTINCT FROM actor THEN
        RAISE EXCEPTION 'catalog_verification_actor_required' USING ERRCODE='42501';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER guard_catalog_series_setup BEFORE INSERT OR UPDATE ON public.catalog_series_setup
    FOR EACH ROW EXECUTE FUNCTION private.guard_catalog_series_setup();

-- Flatten objects into independently confirmable cells; ordered rule tables
-- (arrays) remain atomic. Source labels describe a rule, not another value.
CREATE FUNCTION private.catalog_rule_cells(data JSONB) RETURNS TABLE(field_name TEXT,value JSONB)
LANGUAGE sql IMMUTABLE SET search_path='' AS $$
    WITH RECURSIVE cells(path,value) AS (
        SELECT key,value FROM jsonb_each(data) WHERE key IN (
            'depth_mm','chamber_count','sash_overlap_mm','glass_clearance_white_mm','glass_clearance_foil_mm',
            'pulley_height_mm','central_overlap_mm','sliding_lateral_clearance_mm','sliding_end_add_mm',
            'corner_bracket_loss_mm','hook_depth_mm','door_threshold_mm','door_bottom_clearance_mm',
            'door_leaf_side_clearance_mm','rail_type','rail_count','rebate_depth_mm','end_milling_overlap_mm',
            'sliding_glazing_deduction_width_mm','sliding_glazing_deduction_height_mm','sliding_parameters',
            'dimensional_limits','opening_capabilities','paired_leaf_rule','finish_authority','finishes',
            'face_width_mm','commercial_length_mm','welding_loss_mm','reinforcement_gap_mm',
            'weight_kg_m','steel_weight_kg_m','reinforcement_sku','cut_rule','reinforcement_rule','coupling_rule',
            'glass_thickness_mm','bead_article_id','bead_width_mm','gasket_interior_mm','gasket_exterior_mm',
            'cut_add_mm','opening_type','min_leaf_width_mm','max_leaf_width_mm','min_leaf_height_mm',
            'max_leaf_height_mm','max_leaf_weight_kg','weight_kg','carriages_qty','carriage_capacity_kg',
            'stay_arms_qty','contents','class_authority')
        UNION ALL
        SELECT c.path||'.'||item.key,item.value FROM cells c
        CROSS JOIN LATERAL jsonb_each(CASE WHEN jsonb_typeof(c.value)='object' THEN c.value ELSE '{}'::jsonb END) item
        WHERE item.key<>'source'
    ) SELECT path,value FROM cells WHERE jsonb_typeof(value)<>'object' AND value<>'null'::jsonb
$$;

CREATE FUNCTION private.record_catalog_rule_changes() RETURNS TRIGGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE cell RECORD; metadata JSONB; annotation JSONB; actor UUID:=auth.uid();
    old_data JSONB; numeric_value NUMERIC; json_value JSONB; system UUID;
    prior_numeric NUMERIC; prior_json JSONB;
BEGIN
    IF NEW.org_id IS NULL OR actor IS NULL THEN RETURN NEW; END IF;
    system:=CASE WHEN TG_TABLE_NAME='profile_systems' THEN NEW.id ELSE (to_jsonb(NEW)->>'system_id')::uuid END;
    IF system IS NULL THEN RETURN NEW; END IF;
    old_data:=CASE WHEN TG_OP='UPDATE' THEN to_jsonb(OLD) ELSE '{}'::jsonb END;
    metadata:=COALESCE(NULLIF(current_setting('app.catalog_value_origins',TRUE),'')::jsonb,'{}'::jsonb);
    FOR cell IN SELECT field_name,COALESCE(n.value,'null'::jsonb) AS value,o.value AS old_value
        FROM private.catalog_rule_cells(to_jsonb(NEW)) n
        FULL JOIN private.catalog_rule_cells(old_data) o USING(field_name) LOOP
        IF cell.value IS NOT DISTINCT FROM cell.old_value THEN CONTINUE; END IF;
        annotation:=metadata->cell.field_name;
        numeric_value:=NULL; json_value:=cell.value;
        prior_numeric:=NULL; prior_json:=cell.old_value;
        IF jsonb_typeof(cell.value) IN ('number','string') AND (cell.value#>>'{}') ~ '^[+-]?[0-9]+([.][0-9]+)?$' THEN
            numeric_value:=(cell.value#>>'{}')::numeric; json_value:=NULL;
        END IF;
        IF jsonb_typeof(prior_json) IN ('number','string') AND (prior_json#>>'{}') ~ '^[+-]?[0-9]+([.][0-9]+)?$' THEN
            prior_numeric:=(prior_json#>>'{}')::numeric; prior_json:=NULL;
        END IF;
        INSERT INTO public.catalog_value_history(org_id,system_id,authority_table,row_id,field_name,
            value_numeric,value_json,previous_numeric,previous_json,origin,source_ref,evidence_id,set_by,version)
        VALUES(NEW.org_id,system,TG_TABLE_NAME,NEW.id,cell.field_name,numeric_value,json_value,prior_numeric,prior_json,
            COALESCE(annotation->>'origin','WORKSHOP'),COALESCE(annotation->>'source_ref','Escrito por el taller'),
            (annotation->>'evidence_id')::uuid,actor,1);
    END LOOP;
    -- Clearing a rule is a material edit too, although absence is no origin row.
    IF TG_OP='UPDATE' AND EXISTS(SELECT 1 FROM private.catalog_rule_cells(old_data) old_cell
        FULL JOIN private.catalog_rule_cells(to_jsonb(NEW)) new_cell USING(field_name)
        WHERE old_cell.value IS DISTINCT FROM new_cell.value) THEN
        UPDATE public.catalog_series_setup SET verified_at=NULL,verified_by=NULL,verified_hash=NULL
            WHERE system_id=system AND org_id=NEW.org_id;
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER record_catalog_rule_changes AFTER INSERT OR UPDATE ON public.profile_systems
    FOR EACH ROW EXECUTE FUNCTION private.record_catalog_rule_changes();
CREATE TRIGGER record_catalog_rule_changes AFTER INSERT OR UPDATE ON public.profile_articles
    FOR EACH ROW EXECUTE FUNCTION private.record_catalog_rule_changes();
CREATE TRIGGER record_catalog_rule_changes AFTER INSERT OR UPDATE ON public.glazing_bead_matrix
    FOR EACH ROW EXECUTE FUNCTION private.record_catalog_rule_changes();
CREATE TRIGGER record_catalog_rule_changes AFTER INSERT OR UPDATE ON public.hardware_kits
    FOR EACH ROW EXECUTE FUNCTION private.record_catalog_rule_changes();

REVOKE ALL ON FUNCTION private.catalog_values_equal(JSONB,JSONB),
    private.guard_catalog_value_version(),private.guard_catalog_series_setup(),
    private.catalog_rule_cells(JSONB),private.record_catalog_rule_changes() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.catalog_values_equal(JSONB,JSONB) TO catalog_backend;

-- Only reviewed historical values get a workshop origin. Unreviewed rows stay
-- unconfirmed; a matching reviewed manufacturer attestation can promote a cell.
DO $$ DECLARE tab TEXT; item RECORD; cell RECORD; ev RECORD; val NUMERIC; js JSONB; BEGIN
    FOREACH tab IN ARRAY ARRAY['profile_systems','profile_articles','glazing_bead_matrix','hardware_kits'] LOOP
        FOR item IN EXECUTE format('SELECT to_jsonb(t) data FROM public.%I t WHERE org_id IS NOT NULL AND technical_reviewed_by IS NOT NULL AND technical_reviewed_at IS NOT NULL AND NOT review_pending AND data_provenance<>''SEED_SYNTHETIC'' AND NOT EXISTS(SELECT 1 FROM public.profile_systems s WHERE s.id=CASE WHEN %L=''profile_systems'' THEN t.id ELSE (to_jsonb(t)->>''system_id'')::uuid END AND s.is_demo)',tab,tab) LOOP
            IF tab<>'profile_systems' AND item.data->>'system_id' IS NULL THEN CONTINUE; END IF;
            FOR cell IN SELECT * FROM private.catalog_rule_cells(item.data) LOOP
                SELECT e.* INTO ev FROM public.catalog_parameter_evidence e
                    WHERE e.org_id=(item.data->>'org_id')::uuid AND e.row_id=(item.data->>'id')::uuid
                    AND e.authority_table=tab AND e.review_state='REVIEWED'
                    AND e.extraction_method IS DISTINCT FROM 'HUMAN_CORRECTION'
                    AND (e.source_page IS NOT NULL OR e.source_ref IS NOT NULL OR e.source_url IS NOT NULL)
                    AND (cell.field_name=e.field_name OR starts_with(cell.field_name,e.field_name||'.'))
                    AND private.catalog_values_equal(item.data#>string_to_array(e.field_name,'.'),COALESCE(e.canonical_value,to_jsonb(e.value_text)))
                    ORDER BY e.reviewed_at DESC,e.id LIMIT 1;
                val:=NULL; js:=cell.value;
                IF jsonb_typeof(js) IN ('number','string') AND (js#>>'{}') ~ '^[+-]?[0-9]+([.][0-9]+)?$' THEN
                    val:=(js#>>'{}')::numeric; js:=NULL;
                END IF;
                INSERT INTO public.catalog_value_history(org_id,system_id,authority_table,row_id,field_name,
                    value_numeric,value_json,origin,source_ref,evidence_id,set_by,version)
                VALUES((item.data->>'org_id')::uuid,
                    (CASE WHEN tab='profile_systems' THEN item.data->>'id' ELSE item.data->>'system_id' END)::uuid,
                    tab,(item.data->>'id')::uuid,cell.field_name,val,js,
                    CASE WHEN ev.id IS NULL THEN 'WORKSHOP' ELSE 'MANUAL' END,
                    CASE WHEN ev.id IS NULL THEN 'Revisión histórica del taller' ELSE COALESCE(ev.source_ref,ev.source_document) END,
                    ev.id,(item.data->>'technical_reviewed_by')::uuid,1);
            END LOOP;
        END LOOP;
    END LOOP;
END $$;

COMMIT;
