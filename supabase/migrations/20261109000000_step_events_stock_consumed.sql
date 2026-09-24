-- §10 stock consumption is recorded on the step's event stream when a
-- consuming routing step completes (WO_STOCK_CONSUMED). The event enum
-- never listed it, so completing a consuming step always violated the
-- check constraint on a correctly migrated database.
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
        'WO_REMNANTS_SETTLED', 'WO_OPS_EXPORTED', 'WO_STOCK_CONSUMED'
    ));
