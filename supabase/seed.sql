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
        'Kit Oscilobatiente Demo 60',
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
