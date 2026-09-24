-- design_alternatives capability route: a brief becomes several candidate
-- products the estimator compares side by side. Intent-level contract only —
-- the provider proposes structure (openings per module, a bow angle), the
-- backend constructs the real product-v2 model from catalog materials and
-- evaluates every candidate through the engine before it reaches the
-- client. Same enabled-mock default as design_assist; real providers
-- activate via a privileged route update.
INSERT INTO public.ai_routes
    (capability, public_name, provider, provider_model, prompt_version, credits_cost)
VALUES
    ('design_alternatives', 'DEKOPEN Alternativas™', 'MOCK', 'mock-design-1', 'v1.0', 15)
ON CONFLICT (capability) DO NOTHING;
