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

-- The public webhook resolves its own row by opaque link id (the id IS the
-- capability, same shape as the portal share token): a SECURITY DEFINER lookup
-- returns exactly that link with its credential snapshot, so direct table
-- reads stay org-scoped for every role — no cross-tenant USING(true) anywhere.
-- Lives here (not the credential migration) because the row's deal snapshot
-- columns only exist after 20261009010000.
CREATE FUNCTION private.payment_link_for_confirm(p_link_id UUID)
RETURNS TABLE (
    id UUID, org_id UUID, project_id UUID, operation_key TEXT, kind TEXT,
    amount NUMERIC, payer_email TEXT, subject TEXT, status TEXT,
    environment TEXT, flow_order TEXT, flow_token TEXT, url TEXT,
    project_payment_id UUID, deal_total NUMERIC, deal_currency TEXT,
    created_by UUID, created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ,
    flow_api_url TEXT, flow_api_key TEXT, flow_secret_key TEXT
)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = '' AS $$
    SELECT l.id, l.org_id, l.project_id, l.operation_key, l.kind, l.amount,
           l.payer_email, l.subject, l.status, l.environment, l.flow_order,
           l.flow_token, l.url, l.project_payment_id, l.deal_total,
           l.deal_currency, l.created_by, l.created_at, l.updated_at,
           c.flow_api_url, c.flow_api_key, c.flow_secret_key
    FROM public.project_payment_links l
    LEFT JOIN public.project_payment_link_credentials c ON c.link_id = l.id
    WHERE l.id = p_link_id
$$;
REVOKE ALL ON FUNCTION private.payment_link_for_confirm(UUID) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.payment_link_for_confirm(UUID) TO documentary_backend;
