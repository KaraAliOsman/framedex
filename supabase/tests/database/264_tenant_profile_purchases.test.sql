BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
GRANT USAGE ON SCHEMA extensions TO catalog_backend;
SET LOCAL search_path=public,private,auth,extensions,pg_temp;
SELECT plan(8);

SELECT ok(has_table_privilege('catalog_backend','public.profile_purchase_mappings','INSERT'),
 'the catalog import may declare a plain profile bar purchase');
SELECT ok(NOT has_table_privilege('catalog_backend','public.profile_purchase_mappings','DELETE'),
 'an undone import deactivates bar purchases; it never deletes them');
SELECT ok(NOT has_table_privilege('authenticated','public.profile_purchase_mappings','INSERT'),
 'the browser never writes bar purchases directly');

INSERT INTO tenancy_organizations(id,name,tax_id) VALUES
 ('26400000-0000-4000-8000-000000000001','Taller con acero','E2E-264-A'),
 ('26400000-0000-4000-8000-000000000002','Otro taller','E2E-264-B');
INSERT INTO tenancy_memberships(org_id,user_id,role) VALUES
 ('26400000-0000-4000-8000-000000000001','26400000-0000-4000-8000-000000000003','WORKSHOP_MANAGER'),
 ('26400000-0000-4000-8000-000000000002','26400000-0000-4000-8000-000000000004','WORKSHOP_MANAGER');
SET LOCAL ROLE authenticated;
SELECT set_config('request.jwt.claims','{"sub":"26400000-0000-4000-8000-000000000003","role":"authenticated","aal":"aal2"}',TRUE);
SELECT set_config('request.jwt.claim.sub','26400000-0000-4000-8000-000000000003',TRUE);
INSERT INTO profile_systems(id,org_id,name,code,depth_mm,door_leaf_side_clearance_mm,system_family)
 VALUES('26400000-0000-4000-8000-000000000005','26400000-0000-4000-8000-000000000001','PRO6004 ensayo','PRO6004',60,0,'CASEMENT');
RESET ROLE;
SET LOCAL ROLE catalog_backend;
INSERT INTO profile_articles(id,org_id,system_id,sku,name,role,face_width_mm)
 VALUES('26400000-0000-4000-8000-000000000006','26400000-0000-4000-8000-000000000001',
  '26400000-0000-4000-8000-000000000005','MARCO','Marco','FRAME',60);

SELECT lives_ok($$INSERT INTO profile_purchase_mappings(id,org_id,profile_article_id,commercial_sku,manufacturer_name,purchase_unit)
 VALUES('26400000-0000-4000-8000-000000000007','26400000-0000-4000-8000-000000000001',
  '26400000-0000-4000-8000-000000000006','PRO01','Proline','BAR')$$,
 'a catalog manager declares how their own profile is bought');
SELECT lives_ok($$UPDATE profile_purchase_mappings SET is_active=FALSE WHERE id='26400000-0000-4000-8000-000000000007'$$,
 'an undone import deactivates its bar purchase');
SELECT throws_ok($$INSERT INTO profile_purchase_mappings(org_id,profile_article_id,commercial_sku,manufacturer_name,purchase_unit)
 VALUES('26400000-0000-4000-8000-000000000002','26400000-0000-4000-8000-000000000006','AJENO','Proline','BAR')$$,
 '42501',NULL,'nobody declares purchases for another workshop');
SELECT throws_ok($$INSERT INTO profile_purchase_mappings(org_id,profile_article_id,commercial_sku,manufacturer_name,purchase_unit)
 VALUES(NULL,'26400000-0000-4000-8000-000000000006','GLOBAL','Proline','BAR')$$,
 '42501',NULL,'a workshop cannot author global purchases');

SELECT set_config('request.jwt.claims','{"sub":"26400000-0000-4000-8000-000000000004","role":"authenticated","aal":"aal2"}',TRUE);
SELECT set_config('request.jwt.claim.sub','26400000-0000-4000-8000-000000000004',TRUE);
SELECT is((SELECT count(*)::integer FROM profile_purchase_mappings WHERE org_id='26400000-0000-4000-8000-000000000001'),0,
 'another workshop does not read these purchases');
RESET ROLE;

SELECT * FROM finish();
ROLLBACK;
