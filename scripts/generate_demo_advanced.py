"""Generate additive D08 contracts, v8 catalogs and documentary seed only."""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "engine/src"), str(ROOT / "backend")]
from dekopen_engine.models import AdvancedOpeningRecipe  # noqa: E402
from backend.catalogs.demo_advanced import advanced_manifest  # noqa: E402
from scripts.generate_demo_extras import extra_sql, extra_seed_sql  # noqa: E402

MARKER = "-- D08 generated documentary seed; see scripts/generate_demo_advanced.py."


def schema_sql() -> str:
    source = (ROOT / "supabase/migrations/20261231000000_opening_capabilities.sql").read_text(
        encoding="utf-8"
    )
    guard = source.split("CREATE FUNCTION private.guard_opening_authorities()", 1)[1].split(
        "REVOKE ALL ON FUNCTION private.guard_opening_authorities()", 1
    )[0]
    guard = "CREATE OR REPLACE FUNCTION private.guard_opening_authorities()" + guard
    guard = guard.replace("signature TEXT;", "signature TEXT; advanced BOOLEAN; recipe JSONB;")
    guard = guard.replace("'handle_rule','source']", "'handle_rule','source','advanced_recipes']")
    guard = guard.replace(
        "('FIXED','TURN','TILT','TILT_TURN','TOP_HUNG','SLIDE')",
        "('FIXED','TURN','TILT','TILT_TURN','TOP_HUNG','SLIDE','LIFT_SLIDE','PARALLEL_SLIDE','FOLD','PIVOT_V','PIVOT_H','VERTICAL_SLIDE')",
    )
    old_family = """OR (cap->>'movement'='SLIDE' AND NEW.system_family<>'SLIDING')
            OR (cap->>'movement' NOT IN ('FIXED','SLIDE') AND NEW.system_family NOT IN ('CASEMENT','DOOR'))
            OR (cap->>'use'='DOOR' AND cap->>'movement' NOT IN ('FIXED','TURN'))"""
    new_family = """OR (cap->>'movement'='SLIDE' AND NEW.system_family NOT IN ('SLIDING','DOOR'))
            OR (cap->>'movement'='LIFT_SLIDE' AND NEW.system_family<>'LIFT_SLIDE')
            OR (cap->>'movement'='VERTICAL_SLIDE' AND NEW.system_family<>'SLIDING')
            OR (cap->>'movement'='FOLD' AND NEW.system_family<>'DOOR')
            OR (cap->>'movement' IN ('PARALLEL_SLIDE','PIVOT_V','PIVOT_H') AND NEW.system_family<>'CASEMENT')
            OR (cap->>'movement' IN ('TURN','TILT','TILT_TURN','TOP_HUNG') AND NEW.system_family NOT IN ('CASEMENT','DOOR'))
            OR (cap->>'use'='DOOR' AND cap->>'movement' NOT IN ('FIXED','TURN','SLIDE','FOLD'))"""
    assert old_family in guard
    guard = guard.replace(old_family, new_family)
    guard = guard.replace(
        "cap->>'movement' IN ('FIXED','SLIDE')",
        "cap->>'movement' IN ('FIXED','SLIDE','LIFT_SLIDE','PARALLEL_SLIDE','FOLD','PIVOT_V','PIVOT_H','VERTICAL_SLIDE')",
    )
    needle = """        IF NEW.system_family IS NULL"""
    addition = """        advanced := cap->>'movement' IN ('LIFT_SLIDE','PARALLEL_SLIDE','FOLD','PIVOT_V','PIVOT_H','VERTICAL_SLIDE')
            OR (cap->>'movement'='SLIDE' AND cap->>'use'='DOOR');
        IF (advanced AND (cap->>'leaf_role'<>'SINGLE' OR cap->>'fixed_in_sash'='true' OR cap->'hinge_sides'<>'["NONE"]'::JSONB
                OR jsonb_typeof(cap->'advanced_recipes') IS DISTINCT FROM 'array' OR jsonb_array_length(cap->'advanced_recipes')=0
                OR nullif(cap->'handle_rule','null') IS NULL))
            OR (NOT advanced AND coalesce(cap->'advanced_recipes','[]'::JSONB)<>'[]'::JSONB) THEN
            RAISE EXCEPTION 'opening_capability_invalid' USING ERRCODE='23514';
        END IF;
        IF advanced THEN
            IF (SELECT count(DISTINCT value->>'code') FROM jsonb_array_elements(cap->'advanced_recipes'))<>jsonb_array_length(cap->'advanced_recipes') THEN
                RAISE EXCEPTION 'advanced_opening_recipe_ambiguous' USING ERRCODE='23514';
            END IF;
            FOR recipe IN SELECT value FROM jsonb_array_elements(cap->'advanced_recipes') LOOP
                IF NOT private.advanced_recipe_valid(recipe,cap) THEN
                    RAISE EXCEPTION 'advanced_opening_recipe_invalid' USING ERRCODE='23514';
                END IF;
            END LOOP;
        END IF;
"""
    guard = guard.replace(needle, addition + needle, 1)
    latest = (ROOT / "supabase/migrations/20270103000200_accessory_cost_visibility.sql").read_text(
        encoding="utf-8"
    )
    binding = latest.split(
        "CREATE OR REPLACE FUNCTION private.check_opening_catalog_bindings()", 1
    )[1].split("COMMIT;", 1)[0]
    binding = "CREATE OR REPLACE FUNCTION private.check_opening_catalog_bindings()" + binding
    binding = binding.replace(
        "expected_type TEXT;", "expected_type TEXT; recipe JSONB; profile_role TEXT;"
    )
    binding = binding.replace(
        "WHEN cap->>'use'='DOOR' THEN 'DOOR'",
        "WHEN cap->>'use'='DOOR' AND cap->>'movement'='TURN' THEN 'DOOR'",
    )
    needle = """        IF cap->>'leaf_role' IN ('ACTIVE','PASSIVE')"""
    addition = """        FOR recipe IN SELECT value FROM jsonb_array_elements(coalesce(cap->'advanced_recipes','[]'::JSONB)) LOOP
            FOR kit_sku IN SELECT jsonb_array_elements_text(recipe->'hardware_kit_skus')
                UNION SELECT jsonb_array_elements_text(recipe->'pass_through_hardware_kit_skus') LOOP
                IF NOT EXISTS(SELECT 1 FROM public.hardware_kits k WHERE k.system_id=target
                    AND k.org_id IS NOT DISTINCT FROM system_row.org_id AND k.sku=kit_sku AND k.is_active
                    AND k.opening_type=expected_type AND k.class_authority IS NOT NULL
                    AND (cap->>'movement' NOT IN ('LIFT_SLIDE','PARALLEL_SLIDE','FOLD','SLIDE')
                        OR k.carriages_qty>0 AND k.carriage_capacity_kg>0
                           AND k.max_leaf_weight_kg<=k.carriages_qty*k.carriage_capacity_kg)
                    AND (cap->>'movement'<>'PARALLEL_SLIDE' OR k.stay_arms_qty>0)) THEN
                    RAISE EXCEPTION 'advanced_opening_kit_authority_required' USING ERRCODE='23514';
                END IF;
            END LOOP;
            FOR profile_role IN SELECT value FROM unnest(ARRAY[recipe->>'leaf_profile_role',recipe->>'rail_profile_role',
                CASE WHEN recipe->>'threshold_height_mm' IS NOT NULL THEN 'THRESHOLD' END,
                CASE WHEN recipe->>'interlock_required'='true' THEN 'INTERLOCK' END]) value WHERE value IS NOT NULL LOOP
                IF NOT EXISTS(SELECT 1 FROM public.profile_articles a WHERE a.system_id=target
                    AND a.org_id IS NOT DISTINCT FROM system_row.org_id AND a.role::TEXT=profile_role) THEN
                    RAISE EXCEPTION 'advanced_opening_profile_required' USING ERRCODE='23514';
                END IF;
            END LOOP;
        END LOOP;
"""
    binding = binding.replace(needle, addition + needle, 1)
    schema = json.dumps(
        AdvancedOpeningRecipe.model_json_schema(mode="serialization"),
        sort_keys=True,
        ensure_ascii=False,
    ).replace("'", "''")
    validator = (
        (ROOT / "scripts/advanced_opening_schema.sql")
        .read_text(encoding="utf-8")
        .replace("__RECIPE_SCHEMA__", schema)
    )
    return (
        "-- Generated additive D08 contract; historical rows and snapshots are untouched.\nBEGIN;\n"
        "ALTER TABLE public.hardware_kits DROP CONSTRAINT chk_kits_opening_type;\n"
        "ALTER TABLE public.hardware_kits ADD CONSTRAINT chk_kits_opening_type CHECK(opening_type IN "
        "('AWNING','DOOR','SLIDING','TILT','TILT_TURN','TURN','LIFT_SLIDE','PARALLEL_SLIDE','FOLD','PIVOT_V','PIVOT_H','VERTICAL_SLIDE'));\n"
        + validator
        + "\n"
        + guard
        + "\n"
        + binding
        + "\nCOMMIT;\n"
    )


def catalog_sql() -> str:
    catalog = extra_sql(advanced_manifest(), version=8)
    # A populated upgrade does not replay seed.sql. New catalog identities
    # must receive their own documentary policies in the same transaction.
    assert catalog.endswith("COMMIT;\n")
    return catalog.removesuffix("COMMIT;\n") + seed_sql() + "\nCOMMIT;\n"


def seed_sql() -> str:
    codes = ",".join("'" + record["code"] + "'" for record in advanced_manifest())
    # Separate v8 identities. Keep the historical eligibility list unchanged.
    text = (
        extra_seed_sql()
        .replace("-- D06 generated documentary seed; see scripts/generate_demo_extras.py.", MARKER)
        .replace("d06_seed", "d08_seed")
        .replace("catalog/v6/", "catalog/v8/")
        .replace("s.version=6", "s.version=8")
        .replace("_DEMO_V6", "_DEMO_V8")
    )
    import re

    text = re.sub(r"s\.code IN \([^\n]+\)", "s.code IN (" + codes + ")", text)
    # Synthetic threshold frames declare a square bottom joint and a mitred
    # upper joint. These are explicit v8 fixture policies, never backfilled
    # from a saved product or inferred for a manufacturer's real catalog.
    rules = [
        {
            "role": "FRAME",
            "profile_angle_left": left,
            "profile_angle_right": right,
            "reinforcement_angle_left": 90,
            "reinforcement_angle_right": 90,
            "length_authority": "EXISTING_ENGINE",
            "compatible_with_existing_length": True,
        }
        for left, right in ((45, 90), (90, 45))
    ]
    literal = json.dumps(rules, ensure_ascii=False).replace("'", "''")
    return (
        text
        + "\nINSERT INTO public.reinforcement_cut_policies(id,system_id,org_id,version,authority) "
        "SELECT uuid_generate_v5('6ba7b811-9dad-11d1-80b4-00c04fd430c8','https://dekopen.local/catalog/v8/'||s.code||'/threshold-reinforcement'),"
        "p.system_id,p.org_id,9,jsonb_set(p.authority,'{rules}',"
        "p.authority->'rules'||(SELECT coalesce(jsonb_agg(r),'[]'::JSONB) "
        f"FROM jsonb_array_elements('{literal}'::JSONB) r WHERE NOT EXISTS ("
        "SELECT 1 FROM jsonb_array_elements(p.authority->'rules') existing "
        "WHERE existing->>'role'=r->>'role' "
        "AND (existing->>'profile_angle_left')::NUMERIC=(r->>'profile_angle_left')::NUMERIC "
        "AND (existing->>'profile_angle_right')::NUMERIC=(r->>'profile_angle_right')::NUMERIC)))"
        "||jsonb_build_object('policy_id',s.code||'_REFUERZO_UMBRAL_DEMO_V8','version',9) "
        "FROM public.reinforcement_cut_policies p JOIN public.profile_systems s ON s.id=p.system_id "
        "WHERE s.version=8 AND p.version=8 AND s.code IN ('DEMO_HST','DEMO_PLEGABLE','DEMO_PUERTA_CORREDERA') "
        "ON CONFLICT DO NOTHING;\n"
    )


if __name__ == "__main__":
    (ROOT / "supabase/migrations/20270126000000_advanced_opening_authority.sql").write_text(
        schema_sql(), encoding="utf-8", newline="\n"
    )
    (ROOT / "supabase/migrations/20270126000100_demo_advanced_catalog.sql").write_text(
        catalog_sql(), encoding="utf-8", newline="\n"
    )
    seed = ROOT / "supabase/seed.sql"
    prior = seed.read_text(encoding="utf-8").split(MARKER, 1)[0].rstrip()
    temporary = seed.with_suffix(".sql.tmp")
    temporary.write_text(prior + "\n\n" + seed_sql(), encoding="utf-8", newline="\n")
    temporary.replace(seed)
    print("D08 additive schema, seven v8 DEMO families and documentary seed generated.")
