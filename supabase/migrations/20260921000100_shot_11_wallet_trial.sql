BEGIN;

DO $$ BEGIN
  IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='billing_backend') THEN
    CREATE ROLE billing_backend NOLOGIN NOSUPERUSER NOBYPASSRLS;
  END IF;
END $$;
GRANT billing_backend TO postgres;
GRANT USAGE ON SCHEMA public,private,auth TO billing_backend;
GRANT EXECUTE ON FUNCTION private.current_user_org_ids(),auth.uid(),auth.jwt() TO billing_backend;

CREATE FUNCTION private.billing_scope(target UUID) RETURNS BOOLEAN
LANGUAGE sql STABLE SET search_path='' AS $$
  SELECT target = NULLIF(current_setting('app.billing_org',true),'')::uuid;
$$;
REVOKE ALL ON FUNCTION private.billing_scope(UUID) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.billing_scope(UUID) TO billing_backend;

ALTER TABLE public.credit_ledger ADD COLUMN operation_key TEXT;
ALTER TABLE public.credit_ledger ADD COLUMN entry_number BIGINT GENERATED ALWAYS AS IDENTITY;
ALTER TABLE public.credit_ledger ADD CONSTRAINT ledger_org_identity UNIQUE(org_id,id);
CREATE UNIQUE INDEX wallet_operation_once ON public.credit_ledger(org_id,operation_key);

CREATE TABLE public.credit_lots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
  grant_id UUID NOT NULL UNIQUE,
  remaining INTEGER NOT NULL CHECK(remaining >= 0),
  expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  FOREIGN KEY(org_id,grant_id) REFERENCES public.credit_ledger(org_id,id) ON DELETE CASCADE
);
ALTER TABLE public.credit_lots ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.credit_lots FROM PUBLIC,anon,authenticated;
GRANT ALL ON public.credit_lots TO service_role;

-- Preserve legacy evidence. Reject inconsistent historical financial data rather than
-- repairing it with fabricated credits. Old balances without a ledger are opening balances.
DO $$ BEGIN
  IF EXISTS(SELECT 1 FROM public.credit_ledger) THEN
    RAISE EXCEPTION 'wallet_legacy_history_requires_explicit_lot_reconciliation';
  END IF;
  IF EXISTS(SELECT 1 FROM public.tenancy_organizations o
    WHERE EXISTS(SELECT 1 FROM public.credit_ledger l WHERE l.org_id=o.id)
      AND o.credits_balance <> (SELECT sum(amount) FROM public.credit_ledger l WHERE l.org_id=o.id)) THEN
    RAISE EXCEPTION 'wallet_legacy_balance_requires_reconciliation';
  END IF;
END $$;
INSERT INTO public.credit_ledger(org_id,amount,balance_after,action_type,operation_key)
  SELECT id,credits_balance,credits_balance,'MIGRATION_OPENING','migration-opening'
  FROM public.tenancy_organizations o WHERE credits_balance > 0
    AND NOT EXISTS(SELECT 1 FROM public.credit_ledger l WHERE l.org_id=o.id);
UPDATE public.tenancy_organizations SET trial_ends_at=created_at+interval '7 days'
  WHERE subscription_tier='TRIAL';
DO $$ BEGIN
  IF EXISTS(SELECT 1 FROM public.tenancy_organizations
            WHERE subscription_tier='TRIAL' AND credits_balance>500) THEN
    RAISE EXCEPTION 'wallet_legacy_trial_exceeds_cap';
  END IF;
END $$;
INSERT INTO public.credit_lots(org_id,grant_id,remaining,expires_at)
  SELECT o.id,l.id,o.credits_balance,CASE WHEN o.subscription_tier='TRIAL' THEN o.trial_ends_at END
  FROM public.tenancy_organizations o
  CROSS JOIN LATERAL (SELECT id FROM public.credit_ledger WHERE org_id=o.id
                      ORDER BY created_at DESC,id DESC LIMIT 1) l
  WHERE o.credits_balance > 0;

CREATE FUNCTION private.wallet_append() RETURNS TRIGGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE balance INTEGER;
BEGIN
  SELECT credits_balance INTO STRICT balance FROM public.tenancy_organizations
    WHERE id=NEW.org_id FOR UPDATE;
  IF NEW.amount=0 OR NEW.balance_after <> balance+NEW.amount OR NEW.balance_after<0 THEN
    RAISE EXCEPTION 'wallet_invalid_balance' USING ERRCODE='23514';
  END IF;
  UPDATE public.tenancy_organizations SET credits_balance=NEW.balance_after WHERE id=NEW.org_id;
  RETURN NEW;
END $$;
CREATE TRIGGER wallet_append BEFORE INSERT ON public.credit_ledger
  FOR EACH ROW EXECUTE FUNCTION private.wallet_append();

CREATE FUNCTION private.wallet_immutable() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path='' AS $$
BEGIN
  IF TG_OP='DELETE' AND NOT EXISTS(SELECT 1 FROM public.tenancy_organizations WHERE id=OLD.org_id) THEN
    RETURN OLD; -- Explicit parent removal, not editable ledger history.
  END IF;
  RAISE EXCEPTION 'wallet_evidence_immutable' USING ERRCODE='23514';
END $$;
CREATE TRIGGER wallet_immutable BEFORE UPDATE OR DELETE ON public.credit_ledger
  FOR EACH ROW EXECUTE FUNCTION private.wallet_immutable();

CREATE FUNCTION private.wallet_balance_check() RETURNS TRIGGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE target UUID; balance BIGINT; total BIGINT;
BEGIN
  IF TG_TABLE_NAME='tenancy_organizations' THEN target=NEW.id; ELSE target=NEW.org_id; END IF;
  SELECT credits_balance INTO balance FROM public.tenancy_organizations WHERE id=target;
  IF balance IS NULL THEN RETURN NULL; END IF;
  SELECT coalesce(sum(amount),0) INTO total FROM public.credit_ledger WHERE org_id=target;
  IF balance<>total THEN RAISE EXCEPTION 'wallet_ledger_balance_mismatch' USING ERRCODE='23514'; END IF;
  RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER wallet_balance_check AFTER INSERT OR UPDATE ON public.tenancy_organizations
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION private.wallet_balance_check();
CREATE CONSTRAINT TRIGGER wallet_balance_check AFTER INSERT ON public.credit_ledger
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION private.wallet_balance_check();

CREATE FUNCTION private.wallet_new_org() RETURNS TRIGGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE grant_id UUID;
BEGIN
  IF TG_WHEN='BEFORE' THEN
    NEW.credits_balance=0;
    IF NEW.subscription_tier='TRIAL' THEN NEW.trial_ends_at=NEW.created_at+interval '7 days';
    ELSE NEW.trial_ends_at=NULL; END IF;
    RETURN NEW;
  END IF;
  IF NEW.subscription_tier='TRIAL' THEN
    INSERT INTO public.credit_ledger(org_id,amount,balance_after,action_type,operation_key,expires_at)
      VALUES(NEW.id,500,500,'TRIAL_GRANT','trial-grant',NEW.trial_ends_at) RETURNING id INTO grant_id;
    INSERT INTO public.credit_lots(org_id,grant_id,remaining,expires_at)
      VALUES(NEW.id,grant_id,500,NEW.trial_ends_at);
  END IF;
  RETURN NEW;
END $$;
ALTER TABLE public.tenancy_organizations ALTER COLUMN credits_balance SET DEFAULT 0;
CREATE TRIGGER wallet_new_org_before BEFORE INSERT ON public.tenancy_organizations
  FOR EACH ROW EXECUTE FUNCTION private.wallet_new_org();
CREATE TRIGGER wallet_new_org_after AFTER INSERT ON public.tenancy_organizations
  FOR EACH ROW EXECUTE FUNCTION private.wallet_new_org();

DO $$ DECLARE target TEXT; BEGIN
  FOREACH target IN ARRAY ARRAY['payment_customers','subscriptions','payments','payment_events',
                                 'credit_ledger','credit_lots','ai_audit_logs'] LOOP
    EXECUTE format('CREATE POLICY billing_backend_scope ON public.%I FOR ALL TO billing_backend '
      'USING(private.billing_scope(org_id)) WITH CHECK(private.billing_scope(org_id))',target);
    EXECUTE format('CREATE POLICY billing_backend_restrict ON public.%I AS RESTRICTIVE FOR ALL TO billing_backend '
      'USING(private.billing_scope(org_id)) WITH CHECK(private.billing_scope(org_id))',target);
  END LOOP;
END $$;
CREATE POLICY billing_backend_org ON public.tenancy_organizations FOR ALL TO billing_backend
  USING(private.billing_scope(id)) WITH CHECK(private.billing_scope(id));
CREATE POLICY billing_backend_org_restrict ON public.tenancy_organizations AS RESTRICTIVE FOR ALL TO billing_backend
  USING(private.billing_scope(id)) WITH CHECK(private.billing_scope(id));
GRANT SELECT ON public.tenancy_organizations,public.ai_audit_logs TO billing_backend;
GRANT UPDATE(subscription_tier,subscription_active,billing_cycle,updated_at)
  ON public.tenancy_organizations TO billing_backend;
GRANT SELECT,INSERT ON public.credit_ledger TO billing_backend;
GRANT SELECT,INSERT ON public.credit_lots TO billing_backend;
GRANT UPDATE(remaining) ON public.credit_lots TO billing_backend;
GRANT SELECT,INSERT,UPDATE ON public.payment_customers,public.subscriptions,public.payments,
  public.payment_events TO billing_backend;

REVOKE ALL ON FUNCTION private.wallet_append(),private.wallet_immutable(),
  private.wallet_balance_check(),private.wallet_new_org() FROM PUBLIC;

COMMIT;
