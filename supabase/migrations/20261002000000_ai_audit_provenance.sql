-- Audit provenance + immutability: model_used stays the white-label name;
-- route_id is the backend-only pointer to the exact provider/model/prompt
-- version that produced the output. ai_routes is readable only by
-- billing_backend, so the FK reveals nothing to tenants while a JOIN under
-- the backend role gives full provenance.

ALTER TABLE public.ai_audit_logs ADD COLUMN IF NOT EXISTS
    route_id UUID NULL REFERENCES public.ai_routes(id) ON DELETE RESTRICT;

-- Audit rows are immutable evidence at every privilege level: tenants were
-- already revoked; this trigger also refuses backend/owner UPDATE or DELETE
-- so no role can rewrite or erase an invocation record.
CREATE TRIGGER immutable_ai_audit_logs BEFORE UPDATE OR DELETE
ON public.ai_audit_logs
FOR EACH ROW EXECUTE FUNCTION private.reject_immutable_evidence();
