BEGIN;

-- Review-reopen marker (Devin Review): editing technical values on a row a
-- human already reviewed must re-open its review, but provenance alone can't
-- distinguish "reviewed then edited" from "authored and never reviewed" —
-- both read MANUAL with NULL stamps. review_pending records that the last
-- review is stale: set on technical edits of previously-reviewed rows,
-- cleared by review() alongside the stamps. Never-written rows keep FALSE and
-- stay eligible — only legacy seed data and reopened reviews gate production.

ALTER TABLE public.profile_systems
    ADD COLUMN review_pending BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE public.profile_articles
    ADD COLUMN review_pending BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE public.infill_articles
    ADD COLUMN review_pending BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE public.hardware_kits
    ADD COLUMN review_pending BOOLEAN NOT NULL DEFAULT FALSE;

-- The freeze guards' provenance/review exemption must cover the new marker:
-- review() clears it on locked systems and update() sets it in the same write
-- as the technical change, so the strip-lists gain review_pending.
CREATE OR REPLACE FUNCTION private.guard_referenced_system() RETURNS TRIGGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN
    IF TG_OP='DELETE' AND OLD.org_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM public.tenancy_organizations WHERE id=OLD.org_id
    ) THEN RETURN OLD; END IF;
    IF OLD.technical_locked AND (TG_OP='DELETE' OR
        to_jsonb(NEW) - '{data_provenance,technical_reviewed_at,technical_reviewed_by,review_pending}'::TEXT[]
        IS DISTINCT FROM
        to_jsonb(OLD) - '{data_provenance,technical_reviewed_at,technical_reviewed_by,review_pending}'::TEXT[]) THEN
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
        -- review_pending rides the same exemption: it changes only as part of
        -- a technical edit or a review write.
        IF TG_OP='UPDATE' AND
            to_jsonb(NEW) - '{data_provenance,technical_reviewed_at,technical_reviewed_by,review_pending}'::TEXT[]
            IS NOT DISTINCT FROM
            to_jsonb(OLD) - '{data_provenance,technical_reviewed_at,technical_reviewed_by,review_pending}'::TEXT[]
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

COMMIT;
