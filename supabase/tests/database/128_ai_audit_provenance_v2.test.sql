BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(9);

SELECT has_table(
    'public', 'ai_audit_provenance',
    'provenance table exists'
);
SELECT has_column(
    'public', 'ai_audit_provenance', 'audit_id',
    'audit_id column exists'
);
SELECT col_type_is(
    'public', 'ai_audit_provenance', 'audit_id', 'uuid',
    'audit_id is uuid'
);
SELECT col_is_fk(
    'public', 'ai_audit_provenance', 'audit_id',
    'audit_id references ai_audit_logs'
);
SELECT has_trigger(
    'public', 'ai_audit_logs', 'immutable_ai_audit_logs',
    'immutability trigger still installed'
);
SELECT has_function(
    'private', 'reject_ai_audit_mutation', ARRAY[]::text[],
    'purge-aware trigger function exists'
);
SELECT has_function(
    'private', 'purge_expired_ai_audit', ARRAY[]::text[],
    'retention purge function exists'
);
SELECT function_privs_are(
    'private', 'purge_expired_ai_audit', ARRAY[]::text[],
    'service_role', ARRAY['EXECUTE'],
    'service_role may execute the retention purge'
);

-- ACL is not enough — the qualified call needs schema USAGE too.
SET LOCAL ROLE service_role;
SELECT lives_ok(
    'SELECT private.purge_expired_ai_audit()',
    'service_role can actually invoke the retention purge'
);

SELECT * FROM finish();
ROLLBACK;
