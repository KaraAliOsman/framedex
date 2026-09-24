-- Project credit notes (nota de crédito): the only way to annul an emitted
-- factura. An invoice is sealed evidence and is never updated or deleted —
-- a credit note is the counter-document that cancels it, itself sealed and
-- immutable. One total credit note per invoice (partial credits are a
-- future document kind); UNIQUE(invoice_id) makes a retried emission
-- idempotent — the replay returns the already-sealed row, never a re-render.

CREATE TABLE public.project_credit_notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL
        REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    project_id UUID NOT NULL
        REFERENCES public.projects(id) ON DELETE RESTRICT,
    invoice_id UUID NOT NULL
        REFERENCES public.project_invoices(id) ON DELETE RESTRICT,
    credit_code VARCHAR(30) NOT NULL,
    payload_json JSONB NOT NULL,
    storage_bucket TEXT NOT NULL CHECK (storage_bucket = 'documents'),
    storage_object_key TEXT NOT NULL,
    file_sha256 TEXT NOT NULL CHECK (file_sha256 ~ '^[0-9a-f]{64}$'),
    media_type TEXT NOT NULL CHECK (media_type = 'application/pdf'),
    byte_size BIGINT NOT NULL CHECK (byte_size > 0),
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_org_credit_code UNIQUE (org_id, credit_code),
    CONSTRAINT uk_credit_invoice UNIQUE (invoice_id)
);

CREATE INDEX idx_project_credit_notes_project
    ON public.project_credit_notes (org_id, project_id);

ALTER TABLE public.project_credit_notes ENABLE ROW LEVEL SECURITY;

-- Tenants read the registry; only the backend role writes it, and only
-- INSERT — the grant set is what makes a credit note sealed evidence.
CREATE POLICY project_credit_notes_read ON public.project_credit_notes
    FOR SELECT TO authenticated
    USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY project_credit_notes_backend ON public.project_credit_notes
    FOR ALL TO documentary_backend
    USING (org_id IN (SELECT private.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT private.current_user_org_ids()));

GRANT SELECT ON public.project_credit_notes TO authenticated;
GRANT SELECT, INSERT ON public.project_credit_notes TO documentary_backend;
GRANT ALL ON public.project_credit_notes TO service_role;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER
    ON public.project_credit_notes FROM authenticated;
REVOKE ALL ON public.project_credit_notes FROM anon;
