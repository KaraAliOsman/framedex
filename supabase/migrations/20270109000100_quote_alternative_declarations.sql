-- Optional references to earlier issued proposals. The current price never
-- includes these options; emission copies their verified sealed snapshots.
ALTER TABLE public.project_documentary_inputs
  ADD COLUMN alternative_version_ids uuid[] NOT NULL DEFAULT '{}'
  CHECK (cardinality(alternative_version_ids) <= 3);
CREATE FUNCTION private.guard_quote_alternatives() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE target uuid;
BEGIN
  FOREACH target IN ARRAY NEW.alternative_version_ids LOOP
    IF NOT EXISTS (SELECT 1 FROM public.project_versions v WHERE v.id=target
        AND v.org_id=NEW.org_id AND v.project_id=NEW.project_id) THEN
      RAISE EXCEPTION 'quote_alternative_scope_mismatch';
    END IF;
  END LOOP;
  RETURN NEW;
END $$;
CREATE TRIGGER quote_alternative_scope BEFORE INSERT OR UPDATE ON public.project_documentary_inputs
  FOR EACH ROW EXECUTE FUNCTION private.guard_quote_alternatives();

-- The capability printed on a sealed PDF cannot be rebound by editing the
-- approval. Status/decision/view counters remain mutable through portal rules.
CREATE FUNCTION private.guard_document_approval_identity() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF (OLD.link_source='DOCUMENT' OR NEW.link_source='DOCUMENT')
     AND ROW(OLD.id,OLD.org_id,OLD.project_id,OLD.project_version_id,OLD.token_hash,OLD.link_source,OLD.expires_at,OLD.created_by)
       IS DISTINCT FROM ROW(NEW.id,NEW.org_id,NEW.project_id,NEW.project_version_id,NEW.token_hash,NEW.link_source,NEW.expires_at,NEW.created_by) THEN
    RAISE EXCEPTION 'document_approval_identity_immutable';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER document_approval_identity BEFORE UPDATE ON public.customer_approvals
  FOR EACH ROW EXECUTE FUNCTION private.guard_document_approval_identity();
ALTER POLICY document_link_backend ON public.document_portal_links
  USING (org_id IN (SELECT private.current_user_org_ids())
    AND private.documentary_role(org_id, ARRAY['OWNER','ESTIMATOR']));
