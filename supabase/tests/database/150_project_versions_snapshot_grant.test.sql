BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(2);

-- snapshot_json carries the sealed manufacturing facts the production trace
-- reconstructs operations from; without the column grant every order trace
-- 409s on a correctly migrated DB.
SELECT ok(
    has_column_privilege('authenticated', 'public.project_versions', 'snapshot_json', 'SELECT'),
    'snapshot_json is tenant-readable for the production trace'
);
SELECT ok(
    NOT has_column_privilege('authenticated', 'public.project_versions', 'pdf_storage_path', 'SELECT'),
    'internal storage paths stay denied to tenants'
);

SELECT * FROM finish();
ROLLBACK;
