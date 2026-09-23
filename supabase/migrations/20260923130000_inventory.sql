-- Inventory ledger + purchase order receiving.
--
-- Stock is never a mutable "stock = 43" column: every change is an append-only
-- inventory_movements row (receipt, reservation, release, consumption,
-- adjustment, return, scrap) and inventory_stock derives balances by summing
-- the ledger. Receiving a supplier order writes order_receipts +
-- order_receipt_lines (what physically arrived, damaged share, lot) plus one
-- RECEIPT movement per good quantity, and advances the order status through
-- the already-declared PARTIALLY_RECEIVED / FULFILLED lifecycle.

CREATE TYPE public.inventory_movement_type AS ENUM (
    'RECEIPT',
    'RESERVATION',
    'RELEASE',
    'CONSUMPTION',
    'ADJUSTMENT',
    'RETURN',
    'SCRAP'
);

CREATE TABLE public.inventory_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL
        REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    sku TEXT NOT NULL,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    variant_key VARCHAR(150) NOT NULL DEFAULT '',
    attributes JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_org_inventory_item UNIQUE (org_id, sku, variant_key)
);

CREATE TABLE public.order_receipts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL
        REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    order_id UUID NOT NULL
        REFERENCES public.orders(id) ON DELETE RESTRICT,
    receipt_key VARCHAR(100) NOT NULL,
    note VARCHAR(500),
    received_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_org_order_receipt_key UNIQUE (org_id, receipt_key)
);

CREATE TABLE public.order_receipt_lines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    receipt_id UUID NOT NULL
        REFERENCES public.order_receipts(id) ON DELETE CASCADE,
    order_line_id UUID NOT NULL
        REFERENCES public.order_requirement_lines(id) ON DELETE RESTRICT,
    received_qty NUMERIC(14, 2) NOT NULL CHECK (received_qty >= 0),
    damaged_qty NUMERIC(14, 2) NOT NULL DEFAULT 0
        CHECK (damaged_qty >= 0),
    lot_code VARCHAR(100),
    rack_location VARCHAR(50),
    note VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT receipt_line_damage_bounds CHECK (damaged_qty <= received_qty)
);

CREATE TABLE public.inventory_movements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL
        REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    item_id UUID NOT NULL
        REFERENCES public.inventory_items(id) ON DELETE RESTRICT,
    movement_type public.inventory_movement_type NOT NULL,
    quantity NUMERIC(14, 2) NOT NULL CHECK (quantity > 0),
    order_id UUID REFERENCES public.orders(id) ON DELETE SET NULL,
    order_line_id UUID REFERENCES public.order_requirement_lines(id) ON DELETE SET NULL,
    receipt_line_id UUID REFERENCES public.order_receipt_lines(id) ON DELETE SET NULL,
    lot_code VARCHAR(100),
    note VARCHAR(500),
    actor_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX inventory_movements_item_idx
    ON public.inventory_movements (item_id, created_at DESC);
CREATE INDEX inventory_movements_org_idx
    ON public.inventory_movements (org_id, created_at DESC);
CREATE INDEX order_receipt_lines_line_idx
    ON public.order_receipt_lines (order_line_id);
CREATE INDEX order_receipts_order_idx
    ON public.order_receipts (order_id);

-- Derived balances; the ledger stays the only writable truth.
CREATE VIEW public.inventory_stock
    WITH (security_invoker = true) AS
SELECT
    item.id AS item_id,
    item.org_id,
    item.sku,
    item.name,
    item.category,
    item.unit,
    item.variant_key,
    COALESCE(SUM(CASE
        WHEN movement.movement_type IN ('RECEIPT', 'RETURN', 'ADJUSTMENT')
            THEN movement.quantity
        WHEN movement.movement_type IN ('CONSUMPTION', 'SCRAP')
            THEN -movement.quantity
        ELSE 0
    END), 0)::NUMERIC(14, 2) AS on_hand_qty,
    COALESCE(SUM(CASE
        WHEN movement.movement_type = 'RESERVATION' THEN movement.quantity
        WHEN movement.movement_type = 'RELEASE' THEN -movement.quantity
        ELSE 0
    END), 0)::NUMERIC(14, 2) AS reserved_qty
FROM public.inventory_items item
LEFT JOIN public.inventory_movements movement
    ON movement.item_id = item.id
GROUP BY item.id, item.org_id, item.sku, item.name,
    item.category, item.unit, item.variant_key;

ALTER TABLE public.inventory_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.order_receipts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.order_receipt_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.inventory_movements ENABLE ROW LEVEL SECURITY;

-- Reads are org-wide for tenant members; writes additionally require the
-- warehouse roles (OWNER / WORKSHOP_MANAGER) so estimators and installers
-- cannot forge stock or receipts directly.
CREATE POLICY inventory_items_select ON public.inventory_items
    FOR SELECT
    USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY inventory_items_insert ON public.inventory_items
    FOR INSERT
    WITH CHECK (
        org_id IN (SELECT private.current_user_org_ids())
        AND private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER'])
    );
CREATE POLICY inventory_items_update ON public.inventory_items
    FOR UPDATE
    USING (
        org_id IN (SELECT private.current_user_org_ids())
        AND private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER'])
    )
    WITH CHECK (
        org_id IN (SELECT private.current_user_org_ids())
        AND private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER'])
    );
CREATE POLICY inventory_items_delete ON public.inventory_items
    FOR DELETE
    USING (
        org_id IN (SELECT private.current_user_org_ids())
        AND private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER'])
    );

CREATE POLICY order_receipts_select ON public.order_receipts
    FOR SELECT
    USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY order_receipts_insert ON public.order_receipts
    FOR INSERT
    WITH CHECK (
        org_id IN (SELECT private.current_user_org_ids())
        AND private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER'])
    );

CREATE POLICY order_receipt_lines_select ON public.order_receipt_lines
    FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM public.order_receipts receipt
        WHERE receipt.id = receipt_id
          AND receipt.org_id IN (SELECT private.current_user_org_ids())
    ));
CREATE POLICY order_receipt_lines_insert ON public.order_receipt_lines
    FOR INSERT
    WITH CHECK (EXISTS (
        SELECT 1 FROM public.order_receipts receipt
        WHERE receipt.id = receipt_id
          AND receipt.org_id IN (SELECT private.current_user_org_ids())
          AND private.documentary_role(
              receipt.org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER'])
    ));

-- Append-only by privilege: the ledger can be read and written but never
-- edited or deleted.
CREATE POLICY inventory_movements_select ON public.inventory_movements
    FOR SELECT
    USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY inventory_movements_insert ON public.inventory_movements
    FOR INSERT
    WITH CHECK (
        org_id IN (SELECT private.current_user_org_ids())
        AND private.documentary_role(org_id, ARRAY['OWNER', 'WORKSHOP_MANAGER'])
    );

-- Cross-tenant FK targets: a receipt line can only reference requirement lines
-- of the receipt's own org, and a movement can only reference rows of its own
-- org. RLS checks the row's org; this trigger checks the referenced org.
CREATE FUNCTION private.guard_inventory_org()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    receipt_org UUID;
    receipt_order UUID;
BEGIN
    IF TG_TABLE_NAME = 'order_receipts' THEN
        IF NOT EXISTS (
            SELECT 1 FROM public.orders
            WHERE id = NEW.order_id AND org_id = NEW.org_id
        ) THEN
            RAISE EXCEPTION 'inventory_org_mismatch' USING ERRCODE = '23514';
        END IF;
    ELSIF TG_TABLE_NAME = 'order_receipt_lines' THEN
        SELECT org_id, order_id INTO receipt_org, receipt_order
        FROM public.order_receipts WHERE id = NEW.receipt_id;
        IF receipt_org IS NULL OR NOT EXISTS (
            SELECT 1 FROM public.order_requirement_lines
            WHERE id = NEW.order_line_id AND org_id = receipt_org
              AND order_id = receipt_order
        ) THEN
            RAISE EXCEPTION 'inventory_org_mismatch' USING ERRCODE = '23514';
        END IF;
    ELSIF TG_TABLE_NAME = 'inventory_movements' THEN
        IF NOT EXISTS (
            SELECT 1 FROM public.inventory_items
            WHERE id = NEW.item_id AND org_id = NEW.org_id
        ) THEN
            RAISE EXCEPTION 'inventory_org_mismatch' USING ERRCODE = '23514';
        END IF;
        IF NEW.order_id IS NOT NULL AND NOT EXISTS (
            SELECT 1 FROM public.orders
            WHERE id = NEW.order_id AND org_id = NEW.org_id
        ) THEN
            RAISE EXCEPTION 'inventory_org_mismatch' USING ERRCODE = '23514';
        END IF;
        IF NEW.order_line_id IS NOT NULL AND NOT EXISTS (
            SELECT 1 FROM public.order_requirement_lines
            WHERE id = NEW.order_line_id AND org_id = NEW.org_id
        ) THEN
            RAISE EXCEPTION 'inventory_org_mismatch' USING ERRCODE = '23514';
        END IF;
        IF NEW.receipt_line_id IS NOT NULL AND NOT EXISTS (
            SELECT 1 FROM public.order_receipt_lines line_
            JOIN public.order_receipts receipt ON receipt.id = line_.receipt_id
            WHERE line_.id = NEW.receipt_line_id AND receipt.org_id = NEW.org_id
        ) THEN
            RAISE EXCEPTION 'inventory_org_mismatch' USING ERRCODE = '23514';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION private.guard_inventory_org() FROM PUBLIC;

CREATE TRIGGER guard_inventory_org
    BEFORE INSERT ON public.order_receipts
    FOR EACH ROW EXECUTE FUNCTION private.guard_inventory_org();
CREATE TRIGGER guard_inventory_org
    BEFORE INSERT ON public.order_receipt_lines
    FOR EACH ROW EXECUTE FUNCTION private.guard_inventory_org();
CREATE TRIGGER guard_inventory_org
    BEFORE INSERT ON public.inventory_movements
    FOR EACH ROW EXECUTE FUNCTION private.guard_inventory_org();

REVOKE ALL ON public.inventory_items FROM anon;
REVOKE ALL ON public.order_receipts FROM anon;
REVOKE ALL ON public.order_receipt_lines FROM anon;
REVOKE ALL ON public.inventory_movements FROM anon;

GRANT SELECT, INSERT, UPDATE, DELETE ON public.inventory_items TO authenticated, documentary_backend;
GRANT SELECT, INSERT ON public.order_receipts TO authenticated, documentary_backend;
GRANT SELECT, INSERT ON public.order_receipt_lines TO authenticated, documentary_backend;
GRANT SELECT, INSERT ON public.inventory_movements TO authenticated, documentary_backend;
REVOKE UPDATE, DELETE, TRUNCATE ON public.inventory_movements FROM authenticated, documentary_backend, service_role;
GRANT SELECT ON public.inventory_stock TO authenticated, documentary_backend;

GRANT ALL ON public.inventory_items TO service_role;
GRANT ALL ON public.order_receipts TO service_role;
GRANT ALL ON public.order_receipt_lines TO service_role;
GRANT SELECT, INSERT ON public.inventory_movements TO service_role;
GRANT ALL ON public.inventory_stock TO service_role;
