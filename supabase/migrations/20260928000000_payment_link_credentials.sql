-- Payment links carry the credential version they were dispatched with, so
-- rotating or disabling org credentials never strands an outstanding charge.
-- Append-only on top of 20260926000000_payment_links.sql.

ALTER TABLE public.project_payment_links
    ADD COLUMN flow_api_url TEXT,
    ADD COLUMN flow_api_key TEXT,
    ADD COLUMN flow_secret_key TEXT;

COMMENT ON COLUMN public.project_payment_links.flow_secret_key IS
    'Credential snapshot at dispatch time — write-only like org_payment_integrations; never serialized.';
