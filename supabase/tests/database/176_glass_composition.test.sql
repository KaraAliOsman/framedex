BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
GRANT USAGE ON SCHEMA extensions TO catalog_backend;
SET LOCAL search_path=public,private,auth,extensions,pg_temp;
SELECT plan(23);
SELECT has_table('public','catalog_glass_compositions','immutable compositions exist');
SELECT has_table('public','glass_safety_rule_sets','organization safety rules exist');
SELECT has_table('public','glass_safety_rule_revisions','append-only safety history exists');
SELECT ok((SELECT relrowsecurity FROM pg_class WHERE oid='public.catalog_glass_compositions'::regclass),'composition RLS is enabled');
SELECT ok((SELECT relrowsecurity FROM pg_class WHERE oid='public.glass_safety_rule_sets'::regclass),'rules RLS is enabled');
SELECT ok((SELECT relrowsecurity FROM pg_class WHERE oid='public.glass_safety_rule_revisions'::regclass),'history RLS is enabled');
SELECT is(private.legacy_glass_composition(' DVH 5-12-5 ')->'layers'->1->>'width_mm','12','legacy parse preserves chamber width');
SELECT is(private.legacy_glass_composition('vidrio especial sin ficha'),NULL::JSONB,'unparseable legacy data is UNKNOWN');
SELECT is(private.legacy_glass_composition('3+3')->'layers'->0->'interlayers','[{}]'::JSONB,'legacy laminate never invents PVB');
SELECT is((SELECT count(*)::INT FROM catalog_glass_compositions c JOIN profile_systems s ON s.id=c.system_id WHERE s.version=2 AND product->>'source' LIKE 'DEMO%' AND product->>'synthetic'='true'),10,'five v2 families retain two explicit synthetic products');
INSERT INTO tenancy_organizations(id,name,tax_id) VALUES
 ('17600000-0000-4000-8000-000000000001','Glass A','D02-A'),
 ('17600000-0000-4000-8000-000000000002','Glass B','D02-B');
INSERT INTO tenancy_memberships(org_id,user_id,role) VALUES
 ('17600000-0000-4000-8000-000000000001','17600000-0000-4000-8000-000000000003','WORKSHOP_MANAGER'),
 ('17600000-0000-4000-8000-000000000002','17600000-0000-4000-8000-000000000004','WORKSHOP_MANAGER');
SET LOCAL ROLE catalog_backend;
SELECT set_config('request.jwt.claims','{"sub":"17600000-0000-4000-8000-000000000003","role":"authenticated","aal":"aal2"}',TRUE);
SELECT set_config('request.jwt.claim.sub','17600000-0000-4000-8000-000000000003',TRUE);
RESET ROLE;
UPDATE profile_systems SET technical_locked=TRUE WHERE code='DEMO_60' AND version=2;
SET LOCAL ROLE catalog_backend;
SELECT lives_ok($$INSERT INTO glass_purchase_mappings(id,org_id,system_id,technical_sku,purchasing_sku,manufacturer_name,purchase_unit,version,glass_spec,provenance)
 SELECT '17600000-0000-4000-8000-000000000005','17600000-0000-4000-8000-000000000001',id,'D02-VARIANT','D02-BUY','Test supplier','EA',1,'4-16-4','{"source":"Test supplier sheet"}'
 FROM profile_systems WHERE code='DEMO_60' AND version=2 RETURNING id$$,'authorized tenant variant on global series is readable after insert');
SELECT lives_ok($$INSERT INTO catalog_glass_compositions(org_id,system_id,mapping_id,status,product)
 SELECT '17600000-0000-4000-8000-000000000001',system_id,id,'PARSED','{"name":"Test variant","source":"Test supplier sheet","composition":{"layers":[{"kind":"PANE","plies":[{"thickness_mm":"4"}],"interlayers":[]}]}}'
 FROM glass_purchase_mappings WHERE id='17600000-0000-4000-8000-000000000005' RETURNING id$$,'variant recipe follows its mapping scope');
SELECT throws_ok($$INSERT INTO glass_purchase_mappings(org_id,system_id,technical_sku,purchasing_sku,manufacturer_name,purchase_unit,version)
 SELECT '17600000-0000-4000-8000-000000000001',id,'D02-VARIANT','D02-BUY-2','Test','EA',2
 FROM profile_systems WHERE code='DEMO_60' AND version=2$$,'23514','catalog_authority_referenced','new version cannot replace a tenant SKU on a frozen series');
SELECT throws_ok($$INSERT INTO glass_purchase_mappings(org_id,system_id,technical_sku,purchasing_sku,manufacturer_name,purchase_unit,version)
 SELECT '17600000-0000-4000-8000-000000000001',id,'DEMO_60-GLASS-LOWE','D02-FORGED','Test','EA',2
 FROM profile_systems WHERE code='DEMO_60' AND version=2$$,'23514','catalog_authority_referenced','tenant cannot shadow the frozen global SKU');
SELECT throws_ok($$UPDATE glass_purchase_mappings SET glass_spec='6-12-6' WHERE id='17600000-0000-4000-8000-000000000005'$$,
 '42501','permission denied for table glass_purchase_mappings','catalog backend cannot update a frozen mapping');
RESET ROLE;
SELECT throws_ok($$UPDATE glass_purchase_mappings SET glass_spec='6-12-6' WHERE id='17600000-0000-4000-8000-000000000005'$$,
 '23514','catalog_authority_referenced','frozen mapping remains immutable even for database owner');
SELECT throws_ok($$UPDATE catalog_glass_compositions SET id=id WHERE mapping_id='17600000-0000-4000-8000-000000000005'$$,
 '42501','documentary_evidence_immutable','recipe cannot change');
SET LOCAL ROLE catalog_backend;
SELECT throws_ok($$INSERT INTO catalog_glass_compositions(org_id,system_id,mapping_id,status,product)
 SELECT '17600000-0000-4000-8000-000000000002',system_id,id,'PARSED','{"name":"Wrong","source":"Test","composition":{"layers":[]}}'
 FROM glass_purchase_mappings WHERE id='17600000-0000-4000-8000-000000000005'$$,
 '23514','glass_composition_scope_invalid','recipe cannot cross tenant');
INSERT INTO glass_safety_rule_sets(org_id,payload) VALUES('17600000-0000-4000-8000-000000000001','[]');
INSERT INTO glass_safety_rule_revisions(org_id,actor_id,revision,payload) VALUES('17600000-0000-4000-8000-000000000001','17600000-0000-4000-8000-000000000003',1,'[]');
SELECT set_config('request.jwt.claims','{"sub":"17600000-0000-4000-8000-000000000004","role":"authenticated","aal":"aal2"}',TRUE);
SELECT set_config('request.jwt.claim.sub','17600000-0000-4000-8000-000000000004',TRUE);
SELECT is((SELECT count(*)::INT FROM catalog_glass_compositions WHERE mapping_id='17600000-0000-4000-8000-000000000005'),0,'foreign variant is invisible');
SELECT is((SELECT count(*)::INT FROM glass_safety_rule_sets),0,'foreign rules are invisible');
SELECT is((SELECT count(*)::INT FROM glass_safety_rule_revisions),0,'foreign history is invisible');
RESET ROLE;
SELECT throws_ok($$UPDATE glass_safety_rule_revisions SET payload='[{}]'$$,'42501','documentary_evidence_immutable','history cannot be rewritten even by database owner');
SELECT throws_ok($$DELETE FROM glass_safety_rule_revisions$$,'42501','documentary_evidence_immutable','history cannot be deleted');
SELECT * FROM finish();
ROLLBACK;
