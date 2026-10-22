BEGIN;

-- Mutable working projection. It never grants commercial APPLIED authority.
CREATE TABLE public.project_working_prices (
  org_id uuid NOT NULL,
  project_id uuid NOT NULL,
  revision_code text NOT NULL CHECK(revision_code ~ '^REV-[A-Z]+$'),
  policy_revision bigint NOT NULL CHECK(policy_revision>=0),
  source_revision text NOT NULL,
  effective_date date NOT NULL,
  currency public.currency_code NOT NULL,
  state text NOT NULL CHECK(state IN ('READY','BLOCKED','PENDING')),
  request jsonb NOT NULL CHECK(jsonb_typeof(request)='object'),
  input_snapshot jsonb NOT NULL CHECK(jsonb_typeof(input_snapshot)='object'),
  result jsonb NOT NULL CHECK(jsonb_typeof(result)='object'),
  computed_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  PRIMARY KEY(project_id,revision_code),
  FOREIGN KEY(project_id,org_id) REFERENCES public.projects(id,org_id) ON DELETE CASCADE
);
ALTER TABLE public.project_working_prices ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.project_working_prices FROM PUBLIC,anon,authenticated;
GRANT SELECT,INSERT,UPDATE ON public.project_working_prices TO pricing_backend;
CREATE POLICY working_price_read ON public.project_working_prices FOR SELECT TO pricing_backend
  USING(org_id IN(SELECT private.pricing_read_org_ids()));
CREATE POLICY working_price_write ON public.project_working_prices FOR ALL TO pricing_backend
  USING(private.pricing_role(org_id,ARRAY['OWNER','ESTIMATOR']))
  WITH CHECK(private.pricing_role(org_id,ARRAY['OWNER','ESTIMATOR']));

CREATE FUNCTION private.guard_working_price() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
BEGIN
  IF TG_OP='UPDATE' AND (NEW.org_id,NEW.project_id,NEW.revision_code)
    IS DISTINCT FROM (OLD.org_id,OLD.project_id,OLD.revision_code) THEN
    RAISE EXCEPTION 'working_price_identity_immutable' USING ERRCODE='23514';
  END IF;
  PERFORM 1 FROM public.projects p WHERE p.id=NEW.project_id AND p.org_id=NEW.org_id
    AND p.current_revision=NEW.revision_code AND p.status='DRAFT' FOR UPDATE;
  IF NOT FOUND OR EXISTS(SELECT 1 FROM public.project_versions v WHERE v.project_id=NEW.project_id
    AND v.org_id=NEW.org_id AND v.revision_code=NEW.revision_code) OR EXISTS(
      SELECT 1 FROM public.pricing_operations operation JOIN public.projects p ON p.id=operation.project_id
      WHERE operation.project_id=NEW.project_id AND operation.org_id=NEW.org_id
        AND coalesce(operation.revision_code,'REV-A')=NEW.revision_code AND operation.state='APPLIED'
        AND (p.pricing_reset_at IS NULL OR operation.approved_at>p.pricing_reset_at)) THEN
    RAISE EXCEPTION 'working_price_requires_editable_draft' USING ERRCODE='23514';
  END IF;
  NEW.computed_at := clock_timestamp();
  RETURN NEW;
END; $$;
REVOKE ALL ON FUNCTION private.guard_working_price() FROM PUBLIC;
CREATE TRIGGER working_price_guard BEFORE INSERT OR UPDATE ON public.project_working_prices
  FOR EACH ROW EXECUTE FUNCTION private.guard_working_price();

COMMIT;
