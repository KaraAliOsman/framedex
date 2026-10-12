-- Connection evidence belongs to a capability's transport configuration.
-- Budget and token-tariff edits must not hide unchanged connection history.
ALTER TABLE public.ai_capability_routes ADD COLUMN connection_updated_at TIMESTAMPTZ;
UPDATE public.ai_capability_routes r
SET connection_updated_at = s.updated_at
FROM public.ai_settings s WHERE s.org_id = r.org_id;
ALTER TABLE public.ai_capability_routes ALTER COLUMN connection_updated_at SET DEFAULT now();
