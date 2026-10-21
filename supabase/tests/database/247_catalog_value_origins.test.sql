BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
-- Test-only access to pgTAP; rolled back with the fixture transaction.
GRANT USAGE ON SCHEMA extensions TO catalog_backend;
SET LOCAL search_path=public,private,auth,extensions,pg_temp;
SELECT plan(24);
SELECT has_table('public','catalog_value_history','cell history exists');
SELECT has_table('public','catalog_series_setup','series verification exists');
SELECT col_type_is('public','catalog_value_history','value_numeric','numeric','numbers remain NUMERIC');
SELECT col_not_null('public','catalog_value_history','org_id','every history row has tenant');
SELECT col_not_null('public','catalog_series_setup','org_id','every verification has tenant');
SELECT ok((SELECT relrowsecurity FROM pg_class WHERE oid='public.catalog_value_history'::regclass),'history RLS enabled');
SELECT ok((SELECT relrowsecurity FROM pg_class WHERE oid='public.catalog_series_setup'::regclass),'verification RLS enabled');
SELECT ok(NOT has_table_privilege('authenticated','public.catalog_value_history','INSERT'),'member cannot forge origin');
SELECT ok(NOT has_table_privilege('authenticated','public.catalog_series_setup','UPDATE'),'member cannot stamp verification');
SELECT ok(NOT has_table_privilege('catalog_backend','public.catalog_value_history','UPDATE'),'backend cannot rewrite history');
SELECT ok(NOT has_table_privilege('catalog_backend','public.catalog_value_history','DELETE'),'backend cannot delete history');

INSERT INTO public.tenancy_organizations(id,name,tax_id) VALUES
    ('24700000-0000-4000-8000-000000000001','Origins A','ORIGIN-A'),
    ('24700000-0000-4000-8000-000000000002','Origins B','ORIGIN-B');
INSERT INTO public.tenancy_memberships(org_id,user_id,role) VALUES
    ('24700000-0000-4000-8000-000000000001','24700000-0000-4000-8000-000000000003','OWNER'),
    ('24700000-0000-4000-8000-000000000002','24700000-0000-4000-8000-000000000004','OWNER');
INSERT INTO public.profile_systems(id,org_id,name,code,depth_mm,system_family,door_leaf_side_clearance_mm)
    VALUES('24700000-0000-4000-8000-000000000005','24700000-0000-4000-8000-000000000001',
        'History series','ORIGIN-60',60,'CASEMENT',0);
SET LOCAL ROLE catalog_backend;
SELECT set_config('request.jwt.claims','{"sub":"24700000-0000-4000-8000-000000000003","role":"authenticated","aal":"aal2"}',TRUE);
SELECT set_config('request.jwt.claim.sub','24700000-0000-4000-8000-000000000003',TRUE);
SELECT lives_ok($$UPDATE public.profile_systems SET depth_mm=61
    WHERE id='24700000-0000-4000-8000-000000000005'$$,'existing writes record cell versions');
SELECT is((SELECT count(*)::int FROM public.catalog_value_history),1,'one changed cell recorded');
SELECT is((SELECT previous_numeric FROM public.catalog_value_history),60::numeric,'first change retains old exact value');
SELECT is((SELECT origin FROM public.catalog_value_history),'WORKSHOP','human edit is a workshop value');
SELECT lives_ok($$INSERT INTO public.catalog_series_setup(system_id,org_id) VALUES
    ('24700000-0000-4000-8000-000000000005','24700000-0000-4000-8000-000000000001')$$,'owner can prepare verification');

SET LOCAL ROLE authenticated;
SELECT set_config('request.jwt.claims','{"sub":"24700000-0000-4000-8000-000000000004","role":"authenticated","aal":"aal2"}',TRUE);
SELECT set_config('request.jwt.claim.sub','24700000-0000-4000-8000-000000000004',TRUE);
SELECT is((SELECT count(*)::int FROM public.catalog_value_history),0,'foreign tenant cannot read history');
SELECT is((SELECT count(*)::int FROM public.catalog_series_setup),0,'foreign tenant cannot read verification');
SET LOCAL ROLE catalog_backend;
SELECT throws_ok($$INSERT INTO public.catalog_series_setup(system_id,org_id) VALUES
    ('24700000-0000-4000-8000-000000000005','24700000-0000-4000-8000-000000000002')$$,
    '23514',NULL,'cross-tenant verification rejected');

RESET ROLE;
SELECT throws_ok($$UPDATE public.catalog_value_history SET source_ref='rewritten'$$,
    '42501',NULL,'even privileged writes cannot change history');
SELECT throws_ok($$DELETE FROM public.catalog_value_history$$,'42501',NULL,'history cannot be deleted');
SELECT throws_ok($$TRUNCATE public.catalog_value_history$$,'42501',NULL,'history cannot be truncated');
SELECT throws_ok($$INSERT INTO public.catalog_value_history(org_id,system_id,authority_table,row_id,
    field_name,value_numeric,origin,source_ref,set_by,version) VALUES(
    '24700000-0000-4000-8000-000000000001','24700000-0000-4000-8000-000000000005',
    'profile_systems','24700000-0000-4000-8000-000000000005','depth_mm',62,'WORKSHOP','Wrong value',
    '24700000-0000-4000-8000-000000000003',1)$$,'23514',NULL,'origin must match current exact value');
SELECT throws_ok($$INSERT INTO public.catalog_value_history(org_id,system_id,authority_table,row_id,
    field_name,value_numeric,origin,source_ref,set_by,version) VALUES(
    '24700000-0000-4000-8000-000000000001','24700000-0000-4000-8000-000000000005',
    'profile_systems','24700000-0000-4000-8000-000000000005','depth_mm',61,'MANUAL','Unreviewed manual',
    '24700000-0000-4000-8000-000000000003',1)$$,'23514',NULL,'manual origin needs reviewed matching evidence');
SELECT * FROM finish();
ROLLBACK;
