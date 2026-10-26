BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
GRANT USAGE ON SCHEMA extensions TO catalog_backend;
SET LOCAL search_path=public,private,auth,extensions,pg_temp;
SELECT plan(9);

SELECT is((SELECT column_default FROM information_schema.columns WHERE table_name='tenancy_organizations'
  AND column_name='site_measurement'),'''REQUIRED''::text','a workshop measures on site unless its owner says otherwise');
SELECT ok(NOT has_table_privilege('catalog_backend','public.fitting_purchase_mappings','DELETE'),
 'a fitting purchase is immutable evidence');

INSERT INTO tenancy_organizations(id,name,tax_id) VALUES
 ('26600000-0000-4000-8000-000000000001','Taller de una persona','E2E-266-A'),
 ('26600000-0000-4000-8000-000000000002','Otro taller','E2E-266-B');
INSERT INTO tenancy_memberships(org_id,user_id,role) VALUES
 ('26600000-0000-4000-8000-000000000001','26600000-0000-4000-8000-000000000003','OWNER'),
 ('26600000-0000-4000-8000-000000000001','26600000-0000-4000-8000-000000000005','ESTIMATOR'),
 ('26600000-0000-4000-8000-000000000002','26600000-0000-4000-8000-000000000004','OWNER');
INSERT INTO profile_systems(id,org_id,name,code,depth_mm,door_leaf_side_clearance_mm,system_family)
 VALUES('26600000-0000-4000-8000-000000000006','26600000-0000-4000-8000-000000000001','PRO6004 ensayo','PRO6004',60,0,'CASEMENT');

SET LOCAL ROLE authenticated;
SELECT set_config('request.jwt.claims','{"sub":"26600000-0000-4000-8000-000000000005","role":"authenticated","aal":"aal1"}',TRUE);
SELECT set_config('request.jwt.claim.sub','26600000-0000-4000-8000-000000000005',TRUE);
SELECT throws_ok($$SELECT private.set_site_measurement('26600000-0000-4000-8000-000000000001','QUOTED')$$,
 '42501',NULL,'only the owner decides how the workshop measures');
SELECT set_config('request.jwt.claims','{"sub":"26600000-0000-4000-8000-000000000003","role":"authenticated","aal":"aal2"}',TRUE);
SELECT set_config('request.jwt.claim.sub','26600000-0000-4000-8000-000000000003',TRUE);
SELECT is(private.set_site_measurement('26600000-0000-4000-8000-000000000001','QUOTED'),'QUOTED',
 'the owner declares that quoted sizes are fabrication sizes');
SELECT throws_ok($$SELECT private.set_site_measurement('26600000-0000-4000-8000-000000000001','LATER')$$,
 'P0001','site_measurement_invalid','an unknown measuring rule is refused');
RESET ROLE;
SELECT is((SELECT count(*)::integer FROM organization_admin_events
  WHERE org_id='26600000-0000-4000-8000-000000000001' AND action='SITE_MEASUREMENT'),1,'the change is audited');

SET LOCAL ROLE catalog_backend;
SELECT lives_ok($$INSERT INTO fitting_purchase_mappings(system_id,org_id,technical_sku,purchasing_sku,manufacturer_name,purchase_unit,version,provenance)
 VALUES('26600000-0000-4000-8000-000000000006','26600000-0000-4000-8000-000000000001','120500051','120500051','Proveedor','EA',1,'{"source":"OT 385"}')$$,
 'the workshop declares how its steel screw is bought');
SELECT throws_ok($$INSERT INTO fitting_purchase_mappings(system_id,org_id,technical_sku,purchasing_sku,manufacturer_name,purchase_unit,version,provenance)
 VALUES('26600000-0000-4000-8000-000000000006','26600000-0000-4000-8000-000000000002','X','X','Proveedor','EA',1,'{}')$$,
 '42501',NULL,'nobody declares fittings for another workshop''s series');
SELECT set_config('request.jwt.claims','{"sub":"26600000-0000-4000-8000-000000000004","role":"authenticated","aal":"aal2"}',TRUE);
SELECT set_config('request.jwt.claim.sub','26600000-0000-4000-8000-000000000004',TRUE);
SET LOCAL ROLE authenticated;
SELECT is((SELECT count(*)::integer FROM fitting_purchase_mappings WHERE org_id='26600000-0000-4000-8000-000000000001'),0,
 'another workshop does not read these purchases');
RESET ROLE;

SELECT * FROM finish();
ROLLBACK;
