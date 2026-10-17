BEGIN;

-- Presentation declarations affect future snapshots only. No executable markup.
CREATE TABLE public.presentation_changes (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id),
 actor_id uuid NOT NULL,
 operation_key text NOT NULL CHECK(length(operation_key) BETWEEN 8 AND 200),
 request_hash text NOT NULL CHECK(request_hash ~ '^[a-f0-9]{64}$'),
 before_state jsonb NOT NULL CHECK(jsonb_typeof(before_state)='object'),
 after_state jsonb NOT NULL CHECK(jsonb_typeof(after_state)='object'),
 reverses_id uuid UNIQUE REFERENCES public.presentation_changes(id),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 UNIQUE(org_id,actor_id,operation_key)
);
ALTER TABLE public.presentation_changes ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.presentation_changes FROM PUBLIC,anon,authenticated;
GRANT SELECT ON public.presentation_changes TO authenticated;
GRANT SELECT,INSERT ON public.presentation_changes TO documentary_backend;
GRANT ALL ON public.presentation_changes TO service_role;
CREATE POLICY presentation_changes_owner ON public.presentation_changes
 USING(private.documentary_role(org_id,ARRAY['OWNER']) AND private.company_assurance(org_id))
 WITH CHECK(private.documentary_role(org_id,ARRAY['OWNER']) AND private.company_assurance(org_id) AND actor_id=auth.uid());
CREATE TRIGGER presentation_changes_immutable BEFORE UPDATE OR DELETE ON public.presentation_changes
 FOR EACH ROW EXECUTE FUNCTION private.client_evidence_immutable();
CREATE TRIGGER presentation_changes_no_truncate BEFORE TRUNCATE ON public.presentation_changes
 FOR EACH STATEMENT EXECUTE FUNCTION private.client_evidence_immutable();

COMMIT;
