-- P11: explicit simulators, dated links and append-only actor provenance.
ALTER TABLE public.project_payments
  ADD COLUMN actor_label text,
  ADD COLUMN simulated boolean NOT NULL DEFAULT false;
CREATE OR REPLACE FUNCTION private.project_payments_void_only() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
BEGIN
  IF TG_OP='DELETE' THEN
    RAISE EXCEPTION 'project_payments_immutable' USING ERRCODE='42501';
  END IF;
  IF OLD.voided_at IS NOT NULL OR NEW.voided_at IS NULL
    OR (to_jsonb(NEW)-ARRAY['voided_at','voided_by','void_reason']) IS DISTINCT FROM
       (to_jsonb(OLD)-ARRAY['voided_at','voided_by','void_reason']) THEN
    RAISE EXCEPTION 'project_payments_void_only' USING ERRCODE='42501';
  END IF;
  RETURN NEW;
END $$;
CREATE FUNCTION private.collection_payment_actor() RETURNS trigger
LANGUAGE plpgsql SET search_path='' AS $$
BEGIN
  NEW.actor_label:=COALESCE(NEW.actor_label,
    NULLIF(current_setting('request.jwt.claims',true),'')::jsonb->>'email');
  RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION private.collection_payment_actor() FROM PUBLIC;
CREATE TRIGGER collection_payment_actor BEFORE INSERT ON public.project_payments
  FOR EACH ROW EXECUTE FUNCTION private.collection_payment_actor();

ALTER TABLE public.project_payment_links
  ADD COLUMN expires_at timestamptz,
  ADD COLUMN deal_revision text,
  ADD COLUMN request_hash text,
  DROP CONSTRAINT project_payment_links_environment_check,
  ADD CONSTRAINT project_payment_links_environment_check
    CHECK(environment IN ('sandbox','production','simulated'));
CREATE FUNCTION private.collection_link_identity() RETURNS trigger
LANGUAGE plpgsql SET search_path='' AS $$
BEGIN
  IF (to_jsonb(NEW)-ARRAY['status','flow_order','flow_token','url','project_payment_id','updated_at'])
    IS DISTINCT FROM
    (to_jsonb(OLD)-ARRAY['status','flow_order','flow_token','url','project_payment_id','updated_at']) THEN
    RAISE EXCEPTION 'collection_link_identity_immutable' USING ERRCODE='42501';
  END IF;
  RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION private.collection_link_identity() FROM PUBLIC;
CREATE TRIGGER collection_link_identity BEFORE UPDATE ON public.project_payment_links
  FOR EACH ROW EXECUTE FUNCTION private.collection_link_identity();

CREATE TABLE public.collection_preferences (
  org_id uuid PRIMARY KEY REFERENCES public.tenancy_organizations(id),
  simulation_enabled boolean NOT NULL DEFAULT true,
  payment_link_days integer NOT NULL DEFAULT 7 CHECK(payment_link_days BETWEEN 1 AND 90),
  sii_active boolean NOT NULL DEFAULT false,
  sii_certified boolean NOT NULL DEFAULT false,
  updated_by uuid NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK(NOT sii_active OR sii_certified)
);
ALTER TABLE public.collection_preferences ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.collection_preferences FROM anon,authenticated,documentary_backend;
GRANT SELECT,INSERT,UPDATE ON public.collection_preferences TO documentary_backend;
GRANT ALL ON public.collection_preferences TO service_role;
CREATE POLICY collection_preferences_read ON public.collection_preferences
  FOR SELECT TO documentary_backend USING(org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY collection_preferences_write ON public.collection_preferences
  FOR ALL TO documentary_backend USING(private.documentary_role(org_id,ARRAY['OWNER']))
  WITH CHECK(private.documentary_role(org_id,ARRAY['OWNER'])
    AND updated_by=(current_setting('request.jwt.claims',true)::jsonb->>'sub')::uuid);
CREATE POLICY collection_preferences_service ON public.collection_preferences TO service_role
  USING(true) WITH CHECK(true);

-- Separate evidence: simulated folios never consume CAF, create a TED or send
-- anything to SII. Replays converge on the same immutable provider response.
CREATE TABLE public.project_fiscal_simulations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id),
  project_id uuid NOT NULL REFERENCES public.projects(id),
  invoice_id uuid NOT NULL REFERENCES public.project_invoices(id),
  credit_note_id uuid REFERENCES public.project_credit_notes(id),
  operation_key text NOT NULL,
  request_hash text NOT NULL,
  folio text NOT NULL CHECK(folio LIKE 'SIM-%'),
  dte_type integer NOT NULL CHECK(dte_type IN (33,39,61)),
  status text NOT NULL CHECK(status IN ('ACCEPTED','WARNINGS','REJECTED')),
  response jsonb NOT NULL,
  actor_id uuid NOT NULL,
  actor_label text,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(org_id,operation_key), UNIQUE(org_id,folio)
);
ALTER TABLE public.project_fiscal_simulations ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.project_fiscal_simulations FROM anon,authenticated,documentary_backend;
GRANT SELECT,INSERT ON public.project_fiscal_simulations TO documentary_backend;
GRANT ALL ON public.project_fiscal_simulations TO service_role;
CREATE POLICY fiscal_simulation_read ON public.project_fiscal_simulations
  FOR SELECT TO documentary_backend USING(org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY fiscal_simulation_write ON public.project_fiscal_simulations
  FOR INSERT TO documentary_backend WITH CHECK(
    private.documentary_role(org_id,ARRAY['OWNER','ESTIMATOR'])
    AND actor_id=(current_setting('request.jwt.claims',true)::jsonb->>'sub')::uuid
    AND EXISTS(SELECT 1 FROM public.project_invoices i
      WHERE i.org_id=project_fiscal_simulations.org_id AND i.project_id=project_fiscal_simulations.project_id
        AND i.id=project_fiscal_simulations.invoice_id)
    AND (credit_note_id IS NULL OR EXISTS(SELECT 1 FROM public.project_credit_notes n
      WHERE n.org_id=project_fiscal_simulations.org_id AND n.invoice_id=project_fiscal_simulations.invoice_id
        AND n.id=project_fiscal_simulations.credit_note_id)));
CREATE POLICY fiscal_simulation_service ON public.project_fiscal_simulations TO service_role
  USING(true) WITH CHECK(true);
CREATE FUNCTION private.fiscal_simulation_immutable() RETURNS trigger
LANGUAGE plpgsql SET search_path='' AS $$
BEGIN
  RAISE EXCEPTION 'fiscal_simulation_immutable' USING ERRCODE='42501';
END $$;
REVOKE ALL ON FUNCTION private.fiscal_simulation_immutable() FROM PUBLIC;
CREATE TRIGGER fiscal_simulation_immutable BEFORE UPDATE OR DELETE ON public.project_fiscal_simulations
  FOR EACH ROW EXECUTE FUNCTION private.fiscal_simulation_immutable();

CREATE TABLE public.collection_reminders (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id),
  project_id uuid NOT NULL REFERENCES public.projects(id),
  source_hash text NOT NULL,
  payload_json jsonb NOT NULL,
  audit_id uuid NOT NULL,
  actor_id uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(org_id,project_id,source_hash)
);
ALTER TABLE public.collection_reminders ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.collection_reminders FROM anon,authenticated,documentary_backend;
GRANT SELECT,INSERT ON public.collection_reminders TO documentary_backend;
GRANT ALL ON public.collection_reminders TO service_role;
CREATE POLICY collection_reminders_read ON public.collection_reminders
  FOR SELECT TO documentary_backend USING(private.documentary_role(org_id,ARRAY['OWNER']));
CREATE POLICY collection_reminders_write ON public.collection_reminders
  FOR INSERT TO documentary_backend WITH CHECK(private.documentary_role(org_id,ARRAY['OWNER'])
    AND actor_id=(current_setting('request.jwt.claims',true)::jsonb->>'sub')::uuid
    AND EXISTS(SELECT 1 FROM public.projects p WHERE p.id=collection_reminders.project_id
      AND p.org_id=collection_reminders.org_id));
CREATE POLICY collection_reminders_service ON public.collection_reminders TO service_role
  USING(true) WITH CHECK(true);
CREATE TRIGGER collection_reminders_immutable BEFORE UPDATE OR DELETE ON public.collection_reminders
  FOR EACH ROW EXECUTE FUNCTION private.fiscal_simulation_immutable();
ALTER TABLE public.mail_outbox DROP CONSTRAINT mail_outbox_kind_check;
ALTER TABLE public.mail_outbox ADD CONSTRAINT mail_outbox_kind_check
  CHECK(kind IN ('QUOTE','APPROVAL','PAYMENT','ORDER_BLOCKED','PURCHASE','COLLECTION'));
