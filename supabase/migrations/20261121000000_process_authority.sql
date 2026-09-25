-- Consolidation A: explicit versioned process authority. #102's ladder was
-- inferred from the system's material family (PVC→WELD/CLEAN, ALU→CRIMP) —
-- material alone is not manufacturing authority. Routing now resolves a
-- declared ManufacturingProcessProfile: joining/corner/cleaning methods,
-- the ordered station template, the operation→workstation map, and the
-- content gates for optional steps. The sealed work order freezes
-- {profile_id, code, version, resolved_via} into its payload so production
-- evidence always names the authority it was routed under.
--
-- Append-only: new table + one nullable FK on profile_systems. Existing
-- orders' payload.routing is untouched (they carry the ladder they froze).

BEGIN;

CREATE TABLE IF NOT EXISTS public.manufacturing_process_profiles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id uuid NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    code text NOT NULL,
    version integer NOT NULL DEFAULT 1,
    label text NOT NULL,
    -- Which products this profile may serve: material family and/or product
    -- kind (e.g. FRAMELESS overrides whatever the system's material says).
    material text NULL,
    product_kind text NULL,
    joining_method text NOT NULL DEFAULT 'NONE'
        CHECK (joining_method IN ('WELD', 'CRIMP', 'MECHANICAL', 'NONE')),
    corner_process text NOT NULL DEFAULT 'NONE'
        CHECK (corner_process IN ('WELD', 'CRIMP', 'CLEAT', 'NONE')),
    cleaning_process boolean NOT NULL DEFAULT false,
    -- Ordered station template. when='required' lands unconditionally
    -- (process-inherent: aluminium machining/crimping, QC, packing);
    -- when='auto' lands only when the sealed result carries work for it.
    stations jsonb NOT NULL,
    -- Member operation → station code. Frozen into the order so the operator
    -- UI groups ops by declared routing, never by a frontend guess.
    operation_station_map jsonb NOT NULL DEFAULT '{}',
    sash_assembly_required boolean NOT NULL DEFAULT false,
    hardware_station boolean NOT NULL DEFAULT false,
    glazing boolean NOT NULL DEFAULT true,
    qc boolean NOT NULL DEFAULT true,
    packaging boolean NOT NULL DEFAULT true,
    optional_operations jsonb NOT NULL DEFAULT '[]',
    machine_neutral_machining jsonb NOT NULL DEFAULT '[]',
    provenance jsonb NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE NULLS NOT DISTINCT (org_id, code, version)
);

ALTER TABLE public.profile_systems
    ADD COLUMN IF NOT EXISTS process_profile_id uuid NULL
        REFERENCES public.manufacturing_process_profiles(id);

-- Global declared authorities (org_id NULL = shared library rows).

INSERT INTO public.manufacturing_process_profiles
    (org_id, code, version, label, material, product_kind,
     joining_method, corner_process, cleaning_process,
     stations, operation_station_map, optional_operations, provenance)
VALUES
    (NULL, 'PVC_WELDED', 1, 'PVC — soldadura y limpieza', 'PVC', 'STANDARD',
     'WELD', 'WELD', true,
     '[
       {"code":"CUT","when":"auto"},
       {"code":"MACHINING","when":"auto"},
       {"code":"WELD","when":"required"},
       {"code":"CLEAN","when":"required"},
       {"code":"SASH_ASSEMBLE","when":"auto"},
       {"code":"HARDWARE","when":"auto"},
       {"code":"GLAZE","when":"auto"},
       {"code":"QC","when":"required"},
       {"code":"PACK","when":"required"}
     ]'::jsonb,
     '{"END_MACHINING":"MACHINING","DRAINAGE":"MACHINING","HANDLE_PREP":"MACHINING","SAW_CUT":"CUT"}'::jsonb,
     '["DRAINAGE","END_MACHINING"]'::jsonb,
     '{"source":"SEED","authority":"GLOBAL"}'::jsonb),

    (NULL, 'ALU_CRIMPED', 1, 'Aluminio — mecanizado y prensado', 'ALUMINIUM', 'STANDARD',
     'CRIMP', 'CRIMP', false,
     '[
       {"code":"CUT","when":"auto"},
       {"code":"MACHINING","when":"required"},
       {"code":"CRIMP","when":"required"},
       {"code":"SASH_ASSEMBLE","when":"auto"},
       {"code":"HARDWARE","when":"auto"},
       {"code":"GLAZE","when":"auto"},
       {"code":"QC","when":"required"},
       {"code":"PACK","when":"required"}
     ]'::jsonb,
     '{"END_MACHINING":"MACHINING","DRAINAGE":"MACHINING","HANDLE_PREP":"MACHINING","SAW_CUT":"CUT"}'::jsonb,
     '["HANDLE_PREP","END_MACHINING","DRAINAGE"]'::jsonb,
     '{"source":"SEED","authority":"GLOBAL"}'::jsonb),

    -- The pane IS the product: no weld/crimp exists regardless of the
    -- associated system's material family.
    (NULL, 'FRAMELESS_GLASS', 1, 'Vidrio sin marco — soporte y herrajes', NULL, 'FRAMELESS',
     'NONE', 'NONE', false,
     '[
       {"code":"CUT","when":"auto"},
       {"code":"HARDWARE","when":"auto"},
       {"code":"GLAZE","when":"auto"},
       {"code":"QC","when":"required"},
       {"code":"PACK","when":"required"}
     ]'::jsonb,
     '{"HANDLE_PREP":"HARDWARE","SAW_CUT":"CUT"}'::jsonb,
     '["HANDLE_PREP"]'::jsonb,
     '{"source":"SEED","authority":"GLOBAL"}'::jsonb),

    -- Honest fallback when no authority matches: assembly only, no invented
    -- thermal/mechanical joining steps.
    (NULL, 'GENERIC_LEGACY', 1, 'Genérico — sin autoridad de proceso', NULL, 'STANDARD',
     'NONE', 'NONE', false,
     '[
       {"code":"CUT","when":"auto"},
       {"code":"ASSEMBLE","when":"auto"},
       {"code":"GLAZE","when":"auto"},
       {"code":"QC","when":"required"},
       {"code":"PACK","when":"required"}
     ]'::jsonb,
     '{"SAW_CUT":"CUT"}'::jsonb,
     '[]'::jsonb,
     '{"source":"SEED","authority":"GLOBAL"}'::jsonb);

GRANT SELECT ON public.manufacturing_process_profiles TO authenticated;
GRANT SELECT ON public.manufacturing_process_profiles TO documentary_backend;
GRANT SELECT (process_profile_id) ON public.profile_systems TO authenticated;
REVOKE ALL ON public.manufacturing_process_profiles FROM anon;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER ON public.manufacturing_process_profiles FROM authenticated;

COMMIT;
