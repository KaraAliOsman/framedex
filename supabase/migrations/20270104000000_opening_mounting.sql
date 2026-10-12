-- D07: append-only survey and confirmation evidence; no historical rewrites.
BEGIN;

CREATE TABLE public.mounting_rules (
  org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
  system_id UUID NOT NULL REFERENCES public.profile_systems(id) ON DELETE RESTRICT,
  code TEXT NOT NULL CHECK(code ~ '^[A-Z0-9_.-]+$'),
  revision INTEGER NOT NULL CHECK(revision>0),
  rule JSONB NOT NULL CHECK(jsonb_typeof(rule)='object' AND rule->>'code'=code),
  actor_id UUID NOT NULL,
  reason TEXT NOT NULL CHECK(length(btrim(reason))>0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
  PRIMARY KEY(org_id,system_id,code,revision)
);
ALTER TABLE public.mounting_rules ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.mounting_rules FROM anon,authenticated;
GRANT SELECT,INSERT ON public.mounting_rules TO pricing_backend;
GRANT SELECT ON public.mounting_rules TO documentary_backend;
GRANT ALL ON public.mounting_rules TO service_role;
CREATE POLICY mounting_rules_read ON public.mounting_rules FOR SELECT TO pricing_backend,documentary_backend
  USING(private.documentary_role(org_id,ARRAY['OWNER','ESTIMATOR','WORKSHOP_MANAGER']));
CREATE POLICY mounting_rules_write ON public.mounting_rules FOR INSERT TO pricing_backend
  WITH CHECK(private.documentary_role(org_id,ARRAY['OWNER','WORKSHOP_MANAGER']));
CREATE TRIGGER mounting_rules_immutable BEFORE UPDATE OR DELETE ON public.mounting_rules
  FOR EACH ROW EXECUTE FUNCTION private.reject_immutable_evidence();

CREATE TABLE public.position_measurements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
  project_id UUID NOT NULL,
  position_id UUID NOT NULL,
  revision_code TEXT NOT NULL CHECK(revision_code ~ '^REV-[A-Z]+$'),
  generation INTEGER NOT NULL CHECK(generation>0),
  measurements JSONB NOT NULL CHECK(jsonb_typeof(measurements)='array' AND jsonb_array_length(measurements)>0),
  binding TEXT NOT NULL CHECK(binding ~ '^[0-9a-f]{64}$'),
  state TEXT NOT NULL CHECK(state IN ('CUSTOMER','SITE','CONFIRMED')),
  price_change JSONB,
  actor_id UUID NOT NULL,
  reason TEXT NOT NULL CHECK(length(btrim(reason))>0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
  -- A removed draft position keeps its immutable measurement history.
  -- Its tenant/position association is verified by the INSERT trigger.
  CONSTRAINT position_measurements_project_fk FOREIGN KEY(project_id,org_id) REFERENCES public.projects(id,org_id) ON DELETE RESTRICT,
  UNIQUE(org_id,position_id,revision_code,generation)
);
ALTER TABLE public.position_measurements ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.position_measurements FROM anon,authenticated;
GRANT SELECT,INSERT ON public.position_measurements TO pricing_backend;
GRANT SELECT ON public.position_measurements TO documentary_backend;
GRANT ALL ON public.position_measurements TO service_role;
CREATE POLICY position_measurements_read ON public.position_measurements FOR SELECT TO pricing_backend,documentary_backend
  USING(private.documentary_role(org_id,ARRAY['OWNER','ESTIMATOR','WORKSHOP_MANAGER']));
CREATE POLICY position_measurements_write ON public.position_measurements FOR INSERT TO pricing_backend
  WITH CHECK(private.documentary_role(org_id,ARRAY['OWNER','ESTIMATOR','WORKSHOP_MANAGER']));
CREATE TRIGGER position_measurements_immutable BEFORE UPDATE OR DELETE ON public.position_measurements
  FOR EACH ROW EXECUTE FUNCTION private.reject_immutable_evidence();

CREATE FUNCTION private.guard_position_measurement() RETURNS TRIGGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public,private AS $$
DECLARE p RECORD;
BEGIN
  IF NOT private.documentary_role(NEW.org_id,ARRAY['OWNER','ESTIMATOR','WORKSHOP_MANAGER'])
    OR NEW.actor_id IS DISTINCT FROM (current_setting('request.jwt.claims',true)::jsonb->>'sub')::UUID THEN
    RAISE EXCEPTION 'measurement_actor_invalid' USING ERRCODE='23514';
  END IF;
  IF NOT EXISTS(SELECT 1 FROM public.project_positions WHERE id=NEW.position_id
    AND project_id=NEW.project_id AND org_id=NEW.org_id) THEN
    RAISE EXCEPTION 'measurement_position_invalid' USING ERRCODE='23514';
  END IF;
  SELECT current_revision,status INTO p FROM public.projects
    WHERE id=NEW.project_id AND org_id=NEW.org_id FOR UPDATE;
  IF p.current_revision IS DISTINCT FROM NEW.revision_code OR p.status IS DISTINCT FROM 'DRAFT'
    OR EXISTS(SELECT 1 FROM public.project_versions WHERE project_id=NEW.project_id
      AND org_id=NEW.org_id AND revision_code=NEW.revision_code) THEN
    RAISE EXCEPTION 'measurement_revision_closed' USING ERRCODE='23514';
  END IF;
  IF NEW.generation<>(SELECT COALESCE(MAX(generation),0)+1 FROM public.position_measurements
    WHERE org_id=NEW.org_id AND position_id=NEW.position_id AND revision_code=NEW.revision_code) THEN
    RAISE EXCEPTION 'measurement_generation_invalid' USING ERRCODE='23514';
  END IF;
  RETURN NEW;
END; $$;
REVOKE ALL ON FUNCTION private.guard_position_measurement() FROM PUBLIC;
CREATE TRIGGER position_measurement_revision BEFORE INSERT ON public.position_measurements
  FOR EACH ROW EXECUTE FUNCTION private.guard_position_measurement();

CREATE FUNCTION private.guard_mounting_rule() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path=pg_catalog,public,private AS $$
DECLARE s JSONB; k TEXT;
BEGIN
  PERFORM pg_advisory_xact_lock(hashtextextended(NEW.org_id::TEXT||NEW.system_id::TEXT||NEW.code,0));
  IF NOT private.documentary_role(NEW.org_id,ARRAY['OWNER','WORKSHOP_MANAGER'])
    OR NEW.actor_id IS DISTINCT FROM (current_setting('request.jwt.claims',true)::jsonb->>'sub')::UUID THEN
    RAISE EXCEPTION 'mounting_actor_invalid' USING ERRCODE='23514';
  END IF;
  IF NEW.revision<>(SELECT COALESCE(MAX(revision),0)+1 FROM public.mounting_rules
    WHERE org_id=NEW.org_id AND system_id=NEW.system_id AND code=NEW.code) THEN
    RAISE EXCEPTION 'mounting_rule_revision_invalid' USING ERRCODE='23514';
  END IF;
  IF NOT EXISTS(SELECT 1 FROM public.profile_systems WHERE id=NEW.system_id AND (org_id IS NULL OR org_id=NEW.org_id)) THEN
    RAISE EXCEPTION 'mounting_system_tenant_mismatch' USING ERRCODE='23514';
  END IF;
  IF COALESCE(NEW.rule->>'kind','') NOT IN ('IN_OPENING','SUBFRAME','OVERLAP','RENOVATION')
    OR COALESCE(length(btrim(NEW.rule->>'source')),0)=0
    OR jsonb_typeof(NEW.rule->'synthetic') IS DISTINCT FROM 'boolean'
    OR jsonb_typeof(NEW.rule->'tolerance_mm') IS DISTINCT FROM 'string'
    OR (NEW.rule->>'tolerance_mm')::NUMERIC<0
    OR NEW.rule->>'tolerance_mm' IN ('NaN','Infinity','-Infinity')
    OR (NEW.rule->>'tolerance_mm')::NUMERIC<>round((NEW.rule->>'tolerance_mm')::NUMERIC,2)
    OR jsonb_typeof(NEW.rule->'extras') IS DISTINCT FROM 'array' THEN
    RAISE EXCEPTION 'mounting_rule_invalid' USING ERRCODE='23514';
  END IF;
  FOREACH k IN ARRAY ARRAY['left','right','top','bottom'] LOOP
    s:=NEW.rule->k;
    IF jsonb_typeof(s) IS DISTINCT FROM 'object' OR
      EXISTS(SELECT 1 FROM unnest(ARRAY['clearance_mm','frame_mm','extension_mm','overlap_mm']) f
        WHERE jsonb_typeof(s->f) IS DISTINCT FROM 'string' OR (s->>f)::NUMERIC<0
          OR s->>f IN ('NaN','Infinity','-Infinity')
          OR (s->>f)::NUMERIC<>round((s->>f)::NUMERIC,2)) THEN
      RAISE EXCEPTION 'mounting_allowance_invalid' USING ERRCODE='23514';
    END IF;
  END LOOP;
  RETURN NEW;
END; $$;
REVOKE ALL ON FUNCTION private.guard_mounting_rule() FROM PUBLIC;
CREATE TRIGGER mounting_rule_contract BEFORE INSERT ON public.mounting_rules
  FOR EACH ROW EXECUTE FUNCTION private.guard_mounting_rule();

-- Confirmation can lock the concurrency point without gaining project edits.
CREATE FUNCTION private.lock_measurement_target(p_org UUID,p_position UUID) RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public,private AS $$
DECLARE p_project UUID;
BEGIN
  IF NOT private.documentary_role(p_org,ARRAY['OWNER','ESTIMATOR','WORKSHOP_MANAGER']) THEN
    RAISE EXCEPTION 'measurement_actor_invalid' USING ERRCODE='23514';
  END IF;
  SELECT project_id INTO p_project FROM public.project_positions WHERE id=p_position AND org_id=p_org;
  IF p_project IS NULL THEN RETURN; END IF;
  PERFORM 1 FROM public.projects WHERE id=p_project AND org_id=p_org FOR UPDATE;
  PERFORM 1 FROM public.project_positions WHERE id=p_position AND org_id=p_org AND project_id=p_project FOR UPDATE;
END; $$;
REVOKE ALL ON FUNCTION private.lock_measurement_target(UUID,UUID) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.lock_measurement_target(UUID,UUID) TO pricing_backend;

CREATE FUNCTION private.guard_workshop_measurements() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path=pg_catalog,public,private AS $$
DECLARE s JSONB;
BEGIN
  IF NEW.order_type='WORKSHOP_OT' AND NEW.project_version_id IS NOT NULL THEN
    SELECT snapshot_json INTO s FROM public.project_versions WHERE id=NEW.project_version_id AND org_id=NEW.org_id;
    IF s->'measurements_required'='true'::JSONB AND
      (jsonb_array_length(s->'positions')=0 OR EXISTS(SELECT 1 FROM jsonb_array_elements(s->'positions') p
        WHERE p->'measurements'->>'state' IS DISTINCT FROM 'CONFIRMED'
          OR p->'measurements'->'current' IS DISTINCT FROM 'true'::JSONB)) THEN
      RAISE EXCEPTION 'production_measurements_unconfirmed' USING ERRCODE='23514';
    END IF;
  END IF;
  RETURN NEW;
END; $$;
REVOKE ALL ON FUNCTION private.guard_workshop_measurements() FROM PUBLIC;
CREATE TRIGGER workshop_measurements_gate BEFORE INSERT ON public.orders
  FOR EACH ROW EXECUTE FUNCTION private.guard_workshop_measurements();
COMMIT;
