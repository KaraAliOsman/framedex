BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(5);

-- §15 profile sections: optional, shape-checked, never fabricated.

SELECT col_is_null('public', 'profile_articles', 'section',
    'section is nullable — absence means approximate rendering');
SELECT col_type_is('public', 'profile_articles', 'section', 'jsonb',
    'section is a jsonb document');
SELECT col_hasnt_default('public', 'profile_articles', 'section',
    'no fabricated section default');

-- The check accepts a valid declared section and rejects degenerate shapes.
-- A cloned, unlocked system keeps this test independent of DEMO_60's lock
-- state and of the singleton-role guard's DEMO occupancy.
INSERT INTO public.profile_systems
SELECT (jsonb_populate_record(NULL::public.profile_systems, to_jsonb(source) ||
    jsonb_build_object('id', gen_random_uuid(), 'code', 'PGTAP144',
        'technical_locked', false, 'is_demo', false))).*
FROM public.profile_systems source WHERE code = 'DEMO_60';

PREPARE good AS
    INSERT INTO public.profile_articles
        (id, system_id, org_id, sku, name, role, material, face_width_mm, section)
    VALUES (
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/test/section-article'),
        (SELECT id FROM public.profile_systems WHERE code = 'PGTAP144' LIMIT 1),
        NULL, 'TEST-SECTION', 'Sección Test', 'ADDITIONAL', 'PVC', 10.00,
        '{"source":"POLYGON","polygon":[{"x_mm":0,"y_mm":0},{"x_mm":60,"y_mm":0},{"x_mm":60,"y_mm":60},{"x_mm":0,"y_mm":60}],"depth_mm":60,"axes":[{"name":"GLAZING","y_mm":40}]}'::jsonb
    );
SELECT lives_ok('good', 'a shaped section with >=3 points inserts');

PREPARE bad AS
    INSERT INTO public.profile_articles
        (id, system_id, org_id, sku, name, role, material, face_width_mm, section)
    VALUES (
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/test/section-bad'),
        (SELECT id FROM public.profile_systems WHERE code = 'PGTAP144' LIMIT 1),
        NULL, 'TEST-SECTION-BAD', 'Sección Mala', 'GLAZING_BEAD', 'PVC', 10.00,
        '{"source":"POLYGON","polygon":[{"x_mm":0,"y_mm":0},{"x_mm":1,"y_mm":0}],"depth_mm":60}'::jsonb
    );
SELECT throws_ok('bad', '23514', NULL, 'a polygon with fewer than 3 points is rejected');

SELECT * FROM finish();
ROLLBACK;
