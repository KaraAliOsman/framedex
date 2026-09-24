BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(14);

-- Tenants read but never write.
SELECT ok(
    (SELECT pol.polcmd = 'r' FROM pg_policy pol
     WHERE pol.polrelid = 'public.delivery_confirmations'::regclass
       AND pol.polname = 'delivery_confirmations_read')
    AND NOT has_table_privilege('authenticated', 'public.delivery_confirmations', 'INSERT')
    AND NOT has_table_privilege('authenticated', 'public.delivery_confirmations', 'UPDATE')
    AND NOT has_table_privilege('authenticated', 'public.delivery_confirmations', 'DELETE'),
    'tenant role policy is SELECT-only and writes are revoked'
);

SELECT has_table(
    'public', 'delivery_confirmations',
    'delivery confirmations table exists'
);
SELECT has_column(
    'public', 'delivery_confirmations', 'org_id',
    'org_id column exists'
);
SELECT has_column(
    'public', 'delivery_confirmations', 'payload_json',
    'sealed payload column exists'
);
SELECT has_column(
    'public', 'delivery_confirmations', 'signature_object_key',
    'immutable signature object key column exists'
);
SELECT col_is_unique(
    'public', 'delivery_confirmations', ARRAY['org_id', 'confirmation_code'],
    'confirmation code unique inside an org'
);
SELECT col_is_unique(
    'public', 'delivery_confirmations', 'order_id',
    'one confirmation per order makes confirm replay-idempotent'
);
SELECT col_is_unique(
    'public', 'delivery_confirmations', 'delivery_id',
    'one confirmation per delivery'
);
SELECT col_is_fk(
    'public', 'delivery_confirmations', 'delivery_id',
    'confirmation belongs to a delivery'
);
SELECT col_is_fk(
    'public', 'delivery_confirmations', 'payment_id',
    'confirmation may reference the cobranza row it collected'
);
SELECT policies_are(
    'public', 'delivery_confirmations',
    ARRAY['delivery_confirmations_read', 'delivery_confirmations_backend'],
    'read for members, writes only for the backend role'
);
SELECT ok(
    has_table_privilege('documentary_backend', 'public.delivery_confirmations', 'INSERT')
    AND NOT has_table_privilege('documentary_backend', 'public.delivery_confirmations', 'UPDATE')
    AND NOT has_table_privilege('documentary_backend', 'public.delivery_confirmations', 'DELETE'),
    'documentary backend may insert but never mutate a sealed confirmation'
);
SELECT ok(
    (SELECT relrowsecurity FROM pg_class
     WHERE oid = 'public.delivery_confirmations'::regclass),
    'row level security is enabled'
);
SELECT ok(
    has_function_privilege('documentary_backend',
        'private.delivery_object_referenced(uuid,text)', 'EXECUTE')
    AND NOT has_function_privilege('authenticated',
        'private.delivery_object_referenced(uuid,text)', 'EXECUTE'),
    'definer reference check is backend-only'
);

SELECT * FROM finish();
ROLLBACK;
