BEGIN;

-- Balance changes still serialize on the organization. KEY SHARE from an
-- independent metadata FK must be allowed during the long agent transaction.
-- Replace the trigger's matching lock as well as the Python wallet lock.
CREATE OR REPLACE FUNCTION private.wallet_append() RETURNS TRIGGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE balance INTEGER;
BEGIN
  SELECT credits_balance INTO STRICT balance FROM public.tenancy_organizations
    WHERE id=NEW.org_id FOR NO KEY UPDATE;
  IF NEW.amount=0 OR NEW.balance_after <> balance+NEW.amount OR NEW.balance_after<0 THEN
    RAISE EXCEPTION 'wallet_invalid_balance' USING ERRCODE='23514';
  END IF;
  UPDATE public.tenancy_organizations SET credits_balance=NEW.balance_after WHERE id=NEW.org_id;
  RETURN NEW;
END $$;

-- Operational defaults contain no credential. A local test flag never
-- changes the real route; an OWNER must choose a test route explicitly.
UPDATE public.ai_routes SET provider='MIMO', provider_model='primalabs-ai/MiMo-V2.6-Pro', updated_at=now()
WHERE capability IN ('design_assist','design_alternatives','agent','context_assist','catalog_compile','vision_ocr','nlp_command','discount_suggest','fabricability');
INSERT INTO public.ai_routes(capability,public_name,provider,provider_model,prompt_version,credits_cost)
SELECT 'catalog_import', public_name,'MIMO','primalabs-ai/MiMo-V2.6-Pro',prompt_version,credits_cost
FROM public.ai_routes WHERE capability='catalog_compile'
ON CONFLICT(capability) DO NOTHING;

CREATE TABLE public.ai_settings (
    org_id UUID PRIMARY KEY REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    monthly_budget_credits INT CHECK(monthly_budget_credits >= 0),
    budget_notice_at TIMESTAMPTZ,
    revision INT NOT NULL DEFAULT 1 CHECK(revision > 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by UUID
);
CREATE TABLE public.ai_capability_routes (
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    capability VARCHAR(100) NOT NULL CHECK(capability IN ('design_assist','agent','context_assist','catalog_import')),
    provider VARCHAR(40) NOT NULL CHECK(provider ~ '^[A-Z][A-Z0-9_]{0,39}$'),
    provider_model VARCHAR(120) NOT NULL CHECK(length(trim(provider_model)) > 0),
    timeout_s INT NOT NULL DEFAULT 60 CHECK(timeout_s BETWEEN 1 AND 180),
    retries INT NOT NULL DEFAULT 2 CHECK(retries BETWEEN 0 AND 2),
    tools_mode VARCHAR(8) NOT NULL DEFAULT 'AUTO' CHECK(tools_mode IN ('AUTO','NATIVE','JSON')),
    input_usd_per_million NUMERIC(18,8) CHECK(input_usd_per_million BETWEEN 0 AND 1000000),
    output_usd_per_million NUMERIC(18,8) CHECK(output_usd_per_million BETWEEN 0 AND 1000000),
    revision INT NOT NULL DEFAULT 1 CHECK(revision > 0),
    connection_state VARCHAR(24) NOT NULL DEFAULT 'UNTESTED' CHECK(connection_state IN ('UNTESTED','CONNECTED','ERROR')),
    connection_code VARCHAR(120),
    checked_at TIMESTAMPTZ,
    PRIMARY KEY(org_id,capability),
    CHECK((input_usd_per_million IS NULL) = (output_usd_per_million IS NULL))
);
-- Separate from the financial audit: physical provider usage survives a
-- rejected proposal and the domain rollback. Only allowlisted metadata lives
-- here; no prompts, outputs, goal, URLs, headers or credentials.
CREATE TABLE public.ai_provider_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    job_id UUID,
    ai_job_id UUID,
    operation_key VARCHAR(120) NOT NULL,
    input_hash VARCHAR(64) NOT NULL CHECK(input_hash ~ '^[a-f0-9]{64}$'),
    capability VARCHAR(100) NOT NULL,
    provider VARCHAR(40) NOT NULL,
    provider_model VARCHAR(120) NOT NULL,
    test_mode BOOLEAN NOT NULL DEFAULT false,
    status VARCHAR(16) NOT NULL DEFAULT 'RUNNING' CHECK(status IN ('RUNNING','SUCCEEDED','FAILED')),
    credits_reserved INT NOT NULL CHECK(credits_reserved > 0),
    tokens_prompt INT CHECK(tokens_prompt >= 0),
    tokens_completion INT CHECK(tokens_completion >= 0),
    estimated_cost_usd NUMERIC(30,14) CHECK(estimated_cost_usd >= 0),
    input_usd_per_million NUMERIC(18,8),
    output_usd_per_million NUMERIC(18,8),
    latency_ms INT CHECK(latency_ms >= 0),
    retries INT NOT NULL DEFAULT 0 CHECK(retries BETWEEN 0 AND 2),
    fallback BOOLEAN NOT NULL DEFAULT false,
    tool_names JSONB NOT NULL DEFAULT '[]' CHECK(jsonb_typeof(tool_names)='array'),
    error_code VARCHAR(120),
    attempt INT NOT NULL DEFAULT 1 CHECK(attempt > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    UNIQUE(org_id,operation_key,attempt),
    UNIQUE(org_id,id)
);
CREATE INDEX ai_provider_usage_month ON public.ai_provider_usage(org_id,created_at DESC);
CREATE INDEX ai_provider_usage_job ON public.ai_provider_usage(org_id,job_id);

ALTER TABLE public.ai_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_capability_routes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_provider_usage ENABLE ROW LEVEL SECURITY;
CREATE POLICY ai_settings_backend ON public.ai_settings TO billing_backend
    USING(private.billing_scope(org_id)) WITH CHECK(private.billing_scope(org_id));
CREATE POLICY ai_capability_routes_backend ON public.ai_capability_routes TO billing_backend
    USING(private.billing_scope(org_id)) WITH CHECK(private.billing_scope(org_id));
CREATE POLICY ai_provider_usage_backend ON public.ai_provider_usage TO billing_backend
    USING(private.billing_scope(org_id)) WITH CHECK(private.billing_scope(org_id));
GRANT SELECT, INSERT, UPDATE ON public.ai_settings, public.ai_capability_routes, public.ai_provider_usage TO billing_backend;
REVOKE ALL ON public.ai_settings, public.ai_capability_routes, public.ai_provider_usage FROM anon,authenticated;

CREATE FUNCTION private.ai_usage_terminal_immutable() RETURNS trigger
LANGUAGE plpgsql SET search_path='' AS $$
BEGIN
    IF OLD.status IN ('SUCCEEDED','FAILED') OR TG_OP='DELETE' THEN
        RAISE EXCEPTION 'ai_provider_usage_immutable';
    END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER ai_usage_terminal_immutable BEFORE UPDATE OR DELETE ON public.ai_provider_usage
FOR EACH ROW EXECUTE FUNCTION private.ai_usage_terminal_immutable();

ALTER TABLE public.job_runs ADD COLUMN phase VARCHAR(40);
CREATE TABLE public.ai_usage_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id),
    usage_id UUID NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    status VARCHAR(12) NOT NULL CHECK(status IN ('OK','ERROR','CACHED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY(org_id,usage_id) REFERENCES public.ai_provider_usage(org_id,id)
);
ALTER TABLE public.ai_usage_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY ai_usage_events_backend ON public.ai_usage_events TO billing_backend
USING(private.billing_scope(org_id)) WITH CHECK(private.billing_scope(org_id));
GRANT SELECT,INSERT ON public.ai_usage_events TO billing_backend;
REVOKE ALL ON public.ai_usage_events FROM anon,authenticated;
CREATE INDEX ai_usage_events_usage ON public.ai_usage_events(org_id,usage_id);
CREATE FUNCTION private.ai_usage_event_immutable() RETURNS trigger
LANGUAGE plpgsql SET search_path='' AS $$
BEGIN RAISE EXCEPTION 'ai_usage_event_immutable'; END; $$;
CREATE TRIGGER ai_usage_event_immutable BEFORE UPDATE OR DELETE ON public.ai_usage_events
FOR EACH ROW EXECUTE FUNCTION private.ai_usage_event_immutable();
COMMIT;
