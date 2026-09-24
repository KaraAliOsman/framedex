BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(9);

SELECT has_table(
    'public', 'clients',
    'clients table exists'
);
SELECT has_column(
    'public', 'clients', 'org_id',
    'org_id column exists'
);
SELECT col_is_fk(
    'public', 'clients', 'org_id',
    'org_id references tenancy_organizations'
);
SELECT has_column(
    'public', 'clients', 'is_active',
    'is_active column exists'
);
SELECT col_is_unique(
    'public', 'clients', ARRAY['org_id', 'rut'],
    'one client per RUT inside an org'
);
SELECT has_column(
    'public', 'projects', 'client_id',
    'projects.client_id column exists'
);
SELECT col_is_fk(
    'public', 'projects', 'client_id',
    'projects.client_id references clients'
);
SELECT policies_are(
    'public', 'clients',
    ARRAY['clients_isolation'],
    'exactly the org isolation policy'
);
SELECT ok(
    (SELECT relrowsecurity FROM pg_class
     WHERE oid = 'public.clients'::regclass),
    'row level security is enabled'
);

SELECT * FROM finish();
ROLLBACK;
