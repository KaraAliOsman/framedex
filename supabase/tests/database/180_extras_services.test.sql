BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path=public,extensions,pg_temp;
SELECT plan(29);
SELECT has_column('public','profile_systems','extra_authority','accessory authority is additive');
SELECT is((SELECT count(*)::INT FROM profile_systems WHERE version=6 AND is_global),6,'six additive v6 series');
SELECT is((SELECT count(*)::INT FROM profile_systems WHERE version<6 AND extra_authority IS NOT NULL),0,'prior accessory field stays absent');
SELECT ok((SELECT bool_and(extra_authority_valid(extra_authority)) FROM profile_systems WHERE version=6),'all v6 authorities are valid');
SELECT ok((SELECT bool_and((d->>'synthetic')::BOOLEAN) FROM profile_systems s CROSS JOIN LATERAL jsonb_array_elements(s.extra_authority->'definitions') d WHERE s.version=6),'all synthetic tariffs declare DEMO');
SELECT ok((SELECT relrowsecurity FROM pg_class WHERE oid='public.organization_extra_settings'::regclass),'settings have RLS');
SELECT ok((SELECT relrowsecurity FROM pg_class WHERE oid='public.organization_extra_history'::regclass),'history has RLS');
SELECT ok((SELECT relrowsecurity FROM pg_class WHERE oid='public.project_extra_services'::regclass),'services have RLS');
SELECT ok(has_column_privilege('documentary_backend','public.profile_systems','extra_authority','SELECT'),'seal can read authority');
SELECT ok(NOT has_table_privilege('authenticated','public.organization_extra_settings','SELECT'),'raw rates are not public');
SELECT ok(NOT has_table_privilege('authenticated','public.project_extra_services','UPDATE'),'services cannot bypass backend');
SELECT ok(NOT has_table_privilege('pricing_backend','public.organization_extra_history','UPDATE'),'backend cannot edit history');
SELECT has_trigger('public','organization_extra_settings','extra_policy_identity','policy identity and monotonic revision guarded');
SELECT has_trigger('public','organization_extra_history','organization_extra_history_immutable','history immutable even for elevated writes');
SELECT has_trigger('public','project_extra_services','extra_service_editable','priced or issued services immutable');
CREATE TEMP TABLE sample_extra AS SELECT extra_authority AS a FROM profile_systems WHERE code='DEMO_60' AND version=6;
SELECT ok((SELECT NOT extra_authority_valid(a||'{"source":""}') FROM sample_extra),'blank source rejected');
SELECT ok((SELECT NOT extra_authority_valid(jsonb_set(a,'{definitions,0,cost_rate}','0.1')) FROM sample_extra),'binary float rates rejected');
SELECT ok((SELECT NOT extra_authority_valid(jsonb_set(a,'{definitions,0,cost_rate}','"-1"')) FROM sample_extra),'negative cost rejected');
SELECT ok((SELECT NOT extra_authority_valid(jsonb_set(a,'{definitions,0,selling_rate}','"1"')) FROM sample_extra),'sale below cost rejected');
SELECT ok((SELECT NOT extra_authority_valid(jsonb_set(a,'{definitions,0,unit}','"EA"')) FROM sample_extra),'length tariff needs meters');
SELECT ok((SELECT NOT extra_authority_valid(jsonb_set(a,'{definitions,0,scope}','"PROJECT"')) FROM sample_extra),'physical profile cannot be a project service');
SELECT ok((SELECT NOT extra_authority_valid(jsonb_set(a,'{definitions}',(a->'definitions')||jsonb_build_array(a->'definitions'->0))) FROM sample_extra),'duplicate authority rejected');
SELECT ok((SELECT NOT extra_authority_valid(jsonb_set(a,'{definitions,0,basis}','"AREA"')) FROM sample_extra),'profile needs sourced length rule');
SELECT ok((SELECT NOT extra_authority_valid(jsonb_set(a,'{definitions,1,default_sides}','["LEFT","LEFT"]')) FROM sample_extra),'duplicate sides rejected');
SELECT ok(NOT extra_policy_valid('{"schema_version":1,"services":[],"position_defaults":[{"code":"A"},{"code":"A"}],"document_prices":"ITEMIZED"}'::JSONB),'template cannot duplicate extras');
SELECT ok((SELECT NOT extra_policy_valid(jsonb_build_object('schema_version',1,'services',jsonb_build_array(a->'definitions'->0),'position_defaults','[]'::JSONB,'document_prices','ITEMIZED')) FROM sample_extra),'org service cannot fabricate technical articles');
SELECT ok(hardware_schema_valid('{"Valdivia":{"cost_rate":"15000","selling_rate":"22500"}}',
  '{"type":"object","additionalProperties":{"type":"object","properties":{"cost_rate":{"type":"string"},"selling_rate":{"type":"string"}},"required":["cost_rate","selling_rate"],"additionalProperties":false}}','{}'), 'typed zone maps accepted');
SELECT ok(NOT hardware_schema_valid('{"Valdivia":{"cost_rate":"15000","selling_rate":"22500","unknown":true}}',
  '{"type":"object","additionalProperties":{"type":"object","properties":{"cost_rate":{"type":"string"},"selling_rate":{"type":"string"}},"required":["cost_rate","selling_rate"],"additionalProperties":false}}','{}'), 'typed zone maps still reject undeclared fields');
SELECT ok(NOT hardware_schema_valid('{"Valdivia":{"cost_rate":0.1,"selling_rate":"22500"}}',
  '{"type":"object","additionalProperties":{"type":"object","properties":{"cost_rate":{"type":"string"},"selling_rate":{"type":"string"}},"required":["cost_rate","selling_rate"],"additionalProperties":false}}','{}'), 'typed zone maps reject binary numeric tariffs');
SELECT * FROM finish();
ROLLBACK;
