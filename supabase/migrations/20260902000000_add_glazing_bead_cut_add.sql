BEGIN;

ALTER TABLE public.glazing_bead_matrix
    ADD COLUMN cut_add_mm NUMERIC(6, 2);

UPDATE public.glazing_bead_matrix AS bead_rule
SET cut_add_mm = 9.00
FROM public.profile_systems AS profile_system
WHERE bead_rule.system_id = profile_system.id
  AND profile_system.code = 'DEMO_60'
  AND profile_system.is_global = TRUE;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM public.glazing_bead_matrix
        WHERE cut_add_mm IS NULL
    ) THEN
        RAISE EXCEPTION
            'glazing_bead_matrix.cut_add_mm requires an explicit catalog value';
    END IF;
END;
$$;

ALTER TABLE public.glazing_bead_matrix
    ALTER COLUMN cut_add_mm SET NOT NULL;

COMMIT;
