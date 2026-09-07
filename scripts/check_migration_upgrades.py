"""Exercise SHOT-06 on populated SHOT-05 catalogs in independent PostgreSQL 16."""

from pathlib import Path
import subprocess

import local_gates

ROOT = Path(__file__).resolve().parents[1]


def verify(container: str) -> None:
    docker = local_gates.executable("docker")

    def sql(database: str, source: str, *, expected_error: str | None = None) -> None:
        command = [docker, "exec", "-i", container, "psql", "-v", "ON_ERROR_STOP=1",
                   "-U", "postgres", "-d", database]
        if expected_error is None:
            local_gates.run(command, input_text=source)
            return
        result = subprocess.run(command, input=source, capture_output=True, text=True,
                                encoding="utf-8", check=False)
        if result.returncode != 3 or expected_error not in result.stderr:
            raise RuntimeError("Missing-authority migration did not fail as specified: "
                               + local_gates.redact(result.stdout + result.stderr))
        print("  Missing-authority upgrade: deliberate rejection confirmed", flush=True)

    bootstrap = (ROOT / "supabase/compat/postgres16_bootstrap.sql").read_text(encoding="utf-8")
    # Roles are cluster-wide and already created by the clean PostgreSQL 16 gate.
    bootstrap = bootstrap[bootstrap.index("CREATE SCHEMA auth;"):]
    historical = [ROOT / "supabase/migrations" / name for name in (
        "20260901000000_initial_schema.sql", "20260902000000_add_glazing_bead_cut_add.sql",
    )]
    authorities = (ROOT / "supabase/migrations/20260905000000_shot_06_catalog_authorities.sql").read_text(encoding="utf-8")
    catalog = (ROOT / "supabase/migrations/20260905000100_shot_06_demo_catalog.sql").read_text(encoding="utf-8")
    for database in ("shot06_upgrade", "shot06_unresolved"):
        sql("postgres", f"CREATE DATABASE {database};")
        sql(database, bootstrap)
        for path in historical:
            sql(database, path.read_text(encoding="utf-8"))

    sql("shot06_upgrade", """
        INSERT INTO public.profile_systems (id, code, name, depth_mm, is_global, is_demo)
        VALUES ('3067da09-3119-5ad0-a1d5-498cd2dfd753', 'DEMO_60', 'Upgrade fixture', 60.00, TRUE, TRUE);
        INSERT INTO public.profile_articles (system_id, sku, name, role, face_width_mm)
        VALUES ('3067da09-3119-5ad0-a1d5-498cd2dfd753', 'MARCO', 'Historical frame', 'FRAME', 60.00);
        INSERT INTO public.hardware_kits (system_id, sku, name, opening_type,
            min_leaf_width_mm, max_leaf_width_mm, min_leaf_height_mm, max_leaf_height_mm,
            max_leaf_weight_kg, carriages_qty, stay_arms_qty)
        VALUES ('3067da09-3119-5ad0-a1d5-498cd2dfd753', 'KIT-TILT-TURN', 'Kit Oscilobatiente Demo 60',
            'TILT_TURN', 450.00, 1400.00, 600.00, 2400.00, 100.00, 0, 1);
    """)
    sql("shot06_upgrade", authorities)
    sql("shot06_upgrade", catalog)
    sql("shot06_upgrade", """
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM public.profile_systems WHERE code = 'DEMO_60'
                AND sliding_glazing_deduction_width_mm = 20.00
                AND sliding_glazing_deduction_height_mm = 20.00
                AND door_leaf_side_clearance_mm = 7.00) THEN
                RAISE EXCEPTION 'DEMO authority backfill failed';
            END IF;
            IF NOT EXISTS (SELECT 1 FROM public.profile_articles WHERE sku = 'MARCO'
                AND material = 'PVC' AND face_width_mm = 60.00 AND welding_loss_mm = 6.00) THEN
                RAISE EXCEPTION 'Historical profile changed during upgrade';
            END IF;
            IF NOT EXISTS (SELECT 1 FROM public.hardware_kits WHERE sku = 'KIT-TILT-TURN'
                AND name = 'Kit Vorne OB 100kg' AND weight_kg = 2.50 AND max_leaf_weight_kg = 100.00
                AND min_leaf_width_mm = 450.00 AND max_leaf_width_mm = 1400.00) THEN
                RAISE EXCEPTION 'Historical kit authority upgrade failed';
            END IF;
            IF (SELECT count(*) FROM public.infill_articles WHERE weight_kg_m2 = 10.0000) <> 1
                OR (SELECT count(*) FROM public.hardware_kits) <> 3
                OR (SELECT count(*) FROM public.profile_articles WHERE role = 'THRESHOLD') <> 1 THEN
                RAISE EXCEPTION 'New synthetic catalog upgrade failed';
            END IF;
        END $$;
    """)
    print("  Populated SHOT-05 DEMO catalog upgrade: PASS", flush=True)
    sql("shot06_upgrade", """
        CREATE TABLE shot07_before AS SELECT
          (SELECT jsonb_agg(to_jsonb(s) ORDER BY id) FROM public.profile_systems s) systems,
          (SELECT jsonb_agg(to_jsonb(p) ORDER BY id) FROM public.profile_articles p) profiles,
          (SELECT jsonb_agg(to_jsonb(k) ORDER BY id) FROM public.hardware_kits k) kits;
    """)
    for name in ("20260906000000_shot_07_authorities.sql",
                 "20260906000100_shot_07_demo_catalog.sql"):
        sql("shot06_upgrade", (ROOT / "supabase/migrations" / name).read_text(encoding="utf-8"))
    sql("shot06_upgrade", """
        DO $$ BEGIN
          IF (SELECT jsonb_agg(to_jsonb(s)-'chamber_clearance_mm' ORDER BY id)
              FROM public.profile_systems s) IS DISTINCT FROM (SELECT systems FROM shot07_before)
             OR (SELECT jsonb_agg(to_jsonb(p) ORDER BY id) FROM public.profile_articles p)
                IS DISTINCT FROM (SELECT profiles FROM shot07_before)
             OR (SELECT jsonb_agg(to_jsonb(k)-'carriage_capacity_kg' ORDER BY id)
                 FROM public.hardware_kits k) IS DISTINCT FROM (SELECT kits FROM shot07_before)
          THEN RAISE EXCEPTION 'SHOT-07 changed existing SHOT-06 catalog data'; END IF;
          IF (SELECT count(*) FROM public.inspector_rule_configs) <> 14
             OR NOT EXISTS (SELECT 1 FROM public.profile_systems
                 WHERE code='DEMO_60' AND chamber_clearance_mm=12.00)
             OR NOT EXISTS (SELECT 1 FROM public.cutting_profiles WHERE code='DEMO'
                 AND kerf_mm=4 AND head_trim_mm=15 AND tail_trim_mm=15)
             OR to_regclass('public.profile_purchase_mappings') IS NULL
             OR to_regclass('public.reinforcement_articles') IS NULL
          THEN RAISE EXCEPTION 'SHOT-07 explicit fixture upgrade failed'; END IF;
        END $$;
        INSERT INTO public.profile_systems (code,name,depth_mm,
          sliding_glazing_deduction_width_mm,sliding_glazing_deduction_height_mm,
          door_leaf_side_clearance_mm)
        VALUES ('LEGACY-NO-INSPECTOR','Historical non-inspector system',60,20,20,7);
        DO $$ DECLARE target UUID; BEGIN
          SELECT id INTO target FROM public.profile_systems WHERE code='LEGACY-NO-INSPECTOR';
          IF NOT EXISTS (SELECT 1 FROM public.profile_systems
                         WHERE id=target AND chamber_clearance_mm IS NULL)
          THEN RAISE EXCEPTION 'Legacy nullable authority not preserved'; END IF;
          BEGIN
            INSERT INTO public.inspector_rule_configs(system_id,rule_id,params)
            VALUES (target,'R01','{}');
            RAISE EXCEPTION 'Missing clearance unexpectedly accepted';
          EXCEPTION WHEN raise_exception THEN
            IF SQLERRM <> 'Inspector requires explicit chamber clearance' THEN RAISE; END IF;
          END;
          IF EXISTS (SELECT 1 FROM public.inspector_rule_configs WHERE system_id=target)
          THEN RAISE EXCEPTION 'Failed config activation did not roll back'; END IF;
        END $$;
    """)
    print("  SHOT-07 populated upgrade, existing authorities and activation rollback: PASS",
          flush=True)
    sql("shot06_unresolved", """
        INSERT INTO public.profile_systems (code, name, depth_mm)
        VALUES ('UNRESOLVED-CATALOG', 'No approved SHOT-06 authority', 70.00);
    """)
    sql("shot06_unresolved", authorities,
        expected_error="SHOT-06 geometry requires explicit catalog authorities")
    sql("shot06_unresolved", """
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public'
                AND table_name = 'profile_systems' AND column_name = 'door_leaf_side_clearance_mm')
                OR to_regclass('public.infill_articles') IS NOT NULL
                OR EXISTS (SELECT 1 FROM pg_enum WHERE enumtypid = 'public.profile_role'::REGTYPE
                    AND enumlabel = 'THRESHOLD') THEN
                RAISE EXCEPTION 'Failed upgrade did not roll back atomically';
            END IF;
            IF (SELECT count(*) FROM public.profile_systems WHERE code = 'UNRESOLVED-CATALOG') <> 1 THEN
                RAISE EXCEPTION 'Failed upgrade damaged the existing catalog';
            END IF;
        END $$;
    """)
    print("  Missing-authority transaction rollback and catalog preservation: PASS", flush=True)
