-- Human-confirmed tenant reference windows are append-only engineering evidence.
CREATE TABLE public.catalog_reference_windows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id),
    system_id UUID NOT NULL REFERENCES public.profile_systems(id),
    schema_version INTEGER NOT NULL DEFAULT 1 CHECK(schema_version=1),
    input JSONB NOT NULL CHECK(jsonb_typeof(input)='object'),
    expected_output JSONB NOT NULL CHECK(jsonb_typeof(expected_output)='object'),
    technical_hash TEXT NOT NULL CHECK(technical_hash ~ '^sha256:[0-9a-f]{64}$'),
    verified_by UUID NOT NULL,
    verified_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX catalog_reference_windows_series ON public.catalog_reference_windows(org_id,system_id,verified_at,id);
ALTER TABLE public.catalog_reference_windows ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.catalog_reference_windows FROM anon,authenticated;
GRANT SELECT ON public.catalog_reference_windows TO authenticated,catalog_backend;
GRANT INSERT ON public.catalog_reference_windows TO catalog_backend;
GRANT ALL ON public.catalog_reference_windows TO service_role;
CREATE POLICY catalog_reference_windows_read ON public.catalog_reference_windows FOR SELECT
    TO authenticated,catalog_backend USING(org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY catalog_reference_windows_insert ON public.catalog_reference_windows FOR INSERT
    TO catalog_backend WITH CHECK(private.can_manage_catalog(org_id) AND verified_by=COALESCE(
        NULLIF(current_setting('request.jwt.claim.sub',TRUE),''),
        NULLIF(current_setting('request.jwt.claims',TRUE),'')::jsonb->>'sub')::UUID);

CREATE FUNCTION private.guard_catalog_reference_window() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path='' AS $$
DECLARE actor UUID:=COALESCE(NULLIF(current_setting('request.jwt.claim.sub',TRUE),''),
    NULLIF(current_setting('request.jwt.claims',TRUE),'')::jsonb->>'sub')::UUID;
BEGIN
    IF NOT EXISTS(SELECT 1 FROM public.profile_systems s WHERE s.id=NEW.system_id AND s.org_id=NEW.org_id) THEN
        RAISE EXCEPTION 'catalog_reference_tenant_mismatch' USING ERRCODE='23514';
    END IF;
    IF current_user='catalog_backend' AND NEW.verified_by IS DISTINCT FROM actor THEN
        RAISE EXCEPTION 'catalog_reference_actor_required' USING ERRCODE='42501';
    END IF;
    RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION private.guard_catalog_reference_window() FROM PUBLIC;
CREATE TRIGGER guard_catalog_reference_window BEFORE INSERT ON public.catalog_reference_windows
    FOR EACH ROW EXECUTE FUNCTION private.guard_catalog_reference_window();
CREATE TRIGGER immutable_catalog_reference_window BEFORE UPDATE OR DELETE ON public.catalog_reference_windows
    FOR EACH ROW EXECUTE FUNCTION private.reject_immutable_evidence();
CREATE TRIGGER immutable_catalog_reference_window_truncate BEFORE TRUNCATE ON public.catalog_reference_windows
    FOR EACH STATEMENT EXECUTE FUNCTION private.reject_immutable_evidence();

ALTER TABLE public.catalog_series_setup
    ADD COLUMN wizard_step SMALLINT NOT NULL DEFAULT 1 CHECK(wizard_step BETWEEN 1 AND 5),
    ADD COLUMN wizard_state JSONB NOT NULL DEFAULT '{}' CHECK(jsonb_typeof(wizard_state)='object' AND octet_length(wizard_state::text)<=65536),
    ADD COLUMN progress_revision INTEGER NOT NULL DEFAULT 1 CHECK(progress_revision>0);
