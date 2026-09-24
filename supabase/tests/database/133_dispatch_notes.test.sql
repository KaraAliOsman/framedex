BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(10);

-- Tenants read but never write.
SELECT ok(
    (SELECT pol.polcmd = 'r' FROM pg_policy pol
     WHERE pol.polrelid = 'public.dispatch_notes'::regclass
       AND pol.polname = 'dispatch_notes_read')
    AND NOT has_table_privilege('authenticated', 'public.dispatch_notes', 'INSERT')
    AND NOT has_table_privilege('authenticated', 'public.dispatch_notes', 'UPDATE')
    AND NOT has_table_privilege('authenticated', 'public.dispatch_notes', 'DELETE'),
    'tenant role policy is SELECT-only and writes are revoked'
);

SELECT has_table(
    'public', 'dispatch_notes',
    'dispatch notes table exists'
);
SELECT has_column(
    'public', 'dispatch_notes', 'org_id',
    'org_id column exists'
);
SELECT has_column(
    'public', 'dispatch_notes', 'payload_json',
    'sealed payload column exists'
);
SELECT col_is_unique(
    'public', 'dispatch_notes', 'work_order_id',
    'one guía de despacho per work order'
);
SELECT col_is_unique(
    'public', 'dispatch_notes', ARRAY['org_id', 'note_code'],
    'note code unique inside an org'
);
SELECT col_is_fk(
    'public', 'dispatch_notes', 'work_order_id',
    'note belongs to an order'
);
SELECT policies_are(
    'public', 'dispatch_notes',
    ARRAY['dispatch_notes_read', 'dispatch_notes_backend'],
    'read for members, writes only for the backend role'
);
SELECT ok(
    has_table_privilege('documentary_backend', 'public.dispatch_notes', 'INSERT'),
    'documentary backend may insert sealed notes'
);
SELECT ok(
    (SELECT relrowsecurity FROM pg_class
     WHERE oid = 'public.dispatch_notes'::regclass),
    'row level security is enabled'
);

SELECT * FROM finish();
ROLLBACK;
