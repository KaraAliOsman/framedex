-- Provenance v2: route_id resolves to a LIVE ai_routes row, but routes are
-- platform-mutable config — an edit would silently re-attribute historical
-- audits to a newer provider/model/prompt. ai_audit_provenance seals the
-- exact route configuration at invocation time, backend-only (billing_backend)
-- so sealed provider internals never reach tenant-readable surfaces.

CREATE TABLE public.ai_audit_provenance (
    audit_id UUID PRIMARY KEY
        REFERENCES public.ai_audit_logs(id) ON DELETE CASCADE,
    provider VARCHAR(40) NOT NULL,
    provider_model VARCHAR(120) NOT NULL,
    prompt_version VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.ai_audit_provenance ENABLE ROW LEVEL SECURITY;

CREATE POLICY ai_audit_provenance_backend ON public.ai_audit_provenance
    FOR ALL TO billing_backend
    USING (true) WITH CHECK (true);

GRANT SELECT, INSERT ON public.ai_audit_provenance TO billing_backend;
GRANT ALL ON public.ai_audit_provenance TO service_role;
REVOKE ALL ON public.ai_audit_provenance FROM anon, authenticated;

-- The audit table is immutable evidence, but retention expiry needs a narrow
-- controlled delete path: a session flag only the service_role purge function
-- sets, never a role grant. Organization teardown is intentionally still
-- refused — the same guarantee every other immutable evidence table gives.
CREATE FUNCTION private.reject_ai_audit_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
    IF TG_OP = 'DELETE'
        AND current_setting('dekopen.audit_purge', true) = 'on' THEN
        RETURN OLD;
    END IF;
    RAISE EXCEPTION 'ai_audit_immutable' USING ERRCODE = '42501';
END;
$$;
REVOKE ALL ON FUNCTION private.reject_ai_audit_mutation() FROM PUBLIC;

DROP TRIGGER IF EXISTS immutable_ai_audit_logs ON public.ai_audit_logs;
CREATE TRIGGER immutable_ai_audit_logs BEFORE UPDATE OR DELETE
ON public.ai_audit_logs
FOR EACH ROW EXECUTE FUNCTION private.reject_ai_audit_mutation();

CREATE FUNCTION private.purge_expired_ai_audit()
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    purged INTEGER;
BEGIN
    PERFORM set_config('dekopen.audit_purge', 'on', true);
    DELETE FROM public.ai_audit_logs WHERE retention_until < now();
    GET DIAGNOSTICS purged = ROW_COUNT;
    RETURN purged;
END;
$$;
REVOKE ALL ON FUNCTION private.purge_expired_ai_audit() FROM PUBLIC;
-- EXECUTE alone is not enough: qualified calls need schema USAGE too.
GRANT USAGE ON SCHEMA private TO service_role;
GRANT EXECUTE ON FUNCTION private.purge_expired_ai_audit() TO service_role;
