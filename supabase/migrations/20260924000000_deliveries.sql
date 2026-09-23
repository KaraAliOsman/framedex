-- Delivery scheduling: one active delivery per work order; transitions feed
-- the order timeline via production_step_events.
-- Append-only on top of 20260923220500_analytics_orders_read.sql.

CREATE TABLE public.deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    order_id UUID NOT NULL REFERENCES public.orders(id) ON DELETE RESTRICT,
    scheduled_date DATE NOT NULL,
    time_window TEXT NOT NULL DEFAULT 'AM'
        CHECK (time_window IN ('AM', 'PM', 'JORNADA')),
    address TEXT NOT NULL CHECK (length(btrim(address)) > 0),
    contact_name TEXT,
    contact_phone TEXT,
    installer_name TEXT,
    notes TEXT,
    status TEXT NOT NULL DEFAULT 'SCHEDULED'
        CHECK (status IN ('SCHEDULED', 'ON_ROUTE', 'DELIVERED', 'FAILED')),
    scheduled_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (order_id)
);
CREATE INDEX deliveries_org_idx ON public.deliveries (org_id);
CREATE INDEX deliveries_date_idx ON public.deliveries (org_id, scheduled_date);

ALTER TABLE public.deliveries ENABLE ROW LEVEL SECURITY;

CREATE POLICY deliveries_isolation ON public.deliveries FOR ALL
USING (org_id IN (SELECT private.current_user_org_ids()))
WITH CHECK (org_id IN (SELECT private.current_user_org_ids()));

ALTER TABLE public.production_step_events
    DROP CONSTRAINT production_step_events_event_check;
ALTER TABLE public.production_step_events
    ADD CONSTRAINT production_step_events_event_check
    CHECK (event IN (
        'WO_RELEASED', 'STEP_STARTED', 'STEP_COMPLETED', 'STEP_BLOCKED',
        'STEP_UNBLOCKED', 'NOTE', 'WO_COMPLETED', 'WO_HOLD', 'WO_OPTIMIZED',
        'QC_FAILED', 'WO_REMADE', 'WO_CNC_EXPORTED',
        'WO_PACKED', 'WO_DISPATCHED', 'WO_INSTALLED',
        'WO_DELIVERY_SCHEDULED', 'WO_DELIVERY_ON_ROUTE',
        'WO_DELIVERY_DELIVERED', 'WO_DELIVERY_FAILED'
    ));

REVOKE ALL ON public.deliveries FROM anon;
GRANT SELECT ON public.deliveries TO authenticated;
GRANT SELECT, INSERT, UPDATE ON public.deliveries TO documentary_backend;
GRANT ALL ON public.deliveries TO service_role;
-- pg_default_acl hands arwdDxtm on new public tables to app roles; tenant
-- members only read deliveries through the API/backend role.
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER ON public.deliveries FROM authenticated;
