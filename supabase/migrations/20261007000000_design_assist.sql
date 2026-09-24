-- design_assist capability route (PRD-13): natural-language design intent →
-- validated typed product operations. The mock route ships enabled so the
-- capability works deterministically on every environment; a real provider
-- is activated later by a privileged route update, never a code change.
INSERT INTO public.ai_routes
    (capability, public_name, provider, provider_model, prompt_version, credits_cost)
VALUES
    ('design_assist', 'DEKOPEN Diseñador™', 'MOCK', 'mock-design-1', 'v1.0', 10)
ON CONFLICT (capability) DO NOTHING;
