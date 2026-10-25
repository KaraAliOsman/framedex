-- P12e · How a workshop measures. REQUIRED: every window needs a site
-- measurement confirmed before it can be manufactured (the historic rule).
-- QUOTED: the workshop declares that the quoted size is the fabrication size,
-- as a one-person workshop does; each sealed revision records which policy it
-- was issued under, so a change never reinterprets an issued revision.
BEGIN;

ALTER TABLE public.tenancy_organizations
    ADD COLUMN site_measurement text NOT NULL DEFAULT 'REQUIRED'
    CHECK (site_measurement IN ('REQUIRED', 'QUOTED'));
GRANT SELECT (site_measurement) ON public.tenancy_organizations TO authenticated, documentary_backend;

CREATE FUNCTION private.set_site_measurement(p_org uuid, p_value text) RETURNS text
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$ DECLARE previous text; BEGIN
 PERFORM private.require_company_owner(p_org);
 IF p_value NOT IN ('REQUIRED','QUOTED') THEN RAISE EXCEPTION 'site_measurement_invalid'; END IF;
 SELECT site_measurement INTO previous FROM public.tenancy_organizations WHERE id=p_org FOR UPDATE;
 IF previous IS DISTINCT FROM p_value THEN
  UPDATE public.tenancy_organizations SET site_measurement=p_value,updated_at=clock_timestamp() WHERE id=p_org;
  INSERT INTO public.organization_admin_events(org_id,actor_id,action,before_record,after_record)
   VALUES(p_org,auth.uid(),'SITE_MEASUREMENT',jsonb_build_object('site_measurement',previous),
          jsonb_build_object('site_measurement',p_value));
 END IF;
 RETURN p_value;
END $$;
REVOKE ALL ON FUNCTION private.set_site_measurement(uuid,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.set_site_measurement(uuid,text) TO authenticated;

COMMIT;
