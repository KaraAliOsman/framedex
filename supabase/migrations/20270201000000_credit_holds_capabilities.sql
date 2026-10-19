-- v1 final (06): durable holds of spendable credits for admitted AI exchanges,
-- and the versioned consumption policy sealed on each audit.
--
-- spendable = usable balance of lots − ACTIVE holds. A hold is not a debit and
-- not a second wallet: settlement debits through the existing ledger/lots and
-- releases the hold exactly once. The legacy policy keeps the fixed debit of
-- route.credits_cost (legacy_route_v1); no token formula is activated here.
BEGIN;

CREATE TABLE public.credit_holds (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
  user_id UUID NOT NULL,
  operation_key TEXT NOT NULL,
  ai_job_id UUID,
  capability TEXT NOT NULL,
  consumption_policy TEXT NOT NULL DEFAULT 'legacy_route_v1',
  credits INTEGER NOT NULL CHECK(credits > 0),
  status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE','SETTLED','RELEASED','UNCERTAIN')),
  -- Lots that backed the admission, in consumption order: [{lot_id, credits, expires_at}].
  allocation JSONB NOT NULL DEFAULT '[]'::jsonb CHECK(jsonb_typeof(allocation)='array'),
  ledger_id UUID,
  reason TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ,
  UNIQUE(org_id, operation_key)
);
CREATE INDEX credit_holds_active ON public.credit_holds(org_id) WHERE status = 'ACTIVE';
ALTER TABLE public.credit_holds ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.credit_holds FROM PUBLIC, anon, authenticated;
GRANT ALL ON public.credit_holds TO service_role;
CREATE POLICY billing_backend_scope ON public.credit_holds FOR ALL TO billing_backend
  USING(private.billing_scope(org_id)) WITH CHECK(private.billing_scope(org_id));
CREATE POLICY billing_backend_restrict ON public.credit_holds AS RESTRICTIVE FOR ALL TO billing_backend
  USING(private.billing_scope(org_id)) WITH CHECK(private.billing_scope(org_id));
GRANT SELECT, INSERT ON public.credit_holds TO billing_backend;
-- Re-admission of a released key rewrites its amount, actor, job and allocation.
GRANT UPDATE(status, ledger_id, reason, resolved_at, credits, allocation, user_id, ai_job_id, created_at)
  ON public.credit_holds TO billing_backend;

-- The audit seals which consumption policy priced it (history keeps NULL =
-- legacy fixed route debit, the only policy that ever existed before).
ALTER TABLE public.ai_audit_logs ADD COLUMN IF NOT EXISTS consumption_policy TEXT;

COMMIT;
