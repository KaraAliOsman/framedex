-- Dispatch notes (guía de despacho): a sealed, immutable shipping document
-- per work order. Written once inside dispatch_work_order's transaction —
-- after that it is evidence: no update, no delete. A replayed dispatch finds
-- the existing note via UNIQUE (work_order_id) and never re-renders.

CREATE TABLE public.dispatch_notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL
        REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    project_id UUID NOT NULL
        REFERENCES public.projects(id) ON DELETE RESTRICT,
    work_order_id UUID NOT NULL
        REFERENCES public.orders(id) ON DELETE RESTRICT,
    note_code VARCHAR(30) NOT NULL,
    payload_json JSONB NOT NULL,
    storage_bucket TEXT NOT NULL CHECK (storage_bucket = 'documents'),
    storage_object_key TEXT NOT NULL,
    file_sha256 TEXT NOT NULL CHECK (file_sha256 ~ '^[0-9a-f]{64}$'),
    media_type TEXT NOT NULL CHECK (media_type = 'application/pdf'),
    byte_size BIGINT NOT NULL CHECK (byte_size > 0),
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_dispatch_note UNIQUE (work_order_id),
    CONSTRAINT uk_org_dispatch_note_code UNIQUE (org_id, note_code)
);

CREATE INDEX idx_dispatch_notes_project
    ON public.dispatch_notes (org_id, project_id);

ALTER TABLE public.dispatch_notes ENABLE ROW LEVEL SECURITY;

-- Tenants read the registry; only the backend role writes it, and only
-- INSERT — the grant set is what makes a note sealed evidence.
CREATE POLICY dispatch_notes_read ON public.dispatch_notes
    FOR SELECT TO authenticated
    USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY dispatch_notes_backend ON public.dispatch_notes
    FOR ALL TO documentary_backend
    USING (org_id IN (SELECT private.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT private.current_user_org_ids()));

GRANT SELECT ON public.dispatch_notes TO authenticated;
GRANT SELECT, INSERT ON public.dispatch_notes TO documentary_backend;
GRANT ALL ON public.dispatch_notes TO service_role;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER
    ON public.dispatch_notes FROM authenticated;
REVOKE ALL ON public.dispatch_notes FROM anon;
