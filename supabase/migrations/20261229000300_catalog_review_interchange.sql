BEGIN;

GRANT EXECUTE ON FUNCTION private.pricing_role(UUID,TEXT[])
    TO documentary_backend,catalog_backend,billing_backend;

CREATE POLICY catalog_ai_commercial_boundary ON public.ai_audit_logs AS RESTRICTIVE FOR SELECT
    TO authenticated,billing_backend,documentary_backend
    USING(input_payload #>> '{source,kind}' IS DISTINCT FROM 'catalog_import'
        OR private.pricing_role(org_id,ARRAY['OWNER','WORKSHOP_MANAGER']));

ALTER TABLE public.catalog_imports DROP CONSTRAINT catalog_imports_kind;
ALTER TABLE public.catalog_imports ADD CONSTRAINT catalog_imports_kind
    CHECK (kind IN ('PDF','XLSX','CSV','IMAGE','TEXT'));
ALTER TABLE public.catalog_imports DROP CONSTRAINT catalog_imports_status;
ALTER TABLE public.catalog_imports ADD CONSTRAINT catalog_imports_status
    CHECK (status IN ('UPLOADED','EXTRACTING','REVIEW_READY','CONFIRMED','FAILED','UNDONE'));
ALTER TABLE public.catalog_imports ADD COLUMN contains_costs BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN approved_by UUID, ADD COLUMN approved_at TIMESTAMPTZ,
    ADD CONSTRAINT catalog_imports_org_id_unique UNIQUE(id,org_id);
-- Raw cost rows retain the commercial read boundary, even through imports.
DROP POLICY catalog_imports_member_read ON public.catalog_imports;
CREATE POLICY catalog_imports_member_read ON public.catalog_imports FOR SELECT TO authenticated
    USING (org_id IN (SELECT private.current_user_org_ids()) AND
        (NOT contains_costs OR private.pricing_role(org_id,ARRAY['OWNER','WORKSHOP_MANAGER'])));
DROP POLICY catalog_imports_member_insert ON public.catalog_imports;
DROP POLICY catalog_imports_member_update ON public.catalog_imports;
DROP POLICY catalog_imports_backend ON public.catalog_imports;
CREATE POLICY catalog_imports_backend ON public.catalog_imports FOR ALL TO documentary_backend
    USING (org_id IN (SELECT private.current_user_org_ids()) AND
        (NOT contains_costs OR private.pricing_role(org_id,ARRAY['OWNER','WORKSHOP_MANAGER'])))
    WITH CHECK (org_id IN (SELECT private.current_user_org_ids()) AND
        (NOT contains_costs OR private.pricing_role(org_id,ARRAY['OWNER','WORKSHOP_MANAGER'])));

CREATE TABLE public.catalog_color_skus (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    system_id UUID NOT NULL REFERENCES public.profile_systems(id) ON DELETE CASCADE,
    profile_article_id UUID NOT NULL REFERENCES public.profile_articles(id) ON DELETE CASCADE,
    finish VARCHAR(50) NOT NULL CHECK(length(btrim(finish))>0),
    commercial_sku VARCHAR(150) NOT NULL CHECK(length(btrim(commercial_sku))>0),
    physical_stock_identity VARCHAR(200) NOT NULL CHECK(length(btrim(physical_stock_identity))>0),
    source TEXT NOT NULL CHECK(length(btrim(source))>0),
    UNIQUE(profile_article_id,finish)
);
CREATE FUNCTION private.guard_catalog_color_sku() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path='' AS $$ BEGIN
    IF NOT EXISTS(SELECT 1 FROM public.profile_articles a JOIN public.profile_systems s ON s.id=a.system_id
        WHERE a.id=NEW.profile_article_id AND a.system_id=NEW.system_id
        AND a.org_id=NEW.org_id AND s.org_id=NEW.org_id AND s.finishes ? NEW.finish) THEN
        RAISE EXCEPTION 'catalog_color_scope_invalid' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION private.guard_catalog_color_sku() FROM PUBLIC;
CREATE TRIGGER guard_catalog_color_sku BEFORE INSERT OR UPDATE ON public.catalog_color_skus
    FOR EACH ROW EXECUTE FUNCTION private.guard_catalog_color_sku();
CREATE TRIGGER guard_referenced_catalog BEFORE INSERT OR UPDATE OR DELETE ON public.catalog_color_skus
    FOR EACH ROW EXECUTE FUNCTION private.guard_referenced_catalog();
ALTER TABLE public.catalog_color_skus ENABLE ROW LEVEL SECURITY;
CREATE POLICY catalog_color_skus_read ON public.catalog_color_skus FOR SELECT TO authenticated,catalog_backend
    USING(org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY catalog_color_skus_write ON public.catalog_color_skus FOR ALL TO catalog_backend
    USING(private.can_manage_catalog(org_id)) WITH CHECK(private.can_manage_catalog(org_id));
REVOKE ALL ON public.catalog_color_skus FROM anon,authenticated;
GRANT SELECT ON public.catalog_color_skus TO authenticated;
GRANT SELECT,INSERT,UPDATE,DELETE ON public.catalog_color_skus TO catalog_backend;
GRANT ALL ON public.catalog_color_skus TO service_role;

CREATE TABLE public.catalog_import_publications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    import_id UUID NOT NULL,
    actor_id UUID NOT NULL,
    action VARCHAR(10) NOT NULL CHECK(action IN ('PUBLISH','UNDO')),
    review_token VARCHAR(71) NOT NULL CHECK(review_token ~ '^sha256:[0-9a-f]{64}$'),
    candidates JSONB NOT NULL CHECK(jsonb_typeof(candidates)='array'),
    changes JSONB NOT NULL CHECK(jsonb_typeof(changes)='array'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY(import_id,org_id) REFERENCES public.catalog_imports(id,org_id)
);
ALTER TABLE public.catalog_import_publications ENABLE ROW LEVEL SECURITY;
CREATE POLICY catalog_import_publications_read ON public.catalog_import_publications FOR SELECT
    TO authenticated,catalog_backend
    USING(org_id IN (SELECT private.current_user_org_ids()) AND EXISTS
        (SELECT 1 FROM public.catalog_imports i WHERE i.id=import_id AND i.org_id=catalog_import_publications.org_id));
CREATE POLICY catalog_import_publications_write ON public.catalog_import_publications FOR INSERT TO catalog_backend
    WITH CHECK(private.can_manage_catalog(org_id) AND actor_id=auth.uid());
REVOKE ALL ON public.catalog_import_publications FROM anon,authenticated;
GRANT SELECT ON public.catalog_import_publications TO authenticated;
GRANT SELECT,INSERT ON public.catalog_import_publications TO catalog_backend;
GRANT ALL ON public.catalog_import_publications TO service_role;
CREATE TRIGGER immutable_evidence BEFORE UPDATE OR DELETE ON public.catalog_import_publications
    FOR EACH ROW EXECUTE FUNCTION private.reject_immutable_evidence();
CREATE INDEX catalog_import_publications_org ON public.catalog_import_publications(org_id,import_id);
CREATE INDEX catalog_color_skus_system ON public.catalog_color_skus(system_id);

GRANT SELECT,INSERT ON public.glass_purchase_mappings TO catalog_backend;
-- PostgreSQL row locks require UPDATE on at least one column. The existing
-- immutable-version trigger still rejects updates, including an id rewrite.
GRANT UPDATE(id) ON public.glass_purchase_mappings TO catalog_backend;
CREATE POLICY catalog_glass_backend ON public.glass_purchase_mappings FOR ALL TO catalog_backend
    USING(private.can_manage_catalog(org_id) AND EXISTS
        (SELECT 1 FROM public.profile_systems s WHERE s.id=system_id AND s.org_id=glass_purchase_mappings.org_id))
    WITH CHECK(private.can_manage_catalog(org_id) AND EXISTS
        (SELECT 1 FROM public.profile_systems s WHERE s.id=system_id AND s.org_id=glass_purchase_mappings.org_id));
-- Undo retires immutable glass versions without deleting their evidence.
CREATE TABLE public.catalog_glass_retractions (
    mapping_id UUID PRIMARY KEY REFERENCES public.glass_purchase_mappings(id) ON DELETE RESTRICT,
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    import_id UUID NOT NULL,
    actor_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY(import_id,org_id) REFERENCES public.catalog_imports(id,org_id)
);
ALTER TABLE public.catalog_glass_retractions ENABLE ROW LEVEL SECURITY;
CREATE POLICY catalog_glass_retractions_read ON public.catalog_glass_retractions FOR SELECT
    TO authenticated,documentary_backend,catalog_backend
    USING(org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY catalog_glass_retractions_write ON public.catalog_glass_retractions FOR INSERT TO catalog_backend
    WITH CHECK(private.can_manage_catalog(org_id) AND actor_id=auth.uid() AND EXISTS
        (SELECT 1 FROM public.glass_purchase_mappings g WHERE g.id=mapping_id AND g.org_id=catalog_glass_retractions.org_id));
REVOKE ALL ON public.catalog_glass_retractions FROM anon,authenticated;
GRANT SELECT ON public.catalog_glass_retractions TO authenticated,documentary_backend;
GRANT SELECT,INSERT ON public.catalog_glass_retractions TO catalog_backend;
GRANT ALL ON public.catalog_glass_retractions TO service_role;
CREATE TRIGGER immutable_evidence BEFORE UPDATE OR DELETE ON public.catalog_glass_retractions
    FOR EACH ROW EXECUTE FUNCTION private.reject_immutable_evidence();
CREATE FUNCTION private.guard_catalog_glass_retraction() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path='' AS $$
DECLARE locked BOOLEAN;
BEGIN
    SELECT s.technical_locked INTO locked FROM public.profile_systems s
        JOIN public.glass_purchase_mappings g ON g.system_id=s.id
        WHERE g.id=NEW.mapping_id AND g.org_id=NEW.org_id FOR UPDATE OF s;
    IF locked THEN
        RAISE EXCEPTION 'catalog_authority_referenced' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION private.guard_catalog_glass_retraction() FROM PUBLIC;
CREATE TRIGGER guard_catalog_glass_retraction BEFORE INSERT ON public.catalog_glass_retractions
    FOR EACH ROW EXECUTE FUNCTION private.guard_catalog_glass_retraction();
CREATE POLICY catalog_glass_not_retracted ON public.glass_purchase_mappings AS RESTRICTIVE FOR SELECT
    TO authenticated,documentary_backend
    USING(NOT EXISTS(SELECT 1 FROM public.catalog_glass_retractions r WHERE r.mapping_id=glass_purchase_mappings.id));
GRANT SELECT ON public.catalog_imports TO catalog_backend;
CREATE POLICY catalog_import_catalog_read ON public.catalog_imports FOR SELECT TO catalog_backend
    USING(org_id IN (SELECT private.current_user_org_ids()) AND
        (NOT contains_costs OR private.pricing_role(org_id,ARRAY['OWNER','WORKSHOP_MANAGER'])));

ALTER TABLE public.catalog_parameter_evidence DROP CONSTRAINT catalog_parameter_evidence_authority_table_check;
ALTER TABLE public.catalog_parameter_evidence ADD CONSTRAINT catalog_parameter_evidence_authority_table_check
    CHECK(authority_table IN ('profile_systems','profile_articles','glazing_bead_matrix','hardware_kits',
        'infill_articles','manufacturing_placement_policies','handle_requirement_policies',
        'reinforcement_cut_policies','glass_purchase_mappings','fitting_purchase_mappings',
        'catalog_imports','catalog_color_skus'));

COMMIT;
