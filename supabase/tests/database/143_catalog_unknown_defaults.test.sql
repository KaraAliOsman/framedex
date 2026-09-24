BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(10);

-- Missing manufacturing data is UNKNOWN (NULL), never a fabricated default:
-- a supplier document that does not state stock length, weld loss, gap or
-- weight must keep that absence all the way to the row.

SELECT col_is_null('public', 'profile_articles', 'commercial_length_mm',
    'stock length is nullable');
SELECT col_is_null('public', 'profile_articles', 'welding_loss_mm',
    'welding loss is nullable');
SELECT col_is_null('public', 'profile_articles', 'reinforcement_gap_mm',
    'reinforcement gap is nullable');
SELECT col_is_null('public', 'profile_articles', 'weight_kg_m',
    'profile weight is nullable');
SELECT col_is_null('public', 'profile_articles', 'steel_weight_kg_m',
    'steel weight is nullable');

SELECT col_hasnt_default('public', 'profile_articles', 'commercial_length_mm',
    'no 6000mm fabrication survives');
SELECT col_hasnt_default('public', 'profile_articles', 'welding_loss_mm',
    'no 6mm fabrication survives');
SELECT col_hasnt_default('public', 'profile_articles', 'reinforcement_gap_mm',
    'no 15mm fabrication survives');
SELECT col_hasnt_default('public', 'profile_articles', 'weight_kg_m',
    'no 1.2 kg/m fabrication survives');

INSERT INTO public.profile_systems
SELECT (jsonb_populate_record(NULL::public.profile_systems,to_jsonb(source)||
    jsonb_build_object('id',gen_random_uuid(),'code','PGTAP143','technical_locked',false,'is_demo',false))).*
FROM public.profile_systems source WHERE code='DEMO_60';
INSERT INTO public.profile_articles (system_id, sku, name, role, material, face_width_mm)
SELECT id, 'UNKNOWN-TEST', 'unknown fabrication data', 'MULLION_V', 'PVC', '60.00'
FROM public.profile_systems WHERE code = 'PGTAP143';
SELECT is(
    (SELECT ROW(commercial_length_mm, welding_loss_mm, reinforcement_gap_mm,
                weight_kg_m, steel_weight_kg_m)::text
     FROM public.profile_articles WHERE sku = 'UNKNOWN-TEST'),
    ROW(NULL, NULL, NULL, NULL, NULL)::text,
    'omitted fabrication columns stay NULL — nothing was invented'
);

SELECT * FROM finish();
ROLLBACK;
