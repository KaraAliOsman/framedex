SELECT m.id,m.order_id,m.movement_type::text AS kind,m.quantity,m.created_at,
 i.sku,i.name,i.unit,m.note
FROM public.inventory_movements m JOIN public.inventory_items i ON i.id=m.item_id AND i.org_id=m.org_id
WHERE m.org_id=%(org)s AND m.order_id IS NOT NULL AND m.movement_type IN ('CONSUMPTION','RETURN','SCRAP')
 AND (%(order_id)s::uuid IS NULL OR m.order_id=%(order_id)s::uuid)
ORDER BY m.created_at,m.id
