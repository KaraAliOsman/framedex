-- Receiving transitions on supplier orders.
-- order rows remain immutable evidence: the only permitted mutation after
-- DRAFT->SENT is the status column moving forward
-- SENT -> PARTIALLY_RECEIVED -> FULFILLED (or straight to FULFILLED).
-- Supplier payload, snapshot, lines and hash can never change; CANCELLED
-- keeps needing an explicit attestation path that does not exist yet.

ALTER TABLE public.orders
    DROP CONSTRAINT shot09_supplier_order_state;
ALTER TABLE public.orders
    ADD CONSTRAINT shot09_supplier_order_state CHECK (
        order_type = 'WORKSHOP_OT'::order_type
        OR status IN ('DRAFT'::order_status, 'SENT'::order_status,
                      'PARTIALLY_RECEIVED'::order_status, 'FULFILLED'::order_status)
    );

CREATE OR REPLACE FUNCTION private.guard_order_evidence()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
    IF OLD.order_type = 'WORKSHOP_OT' THEN
        RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
    END IF;
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'order_evidence_immutable' USING ERRCODE = '42501';
    END IF;
    IF OLD.status = 'DRAFT' AND NEW.status = 'SENT'
       AND NEW.sent_by IS NOT NULL AND NEW.sent_at IS NOT NULL
       AND (to_jsonb(NEW) - ARRAY['status', 'sent_by', 'sent_at', 'updated_at'])
           = (to_jsonb(OLD) - ARRAY['status', 'sent_by', 'sent_at', 'updated_at']) THEN
        RETURN NEW;
    END IF;
    IF OLD.status IN ('SENT', 'PARTIALLY_RECEIVED')
       AND NEW.status IN ('PARTIALLY_RECEIVED', 'FULFILLED')
       AND (to_jsonb(NEW) - ARRAY['status', 'updated_at'])
           = (to_jsonb(OLD) - ARRAY['status', 'updated_at']) THEN
        RETURN NEW;
    END IF;
    RAISE EXCEPTION 'order_evidence_immutable' USING ERRCODE = '42501';
END;
$$;
REVOKE ALL ON FUNCTION private.guard_order_evidence() FROM PUBLIC;
