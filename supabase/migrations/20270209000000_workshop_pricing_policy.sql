BEGIN;

-- Separate from the historical advanced rules: changing the workshop's working
-- policy never rewrites an applied operation or an issued revision.
CREATE TABLE public.workshop_pricing_policies (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL UNIQUE REFERENCES public.tenancy_organizations(id),
  currency public.currency_code NOT NULL,
  labor_rate numeric(14,4) NOT NULL CHECK(labor_rate>=0 AND labor_rate<'Infinity'::numeric),
  labor_basis text NOT NULL CHECK(labor_basis IN ('M2','WINDOW')),
  installation_rate numeric(14,4) NOT NULL CHECK(installation_rate>=0 AND installation_rate<'Infinity'::numeric),
  installation_basis text NOT NULL CHECK(installation_basis IN ('M2','WINDOW')),
  margin numeric(6,4) NOT NULL CHECK(margin>=0 AND margin<1),
  rounding_step numeric(14,4) NOT NULL CHECK(rounding_step>0 AND rounding_step<'Infinity'::numeric),
  waste numeric(6,4) NOT NULL CHECK(waste BETWEEN 0 AND 1),
  tax_rate numeric(6,4) NOT NULL CHECK(tax_rate BETWEEN 0 AND 1),
  use_advanced boolean NOT NULL DEFAULT false,
  revision bigint NOT NULL DEFAULT 1 CHECK(revision>0),
  updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  CHECK((currency='CLP' AND rounding_step>=1 AND mod(rounding_step,1)=0)
     OR (currency='USD' AND rounding_step>=0.01 AND mod(rounding_step,0.01)=0))
);
ALTER TABLE public.workshop_pricing_policies ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.workshop_pricing_policies FROM PUBLIC,anon,authenticated;
GRANT SELECT,INSERT,UPDATE ON public.workshop_pricing_policies TO authenticated;
GRANT SELECT ON public.workshop_pricing_policies TO pricing_backend;
CREATE POLICY workshop_policy_owner ON public.workshop_pricing_policies
  FOR ALL TO authenticated USING(private.pricing_role(org_id,ARRAY['OWNER']) AND auth.jwt()->>'aal'='aal2')
  WITH CHECK(private.pricing_role(org_id,ARRAY['OWNER']) AND auth.jwt()->>'aal'='aal2');
CREATE POLICY workshop_policy_calculator ON public.workshop_pricing_policies
  FOR SELECT TO pricing_backend USING(org_id IN(SELECT private.pricing_read_org_ids()));

CREATE FUNCTION private.workshop_policy_version() RETURNS trigger
LANGUAGE plpgsql SET search_path='' AS $$
BEGIN
  IF TG_OP='UPDATE' THEN
    IF NEW.id<>OLD.id OR NEW.org_id<>OLD.org_id THEN
      RAISE EXCEPTION 'workshop_policy_identity_immutable' USING ERRCODE='23514';
    END IF;
    NEW.revision := OLD.revision+1;
  ELSE
    NEW.revision := 1;
  END IF;
  NEW.updated_at := clock_timestamp();
  RETURN NEW;
END; $$;
REVOKE ALL ON FUNCTION private.workshop_policy_version() FROM PUBLIC;
CREATE TRIGGER a_workshop_policy_version BEFORE INSERT OR UPDATE
  ON public.workshop_pricing_policies FOR EACH ROW EXECUTE FUNCTION private.workshop_policy_version();
CREATE TRIGGER pricing_audit_before BEFORE INSERT OR UPDATE
  ON public.workshop_pricing_policies FOR EACH ROW EXECUTE FUNCTION private.audit_pricing_mutation();

COMMIT;
