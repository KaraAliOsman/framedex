-- Clients hardening: org-scoped composite FK closes cross-tenant links at the
-- database layer, and writes move to the backend role so direct authenticated
-- access can't bypass the API's WRITE_ROLES.

ALTER TABLE public.clients
    ADD CONSTRAINT uk_clients_org_id UNIQUE (org_id, id);

ALTER TABLE public.projects
    DROP CONSTRAINT projects_client_id_fkey;
ALTER TABLE public.projects
    ADD CONSTRAINT fk_projects_client
    FOREIGN KEY (org_id, client_id)
    REFERENCES public.clients (org_id, id)
    ON DELETE SET NULL (client_id);

DROP POLICY clients_isolation ON public.clients;
CREATE POLICY clients_read ON public.clients
    FOR SELECT TO authenticated
    USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY clients_backend ON public.clients
    FOR ALL TO documentary_backend
    USING (org_id IN (SELECT private.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT private.current_user_org_ids()));

REVOKE INSERT, UPDATE, DELETE ON public.clients FROM authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.clients TO documentary_backend;
