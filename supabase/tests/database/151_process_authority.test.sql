BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(18);

-- Consolidation A: routing authority is a declared, versioned catalog row —
-- never inferred from the material family alone.

SELECT has_table('public', 'manufacturing_process_profiles',
    'process profiles exist');
SELECT col_is_pk('public', 'manufacturing_process_profiles', 'id',
    'profile has a primary key');
SELECT col_is_null('public', 'manufacturing_process_profiles', 'org_id',
    'org_id nullable — NULL rows are the shared global library');
SELECT has_column('public', 'manufacturing_process_profiles', 'version',
    'profiles are versioned');
SELECT has_column('public', 'manufacturing_process_profiles', 'stations',
    'ordered station template is declared');
SELECT has_column('public', 'manufacturing_process_profiles', 'operation_station_map',
    'operation→workstation map is declared');
SELECT has_column('public', 'profile_systems', 'process_profile_id',
    'systems can bind an explicit process profile');
SELECT col_is_fk('public', 'profile_systems', 'process_profile_id',
    'system binding references the authority table');

-- The global seeds declare the three real authorities plus an honest generic.
SELECT ok(
    (SELECT count(*) FROM public.manufacturing_process_profiles
      WHERE org_id IS NULL
        AND code IN ('PVC_WELDED', 'ALU_CRIMPED', 'FRAMELESS_GLASS', 'GENERIC_LEGACY')) = 4,
    'four global declared authorities exist'
);

-- Frameless must never inherit joining steps: its template contains no
-- WELD/CRIMP station codes at all.
SELECT ok(
    NOT EXISTS (
        SELECT 1
        FROM public.manufacturing_process_profiles p,
             jsonb_array_elements(p.stations) s
        WHERE p.code = 'FRAMELESS_GLASS' AND p.org_id IS NULL
          AND s->>'code' IN ('WELD', 'CRIMP')
    ),
    'FRAMELESS_GLASS declares no welding or crimping stations'
);

-- The authority table is readable by tenants (routing is public knowledge
-- inside the org), never writable through PostgREST.
SELECT ok(
    has_table_privilege('authenticated', 'public.manufacturing_process_profiles', 'SELECT'),
    'authenticated can read process profiles'
);
SELECT ok(
    NOT has_table_privilege('authenticated', 'public.manufacturing_process_profiles', 'INSERT'),
    'authenticated cannot author process profiles'
);

-- Review fix: org-owned profiles are tenant-private — RLS scopes member
-- reads to (own org ∪ global library), otherwise routing declarations leak
-- cross-tenant through PostgREST.
INSERT INTO public.tenancy_organizations (id, name, tax_id) VALUES
    ('33333333-3333-4333-8333-333333333333', 'Tenant C', 'C-1'),
    ('44444444-4444-4444-8444-444444444444', 'Tenant D', 'D-1');
INSERT INTO public.tenancy_memberships (org_id, user_id, role) VALUES
    ('33333333-3333-4333-8333-333333333333',
     'cccccccc-0000-4000-8000-000000000001', 'WORKSHOP_MANAGER');
INSERT INTO public.manufacturing_process_profiles
    (org_id, code, version, label, stations) VALUES
    ('33333333-3333-4333-8333-333333333333', 'TENANT_CUSTOM', 1, 'Perfil propio', '[]'::jsonb),
    ('44444444-4444-4444-8444-444444444444', 'OTHER_CUSTOM', 1, 'Perfil ajeno', '[]'::jsonb);

SET LOCAL ROLE authenticated;
SELECT set_config('request.jwt.claims',
    '{"sub":"cccccccc-0000-4000-8000-000000000001","role":"authenticated"}', TRUE);
SELECT set_config('request.jwt.claim.sub',
    'cccccccc-0000-4000-8000-000000000001', TRUE);

SELECT is(
    (SELECT relrowsecurity FROM pg_class
      WHERE oid = 'public.manufacturing_process_profiles'::regclass),
    TRUE,
    'RLS enabled on process profiles'
);
SELECT is(
    (SELECT count(*) FROM public.manufacturing_process_profiles
      WHERE code = 'TENANT_CUSTOM'),
    1::BIGINT,
    'member reads own org profile'
);
SELECT is(
    (SELECT count(*) FROM public.manufacturing_process_profiles
      WHERE code = 'OTHER_CUSTOM'),
    0::BIGINT,
    'member cannot read another tenant''s profile'
);

RESET ROLE;

-- Tenant-scope trigger: a system binds only a GLOBAL profile or one owned by
-- its own org — a foreign org's profile is never addressable by a bare FK.
SELECT throws_ok(
    $$INSERT INTO public.profile_systems (org_id, name, code, depth_mm, sliding_glazing_deduction_width_mm, sliding_glazing_deduction_height_mm, door_leaf_side_clearance_mm, process_profile_id)
      VALUES ('33333333-3333-4333-8333-333333333333', 'SysC', 'SYS-C', 70, 20, 20, 7,
              (SELECT id FROM public.manufacturing_process_profiles
                WHERE code='OTHER_CUSTOM'))$$,
    'process_profile_foreign_org',
    'a system cannot bind another org''s process profile'
);
SELECT lives_ok(
    $$INSERT INTO public.profile_systems (org_id, name, code, depth_mm, sliding_glazing_deduction_width_mm, sliding_glazing_deduction_height_mm, door_leaf_side_clearance_mm, process_profile_id)
      VALUES ('33333333-3333-4333-8333-333333333333', 'SysC2', 'SYS-C2', 70, 20, 20, 7,
              (SELECT id FROM public.manufacturing_process_profiles
                WHERE code='TENANT_CUSTOM'))$$,
    'a system binds its own org''s profile'
);
SELECT lives_ok(
    $$INSERT INTO public.profile_systems (org_id, name, code, depth_mm, sliding_glazing_deduction_width_mm, sliding_glazing_deduction_height_mm, door_leaf_side_clearance_mm, process_profile_id)
      VALUES ('33333333-3333-4333-8333-333333333333', 'SysC3', 'SYS-C3', 70, 20, 20, 7,
              (SELECT id FROM public.manufacturing_process_profiles
                WHERE code='PVC_WELDED' AND org_id IS NULL))$$,
    'a system binds a global profile'
);

SELECT * FROM finish();
ROLLBACK;
