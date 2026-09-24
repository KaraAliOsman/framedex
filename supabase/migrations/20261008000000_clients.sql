-- Client registry: one org-scoped record per customer so project headers
-- stop re-typing contact data. Projects keep their own client_* fields as the
-- address-of-record snapshot (documents seal those, never the live row); the
-- link only prevents drift on reuse and powers the picker.

CREATE TABLE public.clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL
        REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    rut VARCHAR(50),
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    notes TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_org_client_rut UNIQUE (org_id, rut)
);

ALTER TABLE public.projects
    ADD COLUMN client_id UUID
        REFERENCES public.clients(id) ON DELETE SET NULL;
CREATE INDEX idx_projects_client
    ON public.projects (org_id, client_id) WHERE client_id IS NOT NULL;

ALTER TABLE public.clients ENABLE ROW LEVEL SECURITY;

CREATE POLICY clients_isolation ON public.clients
    FOR ALL
    USING (org_id IN (SELECT private.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT private.current_user_org_ids()));

GRANT SELECT, INSERT, UPDATE, DELETE ON public.clients TO authenticated;
REVOKE ALL ON public.clients FROM anon;
