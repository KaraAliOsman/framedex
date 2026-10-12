-- Read-only historical authority: defaults affect only new declarations.
ALTER TABLE public.project_positions ALTER COLUMN location_tag TYPE varchar(120);
ALTER TABLE public.tenancy_organizations
  ADD COLUMN document_preferences jsonb NOT NULL DEFAULT '{}'::jsonb
  CHECK (jsonb_typeof(document_preferences)='object');
GRANT SELECT (document_preferences) ON public.tenancy_organizations TO authenticated, documentary_backend;
GRANT UPDATE (document_preferences) ON public.tenancy_organizations TO documentary_backend;
ALTER TABLE public.project_documentary_inputs
  ADD COLUMN commercial_terms jsonb NOT NULL DEFAULT '{}'::jsonb
  CHECK (jsonb_typeof(commercial_terms)='object');

-- A PDF owns one revocable portal approval. Re-sharing does not silently
-- revoke the printed QR; both links are listed and individually revocable.
ALTER TABLE public.customer_approvals
  ADD COLUMN link_source text NOT NULL DEFAULT 'SHARE'
  CHECK (link_source IN ('SHARE','DOCUMENT'));
CREATE UNIQUE INDEX one_document_approval_per_revision ON public.customer_approvals(org_id, project_version_id)
  WHERE link_source='DOCUMENT';
CREATE TABLE public.document_portal_links (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id),
  project_version_id uuid NOT NULL REFERENCES public.project_versions(id),
  approval_id uuid NOT NULL UNIQUE REFERENCES public.customer_approvals(id),
  token_ciphertext text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(org_id,project_version_id)
);
ALTER TABLE public.document_portal_links ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.document_portal_links FROM anon, authenticated, portal_backend;
GRANT SELECT, INSERT ON public.document_portal_links TO documentary_backend;
GRANT SELECT, INSERT ON public.document_portal_links TO service_role;
CREATE POLICY document_link_backend ON public.document_portal_links TO documentary_backend
  USING (org_id IN (SELECT private.current_user_org_ids()))
  WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER','ESTIMATOR']));
CREATE POLICY document_link_service ON public.document_portal_links TO service_role
  USING (auth.jwt()->>'role'='service_role') WITH CHECK (auth.jwt()->>'role'='service_role');
CREATE FUNCTION private.guard_document_portal_link() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'document_portal_link_immutable'; END IF;
  IF NOT EXISTS (SELECT 1 FROM public.customer_approvals a
    JOIN public.project_versions v ON v.id=a.project_version_id AND v.org_id=a.org_id AND v.project_id=a.project_id
    WHERE a.id=NEW.approval_id AND a.org_id=NEW.org_id AND a.project_version_id=NEW.project_version_id
      AND a.link_source='DOCUMENT') THEN RAISE EXCEPTION 'document_portal_link_scope_mismatch'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER document_portal_link_authority BEFORE INSERT OR UPDATE OR DELETE ON public.document_portal_links
  FOR EACH ROW EXECUTE FUNCTION private.guard_document_portal_link();
