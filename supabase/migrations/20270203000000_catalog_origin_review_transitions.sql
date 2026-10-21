BEGIN;

-- New/deleted articles, changed identities and sections also invalidate a
-- reference window, even when no scalar rule changed in the cell ledger.
CREATE FUNCTION private.invalidate_catalog_series_verification() RETURNS TRIGGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE data JSONB; system UUID;
BEGIN
    IF TG_OP='UPDATE' AND to_jsonb(NEW)-ARRAY['technical_reviewed_at','technical_reviewed_by','review_pending','data_provenance']
        IS NOT DISTINCT FROM to_jsonb(OLD)-ARRAY['technical_reviewed_at','technical_reviewed_by','review_pending','data_provenance'] THEN
        RETURN NEW;
    END IF;
    data:=CASE WHEN TG_OP='DELETE' THEN to_jsonb(OLD) ELSE to_jsonb(NEW) END;
    system:=(CASE WHEN TG_TABLE_NAME='profile_systems' THEN data->>'id' ELSE data->>'system_id' END)::uuid;
    UPDATE public.catalog_series_setup SET verified_at=NULL,verified_by=NULL,verified_hash=NULL
        WHERE system_id=system AND org_id=(data->>'org_id')::uuid AND verified_at IS NOT NULL;
    IF TG_OP='DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END $$;

CREATE FUNCTION private.record_catalog_review_origins() RETURNS TRIGGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE cell RECORD; system UUID; val NUMERIC; js JSONB;
BEGIN
    IF NEW.org_id IS NULL OR NEW.technical_reviewed_at IS NULL OR NEW.technical_reviewed_by IS NULL
        OR NEW.technical_reviewed_at IS NOT DISTINCT FROM OLD.technical_reviewed_at THEN RETURN NEW; END IF;
    system:=CASE WHEN TG_TABLE_NAME='profile_systems' THEN NEW.id ELSE (to_jsonb(NEW)->>'system_id')::uuid END;
    IF system IS NULL THEN RETURN NEW; END IF;
    FOR cell IN SELECT * FROM private.catalog_rule_cells(to_jsonb(NEW)) c WHERE COALESCE((
        SELECT h.origin FROM public.catalog_value_history h WHERE h.org_id=NEW.org_id
        AND h.authority_table=TG_TABLE_NAME AND h.row_id=NEW.id AND h.field_name=c.field_name
        ORDER BY h.version DESC LIMIT 1),'SUGGESTED')='SUGGESTED' LOOP
        val:=NULL; js:=cell.value;
        IF jsonb_typeof(js) IN ('number','string') AND (js#>>'{}') ~ '^[+-]?[0-9]+([.][0-9]+)?$' THEN
            val:=(js#>>'{}')::numeric; js:=NULL;
        END IF;
        INSERT INTO public.catalog_value_history(org_id,system_id,authority_table,row_id,field_name,
            value_numeric,value_json,origin,source_ref,set_by,version)
        VALUES(NEW.org_id,system,TG_TABLE_NAME,NEW.id,cell.field_name,val,js,'WORKSHOP',
            'Confirmado en la revisión del taller',NEW.technical_reviewed_by,1);
    END LOOP;
    RETURN NEW;
END $$;

CREATE FUNCTION private.record_catalog_manual_origin() RETURNS TRIGGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE target JSONB; system UUID; cell RECORD; val NUMERIC; js JSONB;
BEGIN
    IF NEW.review_state<>'REVIEWED' OR NEW.authority_table NOT IN
        ('profile_systems','profile_articles','glazing_bead_matrix','hardware_kits')
        OR NEW.extraction_method='HUMAN_CORRECTION'
        OR (NEW.source_page IS NULL AND NEW.source_ref IS NULL AND NEW.source_url IS NULL)
        OR (TG_OP='UPDATE' AND OLD.review_state='REVIEWED') THEN RETURN NEW; END IF;
    EXECUTE format('SELECT to_jsonb(t) FROM public.%I t WHERE id=$1 AND org_id=$2',NEW.authority_table)
        INTO target USING NEW.row_id,NEW.org_id;
    IF target IS NULL OR target->>'data_provenance'='SEED_SYNTHETIC' OR NOT private.catalog_values_equal(
        target#>string_to_array(NEW.field_name,'.'),COALESCE(NULLIF(NEW.canonical_value,'null'::jsonb),to_jsonb(NEW.value_text))) THEN RETURN NEW; END IF;
    system:=(CASE WHEN NEW.authority_table='profile_systems' THEN target->>'id' ELSE target->>'system_id' END)::uuid;
    IF system IS NULL OR EXISTS(SELECT 1 FROM public.profile_systems WHERE id=system AND is_demo) THEN RETURN NEW; END IF;
    FOR cell IN SELECT * FROM private.catalog_rule_cells(target) c
        WHERE c.field_name=NEW.field_name OR starts_with(c.field_name,NEW.field_name||'.') LOOP
        val:=NULL; js:=cell.value;
        IF jsonb_typeof(js) IN ('number','string') AND (js#>>'{}') ~ '^[+-]?[0-9]+([.][0-9]+)?$' THEN
            val:=(js#>>'{}')::numeric; js:=NULL;
        END IF;
        INSERT INTO public.catalog_value_history(org_id,system_id,authority_table,row_id,field_name,
            value_numeric,value_json,origin,source_ref,evidence_id,set_by,version)
        VALUES(NEW.org_id,system,NEW.authority_table,NEW.row_id,cell.field_name,val,js,'MANUAL',
            COALESCE(NEW.source_ref,NEW.source_document),NEW.id,NEW.reviewed_by,1);
    END LOOP;
    RETURN NEW;
END $$;

CREATE TRIGGER record_catalog_manual_origin AFTER INSERT OR UPDATE OF review_state
    ON public.catalog_parameter_evidence FOR EACH ROW EXECUTE FUNCTION private.record_catalog_manual_origin();
DO $$ DECLARE tab TEXT; BEGIN
    FOREACH tab IN ARRAY ARRAY['profile_systems','profile_articles','glazing_bead_matrix','hardware_kits'] LOOP
        EXECUTE format('CREATE TRIGGER invalidate_catalog_series_verification AFTER INSERT OR UPDATE OR DELETE ON public.%I FOR EACH ROW EXECUTE FUNCTION private.invalidate_catalog_series_verification()',tab);
        EXECUTE format('CREATE TRIGGER record_catalog_review_origins AFTER UPDATE OF technical_reviewed_at ON public.%I FOR EACH ROW EXECUTE FUNCTION private.record_catalog_review_origins()',tab);
    END LOOP;
END $$;
REVOKE ALL ON FUNCTION private.invalidate_catalog_series_verification(),
    private.record_catalog_review_origins(),private.record_catalog_manual_origin() FROM PUBLIC;

COMMIT;
