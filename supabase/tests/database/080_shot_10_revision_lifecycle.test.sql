BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;
SET LOCAL search_path=public,extensions;
SELECT plan(16);
SELECT has_column('public','pricing_operations','revision_code',
  'pricing operations expose revision-scoped authority');
SELECT col_type_is('public','pricing_operations','revision_code','text',
  'pricing revision code remains textual and exact');
SELECT has_trigger('public','projects','guard_project_revision_state',
  'project workflow state changes require the revision service');
SELECT has_function('private','project_has_applied_commercial_state',ARRAY['uuid'],
  'commercial guard remains a private revision-aware authority');
SELECT ok(
  (SELECT pg_get_constraintdef(oid) LIKE '%SHOT10_V1%'
   FROM pg_constraint
   WHERE conrelid='public.project_versions'::regclass
     AND conname='project_versions_authority_kind'),
  'SHOT10_V1 is additive to historical documentary authorities'
);
SELECT ok(
  (SELECT pg_get_constraintdef(oid) LIKE '%SHOT09_V1%REV-A%'
   FROM pg_constraint
   WHERE conrelid='public.project_versions'::regclass
     AND conname='project_versions_initial_revision'),
  'historical SHOT09_V1 remains REV-A-only'
);
SELECT ok(
  pg_get_functiondef('private.require_applied_pricing_authority()'::regprocedure)
    LIKE '%COALESCE(revision_code, ''REV-A'') = NEW.revision_code%',
  'freeze binds APPLIED pricing to the emitted revision'
);
SELECT ok(
  pg_get_functiondef('private.guard_documentary_input_mutation()'::regprocedure)
    LIKE '%version.revision_code = project.current_revision%',
  'documentary inputs are sealed only for the emitted current revision'
);
SELECT ok(to_regclass('public.uk_tenant_system_singleton_profile_role') IS NOT NULL,
  'tenant singleton profile roles have an atomic database constraint');
SELECT ok(to_regclass('public.uk_global_system_singleton_profile_role') IS NOT NULL,
  'global singleton profile roles have an atomic database constraint');
SELECT ok(
  pg_get_indexdef('public.uk_tenant_system_singleton_profile_role'::regclass)
    LIKE '%INVERSOR%' AND
  pg_get_indexdef('public.uk_tenant_system_singleton_profile_role'::regclass)
    LIKE '%ADDITIONAL%',
  'tenant singleton index covers every singleton profile role'
);
SELECT ok(
  pg_get_indexdef('public.uk_global_system_singleton_profile_role'::regclass)
    LIKE '%INVERSOR%' AND
  pg_get_indexdef('public.uk_global_system_singleton_profile_role'::regclass)
    LIKE '%ADDITIONAL%',
  'global singleton index covers every singleton profile role'
);
SELECT has_trigger('public','profile_articles','guard_singleton_profile_role',
  'singleton profile roles are enforced across global and tenant scopes');
INSERT INTO public.tenancy_organizations (id, name, tax_id)
VALUES ('88000000-0000-4000-8000-000000000001','Singleton A','SHOT10-A');
INSERT INTO public.profile_systems
SELECT (jsonb_populate_record(NULL::public.profile_systems,to_jsonb(source)||
  jsonb_build_object('id','77000000-0000-4000-8000-0000000000AA'::uuid,'code','PGTAP10',
    'is_demo',false,'technical_locked',false))).*
FROM public.profile_systems source WHERE code='DEMO_60';
INSERT INTO public.profile_articles (system_id, sku, name, role, face_width_mm)
VALUES ('77000000-0000-4000-8000-0000000000AA','PGTAP10-FRAME','Global frame','FRAME',60.00);
SELECT throws_ok($$
  INSERT INTO public.profile_articles (system_id, org_id, sku, name, role, face_width_mm)
  VALUES ('77000000-0000-4000-8000-0000000000AA','88000000-0000-4000-8000-000000000001',
          'PGTAP-DUP-FRAME','Duplicate frame','FRAME',60.00)$$,
  '23505', 'catalog_singleton_role_conflict',
  'a tenant frame cannot duplicate the global frame on a global system');
SELECT lives_ok($$
  INSERT INTO public.profile_articles (system_id, org_id, sku, name, role, face_width_mm)
  VALUES ('77000000-0000-4000-8000-0000000000AA','88000000-0000-4000-8000-000000000001',
          'PGTAP-TENANT-COUPLER','Tenant coupler','COUPLER',60.00)$$,
  'a tenant may extend a global system with a role the global catalog lacks');
SELECT lives_ok($$
  INSERT INTO public.profile_articles (system_id, org_id, sku, name, role, face_width_mm)
  VALUES ('77000000-0000-4000-8000-0000000000AA',NULL,
          'PGTAP-GLOBAL-COUPLER','Global coupler','COUPLER',60.00)$$,
  'couplers are multi-valued: a second visible coupler on the same system is allowed');
SELECT * FROM finish();
ROLLBACK;
