BEGIN;

-- The preferred quotation currency does not reinterpret existing labor/installation
-- tariffs, which retain the organization's established base-currency authority.
ALTER TABLE public.tenancy_organizations ADD COLUMN quotation_currency public.currency_code;
GRANT SELECT(quotation_currency) ON public.tenancy_organizations TO authenticated,documentary_backend,pricing_backend;

-- No direct member can change legal identity, membership or invitation evidence.
CREATE TABLE public.organization_invitations (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id),
 operation_key uuid NOT NULL,
 email text NOT NULL CHECK(length(email)<=255),
 role public.org_role NOT NULL,
 token_digest text NOT NULL UNIQUE CHECK(token_digest ~ '^[0-9a-f]{64}$'),
 created_by uuid NOT NULL,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 expires_at timestamptz NOT NULL,
 accepted_by uuid,
 accepted_at timestamptz,
 revoked_at timestamptz,
 mail_id uuid REFERENCES public.mail_outbox(id),
 UNIQUE(org_id,operation_key)
);
CREATE TABLE public.organization_admin_events (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id),
 actor_id uuid NOT NULL,
 action text NOT NULL,
 before_record jsonb NOT NULL,
 after_record jsonb NOT NULL,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
ALTER TABLE public.organization_invitations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.organization_admin_events ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.organization_invitations,public.organization_admin_events FROM PUBLIC,anon,authenticated;
GRANT ALL ON public.organization_invitations,public.organization_admin_events TO service_role;
CREATE POLICY organization_invitations_owner ON public.organization_invitations USING(private.documentary_role(org_id,ARRAY['OWNER']) AND private.company_assurance(org_id));
CREATE POLICY organization_admin_events_owner ON public.organization_admin_events USING(private.documentary_role(org_id,ARRAY['OWNER']) AND private.company_assurance(org_id));
GRANT SELECT(id,org_id,email,role,created_at,expires_at,accepted_at,revoked_at,mail_id) ON public.organization_invitations TO authenticated;
GRANT SELECT ON public.organization_admin_events TO authenticated;
CREATE TRIGGER organization_admin_events_immutable BEFORE UPDATE OR DELETE ON public.organization_admin_events FOR EACH ROW EXECUTE FUNCTION private.client_evidence_immutable();
CREATE TRIGGER organization_admin_events_no_truncate BEFORE TRUNCATE ON public.organization_admin_events FOR EACH STATEMENT EXECUTE FUNCTION private.client_evidence_immutable();

CREATE FUNCTION private.require_company_owner(p_org uuid) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$ BEGIN
 IF NOT private.documentary_role(p_org,ARRAY['OWNER']) OR NOT private.company_assurance(p_org) THEN
  RAISE EXCEPTION 'company_owner_required' USING ERRCODE='42501';
 END IF;
END $$;
REVOKE ALL ON FUNCTION private.require_company_owner(uuid) FROM PUBLIC;

CREATE FUNCTION private.company_settings(p_org uuid) RETURNS TABLE(name text,tax_id text,currency text,base_currency text,require_mfa boolean,updated_at timestamptz)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path='' AS $$ BEGIN
 IF NOT p_org IN(SELECT private.current_user_org_ids()) OR NOT private.company_assurance(p_org) THEN RAISE EXCEPTION 'company_access_denied' USING ERRCODE='42501'; END IF;
 RETURN QUERY SELECT o.name::text,o.tax_id::text,coalesce(o.quotation_currency,o.currency)::text,o.currency::text,o.require_mfa,o.updated_at FROM public.tenancy_organizations o WHERE o.id=p_org;
END $$;

CREATE FUNCTION private.save_company(p_org uuid,p_name text,p_tax text,p_currency text,p_mfa boolean,p_expected timestamptz) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$ DECLARE old_value jsonb; BEGIN
 PERFORM private.require_company_owner(p_org);
 SELECT to_jsonb(o) INTO old_value FROM public.tenancy_organizations o WHERE o.id=p_org FOR UPDATE;
 PERFORM private.require_company_owner(p_org);
 IF (old_value->>'updated_at')::timestamptz IS DISTINCT FROM p_expected THEN RAISE EXCEPTION 'company_stale_edit'; END IF;
 IF length(btrim(p_name)) NOT BETWEEN 1 AND 255 OR length(p_tax)>50 THEN RAISE EXCEPTION 'company_invalid'; END IF;
 IF p_tax IS DISTINCT FROM old_value->>'tax_id' AND NOT private.client_rut_valid(p_tax) THEN RAISE EXCEPTION 'company_rut_invalid'; END IF;
 UPDATE public.tenancy_organizations SET name=btrim(p_name),tax_id=btrim(p_tax),quotation_currency=p_currency::public.currency_code,require_mfa=p_mfa,updated_at=clock_timestamp() WHERE id=p_org;
 INSERT INTO public.organization_admin_events(org_id,actor_id,action,before_record,after_record)
 SELECT p_org,auth.uid(),'COMPANY',jsonb_build_object('name',old_value->'name','tax_id',old_value->'tax_id','currency',coalesce(old_value->>'quotation_currency',old_value->>'currency'),'require_mfa',old_value->'require_mfa'),
 jsonb_build_object('name',o.name,'tax_id',o.tax_id,'currency',coalesce(o.quotation_currency,o.currency),'require_mfa',o.require_mfa) FROM public.tenancy_organizations o WHERE o.id=p_org;
END $$;

CREATE FUNCTION private.company_users(p_org uuid) RETURNS TABLE(id uuid,email text,role text,is_active boolean,updated_at timestamptz)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path='' AS $$ BEGIN
 PERFORM private.require_company_owner(p_org);
 RETURN QUERY SELECT m.id,coalesce(u.email,'Identidad no disponible')::text,m.role::text,m.is_active,m.updated_at
 FROM public.tenancy_memberships m LEFT JOIN auth.users u ON u.id=m.user_id WHERE m.org_id=p_org ORDER BY m.is_active DESC,u.email,m.id;
END $$;

CREATE FUNCTION private.change_company_user(p_org uuid,p_id uuid,p_role text,p_active boolean,p_expected timestamptz) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$ DECLARE old_row public.tenancy_memberships; BEGIN
 PERFORM private.require_company_owner(p_org);
 -- One organization lock serializes last-owner checks and invitation acceptance.
 PERFORM id FROM public.tenancy_organizations WHERE id=p_org FOR UPDATE;
 PERFORM private.require_company_owner(p_org);
 SELECT * INTO old_row FROM public.tenancy_memberships WHERE id=p_id AND org_id=p_org FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'company_user_not_found'; END IF;
 IF old_row.updated_at IS DISTINCT FROM p_expected THEN RAISE EXCEPTION 'company_user_stale'; END IF;
 IF old_row.role='OWNER' AND old_row.is_active AND (p_role<>'OWNER' OR NOT p_active) AND NOT EXISTS(
 SELECT 1 FROM public.tenancy_memberships WHERE org_id=p_org AND id<>p_id AND is_active AND role='OWNER') THEN RAISE EXCEPTION 'company_last_owner'; END IF;
 UPDATE public.tenancy_memberships SET role=p_role::public.org_role,is_active=p_active,updated_at=clock_timestamp() WHERE id=p_id AND org_id=p_org;
 INSERT INTO public.organization_admin_events(org_id,actor_id,action,before_record,after_record)
 SELECT p_org,auth.uid(),'MEMBERSHIP',to_jsonb(old_row),to_jsonb(m) FROM public.tenancy_memberships m WHERE m.id=p_id;
END $$;

CREATE FUNCTION private.create_company_invitation(p_org uuid,p_key uuid,p_email text,p_role text,p_digest text) RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$ DECLARE invitation public.organization_invitations; identity uuid; BEGIN
 PERFORM private.require_company_owner(p_org);
 PERFORM id FROM public.tenancy_organizations WHERE id=p_org FOR UPDATE;
 PERFORM private.require_company_owner(p_org);
 SELECT * INTO invitation FROM public.organization_invitations WHERE org_id=p_org AND operation_key=p_key;
 IF FOUND THEN
  IF invitation.email<>lower(btrim(p_email)) OR invitation.role::text<>p_role THEN RAISE EXCEPTION 'company_invitation_key_conflict'; END IF;
  RETURN invitation.id;
 END IF;
 IF EXISTS(SELECT 1 FROM public.tenancy_memberships m JOIN auth.users u ON u.id=m.user_id WHERE m.org_id=p_org AND m.is_active AND lower(u.email)=lower(btrim(p_email))) THEN RAISE EXCEPTION 'company_user_already_active'; END IF;
 IF EXISTS(SELECT 1 FROM public.organization_invitations WHERE org_id=p_org AND email=lower(btrim(p_email)) AND accepted_at IS NULL AND revoked_at IS NULL AND expires_at>clock_timestamp()) THEN RAISE EXCEPTION 'company_invitation_pending'; END IF;
 INSERT INTO public.organization_invitations(org_id,operation_key,email,role,token_digest,created_by,expires_at)
 VALUES(p_org,p_key,lower(btrim(p_email)),p_role::public.org_role,p_digest,auth.uid(),clock_timestamp()+interval '7 days') RETURNING id INTO identity;
 INSERT INTO public.organization_admin_events(org_id,actor_id,action,before_record,after_record)
 VALUES(p_org,auth.uid(),'INVITE','{}',jsonb_build_object('id',identity,'email',lower(btrim(p_email)),'role',p_role));
 RETURN identity;
END $$;

CREATE FUNCTION private.link_company_invitation_mail(p_org uuid,p_id uuid,p_mail uuid) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$ BEGIN
 PERFORM private.require_company_owner(p_org);
 IF NOT EXISTS(SELECT 1 FROM public.mail_outbox WHERE id=p_mail AND org_id=p_org AND kind='INVITATION') THEN RAISE EXCEPTION 'company_invitation_mail_invalid'; END IF;
 UPDATE public.organization_invitations SET mail_id=p_mail WHERE org_id=p_org AND id=p_id AND mail_id IS NULL;
END $$;

CREATE FUNCTION private.revoke_company_invitation(p_org uuid,p_id uuid) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$ BEGIN
 PERFORM private.require_company_owner(p_org);
 UPDATE public.organization_invitations SET revoked_at=clock_timestamp() WHERE org_id=p_org AND id=p_id AND accepted_at IS NULL AND revoked_at IS NULL;
 IF NOT FOUND THEN RAISE EXCEPTION 'company_invitation_not_pending'; END IF;
 INSERT INTO public.organization_admin_events(org_id,actor_id,action,before_record,after_record) VALUES(p_org,auth.uid(),'REVOKE_INVITATION',jsonb_build_object('id',p_id),'{}');
END $$;

-- A verified user can inspect/accept their capability before acquiring membership.
CREATE FUNCTION private.inspect_company_invitation(p_digest text) RETURNS TABLE(organization_name text,email text,role text,expires_at timestamptz,accepted boolean)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path='' AS $$ BEGIN
 RETURN QUERY SELECT o.name::text,i.email,i.role::text,i.expires_at,coalesce(i.accepted_by=auth.uid(),false)
 FROM public.organization_invitations i JOIN public.tenancy_organizations o ON o.id=i.org_id JOIN auth.users u ON u.id=auth.uid()
 WHERE i.token_digest=p_digest AND i.revoked_at IS NULL AND u.email_confirmed_at IS NOT NULL AND u.deleted_at IS NULL AND lower(u.email)=i.email
 AND (i.accepted_by=auth.uid() OR EXISTS(SELECT 1 FROM public.tenancy_memberships m WHERE m.org_id=i.org_id AND m.user_id=i.created_by AND m.is_active AND m.role='OWNER'))
 AND (i.expires_at>clock_timestamp() OR i.accepted_by=auth.uid());
END $$;

CREATE FUNCTION private.accept_company_invitation(p_digest text) RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$ DECLARE invitation public.organization_invitations; live_email text; BEGIN
 SELECT lower(email) INTO live_email FROM auth.users WHERE id=auth.uid() AND email_confirmed_at IS NOT NULL AND deleted_at IS NULL;
 IF live_email IS NULL THEN RAISE EXCEPTION 'company_invitation_identity_required'; END IF;
 SELECT * INTO invitation FROM public.organization_invitations WHERE token_digest=p_digest;
 IF NOT FOUND OR invitation.email<>live_email THEN RAISE EXCEPTION 'company_invitation_not_available'; END IF;
 PERFORM id FROM public.tenancy_organizations WHERE id=invitation.org_id FOR UPDATE;
 SELECT * INTO invitation FROM public.organization_invitations WHERE id=invitation.id FOR UPDATE;
 IF invitation.accepted_by=auth.uid() THEN RETURN invitation.org_id; END IF;
 IF invitation.accepted_at IS NOT NULL OR invitation.revoked_at IS NOT NULL OR invitation.expires_at<=clock_timestamp() THEN RAISE EXCEPTION 'company_invitation_not_available'; END IF;
 IF NOT EXISTS(SELECT 1 FROM public.tenancy_memberships WHERE org_id=invitation.org_id AND user_id=invitation.created_by AND is_active AND role='OWNER') THEN RAISE EXCEPTION 'company_invitation_not_available'; END IF;
 IF (invitation.role='OWNER' OR (SELECT require_mfa FROM public.tenancy_organizations WHERE id=invitation.org_id)) AND coalesce(auth.jwt()->>'aal','')<>'aal2' THEN RAISE EXCEPTION 'company_invitation_mfa_required'; END IF;
 IF EXISTS(SELECT 1 FROM public.tenancy_memberships WHERE org_id=invitation.org_id AND user_id=auth.uid()) THEN
  -- A prior deactivation cannot be bypassed by an old invitation.
  RAISE EXCEPTION 'company_invitation_membership_exists';
 END IF;
 INSERT INTO public.tenancy_memberships(org_id,user_id,role) VALUES(invitation.org_id,auth.uid(),invitation.role);
 UPDATE public.organization_invitations SET accepted_by=auth.uid(),accepted_at=clock_timestamp() WHERE id=invitation.id;
 INSERT INTO public.organization_admin_events(org_id,actor_id,action,before_record,after_record) VALUES(invitation.org_id,auth.uid(),'ACCEPT_INVITATION','{}',jsonb_build_object('id',invitation.id,'role',invitation.role));
 RETURN invitation.org_id;
END $$;

CREATE FUNCTION private.company_numbering(p_org uuid) RETURNS TABLE(prefix text,next_number bigint)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path='' AS $$ BEGIN
 IF NOT p_org IN(SELECT private.current_user_org_ids()) OR NOT private.company_assurance(p_org) THEN RAISE EXCEPTION 'company_access_denied'; END IF;
 RETURN QUERY SELECT 'P'::text,CASE WHEN is_called THEN last_value+1 ELSE last_value END FROM public.project_code_seq
 UNION ALL SELECT k,coalesce(c.last_value,0)+1 FROM unnest(ARRAY['OC','RT','REC']) k LEFT JOIN public.entity_code_counters c ON c.org_id=p_org AND c.kind=k;
END $$;

DO $$ DECLARE signature text; BEGIN
 FOREACH signature IN ARRAY ARRAY['company_settings(uuid)','save_company(uuid,text,text,text,boolean,timestamptz)','company_users(uuid)',
 'change_company_user(uuid,uuid,text,boolean,timestamptz)','create_company_invitation(uuid,uuid,text,text,text)',
 'link_company_invitation_mail(uuid,uuid,uuid)','revoke_company_invitation(uuid,uuid)','inspect_company_invitation(text)','accept_company_invitation(text)','company_numbering(uuid)'] LOOP
  EXECUTE 'REVOKE ALL ON FUNCTION private.'||signature||' FROM PUBLIC';
  EXECUTE 'GRANT EXECUTE ON FUNCTION private.'||signature||' TO authenticated';
 END LOOP;
END $$;

-- The encrypted outbox may deliver this explicit human invitation.
ALTER TABLE public.mail_outbox DROP CONSTRAINT mail_outbox_kind_check;
ALTER TABLE public.mail_outbox ADD CONSTRAINT mail_outbox_kind_check CHECK(kind IN('MAGIC_LINK','QUOTE','APPROVAL','PAYMENT','ORDER_BLOCKED','PURCHASE','COLLECTION','INVITATION'));
COMMIT;
