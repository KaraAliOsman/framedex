-- QC outcome events + remake orders: extend the step-event CHECK and exclude
-- remakes from the per-position release uniqueness. Applies on top of
-- 20260923150000_production.sql (safe whether that migration shipped earlier or
-- in the same batch — the constraint/index are recreated deterministically).

ALTER TABLE public.production_step_events
    DROP CONSTRAINT production_step_events_event_check;
ALTER TABLE public.production_step_events
    ADD CONSTRAINT production_step_events_event_check
    CHECK (event IN (
        'WO_RELEASED', 'STEP_STARTED', 'STEP_COMPLETED', 'STEP_BLOCKED',
        'STEP_UNBLOCKED', 'NOTE', 'WO_COMPLETED', 'WO_HOLD', 'WO_OPTIMIZED',
        'QC_FAILED', 'WO_REMADE'
    ));

DROP INDEX IF EXISTS public.orders_workshop_position_uq;
CREATE UNIQUE INDEX orders_workshop_position_uq
    ON public.orders (org_id, project_version_id, (payload_json->>'position_id'))
    WHERE order_type = 'WORKSHOP_OT'
      AND project_version_id IS NOT NULL
      AND payload_json ? 'position_id'
      AND NOT (payload_json ? 'remake_of');
