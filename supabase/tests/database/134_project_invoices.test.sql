BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(11);

-- Tenants read but never write.
SELECT ok(
    (SELECT pol.polcmd = 'r' FROM pg_policy pol
     WHERE pol.polrelid = 'public.project_invoices'::regclass
       AND pol.polname = 'project_invoices_read')
    AND NOT has_table_privilege('authenticated', 'public.project_invoices', 'INSERT')
    AND NOT has_table_privilege('authenticated', 'public.project_invoices', 'UPDATE')
    AND NOT has_table_privilege('authenticated', 'public.project_invoices', 'DELETE'),
    'tenant role policy is SELECT-only and writes are revoked'
);

SELECT has_table(
    'public', 'project_invoices',
    'project invoices table exists'
);
SELECT has_column(
    'public', 'project_invoices', 'org_id',
    'org_id column exists'
);
SELECT has_column(
    'public', 'project_invoices', 'payload_json',
    'sealed payload column exists'
);
SELECT col_is_unique(
    'public', 'project_invoices', ARRAY['org_id', 'invoice_code'],
    'invoice code unique inside an org'
);
SELECT col_is_fk(
    'public', 'project_invoices', 'project_id',
    'invoice belongs to a project'
);
SELECT col_is_fk(
    'public', 'project_invoices', 'project_version_id',
    'invoice pins the sealed revision it billed'
);
SELECT policies_are(
    'public', 'project_invoices',
    ARRAY['project_invoices_read', 'project_invoices_backend'],
    'read for members, writes only for the backend role'
);
SELECT ok(
    has_table_privilege('documentary_backend', 'public.project_invoices', 'INSERT')
    AND NOT has_table_privilege('documentary_backend', 'public.project_invoices', 'UPDATE')
    AND NOT has_table_privilege('documentary_backend', 'public.project_invoices', 'DELETE'),
    'documentary backend may insert but never mutate a sealed invoice'
);
SELECT ok(
    (SELECT relrowsecurity FROM pg_class
     WHERE oid = 'public.project_invoices'::regclass),
    'row level security is enabled'
);
SELECT ok(
    NOT has_table_privilege('anon', 'public.project_invoices', 'SELECT'),
    'anon role cannot read invoices'
);

SELECT * FROM finish();
ROLLBACK;
