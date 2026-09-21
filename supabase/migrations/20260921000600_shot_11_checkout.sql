BEGIN;
ALTER TABLE public.flow_lifecycle_operations DROP CONSTRAINT flow_lifecycle_operations_state_check;
ALTER TABLE public.flow_lifecycle_operations ADD CONSTRAINT flow_lifecycle_operations_state_check
 CHECK(state IN ('prepared','dispatching','uncertain','confirmed','needs_admin','abandoned'));
-- Provisioned server authority: OWNER customers select only opaque offer IDs.
CREATE TABLE public.billing_offers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
  product_code TEXT NOT NULL,
  kind TEXT NOT NULL CHECK(kind IN ('subscription','pack')),
  plan_tier TEXT CHECK(plan_tier IN ('STARTER','PRO','BUSINESS','BUSINESS_2X')),
  billing_cycle TEXT CHECK(billing_cycle IN ('monthly','annual')),
  credits INTEGER NOT NULL CHECK(credits>=0),
  provider_environment TEXT NOT NULL CHECK(provider_environment IN ('sandbox','production')),
  provider_plan_id TEXT,
  net_usd NUMERIC(12,2) NOT NULL CHECK(net_usd>0),
  amount NUMERIC(12,2) NOT NULL CHECK(amount>0 AND amount=trunc(amount)),
  fx_rate NUMERIC NOT NULL CHECK(fx_rate>0 AND fx_rate<1000000),
  fx_source TEXT NOT NULL CHECK(length(trim(fx_source))>0),
  fx_observed_on DATE NOT NULL,
  fx_snapshot_id UUID NOT NULL,
  active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(org_id,id),
  UNIQUE(org_id,provider_environment,provider_plan_id),
  CHECK((kind='subscription' AND plan_tier IS NOT NULL AND billing_cycle IS NOT NULL AND provider_plan_id IS NOT NULL)
     OR (kind='pack' AND plan_tier IS NULL AND billing_cycle IS NULL AND provider_plan_id IS NULL AND credits>0))
);
CREATE TRIGGER billing_offer_audit BEFORE INSERT OR UPDATE OR DELETE ON public.billing_offers
  FOR EACH ROW EXECUTE FUNCTION private.audit_pricing_mutation();
CREATE FUNCTION private.billing_offer_immutable() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path='' AS $$ BEGIN
  IF (to_jsonb(NEW)-'active') IS DISTINCT FROM (to_jsonb(OLD)-'active') THEN
    RAISE EXCEPTION 'billing_offer_immutable' USING ERRCODE='23514';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER billing_offer_immutable BEFORE UPDATE ON public.billing_offers
  FOR EACH ROW EXECUTE FUNCTION private.billing_offer_immutable();
CREATE TABLE public.billing_checkouts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
  user_id UUID NOT NULL,
  operation_key UUID NOT NULL,
  offer_id UUID NOT NULL,
  start_date DATE NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(org_id,operation_key),
  FOREIGN KEY(org_id,offer_id) REFERENCES public.billing_offers(org_id,id)
);
CREATE TRIGGER billing_checkout_immutable BEFORE UPDATE OR DELETE ON public.billing_checkouts
  FOR EACH ROW EXECUTE FUNCTION private.wallet_immutable();
ALTER TABLE public.billing_offers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.billing_checkouts ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.billing_offers,public.billing_checkouts FROM PUBLIC,anon,authenticated;
GRANT ALL ON public.billing_offers,public.billing_checkouts TO service_role;
GRANT SELECT ON public.billing_offers TO billing_backend;
GRANT SELECT,INSERT ON public.billing_checkouts TO billing_backend;
CREATE POLICY billing_backend_scope ON public.billing_offers FOR ALL TO billing_backend
 USING(private.billing_scope(org_id)) WITH CHECK(private.billing_scope(org_id));
CREATE POLICY billing_backend_scope ON public.billing_checkouts FOR ALL TO billing_backend
 USING(private.billing_scope(org_id)) WITH CHECK(private.billing_scope(org_id));
REVOKE ALL ON FUNCTION private.billing_offer_immutable() FROM PUBLIC;
-- Keep unmatched provider evidence without treating an adjustment as a new allowance.
CREATE TABLE public.billing_invoice_observations (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
 subscription_id UUID NOT NULL,
 provider_environment TEXT NOT NULL CHECK(provider_environment IN ('sandbox','production')),
 provider_invoice_id TEXT NOT NULL,
 evidence JSONB NOT NULL CHECK(jsonb_typeof(evidence)='object'),
 evidence_hash TEXT NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 UNIQUE(org_id,provider_environment,provider_invoice_id,evidence_hash),
 FOREIGN KEY(org_id,subscription_id) REFERENCES public.subscriptions(org_id,id)
);
CREATE TRIGGER billing_invoice_observation_immutable BEFORE UPDATE OR DELETE ON public.billing_invoice_observations
 FOR EACH ROW EXECUTE FUNCTION private.wallet_immutable();
ALTER TABLE public.billing_invoice_observations ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.billing_invoice_observations FROM PUBLIC,anon,authenticated;
GRANT ALL ON public.billing_invoice_observations TO service_role;
GRANT SELECT,INSERT ON public.billing_invoice_observations TO billing_backend;
CREATE POLICY billing_backend_scope ON public.billing_invoice_observations FOR ALL TO billing_backend
 USING(private.billing_scope(org_id)) WITH CHECK(private.billing_scope(org_id));
COMMIT;
