-- Manufacturing-trust mandate §2: fabrication values move onto the canonical
-- authority chain and legacy data stops masquerading as reviewed.
--
-- 1) rebate_depth_mm and end_milling_overlap_mm were engine-side invented
--    constants (20.00 / 0.00) never loaded from the catalog — the engine used
--    them to size every glass pane and every mullion. They are now real
--    catalog columns: NULL means UNKNOWN and the consumers refuse precisely
--    instead of computing on an invented number.
--
-- 2) The earlier catalog_unknown_defaults migration could not distinguish
--    rows written by the old SQL defaults from rows carrying reviewed values.
--    `data_provenance` records who authored a row and `technical_reviewed_*`
--    records the human review that clears it; every pre-existing row is
--    marked LEGACY_UNVERIFIED — an honest label for "possibly fabricated by
--    an old default" — and production readiness refuses such values where
--    they feed fabrication math.
--
-- Append-only: adds nullable columns only, deletes nothing.

BEGIN;

ALTER TABLE public.profile_systems
    ADD COLUMN rebate_depth_mm NUMERIC(10, 2),
    ADD COLUMN end_milling_overlap_mm NUMERIC(10, 2),
    ADD COLUMN data_provenance TEXT NOT NULL DEFAULT 'MANUAL'
        CHECK (data_provenance IN ('SEED_SYNTHETIC', 'MANUAL', 'IMPORT', 'LEGACY_UNVERIFIED')),
    ADD COLUMN technical_reviewed_at TIMESTAMPTZ,
    ADD COLUMN technical_reviewed_by UUID;

ALTER TABLE public.profile_articles
    ADD COLUMN data_provenance TEXT NOT NULL DEFAULT 'MANUAL'
        CHECK (data_provenance IN ('SEED_SYNTHETIC', 'MANUAL', 'IMPORT', 'LEGACY_UNVERIFIED')),
    ADD COLUMN technical_reviewed_at TIMESTAMPTZ,
    ADD COLUMN technical_reviewed_by UUID;

ALTER TABLE public.infill_articles
    ADD COLUMN data_provenance TEXT NOT NULL DEFAULT 'MANUAL'
        CHECK (data_provenance IN ('SEED_SYNTHETIC', 'MANUAL', 'IMPORT', 'LEGACY_UNVERIFIED')),
    ADD COLUMN technical_reviewed_at TIMESTAMPTZ,
    ADD COLUMN technical_reviewed_by UUID;

ALTER TABLE public.hardware_kits
    ADD COLUMN data_provenance TEXT NOT NULL DEFAULT 'MANUAL'
        CHECK (data_provenance IN ('SEED_SYNTHETIC', 'MANUAL', 'IMPORT', 'LEGACY_UNVERIFIED')),
    ADD COLUMN technical_reviewed_at TIMESTAMPTZ,
    ADD COLUMN technical_reviewed_by UUID;

-- The freeze guards treat a locked catalog as immutable authority. Provenance
-- and review stamps are audit metadata, not technical values — a locked legacy
-- system is precisely the population that must be reviewable, so a write whose
-- only change is the provenance/review triple passes the guards while any real
-- technical edit stays frozen. `to_jsonb - keys` ignores absent keys, so tables
-- without the triple only gain a pass for no-op writes (which change nothing).
CREATE OR REPLACE FUNCTION private.guard_referenced_system() RETURNS TRIGGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN
    IF TG_OP='DELETE' AND OLD.org_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM public.tenancy_organizations WHERE id=OLD.org_id
    ) THEN RETURN OLD; END IF;
    IF OLD.technical_locked AND (TG_OP='DELETE' OR
        to_jsonb(NEW) - '{data_provenance,technical_reviewed_at,technical_reviewed_by}'::TEXT[]
        IS DISTINCT FROM
        to_jsonb(OLD) - '{data_provenance,technical_reviewed_at,technical_reviewed_by}'::TEXT[]) THEN
        RAISE EXCEPTION 'catalog_authority_referenced' USING ERRCODE='23514';
    END IF;
    RETURN CASE WHEN TG_OP='DELETE' THEN OLD ELSE NEW END;
END;
$$;
REVOKE ALL ON FUNCTION private.guard_referenced_system() FROM PUBLIC;

CREATE OR REPLACE FUNCTION private.guard_referenced_catalog() RETURNS TRIGGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
DECLARE
    payload JSONB;
    target UUID;
    locked BOOLEAN;
BEGIN
    IF TG_OP='DELETE' AND OLD.org_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM public.tenancy_organizations WHERE id=OLD.org_id
    ) THEN RETURN OLD; END IF;
    FOR payload IN SELECT value FROM jsonb_array_elements(
        CASE WHEN TG_OP='INSERT' THEN jsonb_build_array(to_jsonb(NEW))
             WHEN TG_OP='DELETE' THEN jsonb_build_array(to_jsonb(OLD))
             ELSE jsonb_build_array(to_jsonb(OLD),to_jsonb(NEW)) END
    ) LOOP
        -- Provenance-only edits to locked rows are audit writes, not technical
        -- edits: let review and re-labeling through, keep everything else frozen.
        IF TG_OP='UPDATE' AND
            to_jsonb(NEW) - '{data_provenance,technical_reviewed_at,technical_reviewed_by}'::TEXT[]
            IS NOT DISTINCT FROM
            to_jsonb(OLD) - '{data_provenance,technical_reviewed_at,technical_reviewed_by}'::TEXT[]
        THEN CONTINUE; END IF;
        IF TG_TABLE_NAME='profile_purchase_mappings' THEN
            SELECT system_id INTO target FROM public.profile_articles
            WHERE id=(payload->>'profile_article_id')::UUID;
        ELSIF TG_TABLE_NAME='hardware_purchase_mappings' THEN
            SELECT system_id INTO target FROM public.hardware_kits
            WHERE id=(payload->>'hardware_kit_id')::UUID;
        ELSIF TG_TABLE_NAME='panel_purchase_authorities' THEN
            SELECT system_id INTO target FROM public.infill_articles
            WHERE id=(payload->>'infill_article_id')::UUID;
        ELSE
            target := (payload->>'system_id')::UUID;
        END IF;
        -- A real UPDATE creates a conflicting row version, including for unlocked
        -- catalogs: a concurrent save cannot commit calculations from an old snapshot.
        UPDATE public.profile_systems SET technical_locked=technical_locked
        WHERE id=target RETURNING technical_locked INTO locked;
        IF locked THEN
            RAISE EXCEPTION 'catalog_authority_referenced' USING ERRCODE='23514';
        END IF;
    END LOOP;
    RETURN CASE WHEN TG_OP='DELETE' THEN OLD ELSE NEW END;
END;
$$;
REVOKE ALL ON FUNCTION private.guard_referenced_catalog() FROM PUBLIC;

-- Every row that predates provenance is suspect: its values may have been
-- materialized by the dropped defaults rather than authored. NULL fields are
-- already honest UNKNOWN; non-NULL legacy values become visible to readiness.
UPDATE public.profile_systems SET data_provenance = 'LEGACY_UNVERIFIED';
UPDATE public.profile_articles SET data_provenance = 'LEGACY_UNVERIFIED';
UPDATE public.infill_articles SET data_provenance = 'LEGACY_UNVERIFIED';
UPDATE public.hardware_kits SET data_provenance = 'LEGACY_UNVERIFIED';

-- Demo systems are already declared synthetic by name and is_demo flag — their
-- provenance is fixture authoring, not legacy defaults. On a fresh bootstrap
-- this UPDATE matches nothing (the seed runs later and labels them itself).
UPDATE public.profile_articles a SET data_provenance = 'SEED_SYNTHETIC'
FROM public.profile_systems s
WHERE a.system_id = s.id AND s.is_demo = TRUE;
UPDATE public.infill_articles a SET data_provenance = 'SEED_SYNTHETIC'
FROM public.profile_systems s
WHERE a.system_id = s.id AND s.is_demo = TRUE;
UPDATE public.hardware_kits k SET data_provenance = 'SEED_SYNTHETIC'
FROM public.profile_systems s
WHERE k.system_id = s.id AND s.is_demo = TRUE;
UPDATE public.profile_systems SET data_provenance = 'SEED_SYNTHETIC'
WHERE is_demo = TRUE;

COMMIT;
