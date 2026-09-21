BEGIN;

-- Frozen server-side expectations. No browser or callback can author these values.
CREATE TABLE public.billing_orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
  operation_key TEXT NOT NULL,
  provider TEXT NOT NULL CHECK(provider='flow'),
  provider_environment TEXT NOT NULL CHECK(provider_environment IN ('sandbox','production')),
  commerce_order TEXT NOT NULL,
  provider_payment_id TEXT,
  subscription_id UUID,
  provider_invoice_id TEXT,
  amount NUMERIC(12,2) NOT NULL CHECK(amount>0 AND amount=trunc(amount)),
  net_usd NUMERIC(12,2) NOT NULL CHECK(net_usd>0),
  fx_rate NUMERIC NOT NULL CHECK(fx_rate>0 AND fx_rate<1000000),
  fx_source TEXT NOT NULL CHECK(length(trim(fx_source))>0),
  fx_observed_on DATE NOT NULL,
  fx_snapshot_id UUID NOT NULL,
  state TEXT NOT NULL DEFAULT 'prepared' CHECK(state IN
    ('prepared','dispatching','pending','uncertain','succeeded','failed')),
  payment_id UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(org_id,id),
  UNIQUE(org_id,operation_key),
  UNIQUE(provider,provider_environment,commerce_order),
  UNIQUE(provider,provider_environment,provider_payment_id),
  UNIQUE(provider,provider_environment,provider_invoice_id),
  FOREIGN KEY(org_id,subscription_id) REFERENCES public.subscriptions(org_id,id) ON DELETE RESTRICT,
  CHECK((subscription_id IS NULL) = (provider_invoice_id IS NULL))
);
ALTER TABLE public.payments ADD CONSTRAINT payment_org_identity UNIQUE(org_id,id);
ALTER TABLE public.billing_orders ADD FOREIGN KEY(org_id,payment_id)
  REFERENCES public.payments(org_id,id) ON DELETE RESTRICT;

-- Schedules must be supplied by an approved commercial policy, never inferred from
-- callback data. Annual monthly delivery uses several scheduled rows for one order.
CREATE TABLE public.billing_credit_grants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
  order_id UUID NOT NULL,
  installment INTEGER NOT NULL CHECK(installment>=0),
  credits INTEGER NOT NULL CHECK(credits>0),
  available_at TIMESTAMPTZ NOT NULL,
  expires_at TIMESTAMPTZ,
  policy_reference TEXT NOT NULL CHECK(length(trim(policy_reference))>0),
  ledger_id UUID,
  UNIQUE(order_id,installment),
  FOREIGN KEY(org_id,order_id) REFERENCES public.billing_orders(org_id,id) ON DELETE CASCADE,
  FOREIGN KEY(org_id,ledger_id) REFERENCES public.credit_ledger(org_id,id) ON DELETE RESTRICT,
  CHECK(expires_at IS NULL OR expires_at>available_at)
);

DO $$ DECLARE target TEXT; BEGIN
  FOREACH target IN ARRAY ARRAY['billing_orders','billing_credit_grants'] LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY',target);
    EXECUTE format('REVOKE ALL ON public.%I FROM PUBLIC,anon,authenticated',target);
    EXECUTE format('GRANT ALL ON public.%I TO service_role',target);
    EXECUTE format('GRANT SELECT,INSERT ON public.%I TO billing_backend',target);
    EXECUTE format('CREATE POLICY billing_backend_scope ON public.%I FOR ALL TO billing_backend '
      'USING(private.billing_scope(org_id)) WITH CHECK(private.billing_scope(org_id))',target);
  END LOOP;
END $$;
GRANT UPDATE(state,provider_payment_id,payment_id,updated_at) ON public.billing_orders TO billing_backend;
GRANT UPDATE(ledger_id) ON public.billing_credit_grants TO billing_backend;

CREATE FUNCTION private.billing_contract_immutable() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path='' AS $$
BEGIN
  IF TG_TABLE_NAME='billing_orders' THEN
    IF (to_jsonb(NEW)-ARRAY['state','provider_payment_id','payment_id','updated_at'])
        IS DISTINCT FROM (to_jsonb(OLD)-ARRAY['state','provider_payment_id','payment_id','updated_at'])
      OR (OLD.provider_payment_id IS NOT NULL AND NEW.provider_payment_id IS DISTINCT FROM OLD.provider_payment_id)
      OR (OLD.payment_id IS NOT NULL AND NEW.payment_id IS DISTINCT FROM OLD.payment_id)
      OR (OLD.state='succeeded' AND NEW.state<>'succeeded') THEN
      RAISE EXCEPTION 'billing_order_immutable' USING ERRCODE='23514';
    END IF;
  ELSE
    IF (to_jsonb(NEW)-'ledger_id') IS DISTINCT FROM (to_jsonb(OLD)-'ledger_id')
      OR (OLD.ledger_id IS NOT NULL AND NEW.ledger_id IS DISTINCT FROM OLD.ledger_id) THEN
      RAISE EXCEPTION 'billing_grant_immutable' USING ERRCODE='23514';
    END IF;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER billing_order_immutable BEFORE UPDATE ON public.billing_orders
  FOR EACH ROW EXECUTE FUNCTION private.billing_contract_immutable();
CREATE TRIGGER billing_grant_immutable BEFORE UPDATE ON public.billing_credit_grants
  FOR EACH ROW EXECUTE FUNCTION private.billing_contract_immutable();
REVOKE ALL ON FUNCTION private.billing_contract_immutable() FROM PUBLIC;

COMMIT;
