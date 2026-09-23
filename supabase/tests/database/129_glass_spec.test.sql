BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(2);

SELECT has_column(
    'public', 'glass_purchase_mappings', 'glass_spec',
    'glass_spec column exists — the mapping owns the composition'
);
SELECT col_type_is(
    'public', 'glass_purchase_mappings', 'glass_spec', 'character varying(200)',
    'glass_spec is varchar(200)'
);

SELECT * FROM finish();
ROLLBACK;
