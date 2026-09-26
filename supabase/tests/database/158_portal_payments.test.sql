BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(2);

SELECT ok(
    EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'project_payments'
          AND policyname = 'project_payments_portal_read'
          AND 'portal_backend' = ANY(roles)
    ),
    'portal_backend holds the org-scoped payment read policy'
);
SELECT ok(
    NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'project_payments'
          AND policyname = 'project_payments_portal_read'
          AND 'authenticated' = ANY(roles)
    ),
    'members do NOT gain the portal payment read'
);

SELECT * FROM finish();
ROLLBACK;
