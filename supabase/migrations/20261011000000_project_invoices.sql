-- Project invoices (factura): a sealed sale document emitted on an explicit
-- click against the latest sealed revision. payload_json freezes the deal,
-- the position lines, and the collected balance at issue time — an emitted
-- invoice is evidence: no update, no delete. Annulment is a credit note,
-- a separate future document type.

CREATE TABLE public.project_invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL
        REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    project_id UUID NOT NULL
        REFERENCES public.projects(id) ON DELETE RESTRICT,
    project_version_id UUID NOT NULL
        REFERENCES public.project_versions(id) ON DELETE RESTRICT,
    invoice_code VARCHAR(30) NOT NULL,
    payload_json JSONB NOT NULL,
    storage_bucket TEXT NOT NULL CHECK (storage_bucket = 'documents'),
    storage_object_key TEXT NOT NULL,
    file_sha256 TEXT NOT NULL CHECK (file_sha256 ~ '^[0-9a-f]{64}$'),
    media_type TEXT NOT NULL CHECK (media_type = 'application/pdf'),
    byte_size BIGINT NOT NULL CHECK (byte_size > 0),
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_org_invoice_code UNIQUE (org_id, invoice_code)
);

CREATE INDEX idx_project_invoices_project
    ON public.project_invoices (org_id, project_id);

ALTER TABLE public.project_invoices ENABLE ROW LEVEL SECURITY;

-- Tenants read the registry; only the backend role writes it, and only
-- INSERT — the grant set is what makes an invoice sealed evidence.
CREATE POLICY project_invoices_read ON public.project_invoices
    FOR SELECT TO authenticated
    USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY project_invoices_backend ON public.project_invoices
    FOR ALL TO documentary_backend
    USING (org_id IN (SELECT private.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT private.current_user_org_ids()));

GRANT SELECT ON public.project_invoices TO authenticated;
GRANT SELECT, INSERT ON public.project_invoices TO documentary_backend;
GRANT ALL ON public.project_invoices TO service_role;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER
    ON public.project_invoices FROM authenticated;
REVOKE ALL ON public.project_invoices FROM anon;
