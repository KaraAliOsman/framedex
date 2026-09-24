BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(12);

-- Tenants read but never write.
SELECT ok(
    (SELECT pol.polcmd = 'r' FROM pg_policy pol
     WHERE pol.polrelid = 'public.project_credit_notes'::regclass
       AND pol.polname = 'project_credit_notes_read')
    AND NOT has_table_privilege('authenticated', 'public.project_credit_notes', 'INSERT')
    AND NOT has_table_privilege('authenticated', 'public.project_credit_notes', 'UPDATE')
    AND NOT has_table_privilege('authenticated', 'public.project_credit_notes', 'DELETE'),
    'tenant role policy is SELECT-only and writes are revoked'
);

SELECT has_table(
    'public', 'project_credit_notes',
    'project credit notes table exists'
);
SELECT has_column(
    'public', 'project_credit_notes', 'org_id',
    'org_id column exists'
);
SELECT has_column(
    'public', 'project_credit_notes', 'payload_json',
    'sealed payload column exists'
);
SELECT has_column(
    'public', 'project_credit_notes', 'storage_object_key',
    'immutable storage object key column exists'
);
SELECT col_is_unique(
    'public', 'project_credit_notes', ARRAY['org_id', 'credit_code'],
    'credit code unique inside an org'
);
SELECT col_is_unique(
    'public', 'project_credit_notes', 'invoice_id',
    'one total credit note per invoice makes emission replay-idempotent'
);
SELECT col_is_fk(
    'public', 'project_credit_notes', 'project_id',
    'credit note belongs to a project'
);
SELECT col_is_fk(
    'public', 'project_credit_notes', 'invoice_id',
    'credit note annuls a specific invoice'
);
SELECT policies_are(
    'public', 'project_credit_notes',
    ARRAY['project_credit_notes_read', 'project_credit_notes_backend'],
    'read for members, writes only for the backend role'
);
SELECT ok(
    has_table_privilege('documentary_backend', 'public.project_credit_notes', 'INSERT')
    AND NOT has_table_privilege('documentary_backend', 'public.project_credit_notes', 'UPDATE')
    AND NOT has_table_privilege('documentary_backend', 'public.project_credit_notes', 'DELETE'),
    'documentary backend may insert but never mutate a sealed credit note'
);
SELECT ok(
    (SELECT relrowsecurity FROM pg_class
     WHERE oid = 'public.project_credit_notes'::regclass),
    'row level security is enabled'
);

SELECT * FROM finish();
ROLLBACK;
