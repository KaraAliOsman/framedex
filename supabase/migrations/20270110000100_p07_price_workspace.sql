BEGIN;

ALTER TABLE public.pricing_rules
  ADD COLUMN minimum_margin_pct NUMERIC(6,4) NOT NULL DEFAULT 0.25,
  ADD COLUMN maximum_margin_pct NUMERIC(6,4) NOT NULL DEFAULT 0.60,
  ADD COLUMN discount_approval_pct NUMERIC(6,4) NOT NULL DEFAULT 0.10;
-- Existing declared targets remain authority, even outside the new default band.
SELECT set_config('app.pricing_reason','P07: conservar los objetivos históricos al iniciar la banda',true);
UPDATE public.pricing_rules SET minimum_margin_pct=least(default_margin_pct,minimum_margin_pct),
  maximum_margin_pct=greatest(default_margin_pct,maximum_margin_pct)
  WHERE default_margin_pct<minimum_margin_pct OR default_margin_pct>maximum_margin_pct;
ALTER TABLE public.pricing_rules ADD CONSTRAINT p07_margin_band CHECK (
  minimum_margin_pct>=0 AND minimum_margin_pct<=default_margin_pct
  AND default_margin_pct<=maximum_margin_pct AND maximum_margin_pct<1
  AND discount_approval_pct BETWEEN 0 AND 1);

CREATE FUNCTION private.p07_lock_pricing_rules() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path='' AS $$
BEGIN
  PERFORM pg_advisory_xact_lock(hashtextextended(COALESCE(NEW.org_id,OLD.org_id)::text || ':pricing_rules',0));
  IF TG_OP='DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END; $$;
REVOKE ALL ON FUNCTION private.p07_lock_pricing_rules() FROM PUBLIC;
CREATE TRIGGER p07_rules_lock BEFORE INSERT OR UPDATE OR DELETE ON public.pricing_rules
  FOR EACH ROW EXECUTE FUNCTION private.p07_lock_pricing_rules();

CREATE TABLE public.pricing_attention_receipts (
  org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
  operation_id UUID NOT NULL,
  user_id UUID NOT NULL,
  acknowledged_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
  PRIMARY KEY(org_id,operation_id,user_id),
  FOREIGN KEY(operation_id,org_id) REFERENCES public.pricing_operations(id,org_id) ON DELETE CASCADE
);
ALTER TABLE public.pricing_attention_receipts ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.pricing_attention_receipts FROM PUBLIC,anon,authenticated;
GRANT SELECT,INSERT ON public.pricing_attention_receipts TO pricing_backend;
CREATE POLICY p07_receipt_read ON public.pricing_attention_receipts FOR SELECT TO pricing_backend
  USING(user_id=auth.uid() AND private.pricing_role(org_id,ARRAY['OWNER','ESTIMATOR']));
CREATE POLICY p07_receipt_insert ON public.pricing_attention_receipts FOR INSERT TO pricing_backend
  WITH CHECK(user_id=auth.uid() AND private.pricing_role(org_id,ARRAY['OWNER','ESTIMATOR']) AND EXISTS (
    SELECT 1 FROM public.pricing_operations o WHERE o.id=operation_id AND o.org_id=pricing_attention_receipts.org_id
      AND o.requested_by=auth.uid() AND o.state IN ('APPLIED','REJECTED')
      AND o.approved_by IS DISTINCT FROM o.requested_by));

CREATE INDEX p07_pending_by_tenant ON public.pricing_operations(org_id,created_at) WHERE state='PENDING';
CREATE INDEX p07_decisions_by_requester ON public.pricing_operations(org_id,requested_by,approved_at)
  WHERE state IN ('APPLIED','REJECTED');

COMMIT;
