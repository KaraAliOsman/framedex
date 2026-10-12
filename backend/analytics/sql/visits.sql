SELECT v.id,v.code,v.project_id,v.project_version_id,v.kind,v.planned_on,v.status,v.context_json,
 min(e.created_at) FILTER(WHERE e.kind='RECEIVE') AS received_at,z.timezone
FROM public.field_visits v JOIN public.tenancy_organizations z ON z.id=v.org_id
LEFT JOIN public.field_events e ON e.org_id=v.org_id AND e.visit_id=v.id
WHERE v.org_id=%(org)s AND v.kind='INSTALLATION' AND v.planned_on BETWEEN %(start)s AND %(end)s
GROUP BY v.id,z.timezone ORDER BY v.planned_on,v.id
