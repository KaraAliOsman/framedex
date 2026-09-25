BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(10);

SELECT has_table('public', 'document_imports', 'ingestion table exists');
SELECT has_column('public', 'document_imports', 'candidates', 'review candidates are stored');
SELECT has_column('public', 'document_imports', 'audit_id', 'vision usage links to the AI audit');
SELECT ok(
    EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.document_imports'::regclass
          AND pg_get_constraintdef(oid) LIKE '%EXTRACTING%REVIEW_READY%CONFIRMED%'
    ),
    'status enum covers the review lifecycle'
);
SELECT ok(
    EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'document_imports'
          AND policyname = 'document_imports_member_read'
    ),
    'tenant isolation policy exists'
);
SELECT ok(
    has_table_privilege('authenticated', 'public.document_imports', 'SELECT')
    AND NOT has_table_privilege('authenticated', 'public.document_imports', 'UPDATE'),
    'tenant role reads its imports but cannot rewrite candidates'
);
SELECT ok(
    has_table_privilege('documentary_backend', 'public.document_imports', 'INSERT')
    AND has_table_privilege('documentary_backend', 'public.document_imports', 'UPDATE'),
    'the backend role owns extraction writes'
);
SELECT ok(
    NOT has_table_privilege('anon', 'public.document_imports', 'SELECT'),
    'anonymous role sees nothing'
);
SELECT ok(
    EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.document_imports'::regclass
          AND contype = 'f'
          AND pg_get_constraintdef(oid) LIKE '%ai_audit_logs%'
    ),
    'audit_id references the immutable AI audit log'
);
SELECT ok(
    EXISTS (
        SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relname = 'document_imports' AND c.relrowsecurity
    ),
    'RLS is enabled'
);

SELECT * FROM finish();
ROLLBACK;
