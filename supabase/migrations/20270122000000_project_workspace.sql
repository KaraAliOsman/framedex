-- P21: presentation order and declared site grouping preserve physical identities.
BEGIN;
ALTER TABLE public.project_positions
  ADD COLUMN display_order INTEGER CHECK (display_order > 0),
  ADD COLUMN placement JSONB NOT NULL DEFAULT '{}'::jsonb
    CHECK (jsonb_typeof(placement) = 'object'
      AND placement - ARRAY['floor','room','axis'] = '{}'::jsonb
      AND (NOT placement ? 'floor' OR (jsonb_typeof(placement->'floor')='string' AND length(placement->>'floor') <= 80))
      AND (NOT placement ? 'room' OR (jsonb_typeof(placement->'room')='string' AND length(placement->>'room') <= 80))
      AND (NOT placement ? 'axis' OR (jsonb_typeof(placement->'axis')='string' AND length(placement->>'axis') <= 80)));
-- Historical rows use their unchanged position_index as the read fallback.
GRANT SELECT (display_order, placement) ON public.project_positions TO authenticated;
CREATE INDEX project_positions_display_order
  ON public.project_positions (org_id, project_id, (COALESCE(display_order, position_index)), position_index);
CREATE FUNCTION private.guard_project_workspace() RETURNS TRIGGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN
  IF TG_OP='UPDATE' AND (NEW.display_order,NEW.placement) IS DISTINCT FROM (OLD.display_order,OLD.placement) THEN
    PERFORM 1 FROM public.projects WHERE id=OLD.project_id FOR UPDATE;
    IF EXISTS (SELECT 1 FROM public.projects p WHERE p.id=OLD.project_id AND
      (p.status<>'DRAFT' OR private.project_has_applied_commercial_state(p.id)
        OR EXISTS (SELECT 1 FROM public.project_versions v WHERE v.project_id=p.id AND v.revision_code=p.current_revision))) THEN
      RAISE EXCEPTION 'project_workspace_revision_required' USING ERRCODE='42501';
    END IF;
  END IF;
  RETURN NEW;
END; $$;
REVOKE ALL ON FUNCTION private.guard_project_workspace() FROM PUBLIC;
CREATE TRIGGER guard_project_workspace BEFORE UPDATE ON public.project_positions
  FOR EACH ROW EXECUTE FUNCTION private.guard_project_workspace();
COMMIT;
