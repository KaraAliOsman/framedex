-- Delivery confirmations (comprobante de entrega): the sealed proof that the
-- client received the goods — receiver identity + signature rendered into an
-- immutable PDF. One confirmation per work order; UNIQUE(order_id) makes a
-- retried confirmation replay the already-sealed row. When the driver also
-- collects payment (contado contra entrega), the cobranza row lands in the
-- same transaction and is referenced here — no re-entering between
-- departments.
-- Append-only on top of 20261012000000_project_credit_notes.sql.

CREATE TABLE public.delivery_confirmations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL
        REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    order_id UUID NOT NULL
        REFERENCES public.orders(id) ON DELETE RESTRICT,
    delivery_id UUID NOT NULL
        REFERENCES public.deliveries(id) ON DELETE RESTRICT,
    payment_id UUID
        REFERENCES public.project_payments(id) ON DELETE RESTRICT,
    confirmation_code VARCHAR(30) NOT NULL,
    payload_json JSONB NOT NULL,
    signature_object_key TEXT NOT NULL,
    storage_bucket TEXT NOT NULL CHECK (storage_bucket = 'documents'),
    storage_object_key TEXT NOT NULL,
    file_sha256 TEXT NOT NULL CHECK (file_sha256 ~ '^[0-9a-f]{64}$'),
    media_type TEXT NOT NULL CHECK (media_type = 'application/pdf'),
    byte_size BIGINT NOT NULL CHECK (byte_size > 0),
    issued_by UUID NOT NULL,
    issued_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_org_confirmation_code UNIQUE (org_id, confirmation_code),
    CONSTRAINT uk_confirmation_order UNIQUE (order_id),
    CONSTRAINT uk_confirmation_delivery UNIQUE (delivery_id)
);

CREATE INDEX idx_delivery_confirmations_org
    ON public.delivery_confirmations (org_id);

ALTER TABLE public.delivery_confirmations ENABLE ROW LEVEL SECURITY;

-- Tenants read the registry; only the backend role writes it, and only
-- INSERT — the grant set is what makes a confirmation sealed evidence.
CREATE POLICY delivery_confirmations_read ON public.delivery_confirmations
    FOR SELECT TO authenticated
    USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY delivery_confirmations_backend ON public.delivery_confirmations
    FOR ALL TO documentary_backend
    USING (org_id IN (SELECT private.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT private.current_user_org_ids()));

GRANT SELECT ON public.delivery_confirmations TO authenticated;
GRANT SELECT, INSERT ON public.delivery_confirmations TO documentary_backend;
GRANT ALL ON public.delivery_confirmations TO service_role;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER
    ON public.delivery_confirmations FROM authenticated;
REVOKE ALL ON public.delivery_confirmations FROM anon;

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
        'WO_DELIVERY_DELIVERED', 'WO_DELIVERY_FAILED', 'WO_DELIVERY_CONFIRMED'
    ));
