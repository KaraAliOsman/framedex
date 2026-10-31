BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path=public,private,auth,extensions,pg_temp;
SELECT plan(14);

-- Taller (one person), Pro (owner + two) and Empresa (every role).
INSERT INTO tenancy_organizations(id,name,tax_id,subscription_tier) VALUES
 ('26800000-0000-4000-8000-000000000001','Taller solo','E2E-268-A','STARTER'),
 ('26800000-0000-4000-8000-000000000002','Taller Pro','E2E-268-B','PRO'),
 ('26800000-0000-4000-8000-000000000003','Fábrica','E2E-268-C','BUSINESS');
INSERT INTO auth.users(id,email,email_confirmed_at) VALUES
 ('26800000-0000-4000-8000-00000000000a','solo@example.test',now()),
 ('26800000-0000-4000-8000-00000000000b','pro@example.test',now()),
 ('26800000-0000-4000-8000-00000000000c','fabrica@example.test',now()),
 ('26800000-0000-4000-8000-00000000000d','oficina@example.test',now());
INSERT INTO tenancy_memberships(id,org_id,user_id,role,is_active) VALUES
 ('26800000-0000-4000-8000-0000000000a1','26800000-0000-4000-8000-000000000001','26800000-0000-4000-8000-00000000000a','OWNER',true),
 ('26800000-0000-4000-8000-0000000000a2','26800000-0000-4000-8000-000000000001','26800000-0000-4000-8000-00000000000d','ESTIMATOR',false),
 ('26800000-0000-4000-8000-0000000000b1','26800000-0000-4000-8000-000000000002','26800000-0000-4000-8000-00000000000b','OWNER',true),
 ('26800000-0000-4000-8000-0000000000c1','26800000-0000-4000-8000-000000000003','26800000-0000-4000-8000-00000000000c','OWNER',true);

SET LOCAL ROLE authenticated;
SELECT set_config('request.jwt.claims','{"sub":"26800000-0000-4000-8000-00000000000a","role":"authenticated","aal":"aal2"}',TRUE);
SELECT set_config('request.jwt.claim.sub','26800000-0000-4000-8000-00000000000a',TRUE);
SELECT is((organization_plan('26800000-0000-4000-8000-000000000001')->>'seats')::int,1,'Taller is one person');
SELECT throws_ok($$SELECT create_company_invitation('26800000-0000-4000-8000-000000000001',gen_random_uuid(),'nuevo@example.test','OWNER',encode(sha256('d-268-1'::bytea),'hex'))$$,
 'company_plan_seats_full','Taller does not invite anyone');
SELECT throws_ok($$SELECT change_company_user('26800000-0000-4000-8000-000000000001','26800000-0000-4000-8000-0000000000a2','ESTIMATOR',true,
 (SELECT updated_at FROM tenancy_memberships WHERE id='26800000-0000-4000-8000-0000000000a2'))$$,
 'company_plan_seats_full','a deactivated person does not come back over the seat limit');
SELECT is(plan_allows('26800000-0000-4000-8000-000000000003','subagents'),false,'nobody reads the plan of a workshop they do not belong to');
SELECT throws_ok($$SELECT organization_plan('26800000-0000-4000-8000-000000000002')$$,'42501',NULL,'nor its seats');

SELECT set_config('request.jwt.claims','{"sub":"26800000-0000-4000-8000-00000000000b","role":"authenticated","aal":"aal2"}',TRUE);
SELECT set_config('request.jwt.claim.sub','26800000-0000-4000-8000-00000000000b',TRUE);
SELECT throws_ok($$SELECT create_company_invitation('26800000-0000-4000-8000-000000000002',gen_random_uuid(),'operario@example.test','OPERATOR',encode(sha256('d-268-2'::bytea),'hex'))$$,
 'company_plan_role_unavailable','Pro has no operator role');
SELECT lives_ok($$SELECT create_company_invitation('26800000-0000-4000-8000-000000000002',gen_random_uuid(),'oficina@example.test','ESTIMATOR',encode(sha256('d-268-3'::bytea),'hex'))$$,
 'Pro invites the office');
SELECT lives_ok($$SELECT create_company_invitation('26800000-0000-4000-8000-000000000002',gen_random_uuid(),'taller@example.test','WORKSHOP_MANAGER',encode(sha256('d-268-4'::bytea),'hex'))$$,
 'and the workshop');
SELECT throws_ok($$SELECT create_company_invitation('26800000-0000-4000-8000-000000000002',gen_random_uuid(),'cuarto@example.test','ESTIMATOR',encode(sha256('d-268-5'::bytea),'hex'))$$,
 'company_plan_seats_full','a live invitation already holds its seat');
SELECT is(organization_plan('26800000-0000-4000-8000-000000000002')->>'pending_invitations','2','the plan counts the seats held by invitations');
SELECT is(plan_allows('26800000-0000-4000-8000-000000000002','subagents'),false,'Pro does not delegate to subagents');

-- The plan shrinks while an invitation is out: accepting it is refused.
RESET ROLE;
UPDATE tenancy_organizations SET subscription_tier='STARTER' WHERE id='26800000-0000-4000-8000-000000000002';
SET LOCAL ROLE authenticated;
SELECT set_config('request.jwt.claims','{"sub":"26800000-0000-4000-8000-00000000000d","role":"authenticated","aal":"aal1"}',TRUE);
SELECT set_config('request.jwt.claim.sub','26800000-0000-4000-8000-00000000000d',TRUE);
SELECT throws_ok($$SELECT accept_company_invitation(encode(sha256('d-268-3'::bytea),'hex'))$$,'company_plan_role_unavailable',
 'an invitation does not outgrow a smaller plan');

SELECT set_config('request.jwt.claims','{"sub":"26800000-0000-4000-8000-00000000000c","role":"authenticated","aal":"aal2"}',TRUE);
SELECT set_config('request.jwt.claim.sub','26800000-0000-4000-8000-00000000000c',TRUE);
SELECT lives_ok($$SELECT create_company_invitation('26800000-0000-4000-8000-000000000003',gen_random_uuid(),'operario@example.test','OPERATOR',encode(sha256('d-268-6'::bytea),'hex'))$$,
 'Empresa invites every role');

RESET ROLE;
SET LOCAL ROLE portal_backend;
SELECT set_config('app.portal_org_id','26800000-0000-4000-8000-000000000001',TRUE);
SELECT is(portal_plan_features(),'[]'::jsonb,'the client of a Taller sees no 3D');
RESET ROLE;

SELECT * FROM finish();
ROLLBACK;
