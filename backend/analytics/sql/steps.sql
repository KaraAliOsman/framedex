SELECT s.id,s.order_id,s.code,s.label,s.sequence,s.status,s.started_at,s.finished_at,
 CASE WHEN s.finished_at>=s.started_at THEN extract(epoch FROM(s.finished_at-s.started_at))/3600::numeric ELSE NULL END AS elapsed_hours
FROM public.production_steps s WHERE s.org_id=%(org)s
 AND (%(order_id)s::uuid IS NULL OR s.order_id=%(order_id)s::uuid) ORDER BY s.order_id,s.sequence
