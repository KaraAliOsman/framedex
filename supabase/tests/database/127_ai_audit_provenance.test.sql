BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(4);

-- Provider provenance is backend-only: the audit row points at the route
-- (which only billing_backend can read) rather than storing provider/model
-- text in the tenant-readable model_used.
SELECT has_column('public', 'ai_audit_logs', 'route_id',
    'audit rows carry backend-only route provenance');
SELECT col_type_is('public', 'ai_audit_logs', 'route_id', 'uuid',
    'route provenance is the route id');
SELECT col_is_fk('public', 'ai_audit_logs', 'route_id',
    'route provenance is a foreign key into ai_routes');

-- Immutability at every privilege level: the trigger refuses UPDATE/DELETE
-- even for backend roles and the table owner.
SELECT has_trigger('public', 'ai_audit_logs', 'immutable_ai_audit_logs',
    'audit history is immutable for every role');

SELECT * FROM finish();
ROLLBACK;
