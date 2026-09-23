-- Production slice: work centers, work-order routing steps, append-only step events.
-- WORKSHOP_OT orders are the work-order substrate: free-form status/payload,
-- org-scoped access for the shop floor (workshop_orders_inherited_access).

ALTER TYPE public.order_status ADD VALUE IF NOT EXISTS 'RELEASED';
ALTER TYPE public.order_status ADD VALUE IF NOT EXISTS 'IN_PROGRESS';
ALTER TYPE public.order_status ADD VALUE IF NOT EXISTS 'COMPLETED';
ALTER TYPE public.order_status ADD VALUE IF NOT EXISTS 'HOLD';

-- One work order per sealed position per version (idempotent release).
CREATE UNIQUE INDEX orders_workshop_position_uq
ON public.orders (org_id, project_version_id, (payload_json->>'position_id'))
WHERE order_type = 'WORKSHOP_OT'
  AND project_version_id IS NOT NULL
  AND payload_json ? 'position_id';

CREATE TABLE public.work_centers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    code TEXT NOT NULL CHECK (length(btrim(code)) > 0),
    name TEXT NOT NULL CHECK (length(btrim(name)) > 0),
    kind TEXT NOT NULL CHECK (kind IN ('CUT', 'ASSEMBLY', 'GLAZING', 'QC', 'PACK')),
    display_order INTEGER NOT NULL DEFAULT 0,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (org_id, code)
);
CREATE INDEX work_centers_org_idx ON public.work_centers (org_id);

CREATE TABLE public.production_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    order_id UUID NOT NULL REFERENCES public.orders(id) ON DELETE RESTRICT,
    sequence INTEGER NOT NULL CHECK (sequence > 0),
    work_center_id UUID REFERENCES public.work_centers(id) ON DELETE SET NULL,
    code TEXT NOT NULL CHECK (code IN ('CUT', 'ASSEMBLE', 'GLAZE', 'QC', 'PACK')),
    label TEXT NOT NULL CHECK (length(btrim(label)) > 0),
    status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING', 'READY', 'IN_PROGRESS', 'DONE', 'BLOCKED')),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    actor_id UUID,
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (order_id, sequence)
);
CREATE INDEX production_steps_order_idx ON public.production_steps (order_id);
CREATE INDEX production_steps_org_idx ON public.production_steps (org_id);

CREATE TABLE public.production_step_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    order_id UUID NOT NULL REFERENCES public.orders(id) ON DELETE RESTRICT,
    step_id UUID REFERENCES public.production_steps(id) ON DELETE SET NULL,
    event TEXT NOT NULL CHECK (event IN (
        'WO_RELEASED', 'STEP_STARTED', 'STEP_COMPLETED', 'STEP_BLOCKED',
        'STEP_UNBLOCKED', 'NOTE', 'WO_COMPLETED', 'WO_HOLD'
    )),
    actor_id UUID,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(payload) = 'object'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX production_step_events_order_idx ON public.production_step_events (order_id);
CREATE INDEX production_step_events_step_idx ON public.production_step_events (step_id);

ALTER TABLE public.work_centers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.production_steps ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.production_step_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY work_centers_isolation ON public.work_centers FOR ALL
USING (org_id IN (SELECT private.current_user_org_ids()))
WITH CHECK (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY production_steps_isolation ON public.production_steps FOR ALL
USING (org_id IN (SELECT private.current_user_org_ids()))
WITH CHECK (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY production_step_events_isolation ON public.production_step_events FOR ALL
USING (org_id IN (SELECT private.current_user_org_ids()))
WITH CHECK (org_id IN (SELECT private.current_user_org_ids()));

REVOKE ALL ON public.work_centers FROM anon;
REVOKE ALL ON public.production_steps FROM anon;
REVOKE ALL ON public.production_step_events FROM anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.work_centers TO authenticated, documentary_backend;
GRANT SELECT, INSERT, UPDATE ON public.production_steps TO authenticated, documentary_backend;
GRANT SELECT, INSERT ON public.production_step_events TO authenticated, documentary_backend;
GRANT ALL ON public.work_centers TO service_role;
GRANT ALL ON public.production_steps TO service_role;
GRANT ALL ON public.production_step_events TO service_role;
REVOKE UPDATE, DELETE, TRUNCATE ON public.production_step_events FROM authenticated, documentary_backend;
