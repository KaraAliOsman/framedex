BEGIN;

-- A commercial revision may precede workshop preparation. NULL is an honest
-- pending input, never a default manufacturing policy. Physical release still
-- requires the complete engine-derived, verified decision frozen by the API.
ALTER TABLE public.position_documentary_inputs
    ALTER COLUMN manufacturing_placement_policy_id DROP NOT NULL,
    ALTER COLUMN handle_requirement_policy_id DROP NOT NULL,
    ALTER COLUMN reinforcement_cut_policy_id DROP NOT NULL;

CREATE OR REPLACE FUNCTION private.validate_position_documentary_policy_scope()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
DECLARE target_system UUID;
BEGIN
    SELECT system_id INTO target_system FROM public.project_positions
    WHERE id=NEW.position_id AND project_id=NEW.project_id AND org_id=NEW.org_id;
    IF target_system IS NULL THEN
        RAISE EXCEPTION 'documentary_position_not_found' USING ERRCODE='23503';
    END IF;
    IF (NEW.manufacturing_placement_policy_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM public.manufacturing_placement_policies
        WHERE id=NEW.manufacturing_placement_policy_id AND system_id=target_system
            AND (org_id IS NULL OR org_id=NEW.org_id)))
    OR (NEW.handle_requirement_policy_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM public.handle_requirement_policies
        WHERE id=NEW.handle_requirement_policy_id AND system_id=target_system
            AND (org_id IS NULL OR org_id=NEW.org_id)))
    OR (NEW.reinforcement_cut_policy_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM public.reinforcement_cut_policies
        WHERE id=NEW.reinforcement_cut_policy_id AND system_id=target_system
            AND (org_id IS NULL OR org_id=NEW.org_id))) THEN
        RAISE EXCEPTION 'documentary_policy_scope_mismatch' USING ERRCODE='23503';
    END IF;
    RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION private.validate_position_documentary_policy_scope() FROM PUBLIC;
COMMIT;
