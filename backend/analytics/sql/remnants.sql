SELECT r.id,r.kind,r.length_mm,r.width_mm,r.height_mm,r.origin_order_id,
 r.consumed_order_id,r.status,c.code,r.created_at
FROM public.inventory_remnants r LEFT JOIN public.entity_codes c ON c.org_id=r.org_id AND c.entity_id=r.id AND c.kind='RT'
WHERE r.org_id=%(org)s AND (%(order_id)s::uuid IS NULL OR r.origin_order_id=%(order_id)s::uuid OR r.consumed_order_id=%(order_id)s::uuid)
ORDER BY r.created_at,r.id
