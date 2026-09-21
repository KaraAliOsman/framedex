BEGIN;

-- Supabase platform default privileges can be broader than explicit baseline GRANTs.
REVOKE ALL ON public.tenancy_organizations FROM anon, authenticated;
GRANT SELECT ON public.tenancy_organizations TO authenticated;

-- Foundational billing tables predate the OWNER-only S20/S24 capability contract.
-- Direct authenticated writes cannot be trusted, even from an OWNER browser.
REVOKE ALL ON public.payment_customers, public.subscriptions, public.payments,
  public.credit_ledger, public.payment_events FROM anon, authenticated;
GRANT SELECT ON public.payment_customers, public.subscriptions, public.payments,
  public.credit_ledger TO authenticated;

DROP POLICY payment_customers_isolation ON public.payment_customers;
DROP POLICY subscriptions_isolation ON public.subscriptions;
DROP POLICY payments_isolation ON public.payments;
DROP POLICY credit_ledger_isolation ON public.credit_ledger;

DO $$
DECLARE target TEXT;
BEGIN
  FOREACH target IN ARRAY ARRAY['payment_customers','subscriptions','payments','credit_ledger']
  LOOP
    EXECUTE format(
      'CREATE POLICY billing_owner_read ON public.%I FOR SELECT TO authenticated '
      'USING (org_id IN (SELECT private.current_user_org_ids()) '
      'AND private.pricing_role(org_id, ARRAY[''OWNER'']) '
      'AND auth.jwt()->>''aal'' = ''aal2'')', target);
  END LOOP;
END $$;

CREATE UNIQUE INDEX payment_customer_provider_identity
  ON public.payment_customers(provider, provider_customer_id);
CREATE UNIQUE INDEX subscription_provider_identity
  ON public.subscriptions(provider, provider_subscription_id)
  WHERE provider_subscription_id IS NOT NULL;
ALTER TABLE public.subscriptions ADD CONSTRAINT subscription_org_identity UNIQUE(org_id, id);
ALTER TABLE public.payments DROP CONSTRAINT payments_subscription_id_fkey;
ALTER TABLE public.payments ADD CONSTRAINT payment_subscription_same_org
  FOREIGN KEY(org_id, subscription_id) REFERENCES public.subscriptions(org_id, id) ON DELETE RESTRICT;
ALTER TABLE public.payments ADD CONSTRAINT payment_positive_integral_clp
  CHECK(amount > 0 AND (currency <> 'CLP' OR amount=trunc(amount)));
ALTER TABLE public.subscriptions ADD CONSTRAINT subscription_positive_integral_clp
  CHECK(amount > 0 AND (currency <> 'CLP' OR amount=trunc(amount)));

DO $storage$
BEGIN
  IF to_regclass('storage.buckets') IS NOT NULL THEN
    EXECUTE $sql$
      INSERT INTO storage.buckets(id, name, public)
      VALUES ('dekopen-backups', 'dekopen-backups', FALSE)
      ON CONFLICT(id) DO UPDATE SET public=FALSE
    $sql$;
    -- No authenticated backup-object policy. Only the server Storage credential can access it.
  END IF;
END;
$storage$;

COMMIT;
