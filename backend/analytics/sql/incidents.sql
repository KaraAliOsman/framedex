SELECT i.id,i.code,i.kind,i.status,i.position_id,i.unit_index,i.description,i.created_at,
 v.id AS visit_id,v.project_id,v.project_version_id,v.context_json,
 (SELECT p->>'typology' FROM public.project_versions sv,
   LATERAL jsonb_array_elements(COALESCE(sv.snapshot_json->'positions','[]'::jsonb)) p
   WHERE sv.id=v.project_version_id AND sv.org_id=v.org_id AND p->>'id'=i.position_id::text LIMIT 1) AS frozen_typology
FROM public.field_incidents i JOIN public.field_visits v ON v.org_id=i.org_id AND v.id=i.visit_id
JOIN public.tenancy_organizations z ON z.id=i.org_id
WHERE i.org_id=%(org)s AND (i.created_at AT TIME ZONE z.timezone)::date BETWEEN %(start)s AND %(end)s
ORDER BY i.created_at,i.id
