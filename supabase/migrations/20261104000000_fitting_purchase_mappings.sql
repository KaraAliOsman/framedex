-- §9: purchase authority for counted fittings (frameless clamps, patch
-- fittings, hinges, locks, connectors, point supports). Mirrors
-- glass_purchase_mappings: declared technical sku -> purchasing sku, global
-- (org_id NULL) or org-bound, versioned, immutable once written -- authority
-- rows are evidence, never editable history.

CREATE TABLE public.fitting_purchase_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    system_id UUID NOT NULL REFERENCES public.profile_systems(id) ON DELETE RESTRICT,
    org_id UUID REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    technical_sku TEXT NOT NULL CHECK (length(btrim(technical_sku)) > 0),
    purchasing_sku TEXT NOT NULL CHECK (length(btrim(purchasing_sku)) > 0),
    manufacturer_name TEXT NOT NULL CHECK (length(btrim(manufacturer_name)) > 0),
    purchase_unit TEXT NOT NULL CHECK (purchase_unit = 'EA'),
    version INTEGER NOT NULL CHECK (version >= 1),
    provenance JSONB NOT NULL CHECK (jsonb_typeof(provenance) = 'object'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE NULLS NOT DISTINCT (system_id, org_id, technical_sku, version),
    UNIQUE (id, system_id)
);

ALTER TABLE public.fitting_purchase_mappings ENABLE ROW LEVEL SECURITY;

CREATE POLICY fitting_purchase_mapping_read
ON public.fitting_purchase_mappings FOR SELECT TO authenticated, documentary_backend
USING (auth.uid() IS NOT NULL AND (org_id IS NULL OR org_id IN (SELECT private.current_user_org_ids())));

CREATE TRIGGER immutable_authority BEFORE UPDATE OR DELETE ON public.fitting_purchase_mappings
FOR EACH ROW EXECUTE FUNCTION private.reject_immutable_evidence();

REVOKE ALL ON public.fitting_purchase_mappings FROM anon, authenticated;
GRANT SELECT ON public.fitting_purchase_mappings TO authenticated, documentary_backend;
GRANT ALL ON public.fitting_purchase_mappings TO service_role;

-- FITTING joins the requirement categories a projection may emit.
ALTER TABLE public.purchase_requirement_lines
    DROP CONSTRAINT purchase_requirement_lines_category_check;
ALTER TABLE public.purchase_requirement_lines
    ADD CONSTRAINT purchase_requirement_lines_category_check
    CHECK (
        category IN (
            'PROFILE', 'REINFORCEMENT', 'GLASS', 'HARDWARE_KIT',
            'PANEL', 'ACCESSORY', 'FITTING'
        )
    );
