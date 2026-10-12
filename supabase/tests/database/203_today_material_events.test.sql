BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(5);

INSERT INTO tenancy_organizations(id,name,tax_id) VALUES
 ('03000000-0000-4000-8000-000000000001','P03 event fixture DEMO','P03-EVENT');
INSERT INTO projects(id,org_id,code,name,client_name,created_by) VALUES
 ('03000000-0000-4000-8000-000000000004','03000000-0000-4000-8000-000000000001','P03-EVENT','Event fixture DEMO','Test client','03000000-0000-4000-8000-000000000003');
INSERT INTO orders(id,org_id,project_id,order_type,status,order_code,payload_json) VALUES
 ('03000000-0000-4000-8000-000000000002','03000000-0000-4000-8000-000000000001','03000000-0000-4000-8000-000000000004','WORKSHOP_OT','RELEASED','OT-P03-EVENT','{}');
SELECT lives_ok($$INSERT INTO production_step_events(org_id,order_id,event,actor_id)
 VALUES('03000000-0000-4000-8000-000000000001','03000000-0000-4000-8000-000000000002','WO_MATERIAL_RECHECK','03000000-0000-4000-8000-000000000003')$$,
 'a material recheck can finish its audit transaction');
SELECT lives_ok($$INSERT INTO production_step_events(org_id,order_id,event,actor_id)
 VALUES('03000000-0000-4000-8000-000000000001','03000000-0000-4000-8000-000000000002','WO_CANCELLED','03000000-0000-4000-8000-000000000003')$$,
 'a cancelled order can finish its audit transaction');
SELECT lives_ok($$INSERT INTO production_step_events(org_id,order_id,event,actor_id)
 VALUES('03000000-0000-4000-8000-000000000001','03000000-0000-4000-8000-000000000002','WO_CNC_PROGRAM','03000000-0000-4000-8000-000000000003')$$,
 'previous CNC evidence is still accepted');
SELECT throws_ok($$INSERT INTO production_step_events(org_id,order_id,event,actor_id)
 VALUES('03000000-0000-4000-8000-000000000001','03000000-0000-4000-8000-000000000002','UNDECLARED_EVENT','03000000-0000-4000-8000-000000000003')$$,
 '23514', NULL, 'unknown events remain rejected');
SELECT ok(NOT has_table_privilege('authenticated','production_step_events','INSERT')
 AND NOT has_table_privilege('documentary_backend','production_step_events','UPDATE')
 AND NOT has_table_privilege('documentary_backend','production_step_events','DELETE'),
 'tenant callers cannot forge events and history stays append-only');
SELECT * FROM finish();
ROLLBACK;
