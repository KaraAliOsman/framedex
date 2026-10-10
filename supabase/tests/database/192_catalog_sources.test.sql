BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
-- Test-only access: the transaction rolls back this grant with the fixture.
GRANT USAGE ON SCHEMA extensions TO catalog_backend;
SET LOCAL search_path=public,private,auth,extensions,pg_temp;
SELECT plan(16);
SELECT has_table('public','catalog_import_events','import timeline is durable');
SELECT has_column('public','catalog_parameter_evidence','canonical_value','evidence retains complete typed value');
SELECT has_column('public','catalog_parameter_evidence','source_import_id','evidence pins original import');
SELECT ok(NOT has_table_privilege('authenticated','public.catalog_import_events','INSERT'),'member cannot forge import history');
SELECT ok(NOT has_column_privilege('authenticated','public.profile_articles','technical_reviewed_at','UPDATE'),'member cannot self-certify an article');

INSERT INTO public.tenancy_organizations(id,name,tax_id) VALUES
('a1600000-0000-4000-8000-000000000001','P16 A','P16-A'),
('a1600000-0000-4000-8000-000000000002','P16 B','P16-B');
INSERT INTO public.tenancy_memberships(org_id,user_id,role) VALUES
('a1600000-0000-4000-8000-000000000001','a1600000-0000-4000-8000-000000000011','WORKSHOP_MANAGER'),
('a1600000-0000-4000-8000-000000000001','a1600000-0000-4000-8000-000000000012','ESTIMATOR'),
('a1600000-0000-4000-8000-000000000002','a1600000-0000-4000-8000-000000000013','WORKSHOP_MANAGER');
INSERT INTO public.catalog_imports(id,org_id,file_name,kind,storage_path,created_by,status,candidates) VALUES
('a1600000-0000-4000-8000-000000000021','a1600000-0000-4000-8000-000000000001','original.pdf','PDF','p16/a.pdf','a1600000-0000-4000-8000-000000000011','REVIEW_READY','[]'),
('a1600000-0000-4000-8000-000000000022','a1600000-0000-4000-8000-000000000002','foreign.pdf','PDF','p16/b.pdf','a1600000-0000-4000-8000-000000000013','REVIEW_READY','[]');
SELECT is((SELECT count(*)::integer FROM public.catalog_import_events WHERE import_id='a1600000-0000-4000-8000-000000000021'),1,'state transition is recorded by the database');
SELECT throws_ok($$UPDATE public.catalog_imports SET file_name='replacement.pdf' WHERE id='a1600000-0000-4000-8000-000000000021'$$,'23514','catalog_import_source_immutable','original metadata cannot be rewritten');
SELECT throws_ok($$UPDATE public.catalog_imports SET candidates='[{"forged":true}]' WHERE id='a1600000-0000-4000-8000-000000000021'$$,'23514','catalog_import_source_immutable','stored extraction cannot be rewritten after review');

INSERT INTO public.catalog_parameter_evidence(id,org_id,authority_table,row_id,field_name,value_text,source_document,source_import_id,declared_by)
VALUES('a1600000-0000-4000-8000-000000000031','a1600000-0000-4000-8000-000000000001','catalog_imports','a1600000-0000-4000-8000-000000000021','depth_mm','60.01','original.pdf','a1600000-0000-4000-8000-000000000021','a1600000-0000-4000-8000-000000000011');
SELECT throws_ok($$UPDATE public.catalog_parameter_evidence SET value_text='60' WHERE id='a1600000-0000-4000-8000-000000000031'$$,'23514','catalog_evidence_immutable','source value cannot be silently corrected');
SELECT throws_ok($$DELETE FROM public.catalog_parameter_evidence WHERE id='a1600000-0000-4000-8000-000000000031'$$,'23514','catalog_evidence_immutable','evidence cannot disappear after publication or undo');
SELECT throws_ok($$UPDATE public.catalog_import_events SET action='PUBLISH' WHERE import_id='a1600000-0000-4000-8000-000000000021'$$,'42501','documentary_evidence_immutable','timeline is immutable');

SET LOCAL ROLE authenticated;
SELECT set_config('request.jwt.claims','{"sub":"a1600000-0000-4000-8000-000000000011","role":"authenticated"}',TRUE);
SELECT set_config('request.jwt.claim.sub','a1600000-0000-4000-8000-000000000011',TRUE);
SELECT is((SELECT count(*)::integer FROM public.catalog_import_events WHERE import_id IN ('a1600000-0000-4000-8000-000000000021','a1600000-0000-4000-8000-000000000022')),1,'timeline keeps tenant isolation');
SET LOCAL ROLE catalog_backend;
SELECT throws_ok($$UPDATE public.catalog_parameter_evidence SET review_state='REVIEWED',reviewed_by='a1600000-0000-4000-8000-000000000012',reviewed_at=now() WHERE id='a1600000-0000-4000-8000-000000000031'$$,'42501','catalog_evidence_reviewer_required','reviewer cannot impersonate another member');
SELECT lives_ok($$UPDATE public.catalog_parameter_evidence SET review_state='REVIEWED',reviewed_by='a1600000-0000-4000-8000-000000000011',reviewed_at=now() WHERE id='a1600000-0000-4000-8000-000000000031'$$,'technical reviewer can attest with their identity');
SELECT throws_ok($$UPDATE public.catalog_parameter_evidence SET review_state='REJECTED',reviewed_by='a1600000-0000-4000-8000-000000000011',reviewed_at=now() WHERE id='a1600000-0000-4000-8000-000000000031'$$,'23514','catalog_evidence_immutable','reviewed attestation is immutable');
RESET ROLE;
SELECT set_config('request.jwt.claims','{"sub":"a1600000-0000-4000-8000-000000000012","role":"authenticated"}',TRUE);
SELECT set_config('request.jwt.claim.sub','a1600000-0000-4000-8000-000000000012',TRUE);
SET LOCAL ROLE catalog_backend;
SELECT throws_ok($$INSERT INTO public.catalog_parameter_evidence(org_id,authority_table,row_id,field_name,source_document,declared_by,review_state,reviewed_by,reviewed_at) VALUES('a1600000-0000-4000-8000-000000000001','catalog_imports','a1600000-0000-4000-8000-000000000021','depth_mm','forged.pdf','a1600000-0000-4000-8000-000000000012','REVIEWED','a1600000-0000-4000-8000-000000000012',now())$$,'42501','catalog_evidence_reviewer_required','member cannot self-certify through the backend role');
RESET ROLE;
SELECT * FROM finish();
ROLLBACK;
