BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(2);

-- §B: the frozen snapshot carries client PII, pricing, BOM and manufacturing
-- authority — it must never be tenant-readable through PostgREST. The
-- production trace resolves it server-side via the documentary authority.
SELECT ok(
    NOT has_column_privilege('authenticated', 'public.project_versions', 'snapshot_json', 'SELECT'),
    'snapshot_json is denied to the tenant role'
);
SELECT ok(
    has_column_privilege('documentary_backend', 'public.project_versions', 'snapshot_json', 'SELECT'),
    'snapshot_json stays readable by the documentary authority'
);

SELECT * FROM finish();
ROLLBACK;
