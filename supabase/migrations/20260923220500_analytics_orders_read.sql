-- Analytics readers include ESTIMATOR, but the orders table only exposes
-- supplier rows to documentary_backend for OWNER / WORKSHOP_MANAGER; an
-- estimator's supplier_orders aggregate would silently return {}. An
-- org-scoped SELECT policy matching the endpoint's reader set fixes it —
-- the API role check still decides who may call the endpoint.
-- Append-only on top of 20260923210000_analytics_read_grants.sql.

CREATE POLICY orders_analytics_read ON public.orders FOR SELECT
    TO documentary_backend
    USING (
        org_id IN (SELECT private.current_user_org_ids())
        AND private.documentary_role(
            org_id, ARRAY['OWNER', 'ESTIMATOR', 'WORKSHOP_MANAGER']
        )
    );
