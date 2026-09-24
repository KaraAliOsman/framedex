-- SHOT-14: catalog ingestion — supplier catalogs become reviewable article
-- candidates, then real profile_articles on explicit confirm.
-- Same lifecycle as document_imports: candidates are review data, never
-- catalog truth until a human confirms them.

CREATE TABLE public.catalog_imports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id),
    system_id UUID REFERENCES public.profile_systems(id) ON DELETE SET NULL,
    file_name VARCHAR(200) NOT NULL,
    kind VARCHAR(10) NOT NULL
        CONSTRAINT catalog_imports_kind CHECK (kind IN ('PDF', 'XLSX', 'IMAGE')),
    storage_path VARCHAR(500) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'UPLOADED'
        CONSTRAINT catalog_imports_status CHECK (
            status IN ('UPLOADED', 'EXTRACTING', 'REVIEW_READY', 'CONFIRMED', 'FAILED')
        ),
    -- [{key, sku, name, role, face_width_mm, commercial_length_mm,
    --   welding_loss_mm, reinforcement_sku, weight_kg_m, steel_weight_kg_m,
    --   confidence, warnings}]
    candidates JSONB NOT NULL DEFAULT '[]'::jsonb,
    warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
    -- [{key, article_id}] once CONFIRMED — replay returns it verbatim.
    result JSONB NOT NULL DEFAULT '[]'::jsonb,
    error_code VARCHAR(80) NULL,
    audit_id UUID NULL REFERENCES public.ai_audit_logs(id),
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.catalog_imports ENABLE ROW LEVEL SECURITY;

CREATE POLICY catalog_imports_isolation ON public.catalog_imports
    FOR ALL TO authenticated
    USING (org_id IN (SELECT private.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT private.current_user_org_ids()));

CREATE POLICY catalog_imports_backend ON public.catalog_imports
    FOR ALL TO documentary_backend
    USING (true) WITH CHECK (true);

GRANT SELECT ON public.catalog_imports TO authenticated;
GRANT SELECT, INSERT, UPDATE ON public.catalog_imports TO documentary_backend;
GRANT ALL ON public.catalog_imports TO service_role;
REVOKE ALL ON public.catalog_imports FROM anon;

-- Candidates and result are backend-owned evidence — tenants keep SELECT only.
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER ON public.catalog_imports FROM authenticated;
