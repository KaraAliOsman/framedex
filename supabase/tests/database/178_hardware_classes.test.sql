BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path=public,extensions,pg_temp;
SELECT plan(22);
SELECT has_column('public','hardware_kits','class_authority','class authority is additive');
SELECT is((SELECT count(*)::INT FROM profile_systems WHERE version=4 AND is_global),6,'six additive v4 series');
SELECT is((SELECT count(*)::INT FROM profile_systems s WHERE s.version=4 AND s.is_global AND
    (SELECT count(*) FROM inspector_rule_configs r WHERE r.system_id=s.id AND r.org_id IS NULL AND r.is_active)=14),6,
    'every clean-seeded v4 series has all fourteen inspection authorities');
SELECT is((SELECT count(*)::INT FROM profile_systems s WHERE s.version=4 AND s.is_global AND
    (SELECT count(*) FROM manufacturing_placement_policies p WHERE p.system_id=s.id AND p.org_id IS NULL)=1),6,
    'every clean-seeded v4 series has its manufacturing policy');
SELECT is((SELECT count(*)::INT FROM profile_systems s WHERE s.version=4 AND s.is_global AND
    (SELECT count(*) FROM handle_requirement_policies p WHERE p.system_id=s.id AND p.org_id IS NULL)=1),6,
    'every clean-seeded v4 series has its handle policy');
SELECT is((SELECT count(*)::INT FROM hardware_kits k JOIN profile_systems s ON s.id=k.system_id WHERE s.version<4 AND k.class_authority IS NOT NULL),0,'historical kit authority stays absent');
SELECT ok((SELECT bool_and(class_authority IS NOT NULL AND contents='[]'::JSONB) FROM hardware_kits k JOIN profile_systems s ON s.id=k.system_id WHERE s.version=4),'new kits have one component authority');
SELECT ok((SELECT relrowsecurity FROM pg_class WHERE oid='public.hardware_kits'::regclass),'hardware keeps tenant RLS');
CREATE TEMP TABLE sample AS SELECT class_authority AS a FROM hardware_kits WHERE class_authority IS NOT NULL LIMIT 1;
SELECT ok((SELECT hardware_class_authority_valid(a) FROM sample),'complete class accepted');
SELECT ok((SELECT NOT hardware_class_authority_valid(a||'{"source":""}'::JSONB) FROM sample),'empty source rejected');
SELECT ok((SELECT NOT hardware_class_authority_valid(jsonb_set(a,'{components,0,quantity,step}','"-1"'::JSONB)) FROM sample),'negative step rejected');
SELECT ok((SELECT NOT hardware_class_authority_valid(jsonb_set(a,'{components,0,weight_kg}','"-0.01"'::JSONB)) FROM sample),'negative component mass rejected');
SELECT ok((SELECT NOT hardware_class_authority_valid(jsonb_set(a,'{components,0,weight_kg_m}','"0.15"'::JSONB)) FROM sample),'two mass authorities rejected');
SELECT ok((SELECT NOT hardware_class_authority_valid(jsonb_set(a,'{components,0,price_unit}','"M"'::JSONB)) FROM sample),'meter needs declared length');
SELECT ok((SELECT NOT hardware_class_authority_valid(jsonb_set(a,'{components,0,machining,0,positions_mm}','["-1"]'::JSONB)) FROM sample),'negative machining position rejected');
SELECT ok((SELECT NOT hardware_class_authority_valid(jsonb_set(a,'{components,0,machining,0,positions_mm}','["100","100"]'::JSONB)) FROM sample),'duplicate machining position rejected');
SELECT ok((SELECT NOT hardware_class_authority_valid(jsonb_set(a,'{handles,0,default_color}','"UNDECLARED"'::JSONB)) FROM sample),'undeclared handle color rejected');
SELECT ok((SELECT NOT hardware_class_authority_valid(a||'{"default_handle":"UNDECLARED"}'::JSONB) FROM sample),'undeclared handle model rejected');
SELECT ok((SELECT NOT hardware_class_authority_valid(jsonb_set(a,'{options,0,replaces_skus}','["UNDECLARED"]'::JSONB)) FROM sample),'option replacement needs base component');
SELECT ok((SELECT NOT hardware_class_authority_valid(a||'{"components":[]}'::JSONB) FROM sample),'empty component class rejected');
SELECT ok((SELECT NOT hardware_class_authority_valid(a||'{"minimum_width_height_ratio":"2","maximum_width_height_ratio":"1"}'::JSONB) FROM sample),'inverted aspect ratio rejected');
SELECT ok(NOT EXISTS(SELECT 1 FROM hardware_kits WHERE class_authority IS NOT NULL AND class_authority->>'synthetic'<>'true'),'DEMO class never claims certification');
SELECT * FROM finish();
ROLLBACK;
