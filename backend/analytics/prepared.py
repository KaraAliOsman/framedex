"""Saved draft quotations created by this member's verified AI work."""

from pricing.repository import rows


def prepared_quotations(org_id, user_id, role):
    if role not in {'OWNER', 'ESTIMATOR'}:
        return {'count': 0, 'items': []}
    # Stay authenticated: ai_jobs is private to its user as well as its org.
    # Compare text identities without casting arbitrary result JSON to UUID.
    found = rows(
        """
        SELECT p.id,p.code,p.name,p.current_revision
        FROM public.projects p
        WHERE p.org_id=%s AND p.status='DRAFT'
          AND NOT EXISTS(SELECT 1 FROM public.project_versions v WHERE v.org_id=p.org_id AND v.project_id=p.id)
          AND EXISTS(SELECT 1 FROM public.project_positions w WHERE w.org_id=p.org_id AND w.project_id=p.id)
          AND EXISTS(SELECT 1 FROM public.ai_jobs j WHERE j.org_id=p.org_id AND j.user_id=%s
            AND j.state NOT IN ('CANCELED','FAILED')
            AND j.result#>>'{created_project,project_id}'=p.id::text
            AND EXISTS(SELECT 1 FROM jsonb_array_elements(COALESCE(j.receipt->'objects','[]'::jsonb)) obj
              WHERE obj->>'kind'='project' AND obj->>'status'='applied' AND obj->>'id'=p.id::text))
        ORDER BY p.updated_at DESC,p.id
        """, [org_id, user_id],
    )
    return {'count': len(found), 'items': [
        {'project_id': str(item['id']), 'code': item['code'], 'name': item['name'],
         'href': f"/projects/{item['id']}?section=quote"} for item in found[:50]
    ]}
