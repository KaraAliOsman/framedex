BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(9);

SELECT has_table(
    'public', 'catalog_imports',
    'catalog_imports table exists'
);
SELECT has_column(
    'public', 'catalog_imports', 'org_id',
    'org_id column exists'
);
SELECT col_is_fk(
    'public', 'catalog_imports', 'org_id',
    'org_id references tenancy_organizations'
);
SELECT has_column(
    'public', 'catalog_imports', 'system_id',
    'system_id column exists'
);
SELECT col_is_fk(
    'public', 'catalog_imports', 'system_id',
    'system_id references profile_systems'
);
SELECT has_column(
    'public', 'catalog_imports', 'candidates',
    'candidates column exists'
);
SELECT has_column(
    'public', 'catalog_imports', 'result',
    'result column exists'
);
SELECT has_column(
    'public', 'catalog_imports', 'audit_id',
    'audit_id column exists'
);
SELECT policies_are(
    'public', 'catalog_imports',
    ARRAY[
        'catalog_imports_member_read',
        'catalog_imports_member_insert',
        'catalog_imports_member_update',
        'catalog_imports_backend'
    ],
    'exactly the member + backend policies'
);

SELECT * FROM finish();
ROLLBACK;
