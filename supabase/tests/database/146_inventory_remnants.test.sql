BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(13);

SELECT has_table('public', 'inventory_remnants', 'remnant ledger table exists');
SELECT ok(
    EXISTS (
        SELECT 1
        FROM pg_tables
        WHERE schemaname = 'public'
          AND tablename = 'inventory_remnants'
          AND rowsecurity = true
    ),
    'remnant ledger enforces row level security'
);
SELECT ok(
    EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'inventory_remnants'
          AND policyname = 'inventory_remnants_isolation' AND cmd = 'ALL'
    ),
    'org isolation policy covers all commands'
);
SELECT ok(
    EXISTS (
        SELECT 1
        FROM pg_class c JOIN pg_namespace n ON c.relnamespace = n.oid
        WHERE n.nspname = 'public' AND c.relname = 'inventory_remnants'
          AND NOT has_table_privilege('authenticated', c.oid, 'INSERT')
          AND NOT has_table_privilege('authenticated', c.oid, 'UPDATE')
          AND NOT has_table_privilege('authenticated', c.oid, 'DELETE')
          AND has_table_privilege('authenticated', c.oid, 'SELECT')
    ),
    'authenticated reads remnants but can never write them directly'
);
SELECT ok(
    has_table_privilege('documentary_backend', 'public.inventory_remnants', 'INSERT')
    AND has_table_privilege('documentary_backend', 'public.inventory_remnants', 'UPDATE')
    AND NOT has_table_privilege('documentary_backend', 'public.inventory_remnants', 'DELETE'),
    'documentary role writes but never deletes remnant rows'
);
SELECT ok(
    EXISTS (
        SELECT 1
        FROM pg_constraint c JOIN pg_class t ON c.conrelid = t.oid
        JOIN pg_namespace n ON t.relnamespace = n.oid
        WHERE n.nspname = 'public' AND t.relname = 'production_step_events'
          AND c.conname = 'production_step_events_event_check'
          AND pg_get_constraintdef(c.oid) LIKE '%WO_REMNANTS_SETTLED%'
    ),
    'step events accept the remnant settle event'
);

-- Shape constraint: BAR rows carry a length + authority; SHEET rows carry
-- width/height + the workshop sku they were nested under — never mixed.
-- Privileged writes bypass RLS, so dimensional errors surface as 23514.
SET LOCAL ROLE service_role;
INSERT INTO public.tenancy_organizations (name, tax_id)
    VALUES ('Remnant Test Org', '76123456-7') RETURNING id \gset remnant_
SELECT throws_ok(
    format(
        $fmt$INSERT INTO public.inventory_remnants(
            org_id, kind, length_mm, width_mm, height_mm, stock_authority_id)
          VALUES (%L, 'BAR', 700, 100, 100, gen_random_uuid())$fmt$,
        :'remnant_id'
    ),
    '23514',
    NULL,
    'a BAR row with sheet dimensions violates the shape check'
);
SELECT throws_ok(
    format(
        $fmt$INSERT INTO public.inventory_remnants(
            org_id, kind, width_mm, height_mm, stock_authority_id, sheet_workshop_sku)
          VALUES (%L, 'SHEET', 800, 600, gen_random_uuid(), 'GLASS-4')$fmt$,
        :'remnant_id'
    ),
    '23514',
    NULL,
    'a SHEET row cannot carry a bar stock authority'
);
SELECT throws_ok(
    format(
        $fmt$INSERT INTO public.inventory_remnants(
            org_id, kind, length_mm, stock_authority_id)
          VALUES (%L, 'BAR', -10, gen_random_uuid())$fmt$,
        :'remnant_id'
    ),
    '23514',
    NULL,
    'non-positive remnant length is refused'
);
SELECT lives_ok(
    format(
        $fmt$INSERT INTO public.inventory_remnants(
            org_id, kind, length_mm, stock_authority_id, status, origin)
          VALUES (%L, 'BAR', 700, gen_random_uuid(), 'AVAILABLE', 'MANUAL')$fmt$,
        :'remnant_id'
    ),
    'a well-formed BAR remnant inserts'
);
SELECT lives_ok(
    format(
        $fmt$INSERT INTO public.inventory_remnants(
            org_id, kind, width_mm, height_mm, sheet_workshop_sku, status, origin)
          VALUES (%L, 'SHEET', 900, 500, 'GLASS-4', 'AVAILABLE', 'PRODUCTION')$fmt$,
        :'remnant_id'
    ),
    'a well-formed SHEET remnant inserts'
);
SELECT is(
    (
        SELECT count(*)::int FROM public.inventory_remnants
        WHERE org_id = :'remnant_id'
          AND status = 'AVAILABLE'
    ),
    2,
    'both remnant kinds land AVAILABLE in the pool'
);
SELECT throws_ok(
    format(
        $fmt$INSERT INTO public.inventory_remnants(
            org_id, kind, length_mm, stock_authority_id, status)
          VALUES (%L, 'BAR', 700, gen_random_uuid(), 'RETURNED')$fmt$,
        :'remnant_id'
    ),
    '23514',
    NULL,
    'an unknown lifecycle status is refused'
);

SELECT * FROM finish();
ROLLBACK;
