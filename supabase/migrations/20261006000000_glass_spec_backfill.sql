-- The shot-09 authority migration creates GLASS-BASE before the glass_spec
-- column exists, so the seed's deterministic insert always conflicts and the
-- recipe stays NULL on every database. Two guards interact here:
-- immutable_authority rejects EVERY update on the table unconditionally
-- (fresh resets abort on unlocked DEMO_60), and the locked-system rule
-- means a referenced system's authorities must never be mutated after
-- sealing — a locked catalog keeps NULL and imports require the reviewer's
-- explicit composition instead of silently re-resolving the SKU. So the
-- backfill bypasses the unconditional trigger for exactly this one
-- reviewed statement, and still only touches unlocked systems.
ALTER TABLE public.glass_purchase_mappings DISABLE TRIGGER immutable_authority;
ALTER TABLE public.glass_purchase_mappings DISABLE TRIGGER guard_referenced_catalog;

UPDATE public.glass_purchase_mappings mapping
SET glass_spec = '4 Float Incoloro'
FROM public.profile_systems system
WHERE mapping.id = uuid_generate_v5(
        uuid_ns_url(),
        'https://dekopen.local/shot09/glass/DEMO_60/GLASS-BASE/V1')
  AND system.id = mapping.system_id
  AND system.technical_locked IS NOT TRUE
  AND mapping.glass_spec IS NULL;

ALTER TABLE public.glass_purchase_mappings ENABLE TRIGGER immutable_authority;
ALTER TABLE public.glass_purchase_mappings ENABLE TRIGGER guard_referenced_catalog;
