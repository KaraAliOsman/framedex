BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;
SET LOCAL search_path=public,extensions;
SELECT plan(38);
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

-- Owner finding: NULL actor cannot bypass the commercial INSERT guard.
SELECT set_config('request.jwt.claims','{}',true);
SELECT set_config('request.jwt.claim.sub','',true);
SET LOCAL ROLE postgres;
SELECT lives_ok($$INSERT INTO projects(id,org_id,code,name,client_name,created_by) VALUES('88400000-0000-4000-8000-000000000001','88000000-0000-4000-8000-000000000001','ZERO-postgres','Zero draft','Fixture','88100000-0000-4000-8000-000000000001')$$,'postgres actor NULL may insert zero project');
SELECT lives_ok($$INSERT INTO project_positions(org_id,project_id,position_index,typology,system_id,width_mm,height_mm,parametric_tree,bom_snapshot) SELECT '88000000-0000-4000-8000-000000000001','88400000-0000-4000-8000-000000000001',1,'FIXED',id,1000,1000,'{}','{}' FROM profile_systems WHERE code='DEMO_60'$$,'postgres actor NULL may insert zero position');
SELECT throws_ok($$INSERT INTO projects(org_id,code,name,client_name,created_by,total_cost_net) VALUES('88000000-0000-4000-8000-000000000001','REJECT-postgres-total_cost_net','Rejected','Fixture','88100000-0000-4000-8000-000000000001',1)$$,'42501','pricing_service_required','postgres rejects nonzero total_cost_net INSERT');
SELECT throws_ok($$INSERT INTO projects(org_id,code,name,client_name,created_by,total_price_net) VALUES('88000000-0000-4000-8000-000000000001','REJECT-postgres-total_price_net','Rejected','Fixture','88100000-0000-4000-8000-000000000001',1)$$,'42501','pricing_service_required','postgres rejects nonzero total_price_net INSERT');
SELECT throws_ok($$INSERT INTO projects(org_id,code,name,client_name,created_by,total_price_tax) VALUES('88000000-0000-4000-8000-000000000001','REJECT-postgres-total_price_tax','Rejected','Fixture','88100000-0000-4000-8000-000000000001',1)$$,'42501','pricing_service_required','postgres rejects nonzero total_price_tax INSERT');
SELECT throws_ok($$INSERT INTO projects(org_id,code,name,client_name,created_by,total_price_gross) VALUES('88000000-0000-4000-8000-000000000001','REJECT-postgres-total_price_gross','Rejected','Fixture','88100000-0000-4000-8000-000000000001',1)$$,'42501','pricing_service_required','postgres rejects nonzero total_price_gross INSERT');
SELECT throws_ok($$INSERT INTO project_positions(org_id,project_id,position_index,typology,system_id,width_mm,height_mm,parametric_tree,bom_snapshot,cost_net) SELECT '88000000-0000-4000-8000-000000000001','88400000-0000-4000-8000-000000000001',2,'FIXED',id,1000,1000,'{}','{}',0.01 FROM profile_systems WHERE code='DEMO_60'$$,'42501','pricing_service_required','postgres rejects nonzero cost_net INSERT');
SELECT throws_ok($$INSERT INTO project_positions(org_id,project_id,position_index,typology,system_id,width_mm,height_mm,parametric_tree,bom_snapshot,price_net) SELECT '88000000-0000-4000-8000-000000000001','88400000-0000-4000-8000-000000000001',2,'FIXED',id,1000,1000,'{}','{}',0.01 FROM profile_systems WHERE code='DEMO_60'$$,'42501','pricing_service_required','postgres rejects nonzero price_net INSERT');
SELECT throws_ok($$INSERT INTO project_positions(org_id,project_id,position_index,typology,system_id,width_mm,height_mm,parametric_tree,bom_snapshot,discount_pct) SELECT '88000000-0000-4000-8000-000000000001','88400000-0000-4000-8000-000000000001',2,'FIXED',id,1000,1000,'{}','{}',0.01 FROM profile_systems WHERE code='DEMO_60'$$,'42501','pricing_service_required','postgres rejects nonzero discount_pct INSERT');
SET LOCAL ROLE service_role;
SELECT lives_ok($$INSERT INTO projects(id,org_id,code,name,client_name,created_by) VALUES('88400000-0000-4000-8000-000000000002','88000000-0000-4000-8000-000000000001','ZERO-service_role','Zero draft','Fixture','88100000-0000-4000-8000-000000000001')$$,'service_role actor NULL may insert zero project');
SELECT lives_ok($$INSERT INTO project_positions(org_id,project_id,position_index,typology,system_id,width_mm,height_mm,parametric_tree,bom_snapshot) SELECT '88000000-0000-4000-8000-000000000001','88400000-0000-4000-8000-000000000002',1,'FIXED',id,1000,1000,'{}','{}' FROM profile_systems WHERE code='DEMO_60'$$,'service_role actor NULL may insert zero position');
SELECT throws_ok($$INSERT INTO projects(org_id,code,name,client_name,created_by,total_cost_net) VALUES('88000000-0000-4000-8000-000000000001','REJECT-service_role-total_cost_net','Rejected','Fixture','88100000-0000-4000-8000-000000000001',1)$$,'42501','pricing_service_required','service_role rejects nonzero total_cost_net INSERT');
SELECT throws_ok($$INSERT INTO projects(org_id,code,name,client_name,created_by,total_price_net) VALUES('88000000-0000-4000-8000-000000000001','REJECT-service_role-total_price_net','Rejected','Fixture','88100000-0000-4000-8000-000000000001',1)$$,'42501','pricing_service_required','service_role rejects nonzero total_price_net INSERT');
SELECT throws_ok($$INSERT INTO projects(org_id,code,name,client_name,created_by,total_price_tax) VALUES('88000000-0000-4000-8000-000000000001','REJECT-service_role-total_price_tax','Rejected','Fixture','88100000-0000-4000-8000-000000000001',1)$$,'42501','pricing_service_required','service_role rejects nonzero total_price_tax INSERT');
SELECT throws_ok($$INSERT INTO projects(org_id,code,name,client_name,created_by,total_price_gross) VALUES('88000000-0000-4000-8000-000000000001','REJECT-service_role-total_price_gross','Rejected','Fixture','88100000-0000-4000-8000-000000000001',1)$$,'42501','pricing_service_required','service_role rejects nonzero total_price_gross INSERT');
SELECT throws_ok($$INSERT INTO project_positions(org_id,project_id,position_index,typology,system_id,width_mm,height_mm,parametric_tree,bom_snapshot,cost_net) SELECT '88000000-0000-4000-8000-000000000001','88400000-0000-4000-8000-000000000002',2,'FIXED',id,1000,1000,'{}','{}',0.01 FROM profile_systems WHERE code='DEMO_60'$$,'42501','pricing_service_required','service_role rejects nonzero cost_net INSERT');
SELECT throws_ok($$INSERT INTO project_positions(org_id,project_id,position_index,typology,system_id,width_mm,height_mm,parametric_tree,bom_snapshot,price_net) SELECT '88000000-0000-4000-8000-000000000001','88400000-0000-4000-8000-000000000002',2,'FIXED',id,1000,1000,'{}','{}',0.01 FROM profile_systems WHERE code='DEMO_60'$$,'42501','pricing_service_required','service_role rejects nonzero price_net INSERT');
SELECT throws_ok($$INSERT INTO project_positions(org_id,project_id,position_index,typology,system_id,width_mm,height_mm,parametric_tree,bom_snapshot,discount_pct) SELECT '88000000-0000-4000-8000-000000000001','88400000-0000-4000-8000-000000000002',2,'FIXED',id,1000,1000,'{}','{}',0.01 FROM profile_systems WHERE code='DEMO_60'$$,'42501','pricing_service_required','service_role rejects nonzero discount_pct INSERT');
RESET ROLE;
SELECT * FROM finish();
ROLLBACK;
