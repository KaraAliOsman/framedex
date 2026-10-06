BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
GRANT USAGE ON SCHEMA extensions TO catalog_backend;
SET LOCAL search_path=public,private,auth,extensions,pg_temp;
SELECT plan(15);

SELECT has_column('public','profile_systems','system_family','system families are explicit');
SELECT has_column('public','profile_systems','dimensional_limits','limits belong to the system authority');
SELECT has_column('public','profile_articles','cut_rule','cut rules belong to each role');
SELECT has_column('public','profile_articles','reinforcement_rule','reinforcement is source-backed catalog data');
SELECT cmp_ok((SELECT rebate_depth_mm FROM profile_systems WHERE code='DEMO_60' AND version=2),
 '=',15.00::NUMERIC,'historical seeding cannot overwrite a new family authority');
SELECT ok((SELECT legacy_authority FROM profile_systems WHERE code='DEMO_60' AND version=1)
 AND NOT (SELECT legacy_authority FROM profile_systems WHERE code='DEMO_60' AND version=2),
 'fresh seeding preserves the canonical legacy identity without exempting new catalogs');
SELECT is((SELECT count(DISTINCT s.id)::INT FROM profile_systems s
 JOIN inspector_rule_configs i ON i.system_id=s.id
 JOIN manufacturing_placement_policies m ON m.system_id=s.id
 JOIN handle_requirement_policies h ON h.system_id=s.id
 WHERE s.version=2 AND s.is_global AND s.is_demo AND s.code IN
 ('DEMO_60','DEMO_70','DEMO_CORREDERA_60','DEMO_ALU_CORREDERA','DEMO_ALU_PRACTICABLE')),
 5,'all five new DEMO families carry their synthetic review and manufacturing policies on a clean installation');

INSERT INTO tenancy_organizations(id,name,tax_id) VALUES
 ('17500000-0000-4000-8000-000000000001','D01 family gate','D01-GATE');
INSERT INTO tenancy_memberships(org_id,user_id,role) VALUES
 ('17500000-0000-4000-8000-000000000001','17500000-0000-4000-8000-000000000002','WORKSHOP_MANAGER');
SET LOCAL ROLE authenticated;
SELECT set_config('request.jwt.claims','{"sub":"17500000-0000-4000-8000-000000000002","role":"authenticated","aal":"aal2"}',TRUE);
SELECT set_config('request.jwt.claim.sub','17500000-0000-4000-8000-000000000002',TRUE);
SELECT throws_ok($$INSERT INTO profile_systems(org_id,name,code,depth_mm,door_leaf_side_clearance_mm)
 VALUES('17500000-0000-4000-8000-000000000001','Sin familia','NO-FAMILY',60,0)$$,
 '23514','catalog_family_required','a new series cannot silently inherit a legacy family');
SELECT throws_ok($$INSERT INTO profile_systems(org_id,name,code,depth_mm,door_leaf_side_clearance_mm,system_family,pulley_height_mm)
 VALUES('17500000-0000-4000-8000-000000000001','Practicable','FLAT-SLIDING',60,0,'CASEMENT',10)$$,
 '23514','catalog_family_required','flat sliding values cannot contaminate a casement');
SELECT lives_ok($$INSERT INTO profile_systems(id,org_id,name,code,depth_mm,door_leaf_side_clearance_mm,system_family)
 VALUES('17500000-0000-4000-8000-000000000003','17500000-0000-4000-8000-000000000001','Practicable','CASEMENT-GATE',60,0,'CASEMENT')$$,
 'a typed tenant casement is writable');
SELECT throws_ok($$INSERT INTO profile_systems(org_id,name,code,depth_mm,door_leaf_side_clearance_mm,legacy_authority)
 VALUES('17500000-0000-4000-8000-000000000001','Legacy','FORGED-LEGACY',60,0,TRUE)$$,
 '42501',NULL,'the historical marker cannot be authored by a tenant');
RESET ROLE;
SET LOCAL ROLE catalog_backend;
SELECT throws_ok($$INSERT INTO profile_articles(org_id,system_id,sku,name,role,face_width_mm,cut_rule)
 VALUES('17500000-0000-4000-8000-000000000001','17500000-0000-4000-8000-000000000003','BAD-RULE','Marco','FRAME',60,
 '{"angle_degrees":45,"welding_loss_per_end_mm":"3.00","joint_deduction_per_end_mm":"0.00","meeting_deduction_mm":"0.00","cut_step_mm":"0.01","rounding":"UP"}')$$,
 '23514','catalog_cut_rule_invalid','a rule without a source is rejected even by the API role');
SELECT lives_ok($$INSERT INTO profile_articles(org_id,system_id,sku,name,role,face_width_mm,cut_rule)
 VALUES('17500000-0000-4000-8000-000000000001','17500000-0000-4000-8000-000000000003','SLIDING-SASH-GATE','Hoja corredera','SLIDING_SASH',60,
 '{"angle_degrees":90,"welding_loss_per_end_mm":"0.00","joint_deduction_per_end_mm":"0.00","meeting_deduction_mm":"0.00","cut_step_mm":"0.01","rounding":"UP","source":"Fixture exacto, página 1"}')$$,
 'new profile roles accept a complete exact authority');
SELECT throws_ok($$INSERT INTO profile_articles(org_id,system_id,sku,name,role,face_width_mm)
 VALUES('17500000-0000-4000-8000-000000000001','17500000-0000-4000-8000-000000000003','DUPLICATE-SASH','Otra hoja','SLIDING_SASH',60)$$,
 '23505','catalog_singleton_role_conflict','every new singleton role is unambiguous');
SELECT throws_ok($$UPDATE profile_systems SET dimensional_limits='[{"opening_type":"SLIDING_2L","source":"Fuente", "min_leaf_width_mm":"200","max_leaf_width_mm":"1000","min_leaf_height_mm":"200","max_leaf_height_mm":"1500","min_aspect_ratio":"0.2","max_aspect_ratio":"5"}]'
 WHERE id='17500000-0000-4000-8000-000000000003'$$,
 '23514','catalog_limit_family_incompatible','limits cannot declare an opening from another family');
SELECT * FROM finish();
ROLLBACK;
