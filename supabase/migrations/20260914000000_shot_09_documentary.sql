ALTER TYPE public.order_type ADD VALUE IF NOT EXISTS 'SUPPLIER_PANEL_PO';

BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'documentary_backend') THEN
        CREATE ROLE documentary_backend NOLOGIN NOSUPERUSER NOBYPASSRLS;
    END IF;
END;
$$;
GRANT documentary_backend TO postgres;
CREATE SCHEMA IF NOT EXISTS extensions;
GRANT USAGE ON SCHEMA public, private, auth, extensions TO documentary_backend;
GRANT EXECUTE ON FUNCTION private.current_user_org_ids() TO documentary_backend;
GRANT EXECUTE ON FUNCTION auth.uid() TO documentary_backend;
GRANT SELECT ON public.tenancy_memberships, public.tenancy_organizations TO documentary_backend;

CREATE FUNCTION private.documentary_role(target_org UUID, allowed_roles TEXT[])
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.tenancy_memberships
        WHERE org_id = target_org
          AND user_id = auth.uid()
          AND is_active
          AND role::text = ANY(allowed_roles)
    );
$$;
REVOKE ALL ON FUNCTION private.documentary_role(UUID, TEXT[]) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.documentary_role(UUID, TEXT[])
    TO authenticated, documentary_backend;

CREATE OR REPLACE FUNCTION private.guard_commercial_write() RETURNS TRIGGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
DECLARE
    project_is_priced BOOLEAN;
BEGIN
    IF current_setting('role') = 'pricing_backend' THEN
        IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
        RETURN NEW;
    END IF;
    IF current_setting('role') = 'documentary_backend'
       AND TG_TABLE_NAME = 'project_positions' THEN
        IF TG_OP = 'UPDATE'
           AND (to_jsonb(NEW) - ARRAY['location_tag', 'updated_at'])
               = (to_jsonb(OLD) - ARRAY['location_tag', 'updated_at'])
           AND NOT EXISTS (
               SELECT 1 FROM public.project_versions WHERE project_id = OLD.project_id
           ) THEN
            RETURN NEW;
        END IF;
        RAISE EXCEPTION 'documentary_position_update_forbidden' USING ERRCODE = '42501';
    END IF;
    IF TG_OP = 'DELETE' THEN
        IF (session_user IN ('postgres', 'supabase_admin') OR
            (session_user = 'authenticator' AND current_setting('role') = 'service_role'))
           AND auth.uid() IS NULL AND pg_trigger_depth() > 1
           AND NOT EXISTS (
               SELECT 1 FROM public.tenancy_organizations WHERE id = OLD.org_id
           ) THEN
            RETURN OLD;
        END IF;
    END IF;
    IF TG_TABLE_NAME = 'project_positions' THEN
        IF TG_OP = 'INSERT' THEN
            project_is_priced := private.project_has_applied_commercial_state(NEW.project_id);
            IF NEW.cost_net <> 0 OR NEW.price_net <> 0 OR NEW.discount_pct <> 0
               OR project_is_priced THEN
                RAISE EXCEPTION 'pricing_service_required' USING ERRCODE = '42501';
            END IF;
        ELSIF TG_OP = 'UPDATE' THEN
            project_is_priced := private.project_has_applied_commercial_state(OLD.project_id)
                OR (NEW.project_id IS DISTINCT FROM OLD.project_id
                    AND private.project_has_applied_commercial_state(NEW.project_id));
            IF (NEW.cost_net, NEW.price_net, NEW.discount_pct)
                 IS DISTINCT FROM (OLD.cost_net, OLD.price_net, OLD.discount_pct)
               OR project_is_priced THEN
                RAISE EXCEPTION 'pricing_service_required' USING ERRCODE = '42501';
            END IF;
        ELSE
            project_is_priced := private.project_has_applied_commercial_state(OLD.project_id);
            IF OLD.cost_net <> 0 OR OLD.price_net <> 0 OR OLD.discount_pct <> 0
               OR project_is_priced THEN
                RAISE EXCEPTION 'pricing_service_required' USING ERRCODE = '42501';
            END IF;
            RETURN OLD;
        END IF;
    ELSE
        IF TG_OP = 'INSERT' THEN
            IF NEW.total_cost_net <> 0 OR NEW.total_price_net <> 0
               OR NEW.total_price_tax <> 0 OR NEW.total_price_gross <> 0 THEN
                RAISE EXCEPTION 'pricing_service_required' USING ERRCODE = '42501';
            END IF;
        ELSIF TG_OP = 'UPDATE' THEN
            project_is_priced := private.project_has_applied_commercial_state(OLD.id);
            IF (NEW.total_cost_net, NEW.total_price_net,
                NEW.total_price_tax, NEW.total_price_gross)
                 IS DISTINCT FROM (OLD.total_cost_net, OLD.total_price_net,
                                   OLD.total_price_tax, OLD.total_price_gross)
               OR project_is_priced THEN
                RAISE EXCEPTION 'pricing_service_required' USING ERRCODE = '42501';
            END IF;
        ELSE
            project_is_priced := private.project_has_applied_commercial_state(OLD.id);
            IF project_is_priced THEN
                RAISE EXCEPTION 'pricing_service_required' USING ERRCODE = '42501';
            END IF;
            RETURN OLD;
        END IF;
    END IF;
    RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION private.guard_commercial_write() FROM PUBLIC;

CREATE FUNCTION private.reject_immutable_evidence()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
    RAISE EXCEPTION 'documentary_evidence_immutable' USING ERRCODE = '42501';
END;
$$;
REVOKE ALL ON FUNCTION private.reject_immutable_evidence() FROM PUBLIC;

CREATE TABLE public.manufacturing_placement_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    system_id UUID NOT NULL REFERENCES public.profile_systems(id) ON DELETE RESTRICT,
    org_id UUID REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    version INTEGER NOT NULL CHECK (version >= 1),
    authority JSONB NOT NULL CHECK (jsonb_typeof(authority) = 'object'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE NULLS NOT DISTINCT (system_id, org_id, version),
    UNIQUE (id, system_id)
);

CREATE TABLE public.handle_requirement_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    system_id UUID NOT NULL REFERENCES public.profile_systems(id) ON DELETE RESTRICT,
    org_id UUID REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    version INTEGER NOT NULL CHECK (version >= 1),
    authority JSONB NOT NULL CHECK (jsonb_typeof(authority) = 'object'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE NULLS NOT DISTINCT (system_id, org_id, version),
    UNIQUE (id, system_id)
);

CREATE TABLE public.reinforcement_cut_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    system_id UUID NOT NULL REFERENCES public.profile_systems(id) ON DELETE RESTRICT,
    org_id UUID REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    version INTEGER NOT NULL CHECK (version >= 1),
    authority JSONB NOT NULL CHECK (jsonb_typeof(authority) = 'object'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE NULLS NOT DISTINCT (system_id, org_id, version),
    UNIQUE (id, system_id)
);

CREATE TABLE public.glass_purchase_mappings (
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

CREATE TABLE public.hardware_purchase_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hardware_kit_id UUID NOT NULL REFERENCES public.hardware_kits(id) ON DELETE RESTRICT,
    org_id UUID REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    purchasing_sku TEXT NOT NULL CHECK (length(btrim(purchasing_sku)) > 0),
    manufacturer_name TEXT NOT NULL CHECK (length(btrim(manufacturer_name)) > 0),
    purchase_unit TEXT NOT NULL CHECK (purchase_unit = 'KIT'),
    version INTEGER NOT NULL CHECK (version >= 1),
    provenance JSONB NOT NULL CHECK (jsonb_typeof(provenance) = 'object'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE NULLS NOT DISTINCT (hardware_kit_id, org_id, version),
    UNIQUE (id, hardware_kit_id)
);

CREATE TABLE public.panel_purchase_authorities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    infill_article_id UUID NOT NULL REFERENCES public.infill_articles(id) ON DELETE RESTRICT,
    org_id UUID REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    purchasing_sku TEXT NOT NULL CHECK (length(btrim(purchasing_sku)) > 0),
    manufacturer_name TEXT NOT NULL CHECK (length(btrim(manufacturer_name)) > 0),
    supply_form TEXT NOT NULL CHECK (supply_form = 'CUT_TO_SIZE'),
    purchase_unit TEXT NOT NULL CHECK (purchase_unit = 'EA'),
    version INTEGER NOT NULL CHECK (version >= 1),
    provenance JSONB NOT NULL CHECK (jsonb_typeof(provenance) = 'object'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE NULLS NOT DISTINCT (infill_article_id, org_id, version),
    UNIQUE (id, infill_article_id)
);

ALTER TABLE public.manufacturing_placement_policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.handle_requirement_policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reinforcement_cut_policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.glass_purchase_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.hardware_purchase_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.panel_purchase_authorities ENABLE ROW LEVEL SECURITY;

CREATE POLICY manufacturing_placement_policy_read
ON public.manufacturing_placement_policies FOR SELECT TO authenticated, documentary_backend
USING (auth.uid() IS NOT NULL AND (org_id IS NULL OR org_id IN (SELECT private.current_user_org_ids())));
CREATE POLICY handle_requirement_policy_read
ON public.handle_requirement_policies FOR SELECT TO authenticated, documentary_backend
USING (auth.uid() IS NOT NULL AND (org_id IS NULL OR org_id IN (SELECT private.current_user_org_ids())));
CREATE POLICY reinforcement_cut_policy_read
ON public.reinforcement_cut_policies FOR SELECT TO authenticated, documentary_backend
USING (auth.uid() IS NOT NULL AND (org_id IS NULL OR org_id IN (SELECT private.current_user_org_ids())));
CREATE POLICY glass_purchase_mapping_read
ON public.glass_purchase_mappings FOR SELECT TO authenticated, documentary_backend
USING (auth.uid() IS NOT NULL AND (org_id IS NULL OR org_id IN (SELECT private.current_user_org_ids())));
CREATE POLICY hardware_purchase_mapping_read
ON public.hardware_purchase_mappings FOR SELECT TO authenticated, documentary_backend
USING (auth.uid() IS NOT NULL AND (org_id IS NULL OR org_id IN (SELECT private.current_user_org_ids())));
CREATE POLICY panel_purchase_authority_read
ON public.panel_purchase_authorities FOR SELECT TO authenticated, documentary_backend
USING (auth.uid() IS NOT NULL AND (org_id IS NULL OR org_id IN (SELECT private.current_user_org_ids())));

DO $$
DECLARE
    table_name TEXT;
BEGIN
    FOREACH table_name IN ARRAY ARRAY[
        'manufacturing_placement_policies',
        'handle_requirement_policies',
        'reinforcement_cut_policies',
        'glass_purchase_mappings',
        'hardware_purchase_mappings',
        'panel_purchase_authorities'
    ] LOOP
        EXECUTE format(
            'CREATE TRIGGER immutable_authority BEFORE UPDATE OR DELETE ON public.%I '
            'FOR EACH ROW EXECUTE FUNCTION private.reject_immutable_evidence()',
            table_name
        );
        EXECUTE format('REVOKE ALL ON public.%I FROM anon, authenticated', table_name);
        EXECUTE format('GRANT SELECT ON public.%I TO authenticated, documentary_backend', table_name);
        EXECUTE format('GRANT ALL ON public.%I TO service_role', table_name);
    END LOOP;
END;
$$;

ALTER TABLE public.profile_purchase_mappings
    ADD COLUMN physical_stock_identity UUID,
    ADD COLUMN stock_color TEXT,
    ADD COLUMN cutting_profile_id UUID REFERENCES public.cutting_profiles(id) ON DELETE RESTRICT,
    ADD COLUMN binding_version INTEGER CHECK (binding_version >= 1),
    ADD CONSTRAINT profile_physical_binding_complete CHECK (
        (physical_stock_identity IS NULL AND stock_color IS NULL
            AND cutting_profile_id IS NULL AND binding_version IS NULL)
        OR
        (physical_stock_identity IS NOT NULL AND length(btrim(stock_color)) > 0
            AND cutting_profile_id IS NOT NULL AND binding_version IS NOT NULL)
    );

ALTER TABLE public.reinforcement_articles
    ADD COLUMN physical_stock_identity UUID,
    ADD COLUMN stock_color TEXT,
    ADD COLUMN cutting_profile_id UUID REFERENCES public.cutting_profiles(id) ON DELETE RESTRICT,
    ADD COLUMN binding_version INTEGER CHECK (binding_version >= 1),
    ADD CONSTRAINT reinforcement_physical_binding_complete CHECK (
        (physical_stock_identity IS NULL AND stock_color IS NULL
            AND cutting_profile_id IS NULL AND binding_version IS NULL)
        OR
        (physical_stock_identity IS NOT NULL AND length(btrim(stock_color)) > 0
            AND cutting_profile_id IS NOT NULL AND binding_version IS NOT NULL)
    );

ALTER TABLE public.project_positions
    ADD CONSTRAINT shot09_position_identity UNIQUE (id, project_id, org_id);

CREATE TABLE public.project_documentary_inputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    payment_terms TEXT NOT NULL CHECK (length(btrim(payment_terms)) > 0),
    quotation_valid_until DATE NOT NULL,
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (project_id, org_id)
        REFERENCES public.projects(id, org_id) ON DELETE CASCADE,
    UNIQUE (project_id, org_id)
);

CREATE TABLE public.position_documentary_inputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    position_id UUID NOT NULL,
    project_id UUID NOT NULL,
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    manufacturing_placement_policy_id UUID NOT NULL
        REFERENCES public.manufacturing_placement_policies(id) ON DELETE RESTRICT,
    handle_requirement_policy_id UUID NOT NULL
        REFERENCES public.handle_requirement_policies(id) ON DELETE RESTRICT,
    reinforcement_cut_policy_id UUID NOT NULL
        REFERENCES public.reinforcement_cut_policies(id) ON DELETE RESTRICT,
    workshop_annotations JSONB NOT NULL CHECK (jsonb_typeof(workshop_annotations) = 'array'),
    structural_inputs JSONB NOT NULL CHECK (jsonb_typeof(structural_inputs) = 'array'),
    glass_polishing JSONB NOT NULL CHECK (jsonb_typeof(glass_polishing) = 'array'),
    handle_intents JSONB NOT NULL CHECK (jsonb_typeof(handle_intents) = 'array'),
    accessory_schedule JSONB NOT NULL CHECK (jsonb_typeof(accessory_schedule) = 'object'),
    legacy_handle_migration_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (position_id, project_id, org_id)
        REFERENCES public.project_positions(id, project_id, org_id) ON DELETE CASCADE,
    UNIQUE (position_id, org_id)
);

CREATE FUNCTION private.validate_position_documentary_policy_scope()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    target_system UUID;
BEGIN
    SELECT system_id INTO target_system
    FROM public.project_positions
    WHERE id = NEW.position_id AND project_id = NEW.project_id AND org_id = NEW.org_id;
    IF target_system IS NULL THEN
        RAISE EXCEPTION 'documentary_position_not_found' USING ERRCODE = '23503';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM public.manufacturing_placement_policies
        WHERE id = NEW.manufacturing_placement_policy_id
          AND system_id = target_system AND (org_id IS NULL OR org_id = NEW.org_id)
    ) OR NOT EXISTS (
        SELECT 1 FROM public.handle_requirement_policies
        WHERE id = NEW.handle_requirement_policy_id
          AND system_id = target_system AND (org_id IS NULL OR org_id = NEW.org_id)
    ) OR NOT EXISTS (
        SELECT 1 FROM public.reinforcement_cut_policies
        WHERE id = NEW.reinforcement_cut_policy_id
          AND system_id = target_system AND (org_id IS NULL OR org_id = NEW.org_id)
    ) THEN
        RAISE EXCEPTION 'documentary_policy_scope_mismatch' USING ERRCODE = '23503';
    END IF;
    RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION private.validate_position_documentary_policy_scope() FROM PUBLIC;
CREATE TRIGGER validate_position_documentary_policy_scope
BEFORE INSERT OR UPDATE ON public.position_documentary_inputs
FOR EACH ROW EXECUTE FUNCTION private.validate_position_documentary_policy_scope();

CREATE FUNCTION private.guard_documentary_input_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
    IF (TG_OP <> 'INSERT' AND EXISTS (
            SELECT 1 FROM public.project_versions WHERE project_id = OLD.project_id
        )) OR (TG_OP <> 'DELETE' AND EXISTS (
            SELECT 1 FROM public.project_versions WHERE project_id = NEW.project_id
        )) THEN
        RAISE EXCEPTION 'sealed_documentary_inputs_immutable' USING ERRCODE = '42501';
    END IF;
    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END;
$$;
REVOKE ALL ON FUNCTION private.guard_documentary_input_mutation() FROM PUBLIC;
CREATE TRIGGER guard_project_documentary_inputs
BEFORE INSERT OR UPDATE OR DELETE ON public.project_documentary_inputs
FOR EACH ROW EXECUTE FUNCTION private.guard_documentary_input_mutation();
CREATE TRIGGER guard_position_documentary_inputs
BEFORE INSERT OR UPDATE OR DELETE ON public.position_documentary_inputs
FOR EACH ROW EXECUTE FUNCTION private.guard_documentary_input_mutation();

ALTER TABLE public.project_documentary_inputs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.position_documentary_inputs ENABLE ROW LEVEL SECURITY;
CREATE POLICY project_documentary_inputs_access
ON public.project_documentary_inputs FOR ALL TO authenticated
USING (private.documentary_role(org_id, ARRAY['OWNER', 'ESTIMATOR']))
WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'ESTIMATOR']));
CREATE POLICY position_documentary_inputs_access
ON public.position_documentary_inputs FOR ALL TO authenticated
USING (private.documentary_role(org_id, ARRAY['OWNER', 'ESTIMATOR']))
WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'ESTIMATOR']));
CREATE POLICY project_documentary_inputs_backend
ON public.project_documentary_inputs FOR ALL TO documentary_backend
USING (private.documentary_role(org_id, ARRAY['OWNER', 'ESTIMATOR']))
WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'ESTIMATOR']));
CREATE POLICY position_documentary_inputs_backend
ON public.position_documentary_inputs FOR ALL TO documentary_backend
USING (private.documentary_role(org_id, ARRAY['OWNER', 'ESTIMATOR']))
WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'ESTIMATOR']));
REVOKE ALL ON public.project_documentary_inputs, public.position_documentary_inputs FROM anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.project_documentary_inputs,
    public.position_documentary_inputs TO authenticated, documentary_backend;
GRANT ALL ON public.project_documentary_inputs, public.position_documentary_inputs TO service_role;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM public.project_versions) THEN
        RAISE EXCEPTION 'SHOT-09 requires an empty pre-authority project_versions table';
    END IF;
END;
$$;

ALTER TABLE public.pricing_operations
    ADD CONSTRAINT shot09_pricing_operation_identity UNIQUE (id, project_id, org_id);

ALTER TABLE public.project_versions
    DROP CONSTRAINT IF EXISTS project_versions_project_id_fkey,
    DROP CONSTRAINT IF EXISTS project_versions_org_id_fkey,
    ADD COLUMN pricing_operation_id UUID NOT NULL,
    ADD COLUMN canonical_version TEXT NOT NULL,
    ADD COLUMN bom_hash TEXT NOT NULL CHECK (bom_hash ~ '^[0-9a-f]{64}$'),
    ADD COLUMN snapshot_sha256 TEXT NOT NULL CHECK (snapshot_sha256 ~ '^[0-9a-f]{64}$'),
    ADD COLUMN production_allowed BOOLEAN NOT NULL,
    ADD COLUMN documentary_complete BOOLEAN NOT NULL,
    ADD CONSTRAINT project_versions_initial_revision CHECK (revision_code = 'REV-A'),
    ADD CONSTRAINT project_versions_project_tenant
        FOREIGN KEY (project_id, org_id) REFERENCES public.projects(id, org_id) ON DELETE RESTRICT,
    ADD CONSTRAINT project_versions_org_restrict
        FOREIGN KEY (org_id) REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    ADD CONSTRAINT project_versions_pricing_authority
        FOREIGN KEY (pricing_operation_id, project_id, org_id)
        REFERENCES public.pricing_operations(id, project_id, org_id) ON DELETE RESTRICT,
    ADD CONSTRAINT shot09_project_version_identity
        UNIQUE (id, project_id, org_id, bom_hash, snapshot_sha256),
    ADD CONSTRAINT shot09_project_version_operation UNIQUE (pricing_operation_id);

CREATE FUNCTION private.require_applied_pricing_authority()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM public.pricing_operations
        WHERE id = NEW.pricing_operation_id
          AND project_id = NEW.project_id
          AND org_id = NEW.org_id
          AND state = 'APPLIED'
    ) THEN
        RAISE EXCEPTION 'applied_pricing_authority_required' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION private.require_applied_pricing_authority() FROM PUBLIC;
CREATE TRIGGER require_applied_pricing_authority
BEFORE INSERT ON public.project_versions
FOR EACH ROW EXECUTE FUNCTION private.require_applied_pricing_authority();
CREATE TRIGGER project_versions_immutable
BEFORE UPDATE OR DELETE ON public.project_versions
FOR EACH ROW EXECUTE FUNCTION private.reject_immutable_evidence();

CREATE FUNCTION private.protect_sealed_pricing_operation()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM public.project_versions WHERE pricing_operation_id = OLD.id
    ) THEN
        RAISE EXCEPTION 'sealed_pricing_operation_immutable' USING ERRCODE = '42501';
    END IF;
    RETURN COALESCE(NEW, OLD);
END;
$$;
REVOKE ALL ON FUNCTION private.protect_sealed_pricing_operation() FROM PUBLIC;
CREATE TRIGGER protect_sealed_pricing_operation
BEFORE UPDATE OR DELETE ON public.pricing_operations
FOR EACH ROW EXECUTE FUNCTION private.protect_sealed_pricing_operation();

DROP POLICY IF EXISTS project_versions_isolation ON public.project_versions;
REVOKE ALL ON public.project_versions FROM anon, authenticated;
GRANT SELECT (
    id, project_id, org_id, revision_code, pricing_operation_id, canonical_version,
    bom_hash, snapshot_sha256, production_allowed, documentary_complete,
    emitted_by, emitted_at
) ON public.project_versions TO authenticated;
GRANT SELECT, INSERT ON public.project_versions TO documentary_backend;
GRANT ALL ON public.project_versions TO service_role;
CREATE POLICY project_versions_safe_read
ON public.project_versions FOR SELECT TO authenticated
USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY project_versions_backend
ON public.project_versions FOR ALL TO documentary_backend
USING (private.documentary_role(org_id, ARRAY['OWNER', 'ESTIMATOR', 'WORKSHOP_MANAGER']))
WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'ESTIMATOR']));

GRANT SELECT ON public.projects, public.project_positions, public.pricing_operations,
    public.profile_systems, public.profile_articles, public.glazing_bead_matrix,
    public.hardware_kits, public.infill_articles, public.profile_purchase_mappings,
    public.reinforcement_articles, public.cutting_profiles, public.inspector_rule_configs
TO documentary_backend;
GRANT UPDATE (location_tag, updated_at) ON public.project_positions TO documentary_backend;
CREATE POLICY pricing_operation_documentary_read
ON public.pricing_operations FOR SELECT TO documentary_backend
USING (private.documentary_role(org_id, ARRAY['OWNER', 'ESTIMATOR']));
CREATE POLICY infill_articles_documentary_read
ON public.infill_articles FOR SELECT TO documentary_backend
USING (org_id IS NULL OR org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY profile_purchase_mappings_documentary_read
ON public.profile_purchase_mappings FOR SELECT TO documentary_backend
USING (org_id IS NULL OR org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY reinforcement_articles_documentary_read
ON public.reinforcement_articles FOR SELECT TO documentary_backend
USING (org_id IS NULL OR org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY cutting_profiles_documentary_read
ON public.cutting_profiles FOR SELECT TO documentary_backend
USING (org_id IS NULL OR org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY inspector_rule_configs_documentary_read
ON public.inspector_rule_configs FOR SELECT TO documentary_backend
USING (org_id IS NULL OR org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY project_documentary_backend_read
ON public.projects FOR SELECT TO documentary_backend
USING (private.documentary_role(org_id, ARRAY['OWNER', 'ESTIMATOR', 'WORKSHOP_MANAGER']));
CREATE POLICY position_documentary_backend_read
ON public.project_positions FOR SELECT TO documentary_backend
USING (private.documentary_role(org_id, ARRAY['OWNER', 'ESTIMATOR', 'WORKSHOP_MANAGER']));
CREATE POLICY position_documentary_backend_location_update
ON public.project_positions FOR UPDATE TO documentary_backend
USING (private.documentary_role(org_id, ARRAY['OWNER', 'ESTIMATOR']))
WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'ESTIMATOR']));

CREATE TABLE public.purchase_projections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    project_version_id UUID NOT NULL,
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    bom_hash TEXT NOT NULL CHECK (bom_hash ~ '^[0-9a-f]{64}$'),
    snapshot_sha256 TEXT NOT NULL CHECK (snapshot_sha256 ~ '^[0-9a-f]{64}$'),
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    projection_hash TEXT NOT NULL CHECK (projection_hash ~ '^[0-9a-f]{64}$'),
    snapshot_json JSONB NOT NULL CHECK (jsonb_typeof(snapshot_json) = 'object'),
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (project_version_id, project_id, org_id, bom_hash, snapshot_sha256)
        REFERENCES public.project_versions(id, project_id, org_id, bom_hash, snapshot_sha256)
        ON DELETE RESTRICT,
    UNIQUE (project_version_id),
    UNIQUE (projection_hash),
    UNIQUE (id, project_id, project_version_id, org_id, bom_hash, snapshot_sha256)
);

CREATE TABLE public.purchase_requirement_lines (
    id UUID PRIMARY KEY,
    requirement_key TEXT NOT NULL CHECK (requirement_key ~ '^[0-9a-f]{64}$'),
    projection_id UUID NOT NULL,
    project_id UUID NOT NULL,
    project_version_id UUID NOT NULL,
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    bom_hash TEXT NOT NULL CHECK (bom_hash ~ '^[0-9a-f]{64}$'),
    snapshot_sha256 TEXT NOT NULL CHECK (snapshot_sha256 ~ '^[0-9a-f]{64}$'),
    order_type public.order_type NOT NULL CHECK (
        order_type IN (
            'SUPPLIER_PROFILE_PO', 'SUPPLIER_GLASS_PO',
            'SUPPLIER_HARDWARE_PO', 'SUPPLIER_PANEL_PO'
        )
    ),
    category TEXT NOT NULL CHECK (
        category IN ('PROFILE', 'REINFORCEMENT', 'GLASS', 'HARDWARE_KIT', 'PANEL', 'ACCESSORY')
    ),
    technical_identity JSONB NOT NULL CHECK (jsonb_typeof(technical_identity) = 'object'),
    purchasing_sku TEXT NOT NULL CHECK (length(btrim(purchasing_sku)) > 0),
    physical_stock_identity UUID,
    unit TEXT NOT NULL CHECK (unit IN ('BAR', 'EA', 'KIT')),
    quantity NUMERIC(20, 4) NOT NULL CHECK (quantity > 0 AND quantity = trunc(quantity)),
    specification JSONB NOT NULL CHECK (jsonb_typeof(specification) = 'object'),
    source_trace JSONB NOT NULL CHECK (jsonb_typeof(source_trace) = 'array'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (projection_id, project_id, project_version_id, org_id, bom_hash, snapshot_sha256)
        REFERENCES public.purchase_projections(
            id, project_id, project_version_id, org_id, bom_hash, snapshot_sha256
        ) ON DELETE RESTRICT,
    UNIQUE (projection_id, requirement_key),
    UNIQUE (id, project_id, project_version_id, org_id, order_type)
);

CREATE TABLE public.supplier_eligibility_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    project_version_id UUID NOT NULL,
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    bom_hash TEXT NOT NULL CHECK (bom_hash ~ '^[0-9a-f]{64}$'),
    snapshot_sha256 TEXT NOT NULL CHECK (snapshot_sha256 ~ '^[0-9a-f]{64}$'),
    order_type public.order_type NOT NULL CHECK (
        order_type IN (
            'SUPPLIER_PROFILE_PO', 'SUPPLIER_GLASS_PO',
            'SUPPLIER_HARDWARE_PO', 'SUPPLIER_PANEL_PO'
        )
    ),
    supplier_identity TEXT NOT NULL CHECK (length(btrim(supplier_identity)) > 0),
    supplier_name TEXT NOT NULL CHECK (length(btrim(supplier_name)) > 0),
    supplier_details JSONB NOT NULL CHECK (jsonb_typeof(supplier_details) = 'object'),
    eligible_requirement_keys JSONB NOT NULL CHECK (jsonb_typeof(eligible_requirement_keys) = 'array'),
    evidence JSONB NOT NULL CHECK (jsonb_typeof(evidence) = 'object'),
    version INTEGER NOT NULL CHECK (version >= 1),
    content_hash TEXT NOT NULL CHECK (content_hash ~ '^[0-9a-f]{64}$'),
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (project_version_id, project_id, org_id, bom_hash, snapshot_sha256)
        REFERENCES public.project_versions(id, project_id, org_id, bom_hash, snapshot_sha256)
        ON DELETE RESTRICT,
    UNIQUE (project_version_id, order_type, supplier_identity, version),
    UNIQUE (content_hash),
    UNIQUE (id, project_id, project_version_id, org_id, order_type)
);

CREATE TABLE public.purchase_allocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requirement_line_id UUID NOT NULL,
    supplier_eligibility_id UUID NOT NULL,
    project_id UUID NOT NULL,
    project_version_id UUID NOT NULL,
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    order_type public.order_type NOT NULL,
    allocated_by UUID NOT NULL,
    allocated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (requirement_line_id, project_id, project_version_id, org_id, order_type)
        REFERENCES public.purchase_requirement_lines(
            id, project_id, project_version_id, org_id, order_type
        ) ON DELETE RESTRICT,
    FOREIGN KEY (supplier_eligibility_id, project_id, project_version_id, org_id, order_type)
        REFERENCES public.supplier_eligibility_versions(
            id, project_id, project_version_id, org_id, order_type
        ) ON DELETE RESTRICT,
    UNIQUE (requirement_line_id),
    UNIQUE (id, project_id, project_version_id, org_id, order_type)
);

CREATE TABLE public.order_allocation_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    project_version_id UUID NOT NULL,
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    bom_hash TEXT NOT NULL CHECK (bom_hash ~ '^[0-9a-f]{64}$'),
    snapshot_sha256 TEXT NOT NULL CHECK (snapshot_sha256 ~ '^[0-9a-f]{64}$'),
    order_type public.order_type NOT NULL CHECK (
        order_type IN (
            'SUPPLIER_PROFILE_PO', 'SUPPLIER_GLASS_PO',
            'SUPPLIER_HARDWARE_PO', 'SUPPLIER_PANEL_PO'
        )
    ),
    allocation_hash TEXT NOT NULL CHECK (allocation_hash ~ '^[0-9a-f]{64}$'),
    confirmed_by UUID NOT NULL,
    confirmed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (project_version_id, project_id, org_id, bom_hash, snapshot_sha256)
        REFERENCES public.project_versions(id, project_id, org_id, bom_hash, snapshot_sha256)
        ON DELETE RESTRICT,
    UNIQUE (project_version_id, order_type),
    UNIQUE (allocation_hash),
    UNIQUE (id, project_id, project_version_id, org_id, order_type)
);

CREATE FUNCTION private.guard_confirmed_allocation()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = ''
AS $$
DECLARE
    target_version UUID;
    target_type public.order_type;
BEGIN
    target_version := CASE WHEN TG_OP = 'INSERT' THEN NEW.project_version_id
                           ELSE OLD.project_version_id END;
    target_type := CASE WHEN TG_OP = 'INSERT' THEN NEW.order_type ELSE OLD.order_type END;
    IF EXISTS (
        SELECT 1
        FROM public.order_allocation_batches
        WHERE project_version_id = target_version
          AND order_type = target_type
    ) THEN
        RAISE EXCEPTION 'confirmed_allocation_immutable' USING ERRCODE = '42501';
    END IF;
    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END;
$$;
REVOKE ALL ON FUNCTION private.guard_confirmed_allocation() FROM PUBLIC;
CREATE TRIGGER guard_confirmed_allocation
BEFORE INSERT OR UPDATE OR DELETE ON public.purchase_allocations
FOR EACH ROW EXECUTE FUNCTION private.guard_confirmed_allocation();

ALTER TABLE public.orders
    ADD COLUMN project_version_id UUID,
    ADD COLUMN allocation_batch_id UUID,
    ADD COLUMN supplier_eligibility_id UUID,
    ADD COLUMN bom_hash TEXT CHECK (bom_hash ~ '^[0-9a-f]{64}$'),
    ADD COLUMN revision_snapshot_sha256 TEXT CHECK (revision_snapshot_sha256 ~ '^[0-9a-f]{64}$'),
    ADD COLUMN purchase_projection_hash TEXT CHECK (purchase_projection_hash ~ '^[0-9a-f]{64}$'),
    ADD COLUMN allocation_identity TEXT CHECK (allocation_identity ~ '^[0-9a-f]{64}$'),
    ADD COLUMN order_snapshot_hash TEXT CHECK (order_snapshot_hash ~ '^[0-9a-f]{64}$'),
    ADD COLUMN supplier_identity TEXT,
    ADD COLUMN supplier_details JSONB,
    ADD COLUMN confirmed_by UUID,
    ADD COLUMN confirmed_at TIMESTAMPTZ,
    ADD COLUMN sent_by UUID,
    ADD COLUMN sent_at TIMESTAMPTZ,
    ADD CONSTRAINT shot09_supplier_order_complete CHECK (
        order_type = 'WORKSHOP_OT'
        OR (
            project_version_id IS NOT NULL AND allocation_batch_id IS NOT NULL
            AND supplier_eligibility_id IS NOT NULL AND bom_hash IS NOT NULL
            AND revision_snapshot_sha256 IS NOT NULL AND purchase_projection_hash IS NOT NULL
            AND allocation_identity IS NOT NULL AND order_snapshot_hash IS NOT NULL
            AND supplier_identity IS NOT NULL AND length(btrim(supplier_identity)) > 0
            AND supplier_name IS NOT NULL AND length(btrim(supplier_name)) > 0
            AND supplier_details IS NOT NULL AND jsonb_typeof(supplier_details) = 'object'
            AND confirmed_by IS NOT NULL AND confirmed_at IS NOT NULL
        )
    ),
    ADD CONSTRAINT shot09_supplier_order_state CHECK (
        order_type = 'WORKSHOP_OT' OR status IN ('DRAFT', 'SENT')
    ),
    ADD CONSTRAINT shot09_order_version_binding
        FOREIGN KEY (
            project_version_id, project_id, org_id, bom_hash, revision_snapshot_sha256
        ) REFERENCES public.project_versions(
            id, project_id, org_id, bom_hash, snapshot_sha256
        ) ON DELETE RESTRICT,
    ADD CONSTRAINT shot09_order_batch_binding
        FOREIGN KEY (allocation_batch_id, project_id, project_version_id, org_id, order_type)
        REFERENCES public.order_allocation_batches(
            id, project_id, project_version_id, org_id, order_type
        ) ON DELETE RESTRICT,
    ADD CONSTRAINT shot09_order_eligibility_binding
        FOREIGN KEY (supplier_eligibility_id, project_id, project_version_id, org_id, order_type)
        REFERENCES public.supplier_eligibility_versions(
            id, project_id, project_version_id, org_id, order_type
        ) ON DELETE RESTRICT,
    ADD CONSTRAINT shot09_order_supplier_identity
        UNIQUE (project_version_id, order_type, supplier_identity),
    ADD CONSTRAINT shot09_order_composite_identity
        UNIQUE (
            id, project_id, project_version_id, org_id, order_type,
            bom_hash, revision_snapshot_sha256
        );

CREATE FUNCTION private.guard_order_evidence()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
    IF OLD.order_type = 'WORKSHOP_OT' THEN
        RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
    END IF;
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'order_evidence_immutable' USING ERRCODE = '42501';
    END IF;
    IF OLD.status = 'DRAFT' AND NEW.status = 'SENT'
       AND NEW.sent_by IS NOT NULL AND NEW.sent_at IS NOT NULL
       AND (to_jsonb(NEW) - ARRAY['status', 'sent_by', 'sent_at', 'updated_at'])
           = (to_jsonb(OLD) - ARRAY['status', 'sent_by', 'sent_at', 'updated_at']) THEN
        RETURN NEW;
    END IF;
    RAISE EXCEPTION 'order_evidence_immutable' USING ERRCODE = '42501';
END;
$$;
REVOKE ALL ON FUNCTION private.guard_order_evidence() FROM PUBLIC;
CREATE TRIGGER guard_order_evidence
BEFORE UPDATE OR DELETE ON public.orders
FOR EACH ROW EXECUTE FUNCTION private.guard_order_evidence();

DROP POLICY IF EXISTS orders_isolation ON public.orders;
REVOKE ALL ON public.orders FROM anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.orders TO authenticated;
GRANT SELECT, INSERT, UPDATE ON public.orders TO documentary_backend;
GRANT ALL ON public.orders TO service_role;
CREATE POLICY workshop_orders_inherited_access
ON public.orders FOR ALL TO authenticated
USING (
    order_type = 'WORKSHOP_OT'
    AND org_id IN (SELECT private.current_user_org_ids())
)
WITH CHECK (
    order_type = 'WORKSHOP_OT'
    AND org_id IN (SELECT private.current_user_org_ids())
);
CREATE POLICY orders_backend
ON public.orders FOR ALL TO documentary_backend
USING (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']))
WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']));

CREATE TABLE public.order_requirement_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL,
    requirement_line_id UUID NOT NULL,
    project_id UUID NOT NULL,
    project_version_id UUID NOT NULL,
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    order_type public.order_type NOT NULL,
    bom_hash TEXT NOT NULL CHECK (bom_hash ~ '^[0-9a-f]{64}$'),
    revision_snapshot_sha256 TEXT NOT NULL CHECK (revision_snapshot_sha256 ~ '^[0-9a-f]{64}$'),
    quantity NUMERIC(20, 4) NOT NULL CHECK (quantity > 0 AND quantity = trunc(quantity)),
    line_snapshot JSONB NOT NULL CHECK (jsonb_typeof(line_snapshot) = 'object'),
    line_hash TEXT NOT NULL CHECK (line_hash ~ '^[0-9a-f]{64}$'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (
        order_id, project_id, project_version_id, org_id, order_type,
        bom_hash, revision_snapshot_sha256
    ) REFERENCES public.orders(
        id, project_id, project_version_id, org_id, order_type,
        bom_hash, revision_snapshot_sha256
    ) ON DELETE RESTRICT,
    FOREIGN KEY (requirement_line_id, project_id, project_version_id, org_id, order_type)
        REFERENCES public.purchase_requirement_lines(
            id, project_id, project_version_id, org_id, order_type
        ) ON DELETE RESTRICT,
    UNIQUE (requirement_line_id),
    UNIQUE (order_id, line_hash)
);

CREATE TABLE public.document_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    project_id UUID NOT NULL,
    project_version_id UUID NOT NULL,
    order_id UUID,
    order_type public.order_type,
    artifact_scope TEXT NOT NULL CHECK (artifact_scope IN ('PROJECT_REVISION', 'ORDER')),
    artifact_scope_id UUID NOT NULL,
    document_type TEXT NOT NULL CHECK (
        document_type IN ('DOC-01', 'DOC-02', 'DOC-03', 'DOC-04', 'DOC-05', 'DOC-06', 'DOC-07')
    ),
    format TEXT NOT NULL CHECK (format IN ('PDF', 'XLSX')),
    bom_hash TEXT NOT NULL CHECK (bom_hash ~ '^[0-9a-f]{64}$'),
    revision_snapshot_sha256 TEXT NOT NULL CHECK (revision_snapshot_sha256 ~ '^[0-9a-f]{64}$'),
    storage_bucket TEXT NOT NULL CHECK (storage_bucket = 'documents'),
    storage_object_key TEXT NOT NULL,
    file_sha256 TEXT NOT NULL CHECK (file_sha256 ~ '^[0-9a-f]{64}$'),
    media_type TEXT NOT NULL CHECK (
        media_type IN (
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    ),
    byte_size BIGINT NOT NULL CHECK (byte_size > 0),
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (
        project_version_id, project_id, org_id, bom_hash, revision_snapshot_sha256
    ) REFERENCES public.project_versions(
        id, project_id, org_id, bom_hash, snapshot_sha256
    ) ON DELETE RESTRICT,
    FOREIGN KEY (
        order_id, project_id, project_version_id, org_id, order_type,
        bom_hash, revision_snapshot_sha256
    ) REFERENCES public.orders(
        id, project_id, project_version_id, org_id, order_type,
        bom_hash, revision_snapshot_sha256
    ) ON DELETE RESTRICT,
    CHECK (storage_object_key LIKE 'org_' || org_id::text || '/%'),
    CHECK (
        (
            artifact_scope = 'PROJECT_REVISION'
            AND artifact_scope_id = project_version_id
            AND order_id IS NULL AND order_type IS NULL
            AND document_type IN ('DOC-01', 'DOC-03', 'DOC-05', 'DOC-06', 'DOC-07')
        )
        OR
        (
            artifact_scope = 'ORDER'
            AND artifact_scope_id = order_id
            AND order_id IS NOT NULL
            AND (
                (document_type = 'DOC-02' AND order_type = 'SUPPLIER_GLASS_PO')
                OR (document_type = 'DOC-04' AND order_type = 'SUPPLIER_PROFILE_PO')
            )
        )
    ),
    CHECK (
        (document_type IN ('DOC-01', 'DOC-03', 'DOC-05', 'DOC-06', 'DOC-07') AND format = 'PDF')
        OR (document_type = 'DOC-02' AND format = 'XLSX')
        OR (document_type = 'DOC-04' AND format IN ('PDF', 'XLSX'))
    ),
    UNIQUE (artifact_scope_id, document_type, format),
    UNIQUE (storage_bucket, storage_object_key)
);

ALTER TABLE public.purchase_projections ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.purchase_requirement_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.supplier_eligibility_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.purchase_allocations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.order_allocation_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.order_requirement_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_artifacts ENABLE ROW LEVEL SECURITY;

CREATE POLICY purchase_projections_backend
ON public.purchase_projections FOR ALL TO documentary_backend
USING (private.documentary_role(org_id, ARRAY['OWNER', 'ESTIMATOR', 'WORKSHOP_MANAGER']))
WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'ESTIMATOR']));
CREATE POLICY purchase_requirement_lines_backend
ON public.purchase_requirement_lines FOR ALL TO documentary_backend
USING (private.documentary_role(org_id, ARRAY['OWNER', 'ESTIMATOR', 'WORKSHOP_MANAGER']))
WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'ESTIMATOR']));
CREATE POLICY supplier_eligibility_backend
ON public.supplier_eligibility_versions FOR ALL TO documentary_backend
USING (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']))
WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']));
CREATE POLICY purchase_allocations_backend
ON public.purchase_allocations FOR ALL TO documentary_backend
USING (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']))
WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']));
CREATE POLICY allocation_batches_backend
ON public.order_allocation_batches FOR ALL TO documentary_backend
USING (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']))
WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']));
CREATE POLICY order_requirement_lines_backend
ON public.order_requirement_lines FOR ALL TO documentary_backend
USING (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']))
WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']));
CREATE POLICY document_artifacts_backend
ON public.document_artifacts FOR ALL TO documentary_backend
USING (private.documentary_role(org_id, ARRAY['OWNER', 'ESTIMATOR', 'WORKSHOP_MANAGER']))
WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'ESTIMATOR', 'WORKSHOP_MANAGER']));

DO $$
DECLARE
    table_name TEXT;
BEGIN
    FOREACH table_name IN ARRAY ARRAY[
        'purchase_projections',
        'purchase_requirement_lines',
        'supplier_eligibility_versions',
        'order_allocation_batches',
        'order_requirement_lines',
        'document_artifacts'
    ] LOOP
        EXECUTE format(
            'CREATE TRIGGER immutable_evidence BEFORE UPDATE OR DELETE ON public.%I '
            'FOR EACH ROW EXECUTE FUNCTION private.reject_immutable_evidence()',
            table_name
        );
    END LOOP;
END;
$$;

REVOKE ALL ON public.purchase_projections, public.purchase_requirement_lines,
    public.supplier_eligibility_versions, public.purchase_allocations,
    public.order_allocation_batches, public.order_requirement_lines,
    public.document_artifacts FROM anon, authenticated;
GRANT SELECT, INSERT ON public.purchase_projections, public.purchase_requirement_lines,
    public.supplier_eligibility_versions, public.order_allocation_batches,
    public.order_requirement_lines, public.document_artifacts TO documentary_backend;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.purchase_allocations TO documentary_backend;
GRANT ALL ON public.purchase_projections, public.purchase_requirement_lines,
    public.supplier_eligibility_versions, public.purchase_allocations,
    public.order_allocation_batches, public.order_requirement_lines,
    public.document_artifacts TO service_role;

DO $storage$
BEGIN
    IF to_regclass('storage.buckets') IS NOT NULL THEN
        EXECUTE $sql$
            INSERT INTO storage.buckets (id, name, public, file_size_limit)
            VALUES ('documents', 'documents', FALSE, 52428800)
            ON CONFLICT (id) DO UPDATE
            SET public = FALSE, file_size_limit = EXCLUDED.file_size_limit
        $sql$;
    END IF;
END;
$storage$;

COMMIT;
