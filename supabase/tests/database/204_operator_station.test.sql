BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path=public,private,auth,extensions,pg_temp;
SELECT plan(12);
SELECT has_table('public','production_operator_stations','station is persisted');
SELECT col_is_pk('public','production_operator_stations',ARRAY['org_id','user_id'],'choice belongs to one user and tenant');
SELECT ok((SELECT relrowsecurity FROM pg_class WHERE oid='public.production_operator_stations'::regclass),'station keeps RLS');
SELECT ok(NOT has_table_privilege('anon','public.production_operator_stations','SELECT'),'anonymous cannot read a workstation');
SELECT ok(NOT has_table_privilege('authenticated','public.production_operator_stations','DELETE'),'station selection does not erase history');
SELECT has_index('public','orders','orders_qc_remake_operation_uq','QC operation retries cannot duplicate remakes');
INSERT INTO tenancy_organizations(id,name,tax_id) VALUES
('12000000-0000-4000-8000-000000000001','P12 A DEMO','P12-A'),
('12000000-0000-4000-8000-000000000002','P12 B DEMO','P12-B');
INSERT INTO auth.users(id) VALUES
('12000000-0000-4000-8000-000000000003'),('12000000-0000-4000-8000-000000000004');
INSERT INTO tenancy_memberships(org_id,user_id,role) VALUES
('12000000-0000-4000-8000-000000000001','12000000-0000-4000-8000-000000000003','OPERATOR'),
('12000000-0000-4000-8000-000000000001','12000000-0000-4000-8000-000000000004','OPERATOR');
SET LOCAL ROLE authenticated;
SELECT set_config('request.jwt.claim.sub','12000000-0000-4000-8000-000000000003',true);
SELECT lives_ok($$INSERT INTO production_operator_stations(org_id,user_id,station_code)
 VALUES('12000000-0000-4000-8000-000000000001','12000000-0000-4000-8000-000000000003','CUT')$$,'operator chooses own station');
SELECT throws_ok($$INSERT INTO production_operator_stations(org_id,user_id,station_code)
 VALUES('12000000-0000-4000-8000-000000000001','12000000-0000-4000-8000-000000000004','QC')$$,'42501',NULL,'cannot choose another operator station');
SELECT throws_ok($$INSERT INTO production_operator_stations(org_id,user_id,station_code)
 VALUES('12000000-0000-4000-8000-000000000002','12000000-0000-4000-8000-000000000003','CUT')$$,'42501',NULL,'cannot cross tenant');
SELECT is((SELECT count(*) FROM production_operator_stations),1::bigint,'only own workstation is visible');
SELECT set_config('request.jwt.claim.sub','12000000-0000-4000-8000-000000000004',true);
SELECT is((SELECT count(*) FROM production_operator_stations),0::bigint,'colleague cannot read the preference');
RESET ROLE;
SELECT throws_ok($$UPDATE production_operator_stations SET station_code='UNDECLARED'$$,'23514',NULL,'unknown station remains rejected');
SELECT * FROM finish();
ROLLBACK;
