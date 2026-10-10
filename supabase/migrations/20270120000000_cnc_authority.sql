-- P14: explicit machine authority and append-only history, preserving old files.
ALTER TABLE public.cnc_machines
  ADD COLUMN axes text[] CHECK(axes IS NULL OR axes <@ ARRAY['X','Y','Z','A','B','C']),
  ADD COLUMN clamps_declared boolean NOT NULL DEFAULT false,
  ADD COLUMN authority_source text NOT NULL DEFAULT '',
  ADD COLUMN machine_type text NOT NULL DEFAULT '' CHECK(machine_type IN ('','END_MILLER','MACHINING_CENTER','SAW','DECLARED')),
  ADD COLUMN profile_setups jsonb NOT NULL DEFAULT '[]' CHECK(jsonb_typeof(profile_setups)='array');
GRANT SELECT(axes,clamps_declared,authority_source,machine_type,profile_setups) ON public.cnc_machines TO authenticated;
ALTER TABLE public.cnc_tools ADD COLUMN authority_source text NOT NULL DEFAULT '';
GRANT SELECT(authority_source) ON public.cnc_tools TO authenticated;
ALTER TABLE public.cnc_programs ADD COLUMN review_fingerprint text;
ALTER TABLE public.cnc_programs ALTER COLUMN created_at SET DEFAULT clock_timestamp();
GRANT SELECT(review_fingerprint) ON public.cnc_programs TO authenticated;
CREATE UNIQUE INDEX cnc_program_review_uq ON public.cnc_programs(org_id,work_order_id,machine_id,member_id,review_fingerprint)
  WHERE review_fingerprint IS NOT NULL;

CREATE TABLE public.cnc_authority_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id),
  entity_id uuid NOT NULL,
  entity_kind text NOT NULL CHECK(entity_kind IN ('MACHINE','TOOL')),
  action text NOT NULL CHECK(action IN ('CREATE','UPDATE','RETIRE','REACTIVATE')),
  previous jsonb,
  current jsonb NOT NULL,
  actor_id uuid,
  actor_label text,
  created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
ALTER TABLE public.cnc_authority_events ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.cnc_authority_events FROM anon,authenticated,documentary_backend;
GRANT SELECT ON public.cnc_authority_events TO authenticated,documentary_backend;
GRANT ALL ON public.cnc_authority_events TO service_role;
CREATE POLICY cnc_authority_event_read ON public.cnc_authority_events FOR SELECT
  USING(org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY cnc_authority_event_service ON public.cnc_authority_events TO service_role
  USING(true) WITH CHECK(true);

CREATE FUNCTION private.guard_cnc_authority() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE tenant uuid; entry jsonb; claims jsonb:=COALESCE(NULLIF(current_setting('request.jwt.claims',true),''),'{}')::jsonb;
BEGIN
  tenant:=CASE WHEN TG_OP='DELETE' THEN OLD.org_id ELSE NEW.org_id END;
  IF claims->>'sub' IS NOT NULL
    AND NOT private.documentary_role(tenant,ARRAY['OWNER','WORKSHOP_MANAGER']) THEN
    RAISE EXCEPTION 'cnc_permission_denied' USING ERRCODE='42501';
  END IF;
  IF TG_OP='DELETE' THEN
    RAISE EXCEPTION 'cnc_authority_retire_required' USING ERRCODE='23514';
  END IF;
  IF TG_OP='UPDATE' AND (NEW.id<>OLD.id OR NEW.org_id<>OLD.org_id OR NEW.created_at<>OLD.created_at) THEN
    RAISE EXCEPTION 'cnc_authority_identity_immutable' USING ERRCODE='23514';
  END IF;
  IF TG_TABLE_NAME='cnc_machines' THEN
    IF EXISTS(SELECT 1 FROM unnest(NEW.tool_ids) AS tool(id)
      WHERE NOT EXISTS(SELECT 1 FROM public.cnc_tools t WHERE t.id=tool.id AND t.org_id=NEW.org_id)) THEN
      RAISE EXCEPTION 'cnc_tool_not_in_org' USING ERRCODE='23514';
    END IF;
    FOR entry IN SELECT value FROM jsonb_array_elements(NEW.profile_setups) LOOP
      IF jsonb_typeof(entry)<>'object' OR
         (entry-'profile_sku'-'section_fingerprint'-'loading_orientation'-'axial_datum'-'source')<>'{}'::jsonb OR
         COALESCE(btrim(entry->>'profile_sku'),'')='' OR COALESCE(btrim(entry->>'source'),'')='' OR
         COALESCE(entry->>'section_fingerprint','') !~ '^[0-9a-f]{64}$' OR
         COALESCE(entry->>'loading_orientation','') NOT IN ('EXTERIOR_UP','EXTERIOR_DOWN','EXTERIOR_LEFT','EXTERIOR_RIGHT') OR
         COALESCE(entry->>'axial_datum','')<>'MEMBER_START' THEN
        RAISE EXCEPTION 'cnc_profile_setup_invalid' USING ERRCODE='23514';
      END IF;
    END LOOP;
    IF (SELECT count(*)<>count(DISTINCT value->>'profile_sku') FROM jsonb_array_elements(NEW.profile_setups)) THEN
      RAISE EXCEPTION 'cnc_profile_setup_invalid' USING ERRCODE='23514';
    END IF;
  END IF;
  RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION private.guard_cnc_authority() FROM PUBLIC;
CREATE TRIGGER cnc_machine_authority_guard BEFORE INSERT OR UPDATE OR DELETE ON public.cnc_machines
  FOR EACH ROW EXECUTE FUNCTION private.guard_cnc_authority();
CREATE TRIGGER cnc_tool_authority_guard BEFORE INSERT OR UPDATE OR DELETE ON public.cnc_tools
  FOR EACH ROW EXECUTE FUNCTION private.guard_cnc_authority();

CREATE FUNCTION private.trace_cnc_authority() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE claims jsonb:=COALESCE(NULLIF(current_setting('request.jwt.claims',true),''),'{}')::jsonb;
BEGIN
  IF TG_OP='UPDATE' AND to_jsonb(NEW)=to_jsonb(OLD) THEN RETURN NEW; END IF;
  INSERT INTO public.cnc_authority_events(org_id,entity_id,entity_kind,action,previous,current,actor_id,actor_label)
    VALUES(NEW.org_id,NEW.id,CASE WHEN TG_TABLE_NAME='cnc_tools' THEN 'TOOL' ELSE 'MACHINE' END,
      CASE WHEN TG_OP='INSERT' THEN 'CREATE' WHEN NOT NEW.active AND OLD.active THEN 'RETIRE'
        WHEN NEW.active AND NOT OLD.active THEN 'REACTIVATE' ELSE 'UPDATE' END,
      CASE WHEN TG_OP='UPDATE' THEN to_jsonb(OLD) END,to_jsonb(NEW),
      (claims->>'sub')::uuid,claims->>'email');
  RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION private.trace_cnc_authority() FROM PUBLIC;
CREATE TRIGGER cnc_machine_authority_trace AFTER INSERT OR UPDATE ON public.cnc_machines
  FOR EACH ROW EXECUTE FUNCTION private.trace_cnc_authority();
CREATE TRIGGER cnc_tool_authority_trace AFTER INSERT OR UPDATE ON public.cnc_tools
  FOR EACH ROW EXECUTE FUNCTION private.trace_cnc_authority();

CREATE FUNCTION private.guard_cnc_evidence() RETURNS trigger
LANGUAGE plpgsql SET search_path='' AS $$
BEGIN
  IF TG_OP='DELETE' OR TG_OP='TRUNCATE' THEN
    RAISE EXCEPTION 'cnc_evidence_immutable' USING ERRCODE='23514';
  END IF;
  IF TG_TABLE_NAME='cnc_programs' AND TG_OP='UPDATE' THEN
    IF (to_jsonb(NEW)-'status')<>(to_jsonb(OLD)-'status') OR
       NOT(NEW.status=OLD.status OR (OLD.status='CURRENT' AND NEW.status='SUPERSEDED')) THEN
      RAISE EXCEPTION 'cnc_program_immutable' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
  END IF;
  RAISE EXCEPTION 'cnc_evidence_immutable' USING ERRCODE='23514';
END $$;
REVOKE ALL ON FUNCTION private.guard_cnc_evidence() FROM PUBLIC;
CREATE TRIGGER cnc_program_evidence_guard BEFORE UPDATE OR DELETE ON public.cnc_programs
  FOR EACH ROW EXECUTE FUNCTION private.guard_cnc_evidence();
CREATE TRIGGER cnc_program_truncate_guard BEFORE TRUNCATE ON public.cnc_programs
  EXECUTE FUNCTION private.guard_cnc_evidence();
CREATE TRIGGER cnc_authority_event_guard BEFORE UPDATE OR DELETE ON public.cnc_authority_events
  FOR EACH ROW EXECUTE FUNCTION private.guard_cnc_evidence();
CREATE TRIGGER cnc_authority_event_truncate_guard BEFORE TRUNCATE ON public.cnc_authority_events
  EXECUTE FUNCTION private.guard_cnc_evidence();
REVOKE DELETE,TRUNCATE ON public.cnc_tools,public.cnc_machines FROM documentary_backend;
REVOKE UPDATE,DELETE,TRUNCATE ON public.cnc_authority_events FROM service_role;

-- Stronger storage boundary for program generation/status transitions.
CREATE FUNCTION private.guard_cnc_program_actor() RETURNS trigger
LANGUAGE plpgsql SET search_path='' AS $$
DECLARE claims jsonb:=COALESCE(NULLIF(current_setting('request.jwt.claims',true),''),'{}')::jsonb;
BEGIN
  IF claims->>'sub' IS NOT NULL AND
    NOT private.documentary_role(NEW.org_id,ARRAY['OWNER','WORKSHOP_MANAGER']) THEN
    RAISE EXCEPTION 'cnc_permission_denied' USING ERRCODE='42501';
  END IF;
  IF TG_OP='INSERT' AND claims->>'sub' IS NOT NULL AND NEW.created_by IS DISTINCT FROM (claims->>'sub')::uuid THEN
    RAISE EXCEPTION 'cnc_actor_invalid' USING ERRCODE='42501';
  END IF;
  IF NOT EXISTS(SELECT 1 FROM public.orders WHERE id=NEW.work_order_id AND org_id=NEW.org_id)
    OR NOT EXISTS(SELECT 1 FROM public.cnc_machines WHERE id=NEW.machine_id AND org_id=NEW.org_id) THEN
    RAISE EXCEPTION 'cnc_program_tenant_invalid' USING ERRCODE='23514';
  END IF;
  RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION private.guard_cnc_program_actor() FROM PUBLIC;
CREATE TRIGGER cnc_program_actor_guard BEFORE INSERT OR UPDATE ON public.cnc_programs
  FOR EACH ROW EXECUTE FUNCTION private.guard_cnc_program_actor();
