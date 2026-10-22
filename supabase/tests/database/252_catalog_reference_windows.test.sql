BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
GRANT USAGE ON SCHEMA extensions TO catalog_backend;
SET LOCAL search_path=public,private,auth,extensions,pg_temp;
SELECT plan(23);
SELECT has_table('public','catalog_reference_windows','tenant reference windows exist');
SELECT col_not_null('public','catalog_reference_windows','org_id','reference always has tenant');
SELECT col_not_null('public','catalog_reference_windows','verified_by','reference always has human actor');
SELECT col_type_is('public','catalog_reference_windows','expected_output','jsonb','canonical exact strings stay JSONB');
SELECT ok((SELECT relrowsecurity FROM pg_class WHERE oid='public.catalog_reference_windows'::regclass),'reference RLS enabled');
SELECT ok(NOT has_table_privilege('authenticated','public.catalog_reference_windows','INSERT'),'member cannot forge engine evidence');
SELECT ok(NOT has_table_privilege('catalog_backend','public.catalog_reference_windows','UPDATE'),'backend cannot rewrite reference');
SELECT ok(NOT has_table_privilege('catalog_backend','public.catalog_reference_windows','DELETE'),'backend cannot delete reference');

INSERT INTO public.tenancy_organizations(id,name,tax_id) VALUES
    ('25200000-0000-4000-8000-000000000001','Reference A','REFERENCE-A'),
    ('25200000-0000-4000-8000-000000000002','Reference B','REFERENCE-B');
INSERT INTO public.tenancy_memberships(org_id,user_id,role) VALUES
    ('25200000-0000-4000-8000-000000000001','25200000-0000-4000-8000-000000000003','OWNER'),
    ('25200000-0000-4000-8000-000000000002','25200000-0000-4000-8000-000000000004','OWNER');
INSERT INTO public.profile_systems(id,org_id,name,code,depth_mm,system_family,door_leaf_side_clearance_mm)
    VALUES('25200000-0000-4000-8000-000000000005','25200000-0000-4000-8000-000000000001',
        'Reference series','REFERENCE-60',60,'CASEMENT',0);
SET LOCAL ROLE catalog_backend;
SELECT set_config('request.jwt.claims','{"sub":"25200000-0000-4000-8000-000000000003","role":"authenticated","aal":"aal2"}',TRUE);
SELECT set_config('request.jwt.claim.sub','25200000-0000-4000-8000-000000000003',TRUE);
SELECT lives_ok($$INSERT INTO public.catalog_reference_windows(id,org_id,system_id,input,expected_output,technical_hash,verified_by) VALUES
    ('25200000-0000-4000-8000-000000000006','25200000-0000-4000-8000-000000000001',
     '25200000-0000-4000-8000-000000000005','{"nominal_width_mm":"1200.01"}','{"length_mm":"1206.01"}',
     'sha256:'||repeat('a',64),'25200000-0000-4000-8000-000000000003')$$,'owner can seal a window');
SELECT is((SELECT expected_output->>'length_mm' FROM public.catalog_reference_windows),'1206.01','exact output retains precision');
SELECT throws_ok($$INSERT INTO public.catalog_reference_windows(org_id,system_id,input,expected_output,technical_hash,verified_by) VALUES
    ('25200000-0000-4000-8000-000000000001','25200000-0000-4000-8000-000000000005','{}','{}',
     'sha256:'||repeat('a',64),'25200000-0000-4000-8000-000000000004')$$,'42501',NULL,'actor must match verified identity');
SELECT throws_ok($$INSERT INTO public.catalog_reference_windows(org_id,system_id,input,expected_output,technical_hash,verified_by) VALUES
    ('25200000-0000-4000-8000-000000000002','25200000-0000-4000-8000-000000000005','{}','{}',
     'sha256:'||repeat('a',64),'25200000-0000-4000-8000-000000000003')$$,'23514',NULL,'reference cannot link a foreign series');
SELECT lives_ok($$INSERT INTO public.catalog_series_setup(system_id,org_id,wizard_step,wizard_state) VALUES
    ('25200000-0000-4000-8000-000000000005','25200000-0000-4000-8000-000000000001',4,'{"trial":{"nominal_width_mm":"1200.01"}}')$$,'setup progress is persisted');
SELECT is((SELECT wizard_step::integer FROM public.catalog_series_setup WHERE system_id='25200000-0000-4000-8000-000000000005'),4,'setup can resume step four');
SELECT throws_ok($$UPDATE public.catalog_series_setup SET wizard_step=6 WHERE system_id='25200000-0000-4000-8000-000000000005'$$,'23514',NULL,'unknown wizard steps rejected');
SELECT throws_ok($$UPDATE public.catalog_series_setup SET wizard_state='[]' WHERE system_id='25200000-0000-4000-8000-000000000005'$$,'23514',NULL,'state must be an object');
SELECT throws_ok($$UPDATE public.catalog_series_setup SET wizard_state=jsonb_build_object('large',repeat('x',65537)) WHERE system_id='25200000-0000-4000-8000-000000000005'$$,'23514',NULL,'oversized drafts rejected');

SET LOCAL ROLE authenticated;
SELECT set_config('request.jwt.claims','{"sub":"25200000-0000-4000-8000-000000000004","role":"authenticated","aal":"aal2"}',TRUE);
SELECT set_config('request.jwt.claim.sub','25200000-0000-4000-8000-000000000004',TRUE);
SELECT is((SELECT count(*)::integer FROM public.catalog_reference_windows),0,'foreign tenant cannot read reference');
SELECT is((SELECT count(*)::integer FROM public.catalog_series_setup),0,'foreign tenant cannot read progress');
RESET ROLE;
SELECT throws_ok($$UPDATE public.catalog_reference_windows SET expected_output='{}'$$,'42501',NULL,'even privileged writes cannot rewrite expected output');
SELECT throws_ok($$DELETE FROM public.catalog_reference_windows$$,'42501',NULL,'reference cannot be deleted');
SELECT throws_ok($$TRUNCATE public.catalog_reference_windows$$,'42501',NULL,'reference cannot be truncated');
SELECT throws_ok($$DELETE FROM public.profile_systems WHERE id='25200000-0000-4000-8000-000000000005'$$,'23503',NULL,'deleting a series cannot erase its reference');
SELECT * FROM finish();
ROLLBACK;
