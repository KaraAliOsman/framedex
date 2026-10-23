BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path=public,private,auth,extensions,pg_temp;
SELECT plan(11);

SELECT ok(NOT has_function_privilege('anon','private.create_own_workshop(text)','EXECUTE'),'Anonymous visitors cannot create workshops');
SELECT ok(has_function_privilege('authenticated','private.create_own_workshop(text)','EXECUTE'),'A signed-in person may create their first workshop');
SELECT ok(NOT has_table_privilege('authenticated','public.tenancy_organizations','INSERT'),'Organizations are never inserted directly by the browser');

INSERT INTO auth.users(id,email,email_confirmed_at) VALUES
 ('26200000-0000-4000-8000-000000000001','nuevo@taller.test',now()),
 ('26200000-0000-4000-8000-000000000002','sin-confirmar@taller.test',NULL);

SET LOCAL ROLE authenticated;
SELECT set_config('request.jwt.claim.sub','26200000-0000-4000-8000-000000000002',true);
SELECT throws_ok($$SELECT private.create_own_workshop('Taller sin correo')$$,'42501','workshop_identity_required','An unconfirmed email cannot create a workshop');

SELECT set_config('request.jwt.claim.sub','26200000-0000-4000-8000-000000000001',true);
SELECT throws_ok($$SELECT private.create_own_workshop(' x ')$$,'P0001','workshop_name_invalid','A workshop needs a real name');
SELECT lives_ok($$SELECT private.create_own_workshop('  Ventanas del Sur  ')$$,'A confirmed person creates their workshop');
SELECT throws_ok($$SELECT private.create_own_workshop('Segundo taller')$$,'P0001','workshop_membership_exists','A person creates a workshop only once');
RESET ROLE;

SELECT is((SELECT o.name::text FROM public.tenancy_organizations o JOIN public.tenancy_memberships m ON m.org_id=o.id
  WHERE m.user_id='26200000-0000-4000-8000-000000000001'),'Ventanas del Sur','The name is stored trimmed');
SELECT is((SELECT m.role::text||'/'||m.is_active::text FROM public.tenancy_memberships m
  WHERE m.user_id='26200000-0000-4000-8000-000000000001'),'OWNER/true','The creator owns the workshop');
SELECT is((SELECT o.country||'/'||o.currency::text||'/'||o.subscription_tier::text FROM public.tenancy_organizations o
  JOIN public.tenancy_memberships m ON m.org_id=o.id WHERE m.user_id='26200000-0000-4000-8000-000000000001'),
  'CL/CLP/TRIAL','A new workshop starts in Chile, in pesos, on a live trial');
SELECT is((SELECT count(*)::integer FROM public.organization_admin_events e JOIN public.tenancy_memberships m ON m.org_id=e.org_id
  WHERE m.user_id='26200000-0000-4000-8000-000000000001' AND e.action='CREATE_WORKSHOP'),1,'The creation is evidence');

SELECT * FROM finish();
ROLLBACK;
