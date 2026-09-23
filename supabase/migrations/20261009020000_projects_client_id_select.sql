-- Grant the tenant role SELECT on projects.client_id.
--
-- Tenant access to public.projects is granted per column: the 20261007 client
-- link migration added the column with INSERT/UPDATE privileges but no SELECT,
-- so every read that includes it (project_row, list_projects) was denied for
-- authenticated members.

GRANT SELECT (client_id) ON public.projects TO authenticated;
