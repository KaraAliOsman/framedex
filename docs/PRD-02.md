# PRD-02: MODELO DE DATOS, DDL Y POLÍTICAS DE AISLAMIENTO RLS (v1.1.2)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.1.2 (Congelada y Bloqueada tras Auditoría Final)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Fase:** 0 (Fundacional)  
**Bloquea a:** Todos los módulos del backend y frontend

---

## 1. Principios Rectores de la Base de Datos

1. **Aislamiento Multi-Tenant Absoluto:** Toda tabla de negocio posee la columna `org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE`.
2. **Row Level Security (RLS) Exhaustivo:** Ninguna consulta desde la capa de aplicación o Supabase Client puede ejecutarse sin la evaluación estricta de políticas RLS. Los catálogos globales (`is_global = TRUE`) son legibles por cualquier usuario autenticado de cualquier organización.
3. **Roles de Organización vs. Plataforma (H3 — Seguridad Reforzada):** `SUPERADMIN` es un rol de plataforma a nivel de sistema (`auth.jwt() -> 'app_metadata' ->> 'is_superadmin' = 'true'` — editable únicamente vía service_role / Admin API de Supabase, jamás desde `user_metadata` — o tabla `platform_admins` con consultas exclusivas del backend). **NO forma parte del enum `org_role`**, el cual modela exclusivamente los 4 roles internos del taller (`OWNER`, `ESTIMATOR`, `WORKSHOP_MANAGER`, `INSTALLER`).
4. **Tipado Numérico Exacto:** Prohibido el uso de `FLOAT` o `REAL`.
   - Dimensiones milimétricas: `NUMERIC(10, 2)` (rango hasta 99,999.99 mm).
   - Precios y montos monetarios: `NUMERIC(14, 2)` para moneda internacional/costos, `NUMERIC(14, 0)` para CLP en cotizaciones finales.
   - Factores, mermas y márgenes porcentuales: `NUMERIC(6, 4)`.
5. **Idempotencia Financiera y Auditoría (P1-1, C.1, C.2):** Tablas de pagos con restricciones de unicidad estricta (`payment_events(provider, event_id)` y `payments(provider_payment_id)`), auditoría previa de precios (`price_audit_logs`) y trazabilidad de IA (`ai_audit_logs`).

---

## 2. DDL Canónico Completo (PostgreSQL 16)

```sql
-- Extensiones requeridas
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- 1. TENANCY & AUTHENTICATION
-- ============================================================================

CREATE TYPE org_role AS ENUM ('OWNER', 'ESTIMATOR', 'WORKSHOP_MANAGER', 'INSTALLER');
CREATE TYPE subscription_tier AS ENUM ('TRIAL', 'STARTER', 'PRO', 'BUSINESS', 'BUSINESS_2X');
CREATE TYPE currency_code AS ENUM ('CLP', 'USD');

CREATE TABLE tenancy_organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    tax_id VARCHAR(50) NOT NULL, -- RUT en Chile (e.g. 76.123.456-7)
    country VARCHAR(2) NOT NULL DEFAULT 'CL',
    currency currency_code NOT NULL DEFAULT 'CLP',
    timezone VARCHAR(50) NOT NULL DEFAULT 'America/Santiago',
    subscription_tier subscription_tier NOT NULL DEFAULT 'TRIAL',
    subscription_active BOOLEAN NOT NULL DEFAULT TRUE,
    billing_cycle VARCHAR(10) NOT NULL DEFAULT 'annual' CHECK (billing_cycle IN ('monthly', 'annual')),
    founding_member BOOLEAN NOT NULL DEFAULT FALSE,
    trial_ends_at TIMESTAMPTZ,
    points_balance INT NOT NULL DEFAULT 500 CHECK (points_balance >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE tenancy_memberships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL, -- Enlaza con auth.users de Supabase
    role org_role NOT NULL DEFAULT 'ESTIMATOR',
    totp_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_org_user UNIQUE (org_id, user_id)
);

-- ============================================================================
-- 2. CATALOGS, PROFILES & HARDWARE KITS (Enmienda F1)
-- ============================================================================

CREATE TYPE material_type AS ENUM ('PVC', 'ALUMINIUM');
CREATE TYPE profile_role AS ENUM ('FRAME', 'SASH', 'MULLION_V', 'MULLION_H', 'INVERSOR', 'GLAZING_BEAD', 'COUPLER', 'ADDITIONAL');

CREATE TABLE profile_systems (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID REFERENCES tenancy_organizations(id) ON DELETE CASCADE, -- NULL si es catálogo global público
    name VARCHAR(150) NOT NULL,
    code VARCHAR(50) NOT NULL,
    depth_mm NUMERIC(10, 2) NOT NULL,
    material material_type NOT NULL DEFAULT 'PVC',
    chamber_count INT NOT NULL DEFAULT 3,
    
    -- Parámetros canónicos de sistema
    sash_overlap_mm NUMERIC(4, 2) NOT NULL DEFAULT 8.00,
    glass_clearance_white_mm NUMERIC(4, 2) NOT NULL DEFAULT 3.00, -- Demo 60 congela 5.00
    glass_clearance_foil_mm NUMERIC(4, 2) NOT NULL DEFAULT 5.00,
    pulley_height_mm NUMERIC(4, 2) NOT NULL DEFAULT 12.00,
    central_overlap_mm NUMERIC(4, 2) NOT NULL DEFAULT 35.00,
    sliding_lateral_clearance_mm NUMERIC(4, 2) NOT NULL DEFAULT 0.00,
    sliding_end_add_mm NUMERIC(4, 2) NOT NULL DEFAULT 6.00,
    corner_bracket_loss_mm NUMERIC(4, 2) NOT NULL DEFAULT 0.00,
    hook_depth_mm NUMERIC(4, 2) NOT NULL DEFAULT 0.00,
    door_threshold_mm NUMERIC(4, 2) NOT NULL DEFAULT 30.00,
    door_bottom_clearance_mm NUMERIC(4, 2) NOT NULL DEFAULT 20.00,
    rail_type VARCHAR(10) NOT NULL DEFAULT 'dual' CHECK (rail_type IN ('dual', 'mono')),
    
    is_global BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    version INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_org_system_code UNIQUE (org_id, code, version)
);

CREATE TABLE profile_articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    system_id UUID NOT NULL REFERENCES profile_systems(id) ON DELETE CASCADE,
    org_id UUID REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    sku VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role profile_role NOT NULL,
    face_width_mm NUMERIC(10, 2) NOT NULL,
    commercial_length_mm NUMERIC(10, 2) NOT NULL DEFAULT 6000.00,
    welding_loss_mm NUMERIC(10, 2) NOT NULL DEFAULT 6.00,
    reinforcement_sku VARCHAR(100),
    reinforcement_gap_mm NUMERIC(10, 2) NOT NULL DEFAULT 15.00,
    weight_kg_m NUMERIC(8, 4) NOT NULL DEFAULT 1.2000,
    steel_weight_kg_m NUMERIC(8, 4) NOT NULL DEFAULT 1.7000, -- Peso acero de refuerzo
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_system_sku UNIQUE (system_id, sku)
);

CREATE TABLE glazing_bead_matrix (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    system_id UUID NOT NULL REFERENCES profile_systems(id) ON DELETE CASCADE,
    org_id UUID REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    glass_thickness_mm NUMERIC(6, 2) NOT NULL,
    bead_article_id UUID NOT NULL REFERENCES profile_articles(id) ON DELETE RESTRICT,
    bead_width_mm NUMERIC(6, 2) NOT NULL,
    gasket_interior_mm NUMERIC(6, 2) NOT NULL DEFAULT 3.00,
    gasket_exterior_mm NUMERIC(6, 2) NOT NULL DEFAULT 3.00,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uk_system_glass_thickness UNIQUE (system_id, glass_thickness_mm)
);

CREATE TABLE hardware_kits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES tenancy_organizations(id) ON DELETE CASCADE, -- NULL si global
    system_id UUID REFERENCES profile_systems(id) ON DELETE CASCADE,
    sku VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    opening_type VARCHAR(30) NOT NULL,   -- 'TURN','TILT_TURN','SLIDING','AWNING','DOOR'
    min_leaf_width_mm NUMERIC(10,2) NOT NULL,
    max_leaf_width_mm NUMERIC(10,2) NOT NULL,
    min_leaf_height_mm NUMERIC(10,2) NOT NULL,
    max_leaf_height_mm NUMERIC(10,2) NOT NULL,
    max_leaf_weight_kg NUMERIC(6,2) NOT NULL,   -- alimenta Regla R01
    rail_type VARCHAR(10) NOT NULL DEFAULT 'dual',
    carriages_qty INT NOT NULL DEFAULT 2,        -- alimenta Regla R14
    stay_arms_qty INT NOT NULL DEFAULT 1,        -- alimenta Regla R13
    contents JSONB NOT NULL DEFAULT '[]',        -- [{sku, name, qty, unit}]
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_kit_system_sku UNIQUE (system_id, sku)
);

-- ============================================================================
-- 3. COST LISTS, PRICING & PRICE AUDIT LOGS (Enmienda C.1 & M3)
-- ============================================================================

CREATE TABLE cost_lists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    supplier_name VARCHAR(200) NOT NULL,
    description TEXT,
    currency currency_code NOT NULL DEFAULT 'CLP',
    valid_from DATE NOT NULL,
    valid_to DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE cost_list_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cost_list_id UUID NOT NULL REFERENCES cost_lists(id) ON DELETE CASCADE,
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    sku VARCHAR(100) NOT NULL,
    item_type VARCHAR(50) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    unit_cost NUMERIC(14, 4) NOT NULL CHECK (unit_cost >= 0),
    CONSTRAINT uk_cost_list_sku UNIQUE (cost_list_id, sku)
);

CREATE TABLE pricing_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    pricing_mode VARCHAR(50) NOT NULL DEFAULT 'COST_PLUS_MARGIN',
    default_margin_pct NUMERIC(6, 4) NOT NULL DEFAULT 0.3500,
    tax_rate_pct NUMERIC(6, 4) NOT NULL DEFAULT 0.1900,
    waste_factor_pct NUMERIC(6, 4) NOT NULL DEFAULT 0.0800,
    labor_rate_per_m2 NUMERIC(14, 2) NOT NULL DEFAULT 15000.00,
    installation_rate_per_m2 NUMERIC(14, 2) NOT NULL DEFAULT 12000.00,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_org_pricing_rules UNIQUE (org_id)
);

CREATE TABLE price_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
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

-- ============================================================================
-- 4. PROJECTS, POSITIONS & REVISIONS
-- ============================================================================

CREATE TYPE project_status AS ENUM ('DRAFT', 'QUOTED', 'APPROVED', 'IN_PRODUCTION', 'COMPLETED', 'CANCELLED');
CREATE TYPE inspector_status AS ENUM ('GREEN', 'YELLOW', 'RED');

CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    client_name VARCHAR(255) NOT NULL,
    client_rut VARCHAR(50),
    client_email VARCHAR(255),
    client_phone VARCHAR(50),
    delivery_address TEXT,
    status project_status NOT NULL DEFAULT 'DRAFT',
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

CREATE TABLE project_positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    position_index INT NOT NULL,
    location_tag VARCHAR(100),
    typology VARCHAR(50) NOT NULL,
    width_mm NUMERIC(10, 2) NOT NULL CHECK (width_mm >= 250.00),
    height_mm NUMERIC(10, 2) NOT NULL CHECK (height_mm >= 250.00),
    quantity INT NOT NULL DEFAULT 1 CHECK (quantity >= 1),
    system_id UUID NOT NULL REFERENCES profile_systems(id) ON DELETE RESTRICT,
    color_interior VARCHAR(50) NOT NULL DEFAULT 'WHITE',
    color_exterior VARCHAR(50) NOT NULL DEFAULT 'WHITE',
    glass_spec VARCHAR(200) NOT NULL DEFAULT '4-12-4 Float Incoloro',
    parametric_tree JSONB NOT NULL,
    bom_snapshot JSONB NOT NULL,
    cost_net NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    price_net NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    discount_pct NUMERIC(6, 4) NOT NULL DEFAULT 0.0000,
    inspector_status inspector_status NOT NULL DEFAULT 'GREEN',
    inspector_findings JSONB NOT NULL DEFAULT '[]'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_project_position_idx UNIQUE (project_id, position_index)
);

CREATE TABLE project_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    revision_code VARCHAR(10) NOT NULL,
    snapshot_json JSONB NOT NULL,
    pdf_storage_path VARCHAR(500),
    emitted_by UUID NOT NULL,
    emitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_project_revision UNIQUE (project_id, revision_code)
);

-- ============================================================================
-- 5. ORDERS, OFFCUTS & AI AUDIT LOGS
-- ============================================================================

CREATE TYPE order_type AS ENUM ('WORKSHOP_OT', 'SUPPLIER_PROFILE_PO', 'SUPPLIER_GLASS_PO', 'SUPPLIER_HARDWARE_PO');
CREATE TYPE order_status AS ENUM ('DRAFT', 'SENT', 'PARTIALLY_RECEIVED', 'FULFILLED', 'CANCELLED');
CREATE TYPE offcut_status AS ENUM ('AVAILABLE', 'RESERVED', 'CONSUMED', 'DISCARDED');

CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE RESTRICT,
    order_type order_type NOT NULL,
    order_code VARCHAR(50) NOT NULL,
    status order_status NOT NULL DEFAULT 'DRAFT',
    supplier_name VARCHAR(200),
    payload_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_org_order_code UNIQUE (org_id, order_code)
);

CREATE TABLE offcut_inventory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    profile_article_id UUID NOT NULL REFERENCES profile_articles(id) ON DELETE RESTRICT,
    color VARCHAR(50) NOT NULL,
    length_mm NUMERIC(10, 2) NOT NULL CHECK (length_mm >= 500.00),
    rack_location VARCHAR(50),
    source_order_id UUID REFERENCES orders(id) ON DELETE SET NULL,
    reserved_order_id UUID REFERENCES orders(id) ON DELETE SET NULL,
    status offcut_status NOT NULL DEFAULT 'AVAILABLE',
    qr_code VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    consumed_at TIMESTAMPTZ,
    CONSTRAINT uk_org_offcut_qr UNIQUE (org_id, qr_code)
);

CREATE TABLE ai_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
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

-- ============================================================================
-- 5-BIS. BILLING, PAYMENTS & CREDIT LEDGER (Enmienda 1 / P1-1)
-- ============================================================================

CREATE TABLE payment_customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    provider VARCHAR(30) NOT NULL CHECK (provider IN ('flow', 'paddle', 'mercadopago')),
    provider_customer_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_org_provider UNIQUE (org_id, provider)
);

CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    provider VARCHAR(30) NOT NULL,
    provider_subscription_id VARCHAR(100),
    plan_tier subscription_tier NOT NULL CHECK (plan_tier <> 'TRIAL'),
    billing_cycle VARCHAR(10) NOT NULL CHECK (billing_cycle IN ('monthly', 'annual')),
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'past_due', 'cancelled', 'trialing')),
    currency currency_code NOT NULL DEFAULT 'USD',
    amount NUMERIC(12, 2) NOT NULL,
    current_period_end TIMESTAMPTZ,
    founding_member BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_org_subscription UNIQUE (org_id)
);

CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    subscription_id UUID REFERENCES subscriptions(id) ON DELETE SET NULL,
    provider VARCHAR(30) NOT NULL,
    provider_payment_id VARCHAR(100) NOT NULL UNIQUE,
    amount NUMERIC(12, 2) NOT NULL,
    currency currency_code NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'succeeded', 'failed', 'refunded')),
    tax_doc_type VARCHAR(20),
    tax_doc_folio VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE payment_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(30) NOT NULL,
    event_id VARCHAR(150) NOT NULL,
    event_type VARCHAR(100),
    payload JSONB NOT NULL,
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_provider_event UNIQUE (provider, event_id)
);

CREATE TABLE credit_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    amount INT NOT NULL,
    balance_after INT NOT NULL CHECK (balance_after >= 0),
    action_type VARCHAR(50) NOT NULL,
    reference_id UUID,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ledger_org_created ON credit_ledger (org_id, created_at DESC);

-- ============================================================================
-- 6. POLÍTICAS RLS DE AISLAMIENTO MULTI-TENANT (P2-1 & F1)
-- ============================================================================

ALTER TABLE tenancy_organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenancy_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE profile_systems ENABLE ROW LEVEL SECURITY;
ALTER TABLE profile_articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE glazing_bead_matrix ENABLE ROW LEVEL SECURITY;
ALTER TABLE hardware_kits ENABLE ROW LEVEL SECURITY;
ALTER TABLE cost_lists ENABLE ROW LEVEL SECURITY;
ALTER TABLE cost_list_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE pricing_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE price_audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_positions ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE offcut_inventory ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE credit_ledger ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION current_user_org_ids()
RETURNS SETOF UUID AS $$
    SELECT org_id 
    FROM tenancy_memberships 
    WHERE user_id = auth.uid() AND is_active = TRUE;
$$ LANGUAGE SQL STABLE SECURITY DEFINER;

-- Tenancy & Memberships (Lectura de la propia organización para miembros activos)
CREATE POLICY tenancy_organizations_select ON tenancy_organizations
    FOR SELECT USING (id IN (SELECT current_user_org_ids()));

CREATE POLICY tenancy_memberships_select ON tenancy_memberships
    FOR SELECT USING (org_id IN (SELECT current_user_org_ids()));

-- Catálogos (Lectura: Propios O Globales; Escritura: Solo Propios)
CREATE POLICY profile_systems_select ON profile_systems
    FOR SELECT USING (is_global = TRUE OR org_id IN (SELECT current_user_org_ids()));

CREATE POLICY profile_systems_modify ON profile_systems
    FOR ALL USING (org_id IN (SELECT current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT current_user_org_ids()));

CREATE POLICY profile_articles_select ON profile_articles
    FOR SELECT USING (
        system_id IN (SELECT id FROM profile_systems WHERE is_global = TRUE)
        OR org_id IN (SELECT current_user_org_ids())
    );

CREATE POLICY profile_articles_modify ON profile_articles
    FOR ALL USING (org_id IN (SELECT current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT current_user_org_ids()));

CREATE POLICY glazing_bead_matrix_select ON glazing_bead_matrix
    FOR SELECT USING (
        system_id IN (SELECT id FROM profile_systems WHERE is_global = TRUE)
        OR org_id IN (SELECT current_user_org_ids())
    );

CREATE POLICY glazing_bead_matrix_modify ON glazing_bead_matrix
    FOR ALL USING (org_id IN (SELECT current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT current_user_org_ids()));

CREATE POLICY hardware_kits_select ON hardware_kits
    FOR SELECT USING (
        system_id IN (SELECT id FROM profile_systems WHERE is_global = TRUE)
        OR org_id IN (SELECT current_user_org_ids())
    );

CREATE POLICY hardware_kits_modify ON hardware_kits
    FOR ALL USING (org_id IN (SELECT current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT current_user_org_ids()));

-- Negocio y Proyectos
CREATE POLICY projects_isolation ON projects
    FOR ALL USING (org_id IN (SELECT current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT current_user_org_ids()));

CREATE POLICY positions_isolation ON project_positions
    FOR ALL USING (org_id IN (SELECT current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT current_user_org_ids()));

CREATE POLICY project_versions_isolation ON project_versions
    FOR ALL USING (org_id IN (SELECT current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT current_user_org_ids()));

CREATE POLICY orders_isolation ON orders
    FOR ALL USING (org_id IN (SELECT current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT current_user_org_ids()));

CREATE POLICY offcut_inventory_isolation ON offcut_inventory
    FOR ALL USING (org_id IN (SELECT current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT current_user_org_ids()));

CREATE POLICY price_audit_logs_isolation ON price_audit_logs
    FOR ALL USING (org_id IN (SELECT current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT current_user_org_ids()));

CREATE POLICY ai_audit_logs_isolation ON ai_audit_logs
    FOR ALL USING (org_id IN (SELECT current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT current_user_org_ids()));

-- Billing y Pagos
CREATE POLICY payment_customers_isolation ON payment_customers
    FOR ALL USING (org_id IN (SELECT current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT current_user_org_ids()));

CREATE POLICY subscriptions_isolation ON subscriptions
    FOR ALL USING (org_id IN (SELECT current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT current_user_org_ids()));

CREATE POLICY payments_isolation ON payments
    FOR ALL USING (org_id IN (SELECT current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT current_user_org_ids()));

CREATE POLICY credit_ledger_isolation ON credit_ledger
    FOR SELECT USING (org_id IN (SELECT current_user_org_ids()));

CREATE POLICY payment_events_service_role ON payment_events
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');
```
