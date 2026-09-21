BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;
SET LOCAL search_path=public,extensions;
SELECT plan(12);

SELECT ok(NOT has_table_privilege('authenticated','public.payments','INSERT'), 'client cannot invent payments');
SELECT ok(NOT has_table_privilege('authenticated','public.payments','UPDATE'), 'client cannot mark paid');
SELECT ok(NOT has_table_privilege('authenticated','public.subscriptions','INSERT'), 'client cannot subscribe itself');
SELECT ok(NOT has_table_privilege('authenticated','public.subscriptions','UPDATE'), 'client cannot change entitlements');
SELECT ok(NOT has_table_privilege('authenticated','public.payment_customers','INSERT'), 'client cannot select provider customer');
SELECT ok(NOT has_table_privilege('authenticated','public.credit_ledger','INSERT'), 'client cannot grant credits');
SELECT ok(NOT has_table_privilege('authenticated','public.tenancy_organizations','UPDATE'), 'client cannot change organization balance');
SELECT ok(NOT has_table_privilege('authenticated','public.payment_events','INSERT'), 'event log remains server only');

INSERT INTO public.tenancy_organizations(id,name,tax_id) VALUES
 ('11111111-1111-4111-8111-111111111111','Billing A','A'),
 ('22222222-2222-4222-8222-222222222222','Billing B','B');
INSERT INTO public.tenancy_memberships(org_id,user_id,role) VALUES
 ('11111111-1111-4111-8111-111111111111','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','OWNER'),
 ('11111111-1111-4111-8111-111111111111','bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb','ESTIMATOR');
INSERT INTO public.payments(org_id,provider,provider_payment_id,amount,currency) VALUES
 ('11111111-1111-4111-8111-111111111111','flow','owner-payment',1,'CLP'),
 ('22222222-2222-4222-8222-222222222222','flow','other-payment',1,'CLP');
SET LOCAL ROLE authenticated;
SELECT set_config('request.jwt.claim.sub','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',true);
SELECT set_config('request.jwt.claims','{"sub":"aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa","role":"authenticated","aal":"aal2"}',true);
SELECT is((SELECT count(*) FROM public.payments),1::bigint,'OWNER aal2 sees only own payments');
SELECT set_config('request.jwt.claims','{"sub":"aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa","role":"authenticated","aal":"aal1"}',true);
SELECT is((SELECT count(*) FROM public.payments),0::bigint,'OWNER aal1 cannot read billing through direct SQL');
SELECT set_config('request.jwt.claim.sub','bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',true);
SELECT set_config('request.jwt.claims','{"sub":"bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb","role":"authenticated","aal":"aal2"}',true);
SELECT is((SELECT count(*) FROM public.payments),0::bigint,'ESTIMATOR aal2 cannot read billing');
RESET ROLE;
SELECT throws_ok($$INSERT INTO public.payments(org_id,provider,provider_payment_id,amount,currency)
 VALUES('11111111-1111-4111-8111-111111111111','flow','fractional',1.50,'CLP')$$,
 '23514',NULL,'fractional final CLP is rejected by database');
SELECT * FROM finish();
ROLLBACK;
