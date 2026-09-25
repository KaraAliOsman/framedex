BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(12);

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

SELECT * FROM finish();
ROLLBACK;
