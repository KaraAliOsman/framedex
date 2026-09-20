BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;
SET LOCAL search_path=public,extensions;
SELECT plan(12);
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
    LIKE '%COUPLER%' AND
  pg_get_indexdef('public.uk_tenant_system_singleton_profile_role'::regclass)
    LIKE '%ADDITIONAL%',
  'tenant singleton index covers every non-bead profile role'
);
SELECT ok(
  pg_get_indexdef('public.uk_global_system_singleton_profile_role'::regclass)
    LIKE '%COUPLER%' AND
  pg_get_indexdef('public.uk_global_system_singleton_profile_role'::regclass)
    LIKE '%ADDITIONAL%',
  'global singleton index covers every non-bead profile role'
);
SELECT * FROM finish();
ROLLBACK;
