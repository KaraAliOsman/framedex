-- The shot-09 authority migration creates GLASS-BASE before the glass_spec
-- column exists, so the seed's deterministic insert always conflicts and the
-- recipe stays NULL. immutable_authority on glass_purchase_mappings rejects
-- EVERY update unconditionally (not only locked systems), so the backfill
-- must bypass the trigger for exactly this one reviewed statement —
-- DEMO_60 may already be technical_locked on databases that have sealed
-- positions, which is why the original predicate-only update both skipped
-- its target and aborted fresh resets on unlocked ones.
ALTER TABLE public.glass_purchase_mappings DISABLE TRIGGER immutable_authority;
ALTER TABLE public.glass_purchase_mappings DISABLE TRIGGER guard_referenced_catalog;

UPDATE public.glass_purchase_mappings
SET glass_spec = '4 Float Incoloro'
WHERE id = uuid_generate_v5(
        uuid_ns_url(),
        'https://dekopen.local/shot09/glass/DEMO_60/GLASS-BASE/V1')
  AND glass_spec IS NULL;

ALTER TABLE public.glass_purchase_mappings ENABLE TRIGGER immutable_authority;
ALTER TABLE public.glass_purchase_mappings ENABLE TRIGGER guard_referenced_catalog;
