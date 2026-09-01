BEGIN;

CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;
SET LOCAL search_path = public, extensions;

SELECT plan(15);

INSERT INTO public.tenancy_organizations (id, name, tax_id)
VALUES
    ('11111111-1111-4111-8111-111111111111', 'Tenant A', 'A-1'),
    ('22222222-2222-4222-8222-222222222222', 'Tenant B', 'B-1');

INSERT INTO public.tenancy_memberships (org_id, user_id, role)
VALUES
    (
        '11111111-1111-4111-8111-111111111111',
        'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
        'OWNER'
    ),
    (
        '22222222-2222-4222-8222-222222222222',
        'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
        'OWNER'
    );

SELECT is(
    (
        SELECT count(*)
        FROM public.profile_systems
        WHERE code = 'DEMO_60'
          AND org_id IS NULL
          AND is_global = TRUE
          AND depth_mm = 60.00
          AND glass_clearance_white_mm = 5.00
          AND central_overlap_mm = 35.00
    ),
    1::BIGINT,
    'DEMO_60 seed has the canonical system parameters'
);
SELECT is(
    (SELECT count(*) FROM public.profile_articles WHERE system_id = (
        SELECT id FROM public.profile_systems WHERE code = 'DEMO_60'
    )),
    7::BIGINT,
    'DEMO_60 contains seven canonical profile articles'
);
SELECT is(
    (SELECT count(*) FROM public.glazing_bead_matrix WHERE system_id = (
        SELECT id FROM public.profile_systems WHERE code = 'DEMO_60'
    )),
    5::BIGINT,
    'DEMO_60 contains five canonical glazing mappings'
);

SET LOCAL ROLE authenticated;
SELECT set_config(
    'request.jwt.claims',
    '{"sub":"aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa","role":"authenticated"}',
    TRUE
);
SELECT set_config(
    'request.jwt.claim.sub',
    'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    TRUE
);

SELECT is((SELECT count(*) FROM public.profile_systems), 1::BIGINT, 'tenant A sees DEMO_60');
SELECT is((SELECT count(*) FROM public.profile_articles), 7::BIGINT, 'tenant A sees profiles');
SELECT is((SELECT count(*) FROM public.hardware_kits), 3::BIGINT, 'tenant A sees hardware');
SELECT is((SELECT count(*) FROM public.glazing_bead_matrix), 5::BIGINT, 'tenant A sees beads');

RESET ROLE;
SET LOCAL ROLE authenticated;
SELECT set_config(
    'request.jwt.claims',
    '{"sub":"bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb","role":"authenticated"}',
    TRUE
);
SELECT set_config(
    'request.jwt.claim.sub',
    'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
    TRUE
);

SELECT is((SELECT count(*) FROM public.profile_systems), 1::BIGINT, 'tenant B sees DEMO_60');
SELECT is((SELECT count(*) FROM public.profile_articles), 7::BIGINT, 'tenant B sees profiles');
SELECT is((SELECT count(*) FROM public.hardware_kits), 3::BIGINT, 'tenant B sees hardware');
SELECT is((SELECT count(*) FROM public.glazing_bead_matrix), 5::BIGINT, 'tenant B sees beads');

RESET ROLE;
SET LOCAL ROLE anon;
SELECT set_config('request.jwt.claims', '{}', TRUE);
SELECT set_config('request.jwt.claim.sub', '', TRUE);

SELECT is((SELECT count(*) FROM public.profile_systems), 0::BIGINT, 'anonymous sees no systems');
SELECT is((SELECT count(*) FROM public.profile_articles), 0::BIGINT, 'anonymous sees no profiles');
SELECT is((SELECT count(*) FROM public.hardware_kits), 0::BIGINT, 'anonymous sees no hardware');
SELECT is((SELECT count(*) FROM public.glazing_bead_matrix), 0::BIGINT, 'anonymous sees no beads');

RESET ROLE;
SELECT * FROM finish();
ROLLBACK;
