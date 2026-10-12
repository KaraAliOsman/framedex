-- Guided issuance stores a private review before any public capability exists.
CREATE TABLE public.quotation_previews (
  id uuid PRIMARY KEY,
  org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id),
  project_id uuid NOT NULL REFERENCES public.projects(id),
  pricing_operation_id uuid NOT NULL REFERENCES public.pricing_operations(id),
  created_by uuid NOT NULL,
  revision_code text NOT NULL CHECK (revision_code ~ '^REV-[A-Z]+$'),
  snapshot_json jsonb NOT NULL CHECK (jsonb_typeof(snapshot_json)='object'),
  snapshot_sha256 char(64) NOT NULL CHECK (snapshot_sha256 ~ '^[0-9a-f]{64}$'),
  bom_hash char(64) NOT NULL CHECK (bom_hash ~ '^[0-9a-f]{64}$'),
  storage_object_key text NOT NULL,
  file_sha256 char(64) NOT NULL CHECK (file_sha256 ~ '^[0-9a-f]{64}$'),
  byte_size bigint NOT NULL CHECK (byte_size>0),
  token_ciphertext text NOT NULL,
  document_date timestamptz NOT NULL,
  expires_at timestamptz NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (expires_at>document_date)
);
CREATE TABLE public.quotation_issues (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id),
  project_id uuid NOT NULL REFERENCES public.projects(id),
  preview_id uuid NOT NULL UNIQUE REFERENCES public.quotation_previews(id),
  project_version_id uuid NOT NULL UNIQUE REFERENCES public.project_versions(id),
  artifact_id uuid NOT NULL UNIQUE REFERENCES public.document_artifacts(id),
  approval_id uuid NOT NULL UNIQUE REFERENCES public.customer_approvals(id),
  mail_id uuid NOT NULL UNIQUE REFERENCES public.mail_outbox(id),
  created_by uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- An access deadline is a projection over immutable DOCUMENT identity. Never
-- alter its original expires_at, token, sealed snapshot or PDF bytes.
CREATE TABLE public.quote_link_deadlines (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id),
  project_id uuid NOT NULL REFERENCES public.projects(id),
  approval_id uuid NOT NULL REFERENCES public.customer_approvals(id),
  expires_at timestamptz NOT NULL,
  created_by uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX quote_link_deadlines_latest ON public.quote_link_deadlines(org_id,approval_id,id DESC);
CREATE TABLE public.quote_link_regenerations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id),
  project_id uuid NOT NULL REFERENCES public.projects(id),
  source_approval_id uuid NOT NULL UNIQUE REFERENCES public.customer_approvals(id),
  approval_id uuid NOT NULL UNIQUE REFERENCES public.customer_approvals(id),
  token_ciphertext text NOT NULL,
  created_by uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.quotation_previews ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.quotation_issues ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.quote_link_deadlines ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.quote_link_regenerations ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.quotation_previews, public.quotation_issues,
  public.quote_link_deadlines, public.quote_link_regenerations FROM anon, authenticated, portal_backend;
GRANT SELECT, INSERT ON public.quotation_previews, public.quotation_issues,
  public.quote_link_deadlines, public.quote_link_regenerations TO documentary_backend;
GRANT USAGE ON SEQUENCE public.quote_link_deadlines_id_seq TO documentary_backend;
CREATE POLICY quotation_previews_writer ON public.quotation_previews TO documentary_backend
  USING (private.documentary_role(org_id,ARRAY['OWNER','ESTIMATOR']) AND created_by=auth.uid())
  WITH CHECK (private.documentary_role(org_id,ARRAY['OWNER','ESTIMATOR']) AND created_by=auth.uid());
CREATE POLICY quotation_issues_writer ON public.quotation_issues TO documentary_backend
  USING (private.documentary_role(org_id,ARRAY['OWNER','ESTIMATOR']))
  WITH CHECK (private.documentary_role(org_id,ARRAY['OWNER','ESTIMATOR']) AND created_by=auth.uid());
CREATE POLICY quote_link_deadlines_writer ON public.quote_link_deadlines TO documentary_backend
  USING (private.documentary_role(org_id,ARRAY['OWNER','ESTIMATOR','WORKSHOP_MANAGER']))
  WITH CHECK (private.documentary_role(org_id,ARRAY['OWNER','ESTIMATOR']) AND created_by=auth.uid());
CREATE POLICY quote_link_regenerations_writer ON public.quote_link_regenerations TO documentary_backend
  USING (private.documentary_role(org_id,ARRAY['OWNER','ESTIMATOR']))
  WITH CHECK (private.documentary_role(org_id,ARRAY['OWNER','ESTIMATOR']) AND created_by=auth.uid());
GRANT SELECT ON public.quote_link_deadlines TO portal_backend, service_role;
CREATE POLICY quote_link_deadlines_portal ON public.quote_link_deadlines FOR SELECT TO portal_backend
  USING (org_id=NULLIF(current_setting('app.portal_org_id',true),'')::uuid);
CREATE POLICY quote_link_deadlines_service ON public.quote_link_deadlines FOR SELECT TO service_role
  USING (auth.jwt()->>'role'='service_role');

CREATE FUNCTION private.quote_link_expires_at(target uuid, tenant uuid, original timestamptz)
RETURNS timestamptz LANGUAGE sql STABLE SECURITY INVOKER SET search_path='' AS $$
  SELECT COALESCE((SELECT d.expires_at FROM public.quote_link_deadlines d
    WHERE d.approval_id=target AND d.org_id=tenant ORDER BY d.id DESC LIMIT 1),original);
$$;
REVOKE ALL ON FUNCTION private.quote_link_expires_at(uuid,uuid,timestamptz) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.quote_link_expires_at(uuid,uuid,timestamptz)
  TO documentary_backend,portal_backend,service_role;

CREATE FUNCTION private.guard_quotation_review() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'quotation_review_immutable'; END IF;
  IF NEW.snapshot_json->>'org_id' IS DISTINCT FROM NEW.org_id::text
    OR NEW.snapshot_json->>'project_id' IS DISTINCT FROM NEW.project_id::text
    OR NEW.snapshot_json->>'sealed_by' IS DISTINCT FROM NEW.created_by::text
    OR NEW.snapshot_json->>'revision' IS DISTINCT FROM NEW.revision_code
    OR NOT EXISTS (SELECT 1 FROM public.projects WHERE id=NEW.project_id AND org_id=NEW.org_id)
    OR NOT EXISTS (SELECT 1 FROM public.pricing_operations WHERE id=NEW.pricing_operation_id
      AND project_id=NEW.project_id AND org_id=NEW.org_id)
  THEN RAISE EXCEPTION 'quotation_review_scope_mismatch'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER quotation_review_immutable BEFORE INSERT OR UPDATE OR DELETE ON public.quotation_previews
  FOR EACH ROW EXECUTE FUNCTION private.guard_quotation_review();
CREATE FUNCTION private.guard_quotation_issue() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'quotation_issue_immutable'; END IF;
  IF NOT EXISTS (SELECT 1 FROM public.quotation_previews q
    JOIN public.project_versions v ON v.id=NEW.project_version_id AND v.org_id=q.org_id AND v.project_id=q.project_id
    JOIN public.document_artifacts d ON d.id=NEW.artifact_id AND d.project_version_id=v.id AND d.org_id=v.org_id
    JOIN public.customer_approvals a ON a.id=NEW.approval_id AND a.project_version_id=v.id AND a.org_id=v.org_id
    JOIN public.mail_outbox m ON m.id=NEW.mail_id AND m.org_id=v.org_id AND m.project_id=v.project_id
    WHERE q.id=NEW.preview_id AND q.org_id=NEW.org_id AND q.project_id=NEW.project_id AND q.created_by=NEW.created_by
      AND v.snapshot_sha256=q.snapshot_sha256 AND v.revision_code=q.revision_code
      AND d.file_sha256=q.file_sha256 AND d.document_type='DOC-01' AND d.format='PDF' AND a.link_source='DOCUMENT'
      AND m.kind='QUOTE' AND m.event_key='quote:'||q.id::text AND m.recipient=q.snapshot_json->'project'->>'client_email')
  THEN RAISE EXCEPTION 'quotation_issue_scope_mismatch'; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER quotation_issue_immutable BEFORE INSERT OR UPDATE OR DELETE ON public.quotation_issues
  FOR EACH ROW EXECUTE FUNCTION private.guard_quotation_issue();
CREATE FUNCTION private.guard_quote_link_control() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'quote_link_control_immutable'; END IF;
  IF NOT EXISTS (SELECT 1 FROM public.customer_approvals a WHERE a.id=NEW.approval_id
    AND a.org_id=NEW.org_id AND a.project_id=NEW.project_id)
  THEN RAISE EXCEPTION 'quote_link_control_scope_mismatch'; END IF;
  IF TG_TABLE_NAME='quote_link_regenerations' THEN
    IF NOT EXISTS (
    SELECT 1 FROM public.customer_approvals prior_link JOIN public.customer_approvals fresh
      ON fresh.id=NEW.approval_id AND fresh.org_id=prior_link.org_id AND fresh.project_id=prior_link.project_id
        AND fresh.project_version_id=prior_link.project_version_id
    WHERE prior_link.id=NEW.source_approval_id AND prior_link.org_id=NEW.org_id AND prior_link.status='REVOKED' AND fresh.link_source='SHARE')
    THEN RAISE EXCEPTION 'quote_link_control_scope_mismatch'; END IF;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER quote_link_deadlines_immutable BEFORE INSERT OR UPDATE OR DELETE ON public.quote_link_deadlines
  FOR EACH ROW EXECUTE FUNCTION private.guard_quote_link_control();
CREATE TRIGGER quote_link_regenerations_immutable BEFORE INSERT OR UPDATE OR DELETE ON public.quote_link_regenerations
  FOR EACH ROW EXECUTE FUNCTION private.guard_quote_link_control();
