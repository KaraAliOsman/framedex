BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap WITH SCHEMA extensions;
SET LOCAL search_path=public,extensions;
SELECT plan(8);
SELECT ok((SELECT relrowsecurity FROM pg_class WHERE oid='project_working_prices'::regclass),'working prices have RLS');
SELECT ok(NOT has_table_privilege('anon','project_working_prices','SELECT'),'anonymous cannot read working costs');
SELECT ok(NOT has_table_privilege('authenticated','project_working_prices','SELECT'),'members cannot read private working snapshot directly');
SELECT ok(NOT has_table_privilege('authenticated','project_working_prices','INSERT'),'members cannot manufacture a working price');
SELECT ok(has_table_privilege('pricing_backend','project_working_prices','INSERT'),'trusted calculator can persist work');
SELECT ok(NOT has_table_privilege('pricing_backend','project_working_prices','DELETE'),'calculator cannot delete cached revision history');
SELECT ok(EXISTS(SELECT 1 FROM pg_trigger WHERE tgrelid='project_working_prices'::regclass
  AND tgname='working_price_guard' AND NOT tgisinternal),'draft and identity guard is attached');
SELECT ok(NOT pg_has_role('authenticated','pricing_backend','MEMBER'),'members cannot assume calculator role');
SELECT * FROM finish();
ROLLBACK;
