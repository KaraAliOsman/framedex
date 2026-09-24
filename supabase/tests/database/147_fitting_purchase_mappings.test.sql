BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;
SET LOCAL search_path=public,extensions;
SELECT plan(16);

SELECT has_table('public','fitting_purchase_mappings','fitting authority table exists');
SELECT has_column('public','fitting_purchase_mappings','id','id exists');
SELECT has_column('public','fitting_purchase_mappings','system_id','system_id exists');
SELECT has_column('public','fitting_purchase_mappings','org_id','org_id exists');
SELECT has_column('public','fitting_purchase_mappings','technical_sku','technical_sku exists');
SELECT has_column('public','fitting_purchase_mappings','purchasing_sku','purchasing_sku exists');
SELECT has_column('public','fitting_purchase_mappings','purchase_unit','purchase_unit exists');
SELECT has_column('public','fitting_purchase_mappings','version','version exists');
SELECT has_column('public','fitting_purchase_mappings','provenance','provenance exists');

SELECT ok(NOT has_table_privilege('anon','public.fitting_purchase_mappings','SELECT'),'anon cannot read fitting_purchase_mappings');
SELECT ok(
    NOT has_table_privilege('authenticated','public.fitting_purchase_mappings','INSERT')
    AND NOT has_table_privilege('authenticated','public.fitting_purchase_mappings','UPDATE')
    AND NOT has_table_privilege('authenticated','public.fitting_purchase_mappings','DELETE')
    AND has_table_privilege('authenticated','public.fitting_purchase_mappings','SELECT'),
    'authenticated reads fitting authority but can never write it'
);
SELECT ok(
    has_table_privilege('service_role','public.fitting_purchase_mappings','INSERT')
    AND has_table_privilege('service_role','public.fitting_purchase_mappings','SELECT'),
    'service_role provisions fitting authority'
);

-- Fixture: a system row to hang the authority on.
INSERT INTO public.profile_systems
SELECT (jsonb_populate_record(NULL::public.profile_systems,to_jsonb(source)||
 jsonb_build_object('id','55710000-0000-4000-8000-000000000001','code','PGTAP9','technical_locked',false,'is_demo',false))).*
FROM public.profile_systems source WHERE code='DEMO_60';

INSERT INTO public.fitting_purchase_mappings
    (system_id,org_id,technical_sku,purchasing_sku,manufacturer_name,purchase_unit,version,provenance)
VALUES
    ('55710000-0000-4000-8000-000000000001',NULL,'CLAMP-SS-8','BUY-CLAMP-SS-8','DEMO','EA',1,'{"source":"pgtap"}'),
    ('55710000-0000-4000-8000-000000000001',NULL,'CLAMP-SS-8','BUY-CLAMP-SS-8-V2','DEMO','EA',2,'{"source":"pgtap"}');

SELECT throws_ok(
    $$INSERT INTO public.fitting_purchase_mappings(system_id,org_id,technical_sku,purchasing_sku,manufacturer_name,purchase_unit,version,provenance)
      VALUES('55710000-0000-4000-8000-000000000001',NULL,'CLAMP-SS-8','X','DEMO','EA',1,'{}')$$,
    '23505',NULL,'same (system, org, sku, version) cannot duplicate');
SELECT throws_ok(
    $$INSERT INTO public.fitting_purchase_mappings(system_id,org_id,technical_sku,purchasing_sku,manufacturer_name,purchase_unit,version,provenance)
      VALUES('55710000-0000-4000-8000-000000000001',NULL,'CLAMP-X','X','DEMO','BOX',1,'{}')$$,
    '23514',NULL,'purchase_unit must be EA');
SELECT throws_ok(
    $$UPDATE public.fitting_purchase_mappings SET purchasing_sku='CHANGED'$$,
    '42501','documentary_evidence_immutable','authority rows are immutable on update');
SELECT throws_ok(
    $$DELETE FROM public.fitting_purchase_mappings$$,
    '42501','documentary_evidence_immutable','authority rows are immutable on delete');

ROLLBACK;
