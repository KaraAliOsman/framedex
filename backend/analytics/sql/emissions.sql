SELECT v.id, v.project_id, p.code, p.name, p.status::text AS phase, p.current_revision,
 v.revision_code, v.emitted_at, v.emitted_by,
 COALESCE(d.kind,a.status,'PENDING') AS decision,
 COALESCE(d.decided_at,a.decided_at) AS decided_at,
 COALESCE(d.note,a.decided_note) AS rejection_note,
 selected.id AS selected_version_id, selected.revision_code AS selected_revision,
 jsonb_build_object(
  'project',jsonb_build_object('currency',selected.snapshot_json->'project'->'currency',
   'total_price_net',selected.snapshot_json->'project'->'total_price_net',
   'total_price_gross',selected.snapshot_json->'project'->'total_price_gross'),
  'positions',(SELECT jsonb_agg(jsonb_build_object('id',p->'id','position_index',p->'position_index',
    'typology',p->'typology','is_demo',p->'is_demo'))
   FROM jsonb_array_elements(COALESCE(selected.snapshot_json->'positions','[]'::jsonb)) p),
  'pricing',jsonb_build_object('applied_total_cost_net',selected.snapshot_json->'pricing'->'applied_total_cost_net',
   'result',jsonb_build_object('workspace',jsonb_build_object(
    'cascade',(selected.snapshot_json->'pricing'->'result'->'workspace'->'cascade')-'traces',
    'positions',(SELECT jsonb_agg(jsonb_build_object('position_index',p->'position_index','cascade',(p->'cascade')-'traces'))
     FROM jsonb_array_elements(COALESCE(selected.snapshot_json->'pricing'->'result'->'workspace'->'positions','[]'::jsonb)) p)
   )))) AS snapshot_json,
 v.snapshot_json->'pricing'->>'requested_by' AS estimator_id,
 (v.emitted_at AT TIME ZONE z.timezone)::date AS emitted_on
FROM public.project_versions v
JOIN public.projects p ON p.id=v.project_id AND p.org_id=v.org_id
JOIN public.tenancy_organizations z ON z.id=v.org_id
LEFT JOIN LATERAL (
 SELECT * FROM private.analytics_choices(v.org_id) c
 WHERE c.offering_version_id=v.id ORDER BY c.decided_at DESC LIMIT 1
) d ON true
LEFT JOIN LATERAL (
 SELECT ca.status,ca.decided_at,ca.decided_note FROM public.customer_approvals ca
 WHERE ca.org_id=v.org_id AND ca.project_version_id=v.id AND ca.status IN ('APPROVED','DECLINED','CHANGES_REQUESTED')
 ORDER BY (ca.status='APPROVED') DESC,ca.decided_at DESC,ca.id LIMIT 1
) a ON true
JOIN public.project_versions selected ON selected.org_id=v.org_id
 AND selected.id=CASE WHEN d.kind='APPROVED' THEN d.selected_version_id ELSE v.id END
WHERE v.org_id=%(org)s AND (v.emitted_at AT TIME ZONE z.timezone)::date BETWEEN %(start)s AND %(end)s
ORDER BY v.emitted_at,v.id
