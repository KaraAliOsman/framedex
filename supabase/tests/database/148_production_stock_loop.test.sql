BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SET LOCAL search_path = public, private, auth, extensions, pg_temp;
SELECT plan(8);

INSERT INTO public.tenancy_organizations (id, name, tax_id)
VALUES ('00000000-0000-0000-0000-000000000001', 'PGTAP Stock Org', 'S-1');
INSERT INTO public.projects(id, org_id, code, name, client_name, created_by)
VALUES ('00000000-0000-0000-0000-000000000011',
        '00000000-0000-0000-0000-000000000001', 'P-S', 'pgtap', 'pgtap',
        '00000000-0000-0000-0000-000000000009');
-- The org guard requires a real producing order behind every movement.
INSERT INTO public.orders(id, org_id, project_id, order_type, order_code, payload_json)
VALUES
    ('00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001',
     '00000000-0000-0000-0000-000000000011', 'WORKSHOP_OT', 'OT-S', '{}'::jsonb),
    ('00000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000001',
     '00000000-0000-0000-0000-000000000011', 'WORKSHOP_OT', 'OT-T', '{}'::jsonb),
    ('00000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000001',
     '00000000-0000-0000-0000-000000000011', 'WORKSHOP_OT', 'OT-U', '{}'::jsonb);

SELECT has_view('public', 'inventory_stock', 'derived stock view exists');
SELECT has_index('public', 'inventory_movements',
    'inventory_movements_order_type_idx',
    'reservation/consumption lookups by producing order are indexed');

-- §10 ledger semantics: a CONSUMPTION satisfies the reservation it was held
-- under — reserved_qty must drop alongside on_hand_qty, so consumed material
-- can never look simultaneously gone AND still held for production.
INSERT INTO public.inventory_items(org_id, sku, name, category, unit, variant_key)
VALUES ('00000000-0000-0000-0000-000000000001', 'PGTAP-STOCK', 'pgtap', 'PROFILE', 'BAR', '');
INSERT INTO public.inventory_movements(org_id, item_id, movement_type, quantity, order_id)
SELECT '00000000-0000-0000-0000-000000000001', id, 'RECEIPT', 10,
       '00000000-0000-0000-0000-000000000002'
FROM public.inventory_items WHERE sku = 'PGTAP-STOCK';
INSERT INTO public.inventory_movements(org_id, item_id, movement_type, quantity, order_id)
SELECT '00000000-0000-0000-0000-000000000001', id, 'RESERVATION', 4,
       '00000000-0000-0000-0000-000000000003'
FROM public.inventory_items WHERE sku = 'PGTAP-STOCK';

SELECT is(
    (SELECT reserved_qty FROM public.inventory_stock
      WHERE sku = 'PGTAP-STOCK')::numeric,
    4::numeric,
    'reservation holds stock against the producing order'
);
SELECT is(
    (SELECT on_hand_qty FROM public.inventory_stock
      WHERE sku = 'PGTAP-STOCK')::numeric,
    10::numeric,
    'reservation does not touch on-hand — only availability'
);

INSERT INTO public.inventory_movements(org_id, item_id, movement_type, quantity, order_id)
SELECT '00000000-0000-0000-0000-000000000001', id, 'CONSUMPTION', 4,
       '00000000-0000-0000-0000-000000000003'
FROM public.inventory_items WHERE sku = 'PGTAP-STOCK';

SELECT is(
    (SELECT reserved_qty FROM public.inventory_stock
      WHERE sku = 'PGTAP-STOCK')::numeric,
    0::numeric,
    'consumption settles the hold — nothing stays double-counted'
);
SELECT is(
    (SELECT on_hand_qty FROM public.inventory_stock
      WHERE sku = 'PGTAP-STOCK')::numeric,
    6::numeric,
    'consumption removes the material from stock'
);

INSERT INTO public.inventory_movements(org_id, item_id, movement_type, quantity, order_id)
SELECT '00000000-0000-0000-0000-000000000001', id, 'RESERVATION', 2,
       '00000000-0000-0000-0000-000000000004'
FROM public.inventory_items WHERE sku = 'PGTAP-STOCK';
INSERT INTO public.inventory_movements(org_id, item_id, movement_type, quantity, order_id)
SELECT '00000000-0000-0000-0000-000000000001', id, 'RELEASE', 2,
       '00000000-0000-0000-0000-000000000004'
FROM public.inventory_items WHERE sku = 'PGTAP-STOCK';

SELECT is(
    (SELECT reserved_qty FROM public.inventory_stock
      WHERE sku = 'PGTAP-STOCK')::numeric,
    0::numeric,
    'release frees a re-planned reservation fully'
);
SELECT is(
    (SELECT on_hand_qty FROM public.inventory_stock
      WHERE sku = 'PGTAP-STOCK')::numeric,
    6::numeric,
    'released stock returns to availability untouched'
);

SELECT * FROM finish();
ROLLBACK;
