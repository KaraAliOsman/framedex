BEGIN;

-- Synthetic DEMO_60 fixtures, not manufacturer specifications.
UPDATE public.hardware_kits AS kit
SET weight_kg = 2.50,
    name = CASE WHEN kit.sku = 'KIT-TILT-TURN' THEN 'Kit Vorne OB 100kg' ELSE kit.name END
FROM public.profile_systems AS system
WHERE kit.system_id = system.id AND system.code = 'DEMO_60' AND system.is_global = TRUE
  AND kit.sku IN ('KIT-TURN', 'KIT-TILT-TURN', 'KIT-SLIDING');

INSERT INTO public.profile_articles (
    id, system_id, org_id, sku, name, role, material,
    face_width_mm, welding_loss_mm, reinforcement_gap_mm, reinforcement_sku
)
SELECT uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60/UMBRAL-ALU'),
    system.id, NULL, 'UMBRAL-ALU', 'Umbral Aluminio Demo 60', 'THRESHOLD', 'ALUMINIUM',
    30.00, 0.00, 0.00, NULL
FROM public.profile_systems AS system
WHERE system.code = 'DEMO_60' AND system.is_global = TRUE
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name, role = EXCLUDED.role, material = EXCLUDED.material,
    face_width_mm = EXCLUDED.face_width_mm, welding_loss_mm = EXCLUDED.welding_loss_mm,
    reinforcement_gap_mm = EXCLUDED.reinforcement_gap_mm,
    reinforcement_sku = EXCLUDED.reinforcement_sku;

INSERT INTO public.infill_articles (
    id, system_id, org_id, sku, name, kind, thickness_mm, weight_kg_m2
)
SELECT uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60/PANEL-SANDWICH-DEMO-24'),
    system.id, NULL, 'PANEL-SANDWICH-DEMO-24', 'Panel Sándwich Demo 24mm',
    'SANDWICH_PANEL', 24.00, 10.0000
FROM public.profile_systems AS system
WHERE system.code = 'DEMO_60' AND system.is_global = TRUE
ON CONFLICT (system_id, sku) DO UPDATE SET
    name = EXCLUDED.name, kind = EXCLUDED.kind,
    thickness_mm = EXCLUDED.thickness_mm, weight_kg_m2 = EXCLUDED.weight_kg_m2;

INSERT INTO public.hardware_kits (
    id, system_id, org_id, sku, name, opening_type,
    min_leaf_width_mm, max_leaf_width_mm, min_leaf_height_mm, max_leaf_height_mm,
    max_leaf_weight_kg, rail_type, carriages_qty, stay_arms_qty, weight_kg, contents
)
SELECT uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60/' || fixture.sku),
    system.id, NULL, fixture.sku, fixture.name, fixture.opening_type,
    fixture.min_w, fixture.max_w, fixture.min_h, fixture.max_h, fixture.max_weight,
    'dual', 0, fixture.stays, 2.50, fixture.contents
FROM public.profile_systems AS system
CROSS JOIN (VALUES
    ('KIT-AWNING-16', 'Kit Proyectante Compás 16" 45kg', 'AWNING',
     400.00, 1200.00, 400.00, 1000.00, 45.00, 2,
     '[{"sku":"DEMO-STAY-16","name":"Compás a fricción 16\"","qty":2,"unit":"unit"}]'::JSONB),
    ('KIT-DOOR-MULTIPOINT', 'Kit Puerta Entrada Multipunto Demo 60', 'DOOR',
     700.00, 1200.00, 1800.00, 2400.00, 120.00, 0,
     '[{"sku":"DEMO-LOCK-MULTIPOINT","name":"Cerradura multipunto Demo","qty":1,"unit":"unit"}]'::JSONB)
) AS fixture(sku, name, opening_type, min_w, max_w, min_h, max_h, max_weight, stays, contents)
WHERE system.code = 'DEMO_60' AND system.is_global = TRUE
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name, opening_type = EXCLUDED.opening_type,
    min_leaf_width_mm = EXCLUDED.min_leaf_width_mm,
    max_leaf_width_mm = EXCLUDED.max_leaf_width_mm,
    min_leaf_height_mm = EXCLUDED.min_leaf_height_mm,
    max_leaf_height_mm = EXCLUDED.max_leaf_height_mm,
    max_leaf_weight_kg = EXCLUDED.max_leaf_weight_kg,
    rail_type = EXCLUDED.rail_type, carriages_qty = EXCLUDED.carriages_qty,
    stay_arms_qty = EXCLUDED.stay_arms_qty, weight_kg = EXCLUDED.weight_kg,
    contents = EXCLUDED.contents;

COMMIT;
