-- P16 · What each plan includes, enforced where access is granted.
-- Taller (STARTER) is one person who does everything; Pro and the trial add
-- up to two more people as partner, office or workshop, without a roles
-- screen; Empresa adds unlimited people, every role and the delegated
-- assistant. Downgrading never removes anyone: it only stops new seats and
-- new roles until the plan allows them again.
BEGIN;

CREATE FUNCTION private.plan_terms(p_tier text) RETURNS jsonb
LANGUAGE sql IMMUTABLE SET search_path='' AS $$
 SELECT CASE p_tier
  WHEN 'STARTER' THEN jsonb_build_object('seats',1,'roles',jsonb_build_array('OWNER'),'features',jsonb_build_array())
  WHEN 'BUSINESS' THEN jsonb_build_object('seats',NULL,
   'roles',jsonb_build_array('OWNER','ESTIMATOR','WORKSHOP_MANAGER','OPERATOR','INSTALLER'),
   'features',jsonb_build_array('client_3d','purchasing','cnc','roles','subagents','stations','field'))
  WHEN 'BUSINESS_2X' THEN jsonb_build_object('seats',NULL,
   'roles',jsonb_build_array('OWNER','ESTIMATOR','WORKSHOP_MANAGER','OPERATOR','INSTALLER'),
   'features',jsonb_build_array('client_3d','purchasing','cnc','roles','subagents','stations','field'))
  ELSE jsonb_build_object('seats',3,'roles',jsonb_build_array('OWNER','ESTIMATOR','WORKSHOP_MANAGER'),
   'features',jsonb_build_array('client_3d','purchasing','cnc'))
 END $$;
REVOKE ALL ON FUNCTION private.plan_terms(text) FROM PUBLIC;

-- Seats in use: active people plus live invitations, which already hold one.
CREATE FUNCTION private.plan_seats_used(p_org uuid) RETURNS TABLE(active_members bigint,pending_invitations bigint)
LANGUAGE sql STABLE SET search_path='' AS $$
 SELECT (SELECT count(*) FROM public.tenancy_memberships WHERE org_id=p_org AND is_active),
        (SELECT count(*) FROM public.organization_invitations WHERE org_id=p_org AND accepted_at IS NULL
          AND revoked_at IS NULL AND expires_at>clock_timestamp()) $$;
REVOKE ALL ON FUNCTION private.plan_seats_used(uuid) FROM PUBLIC;

CREATE FUNCTION private.organization_plan(p_org uuid) RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path='' AS $$ DECLARE tier text; used record; BEGIN
 IF NOT p_org IN(SELECT private.current_user_org_ids()) THEN RAISE EXCEPTION 'company_access_denied' USING ERRCODE='42501'; END IF;
 SELECT subscription_tier::text INTO tier FROM public.tenancy_organizations WHERE id=p_org;
 SELECT * INTO used FROM private.plan_seats_used(p_org);
 RETURN private.plan_terms(tier)||jsonb_build_object('code',tier,'active_members',used.active_members,
  'pending_invitations',used.pending_invitations);
END $$;
REVOKE ALL ON FUNCTION private.organization_plan(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.organization_plan(uuid) TO authenticated, documentary_backend, pricing_backend;

-- The portal reads only the features of the tenant its token is bound to.
CREATE FUNCTION private.portal_plan_features() RETURNS jsonb
LANGUAGE sql STABLE SECURITY DEFINER SET search_path='' AS $$
 SELECT coalesce(private.plan_terms(o.subscription_tier::text)->'features','[]'::jsonb)
 FROM public.tenancy_organizations o WHERE o.id=nullif(current_setting('app.portal_org_id',true),'')::uuid $$;
REVOKE ALL ON FUNCTION private.portal_plan_features() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.portal_plan_features() TO portal_backend;

-- A member (or the worker acting as one) asks whether the plan includes a feature.
CREATE FUNCTION private.plan_allows(p_org uuid,p_feature text) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path='' AS $$
 SELECT coalesce((SELECT private.plan_terms(o.subscription_tier::text)->'features' ? p_feature
  FROM public.tenancy_organizations o WHERE o.id=p_org AND p_org IN(SELECT private.current_user_org_ids())),false) $$;
REVOKE ALL ON FUNCTION private.plan_allows(uuid,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.plan_allows(uuid,text) TO authenticated, ai_backend, documentary_backend;

CREATE FUNCTION private.require_plan_access(p_org uuid,p_role text,p_new_seat boolean,p_pending_counts boolean) RETURNS void
LANGUAGE plpgsql STABLE SET search_path='' AS $$ DECLARE terms jsonb; used record; taken bigint; BEGIN
 SELECT private.plan_terms(subscription_tier::text) INTO terms FROM public.tenancy_organizations WHERE id=p_org;
 IF p_role IS NOT NULL AND NOT (terms->'roles') ? p_role THEN RAISE EXCEPTION 'company_plan_role_unavailable'; END IF;
 IF p_new_seat AND terms->>'seats' IS NOT NULL THEN
  SELECT * INTO used FROM private.plan_seats_used(p_org);
  taken:=used.active_members;
  IF p_pending_counts THEN taken:=taken+used.pending_invitations; END IF;
  IF taken>=(terms->>'seats')::int THEN RAISE EXCEPTION 'company_plan_seats_full'; END IF;
 END IF;
END $$;
REVOKE ALL ON FUNCTION private.require_plan_access(uuid,text,boolean,boolean) FROM PUBLIC;

CREATE OR REPLACE FUNCTION private.change_company_user(p_org uuid,p_id uuid,p_role text,p_active boolean,p_expected timestamptz) RETURNS void
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
 -- A role kept from a larger plan stays; a new role or a reactivation needs the current plan.
 PERFORM private.require_plan_access(p_org,CASE WHEN p_role<>old_row.role::text THEN p_role END,
  p_active AND NOT old_row.is_active,true);
 UPDATE public.tenancy_memberships SET role=p_role::public.org_role,is_active=p_active,updated_at=clock_timestamp() WHERE id=p_id AND org_id=p_org;
 INSERT INTO public.organization_admin_events(org_id,actor_id,action,before_record,after_record)
 SELECT p_org,auth.uid(),'MEMBERSHIP',to_jsonb(old_row),to_jsonb(m) FROM public.tenancy_memberships m WHERE m.id=p_id;
END $$;

CREATE OR REPLACE FUNCTION private.create_company_invitation(p_org uuid,p_key uuid,p_email text,p_role text,p_digest text) RETURNS uuid
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
 PERFORM private.require_plan_access(p_org,p_role,true,true);
 INSERT INTO public.organization_invitations(org_id,operation_key,email,role,token_digest,created_by,expires_at)
 VALUES(p_org,p_key,lower(btrim(p_email)),p_role::public.org_role,p_digest,auth.uid(),clock_timestamp()+interval '7 days') RETURNING id INTO identity;
 INSERT INTO public.organization_admin_events(org_id,actor_id,action,before_record,after_record)
 VALUES(p_org,auth.uid(),'INVITE','{}',jsonb_build_object('id',identity,'email',lower(btrim(p_email)),'role',p_role));
 RETURN identity;
END $$;

CREATE OR REPLACE FUNCTION private.accept_company_invitation(p_digest text) RETURNS uuid
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
 -- The plan may have shrunk since the invitation was sent.
 PERFORM private.require_plan_access(invitation.org_id,invitation.role::text,true,false);
 INSERT INTO public.tenancy_memberships(org_id,user_id,role) VALUES(invitation.org_id,auth.uid(),invitation.role);
 UPDATE public.organization_invitations SET accepted_by=auth.uid(),accepted_at=clock_timestamp() WHERE id=invitation.id;
 INSERT INTO public.organization_admin_events(org_id,actor_id,action,before_record,after_record) VALUES(invitation.org_id,auth.uid(),'ACCEPT_INVITATION','{}',jsonb_build_object('id',invitation.id,'role',invitation.role));
 RETURN invitation.org_id;
END $$;
COMMIT;
