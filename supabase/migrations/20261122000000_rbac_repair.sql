-- §B RBAC repair — align PostgREST/RLS with the Django role matrix.
--
-- Browser clients authenticate against Supabase and can reach every granted
-- table through PostgREST, so "the UI does not expose the button" is not
-- security: database permissions must be at least as restrictive as the API.
-- The initial schema granted broad CRUD to `authenticated` and most tenant
-- tables carried a single org-scoped {public} ALL policy — any member could
-- mutate clients, stock, production steps, deliveries, catalog reference
-- tables, purchase mappings and import rows directly, bypassing the
-- OWNER/ESTIMATOR/WORKSHOP_MANAGER gates the API enforces.
--
-- This migration corrects the matrix:
--
--   table                       member read   member write
--   --------------------------  ------------  -------------------------
--   project_versions.snapshot   (col revoke)  —
--   ai_audit_logs               org           org (append); no UPDATE/DELETE
--   clients                     org           OWNER/ESTIMATOR
--   inventory_items             org           OWNER/WORKSHOP_MANAGER
--   inventory_movements         org           OWNER/WORKSHOP_MANAGER (insert)
--   offcut_inventory            org           OWNER/WORKSHOP_MANAGER
--   inventory_remnants          org           OWNER/WORKSHOP_MANAGER
--   order_receipts(+lines)      org           OWNER/WORKSHOP_MANAGER (insert)
--   deliveries                  org           OWNER/WORKSHOP_MANAGER
--   production_steps            org           OWNER/WORKSHOP_MANAGER
--   production_step_events      org           OWNER/WORKSHOP_MANAGER (insert)
--   work_centers                org           OWNER/WORKSHOP_MANAGER
--   catalog_imports             org           OWNER/WORKSHOP_MANAGER
--   document_imports            org           OWNER/ESTIMATOR
--   profile_purchase_mappings   org           OWNER/WORKSHOP_MANAGER
--   infill/reinforcement/
--   cutting/inspector           org           (no member write path at all)
--
-- Write policies stay `TO public` so they also govern the backend roles
-- (`documentary_backend`) — `private.documentary_role` resolves the member's
-- role from request.jwt.claims in either context. Background jobs run as
-- service_role (BYPASSRLS) and are unaffected.

-- 1) project_versions.snapshot_json — sealed evidence (client PII, pricing,
-- BOM, purchasing, manufacturing authority) revoked from the tenant role.
-- Server-side readers (production trace, ops export) resolve it through the
-- documentary authority and return role-safe projections only.
REVOKE SELECT (snapshot_json) ON public.project_versions FROM authenticated;

-- 2) ai_audit_logs — append-only provider evidence (prompts, responses,
-- spend). Org members keep SELECT on their own ledger and INSERT for the
-- invocation path; UPDATE/DELETE are denied at grant AND policy level.
DROP POLICY ai_audit_logs_isolation ON public.ai_audit_logs;
CREATE POLICY ai_audit_logs_select ON public.ai_audit_logs
    FOR SELECT TO public
    USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY ai_audit_logs_insert ON public.ai_audit_logs
    FOR INSERT TO public
    WITH CHECK (org_id IN (SELECT private.current_user_org_ids()));
REVOKE UPDATE, DELETE ON public.ai_audit_logs FROM authenticated;

-- 3) clients — members read; OWNER/ESTIMATOR write (mirrors ClientsView's
-- READ_ROLES / WRITE_ROLES). Deactivation is an UPDATE; hard DELETE stays
-- denied (no delete policy).
DROP POLICY clients_isolation ON public.clients;
CREATE POLICY clients_member_read ON public.clients
    FOR SELECT TO public
    USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY clients_member_insert ON public.clients
    FOR INSERT TO public
    WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'ESTIMATOR']));
CREATE POLICY clients_member_update ON public.clients
    FOR UPDATE TO public
    USING (private.documentary_role(org_id, ARRAY['OWNER', 'ESTIMATOR']))
    WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'ESTIMATOR']));

-- 4) Inventory family — members read; OWNER/WORKSHOP_MANAGER write
-- (mirrors inventory views' _READERS/_WRITERS).
DROP POLICY inventory_items_select ON public.inventory_items;
DROP POLICY inventory_items_insert ON public.inventory_items;
DROP POLICY inventory_items_update ON public.inventory_items;
DROP POLICY inventory_items_delete ON public.inventory_items;
CREATE POLICY inventory_items_member_read ON public.inventory_items
    FOR SELECT TO public
    USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY inventory_items_member_insert ON public.inventory_items
    FOR INSERT TO public
    WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']));
CREATE POLICY inventory_items_member_update ON public.inventory_items
    FOR UPDATE TO public
    USING (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']))
    WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']));
CREATE POLICY inventory_items_member_delete ON public.inventory_items
    FOR DELETE TO public
    USING (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']));

DROP POLICY inventory_movements_select ON public.inventory_movements;
DROP POLICY inventory_movements_insert ON public.inventory_movements;
CREATE POLICY inventory_movements_member_read ON public.inventory_movements
    FOR SELECT TO public
    USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY inventory_movements_member_insert ON public.inventory_movements
    FOR INSERT TO public
    WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']));
-- All inventory writes run through the documentary authority — the tenant
-- role needs SELECT only.
REVOKE INSERT, UPDATE, DELETE ON public.inventory_items FROM authenticated;
REVOKE INSERT ON public.inventory_movements FROM authenticated;

DROP POLICY offcut_inventory_isolation ON public.offcut_inventory;
CREATE POLICY offcut_inventory_member_read ON public.offcut_inventory
    FOR SELECT TO public
    USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY offcut_inventory_member_insert ON public.offcut_inventory
    FOR INSERT TO public
    WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']));
CREATE POLICY offcut_inventory_member_update ON public.offcut_inventory
    FOR UPDATE TO public
    USING (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']))
    WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']));
CREATE POLICY offcut_inventory_member_delete ON public.offcut_inventory
    FOR DELETE TO public
    USING (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']));
REVOKE INSERT, UPDATE, DELETE ON public.offcut_inventory FROM authenticated;

DROP POLICY inventory_remnants_isolation ON public.inventory_remnants;
CREATE POLICY inventory_remnants_member_read ON public.inventory_remnants
    FOR SELECT TO public
    USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY inventory_remnants_member_insert ON public.inventory_remnants
    FOR INSERT TO public
    WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']));
CREATE POLICY inventory_remnants_member_update ON public.inventory_remnants
    FOR UPDATE TO public
    USING (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']))
    WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']));

DROP POLICY order_receipts_select ON public.order_receipts;
DROP POLICY order_receipts_insert ON public.order_receipts;
CREATE POLICY order_receipts_member_read ON public.order_receipts
    FOR SELECT TO public
    USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY order_receipts_member_insert ON public.order_receipts
    FOR INSERT TO public
    WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']));
-- Receipts are append-only evidence written by the documentary authority —
-- all write grants revoked.
REVOKE INSERT, UPDATE, DELETE ON public.order_receipts FROM authenticated;

DROP POLICY order_receipt_lines_select ON public.order_receipt_lines;
DROP POLICY order_receipt_lines_insert ON public.order_receipt_lines;
CREATE POLICY order_receipt_lines_member_read ON public.order_receipt_lines
    FOR SELECT TO public
    USING (EXISTS (
        SELECT 1 FROM public.order_receipts receipt
        WHERE receipt.id = order_receipt_lines.receipt_id
          AND receipt.org_id IN (SELECT private.current_user_org_ids())
    ));
CREATE POLICY order_receipt_lines_member_insert ON public.order_receipt_lines
    FOR INSERT TO public
    WITH CHECK (EXISTS (
        SELECT 1 FROM public.order_receipts receipt
        WHERE receipt.id = order_receipt_lines.receipt_id
          AND private.documentary_role(receipt.org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER'])
    ));
REVOKE INSERT, UPDATE, DELETE ON public.order_receipt_lines FROM authenticated;

-- 5) Production control — members read; OWNER/WORKSHOP_MANAGER write
-- (mirrors production views' _READERS/_WRITERS; INSTALLER is read-only).
DROP POLICY deliveries_isolation ON public.deliveries;
CREATE POLICY deliveries_member_read ON public.deliveries
    FOR SELECT TO public
    USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY deliveries_member_insert ON public.deliveries
    FOR INSERT TO public
    WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']));
CREATE POLICY deliveries_member_update ON public.deliveries
    FOR UPDATE TO public
    USING (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']))
    WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']));
CREATE POLICY deliveries_member_delete ON public.deliveries
    FOR DELETE TO public
    USING (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']));

DROP POLICY production_steps_isolation ON public.production_steps;
CREATE POLICY production_steps_member_read ON public.production_steps
    FOR SELECT TO public
    USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY production_steps_member_insert ON public.production_steps
    FOR INSERT TO public
    WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']));
CREATE POLICY production_steps_member_update ON public.production_steps
    FOR UPDATE TO public
    USING (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']))
    WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']));

DROP POLICY production_step_events_isolation ON public.production_step_events;
CREATE POLICY production_step_events_member_read ON public.production_step_events
    FOR SELECT TO public
    USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY production_step_events_member_insert ON public.production_step_events
    FOR INSERT TO public
    WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']));

DROP POLICY work_centers_isolation ON public.work_centers;
CREATE POLICY work_centers_member_read ON public.work_centers
    FOR SELECT TO public
    USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY work_centers_member_insert ON public.work_centers
    FOR INSERT TO public
    WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']));
CREATE POLICY work_centers_member_update ON public.work_centers
    FOR UPDATE TO public
    USING (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']))
    WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']));
CREATE POLICY work_centers_member_delete ON public.work_centers
    FOR DELETE TO public
    USING (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']));

-- 6) Imports — members read their own org's import rows; writes are
-- role-gated (catalog imports: _CATALOG_WRITERS; document imports: _WRITERS).
DROP POLICY catalog_imports_isolation ON public.catalog_imports;
CREATE POLICY catalog_imports_member_read ON public.catalog_imports
    FOR SELECT TO public
    USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY catalog_imports_member_insert ON public.catalog_imports
    FOR INSERT TO public
    WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']));
CREATE POLICY catalog_imports_member_update ON public.catalog_imports
    FOR UPDATE TO public
    USING (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']))
    WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']));

DROP POLICY document_imports_isolation ON public.document_imports;
CREATE POLICY document_imports_member_read ON public.document_imports
    FOR SELECT TO public
    USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY document_imports_member_insert ON public.document_imports
    FOR INSERT TO public
    WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'ESTIMATOR']));
CREATE POLICY document_imports_member_update ON public.document_imports
    FOR UPDATE TO public
    USING (private.documentary_role(org_id, ARRAY['OWNER', 'ESTIMATOR']))
    WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'ESTIMATOR']));

-- 7) profile_purchase_mappings — purchasing authority is OWNER/WORKSHOP_MANAGER
-- (mirrors purchasing _ALLOWED); members keep read parity with the sibling
-- mapping/policy tables.
DROP POLICY profile_purchase_mappings_modify ON public.profile_purchase_mappings;
CREATE POLICY profile_purchase_mappings_member_insert ON public.profile_purchase_mappings
    FOR INSERT TO public
    WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']));
CREATE POLICY profile_purchase_mappings_member_update ON public.profile_purchase_mappings
    FOR UPDATE TO public
    USING (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']))
    WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']));
CREATE POLICY profile_purchase_mappings_member_delete ON public.profile_purchase_mappings
    FOR DELETE TO public
    USING (private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER']));
REVOKE INSERT, UPDATE, DELETE ON public.profile_purchase_mappings FROM authenticated;

-- 8) Catalog configuration tables — infill/reinforcement/cutting/inspector
-- have no member-facing write endpoint; the org-scoped ALL policy was a pure
-- leak. Member read policies stay; backend contexts keep their *_documentary_read.
DROP POLICY infill_articles_modify ON public.infill_articles;
DROP POLICY reinforcement_articles_modify ON public.reinforcement_articles;
DROP POLICY cutting_profiles_modify ON public.cutting_profiles;
DROP POLICY inspector_rule_configs_modify ON public.inspector_rule_configs;
REVOKE INSERT, UPDATE, DELETE ON public.infill_articles FROM authenticated;
REVOKE INSERT, UPDATE, DELETE ON public.reinforcement_articles FROM authenticated;
REVOKE INSERT, UPDATE, DELETE ON public.cutting_profiles FROM authenticated;
REVOKE INSERT, UPDATE, DELETE ON public.inspector_rule_configs FROM authenticated;

-- 9) tenancy_memberships — membership administration runs through Django
-- owner flows; the write grants were unusable (no write policies) but are
-- revoked for defense in depth.
REVOKE INSERT, UPDATE, DELETE ON public.tenancy_memberships FROM authenticated;

-- 10) The unauthenticated `anon` role had full CRUD grants on tenant tables
-- (Supabase default privileges on table creation). RLS already denied every
-- statement without member claims, but the grants themselves are a leak:
-- revoke all access — anonymous traffic reaches data only through the
-- dedicated portal/backend roles.
REVOKE ALL ON public.ai_audit_logs FROM anon;
REVOKE ALL ON public.inventory_remnants FROM anon;
REVOKE ALL ON public.inventory_stock FROM anon;
REVOKE ALL ON public.offcut_inventory FROM anon;
REVOKE ALL ON public.price_audit_logs FROM anon;
REVOKE ALL ON public.project_positions FROM anon;
REVOKE ALL ON public.projects FROM anon;
REVOKE ALL ON public.tenancy_memberships FROM anon;
