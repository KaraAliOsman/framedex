-- Packing manifest + dispatch: order status DISPATCHED and step events
-- WO_PACKED / WO_DISPATCHED. Append-only on top of
-- 20260923170000_production_cnc_export.sql.

ALTER TYPE public.order_status ADD VALUE IF NOT EXISTS 'DISPATCHED';

ALTER TABLE public.production_step_events
    DROP CONSTRAINT production_step_events_event_check;
ALTER TABLE public.production_step_events
    ADD CONSTRAINT production_step_events_event_check
    CHECK (event IN (
        'WO_RELEASED', 'STEP_STARTED', 'STEP_COMPLETED', 'STEP_BLOCKED',
        'STEP_UNBLOCKED', 'NOTE', 'WO_COMPLETED', 'WO_HOLD', 'WO_OPTIMIZED',
        'QC_FAILED', 'WO_REMADE', 'WO_CNC_EXPORTED',
        'WO_PACKED', 'WO_DISPATCHED'
    ));
