-- Field evidence is additive: no changes to issued revisions, OTs or PODs.
BEGIN;
ALTER TABLE public.orders ADD CONSTRAINT field_order_tenant UNIQUE(id,org_id);
ALTER TABLE public.project_versions ADD CONSTRAINT field_version_tenant UNIQUE(id,project_id,org_id);

CREATE FUNCTION private.field_access(p_org uuid,p_assigned uuid) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path='' AS $$
 SELECT EXISTS(SELECT 1 FROM public.tenancy_memberships m WHERE m.org_id=p_org
 AND m.user_id=auth.uid() AND m.is_active AND m.org_id IN(SELECT private.current_user_org_ids()) AND
 (m.role IN ('OWNER','ESTIMATOR','WORKSHOP_MANAGER') OR
 (m.role='INSTALLER' AND p_assigned=auth.uid())))
$$;
REVOKE ALL ON FUNCTION private.field_access(uuid,uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.field_access(uuid,uuid) TO authenticated,documentary_backend;

CREATE FUNCTION private.field_actor_role(p_org uuid,p_actor uuid) RETURNS text
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path='' AS $$ DECLARE result text; BEGIN
 IF p_actor IS DISTINCT FROM auth.uid() THEN RAISE EXCEPTION 'field_permission'; END IF;
 SELECT m.role::text INTO result FROM public.tenancy_memberships m WHERE m.org_id=p_org AND m.user_id=p_actor
 AND m.is_active AND m.org_id IN(SELECT private.current_user_org_ids()) AND m.role IN ('OWNER','ESTIMATOR','WORKSHOP_MANAGER','INSTALLER') FOR SHARE;
 RETURN result;
END $$;
REVOKE ALL ON FUNCTION private.field_actor_role(uuid,uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.field_actor_role(uuid,uuid) TO documentary_backend;

CREATE FUNCTION private.field_people(p_org uuid) RETURNS TABLE(user_id uuid,role text,display_name text)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path='' AS $$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM public.tenancy_memberships m WHERE m.org_id=p_org AND m.user_id=auth.uid() AND m.is_active
 AND m.org_id IN(SELECT private.current_user_org_ids()) AND m.role IN ('OWNER','ESTIMATOR','WORKSHOP_MANAGER')) THEN RAISE EXCEPTION 'field_permission'; END IF;
 RETURN QUERY SELECT m.user_id,m.role::text,
 coalesce(nullif(u.raw_user_meta_data->>'full_name',''),nullif(u.email,''),'Integrante de terreno')::text
 FROM public.tenancy_memberships m LEFT JOIN auth.users u ON u.id=m.user_id
 WHERE m.org_id=p_org AND m.is_active AND m.role IN ('INSTALLER','OWNER','WORKSHOP_MANAGER','ESTIMATOR') ORDER BY m.role,m.user_id;
 END $$;
REVOKE ALL ON FUNCTION private.field_people(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.field_people(uuid) TO documentary_backend;

CREATE TABLE public.field_visits (
 id uuid PRIMARY KEY DEFAULT uuid_generate_v4(), org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id),
 project_id uuid NOT NULL, project_version_id uuid, assigned_to uuid NOT NULL,
 code text NOT NULL, kind text NOT NULL CHECK(kind IN ('DELIVERY','MEASUREMENT','INSTALLATION','SERVICE')),
 planned_on date NOT NULL, team text NOT NULL CHECK(length(btrim(team)) BETWEEN 1 AND 120),
 vehicle text CHECK(length(vehicle)<=120), context_json jsonb NOT NULL CHECK(jsonb_typeof(context_json)='object'),
 status text NOT NULL DEFAULT 'SCHEDULED' CHECK(status IN ('SCHEDULED','ACTIVE','CLOSED','CANCELLED')),
 created_by uuid NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(id,org_id), UNIQUE(org_id,code),
 FOREIGN KEY(project_id,org_id) REFERENCES public.projects(id,org_id),
 FOREIGN KEY(project_version_id,project_id,org_id) REFERENCES public.project_versions(id,project_id,org_id)
);
CREATE INDEX field_agenda ON public.field_visits(org_id,assigned_to,planned_on);
CREATE TABLE public.field_events (
 id uuid PRIMARY KEY DEFAULT uuid_generate_v4(), org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id),
 visit_id uuid NOT NULL, sequence integer NOT NULL CHECK(sequence>0),
 kind text NOT NULL CHECK(kind IN ('LOAD','DEPART','DELIVER','CHECK','MEASURE','INCIDENT','RECEIVE','DIAGNOSE','RESOLVE','CLOSE','CANCEL')),
 payload_json jsonb NOT NULL CHECK(jsonb_typeof(payload_json)='object'), actor_id uuid NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(visit_id,sequence),
 FOREIGN KEY(visit_id,org_id) REFERENCES public.field_visits(id,org_id)
);
CREATE TABLE public.field_incidents (
 id uuid PRIMARY KEY DEFAULT uuid_generate_v4(), org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id),
 visit_id uuid NOT NULL, order_id uuid, position_id uuid NOT NULL, code text NOT NULL,
 kind text NOT NULL CHECK(kind IN ('DAMAGE','MEASURE','MISSING','ADJUSTMENT','WARRANTY','SERVICE')),
 unit_index integer NOT NULL CHECK(unit_index>0), piece_identity text,
 description text NOT NULL CHECK(length(btrim(description)) BETWEEN 1 AND 2000),
 evidence_json jsonb NOT NULL CHECK(jsonb_typeof(evidence_json)='object'),
 status text NOT NULL DEFAULT 'OPEN' CHECK(status IN ('OPEN','PLANNED','RESOLVED','CLOSED')),
 resolution_json jsonb NOT NULL DEFAULT '{}', diagnosis text,
 created_by uuid NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(id,org_id), UNIQUE(org_id,code),
 FOREIGN KEY(visit_id,org_id) REFERENCES public.field_visits(id,org_id),
 FOREIGN KEY(order_id,org_id) REFERENCES public.orders(id,org_id)
);
CREATE INDEX field_cases ON public.field_incidents(org_id,status,created_at);
CREATE TABLE public.field_assets (
 id uuid PRIMARY KEY DEFAULT uuid_generate_v4(), org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id),
 visit_id uuid NOT NULL, position_id uuid NOT NULL, unit_index integer NOT NULL CHECK(unit_index>0),
 kind text NOT NULL CHECK(kind IN ('PHOTO','SIGNATURE','ACT')),
 storage_object_key text NOT NULL, media_type text NOT NULL CHECK(media_type IN ('image/png','image/jpeg','application/pdf')),
 file_sha256 text NOT NULL CHECK(file_sha256 ~ '^[0-9a-f]{64}$'), byte_size bigint NOT NULL CHECK(byte_size>0),
 payload_json jsonb NOT NULL, created_by uuid NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(id,org_id), UNIQUE(visit_id,storage_object_key),
 FOREIGN KEY(visit_id,org_id) REFERENCES public.field_visits(id,org_id)
);
CREATE UNIQUE INDEX field_one_act ON public.field_assets(visit_id) WHERE kind='ACT';
CREATE TABLE public.field_receipts (
 org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id), actor_id uuid NOT NULL,
 operation_key uuid NOT NULL, visit_id uuid NOT NULL, request_hash text NOT NULL CHECK(request_hash ~ '^[0-9a-f]{64}$'),
 response_json jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(org_id,actor_id,operation_key),
 FOREIGN KEY(visit_id,org_id) REFERENCES public.field_visits(id,org_id)
);
-- Allocate against the entire tenant, including visits hidden by assignment RLS.
-- Evidence cannot be deleted, so the serialized count is a durable sequence.
CREATE FUNCTION private.field_next_code(p_org uuid,p_kind text,p_visit uuid) RETURNS text
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path='' AS $$
DECLARE n bigint; BEGIN
 IF NOT p_org IN(SELECT private.current_user_org_ids()) OR NOT EXISTS(
 SELECT 1 FROM public.tenancy_memberships m WHERE m.org_id=p_org AND m.user_id=auth.uid()
 AND m.is_active AND (m.role IN ('OWNER','ESTIMATOR','WORKSHOP_MANAGER') OR
 (m.role='INSTALLER' AND p_kind IN ('INC','ACT') AND EXISTS(SELECT 1 FROM public.field_visits v
 WHERE v.org_id=p_org AND v.id=p_visit AND v.assigned_to=auth.uid()))))
 THEN RAISE EXCEPTION 'field_permission' USING ERRCODE='42501'; END IF;
 PERFORM pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('field-code:'||p_org::text,0));
 IF p_kind='VIS' THEN SELECT count(*) INTO n FROM public.field_visits WHERE org_id=p_org;
 ELSIF p_kind='INC' THEN SELECT count(*) INTO n FROM public.field_incidents WHERE org_id=p_org;
 ELSIF p_kind='ACT' THEN SELECT count(*) INTO n FROM public.field_assets WHERE org_id=p_org AND kind='ACT';
 ELSE RAISE EXCEPTION 'field_code_invalid'; END IF;
 RETURN p_kind||'-'||lpad((n+1)::text,greatest(6,length((n+1)::text)),'0');
END $$;
REVOKE ALL ON FUNCTION private.field_next_code(uuid,text,uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.field_next_code(uuid,text,uuid) TO documentary_backend;

CREATE FUNCTION private.field_immutable() RETURNS trigger LANGUAGE plpgsql SET search_path='' AS $$
 BEGIN RAISE EXCEPTION 'field_evidence_immutable'; END $$;
CREATE FUNCTION private.field_context_immutable() RETURNS trigger LANGUAGE plpgsql SET search_path='' AS $$
 BEGIN
 IF TG_OP='DELETE' THEN RAISE EXCEPTION 'field_evidence_immutable'; END IF;
 IF TG_TABLE_NAME='field_visits' AND
 (to_jsonb(NEW)-'status') IS DISTINCT FROM (to_jsonb(OLD)-'status') THEN RAISE EXCEPTION 'field_context_immutable'; END IF;
 IF TG_TABLE_NAME='field_incidents' AND
 (to_jsonb(NEW)-ARRAY['status','resolution_json','diagnosis']) IS DISTINCT FROM
 (to_jsonb(OLD)-ARRAY['status','resolution_json','diagnosis']) THEN RAISE EXCEPTION 'field_context_immutable'; END IF;
 RETURN NEW;
 END $$;
ALTER TABLE public.field_visits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.field_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.field_incidents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.field_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.field_receipts ENABLE ROW LEVEL SECURITY;
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['field_visits','field_events','field_incidents','field_assets','field_receipts'] LOOP
 IF t='field_visits' THEN
 EXECUTE format('CREATE POLICY field_read ON public.%I FOR SELECT TO authenticated USING(private.field_access(org_id,assigned_to))',t);
 EXECUTE format('CREATE POLICY field_backend ON public.%I TO documentary_backend USING(private.field_access(org_id,assigned_to)) WITH CHECK(private.field_access(org_id,assigned_to))',t);
 ELSE
 EXECUTE format('CREATE POLICY field_read ON public.%1$I FOR SELECT TO authenticated USING(EXISTS(SELECT 1 FROM public.field_visits v WHERE v.id=%1$I.visit_id AND v.org_id=%1$I.org_id AND private.field_access(v.org_id,v.assigned_to)))',t);
 EXECUTE format('CREATE POLICY field_backend ON public.%1$I TO documentary_backend USING(EXISTS(SELECT 1 FROM public.field_visits v WHERE v.id=%1$I.visit_id AND v.org_id=%1$I.org_id AND private.field_access(v.org_id,v.assigned_to))) WITH CHECK(EXISTS(SELECT 1 FROM public.field_visits v WHERE v.id=%1$I.visit_id AND v.org_id=%1$I.org_id AND private.field_access(v.org_id,v.assigned_to)))',t);
 END IF;
 EXECUTE format('REVOKE ALL ON public.%I FROM anon,authenticated,documentary_backend',t);
 EXECUTE format('GRANT SELECT ON public.%I TO authenticated',t);
 EXECUTE format('GRANT SELECT,INSERT ON public.%I TO documentary_backend',t);
 EXECUTE format('GRANT ALL ON public.%I TO service_role',t);
 EXECUTE format('REVOKE ALL ON public.%I FROM anon',t);
 EXECUTE format('CREATE TRIGGER field_no_truncate BEFORE TRUNCATE ON public.%I FOR EACH STATEMENT EXECUTE FUNCTION private.field_immutable()',t);
 IF t IN ('field_visits','field_incidents') THEN
 EXECUTE format('GRANT UPDATE ON public.%I TO documentary_backend',t);
 EXECUTE format('CREATE TRIGGER field_context_immutable BEFORE UPDATE OR DELETE ON public.%I FOR EACH ROW EXECUTE FUNCTION private.field_context_immutable()',t);
 ELSE
 EXECUTE format('CREATE TRIGGER field_immutable BEFORE UPDATE OR DELETE ON public.%I FOR EACH ROW EXECUTE FUNCTION private.field_immutable()',t);
 END IF;
 END LOOP;
END $$;

CREATE FUNCTION private.field_unit_context() RETURNS trigger LANGUAGE plpgsql SET search_path='' AS $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM public.field_visits v CROSS JOIN LATERAL jsonb_array_elements(v.context_json->'units') u
 WHERE v.id=NEW.visit_id AND v.org_id=NEW.org_id AND u->>'position_id'=NEW.position_id::text
 AND (u->>'unit_index')::int=NEW.unit_index) THEN RAISE EXCEPTION 'field_unit_context_mismatch'; END IF;
 IF TG_TABLE_NAME='field_incidents' THEN
 IF NOT EXISTS(SELECT 1 FROM public.field_visits v
 CROSS JOIN LATERAL jsonb_array_elements(v.context_json->'units') u WHERE v.id=NEW.visit_id AND v.org_id=NEW.org_id
 AND u->>'position_id'=NEW.position_id::text AND (u->>'unit_index')::int=NEW.unit_index
 AND (u->>'order_id')::uuid IS NOT DISTINCT FROM NEW.order_id) THEN RAISE EXCEPTION 'field_order_context_mismatch'; END IF;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER field_unit_context BEFORE INSERT ON public.field_incidents FOR EACH ROW EXECUTE FUNCTION private.field_unit_context();
CREATE TRIGGER field_unit_context BEFORE INSERT ON public.field_assets FOR EACH ROW EXECUTE FUNCTION private.field_unit_context();
-- Supplemental losses are distinct authority; original capacity stays exact.
ALTER TABLE public.purchase_requirement_lines ADD CONSTRAINT field_requirement_tenant UNIQUE(id,org_id);
CREATE TABLE public.field_purchase_authorizations (
 id uuid PRIMARY KEY DEFAULT uuid_generate_v4(), org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id),
 visit_id uuid NOT NULL, incident_id uuid NOT NULL, requirement_line_id uuid NOT NULL,
 quantity numeric(18,4) NOT NULL CHECK(quantity>0 AND quantity=trunc(quantity)),
 created_by uuid NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(id,org_id), UNIQUE(incident_id,requirement_line_id),
 FOREIGN KEY(visit_id,org_id) REFERENCES public.field_visits(id,org_id),
 FOREIGN KEY(incident_id,org_id) REFERENCES public.field_incidents(id,org_id),
 FOREIGN KEY(requirement_line_id,org_id) REFERENCES public.purchase_requirement_lines(id,org_id)
);
ALTER TABLE public.field_purchase_authorizations ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.field_purchase_authorizations FROM PUBLIC,anon,authenticated;
GRANT SELECT,INSERT ON public.field_purchase_authorizations TO documentary_backend;
GRANT ALL ON public.field_purchase_authorizations TO service_role;
CREATE POLICY field_loss_office ON public.field_purchase_authorizations TO documentary_backend
 USING(private.documentary_role(org_id,ARRAY['OWNER','WORKSHOP_MANAGER']))
 WITH CHECK(private.documentary_role(org_id,ARRAY['OWNER','WORKSHOP_MANAGER']));
CREATE FUNCTION private.field_loss_guard() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
BEGIN
 IF NEW.created_by IS DISTINCT FROM auth.uid() OR NOT private.documentary_role(NEW.org_id,ARRAY['OWNER','WORKSHOP_MANAGER'])
 OR NOT EXISTS(SELECT 1 FROM public.field_incidents i JOIN public.field_visits v ON v.id=i.visit_id AND v.org_id=i.org_id
 JOIN public.purchase_requirement_lines r ON r.id=NEW.requirement_line_id AND r.org_id=i.org_id AND r.project_version_id=v.project_version_id
 CROSS JOIN LATERAL jsonb_array_elements(v.context_json->'units') u
 WHERE i.id=NEW.incident_id AND i.org_id=NEW.org_id AND i.visit_id=NEW.visit_id AND i.kind='MISSING' AND i.status='OPEN'
 AND u->>'position_id'=i.position_id::text AND (u->>'unit_index')::int=i.unit_index
 AND u->'requirement_ids' ? NEW.requirement_line_id::text AND NEW.quantity<=r.quantity)
 THEN RAISE EXCEPTION 'field_loss_authority_invalid' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION private.field_loss_guard() FROM PUBLIC;
CREATE TRIGGER field_loss_guard BEFORE INSERT ON public.field_purchase_authorizations FOR EACH ROW EXECUTE FUNCTION private.field_loss_guard();
CREATE TRIGGER field_loss_immutable BEFORE UPDATE OR DELETE ON public.field_purchase_authorizations FOR EACH ROW EXECUTE FUNCTION private.field_immutable();
CREATE TRIGGER field_loss_no_truncate BEFORE TRUNCATE ON public.field_purchase_authorizations FOR EACH STATEMENT EXECUTE FUNCTION private.field_immutable();
ALTER TABLE public.order_requirement_lines ADD COLUMN field_authorization_id uuid;
ALTER TABLE public.order_requirement_lines ADD CONSTRAINT field_purchase_capacity_identity
 FOREIGN KEY(field_authorization_id,org_id) REFERENCES public.field_purchase_authorizations(id,org_id);
CREATE OR REPLACE FUNCTION private.purchase_quantity_capacity() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE capacity numeric; committed numeric; loss public.field_purchase_authorizations;
BEGIN
 IF NULLIF(current_setting('request.jwt.claims',true),'')::jsonb->>'sub' IS NOT NULL
 AND NOT private.documentary_role(NEW.org_id,ARRAY['OWNER','WORKSHOP_MANAGER']) THEN
 RAISE EXCEPTION 'purchase_permission_denied' USING ERRCODE='42501'; END IF;
 IF NEW.field_authorization_id IS NULL THEN
 SELECT quantity INTO capacity FROM public.purchase_requirement_lines WHERE id=NEW.requirement_line_id AND org_id=NEW.org_id FOR UPDATE;
 SELECT COALESCE(SUM(quantity-released_qty),0) INTO committed FROM public.order_requirement_lines
 WHERE requirement_line_id=NEW.requirement_line_id AND org_id=NEW.org_id AND field_authorization_id IS NULL;
 ELSE
 SELECT * INTO loss FROM public.field_purchase_authorizations WHERE id=NEW.field_authorization_id AND org_id=NEW.org_id FOR UPDATE;
 IF loss.id IS NULL OR loss.requirement_line_id<>NEW.requirement_line_id OR NOT EXISTS(
 SELECT 1 FROM public.orders o WHERE o.id=NEW.order_id AND o.org_id=NEW.org_id AND o.payload_json->'field_incident'->>'id'=loss.incident_id::text)
 THEN RAISE EXCEPTION 'field_loss_capacity_identity' USING ERRCODE='23514'; END IF;
 capacity:=loss.quantity;
 SELECT COALESCE(SUM(quantity-released_qty),0) INTO committed FROM public.order_requirement_lines WHERE org_id=NEW.org_id AND field_authorization_id=loss.id;
 END IF;
 IF capacity IS NULL OR NEW.quantity+committed>capacity THEN
 RAISE EXCEPTION 'purchase_requirement_capacity_exceeded' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END $$;
COMMIT;
