-- SHOT-13: AI gateway routing table + audit-log hardening.
-- ai_routes is platform-level operational config (no org_id): tenants never see
-- raw provider/model names — the API only ever surfaces public_name.

CREATE TABLE public.ai_routes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    capability VARCHAR(100) NOT NULL UNIQUE,
    public_name VARCHAR(120) NOT NULL,
    provider VARCHAR(40) NOT NULL,
    provider_model VARCHAR(120) NOT NULL,
    prompt_version VARCHAR(50) NOT NULL,
    credits_cost INT NOT NULL CONSTRAINT ai_routes_cost_positive CHECK (credits_cost > 0),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.ai_routes ENABLE ROW LEVEL SECURITY;

-- Only the billing-scoped backend role reads routes: white-label names must
-- be absolute for tenants.
CREATE POLICY ai_routes_backend_read ON public.ai_routes
    FOR SELECT TO billing_backend
    USING (true);

GRANT SELECT ON public.ai_routes TO billing_backend;
REVOKE ALL ON public.ai_routes FROM anon, authenticated;

-- Capability registry (PRD-13): traffic distribution is operational config.
INSERT INTO public.ai_routes
    (capability, public_name, provider, provider_model, prompt_version, credits_cost)
VALUES
    ('nlp_command',      'DEKOPEN Neural Core™',   'MOCK', 'mock-neural-1', 'v1.0', 5),
    ('discount_suggest', 'DEKOPEN Neural Core™',   'MOCK', 'mock-neural-1', 'v1.0', 5),
    ('vision_ocr',       'DEKOPEN Vision CAD™',    'MOCK', 'mock-vision-1', 'v1.0', 25),
    ('catalog_compile',  'DEKOPEN Matrix Reader™', 'MOCK', 'mock-reader-1', 'v1.0', 40),
    ('fabricability',    'Doble Verificador Ciego','MOCK', 'mock-verifier-1','v1.0', 15);

-- Audit hardening: tenants read their own audit rows but can never write them.
-- billing_backend already carries billing_scope policies on ai_audit_logs; only
-- the table privilege was missing.
REVOKE INSERT, UPDATE, DELETE ON public.ai_audit_logs FROM authenticated;
GRANT INSERT ON public.ai_audit_logs TO billing_backend;
