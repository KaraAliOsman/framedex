BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
GRANT USAGE ON SCHEMA extensions TO catalog_backend;
SET LOCAL search_path=public,private,auth,extensions,pg_temp;
SELECT plan(14);

SELECT ok(has_table_privilege('catalog_backend','public.reinforcement_cut_policies','INSERT'),
 'the owner confirms the workshop rules of their own series');
SELECT ok(NOT has_table_privilege('catalog_backend','public.reinforcement_cut_policies','UPDATE')
 AND NOT has_table_privilege('catalog_backend','public.manufacturing_placement_policies','DELETE'),
 'a confirmed workshop policy is never edited or deleted: a change is a new version');
SELECT ok(NOT has_table_privilege('authenticated','public.inspector_rule_configs','INSERT'),
 'the browser never writes inspector rules directly');
SELECT ok(NOT has_table_privilege('catalog_backend','public.inspector_rule_configs','INSERT')
 AND NOT has_table_privilege('catalog_backend','public.inspector_rule_configs','UPDATE'),
 'inspector rules are written only through their declaring function');

INSERT INTO tenancy_organizations(id,name,tax_id) VALUES
 ('26500000-0000-4000-8000-000000000001','Taller Proline','E2E-265-A'),
 ('26500000-0000-4000-8000-000000000002','Otro taller','E2E-265-B');
INSERT INTO tenancy_memberships(org_id,user_id,role) VALUES
 ('26500000-0000-4000-8000-000000000001','26500000-0000-4000-8000-000000000003','OWNER'),
 ('26500000-0000-4000-8000-000000000002','26500000-0000-4000-8000-000000000004','OWNER');
INSERT INTO profile_systems(id,org_id,name,code,depth_mm,door_leaf_side_clearance_mm,system_family,chamber_clearance_mm)
 VALUES('26500000-0000-4000-8000-000000000005','26500000-0000-4000-8000-000000000001','PRO6004 ensayo','PRO6004',60,0,'CASEMENT',12),
       ('26500000-0000-4000-8000-000000000006','26500000-0000-4000-8000-000000000001','PRO6004 usada','PRO6004U',60,0,'CASEMENT',NULL);
INSERT INTO catalog_series_setup(system_id,org_id,verified_at,verified_by,verified_hash)
 VALUES('26500000-0000-4000-8000-000000000006','26500000-0000-4000-8000-000000000001',now(),
  '26500000-0000-4000-8000-000000000003','sha256:'||repeat('a',64));
-- A saved window locks the series: not a technical edit of what was verified.
UPDATE profile_systems SET technical_locked=TRUE WHERE id='26500000-0000-4000-8000-000000000006';
SELECT isnt((SELECT verified_at FROM catalog_series_setup WHERE system_id='26500000-0000-4000-8000-000000000006'),NULL,
 'using a verified series in a work keeps it verified');

SET LOCAL ROLE catalog_backend;
SELECT set_config('request.jwt.claims','{"sub":"26500000-0000-4000-8000-000000000003","role":"authenticated","aal":"aal2"}',TRUE);
SELECT set_config('request.jwt.claim.sub','26500000-0000-4000-8000-000000000003',TRUE);
SELECT lives_ok($$INSERT INTO reinforcement_cut_policies(system_id,org_id,version,authority)
 VALUES('26500000-0000-4000-8000-000000000005','26500000-0000-4000-8000-000000000001',1,'{"rules":[]}')$$,
 'the owner records a reinforcement policy for their own series');
SELECT throws_ok($$INSERT INTO manufacturing_placement_policies(system_id,org_id,version,authority)
 VALUES('26500000-0000-4000-8000-000000000005','26500000-0000-4000-8000-000000000002',1,'{}')$$,
 '42501',NULL,'nobody writes workshop rules in another workshop''s name');
SELECT throws_ok($$INSERT INTO handle_requirement_policies(system_id,org_id,version,authority)
 VALUES('26500000-0000-4000-8000-000000000005',NULL,9,'{}')$$,
 '42501',NULL,'a workshop cannot author global workshop rules');
SELECT lives_ok($$SELECT private.declare_inspector_rule('26500000-0000-4000-8000-000000000005',
 '26500000-0000-4000-8000-000000000001','R08','{"max_spacing_mm":"800.00"}')$$,
 'the owner declares an inspector rule of their own series');

-- A series already used in a work receives what it never had.
SELECT lives_ok($$UPDATE profile_systems SET chamber_clearance_mm=12 WHERE id='26500000-0000-4000-8000-000000000006'$$,
 'a used series may declare its missing chamber clearance');
SELECT lives_ok($$SELECT private.declare_inspector_rule('26500000-0000-4000-8000-000000000006',
 '26500000-0000-4000-8000-000000000001','R08','{"max_spacing_mm":"800.00"}')$$,
 'a used series may declare an inspector rule it never had');
-- ...but keeps what it declared.
SELECT throws_ok($$SELECT private.declare_inspector_rule('26500000-0000-4000-8000-000000000006',
 '26500000-0000-4000-8000-000000000001','R08','{"max_spacing_mm":"700.00"}')$$,
 '23514','catalog_authority_referenced','a used series keeps its declared inspector rules');
SELECT throws_ok($$UPDATE profile_systems SET chamber_clearance_mm=13 WHERE id='26500000-0000-4000-8000-000000000006'$$,
 '23514','catalog_authority_referenced','a used series keeps its declared chamber clearance');

SELECT set_config('request.jwt.claims','{"sub":"26500000-0000-4000-8000-000000000004","role":"authenticated","aal":"aal2"}',TRUE);
SELECT set_config('request.jwt.claim.sub','26500000-0000-4000-8000-000000000004',TRUE);
SELECT is((SELECT count(*)::integer FROM reinforcement_cut_policies WHERE org_id='26500000-0000-4000-8000-000000000001'),0,
 'another workshop does not read these workshop rules');
RESET ROLE;

SELECT * FROM finish();
ROLLBACK;
