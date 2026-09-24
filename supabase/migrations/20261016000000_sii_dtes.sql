-- SII electronic invoicing (DTE): the CAF registry (folios authorized by the
-- Servicio de Impuestos Internos) and the sealed DTE artifacts emitted from
-- project facturas. A CAF is a folio pool — folio_actual is a cursor the
-- backend advances under an org advisory lock, so it is the one registry in
-- the documentary family that legitimately mutates; the emitted DTE rows are
-- sealed evidence like every other document.

CREATE TABLE public.sii_cafs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL
        REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    tipo_dte INTEGER NOT NULL CHECK (tipo_dte > 0),
    folio_desde INTEGER NOT NULL CHECK (folio_desde >= 1),
    folio_hasta INTEGER NOT NULL,
    -- Cursor initialized to folio_desde-1 at registration; the backend
    -- advances it under the org folio advisory lock before each timbraje.
    folio_actual INTEGER NOT NULL,
    rut_emisor VARCHAR(20) NOT NULL,
    razon_social TEXT NOT NULL,
    giro_emis TEXT,
    dir_origen TEXT,
    cmna_origen TEXT,
    caf_xml TEXT NOT NULL,
    rsask TEXT NOT NULL,
    rsapk_m TEXT NOT NULL,
    rsapk_e TEXT NOT NULL,
    file_sha256 TEXT NOT NULL CHECK (file_sha256 ~ '^[0-9a-f]{64}$'),
    uploaded_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_org_caf_range UNIQUE (org_id, tipo_dte, folio_desde),
    CONSTRAINT ck_caf_range CHECK (folio_desde <= folio_hasta),
    CONSTRAINT ck_caf_cursor CHECK (folio_actual >= folio_desde - 1 AND folio_actual <= folio_hasta)
);

CREATE INDEX idx_sii_cafs_org_tipo
    ON public.sii_cafs (org_id, tipo_dte, folio_desde);

CREATE TABLE public.project_dtes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL
        REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    project_id UUID NOT NULL
        REFERENCES public.projects(id) ON DELETE RESTRICT,
    invoice_id UUID NOT NULL
        REFERENCES public.project_invoices(id) ON DELETE RESTRICT,
    caf_id UUID NOT NULL
        REFERENCES public.sii_cafs(id) ON DELETE RESTRICT,
    dte_type INTEGER NOT NULL,
    folio INTEGER NOT NULL,
    payload_json JSONB NOT NULL,
    storage_bucket TEXT NOT NULL CHECK (storage_bucket = 'documents'),
    storage_object_key TEXT NOT NULL,
    file_sha256 TEXT NOT NULL CHECK (file_sha256 ~ '^[0-9a-f]{64}$'),
    media_type TEXT NOT NULL CHECK (media_type = 'application/xml'),
    byte_size BIGINT NOT NULL CHECK (byte_size > 0),
    issued_by UUID NOT NULL,
    issued_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_org_invoice_dte UNIQUE (org_id, invoice_id),
    CONSTRAINT uk_org_dte_folio UNIQUE (org_id, dte_type, folio)
);

CREATE INDEX idx_project_dtes_invoice
    ON public.project_dtes (org_id, invoice_id);
CREATE INDEX idx_project_dtes_project
    ON public.project_dtes (org_id, project_id);

ALTER TABLE public.sii_cafs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.project_dtes ENABLE ROW LEVEL SECURITY;

-- Tenants may read the folio pool and the emitted DTEs; only the backend
-- role writes. The CAF registry gets UPDATE solely for the folio cursor
-- (the pool is state, not evidence); DTEs get INSERT only — a sealed
-- artifact is never updated or deleted.
CREATE POLICY sii_cafs_read ON public.sii_cafs
    FOR SELECT TO authenticated
    USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY sii_cafs_backend ON public.sii_cafs
    FOR ALL TO documentary_backend
    USING (org_id IN (SELECT private.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT private.current_user_org_ids()));

CREATE POLICY project_dtes_read ON public.project_dtes
    FOR SELECT TO authenticated
    USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY project_dtes_backend ON public.project_dtes
    FOR ALL TO documentary_backend
    USING (org_id IN (SELECT private.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT private.current_user_org_ids()));

GRANT SELECT ON public.sii_cafs TO authenticated;
GRANT SELECT, INSERT, UPDATE ON public.sii_cafs TO documentary_backend;
GRANT ALL ON public.sii_cafs TO service_role;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER
    ON public.sii_cafs FROM authenticated;
REVOKE ALL ON public.sii_cafs FROM anon;

GRANT SELECT ON public.project_dtes TO authenticated;
GRANT SELECT, INSERT ON public.project_dtes TO documentary_backend;
GRANT ALL ON public.project_dtes TO service_role;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER
    ON public.project_dtes FROM authenticated;
REVOKE ALL ON public.project_dtes FROM anon;
