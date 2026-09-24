-- Forward repair for databases that already applied 20261006000000 in a
-- form that could not touch its target. Same rules as the in-place
-- statement: immutable_authority rejects every update unconditionally so
-- it is bypassed for exactly this one reviewed statement; the owning
-- profile_systems row is held FOR UPDATE so a concurrent seal either
-- commits first (we skip) or waits (the recipe legitimately lands
-- pre-seal); and a locked DEMO_60 keeps NULL — sealing means its catalog
-- authority must not be mutated afterwards, so imports require the
-- reviewer's explicit composition. Idempotent via glass_spec IS NULL.
ALTER TABLE public.glass_purchase_mappings DISABLE TRIGGER immutable_authority;
ALTER TABLE public.glass_purchase_mappings DISABLE TRIGGER guard_referenced_catalog;
DO $$
DECLARE
    system_locked BOOLEAN;
BEGIN
    SELECT system.technical_locked INTO system_locked
    FROM public.profile_systems system
    JOIN public.glass_purchase_mappings mapping
        ON mapping.system_id = system.id
    WHERE mapping.id = uuid_generate_v5(
            uuid_ns_url(),
            'https://dekopen.local/shot09/glass/DEMO_60/GLASS-BASE/V1')
    FOR UPDATE OF system;

    IF system_locked IS NOT TRUE THEN
        UPDATE public.glass_purchase_mappings
        SET glass_spec = '4 Float Incoloro'
        WHERE id = uuid_generate_v5(
                uuid_ns_url(),
                'https://dekopen.local/shot09/glass/DEMO_60/GLASS-BASE/V1')
          AND glass_spec IS NULL;
    END IF;
END $$;
ALTER TABLE public.glass_purchase_mappings ENABLE TRIGGER immutable_authority;
ALTER TABLE public.glass_purchase_mappings ENABLE TRIGGER guard_referenced_catalog;
