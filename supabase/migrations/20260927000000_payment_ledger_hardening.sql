-- Cobranza hardening:
-- * private.applied_pricing_currency exposes only "does a live applied deal
--   exist and in which currency" — pricing cost detail stays behind the
--   OWNER/ESTIMATOR policy, but WORKSHOP_MANAGER can read the cobranza summary.
-- * project_payments becomes one-way voidable: DELETE is rejected and UPDATE
--   may only transition the void columns on a never-voided row; every other
--   column is frozen at insert.
-- Append-only on top of 20260926000000_payment_links.sql.

CREATE FUNCTION private.applied_pricing_currency(target_org uuid, target_project uuid)
RETURNS TABLE(currency text)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT o.request->>'currency'
    FROM public.pricing_operations o
    JOIN public.projects p ON p.id = o.project_id AND p.org_id = o.org_id
    WHERE o.org_id = target_org
      AND o.project_id = target_project
      AND o.state = 'APPLIED'
      AND o.approved_at IS NOT NULL
      AND o.approved_at > COALESCE(p.pricing_reset_at, '-infinity'::timestamptz)
    ORDER BY o.created_at DESC, o.id DESC
    LIMIT 1;
$$;
REVOKE ALL ON FUNCTION private.applied_pricing_currency(uuid, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.applied_pricing_currency(uuid, uuid)
TO documentary_backend;

CREATE FUNCTION private.project_payments_void_only()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'project_payments_immutable' USING ERRCODE = '42501';
    END IF;
    IF OLD.voided_at IS NOT NULL
        OR NEW.voided_at IS NULL
        OR NEW.id IS DISTINCT FROM OLD.id
        OR NEW.org_id IS DISTINCT FROM OLD.org_id
        OR NEW.project_id IS DISTINCT FROM OLD.project_id
        OR NEW.operation_key IS DISTINCT FROM OLD.operation_key
        OR NEW.kind IS DISTINCT FROM OLD.kind
        OR NEW.amount IS DISTINCT FROM OLD.amount
        OR NEW.method IS DISTINCT FROM OLD.method
        OR NEW.reference IS DISTINCT FROM OLD.reference
        OR NEW.note IS DISTINCT FROM OLD.note
        OR NEW.recorded_by IS DISTINCT FROM OLD.recorded_by
        OR NEW.recorded_at IS DISTINCT FROM OLD.recorded_at
        OR NEW.created_at IS DISTINCT FROM OLD.created_at
    THEN
        RAISE EXCEPTION 'project_payments_void_only' USING ERRCODE = '42501';
    END IF;
    RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION private.project_payments_void_only() FROM PUBLIC;
CREATE TRIGGER project_payments_void_only
BEFORE UPDATE OR DELETE ON public.project_payments
FOR EACH ROW EXECUTE FUNCTION private.project_payments_void_only();

REVOKE UPDATE ON public.project_payments FROM documentary_backend;
GRANT UPDATE (voided_at, voided_by, void_reason) ON public.project_payments
TO documentary_backend;
