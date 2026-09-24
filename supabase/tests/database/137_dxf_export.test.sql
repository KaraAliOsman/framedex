BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(2);

SELECT ok(
    EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.production_step_events'::regclass
          AND conname = 'production_step_events_event_check'
          AND pg_get_constraintdef(oid) LIKE '%WO_DXF_EXPORTED%'
    ),
    'step events accept WO_DXF_EXPORTED'
);

SELECT throws_ok(
    $$INSERT INTO public.production_step_events
        (org_id, order_id, event, actor_id, payload)
      VALUES ('e0d86732-fd0f-4a96-8ff7-3366a5e08486',
              '00000000-0000-0000-0000-000000000000',
              'WO_DXF_EXPORTED_V2', gen_random_uuid(), '{}'::jsonb)$$,
    '23514',
    NULL,
    'unknown event names are rejected by the check constraint'
);

SELECT * FROM finish();
ROLLBACK;
