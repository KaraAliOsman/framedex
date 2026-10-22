BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path=public,private,auth,extensions,pg_temp;
SELECT plan(9);
SELECT col_type_is('public','price_audit_logs','event_order','bigint','audit order uses an integer');
SELECT col_not_null('public','price_audit_logs','event_order','every audit entry has an order');
SELECT ok(NOT has_table_privilege('authenticated','public.price_audit_logs','INSERT'),'members cannot invent audit events');
SELECT ok(NOT has_table_privilege('authenticated','public.price_audit_logs','UPDATE'),'members cannot reorder history');
INSERT INTO public.tenancy_organizations(id,name,tax_id)
  VALUES('24900000-0000-4000-8000-000000000001','Price history order','PRICE-ORDER');
INSERT INTO public.cost_lists(id,org_id,supplier_name,currency,valid_from)
  VALUES('24900000-0000-4000-8000-000000000002','24900000-0000-4000-8000-000000000001','SYNTHETIC','CLP','2026-01-01');
INSERT INTO public.cost_list_items(id,org_id,cost_list_id,sku,item_type,unit,unit_cost)
  VALUES('24900000-0000-4000-8000-000000000003','24900000-0000-4000-8000-000000000001',
    '24900000-0000-4000-8000-000000000002','ORDER-BAR','SYNTHETIC','BAR',1.2345);
UPDATE public.cost_list_items SET unit_cost=0.0000
  WHERE id='24900000-0000-4000-8000-000000000003';
SELECT is((SELECT count(DISTINCT created_at)::int FROM public.price_audit_logs
  WHERE entity_id='24900000-0000-4000-8000-000000000003'),1,'transaction timestamps really tie');
SELECT is((SELECT new_value FROM public.price_audit_logs
  WHERE entity_id='24900000-0000-4000-8000-000000000003'
  ORDER BY created_at DESC,event_order DESC LIMIT 1),0.0000::numeric,'latest exact price comes first');
SELECT is((SELECT count(DISTINCT event_order)::int FROM public.price_audit_logs
  WHERE entity_id='24900000-0000-4000-8000-000000000003'),2,'same-price history events have distinct order');
SELECT throws_ok($$UPDATE public.price_audit_logs SET event_order=event_order+1
  WHERE entity_id='24900000-0000-4000-8000-000000000003'$$,'428C9',NULL,'identity prevents manually assigning audit order');
SELECT throws_ok($$UPDATE public.price_audit_logs SET event_order=DEFAULT
  WHERE entity_id='24900000-0000-4000-8000-000000000003'$$,'42501',NULL,'privileged edits cannot reorder immutable history');
SELECT * FROM finish();
ROLLBACK;
