-- Consolidation review fixes.
--
-- manufacturing_process_profiles holds org-owned routing authority in
-- addition to the global seeds (org_id NULL). A plain GRANT SELECT made every
-- tenant's private process declarations readable cross-tenant through
-- PostgREST; RLS scopes member reads to (org-owned ∪ global) like the other
-- authority tables. Members get read-only access — profiles are seeded or
-- admin-managed; writes go through service_role (BYPASSRLS).

BEGIN;

ALTER TABLE public.manufacturing_process_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY mpp_member_read ON public.manufacturing_process_profiles
    FOR SELECT TO public
    USING (org_id IS NULL OR org_id IN (SELECT private.current_user_org_ids()));

COMMIT;
