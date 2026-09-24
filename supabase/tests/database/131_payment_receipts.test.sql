BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(10);

SELECT has_table(
    'public', 'payment_receipts',
    'receipts table exists'
);
SELECT has_column(
    'public', 'payment_receipts', 'org_id',
    'org_id column exists'
);
SELECT col_is_fk(
    'public', 'payment_receipts', 'org_id',
    'org_id references tenancy_organizations'
);
SELECT col_is_fk(
    'public', 'payment_receipts', 'payment_id',
    'receipt references the payment'
);
SELECT col_is_unique(
    'public', 'payment_receipts', 'payment_id',
    'one sealed receipt per payment'
);
SELECT col_is_unique(
    'public', 'payment_receipts', ARRAY['org_id', 'receipt_code'],
    'receipt sequence unique inside an org'
);
SELECT has_column(
    'public', 'payment_receipts', 'payload_json',
    'sealed render inputs are stored'
);
SELECT policies_are(
    'public', 'payment_receipts',
    ARRAY['payment_receipts_read', 'payment_receipts_backend'],
    'tenant reads, only the backend role writes'
);
SELECT ok(
    (SELECT pol.polcmd = 'r' FROM pg_policy pol
     WHERE pol.polrelid = 'public.payment_receipts'::regclass
       AND pol.polname = 'payment_receipts_read')
    AND NOT has_table_privilege('authenticated', 'public.payment_receipts', 'INSERT')
    AND NOT has_table_privilege('documentary_backend', 'public.payment_receipts', 'UPDATE')
    AND NOT has_table_privilege('documentary_backend', 'public.payment_receipts', 'DELETE'),
    'sealed evidence: tenants cannot insert, backend cannot mutate'
);
SELECT ok(
    (SELECT relrowsecurity FROM pg_class
     WHERE oid = 'public.payment_receipts'::regclass),
    'row level security is enabled'
);

SELECT * FROM finish();
ROLLBACK;
