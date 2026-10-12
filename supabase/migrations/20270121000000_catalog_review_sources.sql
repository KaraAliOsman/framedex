BEGIN;

ALTER TABLE public.catalog_parameter_evidence
    ADD COLUMN source_import_id UUID,
    ADD COLUMN source_ref TEXT,
    ADD COLUMN source_quote TEXT,
    ADD COLUMN source_literal TEXT,
    ADD COLUMN extraction_confidence TEXT,
    ADD COLUMN extraction_method TEXT,
    ADD COLUMN canonical_value JSONB,
    ADD COLUMN original_value JSONB,
    ADD CONSTRAINT evidence_import_org FOREIGN KEY (source_import_id,org_id)
        REFERENCES public.catalog_imports(id,org_id),
    ADD CONSTRAINT evidence_confidence CHECK (extraction_confidence IS NULL OR
        extraction_confidence IN ('HIGH','LOW','UNKNOWN','HUMAN_REVIEWED')),
    ADD CONSTRAINT evidence_method CHECK (extraction_method IS NULL OR
        extraction_method IN ('AI','MANUAL','HUMAN_CORRECTION'));

-- An attestation's source and value are immutable. Review is its one allowed
-- transition; a correction is another attestation, never an overwritten source.
CREATE FUNCTION private.guard_parameter_evidence_review() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path='' AS $$
DECLARE actor UUID := COALESCE(NULLIF(current_setting('request.jwt.claim.sub',TRUE),''),
    NULLIF(current_setting('request.jwt.claims',TRUE),'')::jsonb->>'sub')::UUID;
BEGIN
    IF TG_OP='DELETE' THEN
        RAISE EXCEPTION 'catalog_evidence_immutable' USING ERRCODE='23514';
    END IF;
    IF current_user='catalog_backend' AND
       (NEW.org_id IS NULL OR NOT private.can_manage_catalog(NEW.org_id) OR
        (TG_OP='INSERT' AND NEW.declared_by IS DISTINCT FROM actor)) THEN
        RAISE EXCEPTION 'catalog_evidence_reviewer_required' USING ERRCODE='42501';
    END IF;
    IF TG_OP='UPDATE' THEN
        IF OLD.review_state<>'PENDING' OR NEW.review_state NOT IN ('REVIEWED','REJECTED') OR
           (to_jsonb(NEW)-ARRAY['review_state','reviewed_by','reviewed_at']) IS DISTINCT FROM
           (to_jsonb(OLD)-ARRAY['review_state','reviewed_by','reviewed_at']) THEN
            RAISE EXCEPTION 'catalog_evidence_immutable' USING ERRCODE='23514';
        END IF;
        IF current_user='catalog_backend' AND NEW.reviewed_by IS DISTINCT FROM actor THEN
            RAISE EXCEPTION 'catalog_evidence_reviewer_required' USING ERRCODE='42501';
        END IF;
    END IF;
    RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION private.guard_parameter_evidence_review() FROM PUBLIC;
CREATE TRIGGER guard_parameter_evidence_review BEFORE INSERT OR UPDATE OR DELETE
    ON public.catalog_parameter_evidence FOR EACH ROW
    EXECUTE FUNCTION private.guard_parameter_evidence_review();

CREATE TABLE public.catalog_import_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id),
    import_id UUID NOT NULL,
    actor_id UUID NOT NULL,
    action TEXT NOT NULL CHECK(action IN
        ('UPLOADED','EXTRACTING','REVIEW_READY','REVIEW','PUBLISH','UNDO','FAILED','HISTORICAL_STATE')),
    details JSONB NOT NULL DEFAULT '{}'::jsonb CHECK(jsonb_typeof(details)='object'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    FOREIGN KEY(import_id,org_id) REFERENCES public.catalog_imports(id,org_id)
);
CREATE INDEX catalog_import_events_timeline ON public.catalog_import_events(org_id,import_id,created_at,id);
ALTER TABLE public.catalog_import_events ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.catalog_import_events FROM anon,authenticated;
GRANT SELECT ON public.catalog_import_events TO authenticated,documentary_backend,catalog_backend;
GRANT INSERT ON public.catalog_import_events TO catalog_backend;
GRANT ALL ON public.catalog_import_events TO service_role;
CREATE POLICY catalog_import_events_read ON public.catalog_import_events FOR SELECT
    TO authenticated,documentary_backend,catalog_backend
    USING(org_id IN (SELECT private.current_user_org_ids()) AND EXISTS
        (SELECT 1 FROM public.catalog_imports i WHERE i.id=import_id AND i.org_id=catalog_import_events.org_id));
CREATE POLICY catalog_import_events_insert ON public.catalog_import_events FOR INSERT TO catalog_backend
    WITH CHECK(private.can_manage_catalog(org_id) AND actor_id=auth.uid());
CREATE TRIGGER immutable_evidence BEFORE UPDATE OR DELETE ON public.catalog_import_events
    FOR EACH ROW EXECUTE FUNCTION private.reject_immutable_evidence();

INSERT INTO public.catalog_import_events(org_id,import_id,actor_id,action,details)
SELECT org_id,id,COALESCE(approved_by,created_by),'HISTORICAL_STATE',
       jsonb_build_object('status',status,'history_available',FALSE)
FROM public.catalog_imports;

CREATE FUNCTION private.record_catalog_import_state() RETURNS TRIGGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE event TEXT;
BEGIN
    IF TG_OP='UPDATE' AND NEW.status=OLD.status THEN RETURN NEW; END IF;
    event:=CASE NEW.status WHEN 'CONFIRMED' THEN 'PUBLISH' WHEN 'UNDONE' THEN 'UNDO' ELSE NEW.status END;
    INSERT INTO public.catalog_import_events(org_id,import_id,actor_id,action,details)
    VALUES(NEW.org_id,NEW.id,COALESCE(auth.uid(),NEW.approved_by,NEW.created_by),event,
        jsonb_build_object('candidate_count',jsonb_array_length(NEW.candidates),
                           'status',NEW.status,'error_code',NEW.error_code));
    RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION private.record_catalog_import_state() FROM PUBLIC;
CREATE TRIGGER record_catalog_import_state AFTER INSERT OR UPDATE OF status
    ON public.catalog_imports FOR EACH ROW EXECUTE FUNCTION private.record_catalog_import_state();

CREATE FUNCTION private.guard_catalog_import_source() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path='' AS $$
BEGIN
    IF (NEW.id,NEW.org_id,NEW.storage_path,NEW.file_name,NEW.kind,NEW.created_by,NEW.created_at)
       IS DISTINCT FROM (OLD.id,OLD.org_id,OLD.storage_path,OLD.file_name,OLD.kind,OLD.created_by,OLD.created_at) OR
       (OLD.status IN ('REVIEW_READY','CONFIRMED','UNDONE') AND NEW.candidates IS DISTINCT FROM OLD.candidates) THEN
        RAISE EXCEPTION 'catalog_import_source_immutable' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION private.guard_catalog_import_source() FROM PUBLIC;
CREATE TRIGGER guard_catalog_import_source BEFORE UPDATE ON public.catalog_imports
    FOR EACH ROW EXECUTE FUNCTION private.guard_catalog_import_source();

CREATE FUNCTION private.catalog_reviewer_label(actor UUID, tenant UUID) RETURNS TEXT
LANGUAGE sql STABLE SECURITY DEFINER SET search_path='' AS $$
    SELECT COALESCE(NULLIF(u.raw_user_meta_data->>'full_name',''),
        CASE m.role::text WHEN 'OWNER' THEN 'Dueño' WHEN 'WORKSHOP_MANAGER' THEN 'Encargado de taller'
             ELSE 'Miembro de la organización' END)
    FROM public.tenancy_memberships m LEFT JOIN auth.users u ON u.id=m.user_id
    WHERE m.user_id=actor AND m.org_id=tenant
      AND tenant IN (SELECT private.current_user_org_ids())
    LIMIT 1
$$;
REVOKE ALL ON FUNCTION private.catalog_reviewer_label(UUID,UUID) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.catalog_reviewer_label(UUID,UUID)
    TO authenticated,catalog_backend,documentary_backend;

COMMIT;
