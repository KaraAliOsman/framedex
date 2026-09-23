-- Deterministic global catalog required by the SHOT-02 gate.

INSERT INTO public.profile_systems (
    id,
    org_id,
    code,
    name,
    depth_mm,
    material,
    chamber_count,
    sash_overlap_mm,
    glass_clearance_white_mm,
    central_overlap_mm,
    sliding_end_add_mm,
    sliding_glazing_deduction_width_mm,
    sliding_glazing_deduction_height_mm,
    door_leaf_side_clearance_mm,
    is_global,
    is_demo
)
VALUES (
    uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60'),
    NULL,
    'DEMO_60',
    'Sistema Demo 60mm PVC',
    60.00,
    'PVC',
    3,
    8.00,
    5.00,
    40.00,
    6.00,
    20.00,
    20.00,
    7.00,
    TRUE,
    TRUE
)
ON CONFLICT (id) DO UPDATE SET
    org_id = EXCLUDED.org_id,
    code = EXCLUDED.code,
    name = EXCLUDED.name,
    depth_mm = EXCLUDED.depth_mm,
    material = EXCLUDED.material,
    chamber_count = EXCLUDED.chamber_count,
    sash_overlap_mm = EXCLUDED.sash_overlap_mm,
    glass_clearance_white_mm = EXCLUDED.glass_clearance_white_mm,
    central_overlap_mm = EXCLUDED.central_overlap_mm,
    sliding_end_add_mm = EXCLUDED.sliding_end_add_mm,
    sliding_glazing_deduction_width_mm = EXCLUDED.sliding_glazing_deduction_width_mm,
    sliding_glazing_deduction_height_mm = EXCLUDED.sliding_glazing_deduction_height_mm,
    door_leaf_side_clearance_mm = EXCLUDED.door_leaf_side_clearance_mm,
    is_global = EXCLUDED.is_global,
    is_demo = EXCLUDED.is_demo;

INSERT INTO public.profile_articles (
    id,
    system_id,
    org_id,
    sku,
    name,
    role,
    face_width_mm,
    commercial_length_mm,
    welding_loss_mm,
    reinforcement_gap_mm
)
VALUES
    (
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60/MARCO'),
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60'),
        NULL,
        'MARCO',
        'Marco Demo 60',
        'FRAME',
        60.00,
        6000.00,
        6.00,
        15.00
    ),
    (
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60/HOJA'),
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60'),
        NULL,
        'HOJA',
        'Hoja Demo 60',
        'SASH',
        75.00,
        6000.00,
        6.00,
        15.00
    ),
    (
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60/POSTE-V'),
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60'),
        NULL,
        'POSTE-V',
        'Poste Vertical Demo 60',
        'MULLION_V',
        80.00,
        6000.00,
        0.00,
        5.00
    ),
    (
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60/POSTE-H'),
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60'),
        NULL,
        'POSTE-H',
        'Travesaño Horizontal Demo 60',
        'MULLION_H',
        80.00,
        6000.00,
        0.00,
        5.00
    ),
    (
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60/JQ-24'),
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60'),
        NULL,
        'JQ-24',
        'Junquillo Demo 60 24mm',
        'GLAZING_BEAD',
        24.00,
        6000.00,
        0.00,
        15.00
    ),
    (
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60/JQ-14'),
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60'),
        NULL,
        'JQ-14',
        'Junquillo Demo 60 14mm',
        'GLAZING_BEAD',
        14.00,
        6000.00,
        0.00,
        15.00
    ),
    (
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60/JQ-10'),
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60'),
        NULL,
        'JQ-10',
        'Junquillo Demo 60 10mm',
        'GLAZING_BEAD',
        10.00,
        6000.00,
        0.00,
        15.00
    )
ON CONFLICT (id) DO UPDATE SET
    system_id = EXCLUDED.system_id,
    org_id = EXCLUDED.org_id,
    sku = EXCLUDED.sku,
    name = EXCLUDED.name,
    role = EXCLUDED.role,
    face_width_mm = EXCLUDED.face_width_mm,
    commercial_length_mm = EXCLUDED.commercial_length_mm,
    welding_loss_mm = EXCLUDED.welding_loss_mm,
    reinforcement_gap_mm = EXCLUDED.reinforcement_gap_mm;

INSERT INTO public.hardware_kits (
    id,
    org_id,
    system_id,
    sku,
    name,
    opening_type,
    min_leaf_width_mm,
    max_leaf_width_mm,
    min_leaf_height_mm,
    max_leaf_height_mm,
    max_leaf_weight_kg,
    carriages_qty,
    stay_arms_qty
)
VALUES
    (
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60/KIT-TURN'),
        NULL,
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60'),
        'KIT-TURN',
        'Kit Practicable Demo 60',
        'TURN',
        400.00,
        1200.00,
        500.00,
        2400.00,
        80.00,
        0,
        0
    ),
    (
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60/KIT-TILT-TURN'),
        NULL,
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60'),
        'KIT-TILT-TURN',
        'Kit Vorne OB 100kg',
        'TILT_TURN',
        450.00,
        1400.00,
        600.00,
        2400.00,
        100.00,
        0,
        1
    ),
    (
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60/KIT-SLIDING'),
        NULL,
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60'),
        'KIT-SLIDING',
        'Kit Corredera Demo 60',
        'SLIDING',
        400.00,
        1500.00,
        500.00,
        2500.00,
        120.00,
        2,
        0
    )
ON CONFLICT (id) DO UPDATE SET
    org_id = EXCLUDED.org_id,
    system_id = EXCLUDED.system_id,
    sku = EXCLUDED.sku,
    name = EXCLUDED.name,
    opening_type = EXCLUDED.opening_type,
    min_leaf_width_mm = EXCLUDED.min_leaf_width_mm,
    max_leaf_width_mm = EXCLUDED.max_leaf_width_mm,
    min_leaf_height_mm = EXCLUDED.min_leaf_height_mm,
    max_leaf_height_mm = EXCLUDED.max_leaf_height_mm,
    max_leaf_weight_kg = EXCLUDED.max_leaf_weight_kg,
    carriages_qty = EXCLUDED.carriages_qty,
    stay_arms_qty = EXCLUDED.stay_arms_qty;

INSERT INTO public.glazing_bead_matrix (
    id,
    system_id,
    org_id,
    glass_thickness_mm,
    bead_article_id,
    bead_width_mm,
    gasket_interior_mm,
    gasket_exterior_mm,
    cut_add_mm
)
VALUES
    (
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60/GLASS-4'),
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60'),
        NULL,
        4.00,
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60/JQ-24'),
        24.00,
        3.00,
        3.00,
        9.00
    ),
    (
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60/GLASS-5'),
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60'),
        NULL,
        5.00,
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60/JQ-24'),
        24.00,
        2.50,
        2.50,
        9.00
    ),
    (
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60/GLASS-6'),
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60'),
        NULL,
        6.00,
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60/JQ-24'),
        24.00,
        2.00,
        2.00,
        9.00
    ),
    (
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60/GLASS-20'),
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60'),
        NULL,
        20.00,
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60/JQ-14'),
        14.00,
        3.00,
        3.00,
        9.00
    ),
    (
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60/GLASS-24'),
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60'),
        NULL,
        24.00,
        uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60/JQ-10'),
        10.00,
        3.00,
        3.00,
        9.00
    )
ON CONFLICT (id) DO UPDATE SET
    system_id = EXCLUDED.system_id,
    org_id = EXCLUDED.org_id,
    glass_thickness_mm = EXCLUDED.glass_thickness_mm,
    bead_article_id = EXCLUDED.bead_article_id,
    bead_width_mm = EXCLUDED.bead_width_mm,
    gasket_interior_mm = EXCLUDED.gasket_interior_mm,
    gasket_exterior_mm = EXCLUDED.gasket_exterior_mm,
    cut_add_mm = EXCLUDED.cut_add_mm;

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

INSERT INTO public.profile_articles (
    id, system_id, org_id, sku, name, role, material,
    face_width_mm, commercial_length_mm, welding_loss_mm, reinforcement_gap_mm,
    weight_kg_m, steel_weight_kg_m
)
SELECT uuid_generate_v5(uuid_ns_url(), 'https://dekopen.local/catalog/DEMO_60/' || coupler.sku),
    system.id, NULL, coupler.sku, coupler.name, 'COUPLER', 'PVC',
    coupler.face_mm, 6000.00, 6.00, 15.00, coupler.weight, 1.7000
FROM public.profile_systems AS system
CROSS JOIN (VALUES
    ('COPLE-60', 'Acoplador Angular Demo 60/30', 30.00::numeric, 0.9000::numeric),
    ('COPLE-90', 'Acoplador Angular Demo 60/34', 34.00::numeric, 1.1000::numeric)
) AS coupler(sku, name, face_mm, weight)
WHERE system.code = 'DEMO_60' AND system.is_global = TRUE
ON CONFLICT (system_id, sku) DO UPDATE SET
    name = EXCLUDED.name, role = EXCLUDED.role, material = EXCLUDED.material,
    face_width_mm = EXCLUDED.face_width_mm,
    commercial_length_mm = EXCLUDED.commercial_length_mm,
    welding_loss_mm = EXCLUDED.welding_loss_mm,
    reinforcement_gap_mm = EXCLUDED.reinforcement_gap_mm,
    weight_kg_m = EXCLUDED.weight_kg_m,
    steel_weight_kg_m = EXCLUDED.steel_weight_kg_m;

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

-- DEMO_60 SYNTHETIC FIXTURE. No manufacturer certification or new mass authority.
UPDATE public.profile_systems SET chamber_clearance_mm=12.00
 WHERE code='DEMO_60' AND is_global=TRUE;
INSERT INTO public.cutting_profiles
 (id, org_id, code, name, kerf_mm, head_trim_mm, tail_trim_mm, is_default, is_active)
VALUES (uuid_generate_v5(uuid_ns_url(),'https://dekopen.local/shot07/cutting/DEMO'),
 NULL,'DEMO','DEMO_60 SYNTHETIC FIXTURE',4.00,15.00,15.00,TRUE,TRUE)
ON CONFLICT (id) DO NOTHING;
INSERT INTO public.profile_purchase_mappings
 (id,profile_article_id,org_id,commercial_sku,manufacturer_name,supplier_name,purchase_unit)
SELECT uuid_generate_v5(uuid_ns_url(),'https://dekopen.local/shot07/purchase/'||article.id),
 article.id,NULL,'DEMO-BAR-'||article.sku,'DEMO_60 SYNTHETIC FIXTURE','DEMO-SUPPLIER','BAR'
FROM public.profile_articles article JOIN public.profile_systems system ON system.id=article.system_id
WHERE system.code='DEMO_60' AND system.is_global=TRUE AND article.org_id IS NULL
ON CONFLICT (id) DO NOTHING;
INSERT INTO public.reinforcement_articles
 (id,system_id,org_id,parent_profile_article_id,sku,commercial_sku,name,
 manufacturer_name,supplier_name,stock_length_mm,purchase_unit,is_default)
SELECT uuid_generate_v5(uuid_ns_url(),'https://dekopen.local/shot07/steel/'||article.id),
 system.id,NULL,article.id,'DEMO-STEEL-'||article.sku,'DEMO-STEEL-BAR-'||article.sku,
 'DEMO_60 SYNTHETIC FIXTURE','DEMO_60 SYNTHETIC FIXTURE','DEMO-SUPPLIER',6000.00,'BAR',TRUE
FROM public.profile_articles article JOIN public.profile_systems system ON system.id=article.system_id
WHERE system.code='DEMO_60' AND system.is_global=TRUE AND article.org_id IS NULL
 AND article.role NOT IN ('GLAZING_BEAD','THRESHOLD')
ON CONFLICT (id) DO NOTHING;
INSERT INTO public.inspector_rule_configs (id,system_id,org_id,rule_id,params)
SELECT uuid_generate_v5(uuid_ns_url(),'https://dekopen.local/shot07/config/'||system.id||'/'||cfg.rule_id),
 system.id,NULL,cfg.rule_id,cfg.params
FROM public.profile_systems system CROSS JOIN (VALUES
 ('R01', '{}'::JSONB),
 ('R02', '{"min_ratio":"0.4000","max_ratio":"2.5000","suggested_ratio":"1.5000"}'::JSONB),
 ('R03', '{"min_width_mm":"350.00","max_width_mm":"1600.00","max_height_mm":"2400.00"}'::JSONB),
 ('R04', '{"monolithic_4_max_area_m2":"1.8000","dvh_4_any_4_max_area_m2":"2.6000"}'::JSONB),
 ('R05', '{"span_trigger_mm":"1800.00"}'::JSONB),
 ('R06', '{}'::JSONB),
 ('R07', '{"width_trigger_mm":"800.00","required_bottom_drains":3}'::JSONB),
 ('R08', '{"max_spacing_mm":"800.00"}'::JSONB),
 ('R09', '{"white_limit_mm":"4000.00","foiled_limit_mm":"3000.00"}'::JSONB),
 ('R10', '{"tolerance_mm":"1.50"}'::JSONB),
 ('R11', '{"expected_mm":"12.00","tolerance_mm":"1.50","suggested_sash_overlap_mm":"8.00"}'::JSONB),
 ('R12', '{"width_trigger_mm":"4500.00","minimum_ix_cm4":"45.0000"}'::JSONB),
 ('R13', '{"height_trigger_mm":"1200.00","required_stay_arms":2}'::JSONB),
 ('R14', '{"weight_trigger_kg":"150.00","required_carriages":4,"minimum_capacity_kg":"80.00"}'::JSONB)
) cfg(rule_id,params)
WHERE system.code='DEMO_60' AND system.is_global=TRUE
ON CONFLICT (system_id,org_id,rule_id) DO NOTHING;

DO $shot09$
BEGIN
IF to_regclass('public.manufacturing_placement_policies') IS NOT NULL THEN
UPDATE public.profile_purchase_mappings AS mapping
SET physical_stock_identity=uuid_generate_v5(
     uuid_ns_url(),'https://dekopen.local/shot09/physical/profile/'||mapping.profile_article_id),
    stock_color='WHITE',
    cutting_profile_id=uuid_generate_v5(uuid_ns_url(),'https://dekopen.local/shot07/cutting/DEMO'),
    binding_version=1
FROM public.profile_articles article JOIN public.profile_systems system ON system.id=article.system_id
WHERE mapping.profile_article_id=article.id AND system.code='DEMO_60' AND system.is_global=TRUE
 AND mapping.org_id IS NULL;
UPDATE public.reinforcement_articles AS reinforcement
SET physical_stock_identity=uuid_generate_v5(
     uuid_ns_url(),'https://dekopen.local/shot09/physical/steel/'||reinforcement.id),
    stock_color='WHITE',
    cutting_profile_id=uuid_generate_v5(uuid_ns_url(),'https://dekopen.local/shot07/cutting/DEMO'),
    binding_version=1
FROM public.profile_systems system
WHERE reinforcement.system_id=system.id AND system.code='DEMO_60' AND system.is_global=TRUE
 AND reinforcement.org_id IS NULL;

INSERT INTO public.manufacturing_placement_policies (id,system_id,org_id,version,authority)
SELECT uuid_generate_v5(uuid_ns_url(),'https://dekopen.local/shot09/placement/DEMO_60/V1'),
 system.id,NULL,1,'{"schema_version":1,"policy_id":"DEMO_60_PLACEMENT_V1","version":1,"sliding_leaf_offsets":{"L1":{"x_mm":"0.00","y_mm":"0.00"},"L2":{"x_mm":"940.00","y_mm":"0.00"}},"sliding_infill_offsets":{"L1":{"x_mm":"70.00","y_mm":"70.00"},"L2":{"x_mm":"70.00","y_mm":"70.00"}},"bead_offsets":{"TOP":{"x_mm":"0.00","y_mm":"0.00"},"RIGHT":{"x_mm":"0.00","y_mm":"0.00"},"BOTTOM":{"x_mm":"0.00","y_mm":"0.00"},"LEFT":{"x_mm":"0.00","y_mm":"0.00"}}}'::jsonb
FROM public.profile_systems system
WHERE system.code='DEMO_60' AND system.is_global=TRUE
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.handle_requirement_policies (id,system_id,org_id,version,authority)
SELECT uuid_generate_v5(uuid_ns_url(),'https://dekopen.local/shot09/handles/DEMO_60/V1'),
 system.id,NULL,1,'{"schema_version":1,"policy_id":"DEMO_60_HANDLES_V1","version":1,"slots":[{"opening_type":"TURN_LEFT","leaf_slot":null,"handle_domain_slot":"PRIMARY","host_member_side":"RIGHT","horizontal_reference":"HOST_MEMBER_AXIS","horizontal_offset_mm":"-10.00","permitted_vertical_references":["OUTER_TOP","OUTER_BOTTOM","LEAF_TOP","LEAF_BOTTOM"],"mounting_min_from_leaf_top_mm":"0.00","mounting_max_from_leaf_top_mm":"3000.00"},{"opening_type":"TURN_RIGHT","leaf_slot":null,"handle_domain_slot":"PRIMARY","host_member_side":"RIGHT","horizontal_reference":"HOST_MEMBER_AXIS","horizontal_offset_mm":"-10.00","permitted_vertical_references":["OUTER_TOP","OUTER_BOTTOM","LEAF_TOP","LEAF_BOTTOM"],"mounting_min_from_leaf_top_mm":"0.00","mounting_max_from_leaf_top_mm":"3000.00"},{"opening_type":"TILT_TURN_LEFT","leaf_slot":null,"handle_domain_slot":"PRIMARY","host_member_side":"RIGHT","horizontal_reference":"HOST_MEMBER_AXIS","horizontal_offset_mm":"-10.00","permitted_vertical_references":["OUTER_TOP","OUTER_BOTTOM","LEAF_TOP","LEAF_BOTTOM"],"mounting_min_from_leaf_top_mm":"0.00","mounting_max_from_leaf_top_mm":"3000.00"},{"opening_type":"TILT_TURN_RIGHT","leaf_slot":null,"handle_domain_slot":"PRIMARY","host_member_side":"RIGHT","horizontal_reference":"HOST_MEMBER_AXIS","horizontal_offset_mm":"-10.00","permitted_vertical_references":["OUTER_TOP","OUTER_BOTTOM","LEAF_TOP","LEAF_BOTTOM"],"mounting_min_from_leaf_top_mm":"0.00","mounting_max_from_leaf_top_mm":"3000.00"},{"opening_type":"SLIDING_2L","leaf_slot":"L1","handle_domain_slot":"PRIMARY","host_member_side":"RIGHT","horizontal_reference":"HOST_MEMBER_AXIS","horizontal_offset_mm":"-10.00","permitted_vertical_references":["OUTER_TOP","OUTER_BOTTOM","LEAF_TOP","LEAF_BOTTOM"],"mounting_min_from_leaf_top_mm":"0.00","mounting_max_from_leaf_top_mm":"3000.00"},{"opening_type":"SLIDING_2L","leaf_slot":"L2","handle_domain_slot":"PRIMARY","host_member_side":"RIGHT","horizontal_reference":"HOST_MEMBER_AXIS","horizontal_offset_mm":"-10.00","permitted_vertical_references":["OUTER_TOP","OUTER_BOTTOM","LEAF_TOP","LEAF_BOTTOM"],"mounting_min_from_leaf_top_mm":"0.00","mounting_max_from_leaf_top_mm":"3000.00"},{"opening_type":"AWNING","leaf_slot":null,"handle_domain_slot":"PRIMARY","host_member_side":"RIGHT","horizontal_reference":"HOST_MEMBER_AXIS","horizontal_offset_mm":"-10.00","permitted_vertical_references":["OUTER_TOP","OUTER_BOTTOM","LEAF_TOP","LEAF_BOTTOM"],"mounting_min_from_leaf_top_mm":"0.00","mounting_max_from_leaf_top_mm":"3000.00"},{"opening_type":"DOOR_ENTRY","leaf_slot":null,"handle_domain_slot":"PRIMARY","host_member_side":"RIGHT","horizontal_reference":"HOST_MEMBER_AXIS","horizontal_offset_mm":"-10.00","permitted_vertical_references":["OUTER_TOP","OUTER_BOTTOM","LEAF_TOP","LEAF_BOTTOM"],"mounting_min_from_leaf_top_mm":"0.00","mounting_max_from_leaf_top_mm":"3000.00"}]}'::jsonb
FROM public.profile_systems system
WHERE system.code='DEMO_60' AND system.is_global=TRUE
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.reinforcement_cut_policies (id,system_id,org_id,version,authority)
SELECT uuid_generate_v5(uuid_ns_url(),'https://dekopen.local/shot09/reinforcement-cuts/DEMO_60/V1'),
 system.id,NULL,1,'{"schema_version":1,"policy_id":"DEMO_60_REINFORCEMENT_CUT_V1","version":1,"rules":[{"role":"FRAME","profile_angle_left":"45.0","profile_angle_right":"45.0","reinforcement_angle_left":"90.0","reinforcement_angle_right":"90.0","length_authority":"EXISTING_ENGINE","compatible_with_existing_length":true},{"role":"FRAME","profile_angle_left":"45.0","profile_angle_right":"90.0","reinforcement_angle_left":"90.0","reinforcement_angle_right":"90.0","length_authority":"EXISTING_ENGINE","compatible_with_existing_length":true},{"role":"SASH","profile_angle_left":"45.0","profile_angle_right":"45.0","reinforcement_angle_left":"90.0","reinforcement_angle_right":"90.0","length_authority":"EXISTING_ENGINE","compatible_with_existing_length":true},{"role":"MULLION_V","profile_angle_left":"90.0","profile_angle_right":"90.0","reinforcement_angle_left":"90.0","reinforcement_angle_right":"90.0","length_authority":"EXISTING_ENGINE","compatible_with_existing_length":true},{"role":"MULLION_H","profile_angle_left":"90.0","profile_angle_right":"90.0","reinforcement_angle_left":"90.0","reinforcement_angle_right":"90.0","length_authority":"EXISTING_ENGINE","compatible_with_existing_length":true},{"role":"COUPLER","profile_angle_left":"90.0","profile_angle_right":"90.0","reinforcement_angle_left":"90.0","reinforcement_angle_right":"90.0","length_authority":"EXISTING_ENGINE","compatible_with_existing_length":true}]}'::jsonb
FROM public.profile_systems system
WHERE system.code='DEMO_60' AND system.is_global=TRUE
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.glass_purchase_mappings
 (id,system_id,org_id,technical_sku,purchasing_sku,manufacturer_name,purchase_unit,version,provenance)
SELECT uuid_generate_v5(uuid_ns_url(),'https://dekopen.local/shot09/glass/DEMO_60/GLASS-BASE/V1'),
 system.id,NULL,'GLASS-BASE','DEMO-GLASS-FINISHED-UNIT','DEMO_60 SYNTHETIC FIXTURE','EA',1,
 '{"source":"DEMO_60 SYNTHETIC FIXTURE","certified":"false"}'::jsonb
FROM public.profile_systems system
WHERE system.code='DEMO_60' AND system.is_global=TRUE
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.hardware_purchase_mappings
 (id,hardware_kit_id,org_id,purchasing_sku,manufacturer_name,purchase_unit,version,provenance)
SELECT uuid_generate_v5(uuid_ns_url(),'https://dekopen.local/shot09/hardware/'||kit.id||'/V1'),
 kit.id,NULL,'DEMO-BUY-'||kit.sku,'DEMO_60 SYNTHETIC FIXTURE','KIT',1,
 '{"source":"DEMO_60 SYNTHETIC FIXTURE","mode":"KIT_ONLY"}'::jsonb
FROM public.hardware_kits kit JOIN public.profile_systems system ON system.id=kit.system_id
WHERE system.code='DEMO_60' AND system.is_global=TRUE AND kit.org_id IS NULL
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.panel_purchase_authorities
 (id,infill_article_id,org_id,purchasing_sku,manufacturer_name,supply_form,purchase_unit,version,provenance)
SELECT uuid_generate_v5(uuid_ns_url(),'https://dekopen.local/shot09/panel/'||panel.id||'/V1'),
 panel.id,NULL,'DEMO-BUY-'||panel.sku,'DEMO_60 SYNTHETIC FIXTURE','CUT_TO_SIZE','EA',1,
 '{"source":"DEMO_60 SYNTHETIC FIXTURE","certified":"false"}'::jsonb
FROM public.infill_articles panel JOIN public.profile_systems system ON system.id=panel.system_id
WHERE system.code='DEMO_60' AND system.is_global=TRUE AND panel.org_id IS NULL
ON CONFLICT (id) DO NOTHING;
END IF;
END;
$shot09$;

COMMIT;
