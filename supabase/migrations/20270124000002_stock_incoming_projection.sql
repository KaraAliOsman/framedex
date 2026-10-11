-- Stock readers need physical incoming quantities, never supplier-order prices.
CREATE FUNCTION private.stock_incoming(p_org uuid)
RETURNS TABLE(line_snapshot jsonb,open_qty numeric)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path='' AS $$
 SELECT jsonb_build_object(
   'purchasing_sku',l.line_snapshot->'purchasing_sku',
   'category',l.line_snapshot->'category',
   'unit',l.line_snapshot->'unit',
   'physical_stock_identity',l.line_snapshot->'physical_stock_identity',
   'specification',l.line_snapshot->'specification'
 ),l.quantity-COALESCE(r.received_qty,0)
 FROM public.order_requirement_lines l
 JOIN public.orders o ON o.id=l.order_id AND o.org_id=l.org_id
   AND o.status IN ('SENT','PARTIALLY_RECEIVED')
 LEFT JOIN (
   SELECT rl.order_line_id,SUM(rl.received_qty-rl.damaged_qty) AS received_qty
   FROM public.order_receipt_lines rl
   JOIN public.order_receipts receipt ON receipt.id=rl.receipt_id AND receipt.org_id=p_org
   GROUP BY rl.order_line_id
 ) r ON r.order_line_id=l.id
 WHERE l.org_id=p_org AND l.released_at IS NULL
   AND private.documentary_role(p_org,ARRAY['OWNER','ESTIMATOR','WORKSHOP_MANAGER'])
   AND private.company_assurance(p_org);
$$;
REVOKE ALL ON FUNCTION private.stock_incoming(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.stock_incoming(uuid) TO authenticated,documentary_backend;
