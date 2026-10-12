-- Analytics adds evidence; no historical revision, stock or price is rewritten.
BEGIN;
CREATE TABLE public.analytics_preferences (
 org_id uuid PRIMARY KEY REFERENCES public.tenancy_organizations(id),
 period_days integer NOT NULL DEFAULT 30 CHECK(period_days BETWEEN 1 AND 366),
 updated_by uuid NOT NULL, updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE public.production_actual_reports (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id),
 order_id uuid NOT NULL, revision integer NOT NULL CHECK(revision>0),
 request_key uuid NOT NULL, request_hash text NOT NULL CHECK(request_hash ~ '^[0-9a-f]{64}$'),
 source_fingerprint text NOT NULL CHECK(source_fingerprint ~ '^[0-9a-f]{64}$'),
 currency text NOT NULL CHECK(currency IN ('CLP','USD','UF')),
 evidence_json jsonb NOT NULL CHECK(jsonb_typeof(evidence_json)='object'),
 result_json jsonb NOT NULL CHECK(jsonb_typeof(result_json)='object'),
 response_json jsonb NOT NULL CHECK(jsonb_typeof(response_json)='object'),
 source text NOT NULL CHECK(length(btrim(source)) BETWEEN 3 AND 1000),
 reason text NOT NULL CHECK(length(btrim(reason)) BETWEEN 3 AND 1000),
 created_by uuid NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY(order_id,org_id) REFERENCES public.orders(id,org_id),
 UNIQUE(org_id,order_id,revision), UNIQUE(org_id,request_key)
);
CREATE INDEX production_actual_reports_latest ON public.production_actual_reports(org_id,order_id,revision DESC);
ALTER TABLE public.analytics_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.production_actual_reports ENABLE ROW LEVEL SECURITY;
CREATE POLICY analytics_preferences_read ON public.analytics_preferences FOR SELECT TO authenticated,documentary_backend
 USING(org_id IN(SELECT private.current_user_org_ids()) AND private.documentary_role(org_id,ARRAY['OWNER','WORKSHOP_MANAGER']));
CREATE POLICY analytics_preferences_owner ON public.analytics_preferences TO documentary_backend
 USING(org_id IN(SELECT private.current_user_org_ids()) AND private.documentary_role(org_id,ARRAY['OWNER']))
 WITH CHECK(org_id IN(SELECT private.current_user_org_ids()) AND private.documentary_role(org_id,ARRAY['OWNER']) AND updated_by=auth.uid());
CREATE POLICY production_actual_reports_read ON public.production_actual_reports FOR SELECT TO authenticated,documentary_backend
 USING(org_id IN(SELECT private.current_user_org_ids()) AND private.documentary_role(org_id,ARRAY['OWNER','WORKSHOP_MANAGER']));
CREATE POLICY production_actual_reports_insert ON public.production_actual_reports FOR INSERT TO documentary_backend
 WITH CHECK(org_id IN(SELECT private.current_user_org_ids()) AND private.documentary_role(org_id,ARRAY['OWNER','WORKSHOP_MANAGER']) AND created_by=auth.uid());
REVOKE ALL ON public.analytics_preferences,public.production_actual_reports FROM PUBLIC,anon,authenticated,documentary_backend;
GRANT SELECT ON public.analytics_preferences,public.production_actual_reports TO authenticated;
GRANT SELECT,INSERT,UPDATE ON public.analytics_preferences TO documentary_backend;
GRANT SELECT,INSERT ON public.production_actual_reports TO documentary_backend,service_role;
GRANT SELECT,INSERT,UPDATE ON public.analytics_preferences TO service_role;
CREATE FUNCTION private.actual_report_guard() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE o public.orders; n integer;
BEGIN
 IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'actual_report_immutable' USING ERRCODE='23514'; END IF;
 IF NEW.created_by IS DISTINCT FROM auth.uid() THEN RAISE EXCEPTION 'actual_report_actor' USING ERRCODE='42501'; END IF;
 PERFORM 1 FROM public.tenancy_memberships m WHERE m.org_id=NEW.org_id AND m.user_id=NEW.created_by
  AND m.is_active AND m.role IN ('OWNER','WORKSHOP_MANAGER') FOR SHARE;
 IF NOT FOUND THEN RAISE EXCEPTION 'actual_report_actor' USING ERRCODE='42501'; END IF;
 SELECT * INTO o FROM public.orders WHERE id=NEW.order_id AND org_id=NEW.org_id FOR UPDATE;
 IF o.id IS NULL OR o.order_type<>'WORKSHOP_OT' THEN RAISE EXCEPTION 'actual_report_scope' USING ERRCODE='23514'; END IF;
 SELECT coalesce(max(revision),0)+1 INTO n FROM public.production_actual_reports WHERE org_id=NEW.org_id AND order_id=NEW.order_id;
 IF NEW.revision<>n THEN RAISE EXCEPTION 'actual_report_revision' USING ERRCODE='23514'; END IF;
 IF NEW.evidence_json->>'closed'='true' AND o.status NOT IN ('COMPLETED','DISPATCHED','INSTALLED','CANCELLED') THEN
   RAISE EXCEPTION 'actual_report_unfinished' USING ERRCODE='23514';
 END IF;
 IF NEW.currency IS DISTINCT FROM (SELECT v.snapshot_json->'project'->>'currency' FROM public.project_versions v WHERE v.id=o.project_version_id AND v.org_id=o.org_id) THEN
   RAISE EXCEPTION 'actual_report_currency' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION private.actual_report_guard() FROM PUBLIC,anon,authenticated;
CREATE TRIGGER actual_report_guard BEFORE INSERT OR UPDATE OR DELETE ON public.production_actual_reports
 FOR EACH ROW EXECUTE FUNCTION private.actual_report_guard();
CREATE TRIGGER actual_report_no_truncate BEFORE TRUNCATE ON public.production_actual_reports
 FOR EACH STATEMENT EXECUTE FUNCTION private.actual_report_guard();

-- A narrow decision projection for cost-authorized managers. No customer
-- identity, consent, signature, RUT or payment credentials cross this edge.
CREATE FUNCTION private.analytics_choices(p_org uuid)
 RETURNS TABLE(offering_version_id uuid,selected_version_id uuid,kind text,decided_at timestamptz,note text)
 LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path='' AS $$ BEGIN
 IF NOT p_org IN(SELECT private.current_user_org_ids()) OR NOT private.documentary_role(p_org,ARRAY['OWNER','WORKSHOP_MANAGER'])
 THEN RAISE EXCEPTION 'analytics_permission' USING ERRCODE='42501'; END IF;
 RETURN QUERY SELECT d.offering_version_id,d.selected_version_id,d.kind::text,d.decided_at,d.evidence->>'note'
 FROM public.quote_decisions d WHERE d.org_id=p_org;
 END $$;
REVOKE ALL ON FUNCTION private.analytics_choices(uuid) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION private.analytics_choices(uuid) TO documentary_backend;
COMMIT;
