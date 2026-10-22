BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;
SET LOCAL search_path=public,extensions;
GRANT USAGE ON SCHEMA extensions TO pricing_backend;
SELECT plan(22);
SELECT ok((SELECT relrowsecurity FROM pg_class WHERE oid='workshop_pricing_policies'::regclass),'workshop policy has RLS');
SELECT ok(NOT has_table_privilege('anon','workshop_pricing_policies','SELECT'),'anonymous cannot read policy costs');
SELECT ok(NOT has_table_privilege('authenticated','workshop_pricing_policies','DELETE'),'policy deletion is unavailable');
INSERT INTO tenancy_organizations(id,name,tax_id) VALUES
 ('94000000-0000-4000-8000-000000000001','Simple pricing A','SIMPLE-POLICY-A'),
 ('94000000-0000-4000-8000-000000000002','Simple pricing B','SIMPLE-POLICY-B');
INSERT INTO tenancy_memberships(org_id,user_id,role) VALUES
 ('94000000-0000-4000-8000-000000000001','94100000-0000-4000-8000-000000000001','OWNER'),
 ('94000000-0000-4000-8000-000000000001','94100000-0000-4000-8000-000000000002','ESTIMATOR'),
 ('94000000-0000-4000-8000-000000000001','94100000-0000-4000-8000-000000000003','WORKSHOP_MANAGER'),
 ('94000000-0000-4000-8000-000000000001','94100000-0000-4000-8000-000000000004','INSTALLER');
SELECT set_config('app.pricing_reason','Prueba sintética de política',true);
SELECT set_config('request.jwt.claims','{"sub":"94100000-0000-4000-8000-000000000001","role":"authenticated","aal":"aal2"}',true);
SET LOCAL ROLE authenticated;
INSERT INTO workshop_pricing_policies(org_id,currency,labor_rate,labor_basis,installation_rate,installation_basis,margin,rounding_step,waste,tax_rate)
 VALUES('94000000-0000-4000-8000-000000000001','CLP',15000.1234,'M2',10000,'WINDOW',.35,1000,0,.19);
SELECT is((SELECT count(*) FROM workshop_pricing_policies),1::bigint,'owner reads own policy');
SELECT is((SELECT labor_rate FROM workshop_pricing_policies),15000.1234::numeric,'four decimals preserved');
SELECT is((SELECT revision FROM workshop_pricing_policies),1::bigint,'first revision is one');
SELECT throws_ok($$INSERT INTO workshop_pricing_policies(org_id,currency,labor_rate,labor_basis,installation_rate,installation_basis,margin,rounding_step,waste,tax_rate)
 VALUES('94000000-0000-4000-8000-000000000002','CLP',1,'M2',1,'M2',.35,1,0,.19)$$,'42501',NULL,'cannot insert in another tenant');
UPDATE workshop_pricing_policies SET margin=.40,revision=99;
SELECT is((SELECT revision FROM workshop_pricing_policies),2::bigint,'revision cannot be forged');
SELECT is((SELECT (old_record->>'margin')::numeric FROM price_audit_logs WHERE entity='workshop_pricing_policies' AND field='UPDATE'),.35::numeric,'old policy retained in audit');
SELECT is((SELECT actor_user_id FROM price_audit_logs WHERE entity='workshop_pricing_policies' AND field='UPDATE'),'94100000-0000-4000-8000-000000000001'::uuid,'verified policy actor');
SELECT throws_ok($$UPDATE workshop_pricing_policies SET rounding_step=.5$$,'23514',NULL,'CLP fractional rounding rejected');
SELECT throws_ok($$UPDATE workshop_pricing_policies SET labor_rate='NaN'$$,'23514',NULL,'nonfinite rate rejected');
SELECT throws_ok($$UPDATE workshop_pricing_policies SET org_id='94000000-0000-4000-8000-000000000002'$$,'23514',NULL,'tenant identity immutable');
SELECT set_config('app.pricing_reason','',true);
SELECT throws_ok($$UPDATE workshop_pricing_policies SET margin=.5$$,'23514',NULL,'audit reason required');
SELECT set_config('app.pricing_reason','Prueba sintética de política',true);
SELECT set_config('request.jwt.claims','{"sub":"94100000-0000-4000-8000-000000000002","role":"authenticated","aal":"aal2"}',true);
SELECT is((SELECT count(*) FROM workshop_pricing_policies),0::bigint,'estimator cannot read service costs');
WITH changed AS (UPDATE workshop_pricing_policies SET margin=.5 RETURNING id)
 SELECT is((SELECT count(*) FROM changed),0::bigint,'estimator cannot edit policy');
SET LOCAL ROLE pricing_backend;
SELECT is((SELECT count(*) FROM workshop_pricing_policies WHERE org_id='94000000-0000-4000-8000-000000000001'),1::bigint,'trusted calculator resolves estimator policy');
SELECT is((SELECT count(*) FROM workshop_pricing_policies WHERE org_id='94000000-0000-4000-8000-000000000002'),0::bigint,'calculator respects tenant scope');
SET LOCAL ROLE authenticated;
SELECT set_config('request.jwt.claims','{"sub":"94100000-0000-4000-8000-000000000003","role":"authenticated","aal":"aal2"}',true);
SELECT is((SELECT count(*) FROM workshop_pricing_policies),0::bigint,'manager cannot read owner policy');
SELECT set_config('request.jwt.claims','{"sub":"94100000-0000-4000-8000-000000000004","role":"authenticated","aal":"aal2"}',true);
SELECT is((SELECT count(*) FROM workshop_pricing_policies),0::bigint,'installer cannot read policy');
SELECT set_config('request.jwt.claims','{"sub":"94100000-0000-4000-8000-000000000001","role":"authenticated","aal":"aal1"}',true);
SELECT is((SELECT count(*) FROM workshop_pricing_policies),0::bigint,'owner policy requires MFA');
SELECT set_config('request.jwt.claims','{"sub":"94100000-0000-4000-8000-000000000001","role":"authenticated","aal":"aal2"}',true);
SELECT throws_ok($$UPDATE price_audit_logs SET reason='reescribir historia' WHERE entity='workshop_pricing_policies'$$,'42501',NULL,'policy audit is append only');
SELECT * FROM finish();
ROLLBACK;
