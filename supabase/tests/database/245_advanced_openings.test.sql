BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path=public,private,auth,extensions,pg_temp;
SELECT plan(24);
CREATE TEMP TABLE advanced_recipes AS SELECT s.code, cap, recipe
  FROM profile_systems s CROSS JOIN LATERAL jsonb_array_elements(s.opening_capabilities) cap
  CROSS JOIN LATERAL jsonb_array_elements(coalesce(cap->'advanced_recipes','[]')) recipe
  WHERE s.version=8;
SELECT is((SELECT count(*)::INT FROM profile_systems WHERE version=8 AND is_demo AND is_global),7,'seven new DEMO identities');
SELECT is((SELECT count(*)::INT FROM advanced_recipes),14,'only fourteen explicitly sourced schemes');
SELECT ok((SELECT bool_and(private.advanced_recipe_valid(recipe,cap)) FROM advanced_recipes),'all SQL recipes satisfy finite complete authority');
SELECT is((SELECT count(*)::INT FROM profile_systems WHERE version<8 AND opening_capabilities::TEXT LIKE '%advanced_recipes%'),0,'historical capability bytes were not backfilled');
SELECT ok((SELECT bool_and((recipe->>'synthetic')::BOOLEAN AND recipe->>'source' LIKE '%sin certificación%') FROM advanced_recipes),'DEMO sources never claim certification');
SELECT ok(NOT private.advanced_recipe_valid(jsonb_set(recipe,'{panels,0,share}','"0.26"'),cap),'incomplete proportion rejected') FROM advanced_recipes WHERE code='DEMO_HST' AND recipe->>'code'='C';
SELECT ok(NOT private.advanced_recipe_valid(jsonb_set(recipe,'{panels,2,track}','0'),cap),'adjacent moving tracks cannot overlap') FROM advanced_recipes WHERE code='DEMO_HST' AND recipe->>'code'='C';
SELECT ok(NOT private.advanced_recipe_valid(jsonb_set(recipe,'{panels,2,plane_offset_mm}','"20"'),cap),'distinct tracks require distinct planes') FROM advanced_recipes WHERE code='DEMO_HST' AND recipe->>'code'='C';
SELECT ok(NOT private.advanced_recipe_valid(jsonb_set(recipe,'{panels,0,travel}','"LEFT"'),cap),'travel through jamb rejected') FROM advanced_recipes WHERE code='DEMO_HST' AND recipe->>'code'='A';
SELECT ok(NOT private.advanced_recipe_valid(jsonb_set(recipe,'{lift_mm}','null'),cap),'HST cannot lose its lift') FROM advanced_recipes WHERE code='DEMO_HST' AND recipe->>'code'='A';
SELECT ok(NOT private.advanced_recipe_valid(jsonb_set(recipe,'{threshold_height_mm}','null'),cap),'HST cannot lose its threshold') FROM advanced_recipes WHERE code='DEMO_HST' AND recipe->>'code'='A';
SELECT ok(NOT private.advanced_recipe_valid(jsonb_set(recipe,'{parallel_offset_mm}','null'),cap),'PSK cannot lose its parallel offset') FROM advanced_recipes WHERE code='DEMO_PSK';
SELECT ok(NOT private.advanced_recipe_valid(jsonb_set(recipe,'{panels,0,pivot_fraction}','null'),cap),'pivot requires a declared displaced axis') FROM advanced_recipes WHERE code='DEMO_PIVOT_V';
SELECT ok(NOT private.advanced_recipe_valid(jsonb_set(recipe,'{panels,0,pivot_fraction}','"1"'),cap),'pivot cannot rotate about an external edge') FROM advanced_recipes WHERE code='DEMO_PIVOT_H';
SELECT ok(NOT private.advanced_recipe_valid(jsonb_set(recipe,'{panels,0,balance}','null'),cap),'guillotine requires balance authority') FROM advanced_recipes WHERE code='DEMO_GUILLOTINA' AND recipe->>'code'='DOBLE-MUELLES';
SELECT ok(NOT private.advanced_recipe_valid(jsonb_set(recipe,'{pass_through_hardware_kit_skus}','[]'),cap),'passage requires its own sourced kit') FROM advanced_recipes WHERE code='DEMO_PLEGABLE' AND recipe->>'code'='3+0-PASO';
SELECT ok(NOT private.advanced_recipe_valid(jsonb_set(recipe,'{panels,0,fold_index}','2'),cap),'fold packet cannot lose physical order') FROM advanced_recipes WHERE code='DEMO_PLEGABLE' AND recipe->>'code'='3+0-PASO';
SELECT ok(NOT private.advanced_recipe_valid(jsonb_set(recipe,'{starter_width_mm}','"NaN"'),cap),'nonfinite Decimal text rejected') FROM advanced_recipes WHERE code='DEMO_PIVOT_V';
SELECT ok(NOT private.advanced_recipe_valid(jsonb_set(recipe,'{made_up_price}','"123"'),cap),'unknown executable/numeric authority rejected') FROM advanced_recipes WHERE code='DEMO_PIVOT_V';
SELECT ok((SELECT relrowsecurity FROM pg_class WHERE oid='public.profile_systems'::REGCLASS),'advanced authority retains tenant RLS');
SELECT ok(NOT has_function_privilege('authenticated','private.advanced_recipe_valid(jsonb,jsonb)','EXECUTE'),'no direct public recipe authority endpoint');
SELECT is((SELECT count(*)::INT FROM reinforcement_cut_policies p JOIN profile_systems s ON s.id=p.system_id
  WHERE s.version=8 AND p.version=9),3,'three explicit threshold policy revisions');
SELECT ok(NOT EXISTS(SELECT 1 FROM reinforcement_cut_policies p JOIN profile_systems s ON s.id=p.system_id
  CROSS JOIN LATERAL jsonb_array_elements(p.authority->'rules') r WHERE s.version=8 AND p.version=9
  GROUP BY p.id,r->>'role',(r->>'profile_angle_left')::NUMERIC,(r->>'profile_angle_right')::NUMERIC HAVING count(*)>1),
  'one sourced reinforcement rule per physical joint');
SET CONSTRAINTS ALL IMMEDIATE;
SELECT throws_ok($$DELETE FROM profile_articles WHERE system_id=(SELECT id FROM profile_systems WHERE code='DEMO_HST' AND version=8) AND role='RAIL'$$,
  '23514','advanced_opening_profile_required','specific guide binding cannot be removed');
SELECT * FROM finish();
ROLLBACK;
