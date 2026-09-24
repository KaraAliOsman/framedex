-- Sole-model pin: every AI capability routes to MiMo v2.6 Pro. The seed
-- inserts use ON CONFLICT DO NOTHING, so pinning an existing database is an
-- UPDATE; the same migration runs on a fresh reset right after the seeds.
-- provider_model is the wire model; AI_GATEWAY_MIMO_API_KEY/_BASE_URL (and
-- the optional _MODEL override) stay deployment config, never catalog data.
UPDATE public.ai_routes
SET provider = 'MIMO', provider_model = 'mimo-v2.6-pro';

-- agent capability: the orchestrating surface — goal in, bounded queries
-- back, and a validated step plan (navigate / ops / prepare) that still ends
-- in a human click for anything consequential.
INSERT INTO public.ai_routes
    (capability, public_name, provider, provider_model, prompt_version, credits_cost)
VALUES
    ('agent', 'DEKOPEN Agente™', 'MIMO', 'mimo-v2.6-pro', 'v1.0', 8)
ON CONFLICT (capability) DO UPDATE
    SET provider = EXCLUDED.provider,
        provider_model = EXCLUDED.provider_model;
