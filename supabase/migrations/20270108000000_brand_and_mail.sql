-- New emissions seal these preferences; historical snapshots remain untouched.
ALTER TABLE public.tenancy_organizations
  ADD COLUMN brand_primary_color text NOT NULL DEFAULT '#075F5A'
    CHECK (brand_primary_color ~ '^#[0-9A-Fa-f]{6}$'),
  ADD COLUMN document_attribution boolean NOT NULL DEFAULT false,
  ADD COLUMN portal_attribution boolean NOT NULL DEFAULT true,
  ADD COLUMN notification_email text,
  ADD COLUMN internal_mail_enabled boolean NOT NULL DEFAULT false;
GRANT SELECT (brand_primary_color, document_attribution, portal_attribution,
  notification_email, internal_mail_enabled) ON public.tenancy_organizations
  TO authenticated, documentary_backend;
GRANT UPDATE (brand_primary_color, document_attribution, portal_attribution,
  notification_email, internal_mail_enabled) ON public.tenancy_organizations TO documentary_backend;

-- A sealed encrypted message is an authority, delivery status is a projection.
CREATE TABLE public.mail_outbox (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id),
  event_key text NOT NULL,
  kind text NOT NULL CHECK (kind IN ('QUOTE','APPROVAL','PAYMENT','ORDER_BLOCKED')),
  recipient text NOT NULL,
  subject text NOT NULL,
  content_ciphertext text NOT NULL,
  project_id uuid REFERENCES public.projects(id),
  created_by uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  state text NOT NULL DEFAULT 'QUEUED'
    CHECK (state IN ('QUEUED','DISPATCHING','SENT','FAILED','UNCERTAIN')),
  attempt integer NOT NULL DEFAULT 0 CHECK (attempt >= 0),
  dispatch_started_at timestamptz,
  delivered_at timestamptz,
  error_code text,
  UNIQUE(org_id, event_key)
);
CREATE TABLE public.mail_attempts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id),
  mail_id uuid NOT NULL REFERENCES public.mail_outbox(id),
  attempt integer NOT NULL,
  event text NOT NULL CHECK (event IN ('DISPATCHING','SENT','FAILED','UNCERTAIN','REQUEUED')),
  actor_id uuid,
  error_code text,
  created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE public.mail_outbox ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mail_attempts ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.mail_outbox, public.mail_attempts FROM anon, authenticated;
GRANT SELECT (id,org_id,event_key,kind,recipient,subject,project_id,created_at,state,
  attempt,delivered_at,error_code) ON public.mail_outbox TO documentary_backend;
GRANT SELECT ON public.mail_attempts TO documentary_backend;
CREATE POLICY mail_outbox_read ON public.mail_outbox FOR SELECT TO documentary_backend
  USING (private.documentary_role(org_id, ARRAY['OWNER','ESTIMATOR','WORKSHOP_MANAGER']));
CREATE POLICY mail_attempts_read ON public.mail_attempts FOR SELECT TO documentary_backend
  USING (private.documentary_role(org_id, ARRAY['OWNER','ESTIMATOR','WORKSHOP_MANAGER']));
GRANT SELECT, INSERT, UPDATE ON public.mail_outbox TO service_role;
GRANT SELECT, INSERT ON public.mail_attempts TO service_role;
CREATE POLICY mail_outbox_service ON public.mail_outbox TO service_role
  USING (auth.jwt()->>'role'='service_role') WITH CHECK (auth.jwt()->>'role'='service_role');
CREATE POLICY mail_attempts_service ON public.mail_attempts TO service_role
  USING (auth.jwt()->>'role'='service_role') WITH CHECK (auth.jwt()->>'role'='service_role');

CREATE FUNCTION private.guard_mail_authority() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP='DELETE' OR (NEW.id,NEW.org_id,NEW.event_key,NEW.kind,NEW.recipient,NEW.subject,
    NEW.content_ciphertext,NEW.project_id,NEW.created_by,NEW.created_at)
    IS DISTINCT FROM (OLD.id,OLD.org_id,OLD.event_key,OLD.kind,OLD.recipient,OLD.subject,
    OLD.content_ciphertext,OLD.project_id,OLD.created_by,OLD.created_at) THEN
    RAISE EXCEPTION 'sealed_mail_immutable';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER mail_authority_immutable BEFORE UPDATE OR DELETE ON public.mail_outbox
  FOR EACH ROW EXECUTE FUNCTION private.guard_mail_authority();
CREATE FUNCTION private.guard_mail_attempt() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP <> 'INSERT' THEN RAISE EXCEPTION 'mail_attempt_immutable'; END IF;
  IF NOT EXISTS (SELECT 1 FROM public.mail_outbox WHERE id=NEW.mail_id AND org_id=NEW.org_id) THEN
    RAISE EXCEPTION 'mail_attempt_scope_mismatch';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER mail_attempt_immutable BEFORE INSERT OR UPDATE OR DELETE ON public.mail_attempts
  FOR EACH ROW EXECUTE FUNCTION private.guard_mail_attempt();
