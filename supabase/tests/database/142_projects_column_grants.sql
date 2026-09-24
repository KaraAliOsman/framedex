BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(2);

-- Columns added after the shot-08 column enumeration must be granted
-- explicitly; otherwise every project read 409s on a correctly migrated DB.
SELECT ok(
    has_column_privilege('authenticated', 'public.projects', 'client_id', 'SELECT')
    AND has_column_privilege('authenticated', 'public.projects', 'client_giro', 'SELECT')
    AND has_column_privilege('authenticated', 'public.projects', 'client_comuna', 'SELECT')
    AND has_column_privilege('authenticated', 'public.projects', 'client_address', 'SELECT')
    AND has_column_privilege('authenticated', 'public.projects', 'pricing_reset_at', 'SELECT'),
    'post-enumeration projects columns stay tenant-readable'
);
SELECT ok(
    NOT has_column_privilege('authenticated', 'public.projects', 'total_cost_net', 'SELECT')
    AND NOT has_column_privilege('authenticated', 'public.project_positions', 'cost_net', 'SELECT'),
    'privileged pricing columns remain denied to tenants'
);

SELECT * FROM finish();
ROLLBACK;
