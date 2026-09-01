-- Dekopen SHOT-02 canonical PostgreSQL 16 schema.
-- Business rules are sourced from PRD-02 plus the owner resolutions recorded in
-- docs/plans/PLAN_SHOT-02.md.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- --------------------------------------------------------------------------
-- Tenancy and authentication
-- --------------------------------------------------------------------------

CREATE TYPE public.org_role AS ENUM (
    'OWNER',
    'ESTIMATOR',
    'WORKSHOP_MANAGER',
    'INSTALLER'
);
CREATE TYPE public.subscription_tier AS ENUM (
    'TRIAL',
    'STARTER',
    'PRO',
    'BUSINESS',
    'BUSINESS_2X'
);
CREATE TYPE public.currency_code AS ENUM ('CLP', 'USD');

CREATE TABLE public.tenancy_organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    tax_id VARCHAR(50) NOT NULL,
    country VARCHAR(2) NOT NULL DEFAULT 'CL',
    currency public.currency_code NOT NULL DEFAULT 'CLP',
    timezone VARCHAR(50) NOT NULL DEFAULT 'America/Santiago',
    subscription_tier public.subscription_tier NOT NULL DEFAULT 'TRIAL',
    subscription_active BOOLEAN NOT NULL DEFAULT TRUE,
    billing_cycle VARCHAR(10) NOT NULL DEFAULT 'annual'
        CHECK (billing_cycle IN ('monthly', 'annual')),
    founding_member BOOLEAN NOT NULL DEFAULT FALSE,
    trial_ends_at TIMESTAMPTZ,
    points_balance INT NOT NULL DEFAULT 500 CHECK (points_balance >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.tenancy_memberships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL
        REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    role public.org_role NOT NULL DEFAULT 'ESTIMATOR',
    totp_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_org_user UNIQUE (org_id, user_id)
);

-- --------------------------------------------------------------------------
-- Catalogs, profiles and hardware kits
-- --------------------------------------------------------------------------

CREATE TYPE public.material_type AS ENUM ('PVC', 'ALUMINIUM');
CREATE TYPE public.profile_role AS ENUM (
    'FRAME',
    'SASH',
    'MULLION_V',
    'MULLION_H',
    'INVERSOR',
    'GLAZING_BEAD',
    'COUPLER',
    'ADDITIONAL'
);

CREATE TABLE public.profile_systems (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    code VARCHAR(50) NOT NULL,
    depth_mm NUMERIC(10, 2) NOT NULL,
    material public.material_type NOT NULL DEFAULT 'PVC',
    chamber_count INT NOT NULL DEFAULT 3,
    sash_overlap_mm NUMERIC(4, 2) NOT NULL DEFAULT 8.00,
    glass_clearance_white_mm NUMERIC(4, 2) NOT NULL DEFAULT 3.00,
    glass_clearance_foil_mm NUMERIC(4, 2) NOT NULL DEFAULT 5.00,
    pulley_height_mm NUMERIC(4, 2) NOT NULL DEFAULT 12.00,
    central_overlap_mm NUMERIC(4, 2) NOT NULL DEFAULT 35.00,
    sliding_lateral_clearance_mm NUMERIC(4, 2) NOT NULL DEFAULT 0.00,
    sliding_end_add_mm NUMERIC(4, 2) NOT NULL DEFAULT 6.00,
    corner_bracket_loss_mm NUMERIC(4, 2) NOT NULL DEFAULT 0.00,
    hook_depth_mm NUMERIC(4, 2) NOT NULL DEFAULT 0.00,
    door_threshold_mm NUMERIC(4, 2) NOT NULL DEFAULT 30.00,
    door_bottom_clearance_mm NUMERIC(4, 2) NOT NULL DEFAULT 20.00,
    rail_type VARCHAR(10) NOT NULL DEFAULT 'dual'
        CHECK (rail_type IN ('dual', 'mono')),
    is_global BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    version INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_org_system_code UNIQUE (org_id, code, version)
);

CREATE UNIQUE INDEX uk_global_system_code
    ON public.profile_systems (code, version)
    WHERE org_id IS NULL;

CREATE TABLE public.profile_articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    system_id UUID NOT NULL REFERENCES public.profile_systems(id) ON DELETE CASCADE,
    org_id UUID REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    sku VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role public.profile_role NOT NULL,
    face_width_mm NUMERIC(10, 2) NOT NULL,
    commercial_length_mm NUMERIC(10, 2) NOT NULL DEFAULT 6000.00,
    welding_loss_mm NUMERIC(10, 2) NOT NULL DEFAULT 6.00,
    reinforcement_sku VARCHAR(100),
    reinforcement_gap_mm NUMERIC(10, 2) NOT NULL DEFAULT 15.00,
    weight_kg_m NUMERIC(8, 4) NOT NULL DEFAULT 1.2000,
    steel_weight_kg_m NUMERIC(8, 4) NOT NULL DEFAULT 1.7000,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_system_sku UNIQUE (system_id, sku)
);

CREATE TABLE public.glazing_bead_matrix (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    system_id UUID NOT NULL REFERENCES public.profile_systems(id) ON DELETE CASCADE,
    org_id UUID REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    glass_thickness_mm NUMERIC(6, 2) NOT NULL,
    bead_article_id UUID NOT NULL
        REFERENCES public.profile_articles(id) ON DELETE RESTRICT,
    bead_width_mm NUMERIC(6, 2) NOT NULL,
    gasket_interior_mm NUMERIC(6, 2) NOT NULL DEFAULT 3.00,
    gasket_exterior_mm NUMERIC(6, 2) NOT NULL DEFAULT 3.00,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uk_system_glass_thickness UNIQUE (system_id, glass_thickness_mm)
);

CREATE TABLE public.hardware_kits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    system_id UUID REFERENCES public.profile_systems(id) ON DELETE CASCADE,
    sku VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    opening_type VARCHAR(30) NOT NULL,
    min_leaf_width_mm NUMERIC(10, 2) NOT NULL,
    max_leaf_width_mm NUMERIC(10, 2) NOT NULL,
    min_leaf_height_mm NUMERIC(10, 2) NOT NULL,
    max_leaf_height_mm NUMERIC(10, 2) NOT NULL,
    max_leaf_weight_kg NUMERIC(6, 2) NOT NULL,
    rail_type VARCHAR(10) NOT NULL DEFAULT 'dual',
    carriages_qty INT NOT NULL DEFAULT 2,
    stay_arms_qty INT NOT NULL DEFAULT 1,
    contents JSONB NOT NULL DEFAULT '[]'::JSONB,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_kit_system_sku UNIQUE (system_id, sku)
);

-- --------------------------------------------------------------------------
-- Cost lists, pricing and price audit logs
-- --------------------------------------------------------------------------

CREATE TABLE public.cost_lists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL
        REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    supplier_name VARCHAR(200) NOT NULL,
    description TEXT,
    currency public.currency_code NOT NULL DEFAULT 'CLP',
    valid_from DATE NOT NULL,
    valid_to DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.cost_list_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cost_list_id UUID NOT NULL REFERENCES public.cost_lists(id) ON DELETE CASCADE,
    org_id UUID NOT NULL
        REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    sku VARCHAR(100) NOT NULL,
    item_type VARCHAR(50) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    unit_cost NUMERIC(14, 4) NOT NULL CHECK (unit_cost >= 0),
    CONSTRAINT uk_cost_list_sku UNIQUE (cost_list_id, sku)
);

CREATE TABLE public.pricing_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL
        REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    pricing_mode VARCHAR(50) NOT NULL DEFAULT 'COST_PLUS_MARGIN',
    default_margin_pct NUMERIC(6, 4) NOT NULL DEFAULT 0.3500,
    tax_rate_pct NUMERIC(6, 4) NOT NULL DEFAULT 0.1900,
    waste_factor_pct NUMERIC(6, 4) NOT NULL DEFAULT 0.0800,
    labor_rate_per_m2 NUMERIC(14, 2) NOT NULL DEFAULT 15000.00,
    installation_rate_per_m2 NUMERIC(14, 2) NOT NULL DEFAULT 12000.00,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_org_pricing_rules UNIQUE (org_id)
);

CREATE TABLE public.price_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL
        REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    project_id UUID,
    entity VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    field VARCHAR(50) NOT NULL,
    old_value NUMERIC(14, 2),
    new_value NUMERIC(14, 2),
    actor_type VARCHAR(20) NOT NULL,
    actor_user_id UUID,
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- --------------------------------------------------------------------------
-- Projects, positions and revisions
-- --------------------------------------------------------------------------

CREATE TYPE public.project_status AS ENUM (
    'DRAFT',
    'QUOTED',
    'APPROVED',
    'IN_PRODUCTION',
    'COMPLETED',
    'CANCELLED'
);
CREATE TYPE public.inspector_status AS ENUM ('GREEN', 'YELLOW', 'RED');

CREATE TABLE public.projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL
        REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    client_name VARCHAR(255) NOT NULL,
    client_rut VARCHAR(50),
    client_email VARCHAR(255),
    client_phone VARCHAR(50),
    delivery_address TEXT,
    status public.project_status NOT NULL DEFAULT 'DRAFT',
    total_cost_net NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    total_price_net NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    total_price_tax NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    total_price_gross NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    current_revision VARCHAR(10) NOT NULL DEFAULT 'REV-A',
    notes_commercial TEXT,
    notes_internal TEXT,
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_org_project_code UNIQUE (org_id, code)
);

CREATE TABLE public.project_positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    org_id UUID NOT NULL
        REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    position_index INT NOT NULL,
    location_tag VARCHAR(100),
    typology VARCHAR(50) NOT NULL,
    width_mm NUMERIC(10, 2) NOT NULL CHECK (width_mm >= 250.00),
    height_mm NUMERIC(10, 2) NOT NULL CHECK (height_mm >= 250.00),
    quantity INT NOT NULL DEFAULT 1 CHECK (quantity >= 1),
    system_id UUID NOT NULL REFERENCES public.profile_systems(id) ON DELETE RESTRICT,
    color_interior VARCHAR(50) NOT NULL DEFAULT 'WHITE',
    color_exterior VARCHAR(50) NOT NULL DEFAULT 'WHITE',
    glass_spec VARCHAR(200) NOT NULL DEFAULT '4-12-4 Float Incoloro',
    parametric_tree JSONB NOT NULL,
    bom_snapshot JSONB NOT NULL,
    cost_net NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    price_net NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    discount_pct NUMERIC(6, 4) NOT NULL DEFAULT 0.0000,
    inspector_status public.inspector_status NOT NULL DEFAULT 'GREEN',
    inspector_findings JSONB NOT NULL DEFAULT '[]'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_project_position_idx UNIQUE (project_id, position_index)
);

CREATE TABLE public.project_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    org_id UUID NOT NULL
        REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    revision_code VARCHAR(10) NOT NULL,
    snapshot_json JSONB NOT NULL,
    pdf_storage_path VARCHAR(500),
    emitted_by UUID NOT NULL,
    emitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_project_revision UNIQUE (project_id, revision_code)
);

-- --------------------------------------------------------------------------
-- Orders, offcuts and AI audit logs
-- --------------------------------------------------------------------------

CREATE TYPE public.order_type AS ENUM (
    'WORKSHOP_OT',
    'SUPPLIER_PROFILE_PO',
    'SUPPLIER_GLASS_PO',
    'SUPPLIER_HARDWARE_PO'
);
CREATE TYPE public.order_status AS ENUM (
    'DRAFT',
    'SENT',
    'PARTIALLY_RECEIVED',
    'FULFILLED',
    'CANCELLED'
);
CREATE TYPE public.offcut_status AS ENUM (
    'AVAILABLE',
    'RESERVED',
    'CONSUMED',
    'DISCARDED'
);

CREATE TABLE public.orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL
        REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT,
    order_type public.order_type NOT NULL,
    order_code VARCHAR(50) NOT NULL,
    status public.order_status NOT NULL DEFAULT 'DRAFT',
    supplier_name VARCHAR(200),
    payload_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_org_order_code UNIQUE (org_id, order_code)
);

CREATE TABLE public.offcut_inventory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL
        REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    profile_article_id UUID NOT NULL
        REFERENCES public.profile_articles(id) ON DELETE RESTRICT,
    color VARCHAR(50) NOT NULL,
    length_mm NUMERIC(10, 2) NOT NULL CHECK (length_mm >= 500.00),
    rack_location VARCHAR(50),
    source_order_id UUID REFERENCES public.orders(id) ON DELETE SET NULL,
    reserved_order_id UUID REFERENCES public.orders(id) ON DELETE SET NULL,
    status public.offcut_status NOT NULL DEFAULT 'AVAILABLE',
    qr_code VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    consumed_at TIMESTAMPTZ,
    CONSTRAINT uk_org_offcut_qr UNIQUE (org_id, qr_code)
);

CREATE TABLE public.ai_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL
        REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    model_used VARCHAR(100) NOT NULL,
    prompt_version VARCHAR(50) NOT NULL,
    retention_until TIMESTAMPTZ NOT NULL,
    input_payload JSONB NOT NULL,
    output_payload JSONB NOT NULL,
    points_debited INT NOT NULL DEFAULT 0,
    tokens_prompt INT NOT NULL DEFAULT 0,
    tokens_completion INT NOT NULL DEFAULT 0,
    latency_ms INT NOT NULL DEFAULT 0,
    state_hash_before VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- --------------------------------------------------------------------------
-- Billing, payments and credit ledger
-- --------------------------------------------------------------------------

CREATE TABLE public.payment_customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL
        REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    provider VARCHAR(30) NOT NULL
        CHECK (provider IN ('flow', 'paddle', 'mercadopago')),
    provider_customer_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_org_provider UNIQUE (org_id, provider)
);

CREATE TABLE public.subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL
        REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    provider VARCHAR(30) NOT NULL,
    provider_subscription_id VARCHAR(100),
    plan_tier public.subscription_tier NOT NULL CHECK (plan_tier <> 'TRIAL'),
    billing_cycle VARCHAR(10) NOT NULL
        CHECK (billing_cycle IN ('monthly', 'annual')),
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'past_due', 'cancelled', 'trialing')),
    currency public.currency_code NOT NULL DEFAULT 'USD',
    amount NUMERIC(12, 2) NOT NULL,
    current_period_end TIMESTAMPTZ,
    founding_member BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_org_subscription UNIQUE (org_id)
);

CREATE TABLE public.payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL
        REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    subscription_id UUID REFERENCES public.subscriptions(id) ON DELETE SET NULL,
    provider VARCHAR(30) NOT NULL,
    provider_payment_id VARCHAR(100) NOT NULL UNIQUE,
    amount NUMERIC(12, 2) NOT NULL,
    currency public.currency_code NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'succeeded', 'failed', 'refunded')),
    tax_doc_type VARCHAR(20),
    tax_doc_folio VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.payment_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES public.tenancy_organizations(id) ON DELETE SET NULL,
    provider VARCHAR(30) NOT NULL,
    event_id VARCHAR(150) NOT NULL,
    event_type VARCHAR(100),
    payload JSONB NOT NULL,
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_provider_event UNIQUE (provider, event_id)
);

CREATE INDEX idx_payment_events_org ON public.payment_events (org_id);

CREATE TABLE public.credit_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL
        REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    amount INT NOT NULL,
    balance_after INT NOT NULL CHECK (balance_after >= 0),
    action_type VARCHAR(50) NOT NULL,
    reference_id UUID,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ledger_org_created
    ON public.credit_ledger (org_id, created_at DESC);

-- --------------------------------------------------------------------------
-- RLS helpers and policies
-- --------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.current_user_org_ids()
RETURNS SETOF UUID
LANGUAGE SQL
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
    SELECT membership.org_id
    FROM public.tenancy_memberships AS membership
    WHERE membership.user_id = auth.uid()
      AND membership.is_active = TRUE;
$$;

CREATE OR REPLACE FUNCTION public.is_platform_superadmin()
RETURNS BOOLEAN
LANGUAGE SQL
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
    SELECT COALESCE(
        (auth.jwt() -> 'app_metadata' ->> 'is_superadmin') = 'true',
        FALSE
    );
$$;

REVOKE ALL ON FUNCTION public.current_user_org_ids() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.is_platform_superadmin() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.current_user_org_ids() TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.is_platform_superadmin() TO authenticated, service_role;

ALTER TABLE public.tenancy_organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tenancy_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profile_systems ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profile_articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.glazing_bead_matrix ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.hardware_kits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cost_lists ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cost_list_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pricing_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.price_audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.project_positions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.project_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.offcut_inventory ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.payment_customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.payment_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.credit_ledger ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenancy_organizations_select ON public.tenancy_organizations
    FOR SELECT
    USING (id IN (SELECT public.current_user_org_ids()));

CREATE POLICY tenancy_memberships_select ON public.tenancy_memberships
    FOR SELECT
    USING (org_id IN (SELECT public.current_user_org_ids()));

CREATE POLICY profile_systems_select ON public.profile_systems
    FOR SELECT
    USING (
        (auth.uid() IS NOT NULL AND is_global = TRUE)
        OR org_id IN (SELECT public.current_user_org_ids())
    );

CREATE POLICY profile_systems_modify ON public.profile_systems
    FOR ALL
    USING (org_id IN (SELECT public.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT public.current_user_org_ids()));

CREATE POLICY profile_articles_select ON public.profile_articles
    FOR SELECT
    USING (
        (
            auth.uid() IS NOT NULL
            AND system_id IN (
                SELECT system.id
                FROM public.profile_systems AS system
                WHERE system.is_global = TRUE
            )
        )
        OR org_id IN (SELECT public.current_user_org_ids())
    );

CREATE POLICY profile_articles_modify ON public.profile_articles
    FOR ALL
    USING (org_id IN (SELECT public.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT public.current_user_org_ids()));

CREATE POLICY glazing_bead_matrix_select ON public.glazing_bead_matrix
    FOR SELECT
    USING (
        (
            auth.uid() IS NOT NULL
            AND system_id IN (
                SELECT system.id
                FROM public.profile_systems AS system
                WHERE system.is_global = TRUE
            )
        )
        OR org_id IN (SELECT public.current_user_org_ids())
    );

CREATE POLICY glazing_bead_matrix_modify ON public.glazing_bead_matrix
    FOR ALL
    USING (org_id IN (SELECT public.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT public.current_user_org_ids()));

CREATE POLICY hardware_kits_select ON public.hardware_kits
    FOR SELECT
    USING (
        (
            auth.uid() IS NOT NULL
            AND system_id IN (
                SELECT system.id
                FROM public.profile_systems AS system
                WHERE system.is_global = TRUE
            )
        )
        OR org_id IN (SELECT public.current_user_org_ids())
    );

CREATE POLICY hardware_kits_modify ON public.hardware_kits
    FOR ALL
    USING (org_id IN (SELECT public.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT public.current_user_org_ids()));

CREATE POLICY cost_lists_isolation ON public.cost_lists
    FOR ALL
    USING (org_id IN (SELECT public.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT public.current_user_org_ids()));

CREATE POLICY cost_list_items_isolation ON public.cost_list_items
    FOR ALL
    USING (org_id IN (SELECT public.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT public.current_user_org_ids()));

CREATE POLICY pricing_rules_isolation ON public.pricing_rules
    FOR ALL
    USING (org_id IN (SELECT public.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT public.current_user_org_ids()));

CREATE POLICY price_audit_logs_isolation ON public.price_audit_logs
    FOR ALL
    USING (org_id IN (SELECT public.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT public.current_user_org_ids()));

CREATE POLICY projects_isolation ON public.projects
    FOR ALL
    USING (org_id IN (SELECT public.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT public.current_user_org_ids()));

CREATE POLICY positions_isolation ON public.project_positions
    FOR ALL
    USING (org_id IN (SELECT public.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT public.current_user_org_ids()));

CREATE POLICY project_versions_isolation ON public.project_versions
    FOR ALL
    USING (org_id IN (SELECT public.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT public.current_user_org_ids()));

CREATE POLICY orders_isolation ON public.orders
    FOR ALL
    USING (org_id IN (SELECT public.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT public.current_user_org_ids()));

CREATE POLICY offcut_inventory_isolation ON public.offcut_inventory
    FOR ALL
    USING (org_id IN (SELECT public.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT public.current_user_org_ids()));

CREATE POLICY ai_audit_logs_isolation ON public.ai_audit_logs
    FOR ALL
    USING (org_id IN (SELECT public.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT public.current_user_org_ids()));

CREATE POLICY payment_customers_isolation ON public.payment_customers
    FOR ALL
    USING (org_id IN (SELECT public.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT public.current_user_org_ids()));

CREATE POLICY subscriptions_isolation ON public.subscriptions
    FOR ALL
    USING (org_id IN (SELECT public.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT public.current_user_org_ids()));

CREATE POLICY payments_isolation ON public.payments
    FOR ALL
    USING (org_id IN (SELECT public.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT public.current_user_org_ids()));

CREATE POLICY credit_ledger_isolation ON public.credit_ledger
    FOR SELECT
    USING (org_id IN (SELECT public.current_user_org_ids()));

CREATE POLICY payment_events_service_role ON public.payment_events
    FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role')
    WITH CHECK (auth.jwt() ->> 'role' = 'service_role');

-- Supabase API roles need table privileges before RLS can evaluate their policies.
GRANT SELECT ON public.profile_systems TO anon;
GRANT SELECT ON public.profile_articles TO anon;
GRANT SELECT ON public.glazing_bead_matrix TO anon;
GRANT SELECT ON public.hardware_kits TO anon;

GRANT SELECT ON public.tenancy_organizations TO authenticated;
GRANT SELECT ON public.tenancy_memberships TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.profile_systems TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.profile_articles TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.glazing_bead_matrix TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.hardware_kits TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.cost_lists TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.cost_list_items TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.pricing_rules TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.price_audit_logs TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.projects TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.project_positions TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.project_versions TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.orders TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.offcut_inventory TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.ai_audit_logs TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.payment_customers TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.subscriptions TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.payments TO authenticated;
GRANT SELECT ON public.credit_ledger TO authenticated;

GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
