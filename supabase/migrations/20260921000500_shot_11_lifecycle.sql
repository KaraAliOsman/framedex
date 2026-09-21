-- PD-11-02/03: attributable credits and immutable lifecycle evidence.
BEGIN;
ALTER TABLE public.credit_lots ADD COLUMN origin TEXT NOT NULL DEFAULT 'legacy'
  CHECK(origin IN ('trial','monthly','pack','legacy'));
UPDATE public.credit_lots l SET origin=CASE
  WHEN e.action_type='TRIAL_GRANT' THEN 'trial'
  WHEN e.action_type='PAYMENT_GRANT' AND l.expires_at IS NULL THEN 'pack'
  WHEN e.action_type='PAYMENT_GRANT' THEN 'monthly'
  ELSE 'legacy' END FROM public.credit_ledger e WHERE e.id=l.grant_id;

CREATE TABLE public.credit_lot_movements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
  lot_id UUID NOT NULL,
  ledger_id UUID NOT NULL,
  amount INTEGER NOT NULL CHECK(amount<>0),
  remaining_after INTEGER NOT NULL CHECK(remaining_after>=0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(lot_id,ledger_id),
  FOREIGN KEY(org_id,ledger_id) REFERENCES public.credit_ledger(org_id,id) ON DELETE CASCADE
);
ALTER TABLE public.credit_lots ADD CONSTRAINT credit_lot_org_identity UNIQUE(org_id,id);
ALTER TABLE public.credit_lot_movements ADD FOREIGN KEY(org_id,lot_id)
  REFERENCES public.credit_lots(org_id,id) ON DELETE CASCADE;
-- Do not fabricate attribution of historical spending. Such an upgrade needs an
-- explicit reconciliation, like the original wallet cutover.
DO $$ BEGIN
  IF EXISTS(SELECT 1 FROM public.credit_lots l JOIN public.credit_ledger e ON e.id=l.grant_id
            WHERE l.remaining<>e.amount) THEN
    RAISE EXCEPTION 'wallet_historical_consumption_requires_attribution';
  END IF;
END $$;
INSERT INTO public.credit_lot_movements(org_id,lot_id,ledger_id,amount,remaining_after)
  SELECT org_id,id,grant_id,remaining,remaining FROM public.credit_lots WHERE remaining>0;
CREATE FUNCTION private.wallet_lot_created() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path='' AS $$
BEGIN
  INSERT INTO public.credit_lot_movements(org_id,lot_id,ledger_id,amount,remaining_after)
    VALUES(NEW.org_id,NEW.id,NEW.grant_id,NEW.remaining,NEW.remaining);
  RETURN NEW;
END $$;
CREATE TRIGGER wallet_lot_created AFTER INSERT ON public.credit_lots
  FOR EACH ROW EXECUTE FUNCTION private.wallet_lot_created();
CREATE TRIGGER wallet_movement_immutable BEFORE UPDATE OR DELETE ON public.credit_lot_movements
  FOR EACH ROW EXECUTE FUNCTION private.wallet_immutable();
-- Origin defaults are derived from the durable grant; existing callers stay safe.
CREATE FUNCTION private.wallet_lot_origin() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path='' AS $$
DECLARE action TEXT;
BEGIN
  IF NEW.origin='pack' AND NEW.expires_at IS NOT NULL THEN
    RAISE EXCEPTION 'purchased_credits_cannot_expire' USING ERRCODE='23514';
  END IF;
  IF TG_OP='UPDATE' THEN
    IF (to_jsonb(NEW)-ARRAY['remaining','expires_at']) IS DISTINCT FROM
       (to_jsonb(OLD)-ARRAY['remaining','expires_at']) THEN
      RAISE EXCEPTION 'wallet_lot_origin_immutable' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
  END IF;
  IF NEW.origin='legacy' THEN
    SELECT action_type INTO action FROM public.credit_ledger WHERE id=NEW.grant_id AND org_id=NEW.org_id;
    IF action='TRIAL_GRANT' THEN NEW.origin='trial';
    ELSIF action IN ('MONTHLY_GRANT','UPGRADE_GRANT') THEN NEW.origin='monthly';
    ELSIF action='PAYMENT_GRANT' THEN
      NEW.origin=CASE WHEN NEW.expires_at IS NULL THEN 'pack' ELSE 'monthly' END;
    END IF;
  END IF;
  IF NEW.origin='pack' AND NEW.expires_at IS NOT NULL THEN
    RAISE EXCEPTION 'purchased_credits_cannot_expire' USING ERRCODE='23514';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER wallet_lot_origin BEFORE INSERT OR UPDATE ON public.credit_lots
  FOR EACH ROW EXECUTE FUNCTION private.wallet_lot_origin();

CREATE TABLE public.billing_periods (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
  subscription_id UUID NOT NULL,
  order_id UUID NOT NULL,
  period_start TIMESTAMPTZ NOT NULL,
  period_end TIMESTAMPTZ NOT NULL CHECK(period_end>period_start),
  plan_tier TEXT NOT NULL CHECK(plan_tier IN ('STARTER','PRO','BUSINESS','BUSINESS_2X')),
  billing_cycle TEXT NOT NULL CHECK(billing_cycle IN ('monthly','annual')),
  allowance INTEGER NOT NULL CHECK(allowance>=0),
  provider_evidence JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(org_id,id), UNIQUE(order_id), UNIQUE(subscription_id,period_start),
  FOREIGN KEY(org_id,subscription_id) REFERENCES public.subscriptions(org_id,id),
  FOREIGN KEY(org_id,order_id) REFERENCES public.billing_orders(org_id,id)
);
CREATE TABLE public.billing_lifecycle_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
  subscription_id UUID NOT NULL,
  period_id UUID NOT NULL,
  operation_key TEXT NOT NULL,
  kind TEXT NOT NULL CHECK(kind IN ('upgrade','downgrade','frequency','cancel','refund')),
  effective_at TIMESTAMPTZ NOT NULL,
  plan_tier TEXT NOT NULL CHECK(plan_tier IN ('STARTER','PRO','BUSINESS','BUSINESS_2X')),
  billing_cycle TEXT NOT NULL CHECK(billing_cycle IN ('monthly','annual')),
  allowance INTEGER NOT NULL CHECK(allowance>=0),
  evidence JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(org_id,operation_key),
  FOREIGN KEY(org_id,subscription_id) REFERENCES public.subscriptions(org_id,id),
  FOREIGN KEY(org_id,period_id) REFERENCES public.billing_periods(org_id,id)
);
CREATE TABLE public.flow_lifecycle_operations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
  subscription_id UUID,
  operation_key TEXT NOT NULL,
  kind TEXT NOT NULL CHECK(kind IN ('change','cancel','refund')),
  state TEXT NOT NULL DEFAULT 'prepared' CHECK(state IN
    ('prepared','dispatching','uncertain','confirmed','needs_admin')),
  authority JSONB NOT NULL,
  preview JSONB,
  result JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(org_id,operation_key),
  FOREIGN KEY(org_id,subscription_id) REFERENCES public.subscriptions(org_id,id)
);
CREATE UNIQUE INDEX flow_one_unresolved_change ON public.flow_lifecycle_operations(subscription_id)
  WHERE kind IN ('change','cancel') AND state IN ('prepared','dispatching','uncertain');
ALTER TABLE public.subscriptions ADD COLUMN current_period_start TIMESTAMPTZ;
ALTER TABLE public.credit_lot_movements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.billing_periods ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.billing_lifecycle_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.flow_lifecycle_operations ENABLE ROW LEVEL SECURITY;
DO $$ DECLARE target TEXT; BEGIN
  FOREACH target IN ARRAY ARRAY['credit_lot_movements','billing_periods','billing_lifecycle_events','flow_lifecycle_operations'] LOOP
    EXECUTE format('REVOKE ALL ON public.%I FROM PUBLIC,anon,authenticated',target);
    EXECUTE format('GRANT ALL ON public.%I TO service_role',target);
    EXECUTE format('GRANT SELECT,INSERT ON public.%I TO billing_backend',target);
    EXECUTE format('CREATE POLICY billing_backend_scope ON public.%I FOR ALL TO billing_backend USING(private.billing_scope(org_id)) WITH CHECK(private.billing_scope(org_id))',target);
    IF target<>'flow_lifecycle_operations' THEN
      EXECUTE format('CREATE TRIGGER billing_evidence_immutable BEFORE UPDATE OR DELETE ON public.%I FOR EACH ROW EXECUTE FUNCTION private.wallet_immutable()',target);
    END IF;
  END LOOP;
END $$;
GRANT UPDATE(state,preview,result) ON public.flow_lifecycle_operations TO billing_backend;
CREATE FUNCTION private.flow_operation_immutable() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path='' AS $$ BEGIN
  IF (to_jsonb(NEW)-ARRAY['state','preview','result']) IS DISTINCT FROM
     (to_jsonb(OLD)-ARRAY['state','preview','result'])
     OR (OLD.preview IS NOT NULL AND NEW.preview IS DISTINCT FROM OLD.preview)
     OR (OLD.state='confirmed' AND NEW IS DISTINCT FROM OLD) THEN
    RAISE EXCEPTION 'flow_operation_authority_immutable' USING ERRCODE='23514';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER flow_operation_immutable BEFORE UPDATE ON public.flow_lifecycle_operations
 FOR EACH ROW EXECUTE FUNCTION private.flow_operation_immutable();
REVOKE ALL ON FUNCTION private.wallet_lot_created(),private.wallet_lot_origin(),private.flow_operation_immutable() FROM PUBLIC;
CREATE FUNCTION private.wallet_attribution_check() RETURNS TRIGGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE target UUID; balance BIGINT; total BIGINT;
BEGIN
  target=NEW.org_id;
  SELECT credits_balance INTO balance FROM public.tenancy_organizations WHERE id=target;
  IF balance IS NULL THEN RETURN NULL; END IF;
  SELECT coalesce(sum(remaining),0) INTO total FROM public.credit_lots WHERE org_id=target;
  IF balance<>total OR EXISTS(
    SELECT 1 FROM public.credit_lots l WHERE l.org_id=target AND l.remaining<>(
      SELECT coalesce(sum(amount),0) FROM public.credit_lot_movements m WHERE m.org_id=target AND m.lot_id=l.id))
    OR EXISTS(SELECT 1 FROM public.credit_ledger e WHERE e.org_id=target AND e.amount<>(
      SELECT coalesce(sum(amount),0) FROM public.credit_lot_movements m WHERE m.org_id=target AND m.ledger_id=e.id)) THEN
    RAISE EXCEPTION 'wallet_attribution_mismatch' USING ERRCODE='23514';
  END IF;
  RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER wallet_attribution_check AFTER INSERT ON public.credit_ledger
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION private.wallet_attribution_check();
CREATE CONSTRAINT TRIGGER wallet_attribution_check AFTER INSERT OR UPDATE ON public.credit_lots
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION private.wallet_attribution_check();
CREATE CONSTRAINT TRIGGER wallet_attribution_check AFTER INSERT ON public.credit_lot_movements
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION private.wallet_attribution_check();
REVOKE ALL ON FUNCTION private.wallet_attribution_check() FROM PUBLIC;
COMMIT;
