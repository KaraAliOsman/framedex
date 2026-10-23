-- P10 · A workshop declares its own steel bar purchases. The price of a
-- reinforced profile consumes the steel's bar (stock length, purchase unit and,
-- under a finish chart, its physical stock binding). Until now only the global
-- demo seeds could write these rows, so an imported series promised a quote it
-- could not price. The catalog import writes them through catalog_backend,
-- like color SKUs; nothing is deleted (an undone import deactivates its rows).
BEGIN;

CREATE POLICY reinforcement_articles_catalog_read ON public.reinforcement_articles
    FOR SELECT TO catalog_backend
    USING (org_id IS NULL OR org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY reinforcement_articles_write ON public.reinforcement_articles
    FOR INSERT TO catalog_backend
    WITH CHECK (private.can_manage_catalog(org_id));
CREATE POLICY reinforcement_articles_update ON public.reinforcement_articles
    FOR UPDATE TO catalog_backend
    USING (private.can_manage_catalog(org_id))
    WITH CHECK (private.can_manage_catalog(org_id));

GRANT SELECT, INSERT, UPDATE ON public.reinforcement_articles TO catalog_backend;

-- Each imported steel field keeps its source like every other catalog authority.
ALTER TABLE public.catalog_parameter_evidence DROP CONSTRAINT catalog_parameter_evidence_authority_table_check;
ALTER TABLE public.catalog_parameter_evidence ADD CONSTRAINT catalog_parameter_evidence_authority_table_check
    CHECK(authority_table IN ('profile_systems','profile_articles','glazing_bead_matrix','hardware_kits',
        'infill_articles','manufacturing_placement_policies','handle_requirement_policies',
        'reinforcement_cut_policies','glass_purchase_mappings','fitting_purchase_mappings',
        'catalog_imports','catalog_color_skus','reinforcement_articles'));

COMMIT;
