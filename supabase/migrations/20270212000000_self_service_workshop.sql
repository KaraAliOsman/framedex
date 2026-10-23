-- P10 · First use (F1): a person with a verified email creates their own
-- workshop. One call creates the organization (Chile defaults: CLP, IVA from
-- the simple pricing policy, America/Santiago, live trial) and the person's
-- OWNER membership. Only someone without any membership may do it, once; the
-- owner's second factor is enrolled by the usual sign-in flow afterwards.
BEGIN;

CREATE FUNCTION private.create_own_workshop(p_name text) RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE live_email text; created uuid; workshop text := btrim(coalesce(p_name, ''));
BEGIN
 SELECT lower(email) INTO live_email FROM auth.users
  WHERE id=auth.uid() AND email_confirmed_at IS NOT NULL AND deleted_at IS NULL;
 IF live_email IS NULL THEN RAISE EXCEPTION 'workshop_identity_required' USING ERRCODE='42501'; END IF;
 -- One creation per person: concurrent calls of the same person serialize here.
 PERFORM pg_advisory_xact_lock(hashtextextended('create_own_workshop:'||auth.uid()::text, 0));
 IF EXISTS(SELECT 1 FROM public.tenancy_memberships WHERE user_id=auth.uid()) THEN
  RAISE EXCEPTION 'workshop_membership_exists';
 END IF;
 IF length(workshop) NOT BETWEEN 2 AND 120 THEN RAISE EXCEPTION 'workshop_name_invalid'; END IF;
 -- The legal identity (RUT) is confirmed in the first-use company step.
 INSERT INTO public.tenancy_organizations(name,tax_id) VALUES(workshop,'') RETURNING id INTO created;
 INSERT INTO public.tenancy_memberships(org_id,user_id,role) VALUES(created,auth.uid(),'OWNER');
 INSERT INTO public.organization_admin_events(org_id,actor_id,action,before_record,after_record)
  VALUES(created,auth.uid(),'CREATE_WORKSHOP','{}',jsonb_build_object('name',workshop));
 RETURN created;
END $$;
REVOKE ALL ON FUNCTION private.create_own_workshop(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.create_own_workshop(text) TO authenticated;

COMMIT;
