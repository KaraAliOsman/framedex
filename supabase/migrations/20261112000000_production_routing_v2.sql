-- Phase-2 §29/§30: material-aware routing depth. The routing ladder was a
-- fixed 5-step vocabulary regardless of what the sealed product physically
-- needs — PVC welded frames and aluminium crimped frames walked the same
-- generic path. Work centers and routing steps now carry the real shop
-- vocabulary (machining, welding, cleaning, crimping, hardware bench, sash
-- assembly) while every already-created step/center stays valid.
--
-- Append-only: widens CHECK lists, touches no rows.

BEGIN;

ALTER TABLE public.work_centers
    DROP CONSTRAINT work_centers_kind_check,
    ADD CONSTRAINT work_centers_kind_check CHECK (kind IN (
        'CUT', 'PROFILE_CUT', 'REINFORCEMENT_CUT', 'MACHINING',
        'WELDING', 'CLEANING', 'CRIMPING', 'SASH_ASSEMBLY', 'ASSEMBLY',
        'HARDWARE', 'GLAZING', 'QC', 'PACK'
    ));

ALTER TABLE public.production_steps
    DROP CONSTRAINT production_steps_code_check,
    ADD CONSTRAINT production_steps_code_check CHECK (code IN (
        'CUT', 'PROFILE_CUT', 'REINFORCEMENT_CUT', 'MACHINING',
        'WELD', 'CLEAN', 'CRIMP', 'SASH_ASSEMBLE', 'ASSEMBLE',
        'HARDWARE', 'GLAZE', 'QC', 'PACK'
    ));

COMMIT;
