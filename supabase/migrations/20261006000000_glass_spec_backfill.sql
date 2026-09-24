-- The shot-09 authority migration creates GLASS-BASE before the glass_spec
-- column exists, so the seed's deterministic insert always conflicts and the
-- recipe stays NULL on every database. Backfill only while the owning catalog
-- remains unlocked: a referenced system's authorities are immutable, and
-- guard_referenced_catalog would (correctly) raise on the locked row.
UPDATE public.glass_purchase_mappings mapping
SET glass_spec = '4 Float Incoloro'
FROM public.profile_systems system
WHERE mapping.id = uuid_generate_v5(
        uuid_ns_url(),
        'https://dekopen.local/shot09/glass/DEMO_60/GLASS-BASE/V1')
  AND system.id = mapping.system_id
  AND system.technical_locked IS NOT TRUE
  AND mapping.glass_spec IS NULL;
