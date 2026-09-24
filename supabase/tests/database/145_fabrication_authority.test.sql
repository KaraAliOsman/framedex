BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(18);

-- §2 fabrication authority: rebate/end-milling are real catalog columns and
-- provenance marks who authored every technical row.

SELECT col_is_null('public', 'profile_systems', 'rebate_depth_mm',
    'rebate_depth_mm is nullable — NULL means UNKNOWN, not a default');
SELECT col_is_null('public', 'profile_systems', 'end_milling_overlap_mm',
    'end_milling_overlap_mm is nullable — NULL means UNKNOWN, not a default');
SELECT col_hasnt_default('public', 'profile_systems', 'rebate_depth_mm',
    'no fabricated rebate default');
SELECT col_hasnt_default('public', 'profile_systems', 'end_milling_overlap_mm',
    'no fabricated end-milling default');

SELECT col_not_null('public', 'profile_articles', 'data_provenance',
    'every article row declares an author');
SELECT col_not_null('public', 'profile_systems', 'data_provenance',
    'every system row declares an author');
SELECT col_not_null('public', 'infill_articles', 'data_provenance',
    'every infill row declares an author');
SELECT col_not_null('public', 'hardware_kits', 'data_provenance',
    'every kit row declares an author');

-- The enum rejects unknown provenance labels.
INSERT INTO public.profile_systems
SELECT (jsonb_populate_record(NULL::public.profile_systems, to_jsonb(source) ||
    jsonb_build_object('id', gen_random_uuid(), 'code', 'PGTAP145',
        'technical_locked', false, 'is_demo', false))).*
FROM public.profile_systems source WHERE code = 'DEMO_60';

PREPARE bad_prov AS
    UPDATE public.profile_systems SET data_provenance = 'AUTOMAGIC'
    WHERE code = 'PGTAP145';
SELECT throws_ok('bad_prov', '23514', NULL,
    'an invented provenance label is rejected');

PREPARE good_review AS
    UPDATE public.profile_systems
    SET technical_reviewed_at = now(),
        technical_reviewed_by = uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/test/reviewer')
    WHERE code = 'PGTAP145';
SELECT lives_ok('good_review', 'a human review can be recorded');

-- Locked catalogs are the population review exists for: audit-metadata writes
-- pass, but a technical edit stays frozen authority.
UPDATE public.profile_systems SET technical_locked = TRUE WHERE code = 'PGTAP145';

PREPARE locked_review AS
    UPDATE public.profile_systems
    SET technical_reviewed_at = now(), data_provenance = 'MANUAL'
    WHERE code = 'PGTAP145';
SELECT lives_ok('locked_review',
    'a locked system still accepts provenance/review stamps');

PREPARE locked_technical AS
    UPDATE public.profile_systems SET depth_mm = depth_mm + 1
    WHERE code = 'PGTAP145';
SELECT throws_ok('locked_technical', '23514', 'catalog_authority_referenced',
    'a locked system still refuses technical edits');

-- review_pending marks a stale review — cleared by review writes, set by
-- the app on technical edits of reviewed rows. Column present + NOT NULL on
-- every provenance table, and it rides the freeze-guard exemption.
SELECT col_not_null('public', 'profile_systems', 'review_pending',
    'systems track a stale-review marker');
SELECT col_not_null('public', 'profile_articles', 'review_pending',
    'articles track a stale-review marker');
SELECT col_not_null('public', 'infill_articles', 'review_pending',
    'infill rows track a stale-review marker');
SELECT col_not_null('public', 'hardware_kits', 'review_pending',
    'kits track a stale-review marker');

PREPARE locked_review_clear AS
    UPDATE public.profile_systems
    SET technical_reviewed_at = now(), technical_reviewed_by = NULL,
        review_pending = FALSE
    WHERE code = 'PGTAP145';
SELECT lives_ok('locked_review_clear',
    'a locked system accepts a review write that clears the pending marker');

SELECT ok((SELECT data_provenance FROM public.profile_systems
           WHERE code = 'DEMO_60' AND is_global LIMIT 1)
          IN ('SEED_SYNTHETIC', 'LEGACY_UNVERIFIED', 'MANUAL', 'IMPORT'),
    'DEMO_60 carries a declared provenance, never an unlabeled row');

SELECT * FROM finish();
ROLLBACK;
