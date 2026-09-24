-- Flow cobranza: per-org provider credentials + one-time payment links that
-- settle into the project_payments ledger through the verified webhook path.
--
-- org_payment_integrations holds the org's own Flow apiKey/secretKey — this is
-- the only table that carries a third-party secret, so authenticated and anon
-- get NO table privilege at all; only the backend role and service_role can
-- read it. The secret is write-only through the API: it never leaves in a
-- response.

CREATE TABLE public.org_payment_integrations (
    org_id uuid PRIMARY KEY REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    provider text NOT NULL DEFAULT 'FLOW' CHECK (provider = 'FLOW'),
    api_url text NOT NULL CHECK (api_url IN ('https://sandbox.flow.cl/api', 'https://www.flow.cl/api')),
    api_key text NOT NULL CHECK (length(api_key) >= 10),
    secret_key text NOT NULL CHECK (length(secret_key) >= 10),
    payer_return_url text,
    enabled boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.org_payment_integrations ENABLE ROW LEVEL SECURITY;

CREATE POLICY org_payment_integrations_isolation ON public.org_payment_integrations
    FOR ALL USING (org_id IN (SELECT private.current_user_org_ids()));

REVOKE ALL ON public.org_payment_integrations FROM anon;
REVOKE ALL ON public.org_payment_integrations FROM authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.org_payment_integrations TO documentary_backend;
GRANT ALL ON public.org_payment_integrations TO service_role;

-- A payment link is the durable claim for one Flow charge: the operation_key is
-- Flow's commerceOrder and the same key lands on the project_payment it
-- settles, so the ledger's UNIQUE (org_id, operation_key) dedupes every retry.
CREATE TABLE public.project_payment_links (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    project_id uuid NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
    operation_key text NOT NULL,
    kind text NOT NULL CHECK (kind IN ('ANTICIPO', 'PARCIAL', 'SALDO')),
    amount numeric(14,0) NOT NULL CHECK (amount > 0 AND amount = trunc(amount)),
    payer_email text NOT NULL,
    subject text NOT NULL,
    status text NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('DISPATCHING', 'PENDING', 'PAID', 'FAILED', 'UNCERTAIN', 'CANCELLED')),
    environment text NOT NULL CHECK (environment IN ('sandbox', 'production')),
    flow_order text,
    flow_token text,
    url text,
    project_payment_id uuid REFERENCES public.project_payments(id) ON DELETE RESTRICT,
    created_by uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (org_id, operation_key)
);

CREATE INDEX project_payment_links_project_idx ON public.project_payment_links(org_id, project_id);

ALTER TABLE public.project_payment_links ENABLE ROW LEVEL SECURITY;

CREATE POLICY project_payment_links_isolation ON public.project_payment_links
    FOR ALL USING (org_id IN (SELECT private.current_user_org_ids()));

REVOKE ALL ON public.project_payment_links FROM anon;
GRANT SELECT ON public.project_payment_links TO authenticated;
GRANT SELECT, INSERT, UPDATE ON public.project_payment_links TO documentary_backend;
GRANT ALL ON public.project_payment_links TO service_role;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER ON public.project_payment_links FROM authenticated;
