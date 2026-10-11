-- P22: customer identities, work-address snapshots and immutable dossier evidence.
BEGIN;

ALTER TABLE public.tenancy_organizations ADD COLUMN require_mfa boolean NOT NULL DEFAULT false;
GRANT SELECT(require_mfa) ON public.tenancy_organizations TO authenticated,documentary_backend,pricing_backend;
CREATE FUNCTION private.bootstrap_memberships(p_user uuid)
RETURNS TABLE(org_id uuid,organization_name text,role text,require_mfa boolean)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path='' AS $$
 SELECT m.org_id,o.name::text,m.role::text,o.require_mfa
 FROM public.tenancy_memberships m JOIN public.tenancy_organizations o ON o.id=m.org_id
 WHERE m.user_id=p_user AND m.user_id=auth.uid() AND m.is_active;
$$;
REVOKE ALL ON FUNCTION private.bootstrap_memberships(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.bootstrap_memberships(uuid) TO authenticated;
-- Bootstrap returns only the caller's organization names/roles. Application
-- data remains unavailable until the required assurance has been attained.
CREATE OR REPLACE FUNCTION private.current_user_org_ids() RETURNS SETOF uuid
LANGUAGE sql STABLE SECURITY DEFINER SET search_path='' AS $$
 SELECT m.org_id FROM public.tenancy_memberships m JOIN public.tenancy_organizations o ON o.id=m.org_id
 WHERE m.user_id=auth.uid() AND m.is_active AND (NOT o.require_mfa OR auth.jwt()->>'aal'='aal2');
$$;
CREATE OR REPLACE FUNCTION private.pricing_role(target_org uuid,allowed_roles text[]) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path='' AS $$
 SELECT EXISTS(SELECT 1 FROM public.tenancy_memberships m WHERE m.org_id=target_org AND m.user_id=auth.uid()
  AND m.is_active AND m.role::text=ANY(allowed_roles) AND m.org_id IN(SELECT private.current_user_org_ids()));
$$;
CREATE OR REPLACE FUNCTION private.documentary_role(target_org uuid,allowed_roles text[]) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path='' AS $$
 SELECT EXISTS(SELECT 1 FROM public.tenancy_memberships m WHERE m.org_id=target_org AND m.user_id=auth.uid()
  AND m.is_active AND m.role::text=ANY(allowed_roles) AND m.org_id IN(SELECT private.current_user_org_ids()));
$$;
CREATE OR REPLACE FUNCTION private.can_manage_catalog(target_org uuid) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path='' AS $$
 SELECT EXISTS(SELECT 1 FROM public.tenancy_memberships m WHERE m.org_id=target_org AND m.user_id=auth.uid()
  AND m.is_active AND m.org_id IN(SELECT private.current_user_org_ids())
  AND (m.role='WORKSHOP_MANAGER' OR (m.role='OWNER' AND auth.jwt()->>'aal'='aal2')));
$$;
CREATE FUNCTION private.company_assurance(p_org uuid) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path='' AS $$
 SELECT EXISTS(SELECT 1 FROM public.tenancy_memberships m WHERE m.org_id=p_org AND m.user_id=auth.uid() AND m.is_active) AND (coalesce(auth.jwt()->>'aal'='aal2',false) OR
  (EXISTS(SELECT 1 FROM public.tenancy_organizations o WHERE o.id=p_org AND NOT o.require_mfa)
   AND NOT private.documentary_role(p_org,ARRAY['OWNER'])));
$$;
REVOKE ALL ON FUNCTION private.company_assurance(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.company_assurance(uuid) TO authenticated,documentary_backend,pricing_backend;

-- A master record also contains legacy notes/contact details; floor roles do
-- not gain dossier access by bypassing the HTTP surface through PostgREST.
DROP POLICY clients_member_read ON public.clients;
CREATE POLICY clients_member_read ON public.clients FOR SELECT
 USING(private.documentary_role(org_id,ARRAY['OWNER','ESTIMATOR','WORKSHOP_MANAGER']) AND private.company_assurance(org_id));
DROP POLICY clients_member_insert ON public.clients;
CREATE POLICY clients_member_insert ON public.clients FOR INSERT
 WITH CHECK(private.documentary_role(org_id,ARRAY['OWNER','ESTIMATOR']) AND private.company_assurance(org_id));
DROP POLICY clients_member_update ON public.clients;
CREATE POLICY clients_member_update ON public.clients FOR UPDATE
 USING(private.documentary_role(org_id,ARRAY['OWNER','ESTIMATOR']) AND private.company_assurance(org_id))
 WITH CHECK(private.documentary_role(org_id,ARRAY['OWNER','ESTIMATOR']) AND private.company_assurance(org_id));

CREATE FUNCTION private.client_rut_key(value text) RETURNS text
LANGUAGE sql IMMUTABLE SET search_path='' AS $$
 SELECT nullif(regexp_replace(upper(coalesce(value,'')), '[.\s-]', '', 'g'),'');
$$;
REVOKE ALL ON FUNCTION private.client_rut_key(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.client_rut_key(text) TO authenticated, documentary_backend, service_role;
CREATE FUNCTION private.client_rut_valid(value text) RETURNS boolean
LANGUAGE plpgsql IMMUTABLE SET search_path='' AS $$
DECLARE key text:=private.client_rut_key(value); body text; tally integer:=0; result integer;
BEGIN
 IF key IS NULL OR key !~ '^[0-9]{5,8}[0-9K]$' THEN RETURN false; END IF;
 body:=left(key,length(key)-1);
 IF body::bigint=0 THEN RETURN false; END IF;
 FOR i IN 0..length(body)-1 LOOP tally:=tally+substr(body,length(body)-i,1)::integer*(2+i%6); END LOOP;
 result:=11-tally%11;
 RETURN right(key,1)=CASE WHEN result=11 THEN '0' WHEN result=10 THEN 'K' ELSE result::text END;
END $$;
REVOKE ALL ON FUNCTION private.client_rut_valid(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.client_rut_valid(text) TO authenticated,documentary_backend,service_role;

ALTER TABLE public.clients
 ADD COLUMN party_kind text NOT NULL DEFAULT 'UNKNOWN' CHECK (party_kind IN ('PERSON','COMPANY','UNKNOWN')),
 ADD COLUMN merged_into_id uuid,
 ADD CONSTRAINT clients_org_identity UNIQUE(org_id,id),
 ADD CONSTRAINT clients_merge_org_fk FOREIGN KEY(org_id,merged_into_id) REFERENCES public.clients(org_id,id),
 ADD CONSTRAINT clients_not_self_merge CHECK (merged_into_id IS DISTINCT FROM id);
-- Historical aliases retain their RUT; uniqueness applies to canonical identities.
ALTER TABLE public.clients DROP CONSTRAINT uk_org_client_rut;
CREATE INDEX clients_rut_identity ON public.clients(org_id,private.client_rut_key(rut)) WHERE merged_into_id IS NULL;

CREATE TABLE public.client_contacts (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id),
 client_id uuid NOT NULL,
 name text NOT NULL DEFAULT '' CHECK(length(name)<=255),
 contact_role text NOT NULL DEFAULT '' CHECK(length(contact_role)<=80),
 email text NOT NULL DEFAULT '' CHECK(length(email)<=255),
 phone text NOT NULL DEFAULT '' CHECK(length(phone)<=64),
 is_primary boolean NOT NULL DEFAULT false,
 is_active boolean NOT NULL DEFAULT true,
 origin_id uuid REFERENCES public.client_contacts(id),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 FOREIGN KEY(org_id,client_id) REFERENCES public.clients(org_id,id),
 UNIQUE(org_id,id),
 CHECK(length(btrim(email))>0 OR length(btrim(phone))>0)
);
CREATE UNIQUE INDEX client_primary_contact ON public.client_contacts(org_id,client_id) WHERE is_primary AND is_active;
CREATE TABLE public.client_addresses (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id),
 client_id uuid NOT NULL,
 label text NOT NULL CHECK(length(btrim(label)) BETWEEN 1 AND 80),
 address text NOT NULL CHECK(length(btrim(address)) BETWEEN 1 AND 500),
 comuna text NOT NULL DEFAULT '' CHECK(length(comuna)<=80),
 is_active boolean NOT NULL DEFAULT true,
 origin_id uuid REFERENCES public.client_addresses(id),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 FOREIGN KEY(org_id,client_id) REFERENCES public.clients(org_id,id),
 UNIQUE(org_id,id)
);
CREATE TABLE public.client_notes (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id),
 client_id uuid NOT NULL,
 operation_key uuid,
 body text NOT NULL,
 created_by uuid,
 author_label text NOT NULL,
 is_legacy boolean NOT NULL DEFAULT false,
 source_updated_at timestamptz,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 FOREIGN KEY(org_id,client_id) REFERENCES public.clients(org_id,id),
 UNIQUE(org_id,operation_key),
 CHECK(length(btrim(body))>0 AND (is_legacy OR length(body)<=4000))
);
CREATE TABLE public.client_merges (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id),
 source_id uuid NOT NULL,
 target_id uuid NOT NULL,
 reason text NOT NULL CHECK(length(btrim(reason)) BETWEEN 1 AND 2000),
 actor_id uuid NOT NULL,
 actor_label text NOT NULL,
 before_record jsonb NOT NULL,
 after_record jsonb NOT NULL,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 FOREIGN KEY(org_id,source_id) REFERENCES public.clients(org_id,id),
 FOREIGN KEY(org_id,target_id) REFERENCES public.clients(org_id,id),
 UNIQUE(org_id,source_id),
 CHECK(source_id<>target_id)
);

-- Historical contact fields are explicit evidence, not a guessed person/type.
INSERT INTO public.client_contacts(org_id,client_id,email,phone,is_primary)
 SELECT org_id,id,coalesce(email,''),coalesce(phone,''),true FROM public.clients
 WHERE length(btrim(coalesce(email,'')))>0 OR length(btrim(coalesce(phone,'')))>0;
INSERT INTO public.client_notes(org_id,client_id,body,author_label,is_legacy,source_updated_at)
 SELECT org_id,id,notes,'Autor no registrado · nota histórica',true,updated_at FROM public.clients
 WHERE length(btrim(coalesce(notes,'')))>0;

ALTER TABLE public.client_contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.client_addresses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.client_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.client_merges ENABLE ROW LEVEL SECURITY;

DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['client_contacts','client_addresses','client_notes','client_merges'] LOOP
  EXECUTE format('REVOKE ALL ON public.%I FROM PUBLIC,anon,authenticated',t);
  EXECUTE format('GRANT SELECT ON public.%I TO authenticated,documentary_backend',t);
  EXECUTE format('GRANT ALL ON public.%I TO service_role',t);
 END LOOP;
END $$;
CREATE POLICY client_contacts_read ON public.client_contacts FOR SELECT
 USING(private.documentary_role(org_id,ARRAY['OWNER','ESTIMATOR','WORKSHOP_MANAGER']) AND private.company_assurance(org_id));
CREATE POLICY client_addresses_read ON public.client_addresses FOR SELECT
 USING(private.documentary_role(org_id,ARRAY['OWNER','ESTIMATOR','WORKSHOP_MANAGER']) AND private.company_assurance(org_id));
CREATE POLICY client_notes_read ON public.client_notes FOR SELECT
 USING(private.documentary_role(org_id,ARRAY['OWNER','ESTIMATOR']) AND private.company_assurance(org_id));
CREATE POLICY client_merges_read ON public.client_merges FOR SELECT
 USING(private.documentary_role(org_id,ARRAY['OWNER','ESTIMATOR']) AND private.company_assurance(org_id));
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['client_contacts','client_addresses','client_notes'] LOOP
  EXECUTE format('CREATE POLICY %I ON public.%I FOR INSERT WITH CHECK (private.documentary_role(org_id,ARRAY[''OWNER'',''ESTIMATOR'']) AND private.company_assurance(org_id) AND EXISTS(SELECT 1 FROM public.clients c WHERE c.org_id=%I.org_id AND c.id=%I.client_id AND c.merged_into_id IS NULL))',t||'_write',t,t,t);
 END LOOP;
 FOREACH t IN ARRAY ARRAY['client_contacts','client_addresses'] LOOP
  EXECUTE format('CREATE POLICY %I ON public.%I FOR UPDATE USING(private.documentary_role(org_id,ARRAY[''OWNER'',''ESTIMATOR'']) AND private.company_assurance(org_id)) WITH CHECK(private.documentary_role(org_id,ARRAY[''OWNER'',''ESTIMATOR'']) AND private.company_assurance(org_id) AND EXISTS(SELECT 1 FROM public.clients c WHERE c.org_id=%I.org_id AND c.id=%I.client_id AND c.merged_into_id IS NULL))',t||'_update',t,t,t);
 END LOOP;
END $$;
GRANT INSERT(id,org_id,client_id,name,contact_role,email,phone,is_primary,is_active) ON public.client_contacts TO authenticated;
GRANT UPDATE(name,contact_role,email,phone,is_primary,is_active,updated_at) ON public.client_contacts TO authenticated;
GRANT INSERT(id,org_id,client_id,label,address,comuna,is_active) ON public.client_addresses TO authenticated;
GRANT UPDATE(label,address,comuna,is_active,updated_at) ON public.client_addresses TO authenticated;
GRANT INSERT(id,org_id,client_id,operation_key,body) ON public.client_notes TO authenticated;

CREATE FUNCTION private.client_note_author() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
BEGIN
 IF auth.uid() IS NULL THEN
  IF current_setting('role',true) IN('none','service_role') THEN
   NEW.created_by:=NULL; NEW.author_label:='Autor no registrado · nota importada';
   NEW.is_legacy:=true; NEW.created_at:=clock_timestamp(); RETURN NEW;
  END IF;
  RAISE EXCEPTION 'client_note_actor_required';
 END IF;
 NEW.created_by:=auth.uid();
 SELECT email INTO NEW.author_label FROM auth.users WHERE id=auth.uid();
 IF NEW.author_label IS NULL THEN RAISE EXCEPTION 'client_note_actor_required'; END IF;
 NEW.is_legacy:=false; NEW.source_updated_at:=NULL; NEW.created_at:=clock_timestamp();
 RETURN NEW;
END $$;
CREATE TRIGGER client_note_author BEFORE INSERT ON public.client_notes FOR EACH ROW EXECUTE FUNCTION private.client_note_author();
CREATE FUNCTION private.client_evidence_immutable() RETURNS trigger
LANGUAGE plpgsql SET search_path='' AS $$ BEGIN RAISE EXCEPTION 'client_evidence_immutable'; END $$;
CREATE TRIGGER client_note_immutable BEFORE UPDATE OR DELETE ON public.client_notes FOR EACH ROW EXECUTE FUNCTION private.client_evidence_immutable();
CREATE TRIGGER client_merge_immutable BEFORE UPDATE OR DELETE ON public.client_merges FOR EACH ROW EXECUTE FUNCTION private.client_evidence_immutable();
CREATE TRIGGER client_note_no_truncate BEFORE TRUNCATE ON public.client_notes FOR EACH STATEMENT EXECUTE FUNCTION private.client_evidence_immutable();
CREATE TRIGGER client_merge_no_truncate BEFORE TRUNCATE ON public.client_merges FOR EACH STATEMENT EXECUTE FUNCTION private.client_evidence_immutable();
CREATE FUNCTION private.capture_client_legacy_note() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
BEGIN
 IF length(btrim(coalesce(NEW.notes,'')))=0 THEN RETURN NEW; END IF;
 IF TG_OP='INSERT' OR NEW.notes IS DISTINCT FROM OLD.notes THEN
  INSERT INTO public.client_notes(org_id,client_id,body,author_label,source_updated_at)
  VALUES(NEW.org_id,NEW.id,NEW.notes,'',NEW.updated_at);
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER capture_client_legacy_note AFTER INSERT OR UPDATE OF notes ON public.clients FOR EACH ROW EXECUTE FUNCTION private.capture_client_legacy_note();

-- Former broad table grants must not permit creating or clearing an alias.
REVOKE INSERT,UPDATE ON public.clients FROM authenticated;
GRANT INSERT(id,org_id,name,rut,email,phone,address,giro,comuna,notes,is_active,created_by,party_kind) ON public.clients TO authenticated;
GRANT UPDATE(name,rut,email,phone,address,giro,comuna,notes,is_active,party_kind,updated_at) ON public.clients TO authenticated;
-- Acquire the same ordered tenant locks before row locks, including direct
-- authenticated writes. This prevents child edits racing a reviewed merge.
CREATE FUNCTION private.lock_client_dossiers() RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$ DECLARE identity uuid; BEGIN
 IF current_setting('role',true)='authenticated' THEN
  FOR identity IN SELECT private.current_user_org_ids() ORDER BY 1 LOOP
   PERFORM pg_advisory_xact_lock(hashtextextended('clients:'||identity::text,0));
  END LOOP;
 END IF;
END $$;
REVOKE ALL ON FUNCTION private.lock_client_dossiers() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.lock_client_dossiers() TO authenticated;
CREATE FUNCTION private.lock_client_statement() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$ BEGIN
 PERFORM private.lock_client_dossiers(); RETURN NULL;
END $$;
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['clients','client_contacts','client_addresses','client_notes'] LOOP
  EXECUTE format('CREATE TRIGGER lock_client_statement BEFORE INSERT OR UPDATE ON public.%I FOR EACH STATEMENT EXECUTE FUNCTION private.lock_client_statement()',t);
 END LOOP;
END $$;

CREATE FUNCTION private.client_identity_guard() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE key text;
BEGIN
 IF TG_OP='UPDATE' AND OLD.merged_into_id IS NOT NULL AND NEW IS DISTINCT FROM OLD THEN
  RAISE EXCEPTION 'client_merged_immutable';
 END IF;
 NEW.updated_at:=clock_timestamp();
 IF TG_OP='INSERT' OR NEW.rut IS DISTINCT FROM OLD.rut THEN
  key:=private.client_rut_key(NEW.rut);
  IF key IS NOT NULL AND (TG_OP='INSERT' OR key IS DISTINCT FROM private.client_rut_key(OLD.rut))
     AND current_setting('role',true)='authenticated' AND NOT private.client_rut_valid(NEW.rut) THEN
   RAISE EXCEPTION 'client_rut_invalid' USING ERRCODE='23514';
  END IF;
  IF key IS NOT NULL AND (TG_OP='INSERT' OR key IS DISTINCT FROM private.client_rut_key(OLD.rut)) THEN
   -- Privileged import also serializes identities; authenticated locks were
   -- acquired by the statement trigger before PostgreSQL acquired row locks.
   PERFORM pg_advisory_xact_lock(hashtextextended('clients:'||NEW.org_id::text,0));
   IF EXISTS(SELECT 1 FROM public.clients c WHERE c.org_id=NEW.org_id AND c.id<>NEW.id AND c.merged_into_id IS NULL AND private.client_rut_key(c.rut)=key) THEN
    RAISE EXCEPTION 'client_rut_conflict' USING ERRCODE='23505';
   END IF;
  END IF;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER client_identity_guard BEFORE INSERT OR UPDATE ON public.clients FOR EACH ROW EXECUTE FUNCTION private.client_identity_guard();
-- Child changes participate in the dossier CAS, including direct RLS writes.
CREATE FUNCTION private.touch_client_dossier() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$ BEGIN
 UPDATE public.clients SET updated_at=clock_timestamp() WHERE org_id=NEW.org_id AND id=NEW.client_id;
 RETURN NEW;
END $$;
CREATE TRIGGER touch_client_contacts AFTER INSERT OR UPDATE ON public.client_contacts FOR EACH ROW EXECUTE FUNCTION private.touch_client_dossier();
CREATE TRIGGER touch_client_addresses AFTER INSERT OR UPDATE ON public.client_addresses FOR EACH ROW EXECUTE FUNCTION private.touch_client_dossier();

ALTER TABLE public.projects ADD COLUMN client_address_id uuid,
 ADD CONSTRAINT project_client_address_org_fk FOREIGN KEY(org_id,client_address_id) REFERENCES public.client_addresses(org_id,id);
GRANT SELECT(client_address_id),INSERT(client_address_id),UPDATE(client_address_id) ON public.projects TO authenticated;
GRANT SELECT(client_address_id) ON public.projects TO documentary_backend,pricing_backend;
CREATE FUNCTION private.project_work_address() RETURNS trigger
LANGUAGE plpgsql SET search_path='' AS $$ DECLARE a public.client_addresses;
BEGIN
 IF NEW.client_address_id IS NULL THEN RETURN NEW; END IF;
 IF TG_OP='UPDATE' AND NEW.client_id IS NOT DISTINCT FROM OLD.client_id AND NEW.client_address_id IS NOT DISTINCT FROM OLD.client_address_id THEN
  -- Preserve the copied snapshot when the master changes; an explicit text
  -- edit becomes an independent work address, including direct RLS writes.
  IF NEW.delivery_address IS DISTINCT FROM OLD.delivery_address THEN NEW.client_address_id:=NULL; END IF;
  RETURN NEW;
 END IF;
 SELECT * INTO a FROM public.client_addresses WHERE id=NEW.client_address_id AND org_id=NEW.org_id AND client_id=NEW.client_id AND is_active FOR SHARE;
 IF NOT FOUND THEN RAISE EXCEPTION 'client_address_not_available'; END IF;
 NEW.delivery_address:=a.address||CASE WHEN length(btrim(a.comuna))>0 THEN ', '||a.comuna ELSE '' END;
 RETURN NEW;
END $$;
CREATE TRIGGER project_work_address BEFORE INSERT OR UPDATE ON public.projects FOR EACH ROW EXECUTE FUNCTION private.project_work_address();

CREATE FUNCTION private.merge_clients(p_org uuid,p_source uuid,p_target uuid,
 p_source_updated timestamptz,p_target_updated timestamptz,p_reason text) RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE s public.clients; t public.clients; before_value jsonb; after_value jsonb; actor_email text;
BEGIN
 IF NOT private.documentary_role(p_org,ARRAY['OWNER','ESTIMATOR']) OR NOT private.company_assurance(p_org) THEN RAISE EXCEPTION 'client_merge_denied'; END IF;
 IF p_source=p_target OR length(btrim(coalesce(p_reason,''))) NOT BETWEEN 1 AND 2000 THEN RAISE EXCEPTION 'client_merge_invalid'; END IF;
 PERFORM private.lock_client_dossiers();
 PERFORM id FROM public.clients WHERE org_id=p_org AND id IN(p_source,p_target) ORDER BY id FOR UPDATE;
 SELECT * INTO s FROM public.clients WHERE org_id=p_org AND id=p_source;
 IF NOT FOUND THEN RAISE EXCEPTION 'client_not_found'; END IF;
 SELECT * INTO t FROM public.clients WHERE org_id=p_org AND id=p_target;
 IF NOT FOUND THEN RAISE EXCEPTION 'client_not_found'; END IF;
 IF s.merged_into_id IS NOT NULL OR t.merged_into_id IS NOT NULL THEN RAISE EXCEPTION 'client_already_merged'; END IF;
 IF s.updated_at IS DISTINCT FROM p_source_updated OR t.updated_at IS DISTINCT FROM p_target_updated THEN RAISE EXCEPTION 'client_merge_stale'; END IF;
 IF private.client_rut_key(s.rut) IS NOT NULL AND private.client_rut_key(t.rut) IS NOT NULL AND private.client_rut_key(s.rut)<>private.client_rut_key(t.rut) THEN RAISE EXCEPTION 'client_merge_rut_mismatch'; END IF;
 SELECT email INTO actor_email FROM auth.users WHERE id=auth.uid() AND email_confirmed_at IS NOT NULL;
 IF actor_email IS NULL THEN RAISE EXCEPTION 'client_merge_actor_required'; END IF;
 before_value:=jsonb_build_object('source',to_jsonb(s),'target',to_jsonb(t),
  'source_contacts',(SELECT coalesce(jsonb_agg(to_jsonb(c) ORDER BY c.id),'[]'::jsonb) FROM public.client_contacts c WHERE c.org_id=p_org AND c.client_id=p_source),
  'source_addresses',(SELECT coalesce(jsonb_agg(to_jsonb(a) ORDER BY a.id),'[]'::jsonb) FROM public.client_addresses a WHERE a.org_id=p_org AND a.client_id=p_source),
  'target_contacts',(SELECT coalesce(jsonb_agg(to_jsonb(c) ORDER BY c.id),'[]'::jsonb) FROM public.client_contacts c WHERE c.org_id=p_org AND c.client_id=p_target),
  'target_addresses',(SELECT coalesce(jsonb_agg(to_jsonb(a) ORDER BY a.id),'[]'::jsonb) FROM public.client_addresses a WHERE a.org_id=p_org AND a.client_id=p_target));
 UPDATE public.clients SET merged_into_id=p_target,is_active=false WHERE org_id=p_org AND id=p_source;
 -- Only missing master fields are adopted. The preview must show these exact rules.
 UPDATE public.clients SET
  rut=coalesce(nullif(btrim(t.rut),''),s.rut),
  email=coalesce(nullif(btrim(t.email),''),s.email),
  phone=coalesce(nullif(btrim(t.phone),''),s.phone),
  address=coalesce(nullif(btrim(t.address),''),s.address),
  giro=coalesce(nullif(btrim(t.giro),''),s.giro),
  comuna=coalesce(nullif(btrim(t.comuna),''),s.comuna),
  party_kind=CASE WHEN t.party_kind='UNKNOWN' THEN s.party_kind ELSE t.party_kind END
 WHERE org_id=p_org AND id=p_target;
 INSERT INTO public.client_contacts(org_id,client_id,name,contact_role,email,phone,is_primary,origin_id)
 SELECT p_org,p_target,c.name,c.contact_role,c.email,c.phone,
  c.is_primary AND NOT EXISTS(SELECT 1 FROM public.client_contacts x WHERE x.org_id=p_org AND x.client_id=p_target AND x.is_primary AND x.is_active),coalesce(c.origin_id,c.id)
 FROM public.client_contacts c WHERE c.org_id=p_org AND c.client_id=p_source AND c.is_active
 AND NOT EXISTS(SELECT 1 FROM public.client_contacts x WHERE x.org_id=p_org AND x.client_id=p_target AND x.is_active
  AND ROW(x.name,x.contact_role,x.email,x.phone) IS NOT DISTINCT FROM ROW(c.name,c.contact_role,c.email,c.phone));
 INSERT INTO public.client_addresses(org_id,client_id,label,address,comuna,origin_id)
 SELECT p_org,p_target,a.label,a.address,a.comuna,coalesce(a.origin_id,a.id) FROM public.client_addresses a
 WHERE a.org_id=p_org AND a.client_id=p_source AND a.is_active
 AND NOT EXISTS(SELECT 1 FROM public.client_addresses x WHERE x.org_id=p_org AND x.client_id=p_target AND x.is_active
  AND ROW(x.label,x.address,x.comuna) IS NOT DISTINCT FROM ROW(a.label,a.address,a.comuna));
 SELECT jsonb_build_object('source',to_jsonb(s2),'target',to_jsonb(t2),
  'target_contacts',(SELECT coalesce(jsonb_agg(to_jsonb(c) ORDER BY c.id),'[]'::jsonb) FROM public.client_contacts c WHERE c.org_id=p_org AND c.client_id=p_target),
  'target_addresses',(SELECT coalesce(jsonb_agg(to_jsonb(a) ORDER BY a.id),'[]'::jsonb) FROM public.client_addresses a WHERE a.org_id=p_org AND a.client_id=p_target)) INTO after_value
 FROM public.clients s2,public.clients t2 WHERE s2.org_id=p_org AND s2.id=p_source AND t2.org_id=p_org AND t2.id=p_target;
 INSERT INTO public.client_merges(org_id,source_id,target_id,reason,actor_id,actor_label,before_record,after_record)
 VALUES(p_org,p_source,p_target,btrim(p_reason),auth.uid(),actor_email,before_value,after_value);
 RETURN p_target;
END $$;
REVOKE ALL ON FUNCTION private.merge_clients(uuid,uuid,uuid,timestamptz,timestamptz,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.merge_clients(uuid,uuid,uuid,timestamptz,timestamptz,text) TO authenticated;

COMMIT;
