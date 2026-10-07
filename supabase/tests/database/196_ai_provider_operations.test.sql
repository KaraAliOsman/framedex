BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT no_plan();

SELECT has_table('public',name,name || ' exists') FROM unnest(ARRAY['ai_settings','ai_capability_routes','ai_provider_usage','ai_usage_events']) name;
SELECT ok(relrowsecurity, relname || ' enforces RLS') FROM pg_class WHERE oid IN ('public.ai_settings'::regclass,'public.ai_capability_routes'::regclass,'public.ai_provider_usage'::regclass,'public.ai_usage_events'::regclass);
SELECT ok(NOT has_table_privilege('authenticated','public.' || name,'SELECT') AND NOT has_table_privilege('anon','public.' || name,'SELECT'),name || ' is private to the backend') FROM unnest(ARRAY['ai_settings','ai_capability_routes','ai_provider_usage','ai_usage_events']) name;
SELECT ok(has_table_privilege('billing_backend','public.' || name,'INSERT'),name || ' permits scoped backend insertion') FROM unnest(ARRAY['ai_settings','ai_capability_routes','ai_provider_usage','ai_usage_events']) name;
SELECT col_type_is('public','ai_provider_usage','estimated_cost_usd','numeric(30,14)','smallest accepted tariff preserves its Decimal cost');
SELECT col_type_is('public','ai_capability_routes','input_usd_per_million','numeric(18,8)','tariff is Decimal');
SELECT has_column('public','job_runs','phase','live worker phase uses the existing polling channel');
SELECT ok(NOT EXISTS(SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name IN ('ai_provider_usage','ai_usage_events') AND column_name IN ('prompt','output','headers','api_key','goal','url')),'physical ledger has no content or credentials');
SELECT ok(NOT EXISTS(SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name IN ('ai_capability_routes','ai_provider_usage') AND data_type IN ('real','double precision')),'monetary metadata never uses float');
SELECT ok(NOT has_table_privilege('billing_backend','public.ai_usage_events','UPDATE') AND NOT has_table_privilege('billing_backend','public.ai_usage_events','DELETE'),'tool events are append-only to their writer');

INSERT INTO public.tenancy_organizations(id,name,tax_id) VALUES
('a3000000-0000-4000-8000-000000000001','Provider operations A','IA3-A'),
('a3000000-0000-4000-8000-000000000002','Provider operations B','IA3-B');
INSERT INTO public.ai_settings(org_id,monthly_budget_credits) VALUES
('a3000000-0000-4000-8000-000000000001',5),('a3000000-0000-4000-8000-000000000002',7);
INSERT INTO public.ai_provider_usage(id,org_id,user_id,operation_key,input_hash,capability,provider,provider_model,credits_reserved,status,tokens_prompt,tokens_completion,estimated_cost_usd)
VALUES('a3000000-0000-4000-8000-000000000010','a3000000-0000-4000-8000-000000000001','a3000000-0000-4000-8000-000000000003','fixture',repeat('a',64),'agent','MIMO','fixture',5,'FAILED',1,0,0.00000000000001);
SELECT is((SELECT estimated_cost_usd::text FROM public.ai_provider_usage WHERE operation_key='fixture'),'0.00000000000001','paid failures retain an exact minimal monetary cost');
SELECT throws_ok($$UPDATE public.ai_provider_usage SET tokens_prompt=0 WHERE operation_key='fixture'$$,'P0001','ai_provider_usage_immutable','failed physical exchanges are immutable');
SELECT throws_ok($$DELETE FROM public.ai_provider_usage WHERE operation_key='fixture'$$,'P0001','ai_provider_usage_immutable','physical exchanges cannot be deleted');
SELECT throws_ok($$INSERT INTO public.ai_usage_events(org_id,usage_id,tool_name,status) VALUES('a3000000-0000-4000-8000-000000000002','a3000000-0000-4000-8000-000000000010','calculate_position','OK')$$,'23503',NULL,'events cannot reference a foreign tenant exchange');
INSERT INTO public.ai_usage_events(org_id,usage_id,tool_name,status) VALUES('a3000000-0000-4000-8000-000000000001','a3000000-0000-4000-8000-000000000010','calculate_position','ERROR');
SELECT throws_ok($$UPDATE public.ai_usage_events SET status='OK'$$,'P0001','ai_usage_event_immutable','tool evidence is immutable');
SELECT throws_ok($$INSERT INTO public.ai_capability_routes(org_id,capability,provider,provider_model,input_usd_per_million) VALUES('a3000000-0000-4000-8000-000000000001','agent','MIMO','fixture',1.25)$$,'23514',NULL,'one-sided tariff is rejected');
SELECT throws_ok($$INSERT INTO public.ai_capability_routes(org_id,capability,provider,provider_model,retries) VALUES('a3000000-0000-4000-8000-000000000001','agent','MIMO','fixture',3)$$,'23514',NULL,'retry ceiling is two');
SELECT throws_ok($$UPDATE public.ai_settings SET monthly_budget_credits=-1$$,'23514',NULL,'negative budgets are rejected');

CREATE TEMP TABLE ai_scope_reads(budgets INT,exchanges INT,events INT,foreign_updates INT);
GRANT INSERT ON ai_scope_reads TO billing_backend;
SET LOCAL ROLE billing_backend;
SELECT set_config('app.billing_org','a3000000-0000-4000-8000-000000000001',true);
WITH changed AS (UPDATE public.ai_settings SET monthly_budget_credits=100 WHERE org_id='a3000000-0000-4000-8000-000000000002' RETURNING org_id)
INSERT INTO ai_scope_reads SELECT (SELECT count(*) FROM public.ai_settings),(SELECT count(*) FROM public.ai_provider_usage),(SELECT count(*) FROM public.ai_usage_events),(SELECT count(*) FROM changed);
RESET ROLE;
SELECT is((SELECT budgets FROM ai_scope_reads),1,'backend scope sees only its budget');
SELECT is((SELECT exchanges FROM ai_scope_reads),1,'backend scope sees only its exchanges');
SELECT is((SELECT events FROM ai_scope_reads),1,'backend scope sees only its executed tool events');
SELECT is((SELECT foreign_updates FROM ai_scope_reads),0,'foreign update has no visible row');
SELECT is((SELECT monthly_budget_credits FROM public.ai_settings WHERE org_id='a3000000-0000-4000-8000-000000000002'),7,'foreign budget remains unchanged');
SELECT * FROM finish();
ROLLBACK;
