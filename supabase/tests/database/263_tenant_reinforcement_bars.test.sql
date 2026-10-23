BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
GRANT USAGE ON SCHEMA extensions TO catalog_backend;
SET LOCAL search_path=public,private,auth,extensions,pg_temp;
SELECT plan(8);

SELECT ok(has_table_privilege('catalog_backend','public.reinforcement_articles','INSERT'),
 'the catalog import may declare a steel bar purchase');
SELECT ok(NOT has_table_privilege('catalog_backend','public.reinforcement_articles','DELETE'),
 'an undone import deactivates steel bars; it never deletes them');
SELECT ok(NOT has_table_privilege('authenticated','public.reinforcement_articles','INSERT'),
 'the browser never writes steel bars directly');

INSERT INTO tenancy_organizations(id,name,tax_id) VALUES
 ('26300000-0000-4000-8000-000000000001','Taller con acero','E2E-263-A'),
 ('26300000-0000-4000-8000-000000000002','Otro taller','E2E-263-B');
INSERT INTO tenancy_memberships(org_id,user_id,role) VALUES
 ('26300000-0000-4000-8000-000000000001','26300000-0000-4000-8000-000000000003','WORKSHOP_MANAGER'),
 ('26300000-0000-4000-8000-000000000002','26300000-0000-4000-8000-000000000004','WORKSHOP_MANAGER');
SET LOCAL ROLE authenticated;
SELECT set_config('request.jwt.claims','{"sub":"26300000-0000-4000-8000-000000000003","role":"authenticated","aal":"aal2"}',TRUE);
SELECT set_config('request.jwt.claim.sub','26300000-0000-4000-8000-000000000003',TRUE);
INSERT INTO profile_systems(id,org_id,name,code,depth_mm,door_leaf_side_clearance_mm,system_family)
 VALUES('26300000-0000-4000-8000-000000000005','26300000-0000-4000-8000-000000000001','PRO6004 ensayo','PRO6004',60,0,'CASEMENT');
RESET ROLE;
SET LOCAL ROLE catalog_backend;
INSERT INTO profile_articles(id,org_id,system_id,sku,name,role,face_width_mm)
 VALUES('26300000-0000-4000-8000-000000000006','26300000-0000-4000-8000-000000000001',
  '26300000-0000-4000-8000-000000000005','MARCO','Marco','FRAME',60);

SELECT lives_ok($$INSERT INTO reinforcement_articles(id,org_id,system_id,parent_profile_article_id,sku,commercial_sku,name,stock_length_mm,purchase_unit,is_default)
 VALUES('26300000-0000-4000-8000-000000000007','26300000-0000-4000-8000-000000000001','26300000-0000-4000-8000-000000000005',
  '26300000-0000-4000-8000-000000000006','ACERO-MARCO','ACERO-MARCO','Acero de marco',6000,'BAR',TRUE)$$,
 'a catalog manager declares the steel bar of their own series');
SELECT lives_ok($$UPDATE reinforcement_articles SET is_active=FALSE WHERE id='26300000-0000-4000-8000-000000000007'$$,
 'an undone import deactivates its steel bar');
SELECT throws_ok($$INSERT INTO reinforcement_articles(org_id,system_id,parent_profile_article_id,sku,commercial_sku,name,stock_length_mm,purchase_unit)
 VALUES('26300000-0000-4000-8000-000000000002','26300000-0000-4000-8000-000000000005',
  '26300000-0000-4000-8000-000000000006','AJENO','AJENO','Acero ajeno',6000,'BAR')$$,
 '42501',NULL,'nobody declares steel for another workshop');
SELECT throws_ok($$INSERT INTO reinforcement_articles(org_id,system_id,parent_profile_article_id,sku,commercial_sku,name,stock_length_mm,purchase_unit)
 VALUES(NULL,'26300000-0000-4000-8000-000000000005',
  '26300000-0000-4000-8000-000000000006','GLOBAL','GLOBAL','Acero global',6000,'BAR')$$,
 '42501',NULL,'a workshop cannot author global steel');

SELECT set_config('request.jwt.claims','{"sub":"26300000-0000-4000-8000-000000000004","role":"authenticated","aal":"aal2"}',TRUE);
SELECT set_config('request.jwt.claim.sub','26300000-0000-4000-8000-000000000004',TRUE);
SELECT is((SELECT count(*)::integer FROM reinforcement_articles WHERE org_id='26300000-0000-4000-8000-000000000001'),0,
 'another workshop does not read this steel');
RESET ROLE;

SELECT * FROM finish();
ROLLBACK;
