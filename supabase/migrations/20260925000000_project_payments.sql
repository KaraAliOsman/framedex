-- Cobranza: payments recorded against a project's commercial deal.
-- A payment is a ledger row: recording is idempotent per
-- (org_id, operation_key) so a double-click or retried request never
-- double-counts, and a mistaken payment is voided (kept in the ledger,
-- excluded from totals) rather than deleted.
-- Append-only on top of 20260924000000_deliveries.sql.

CREATE TABLE public.project_payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
    operation_key TEXT NOT NULL,
    kind TEXT NOT NULL
        CHECK (kind IN ('ANTICIPO', 'PARCIAL', 'SALDO')),
    amount NUMERIC(14, 2) NOT NULL CHECK (amount > 0),
    method TEXT NOT NULL
        CHECK (method IN ('TRANSFER', 'CASH', 'CARD', 'CHECK', 'OTHER')),
    reference TEXT,
    note TEXT,
    recorded_by UUID,
    recorded_at TIMESTAMPTZ NOT NULL,
    voided_at TIMESTAMPTZ,
    voided_by UUID,
    void_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (org_id, operation_key)
);
CREATE INDEX project_payments_project_idx
    ON public.project_payments (org_id, project_id);

ALTER TABLE public.project_payments ENABLE ROW LEVEL SECURITY;

CREATE POLICY project_payments_isolation ON public.project_payments FOR ALL
USING (org_id IN (SELECT private.current_user_org_ids()))
WITH CHECK (org_id IN (SELECT private.current_user_org_ids()));

REVOKE ALL ON public.project_payments FROM anon;
GRANT SELECT ON public.project_payments TO authenticated;
GRANT SELECT, INSERT, UPDATE ON public.project_payments TO documentary_backend;
GRANT ALL ON public.project_payments TO service_role;
-- pg_default_acl hands arwdDxtm on new public tables to app roles; tenant
-- members only reach payments through the API/backend role.
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER ON public.project_payments FROM authenticated;
