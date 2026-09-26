-- Portal quote links returned 409 for every customer: portal_backend's own
-- policies are OR'd with the member-facing policies on the same tables
-- (project_payments, projects, …), and those predicates call
-- private.current_user_org_ids(), which the role could not EXECUTE — the
-- whole query errored instead of evaluating to "no member rows".
-- The function is SECURITY DEFINER and returns an empty set for a JWT-less
-- role, so the grant is safe: member policies yield false, portal policies
-- still gate on app.portal_org_id. Same grant the other backend roles have.
GRANT EXECUTE ON FUNCTION private.current_user_org_ids() TO portal_backend;
GRANT EXECUTE ON FUNCTION auth.uid() TO portal_backend;
