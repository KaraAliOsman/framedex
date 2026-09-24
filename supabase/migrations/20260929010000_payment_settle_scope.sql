-- The verified settlement runs inside the billing scope pinned to the org:
-- every object the settle path touches must carry billing policies, or the
-- public Flow callback rolls the ledger write back. Grants mirror the
-- documentary_backend coverage the same path uses under an authenticated
-- request; policies pin every row to the server's billing org GUC.

GRANT SELECT ON public.projects TO billing_backend;
GRANT SELECT ON public.project_versions TO billing_backend;
GRANT SELECT ON public.tenancy_organizations TO billing_backend;
GRANT SELECT, INSERT ON public.payment_receipts TO billing_backend;
GRANT EXECUTE ON FUNCTION private.applied_pricing_currency(uuid, uuid)
    TO billing_backend;

CREATE POLICY billing_backend_scope ON public.projects
    FOR ALL TO billing_backend
    USING (private.billing_scope(org_id)) WITH CHECK (private.billing_scope(org_id));
CREATE POLICY billing_backend_restrict ON public.projects
    AS RESTRICTIVE FOR ALL TO billing_backend
    USING (private.billing_scope(org_id)) WITH CHECK (private.billing_scope(org_id));

CREATE POLICY billing_backend_scope ON public.project_versions
    FOR ALL TO billing_backend
    USING (private.billing_scope(org_id)) WITH CHECK (private.billing_scope(org_id));
CREATE POLICY billing_backend_restrict ON public.project_versions
    AS RESTRICTIVE FOR ALL TO billing_backend
    USING (private.billing_scope(org_id)) WITH CHECK (private.billing_scope(org_id));

-- tenancy_organizations is keyed by the org's own id, not an org_id column.
CREATE POLICY billing_backend_scope ON public.tenancy_organizations
    FOR ALL TO billing_backend
    USING (private.billing_scope(id)) WITH CHECK (private.billing_scope(id));
CREATE POLICY billing_backend_restrict ON public.tenancy_organizations
    AS RESTRICTIVE FOR ALL TO billing_backend
    USING (private.billing_scope(id)) WITH CHECK (private.billing_scope(id));

CREATE POLICY billing_backend_scope ON public.payment_receipts
    FOR ALL TO billing_backend
    USING (private.billing_scope(org_id)) WITH CHECK (private.billing_scope(org_id));
CREATE POLICY billing_backend_restrict ON public.payment_receipts
    AS RESTRICTIVE FOR ALL TO billing_backend
    USING (private.billing_scope(org_id)) WITH CHECK (private.billing_scope(org_id));
