-- Customer approval links: a sealed revision can be shared with the client
-- through a single-use-capable public token; the token IS the capability.
-- Append-only on top of 20260923210000_analytics_read_grants.sql.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'portal_backend') THEN
        CREATE ROLE portal_backend NOLOGIN NOSUPERUSER NOBYPASSRLS;
    END IF;
END $$;

GRANT portal_backend TO postgres;

GRANT USAGE ON SCHEMA public, private TO portal_backend;

CREATE TABLE public.customer_approvals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL
        REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    project_id UUID NOT NULL
        REFERENCES public.projects(id) ON DELETE CASCADE,
    project_version_id UUID NOT NULL
        REFERENCES public.project_versions(id) ON DELETE CASCADE,
    token_hash CHAR(64) NOT NULL UNIQUE CHECK (token_hash ~ '^[0-9a-f]{64}$'),
    status VARCHAR(10) NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING', 'APPROVED', 'DECLINED')),
    decided_by VARCHAR(255),
    decided_at TIMESTAMPTZ,
    decided_note VARCHAR(500),
    expires_at TIMESTAMPTZ NOT NULL,
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_customer_approvals_project
    ON public.customer_approvals (org_id, project_id);

ALTER TABLE public.customer_approvals ENABLE ROW LEVEL SECURITY;

-- Tenant members read their org's approvals; every write flows through the
-- backend role (API role checks decide who may share or decide — the DB
-- layer only enforces tenancy).
CREATE POLICY customer_approvals_read ON public.customer_approvals
    FOR SELECT TO authenticated
    USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY customer_approvals_backend ON public.customer_approvals
    FOR ALL TO documentary_backend
    USING (org_id IN (SELECT private.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT private.current_user_org_ids()));

-- Public portal path: the share token IS the capability. portal_backend
-- carries no JWT, so current_user_org_ids() is empty — the service joins
-- every read/write to the token row's own org_id instead.
CREATE POLICY customer_approvals_portal ON public.customer_approvals
    FOR ALL TO portal_backend USING (true) WITH CHECK (true);
CREATE POLICY projects_portal_read ON public.projects
    FOR SELECT TO portal_backend USING (true);
CREATE POLICY projects_portal_decide ON public.projects
    FOR UPDATE TO portal_backend USING (true) WITH CHECK (true);
CREATE POLICY project_versions_portal_read ON public.project_versions
    FOR SELECT TO portal_backend USING (true);
CREATE POLICY document_artifacts_portal_read ON public.document_artifacts
    FOR SELECT TO portal_backend USING (true);

GRANT SELECT ON public.customer_approvals TO authenticated;
GRANT ALL ON public.customer_approvals TO documentary_backend;
GRANT ALL ON public.customer_approvals TO portal_backend;
GRANT SELECT, UPDATE ON public.projects TO portal_backend;
GRANT SELECT ON public.project_versions TO portal_backend;
GRANT SELECT ON public.document_artifacts TO portal_backend;
GRANT ALL ON public.customer_approvals TO service_role;

-- Supabase default privileges hand authenticated every privilege on a new
-- table; approvals may only be written through the backend roles.
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER
    ON public.customer_approvals FROM authenticated;
REVOKE ALL ON public.customer_approvals FROM anon;
