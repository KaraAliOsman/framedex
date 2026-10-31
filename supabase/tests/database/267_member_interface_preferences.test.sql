BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path=public,private,auth,extensions,pg_temp;
SELECT plan(7);

SELECT ok(NOT has_table_privilege('authenticated','public.member_interface_preferences','DELETE'),
 'a person resets their interface by saving it, not by deleting rows');
SELECT ok(NOT has_table_privilege('anon','public.member_interface_preferences','SELECT'),
 'nobody signed out reads interface preferences');

INSERT INTO tenancy_organizations(id,name,tax_id) VALUES
 ('26700000-0000-4000-8000-000000000001','Taller A','E2E-267-A'),
 ('26700000-0000-4000-8000-000000000002','Taller B','E2E-267-B');
INSERT INTO tenancy_memberships(org_id,user_id,role) VALUES
 ('26700000-0000-4000-8000-000000000001','26700000-0000-4000-8000-000000000003','OWNER'),
 ('26700000-0000-4000-8000-000000000001','26700000-0000-4000-8000-000000000004','OPERATOR'),
 ('26700000-0000-4000-8000-000000000002','26700000-0000-4000-8000-000000000005','OWNER');

SET LOCAL ROLE authenticated;
SELECT set_config('request.jwt.claims','{"sub":"26700000-0000-4000-8000-000000000004","role":"authenticated","aal":"aal1"}',TRUE);
SELECT set_config('request.jwt.claim.sub','26700000-0000-4000-8000-000000000004',TRUE);
SELECT lives_ok($$INSERT INTO member_interface_preferences(org_id,user_id,preferences)
 VALUES('26700000-0000-4000-8000-000000000001','26700000-0000-4000-8000-000000000004','{"density":"workshop"}')$$,
 'an operator keeps their own workshop density');
SELECT throws_ok($$INSERT INTO member_interface_preferences(org_id,user_id,preferences)
 VALUES('26700000-0000-4000-8000-000000000001','26700000-0000-4000-8000-000000000003','{"text_size":"large"}')$$,
 '42501',NULL,'nobody changes another person''s interface, not even in the same workshop');
SELECT throws_ok($$INSERT INTO member_interface_preferences(org_id,user_id,preferences)
 VALUES('26700000-0000-4000-8000-000000000002','26700000-0000-4000-8000-000000000004','{}')$$,
 '42501',NULL,'nobody keeps preferences in a workshop they do not belong to');

SELECT set_config('request.jwt.claims','{"sub":"26700000-0000-4000-8000-000000000003","role":"authenticated","aal":"aal2"}',TRUE);
SELECT set_config('request.jwt.claim.sub','26700000-0000-4000-8000-000000000003',TRUE);
SELECT is((SELECT count(*)::integer FROM member_interface_preferences
  WHERE org_id='26700000-0000-4000-8000-000000000001'),0,'the owner does not read an operator''s interface');
RESET ROLE;
SELECT throws_ok($$INSERT INTO member_interface_preferences(org_id,user_id,preferences)
 VALUES('26700000-0000-4000-8000-000000000001','26700000-0000-4000-8000-000000000003','[]')$$,
 '23514',NULL,'preferences are always an object');

SELECT * FROM finish();
ROLLBACK;
