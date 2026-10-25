-- P12e · The screws that fix steel inside a profile are counted fittings, and
-- a fitting reaches the purchase order only through its purchase mapping.
-- Only global seeds could write one, so a workshop's own series never got
-- past quote-only. The catalog import declares them now, like glass
-- purchases: versioned, immutable, and bound to the workshop's own series.
BEGIN;

GRANT SELECT, INSERT ON public.fitting_purchase_mappings TO catalog_backend;
-- Row locks need UPDATE on one column; the immutable trigger still rejects it.
GRANT UPDATE(id) ON public.fitting_purchase_mappings TO catalog_backend;
CREATE POLICY catalog_fitting_backend ON public.fitting_purchase_mappings FOR ALL TO catalog_backend
    USING (private.can_manage_catalog(org_id) AND EXISTS
        (SELECT 1 FROM public.profile_systems s WHERE s.id=system_id AND s.org_id=fitting_purchase_mappings.org_id))
    WITH CHECK (private.can_manage_catalog(org_id) AND EXISTS
        (SELECT 1 FROM public.profile_systems s WHERE s.id=system_id AND s.org_id=fitting_purchase_mappings.org_id));

COMMIT;
