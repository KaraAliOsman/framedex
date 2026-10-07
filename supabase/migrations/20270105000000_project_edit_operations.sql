-- IA2: human-applied, reversible project edits. The model only simulates.
BEGIN;
CREATE TABLE public.project_edit_operations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
  project_id UUID NOT NULL,
  actor_id UUID NOT NULL,
  operation_key TEXT NOT NULL CHECK(length(operation_key) BETWEEN 8 AND 120),
  state TEXT NOT NULL CHECK(state IN ('APPLIED','UNDONE')),
  request JSONB NOT NULL CHECK(jsonb_typeof(request)='array'),
  before_state JSONB NOT NULL CHECK(jsonb_typeof(before_state)='object'),
  after_state JSONB NOT NULL CHECK(jsonb_typeof(after_state)='object'),
  created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
  undone_at TIMESTAMPTZ,
  FOREIGN KEY(project_id,org_id) REFERENCES public.projects(id,org_id) ON DELETE RESTRICT,
  UNIQUE(org_id,project_id,operation_key),
  CHECK((state='APPLIED' AND undone_at IS NULL) OR (state='UNDONE' AND undone_at IS NOT NULL))
);
ALTER TABLE public.project_edit_operations ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.project_edit_operations FROM anon,authenticated;
GRANT SELECT,INSERT,UPDATE ON public.project_edit_operations TO pricing_backend;
GRANT ALL ON public.project_edit_operations TO service_role;
CREATE POLICY project_edit_read ON public.project_edit_operations FOR SELECT TO pricing_backend
  USING(private.documentary_role(org_id,ARRAY['OWNER','ESTIMATOR']));
CREATE POLICY project_edit_insert ON public.project_edit_operations FOR INSERT TO pricing_backend
  WITH CHECK(private.documentary_role(org_id,ARRAY['OWNER','ESTIMATOR']) AND
    actor_id=(current_setting('request.jwt.claims',true)::jsonb->>'sub')::UUID);
CREATE POLICY project_edit_update ON public.project_edit_operations FOR UPDATE TO pricing_backend
  USING(private.documentary_role(org_id,ARRAY['OWNER','ESTIMATOR']))
  WITH CHECK(private.documentary_role(org_id,ARRAY['OWNER','ESTIMATOR']));
CREATE FUNCTION private.guard_project_edit_evidence() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path=pg_catalog,public,private AS $$
BEGIN
  IF OLD.state<>'APPLIED' OR NEW.state<>'UNDONE' OR NEW.undone_at IS NULL OR
     (to_jsonb(OLD)-'state'-'undone_at') IS DISTINCT FROM (to_jsonb(NEW)-'state'-'undone_at') THEN
    RAISE EXCEPTION 'project_edit_evidence_immutable' USING ERRCODE='23514';
  END IF;
  RETURN NEW;
END; $$;
CREATE TRIGGER project_edit_evidence BEFORE UPDATE ON public.project_edit_operations
  FOR EACH ROW EXECUTE FUNCTION private.guard_project_edit_evidence();
COMMIT;
