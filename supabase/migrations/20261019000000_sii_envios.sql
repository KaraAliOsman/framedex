-- SII envío: a stamped DTE only becomes a real tax document when it is
-- submitted to the SII inside a signed <EnvioDTE> envelope. Two tables:
--
-- * sii_certificates — the organization's digital certificate (.pfx). The
--   envío signature is made by this cert, a different key from the CAF's
--   RSASK; the blob is wrapped with the deployment KEK like the CAF keys.
--   At most one active certificate per org.
-- * sii_envios — one sealed envío per DTE. The payload/carátula envelope
--   is immutable evidence; status/track_id/glosa are the SII-side
--   lifecycle and legitimately mutate (PENDING → ACCEPTED/REJECTED),
--   backend-only like the CAF folio cursor.

CREATE TABLE public.sii_certificates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    subject TEXT NOT NULL,
    rut_firma TEXT NOT NULL,
    serial_number TEXT,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL,
    pfx_wrapped TEXT NOT NULL,
    password_wrapped TEXT,
    file_sha256 TEXT NOT NULL CHECK (file_sha256 ~ '^[0-9a-f]{64}$'),
    nro_resol INTEGER NOT NULL CHECK (nro_resol >= 0),
    fch_resol DATE NOT NULL,
    active BOOLEAN NOT NULL DEFAULT true,
    uploaded_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX uk_sii_cert_active
    ON public.sii_certificates (org_id) WHERE active;

CREATE TABLE public.sii_envios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
    dte_id UUID NOT NULL REFERENCES public.project_dtes(id) ON DELETE RESTRICT,
    status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING', 'ACCEPTED', 'REJECTED')),
    track_id TEXT,
    glosa TEXT,
    payload_json JSONB NOT NULL,
    storage_bucket TEXT NOT NULL DEFAULT 'documents'
        CHECK (storage_bucket = 'documents'),
    storage_object_key TEXT NOT NULL,
    file_sha256 TEXT NOT NULL CHECK (file_sha256 ~ '^[0-9a-f]{64}$'),
    media_type TEXT NOT NULL DEFAULT 'application/xml'
        CHECK (media_type = 'application/xml'),
    byte_size INTEGER NOT NULL CHECK (byte_size > 0),
    sent_by UUID NOT NULL,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uk_org_dte_envio UNIQUE (org_id, dte_id)
);

CREATE INDEX idx_sii_envios_project
    ON public.sii_envios (org_id, project_id);

ALTER TABLE public.sii_certificates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sii_envios ENABLE ROW LEVEL SECURITY;

CREATE POLICY sii_certificates_read ON public.sii_certificates
    FOR SELECT TO authenticated
    USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY sii_certificates_backend ON public.sii_certificates
    FOR ALL TO documentary_backend
    USING (org_id IN (SELECT private.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT private.current_user_org_ids()));

CREATE POLICY sii_envios_read ON public.sii_envios
    FOR SELECT TO authenticated
    USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY sii_envios_backend ON public.sii_envios
    FOR ALL TO documentary_backend
    USING (org_id IN (SELECT private.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT private.current_user_org_ids()));

-- Column-level tenant read: pfx_wrapped/password_wrapped are KEK ciphertexts
-- a member client must never see (offline-attack material) — grant only the
-- metadata columns; the backend role keeps whole-row access.
REVOKE ALL ON public.sii_certificates FROM anon, authenticated;
GRANT SELECT (id, org_id, subject, rut_firma, serial_number, valid_from,
    valid_to, file_sha256, nro_resol, fch_resol, active, uploaded_by, created_at)
    ON public.sii_certificates TO authenticated;
GRANT SELECT, INSERT, UPDATE ON public.sii_certificates TO documentary_backend;
GRANT ALL ON public.sii_certificates TO service_role;

REVOKE ALL ON public.sii_envios FROM anon, authenticated;
GRANT SELECT ON public.sii_envios TO authenticated;
GRANT SELECT, INSERT, UPDATE ON public.sii_envios TO documentary_backend;
GRANT ALL ON public.sii_envios TO service_role;
