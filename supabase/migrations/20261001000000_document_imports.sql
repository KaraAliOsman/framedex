-- SHOT-15: document ingestion — uploaded schedules become reviewable
-- position candidates, then real positions on explicit confirm.
-- document_imports is tenant-scoped evidence: candidates are review data,
-- never manufacturing truth until a human confirms them.

CREATE TABLE public.document_imports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id),
    project_id UUID NOT NULL REFERENCES public.projects(id),
    file_name VARCHAR(200) NOT NULL,
    kind VARCHAR(10) NOT NULL
        CONSTRAINT document_imports_kind CHECK (kind IN ('PDF', 'XLSX', 'IMAGE')),
    storage_path VARCHAR(500) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'UPLOADED'
        CONSTRAINT document_imports_status CHECK (
            status IN ('UPLOADED', 'EXTRACTING', 'REVIEW_READY', 'CONFIRMED', 'FAILED')
        ),
    -- [{key, label, width_mm, height_mm, quantity, opening_type, confidence, warnings}]
    candidates JSONB NOT NULL DEFAULT '[]'::jsonb,
    warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
    -- [{id, location_tag, quantity}] once CONFIRMED — replay returns it verbatim.
    result JSONB NOT NULL DEFAULT '[]'::jsonb,
    error_code VARCHAR(80) NULL,
    audit_id UUID NULL REFERENCES public.ai_audit_logs(id),
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.document_imports ENABLE ROW LEVEL SECURITY;

CREATE POLICY document_imports_isolation ON public.document_imports
    FOR ALL TO authenticated
    USING (org_id IN (SELECT private.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT private.current_user_org_ids()));

CREATE POLICY document_imports_backend ON public.document_imports
    FOR ALL TO documentary_backend
    USING (true) WITH CHECK (true);

GRANT SELECT ON public.document_imports TO authenticated;
GRANT SELECT, INSERT, UPDATE ON public.document_imports TO documentary_backend;
GRANT ALL ON public.document_imports TO service_role;
REVOKE ALL ON public.document_imports FROM anon;

-- Supabase's default table grants hand authenticated INSERT/UPDATE/DELETE on
-- every new table; candidates and result are backend-owned evidence, so the
-- tenant role keeps SELECT only.
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER ON public.document_imports FROM authenticated;
