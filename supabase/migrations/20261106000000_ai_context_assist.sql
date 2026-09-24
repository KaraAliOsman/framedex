-- context_assist capability route: the contextual "Ask DEKOPEN" surface. The
-- server builds a typed per-surface projection (never a client-supplied
-- context) and the provider answers within it — MOCK by default so every
-- environment exercises the real contract without a live provider.
INSERT INTO public.ai_routes
    (capability, public_name, provider, provider_model, prompt_version, credits_cost)
VALUES
    ('context_assist', 'DEKOPEN Asistente Contextual™', 'MOCK', 'mock-context-1', 'v1.0', 2)
ON CONFLICT (capability) DO NOTHING;
