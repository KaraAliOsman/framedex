-- Manual project work uses the existing screen/edit role contracts.
BEGIN;

DROP POLICY projects_isolation ON public.projects;
CREATE POLICY project_manual_read ON public.projects FOR SELECT TO authenticated
USING (private.pricing_role(org_id, ARRAY['OWNER','ESTIMATOR','WORKSHOP_MANAGER']));
CREATE POLICY project_manual_insert ON public.projects FOR INSERT TO authenticated
WITH CHECK (private.pricing_role(org_id, ARRAY['OWNER','ESTIMATOR'])
    AND created_by = auth.uid() AND status = 'DRAFT' AND current_revision = 'REV-A');
CREATE POLICY project_manual_update ON public.projects FOR UPDATE TO authenticated
USING (private.pricing_role(org_id, ARRAY['OWNER','ESTIMATOR']))
WITH CHECK (private.pricing_role(org_id, ARRAY['OWNER','ESTIMATOR']));
CREATE POLICY project_manual_delete ON public.projects FOR DELETE TO authenticated
USING (private.pricing_role(org_id, ARRAY['OWNER','ESTIMATOR']) AND status = 'DRAFT');

DROP POLICY positions_isolation ON public.project_positions;
CREATE POLICY position_manual_read ON public.project_positions FOR SELECT TO authenticated
USING (private.pricing_role(org_id, ARRAY['OWNER','ESTIMATOR','WORKSHOP_MANAGER']));
CREATE POLICY position_manual_write ON public.project_positions FOR ALL TO authenticated
USING (private.pricing_role(org_id, ARRAY['OWNER','ESTIMATOR']))
WITH CHECK (private.pricing_role(org_id, ARRAY['OWNER','ESTIMATOR']));

-- SHOT-08/09 backend policies and column-level confidentiality remain unchanged.
COMMIT;
