BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(2);

SELECT has_column(
    'public', 'project_payment_links', 'deal_total',
    'link freezes the deal total it was created under'
);
SELECT has_column(
    'public', 'project_payment_links', 'deal_currency',
    'link freezes the deal currency it was created under'
);

SELECT * FROM finish();
ROLLBACK;
