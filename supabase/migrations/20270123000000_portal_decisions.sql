-- A customer's response is separate, immutable evidence. Choosing an offered
-- alternative never edits either issued snapshot or the live offer's design.
BEGIN;
ALTER TABLE public.customer_approvals ALTER COLUMN status TYPE varchar(32);
ALTER TABLE public.customer_approvals DROP CONSTRAINT customer_approvals_status_check;
ALTER TABLE public.customer_approvals ADD CONSTRAINT customer_approvals_status_check
  CHECK (status IN ('PENDING','APPROVED','DECLINED','CHANGES_REQUESTED','REVOKED'));

CREATE TABLE public.quote_decisions (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id),
  project_id uuid NOT NULL REFERENCES public.projects(id),
  offering_version_id uuid NOT NULL REFERENCES public.project_versions(id),
  selected_version_id uuid NOT NULL REFERENCES public.project_versions(id),
  approval_id uuid NOT NULL REFERENCES public.customer_approvals(id),
  kind varchar(32) NOT NULL CHECK (kind IN ('APPROVED','CHANGES_REQUESTED','DECLINED')),
  decided_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  offering_sha256 char(64) NOT NULL CHECK (offering_sha256 ~ '^[0-9a-f]{64}$'),
  selected_sha256 char(64) NOT NULL CHECK (selected_sha256 ~ '^[0-9a-f]{64}$'),
  position_id uuid,
  evidence jsonb NOT NULL CHECK (jsonb_typeof(evidence)='object'),
  UNIQUE(org_id,offering_version_id)
);
ALTER TABLE public.quote_decisions ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.quote_decisions FROM PUBLIC,anon,authenticated,portal_backend,documentary_backend;
GRANT SELECT,INSERT ON public.quote_decisions TO documentary_backend;
GRANT INSERT ON public.quote_decisions TO portal_backend;
GRANT SELECT(id,org_id,project_id,offering_version_id,selected_version_id,approval_id,
             kind,decided_at,offering_sha256,selected_sha256,position_id)
  ON public.quote_decisions TO portal_backend;
GRANT SELECT,INSERT ON public.quote_decisions TO service_role;

CREATE POLICY quote_decisions_commercial ON public.quote_decisions TO documentary_backend
  USING (EXISTS(SELECT 1 FROM public.tenancy_memberships m
    WHERE m.org_id=quote_decisions.org_id AND m.user_id=auth.uid() AND m.is_active
      AND m.role IN ('OWNER','ESTIMATOR')))
  WITH CHECK (EXISTS(SELECT 1 FROM public.tenancy_memberships m
    WHERE m.org_id=quote_decisions.org_id AND m.user_id=auth.uid() AND m.is_active
      AND m.role IN ('OWNER','ESTIMATOR')));
CREATE POLICY quote_decisions_portal_read ON public.quote_decisions FOR SELECT TO portal_backend
  USING (org_id=NULLIF(current_setting('app.portal_org_id',true),'')::uuid);
CREATE POLICY quote_decisions_portal_insert ON public.quote_decisions FOR INSERT TO portal_backend
  WITH CHECK (org_id=NULLIF(current_setting('app.portal_org_id',true),'')::uuid);

CREATE FUNCTION private.quote_decision_guard() RETURNS trigger LANGUAGE plpgsql
  SET search_path=pg_catalog,public,private AS $$
DECLARE offered public.project_versions; selected public.project_versions; link public.customer_approvals;
BEGIN
  IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'quote_decision_immutable' USING ERRCODE='23514'; END IF;
  SELECT * INTO offered FROM public.project_versions WHERE id=NEW.offering_version_id AND org_id=NEW.org_id;
  SELECT * INTO selected FROM public.project_versions WHERE id=NEW.selected_version_id AND org_id=NEW.org_id;
  SELECT * INTO link FROM public.customer_approvals WHERE id=NEW.approval_id AND org_id=NEW.org_id;
  IF offered.id IS NULL OR selected.id IS NULL OR link.id IS NULL
     OR offered.project_id<>NEW.project_id OR selected.project_id<>NEW.project_id
     OR link.project_id<>NEW.project_id OR link.project_version_id<>offered.id
     OR offered.snapshot_sha256<>NEW.offering_sha256 OR selected.snapshot_sha256<>NEW.selected_sha256 THEN
    RAISE EXCEPTION 'quote_decision_scope' USING ERRCODE='23514';
  END IF;
  IF selected.id<>offered.id AND NOT EXISTS(
    SELECT 1 FROM jsonb_array_elements(COALESCE(offered.snapshot_json->'alternatives','[]'::jsonb)) a
    WHERE a=jsonb_build_object('revision',selected.snapshot_json->'revision',
      'project',selected.snapshot_json->'project','positions',selected.snapshot_json->'positions',
      'pricing',selected.snapshot_json->'pricing')) THEN
    RAISE EXCEPTION 'quote_option_not_offered' USING ERRCODE='23514';
  END IF;
  IF NEW.position_id IS NOT NULL AND NOT EXISTS(
    SELECT 1 FROM jsonb_array_elements(selected.snapshot_json->'positions') p
    WHERE p->>'id'=NEW.position_id::text) THEN
    RAISE EXCEPTION 'quote_position_not_offered' USING ERRCODE='23514';
  END IF;
  IF NEW.kind='APPROVED' AND (COALESCE(NEW.evidence->>'name','')=''
     OR COALESCE(NEW.evidence->>'rut','')=''
     OR NEW.evidence->>'confirmed' IS DISTINCT FROM 'true'
     OR COALESCE(NEW.evidence->>'consent','')='') THEN
    RAISE EXCEPTION 'quote_consent_required' USING ERRCODE='23514';
  END IF;
  IF NEW.kind='CHANGES_REQUESTED' AND btrim(COALESCE(NEW.evidence->>'note',''))='' THEN
    RAISE EXCEPTION 'quote_change_note_required' USING ERRCODE='23514';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER quote_decision_guard BEFORE INSERT OR UPDATE OR DELETE ON public.quote_decisions
  FOR EACH ROW EXECUTE FUNCTION private.quote_decision_guard();
CREATE TRIGGER quote_decision_no_truncate BEFORE TRUNCATE ON public.quote_decisions
  FOR EACH STATEMENT EXECUTE FUNCTION private.quote_decision_guard();

-- Nonpersonal facts are shared with the authorized commercial/manufacturing
-- consumers. The evidence JSON has no grant to the public portal or workshop.
CREATE FUNCTION private.quotation_choice(p_org uuid,p_offer uuid)
  RETURNS TABLE(selected_version_id uuid,kind varchar,decided_at timestamptz)
  LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,public,private AS $$
  SELECT d.selected_version_id,d.kind,d.decided_at FROM public.quote_decisions d
  WHERE d.org_id=p_org AND d.offering_version_id=p_offer AND (
    p_org IN(SELECT private.current_user_org_ids())
    OR current_setting('role',true)='service_role'
    OR (current_setting('role',true)='portal_backend'
      AND p_org=NULLIF(current_setting('app.portal_org_id',true),'')::uuid))
$$;
REVOKE ALL ON FUNCTION private.quotation_choice(uuid,uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.quotation_choice(uuid,uuid)
  TO authenticated,documentary_backend,portal_backend,pricing_backend,service_role;

CREATE FUNCTION private.quote_has_production(p_org uuid,p_project uuid) RETURNS boolean
  LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,public,private AS $$
  SELECT EXISTS(SELECT 1 FROM public.orders o WHERE o.org_id=p_org AND o.project_id=p_project
    AND o.order_type='WORKSHOP_OT' AND o.status<>'CANCELLED') AND (
    p_org IN(SELECT private.current_user_org_ids()) OR current_setting('role',true)='service_role'
    OR (current_setting('role',true)='portal_backend'
      AND p_org=NULLIF(current_setting('app.portal_org_id',true),'')::uuid))
$$;
REVOKE ALL ON FUNCTION private.quote_has_production(uuid,uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.quote_has_production(uuid,uuid) TO documentary_backend,portal_backend,service_role;

CREATE FUNCTION private.quote_has_conflicting_purchase(p_org uuid,p_project uuid,p_selected uuid) RETURNS boolean
  LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,public,private AS $$
  SELECT EXISTS(SELECT 1 FROM public.orders o WHERE o.org_id=p_org AND o.project_id=p_project
    AND o.order_type<>'WORKSHOP_OT' AND o.status<>'CANCELLED' AND o.project_version_id<>p_selected) AND (
    p_org IN(SELECT private.current_user_org_ids()) OR current_setting('role',true)='service_role'
    OR (current_setting('role',true)='portal_backend'
      AND p_org=NULLIF(current_setting('app.portal_org_id',true),'')::uuid))
$$;
REVOKE ALL ON FUNCTION private.quote_has_conflicting_purchase(uuid,uuid,uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.quote_has_conflicting_purchase(uuid,uuid,uuid) TO documentary_backend,portal_backend,service_role;

CREATE FUNCTION private.quote_has_conflicting_invoice(p_org uuid,p_project uuid,p_selected uuid) RETURNS boolean
  LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,public,private AS $$
  SELECT EXISTS(SELECT 1 FROM public.project_invoices i WHERE i.org_id=p_org AND i.project_id=p_project
    AND i.project_version_id IS DISTINCT FROM p_selected) AND (
    p_org IN(SELECT private.current_user_org_ids()) OR current_setting('role',true)='service_role'
    OR (current_setting('role',true)='portal_backend'
      AND p_org=NULLIF(current_setting('app.portal_org_id',true),'')::uuid))
$$;
REVOKE ALL ON FUNCTION private.quote_has_conflicting_invoice(uuid,uuid,uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.quote_has_conflicting_invoice(uuid,uuid,uuid) TO documentary_backend,portal_backend,service_role;

CREATE TABLE public.portal_payment_contexts (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id),
  project_id uuid NOT NULL REFERENCES public.projects(id),
  approval_id uuid NOT NULL REFERENCES public.customer_approvals(id),
  payment_link_id uuid NOT NULL UNIQUE REFERENCES public.project_payment_links(id),
  access_hash char(64) NOT NULL UNIQUE CHECK (access_hash ~ '^[0-9a-f]{64}$'),
  token_ciphertext text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
ALTER TABLE public.portal_payment_contexts ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.portal_payment_contexts FROM PUBLIC,anon,authenticated,portal_backend,documentary_backend;
GRANT SELECT,INSERT ON public.portal_payment_contexts TO documentary_backend,service_role;
CREATE POLICY portal_payment_contexts_tenant ON public.portal_payment_contexts TO documentary_backend
  USING(org_id IN(SELECT private.current_user_org_ids()))
  WITH CHECK(org_id IN(SELECT private.current_user_org_ids()));
CREATE FUNCTION private.portal_payment_context_guard() RETURNS trigger LANGUAGE plpgsql
  SET search_path=pg_catalog,public,private AS $$
BEGIN
  IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'portal_payment_context_immutable' USING ERRCODE='23514'; END IF;
  IF NOT EXISTS(SELECT 1 FROM public.customer_approvals a JOIN public.project_payment_links l
    ON l.org_id=a.org_id AND l.project_id=a.project_id
    WHERE a.id=NEW.approval_id AND l.id=NEW.payment_link_id
      AND a.org_id=NEW.org_id AND a.project_id=NEW.project_id) THEN
    RAISE EXCEPTION 'portal_payment_context_scope' USING ERRCODE='23514';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER portal_payment_context_guard BEFORE INSERT OR UPDATE OR DELETE ON public.portal_payment_contexts
  FOR EACH ROW EXECUTE FUNCTION private.portal_payment_context_guard();
CREATE TRIGGER portal_payment_context_no_truncate BEFORE TRUNCATE ON public.portal_payment_contexts
  FOR EACH STATEMENT EXECUTE FUNCTION private.portal_payment_context_guard();

-- Read-only public readiness; capability scoping is still required for each row.
GRANT SELECT(simulation_enabled,payment_link_days,org_id) ON public.collection_preferences TO portal_backend;
CREATE POLICY collection_preferences_portal ON public.collection_preferences FOR SELECT TO portal_backend
  USING(org_id=NULLIF(current_setting('app.portal_org_id',true),'')::uuid);
GRANT SELECT(org_id,provider,enabled) ON public.org_payment_integrations TO portal_backend;
CREATE POLICY org_payment_integrations_portal ON public.org_payment_integrations FOR SELECT TO portal_backend
  USING(org_id=NULLIF(current_setting('app.portal_org_id',true),'')::uuid);
-- The portal cannot enumerate ciphertext. Only the opted-in successor of the
-- already verified offer can be resolved through this narrow projection.
CREATE FUNCTION private.quote_successor_link(p_org uuid,p_offer uuid)
  RETURNS TABLE(id uuid,org_id uuid,project_version_id uuid,token_ciphertext text)
  LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,public,private AS $$
  SELECT l.id,l.org_id,l.project_version_id,l.token_ciphertext
  FROM public.project_versions offered
  JOIN public.projects p ON p.id=offered.project_id AND p.org_id=offered.org_id
  JOIN public.project_versions v ON v.project_id=p.id AND v.org_id=p.org_id AND v.revision_code=p.current_revision
  JOIN public.document_portal_links l ON l.project_version_id=v.id AND l.org_id=v.org_id
  JOIN public.customer_approvals a ON a.id=l.approval_id AND a.org_id=l.org_id
  WHERE offered.id=p_offer AND offered.org_id=p_org AND v.id<>offered.id
    AND offered.snapshot_json->'organization'->'document_preferences'->>'portal_successor_link'='true'
    AND a.status<>'REVOKED' AND private.quote_link_expires_at(a.id,a.org_id,a.expires_at)>now()
    AND (current_setting('role',true)='service_role'
      OR (current_setting('role',true)='portal_backend'
        AND p_org=NULLIF(current_setting('app.portal_org_id',true),'')::uuid))
  ORDER BY l.created_at DESC LIMIT 1
$$;
REVOKE ALL ON FUNCTION private.quote_successor_link(uuid,uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.quote_successor_link(uuid,uuid) TO portal_backend,service_role;
COMMIT;
