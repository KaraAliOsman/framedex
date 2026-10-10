-- P15: receipt provenance, quantity-aware purchases and immutable rack history.
ALTER TABLE public.order_receipts
  ADD COLUMN supplier_document text,
  ADD COLUMN received_on date;
GRANT SELECT (supplier_document, received_on) ON public.order_receipts TO authenticated;

-- A requirement may be bought in explicit partial quantities; serialize its
-- capacity at the database edge as well as in the application transaction.
DROP INDEX public.order_requirement_lines_live_claim;
CREATE FUNCTION private.purchase_quantity_capacity() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE capacity numeric; committed numeric;
BEGIN
  IF NULLIF(current_setting('request.jwt.claims',true),'')::jsonb->>'sub' IS NOT NULL
     AND NOT private.documentary_role(NEW.org_id,ARRAY['OWNER','WORKSHOP_MANAGER']) THEN
    RAISE EXCEPTION 'purchase_permission_denied' USING ERRCODE='42501';
  END IF;
  SELECT quantity INTO capacity FROM public.purchase_requirement_lines
    WHERE id=NEW.requirement_line_id AND org_id=NEW.org_id FOR UPDATE;
  SELECT COALESCE(SUM(quantity-released_qty),0) INTO committed
    FROM public.order_requirement_lines
    WHERE requirement_line_id=NEW.requirement_line_id AND org_id=NEW.org_id;
  IF capacity IS NULL OR NEW.quantity+committed>capacity THEN
    RAISE EXCEPTION 'purchase_requirement_capacity_exceeded' USING ERRCODE='23514';
  END IF;
  RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION private.purchase_quantity_capacity() FROM PUBLIC;
CREATE TRIGGER purchase_quantity_capacity BEFORE INSERT ON public.order_requirement_lines
  FOR EACH ROW EXECUTE FUNCTION private.purchase_quantity_capacity();

CREATE TABLE public.purchase_need_decisions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id),
  operation_key text NOT NULL,
  request_hash text NOT NULL,
  result jsonb NOT NULL,
  actor_id uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(org_id,operation_key)
);
ALTER TABLE public.purchase_need_decisions ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.purchase_need_decisions FROM anon,authenticated,documentary_backend;
GRANT SELECT,INSERT ON public.purchase_need_decisions TO documentary_backend;
GRANT ALL ON public.purchase_need_decisions TO service_role;
CREATE POLICY purchase_need_decision_read ON public.purchase_need_decisions
  FOR SELECT TO documentary_backend USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY purchase_need_decision_write ON public.purchase_need_decisions
  FOR INSERT TO documentary_backend WITH CHECK (
    private.documentary_role(org_id,ARRAY['OWNER','WORKSHOP_MANAGER'])
    AND actor_id=(current_setting('request.jwt.claims',true)::jsonb->>'sub')::uuid);
CREATE POLICY purchase_need_decision_service ON public.purchase_need_decisions
  TO service_role USING (true) WITH CHECK (true);

CREATE TABLE public.inventory_remnant_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id),
  remnant_id uuid NOT NULL REFERENCES public.inventory_remnants(id),
  action text NOT NULL,
  previous_rack text,
  rack_location text,
  previous_status text,
  status text NOT NULL,
  order_id uuid,
  reason text,
  actor_id uuid,
  actor_label text,
  created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE public.inventory_remnant_events ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.inventory_remnant_events FROM anon,authenticated,documentary_backend;
GRANT SELECT ON public.inventory_remnant_events TO authenticated,documentary_backend;
GRANT INSERT ON public.inventory_remnant_events TO documentary_backend;
GRANT ALL ON public.inventory_remnant_events TO service_role;
CREATE POLICY remnant_event_read ON public.inventory_remnant_events FOR SELECT
  USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY remnant_event_write ON public.inventory_remnant_events FOR INSERT
  TO documentary_backend WITH CHECK (
    private.documentary_role(org_id,ARRAY['OWNER','WORKSHOP_MANAGER','OPERATOR'])
    AND actor_id=(current_setting('request.jwt.claims',true)::jsonb->>'sub')::uuid
    AND EXISTS(SELECT 1 FROM public.inventory_remnants r WHERE r.id=remnant_id AND r.org_id=inventory_remnant_events.org_id));
CREATE POLICY remnant_event_service ON public.inventory_remnant_events TO service_role
  USING(true) WITH CHECK(true);
CREATE FUNCTION private.trace_remnant_change() RETURNS trigger
LANGUAGE plpgsql SET search_path='' AS $$
DECLARE claims jsonb:=COALESCE(NULLIF(current_setting('request.jwt.claims',true),''),'{}')::jsonb;
BEGIN
  IF TG_OP='UPDATE' AND NEW.rack_location IS NOT DISTINCT FROM OLD.rack_location
    AND NEW.status=OLD.status THEN RETURN NEW; END IF;
  INSERT INTO public.inventory_remnant_events(org_id,remnant_id,action,previous_rack,rack_location,
    previous_status,status,order_id,reason,actor_id,actor_label)
  VALUES(NEW.org_id,NEW.id,
    CASE WHEN TG_OP='INSERT' THEN 'CREATE' WHEN NEW.status<>OLD.status THEN NEW.status ELSE 'MOVE' END,
    CASE WHEN TG_OP='UPDATE' THEN OLD.rack_location END,NEW.rack_location,
    CASE WHEN TG_OP='UPDATE' THEN OLD.status END,NEW.status,
    COALESCE(NEW.reserved_order_id,NEW.consumed_order_id,NEW.origin_order_id),
    NULLIF(current_setting('dekopen.inventory_reason',true),''),
    (claims->>'sub')::uuid,claims->>'email');
  RETURN NEW;
END $$;
CREATE TRIGGER trace_remnant_change AFTER INSERT OR UPDATE ON public.inventory_remnants
  FOR EACH ROW EXECUTE FUNCTION private.trace_remnant_change();

-- All stock movements, including production reservations, inherit the actor.
CREATE FUNCTION private.inventory_movement_actor() RETURNS trigger
LANGUAGE plpgsql SET search_path='' AS $$
BEGIN
  NEW.actor_label:=COALESCE(NEW.actor_label,NULLIF(current_setting('request.jwt.claims',true)::jsonb->>'email',''));
  RETURN NEW;
END $$;
CREATE TRIGGER inventory_movement_actor BEFORE INSERT ON public.inventory_movements
  FOR EACH ROW EXECUTE FUNCTION private.inventory_movement_actor();
ALTER TABLE public.mail_outbox DROP CONSTRAINT mail_outbox_kind_check;
ALTER TABLE public.mail_outbox ADD CONSTRAINT mail_outbox_kind_check
  CHECK(kind IN ('QUOTE','APPROVAL','PAYMENT','ORDER_BLOCKED','PURCHASE'));

-- D05 physical identities may be catalog strings. Legacy UUIDs retain their
-- exact text; authority ids and remnant identities remain UUIDs.
ALTER TABLE public.inventory_remnants ALTER COLUMN physical_stock_identity TYPE text
  USING physical_stock_identity::text;
CREATE FUNCTION private.inventory_history_immutable() RETURNS trigger
LANGUAGE plpgsql SET search_path='' AS $$
BEGIN RAISE EXCEPTION 'inventory_history_immutable' USING ERRCODE='23514'; END $$;
REVOKE ALL ON FUNCTION private.inventory_history_immutable() FROM PUBLIC;
CREATE TRIGGER inventory_history_immutable BEFORE UPDATE OR DELETE ON public.inventory_remnant_events
  FOR EACH ROW EXECUTE FUNCTION private.inventory_history_immutable();
CREATE TRIGGER purchase_decision_immutable BEFORE UPDATE OR DELETE ON public.purchase_need_decisions
  FOR EACH ROW EXECUTE FUNCTION private.inventory_history_immutable();
