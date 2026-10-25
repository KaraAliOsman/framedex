-- P12b · A series without a finish chart buys its profiles as plain bars
-- (`profile_purchase_mappings`). The price reads them, but only the global
-- seeds could write them, so an imported white series could never quote. The
-- catalog import now declares them through catalog_backend, like color SKUs;
-- nothing is deleted (an undone import deactivates its rows). The publication
-- keeps the reviewed row and its source; these rows carry no per-field evidence.
BEGIN;

CREATE POLICY profile_purchase_mappings_catalog_read ON public.profile_purchase_mappings
    FOR SELECT TO catalog_backend
    USING (org_id IS NULL OR org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY profile_purchase_mappings_catalog_insert ON public.profile_purchase_mappings
    FOR INSERT TO catalog_backend
    WITH CHECK (private.can_manage_catalog(org_id));
CREATE POLICY profile_purchase_mappings_catalog_update ON public.profile_purchase_mappings
    FOR UPDATE TO catalog_backend
    USING (private.can_manage_catalog(org_id))
    WITH CHECK (private.can_manage_catalog(org_id));

GRANT SELECT, INSERT, UPDATE ON public.profile_purchase_mappings TO catalog_backend;

-- The historical member policies were written for every role; the browser has
-- no write grant, so they only ever reached it. Keep them there.
ALTER POLICY profile_purchase_mappings_member_insert ON public.profile_purchase_mappings TO authenticated;
ALTER POLICY profile_purchase_mappings_member_update ON public.profile_purchase_mappings TO authenticated;
ALTER POLICY profile_purchase_mappings_member_delete ON public.profile_purchase_mappings TO authenticated;

COMMIT;
