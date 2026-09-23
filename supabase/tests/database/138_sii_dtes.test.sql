BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(12);

SELECT has_table('public', 'sii_cafs', 'sii_cafs exists');
SELECT has_table('public', 'project_dtes', 'project_dtes exists');

SELECT col_is_unique(
    'public', 'sii_cafs', ARRAY['org_id', 'tipo_dte', 'folio_desde'],
    'caf ranges unique inside an org'
);
SELECT col_is_unique(
    'public', 'project_dtes', ARRAY['org_id', 'invoice_id'],
    'one DTE per invoice makes emit replay-idempotent'
);
SELECT col_is_unique(
    'public', 'project_dtes', ARRAY['org_id', 'dte_type', 'folio'],
    'a folio can never be stamped twice'
);
SELECT col_is_fk(
    'public', 'project_dtes', 'invoice_id',
    'dte belongs to a sealed invoice'
);
SELECT col_is_fk(
    'public', 'project_dtes', 'caf_id',
    'dte references the CAF it was stamped with'
);

-- Tenants read but never write; the backend owns allocation and sealing.
SELECT ok(
    (SELECT pol.polcmd = 'r' FROM pg_policy pol
     WHERE pol.polrelid = 'public.sii_cafs'::regclass
       AND pol.polname = 'sii_cafs_read')
    AND NOT has_table_privilege('authenticated', 'public.sii_cafs', 'INSERT')
    AND NOT has_table_privilege('authenticated', 'public.sii_cafs', 'UPDATE')
    AND NOT has_table_privilege('authenticated', 'public.sii_cafs', 'DELETE'),
    'tenant caf policy is SELECT-only and writes are revoked'
);
SELECT ok(
    (SELECT pol.polcmd = 'r' FROM pg_policy pol
     WHERE pol.polrelid = 'public.project_dtes'::regclass
       AND pol.polname = 'project_dtes_read')
    AND NOT has_table_privilege('authenticated', 'public.project_dtes', 'INSERT')
    AND NOT has_table_privilege('authenticated', 'public.project_dtes', 'UPDATE')
    AND NOT has_table_privilege('authenticated', 'public.project_dtes', 'DELETE'),
    'tenant dte policy is SELECT-only and writes are revoked'
);

SELECT ok(
    has_table_privilege('documentary_backend', 'public.sii_cafs', 'INSERT')
    AND has_table_privilege('documentary_backend', 'public.sii_cafs', 'UPDATE')
    AND NOT has_table_privilege('documentary_backend', 'public.sii_cafs', 'DELETE'),
    'backend may register cafs and advance the folio cursor, never delete'
);
SELECT ok(
    has_table_privilege('documentary_backend', 'public.project_dtes', 'INSERT')
    AND NOT has_table_privilege('documentary_backend', 'public.project_dtes', 'UPDATE')
    AND NOT has_table_privilege('documentary_backend', 'public.project_dtes', 'DELETE'),
    'backend may insert but never mutate a sealed DTE'
);
SELECT ok(
    (SELECT relrowsecurity FROM pg_class
     WHERE oid = 'public.project_dtes'::regclass)
    AND (SELECT relrowsecurity FROM pg_class
     WHERE oid = 'public.sii_cafs'::regclass),
    'row level security is enabled on both tables'
);

SELECT * FROM finish();
ROLLBACK;
