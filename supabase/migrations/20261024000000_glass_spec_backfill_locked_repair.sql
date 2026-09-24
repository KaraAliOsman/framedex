-- Forward repair for databases that already applied 20261006000000 in a
-- form that could not touch its target. Same rules as the in-place
-- statement: immutable_authority rejects every update unconditionally so
-- it is bypassed for exactly this one reviewed statement, and a locked
-- DEMO_60 keeps NULL — sealing means its catalog authority must not be
-- mutated afterwards; imports then require the reviewer's explicit
-- composition. Idempotent via glass_spec IS NULL.
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
