BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(12);

SELECT has_table('public', 'work_centers', 'work centers table exists');
SELECT has_table('public', 'production_steps', 'routing steps table exists');
SELECT has_table('public', 'production_step_events', 'append-only step events table exists');
SELECT ok(
    EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE schemaname = 'public' AND indexname = 'orders_workshop_position_uq'
    ),
    'one work order per sealed position per version'
);
SELECT ok(
    EXISTS (
        SELECT 1 FROM pg_enum e
        JOIN pg_type t ON t.oid = e.enumtypid
        WHERE t.typname = 'order_status' AND e.enumlabel = 'IN_PROGRESS'
    ),
    'workshop order statuses include production lifecycle values'
);
SELECT ok(
    NOT has_table_privilege('authenticated', 'public.production_step_events', 'UPDATE')
    AND NOT has_table_privilege('authenticated', 'public.production_step_events', 'DELETE'),
    'step events are append-only for tenant roles'
);
SELECT ok(
    has_table_privilege('authenticated', 'public.production_step_events', 'INSERT')
    AND has_table_privilege('authenticated', 'public.production_step_events', 'SELECT'),
    'tenant roles can append and read step events'
);
SELECT ok(
    NOT has_table_privilege('service_role', 'public.production_step_events', 'UPDATE')
    AND NOT has_table_privilege('service_role', 'public.production_step_events', 'DELETE'),
    'step events are append-only for service_role too'
);
SELECT ok(
    EXISTS (
        SELECT 1 FROM pg_tables
        WHERE schemaname = 'public'
          AND tablename = 'production_steps'
          AND rowsecurity = true
    ),
    'routing steps enforce row level security'
);
SELECT throws_ok(
    $$INSERT INTO public.production_steps
        (org_id, order_id, sequence, code, label, status)
      VALUES ('00000000-0000-0000-0000-000000000000',
              '00000000-0000-0000-0000-000000000000',
              1, 'CUT', 'x', 'DONE')$$,
    '23503',
    NULL,
    'steps cannot reference a non-existent work order'
);
SELECT throws_ok(
    $$INSERT INTO public.production_step_events
        (org_id, order_id, event)
      VALUES ('00000000-0000-0000-0000-000000000000',
              '00000000-0000-0000-0000-000000000000', 'STEP_STARTED')$$,
    '23503',
    NULL,
    'events cannot reference a non-existent work order'
);
SELECT ok(
    EXISTS (
        SELECT 1 FROM pg_class c JOIN pg_namespace n ON c.relnamespace = n.oid
        WHERE n.nspname = 'public' AND c.relname = 'work_centers_org_id_code_key'
    ) OR EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE schemaname = 'public' AND indexname LIKE 'work_centers%code%'
    ),
    'work center codes unique per org'
);
SELECT * FROM finish();
ROLLBACK;
