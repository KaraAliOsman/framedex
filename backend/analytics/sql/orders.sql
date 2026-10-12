SELECT o.id,o.project_id,o.project_version_id,o.order_code AS code,o.status::text,
 o.expected_at,o.created_at,
 jsonb_build_object('position_id',o.payload_json->'position_id','remake_of',o.payload_json->'remake_of',
  'remake_reason',o.payload_json->'remake_reason','optimization',jsonb_build_object('bars',
   jsonb_build_object('metrics',o.payload_json->'optimization'->'bars'->'metrics',
    'workshop_cut_plan',(SELECT jsonb_agg(jsonb_build_object('stock_length_mm',b->'stock_length_mm'))
     FROM jsonb_array_elements(COALESCE(o.payload_json->'optimization'->'bars'->'workshop_cut_plan','[]'::jsonb)) b)))) AS payload_json,
 (o.created_at AT TIME ZONE z.timezone)::date AS created_on,
 min(e.created_at) FILTER(WHERE e.event='WO_COMPLETED') AS completed_at,
 z.timezone, r.id AS report_id,r.revision AS report_revision,
 r.evidence_json,r.result_json,r.source_fingerprint,r.source,r.reason,r.created_at AS reported_at
FROM public.orders o JOIN public.tenancy_organizations z ON z.id=o.org_id
LEFT JOIN public.production_step_events e ON e.org_id=o.org_id AND e.order_id=o.id
LEFT JOIN LATERAL(SELECT ar.* FROM public.production_actual_reports ar WHERE ar.org_id=o.org_id AND ar.order_id=o.id ORDER BY ar.revision DESC LIMIT 1) r ON true
WHERE o.org_id=%(org)s AND o.order_type='WORKSHOP_OT'
 AND (%(order_id)s::uuid IS NULL OR o.id=%(order_id)s::uuid)
GROUP BY o.id,z.timezone,r.id,r.revision,r.evidence_json,r.result_json,r.source_fingerprint,r.source,r.reason,r.created_at
ORDER BY o.created_at,o.id
