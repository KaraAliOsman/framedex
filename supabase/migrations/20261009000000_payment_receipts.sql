-- Payment receipts: a sealed, immutable comprobante per ledger payment.
-- One row per payment, written once inside record_payment's transaction —
-- after that it is evidence: no update, no delete, a void marks the PAYMENT,
-- never the receipt (real-world: you can't un-issue a receipt).

CREATE TABLE public.payment_receipts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL
        REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    project_id UUID NOT NULL
        REFERENCES public.projects(id) ON DELETE RESTRICT,
    payment_id UUID NOT NULL
        REFERENCES public.project_payments(id) ON DELETE RESTRICT,
    receipt_code VARCHAR(30) NOT NULL,
    payload_json JSONB NOT NULL,
    storage_bucket TEXT NOT NULL CHECK (storage_bucket = 'documents'),
    storage_object_key TEXT NOT NULL,
    file_sha256 TEXT NOT NULL CHECK (file_sha256 ~ '^[0-9a-f]{64}$'),
    media_type TEXT NOT NULL CHECK (media_type = 'application/pdf'),
    byte_size BIGINT NOT NULL CHECK (byte_size > 0),
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_payment_receipt UNIQUE (payment_id),
    CONSTRAINT uk_org_receipt_code UNIQUE (org_id, receipt_code)
);

CREATE INDEX idx_payment_receipts_project
    ON public.payment_receipts (org_id, project_id);

ALTER TABLE public.payment_receipts ENABLE ROW LEVEL SECURITY;

-- Tenants read the registry; only the backend role writes it, and only
-- INSERT — the grant set is what makes a receipt sealed evidence.
CREATE POLICY payment_receipts_read ON public.payment_receipts
    FOR SELECT TO authenticated
    USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY payment_receipts_backend ON public.payment_receipts
    FOR ALL TO documentary_backend
    USING (org_id IN (SELECT private.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT private.current_user_org_ids()));

GRANT SELECT ON public.payment_receipts TO authenticated;
GRANT SELECT, INSERT ON public.payment_receipts TO documentary_backend;
GRANT ALL ON public.payment_receipts TO service_role;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER
    ON public.payment_receipts FROM authenticated;
REVOKE ALL ON public.payment_receipts FROM anon;
