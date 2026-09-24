BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(14);

SELECT has_table('public', 'sii_certificates', 'sii_certificates exists');
SELECT has_table('public', 'sii_envios', 'sii_envios exists');

SELECT col_is_fk(
    'public', 'sii_envios', 'dte_id',
    'envio references the DTE it transports'
);
SELECT col_is_unique(
    'public', 'sii_envios', ARRAY['org_id', 'dte_id'],
    'one envio per DTE makes send replay-idempotent'
);
SELECT index_is_unique(
    'public', 'sii_certificates', 'uk_sii_cert_active',
    'only one active certificate per org'
);
SELECT has_check(
    'public', 'sii_envios',
    'envio status lifecycle is PENDING/ACCEPTED/REJECTED'
);
SELECT has_check(
    'public', 'sii_certificates',
    'certificate nro_resol is non-negative'
);

-- Tenants read but never write; the backend owns certificate material and
-- the SII-side status lifecycle.
SELECT ok(
    (SELECT pol.polcmd = 'r' FROM pg_policy pol
     WHERE pol.polrelid = 'public.sii_certificates'::regclass
       AND pol.polname = 'sii_certificates_read')
    AND NOT has_table_privilege('authenticated', 'public.sii_certificates', 'INSERT')
    AND NOT has_table_privilege('authenticated', 'public.sii_certificates', 'UPDATE')
    AND NOT has_table_privilege('authenticated', 'public.sii_certificates', 'DELETE'),
    'tenant certificate policy is SELECT-only and writes are revoked'
);
SELECT ok(
    (SELECT pol.polcmd = 'r' FROM pg_policy pol
     WHERE pol.polrelid = 'public.sii_envios'::regclass
       AND pol.polname = 'sii_envios_read')
    AND NOT has_table_privilege('authenticated', 'public.sii_envios', 'INSERT')
    AND NOT has_table_privilege('authenticated', 'public.sii_envios', 'UPDATE')
    AND NOT has_table_privilege('authenticated', 'public.sii_envios', 'DELETE'),
    'tenant envio policy is SELECT-only and writes are revoked'
);

SELECT ok(
    (SELECT pol.polcmd = '*' FROM pg_policy pol
     WHERE pol.polrelid = 'public.sii_certificates'::regclass
       AND pol.polname = 'sii_certificates_backend')
    AND has_table_privilege('documentary_backend', 'public.sii_certificates', 'INSERT')
    AND has_table_privilege('documentary_backend', 'public.sii_certificates', 'UPDATE')
    AND NOT has_table_privilege('documentary_backend', 'public.sii_certificates', 'DELETE'),
    'backend may install or retire certificates but never delete evidence'
);
SELECT ok(
    (SELECT pol.polcmd = '*' FROM pg_policy pol
     WHERE pol.polrelid = 'public.sii_envios'::regclass
       AND pol.polname = 'sii_envios_backend')
    AND has_table_privilege('documentary_backend', 'public.sii_envios', 'INSERT')
    AND has_table_privilege('documentary_backend', 'public.sii_envios', 'UPDATE')
    AND NOT has_table_privilege('documentary_backend', 'public.sii_envios', 'DELETE'),
    'backend may seal an envio and advance its status but never delete it'
);
SELECT has_index(
    'public', 'sii_envios', 'idx_sii_envios_project',
    'envio lookups index the project'
);

-- KEK ciphertexts are never tenant-visible: a member client must not be able
-- to exfiltrate wrapped signing material for offline attacks.
SELECT ok(
    NOT has_column_privilege('authenticated', 'public.sii_certificates', 'pfx_wrapped', 'SELECT')
    AND NOT has_column_privilege('authenticated', 'public.sii_certificates', 'password_wrapped', 'SELECT'),
    'tenant read never reaches wrapped certificate material'
);
SELECT ok(
    has_column_privilege('authenticated', 'public.sii_certificates', 'subject', 'SELECT')
    AND has_column_privilege('documentary_backend', 'public.sii_certificates', 'pfx_wrapped', 'SELECT'),
    'metadata stays tenant-readable and the backend keeps the wrapped material'
);

SELECT * FROM finish();
ROLLBACK;
