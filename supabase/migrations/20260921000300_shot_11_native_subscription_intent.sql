BEGIN;

ALTER TABLE public.payment_customers ADD CONSTRAINT payment_customer_org_identity UNIQUE(org_id,id);
ALTER TABLE public.subscriptions DROP CONSTRAINT subscriptions_status_check;
ALTER TABLE public.subscriptions ADD CONSTRAINT subscriptions_status_check
  CHECK(status IN ('pending','active','past_due','cancelled','trialing'));

-- Trusted provisioning supplies a verified Flow plan/customer and explicit approved
-- commercial start terms. Creating a provider subscription does not prove payment.
CREATE TABLE public.flow_subscription_intents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
  operation_key TEXT NOT NULL,
  customer_id UUID NOT NULL,
  subscription_id UUID NOT NULL,
  provider_environment TEXT NOT NULL CHECK(provider_environment IN ('sandbox','production')),
  provider_customer_id TEXT NOT NULL,
  provider_plan_id TEXT NOT NULL,
  provider_subscription_id TEXT,
  net_usd NUMERIC(12,2) NOT NULL CHECK(net_usd>0),
  amount NUMERIC(12,2) NOT NULL CHECK(amount>0 AND amount=trunc(amount)),
  fx_rate NUMERIC NOT NULL CHECK(fx_rate>0 AND fx_rate<1000000),
  fx_source TEXT NOT NULL CHECK(length(trim(fx_source))>0),
  fx_observed_on DATE NOT NULL,
  fx_snapshot_id UUID NOT NULL,
  start_date DATE NOT NULL,
  trial_days INTEGER NOT NULL CHECK(trial_days>=0 AND trial_days<=7),
  policy_reference TEXT NOT NULL CHECK(length(trim(policy_reference))>0),
  state TEXT NOT NULL DEFAULT 'prepared' CHECK(state IN ('prepared','dispatching','uncertain','created')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(org_id,operation_key),
  UNIQUE(subscription_id),
  UNIQUE(provider_environment,provider_customer_id,provider_plan_id),
  UNIQUE(provider_environment,provider_subscription_id),
  FOREIGN KEY(org_id,customer_id) REFERENCES public.payment_customers(org_id,id) ON DELETE RESTRICT,
  FOREIGN KEY(org_id,subscription_id) REFERENCES public.subscriptions(org_id,id) ON DELETE RESTRICT
);
ALTER TABLE public.flow_subscription_intents ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.flow_subscription_intents FROM PUBLIC,anon,authenticated;
GRANT ALL ON public.flow_subscription_intents TO service_role;
GRANT SELECT,INSERT ON public.flow_subscription_intents TO billing_backend;
GRANT UPDATE(state,provider_subscription_id) ON public.flow_subscription_intents TO billing_backend;
CREATE POLICY billing_backend_scope ON public.flow_subscription_intents FOR ALL TO billing_backend
  USING(private.billing_scope(org_id)) WITH CHECK(private.billing_scope(org_id));

CREATE FUNCTION private.flow_subscription_intent_immutable() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path='' AS $$
BEGIN
  IF (to_jsonb(NEW)-ARRAY['state','provider_subscription_id']) IS DISTINCT FROM
     (to_jsonb(OLD)-ARRAY['state','provider_subscription_id'])
    OR (OLD.provider_subscription_id IS NOT NULL AND NEW.provider_subscription_id IS DISTINCT FROM OLD.provider_subscription_id)
    OR (OLD.state='created' AND NEW.state<>'created') THEN
    RAISE EXCEPTION 'flow_subscription_intent_immutable' USING ERRCODE='23514';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER flow_subscription_intent_immutable BEFORE UPDATE ON public.flow_subscription_intents
  FOR EACH ROW EXECUTE FUNCTION private.flow_subscription_intent_immutable();
REVOKE ALL ON FUNCTION private.flow_subscription_intent_immutable() FROM PUBLIC;

COMMIT;
