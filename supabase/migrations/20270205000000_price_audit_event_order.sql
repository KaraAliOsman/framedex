BEGIN;

-- now() is shared by all writes in a transaction. UUIDs cannot order two
-- price edits with that timestamp. Add an immutable tie-breaker without
-- changing any historical price, actor, reason or date.
ALTER TABLE public.price_audit_logs
  ADD COLUMN event_order BIGINT GENERATED ALWAYS AS IDENTITY;
CREATE INDEX price_audit_cell_history_idx ON public.price_audit_logs
  (org_id,entity,entity_id,created_at DESC,event_order DESC);

COMMIT;
