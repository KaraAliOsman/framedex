-- The shot-09 authority migration creates GLASS-BASE before the glass_spec
-- column exists, so the seed's deterministic insert always conflicts and the
-- recipe stays NULL on every database. The backfill is a repair, not an
-- authority edit: no sealed calculation could ever have consumed a column
-- that did not exist when the evidence triggers were armed. Both guards are
-- bypassed for exactly this one reviewed statement, then re-armed.
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
