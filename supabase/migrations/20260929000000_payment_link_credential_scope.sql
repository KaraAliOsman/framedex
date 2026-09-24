-- Payment-link credential snapshot moves behind the backend trust boundary: the
-- links table stays tenant-readable while the Flow credential version lives in a
-- backend-only table (the org_payment_integrations precedent). Adds billing-
-- scoped policies so the public Flow webhook settles inside an org-pinned
-- context — membership/JWT policies return nothing without request claims.

-- The link tenant must bind to the credential row's org_id — two independent
-- keys would let a row carry another tenant's link and authorize it under
-- the wrong billing scope.
ALTER TABLE public.project_payment_links
    ADD CONSTRAINT project_payment_links_id_org_key UNIQUE (id, org_id);

CREATE TABLE public.project_payment_link_credentials (
    link_id UUID PRIMARY KEY
        REFERENCES public.project_payment_links(id) ON DELETE CASCADE,
    org_id UUID NOT NULL
        REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    CONSTRAINT payment_link_credentials_link_org_fk
        FOREIGN KEY (link_id, org_id)
        REFERENCES public.project_payment_links (id, org_id)
        ON DELETE CASCADE,
    flow_api_url TEXT NOT NULL,
    flow_api_key TEXT NOT NULL,
    flow_secret_key TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO public.project_payment_link_credentials
    (link_id, org_id, flow_api_url, flow_api_key, flow_secret_key)
SELECT id, org_id, flow_api_url, flow_api_key, flow_secret_key
FROM public.project_payment_links
WHERE flow_api_url IS NOT NULL;

ALTER TABLE public.project_payment_links
    DROP COLUMN IF EXISTS flow_api_url,
    DROP COLUMN IF EXISTS flow_api_key,
    DROP COLUMN IF EXISTS flow_secret_key;

ALTER TABLE public.project_payment_link_credentials ENABLE ROW LEVEL SECURITY;

-- Credentials are backend-only, same trust level as org_payment_integrations.
REVOKE ALL ON public.project_payment_link_credentials FROM anon, authenticated;
GRANT SELECT, INSERT, UPDATE ON public.project_payment_link_credentials
    TO documentary_backend;
GRANT SELECT, INSERT, UPDATE ON public.project_payment_link_credentials
    TO billing_backend;
GRANT ALL ON public.project_payment_link_credentials TO service_role;

CREATE POLICY payment_link_credentials_backend ON public.project_payment_link_credentials
    FOR ALL TO documentary_backend
    USING (org_id IN (SELECT private.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY billing_backend_scope ON public.project_payment_link_credentials
    FOR ALL TO billing_backend
    USING (private.billing_scope(org_id)) WITH CHECK (private.billing_scope(org_id));
CREATE POLICY billing_backend_restrict ON public.project_payment_link_credentials
    AS RESTRICTIVE FOR ALL TO billing_backend
    USING (private.billing_scope(org_id)) WITH CHECK (private.billing_scope(org_id));

CREATE POLICY billing_backend_scope ON public.project_payment_links
    FOR ALL TO billing_backend
    USING (private.billing_scope(org_id)) WITH CHECK (private.billing_scope(org_id));
CREATE POLICY billing_backend_restrict ON public.project_payment_links
    AS RESTRICTIVE FOR ALL TO billing_backend
    USING (private.billing_scope(org_id)) WITH CHECK (private.billing_scope(org_id));

CREATE POLICY billing_backend_scope ON public.project_payments
    FOR ALL TO billing_backend
    USING (private.billing_scope(org_id)) WITH CHECK (private.billing_scope(org_id));
CREATE POLICY billing_backend_restrict ON public.project_payments
    AS RESTRICTIVE FOR ALL TO billing_backend
    USING (private.billing_scope(org_id)) WITH CHECK (private.billing_scope(org_id));

GRANT SELECT, INSERT, UPDATE ON public.project_payment_links TO billing_backend;
GRANT SELECT, INSERT, UPDATE ON public.project_payments TO billing_backend;

-- Terminal settles drop the in-flight snapshot inside the billing transaction —
-- the scoped DELETE is the whole reason the table exists, so billing_backend
-- gets DELETE here and nowhere else.
GRANT DELETE ON public.project_payment_link_credentials TO billing_backend;
