BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;
SET LOCAL search_path=public,extensions;
SELECT plan(20);
SELECT ok(relrowsecurity,relname||' has RLS') FROM pg_class
 WHERE relnamespace='public'::regnamespace AND relname IN
 ('pricing_configurations','pricing_matrix_cells','pricing_fx_snapshots','pricing_operations') ORDER BY relname;
INSERT INTO tenancy_organizations(id,name,tax_id) VALUES
 ('88000000-0000-4000-8000-000000000001','Pricing A','SHOT08-A'),
 ('88000000-0000-4000-8000-000000000002','Pricing B','SHOT08-B');
INSERT INTO tenancy_memberships(org_id,user_id,role) VALUES
 ('88000000-0000-4000-8000-000000000001','88100000-0000-4000-8000-000000000001','OWNER'),
 ('88000000-0000-4000-8000-000000000001','88100000-0000-4000-8000-000000000002','ESTIMATOR'),
 ('88000000-0000-4000-8000-000000000001','88100000-0000-4000-8000-000000000003','WORKSHOP_MANAGER'),
 ('88000000-0000-4000-8000-000000000001','88100000-0000-4000-8000-000000000004','INSTALLER');
INSERT INTO cost_lists(id,org_id,supplier_name,valid_from) VALUES
 ('88200000-0000-4000-8000-000000000001','88000000-0000-4000-8000-000000000001','A','2026-09-10'),
 ('88200000-0000-4000-8000-000000000002','88000000-0000-4000-8000-000000000002','B','2026-09-10');
SELECT set_config('request.jwt.claims','{"sub":"88100000-0000-4000-8000-000000000001","role":"authenticated","aal":"aal2"}',true);
SELECT set_config('app.pricing_reason','SQL test explicit edit',true);
SET LOCAL ROLE authenticated;
SELECT is((SELECT count(*) FROM cost_lists),1::bigint,'owner sees own costs only');
INSERT INTO cost_list_items(id,org_id,cost_list_id,sku,item_type,unit,unit_cost) VALUES
 ('88300000-0000-4000-8000-000000000001','88000000-0000-4000-8000-000000000001',
  '88200000-0000-4000-8000-000000000001','A','PROFILE','M',1.2345);
UPDATE cost_list_items SET unit_cost=1.2346 WHERE id='88300000-0000-4000-8000-000000000001';
SELECT is((SELECT old_value FROM price_audit_logs WHERE entity_id='88300000-0000-4000-8000-000000000001' AND field='UPDATE'),1.2345::numeric,'old cost has four decimals');
SELECT is((SELECT new_value FROM price_audit_logs WHERE entity_id='88300000-0000-4000-8000-000000000001' AND field='UPDATE'),1.2346::numeric,'new cost has four decimals');
SELECT is((SELECT actor_user_id FROM price_audit_logs WHERE entity_id='88300000-0000-4000-8000-000000000001' AND field='UPDATE'),'88100000-0000-4000-8000-000000000001'::uuid,'verified actor recorded');
SELECT throws_ok($$UPDATE price_audit_logs SET reason='tampered'$$,'42501',NULL,'audit update forbidden');
SELECT throws_ok($$DELETE FROM price_audit_logs$$,'42501',NULL,'audit deletion forbidden');
SELECT throws_ok($$INSERT INTO cost_list_items(org_id,cost_list_id,sku,item_type,unit,unit_cost) VALUES('88000000-0000-4000-8000-000000000001','88200000-0000-4000-8000-000000000002','X','PROFILE','M',1)$$,'23503',NULL,'parent tenant must match');
SELECT set_config('app.pricing_reason','',true);
SELECT throws_ok($$UPDATE cost_list_items SET unit_cost=99 WHERE sku='A'$$,'23514',NULL,'audit failure rejects write');
SELECT is((SELECT unit_cost FROM cost_list_items WHERE sku='A'),1.2346::numeric,'failed audit leaves price intact');
SELECT set_config('request.jwt.claims','{"sub":"88100000-0000-4000-8000-000000000002","role":"authenticated"}',true);
SELECT is((SELECT count(*) FROM cost_list_items),0::bigint,'estimator cannot read raw cost');
SELECT is((SELECT count(*) FROM price_audit_logs),0::bigint,'estimator cannot read cost through audit');
SELECT ok(NOT pg_has_role('authenticated','pricing_backend','MEMBER'),'public role has no membership in backend calculator');
SELECT set_config('request.jwt.claims','{"sub":"88100000-0000-4000-8000-000000000003","role":"authenticated"}',true);
SELECT is((SELECT count(*) FROM cost_list_items),1::bigint,'manager reads required cost');
WITH changed AS (UPDATE cost_list_items SET unit_cost=9 WHERE sku='A' RETURNING id)
SELECT is((SELECT count(*) FROM changed),0::bigint,'manager cannot edit costs');
SELECT set_config('request.jwt.claims','{"sub":"88100000-0000-4000-8000-000000000004","role":"authenticated"}',true);
SELECT is((SELECT count(*) FROM cost_list_items),0::bigint,'installer cannot read costs');
RESET ROLE;
SELECT ok(NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='pricing_backend' AND (rolsuper OR rolbypassrls OR rolcanlogin)),'calculator role has no login or RLS bypass');
SELECT * FROM finish();
ROLLBACK;
