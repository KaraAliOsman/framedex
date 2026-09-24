-- §6: remnant/offcut inventory — dimensional stock with a lifecycle.
--
-- A remnant is one physical piece of leftover material (a bar drop or a sheet
-- offcut) with exact dimensions, its producing stock identity, its origin
-- order, and a status the optimizer can consume. Unlike `inventory_items`
-- (SKU-level quantity stock), remnants are per-instance: a 700mm drop is a
-- different bar than a 5900mm drop.
--
-- Lifecycle: AVAILABLE → RESERVED (a work-order plan claims it) → CONSUMED
-- (the CUT step completes) or back to AVAILABLE (plan replaced / order
-- cancelled) → SCRAPPED. Double-consumption is prevented by locking rows and
-- requiring the status transition — a CONSUMED remnant can never host again.

CREATE TABLE public.inventory_remnants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    kind TEXT NOT NULL CHECK (kind IN ('BAR', 'SHEET')),
    -- Identity: which stock this remnant is. BAR remnants reference the
    -- purchase-mapping or reinforcement-article authority row that produced
    -- them; SHEET remnants reference the workshop_sku they were nested under.
    stock_authority_id UUID,
    sheet_workshop_sku TEXT,
    physical_stock_identity UUID,
    material TEXT,
    color TEXT,
    length_mm NUMERIC(14, 2),
    width_mm NUMERIC(14, 2),
    height_mm NUMERIC(14, 2),
    status TEXT NOT NULL DEFAULT 'AVAILABLE'
        CHECK (status IN ('AVAILABLE', 'RESERVED', 'CONSUMED', 'SCRAPPED')),
    origin TEXT NOT NULL DEFAULT 'MANUAL'
        CHECK (origin IN ('RECEIPT', 'PRODUCTION', 'MANUAL')),
    origin_order_id UUID REFERENCES public.orders(id) ON DELETE SET NULL,
    reserved_order_id UUID REFERENCES public.orders(id) ON DELETE SET NULL,
    consumed_order_id UUID REFERENCES public.orders(id) ON DELETE SET NULL,
    rack_location TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT inventory_remnants_dims_chk CHECK (
        (kind = 'BAR'
            AND length_mm IS NOT NULL AND length_mm > 0
            AND width_mm IS NULL AND height_mm IS NULL
            AND stock_authority_id IS NOT NULL AND sheet_workshop_sku IS NULL)
        OR
        (kind = 'SHEET'
            AND width_mm IS NOT NULL AND width_mm > 0
            AND height_mm IS NOT NULL AND height_mm > 0
            AND length_mm IS NULL
            AND sheet_workshop_sku IS NOT NULL AND stock_authority_id IS NULL)
    )
);

CREATE INDEX inventory_remnants_org_kind_status_idx
    ON public.inventory_remnants (org_id, kind, status);
CREATE INDEX inventory_remnants_reserved_order_idx
    ON public.inventory_remnants (reserved_order_id) WHERE reserved_order_id IS NOT NULL;

ALTER TABLE public.inventory_remnants ENABLE ROW LEVEL SECURITY;

-- Same trust split as production_steps: org-isolation policy for everyone,
-- but only the documentary role holds write grants — `authenticated` reads
-- org-scoped rows and can never forge, reserve, or consume a remnant
-- directly; every mutation travels through the service layer, which gates
-- roles at the view and owns the status machine. No DELETE grant anywhere
-- except service_role: remnants are a ledger — they leave via status, never
-- row removal, so a consumed remnant stays traceable to its origin order.
CREATE POLICY inventory_remnants_isolation ON public.inventory_remnants FOR ALL
    USING (org_id IN (SELECT private.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT private.current_user_org_ids()));

GRANT SELECT ON public.inventory_remnants TO authenticated;
GRANT SELECT, INSERT, UPDATE ON public.inventory_remnants TO documentary_backend;
GRANT ALL ON public.inventory_remnants TO service_role;
-- pg_default_acl hands arwdDxtm on new public tables to app roles; tenant
-- members only read remnants — every mutation travels through the backend.
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER ON public.inventory_remnants FROM authenticated;
REVOKE DELETE, TRUNCATE, TRIGGER ON public.inventory_remnants FROM documentary_backend;

-- The remnant settle fires when a CUT step completes: drops consumed,
-- usable remainders returned to stock under this order's provenance.
ALTER TABLE public.production_step_events
    DROP CONSTRAINT production_step_events_event_check;
ALTER TABLE public.production_step_events
    ADD CONSTRAINT production_step_events_event_check
    CHECK (event IN (
        'WO_RELEASED', 'STEP_STARTED', 'STEP_COMPLETED', 'STEP_BLOCKED',
        'STEP_UNBLOCKED', 'NOTE', 'WO_COMPLETED', 'WO_HOLD', 'WO_OPTIMIZED',
        'QC_FAILED', 'WO_REMADE', 'WO_CNC_EXPORTED', 'WO_DXF_EXPORTED',
        'WO_PACKED', 'WO_DISPATCHED', 'WO_INSTALLED',
        'WO_DELIVERY_SCHEDULED', 'WO_DELIVERY_ON_ROUTE',
        'WO_DELIVERY_DELIVERED', 'WO_DELIVERY_FAILED', 'WO_DELIVERY_CONFIRMED',
        'WO_REMNANTS_SETTLED'
    ));
