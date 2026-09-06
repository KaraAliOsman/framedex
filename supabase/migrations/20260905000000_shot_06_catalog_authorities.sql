BEGIN;

ALTER TYPE public.profile_role ADD VALUE 'THRESHOLD';

ALTER TABLE public.profile_systems
    ADD COLUMN sliding_glazing_deduction_width_mm NUMERIC(10, 2),
    ADD COLUMN sliding_glazing_deduction_height_mm NUMERIC(10, 2),
    ADD COLUMN door_leaf_side_clearance_mm NUMERIC(10, 2);

-- Only the synthetic DEMO_60 fixture has approved values. Fail closed for others.
UPDATE public.profile_systems
SET sliding_glazing_deduction_width_mm = 20.00,
    sliding_glazing_deduction_height_mm = 20.00,
    door_leaf_side_clearance_mm = 7.00
WHERE code = 'DEMO_60' AND is_global = TRUE;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM public.profile_systems
        WHERE sliding_glazing_deduction_width_mm IS NULL
           OR sliding_glazing_deduction_height_mm IS NULL
           OR door_leaf_side_clearance_mm IS NULL
    ) THEN
        RAISE EXCEPTION 'SHOT-06 geometry requires explicit catalog authorities';
    END IF;
END;
$$;

ALTER TABLE public.profile_systems
    ALTER COLUMN sliding_glazing_deduction_width_mm SET NOT NULL,
    ALTER COLUMN sliding_glazing_deduction_height_mm SET NOT NULL,
    ALTER COLUMN door_leaf_side_clearance_mm SET NOT NULL;

ALTER TABLE public.profile_articles
    ADD COLUMN material public.material_type NOT NULL DEFAULT 'PVC';
ALTER TABLE public.hardware_kits ADD COLUMN weight_kg NUMERIC(8, 2);

CREATE TABLE public.infill_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    system_id UUID NOT NULL REFERENCES public.profile_systems(id) ON DELETE CASCADE,
    org_id UUID REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    sku VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    kind VARCHAR(30) NOT NULL CHECK (kind = 'SANDWICH_PANEL'),
    thickness_mm NUMERIC(6, 2) NOT NULL,
    weight_kg_m2 NUMERIC(10, 4),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (system_id, sku)
);

ALTER TABLE public.infill_articles ENABLE ROW LEVEL SECURITY;
CREATE POLICY infill_articles_select ON public.infill_articles
    FOR SELECT TO authenticated
    USING (
        (
            auth.uid() IS NOT NULL
            AND org_id IS NULL
            AND system_id IN (
                SELECT system.id FROM public.profile_systems AS system
                WHERE system.is_global = TRUE
            )
        )
        OR org_id IN (SELECT private.current_user_org_ids())
    );
CREATE POLICY infill_articles_modify ON public.infill_articles
    FOR ALL TO authenticated
    USING (org_id IN (SELECT private.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT private.current_user_org_ids()));
REVOKE ALL ON public.infill_articles FROM anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.infill_articles TO authenticated;
GRANT ALL ON public.infill_articles TO service_role;

COMMENT ON COLUMN public.glazing_bead_matrix.glass_thickness_mm IS
    'Thickness of retained infill: glass or an explicitly supported panel.';

COMMIT;
