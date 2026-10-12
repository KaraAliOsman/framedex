BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path=public,extensions,pg_temp;
SELECT plan(18);
SELECT has_table('public','quotation_previews','private document reviews exist');
SELECT has_table('public','quotation_issues','issuance has an immutable receipt');
SELECT has_table('public','quote_link_deadlines','access deadlines are independent evidence');
SELECT has_table('public','quote_link_regenerations','regeneration has a recovery receipt');
SELECT ok((SELECT bool_and(relrowsecurity) FROM pg_class
  WHERE oid=ANY(ARRAY['quotation_previews'::regclass,'quotation_issues'::regclass,
    'quote_link_deadlines'::regclass,'quote_link_regenerations'::regclass])),'every new tenant table has RLS');
SELECT ok((SELECT bool_and(NOT has_table_privilege('anon',name,'SELECT'))
  FROM unnest(ARRAY['quotation_previews','quotation_issues','quote_link_deadlines','quote_link_regenerations']) name),'anonymous readers cannot query review evidence');
SELECT ok((SELECT bool_and(NOT has_table_privilege('authenticated',name,'SELECT'))
  FROM unnest(ARRAY['quotation_previews','quotation_issues','quote_link_deadlines','quote_link_regenerations']) name),'members use the verified backend boundary');
SELECT ok((SELECT bool_and(NOT has_table_privilege('portal_backend',name,'SELECT'))
  FROM unnest(ARRAY['quotation_previews','quotation_issues','quote_link_regenerations']) name),'portal cannot query encrypted capabilities');
SELECT ok(has_table_privilege('portal_backend','quote_link_deadlines','SELECT'),'portal can read its RLS scoped deadline');
SELECT ok((SELECT bool_and(has_table_privilege('documentary_backend',name,'SELECT')
  AND has_table_privilege('documentary_backend',name,'INSERT'))
  FROM unnest(ARRAY['quotation_previews','quotation_issues','quote_link_deadlines','quote_link_regenerations']) name),'writer can append and recover evidence');
SELECT ok((SELECT bool_and(NOT has_table_privilege('documentary_backend',name,'UPDATE,DELETE'))
  FROM unnest(ARRAY['quotation_previews','quotation_issues','quote_link_deadlines','quote_link_regenerations']) name),'writer cannot rewrite or delete evidence');
SELECT has_trigger('public','quotation_previews','quotation_review_immutable','review identity and scope guarded');
SELECT has_trigger('public','quotation_issues','quotation_issue_immutable','receipt identity and scope guarded');
SELECT has_trigger('public','quote_link_deadlines','quote_link_deadlines_immutable','deadline authority is append only');
SELECT has_trigger('public','quote_link_regenerations','quote_link_regenerations_immutable','regeneration stays bound to the same sealed revision');
SELECT has_trigger('public','customer_approvals','document_approval_identity','P09 printed identity is still immutable');
SELECT ok(has_function_privilege('portal_backend','private.quote_link_expires_at(uuid,uuid,timestamptz)','EXECUTE'),'portal shares deadline authority');
SELECT ok((SELECT NOT p.prosecdef FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
  WHERE n.nspname='private' AND p.proname='quote_link_expires_at' AND p.pronargs=3),'deadline function preserves caller RLS');
SELECT * FROM finish();
ROLLBACK;
