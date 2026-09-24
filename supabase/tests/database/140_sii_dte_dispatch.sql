BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(6);

SELECT has_column('public', 'project_dtes', 'dispatch_note_id', 'project_dtes gains dispatch_note_id');
SELECT col_type_is('public', 'project_dtes', 'dispatch_note_id', 'uuid', 'dispatch_note_id is uuid');
SELECT col_is_fk('public', 'project_dtes', 'dispatch_note_id', 'dispatch_note_id references dispatch_notes');
SELECT col_is_null(
    'public', 'project_dtes', 'invoice_id',
    'invoice_id relaxes for non-invoice DTE families'
);
SELECT col_is_unique(
    'public', 'project_dtes', ARRAY['org_id', 'dispatch_note_id'],
    'uk_org_dispatch_note_dte enforces one DTE per dispatch note'
);
SELECT has_check(
    'public', 'project_dtes',
    'dispatch-note DTE family is isolated from invoice chains'
);

SELECT * FROM finish();
ROLLBACK;
