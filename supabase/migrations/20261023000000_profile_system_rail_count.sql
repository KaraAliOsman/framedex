-- Phase-2 §12: rail capacity is a catalog authority, not a rail_type flag.
-- NULL keeps the legacy derivation (mono=1, dual=2); an explicit positive
-- count overrides it for systems with more tracks than the enum expresses.
BEGIN;

ALTER TABLE public.profile_systems
    ADD COLUMN rail_count SMALLINT
        CHECK (rail_count IS NULL OR rail_count > 0);

COMMIT;
