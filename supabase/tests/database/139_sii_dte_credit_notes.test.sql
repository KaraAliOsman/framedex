BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(5);

SELECT has_column('public', 'project_dtes', 'credit_note_id', 'project_dtes gains credit_note_id');
SELECT col_type_is('public', 'project_dtes', 'credit_note_id', 'uuid', 'credit_note_id is uuid');
SELECT col_is_fk('public', 'project_dtes', 'credit_note_id', 'credit_note_id references project_credit_notes');
SELECT col_is_unique(
    'public', 'project_dtes', ARRAY['org_id', 'credit_note_id'],
    'uk_org_dte_credit_note enforces one DTE per credit note'
);
SELECT has_index(
    'public', 'project_dtes', 'uk_org_invoice_dte',
    'invoice uniqueness survives only for parent DTEs'
);

SELECT * FROM finish();
ROLLBACK;
