BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
GRANT USAGE ON SCHEMA extensions TO catalog_backend;
SET LOCAL search_path=public,private,auth,extensions,pg_temp;
SELECT plan(27);
SELECT has_column('public','profile_systems','opening_capabilities','physical capabilities are additive authority');
SELECT has_column('public','profile_systems','paired_leaf_rule','meeting rule is explicit authority');
SELECT is((SELECT count(*)::INT FROM profile_systems WHERE version=3 AND is_global AND opening_capabilities IS NOT NULL),6,'six new versions declare physical capabilities');
SELECT is((SELECT count(*)::INT FROM profile_systems WHERE is_global AND version IN (1,2) AND opening_capabilities IS NOT NULL),0,'old authorities are never inferred or rewritten');
SELECT is((SELECT count(*)::INT FROM inspector_rule_configs r JOIN profile_systems s ON s.id=r.system_id WHERE s.version=3),84,'all new series have the fourteen sourced inspector rules');
SELECT is((SELECT count(*)::INT FROM hardware_kits k JOIN profile_systems s ON s.id=k.system_id WHERE s.version=3 AND k.opening_type='TILT'),3,'banderola has distinct hardware authority');
SELECT ok((SELECT relrowsecurity FROM pg_class WHERE oid='public.profile_systems'::regclass),'capabilities keep the tenant RLS boundary');
SELECT ok(NOT EXISTS(SELECT p.sku FROM catalog_demo_prices p JOIN profile_systems s ON s.id=p.system_id
    WHERE p.org_id IS NULL AND s.is_active GROUP BY p.sku HAVING count(*)>1),
    'shared DEMO SKUs keep one exact price authority across versions');
INSERT INTO tenancy_organizations(id,name,tax_id) VALUES
 ('17700000-0000-4000-8000-000000000001','Opening A','D03-A'),
 ('17700000-0000-4000-8000-000000000002','Opening B','D03-B');
INSERT INTO tenancy_memberships(org_id,user_id,role) VALUES
 ('17700000-0000-4000-8000-000000000001','17700000-0000-4000-8000-000000000003','WORKSHOP_MANAGER'),
 ('17700000-0000-4000-8000-000000000002','17700000-0000-4000-8000-000000000004','WORKSHOP_MANAGER');
INSERT INTO profile_systems SELECT (jsonb_populate_record(NULL::public.profile_systems,to_jsonb(s)||
 jsonb_build_object('id','17700000-0000-4000-8000-000000000005','org_id','17700000-0000-4000-8000-000000000001',
 'code','D03-TEST','name','Opening authority DEMO','is_global',FALSE,'technical_locked',FALSE))).*
 FROM profile_systems s WHERE code='DEMO_60' AND version=3;
INSERT INTO hardware_kits SELECT (jsonb_populate_record(NULL::public.hardware_kits,to_jsonb(k)||
 jsonb_build_object('id',uuid_generate_v4(),'system_id','17700000-0000-4000-8000-000000000005',
 'org_id','17700000-0000-4000-8000-000000000001'))).*
 FROM hardware_kits k JOIN profile_systems s ON s.id=k.system_id WHERE s.code='DEMO_60' AND s.version=3;
INSERT INTO profile_articles SELECT (jsonb_populate_record(NULL::public.profile_articles,to_jsonb(a)||
 jsonb_build_object('id',uuid_generate_v4(),'system_id','17700000-0000-4000-8000-000000000005',
 'org_id','17700000-0000-4000-8000-000000000001'))).*
 FROM profile_articles a JOIN profile_systems s ON s.id=a.system_id WHERE s.code='DEMO_60' AND s.version=3 AND a.role='INVERSOR';
SET CONSTRAINTS ALL IMMEDIATE;
INSERT INTO inspector_rule_configs(id,system_id,org_id,rule_id,params)
 SELECT '17700000-0000-4000-8000-000000000006','17700000-0000-4000-8000-000000000005',
 '17700000-0000-4000-8000-000000000001',r.rule_id,r.params
 FROM inspector_rule_configs r JOIN profile_systems s ON s.id=r.system_id
 WHERE s.code='DEMO_60' AND s.version=3 ORDER BY r.rule_id LIMIT 1;
SELECT throws_ok($$UPDATE profile_systems SET opening_capabilities='{}' WHERE code='D03-TEST'$$,'23514','opening_capabilities_invalid','object cannot replace a capability array');
SELECT throws_ok($$UPDATE profile_systems SET opening_capabilities=jsonb_set(opening_capabilities,'{0,source}','""') WHERE code='D03-TEST'$$,'23514','opening_capability_invalid','missing source cannot create manufacturing authority');
SELECT throws_ok($$UPDATE profile_systems SET opening_capabilities=opening_capabilities||opening_capabilities WHERE code='D03-TEST'$$,'23514','opening_capability_ambiguous','overlapping physical capabilities are rejected');
SELECT throws_ok($$UPDATE profile_systems SET opening_capabilities=jsonb_set(opening_capabilities,'{1,movement}','"FOLD"') WHERE code='D03-TEST'$$,'23514','opening_capability_invalid','advanced motion needs a later exact contract');
SELECT throws_ok($$UPDATE profile_systems SET opening_capabilities=jsonb_set(opening_capabilities,'{1,use}','"DOOR"') WHERE code='D03-TEST'$$,'23514','opening_capability_family_incompatible','door cannot bypass the casement family');
SELECT throws_ok($$UPDATE profile_systems SET paired_leaf_rule=jsonb_set(paired_leaf_rule,'{meeting_gap_mm}','"-0.01"') WHERE code='D03-TEST'$$,'23514','opening_meeting_rule_exact_required','negative meeting gap cannot become manufacturing authority');
SELECT throws_ok($$UPDATE profile_systems SET opening_capabilities=jsonb_set(opening_capabilities,'{1,hardware_kit_skus}','["FOREIGN-KIT"]') WHERE code='D03-TEST'$$,'23514','opening_capability_kit_incompatible','missing or foreign kit does not grant capability');
SELECT throws_ok($$UPDATE hardware_kits SET is_active=FALSE WHERE system_id='17700000-0000-4000-8000-000000000005' AND sku='DEMO_60-KIT-TURN'$$,'23514','opening_capability_kit_incompatible','deactivating a referenced physical kit is rejected');
SELECT throws_ok($$DELETE FROM profile_articles WHERE system_id='17700000-0000-4000-8000-000000000005' AND role='INVERSOR'$$,'23514','opening_inversor_authority_required','active/passive composition cannot lose its meeting profile');
SET LOCAL ROLE catalog_backend;
SELECT set_config('request.jwt.claims','{"sub":"17700000-0000-4000-8000-000000000004","role":"authenticated","aal":"aal2"}',TRUE);
SELECT set_config('request.jwt.claim.sub','17700000-0000-4000-8000-000000000004',TRUE);
SELECT is((SELECT count(*)::INT FROM profile_systems WHERE code='D03-TEST'),0,'foreign tenant capabilities remain invisible');
SELECT is((SELECT count(*)::INT FROM profile_systems WHERE version=3 AND is_global),6,'global sourced capabilities remain readable');
SELECT is((SELECT count(*)::INT FROM inspector_rule_configs WHERE system_id='17700000-0000-4000-8000-000000000005'),0,'catalog clearance reads do not expose another tenant');
SELECT set_config('request.jwt.claims','{"sub":"17700000-0000-4000-8000-000000000003","role":"authenticated","aal":"aal2"}',TRUE);
SELECT set_config('request.jwt.claim.sub','17700000-0000-4000-8000-000000000003',TRUE);
SELECT is((SELECT count(*)::INT FROM inspector_rule_configs WHERE system_id='17700000-0000-4000-8000-000000000005'),1,'catalog clearance guard can read its own authority');
SELECT ok(NOT has_table_privilege('catalog_backend','public.inspector_rule_configs','UPDATE'),'clearance read grants no inspector write privilege');
RESET ROLE;
SET CONSTRAINTS ALL DEFERRED;
SELECT lives_ok($$DO $body$ BEGIN
 UPDATE profile_systems SET is_active=FALSE WHERE code='D03-TEST';
 UPDATE hardware_kits SET is_active=FALSE WHERE system_id='17700000-0000-4000-8000-000000000005';
 DELETE FROM profile_articles WHERE system_id='17700000-0000-4000-8000-000000000005' AND role='INVERSOR';
 SET CONSTRAINTS ALL IMMEDIATE;
END $body$ $$,'a complete unreferenced catalog can be retired atomically');
SET CONSTRAINTS ALL IMMEDIATE;
SELECT throws_ok($$UPDATE profile_systems SET is_active=TRUE WHERE code='D03-TEST'$$,'23514','opening_capability_kit_incompatible','retired kits cannot feed a reactivated system');
UPDATE profile_systems SET technical_locked=TRUE WHERE code='D03-TEST';
SELECT throws_ok($$UPDATE profile_systems SET opening_capabilities=NULL WHERE code='D03-TEST'$$,'23514','catalog_authority_referenced','frozen authority cannot be cleared');
SELECT ok(NOT EXISTS(SELECT 1 FROM pg_proc p CROSS JOIN LATERAL aclexplode(p.proacl) a WHERE p.oid='private.guard_opening_authorities()'::regprocedure AND a.grantee=0 AND a.privilege_type='EXECUTE'),'authority guard is not exposed to PUBLIC');
SELECT ok(NOT EXISTS(SELECT 1 FROM pg_proc p CROSS JOIN LATERAL aclexplode(p.proacl) a WHERE p.oid='private.check_opening_catalog_bindings()'::regprocedure AND a.grantee=0 AND a.privilege_type='EXECUTE'),'binding guard is not exposed to PUBLIC');
SELECT * FROM finish();
ROLLBACK;
