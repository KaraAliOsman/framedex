-- §10: purchasing ↔ inventory ↔ production loop.
-- Reserved stock is consumed by production: once a CONSUMPTION movement lands
-- it satisfies the reservation it was held under, so reserved_qty must drop
-- too — otherwise consumed material would look both gone AND still held.
-- RESERVATION/RELEASE/CONSUMPTION movements all carry order_id (the work
-- order), item_id and the actor, so the loop stays ledger-traceable.

CREATE OR REPLACE VIEW public.inventory_stock
    WITH (security_invoker = true) AS
SELECT
    item.id AS item_id,
    item.org_id,
    item.sku,
    item.name,
    item.category,
    item.unit,
    item.variant_key,
    COALESCE(SUM(CASE
        WHEN movement.movement_type IN ('RECEIPT', 'RETURN', 'ADJUSTMENT')
            THEN movement.quantity
        WHEN movement.movement_type IN ('CONSUMPTION', 'SCRAP')
            THEN -movement.quantity
        ELSE 0
    END), 0)::NUMERIC(14, 2) AS on_hand_qty,
    COALESCE(SUM(CASE
        WHEN movement.movement_type = 'RESERVATION' THEN movement.quantity
        WHEN movement.movement_type IN ('RELEASE', 'CONSUMPTION')
            THEN -movement.quantity
        ELSE 0
    END), 0)::NUMERIC(14, 2) AS reserved_qty
FROM public.inventory_items item
LEFT JOIN public.inventory_movements movement
    ON movement.item_id = item.id
GROUP BY item.id, item.org_id, item.sku, item.name,
    item.category, item.unit, item.variant_key;

-- Reservation/consumption lookups are keyed by the producing order.
CREATE INDEX IF NOT EXISTS inventory_movements_order_type_idx
    ON public.inventory_movements (order_id, movement_type);
