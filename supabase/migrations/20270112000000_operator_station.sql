-- A station is the user's explicit workstation choice, never a new role grant.
CREATE TABLE public.production_operator_stations (
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    station_code TEXT NOT NULL CHECK (station_code IN (
        'CUT', 'PROFILE_CUT', 'REINFORCEMENT_CUT', 'MACHINING', 'WELD',
        'CLEAN', 'CRIMP', 'SASH_ASSEMBLE', 'ASSEMBLE', 'HARDWARE', 'GLAZE', 'QC', 'PACK'
    )),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (org_id, user_id)
);
ALTER TABLE public.production_operator_stations ENABLE ROW LEVEL SECURITY;
CREATE POLICY operator_station_own ON public.production_operator_stations
FOR ALL TO authenticated, documentary_backend
USING (user_id = auth.uid() AND org_id IN (SELECT private.current_user_org_ids()))
WITH CHECK (user_id = auth.uid() AND org_id IN (SELECT private.current_user_org_ids()));
REVOKE ALL ON public.production_operator_stations FROM anon, authenticated, documentary_backend;
GRANT SELECT, INSERT, UPDATE ON public.production_operator_stations TO authenticated, documentary_backend;
GRANT ALL ON public.production_operator_stations TO service_role;

-- One human QC operation may produce only one remake, even on retry.
CREATE UNIQUE INDEX orders_qc_remake_operation_uq ON public.orders (
    org_id, (payload_json->>'remake_of'), (payload_json->>'qc_operation_key')
) WHERE order_type = 'WORKSHOP_OT' AND payload_json ? 'qc_operation_key';
