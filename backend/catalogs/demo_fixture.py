"""Explicit synthetic authorities. Seeded integer draws never certify a supplier."""

from decimal import Decimal
from random import Random
from typing import Any

SEED = 20261005
SOURCE = f"Catálogo sintético DEKOPEN v2; semilla {SEED}; sin certificación"
SERIES = (
    ("DEMO_60", "PVC practicable 60 mm", "CASEMENT", "PVC", "60.00"),
    ("DEMO_70", "PVC practicable 70 mm", "CASEMENT", "PVC", "70.00"),
    ("DEMO_CORREDERA_60", "PVC corredera 60 mm", "SLIDING", "PVC", "60.00"),
    ("DEMO_ALU_CORREDERA", "Aluminio corredera 60 mm", "SLIDING", "ALUMINIUM", "60.00"),
    ("DEMO_ALU_PRACTICABLE", "Aluminio practicable 65 mm", "CASEMENT", "ALUMINIUM", "65.00"),
)
CASEMENT_OPENINGS = ("FIXED", "TURN_LEFT", "TURN_RIGHT", "TILT_TURN_LEFT", "TILT_TURN_RIGHT", "AWNING")
SLIDING_OPENINGS = ("FIXED", "SLIDING", "SLIDING_2L", "SLIDING_3L", "SLIDING_4L")


def manifest() -> list[dict[str, Any]]:
    rng = Random(SEED)
    result = []
    for code, name, family, material, depth in SERIES:
        is_sliding = family == "SLIDING"
        prefix = code + "-"
        profile_defs = [
            ("MARCO", "FRAME", depth),
            ("HOJA-CORREDERA" if is_sliding else "HOJA",
             "SLIDING_SASH" if is_sliding else "SASH", "70.00" if is_sliding else "75.00"),
            ("POSTE-V", "MULLION_V", "80.00"), ("POSTE-H", "MULLION_H", "80.00"),
            ("JQ-24", "GLAZING_BEAD", "24.00"), ("JQ-14", "GLAZING_BEAD", "14.00"),
            ("JQ-10", "GLAZING_BEAD", "10.00"),
        ]
        if is_sliding:
            profile_defs += [("ENCUENTRO", "INTERLOCK", "20.00"), ("RIEL", "RAIL", "10.00")]
        articles = []
        prices = []
        for sku, role, face in profile_defs:
            welded = material == "PVC" and role in ("FRAME", "SASH")
            steel = material == "PVC" and role not in ("GLAZING_BEAD", "RAIL")
            angle = 45 if role in ("FRAME", "SASH") else 90
            weight = f"{Decimal(rng.randrange(7000, 17001)) / Decimal('10000'):.4f}"
            article: dict[str, Any] = {
                "sku": prefix + sku, "name": name + " · " + sku,
                "role": role, "material": material, "face_width_mm": face,
                "commercial_length_mm": "6000.00", "welding_loss_mm": "6.00" if welded else "0.00",
                "reinforcement_gap_mm": "15.00" if steel else None,
                "weight_kg_m": weight, "steel_weight_kg_m": "1.7000" if steel else None,
                "reinforcement_sku": prefix + "ACERO-" + sku if steel else None,
                "cut_rule": {
                    "angle_degrees": angle, "welding_loss_per_end_mm": "3.00" if welded else "0.00",
                    "joint_deduction_per_end_mm": "2.00" if material == "ALUMINIUM" and angle == 45 else "0.00",
                    "meeting_deduction_mm": "0.00", "cut_step_mm": "0.01", "rounding": "UP", "source": SOURCE,
                },
                "reinforcement_rule": None,
            }
            if steel:
                article["reinforcement_rule"] = {
                    "reinforcement_sku": article["reinforcement_sku"], "reinforcement_type": "Acero galvanizado DEMO",
                    "minimum_length_mm": "1000.00", "required_finishes": ["FOILED", "DARK"],
                    "required_non_white": True, "cut_deduction_mm": "30.00" if welded else "10.00",
                    "screws_per_m": "4.0000", "screw_sku": prefix + "TORNILLO-REF",
                    "screw_weight_kg": "0.003000", "source": SOURCE,
                }
                prices.append({"sku": article["reinforcement_sku"], "unit": "BAR", "unit_cost": str(rng.randrange(9000, 20001))})
            articles.append(article)
            prices.append({"sku": article["sku"], "unit": "BAR", "unit_cost": str(rng.randrange(12000, 40001))})
        if material == "PVC":
            prices.append({"sku": prefix + "TORNILLO-REF", "unit": "EA", "unit_cost": str(rng.randrange(40, 91))})
        openings = SLIDING_OPENINGS if is_sliding else CASEMENT_OPENINGS
        limits = [{
            "opening_type": opening, "min_leaf_width_mm": "200.00", "max_leaf_width_mm": "4500.00" if opening == "FIXED" else "1600.00",
            "min_leaf_height_mm": "200.00", "max_leaf_height_mm": "3000.00" if opening == "FIXED" else "2500.00",
            "max_leaf_weight_kg": None if opening == "FIXED" else "45.0000" if opening == "AWNING" else "150.0000",
            "min_aspect_ratio": "0.2000", "max_aspect_ratio": "6.0000", "source": SOURCE,
        } for opening in openings]
        kits = []
        for opening in (["SLIDING"] if is_sliding else ["TURN", "TILT_TURN", "AWNING"]):
            sku = prefix + "KIT-" + opening
            kits.append({
                "sku": sku, "name": f"Kit {name} · " + {"TURN": "practicable", "TILT_TURN": "oscilobatiente", "SLIDING": "corredera", "AWNING": "proyectante"}[opening], "opening_type": opening,
                "min_leaf_width_mm": "200.00", "max_leaf_width_mm": "1600.00",
                "min_leaf_height_mm": "200.00", "max_leaf_height_mm": "2500.00",
                "max_leaf_weight_kg": "45.00" if opening == "AWNING" else "150.00",
                "weight_kg": "2.5000", "rail_type": "dual", "carriages_qty": 2 if is_sliding else 0,
                "stay_arms_qty": 2 if opening == "AWNING" else 1,
                "contents": [{"sku": prefix + "MANILLA", "name": "Manilla DEMO", "qty": "1", "unit": "EA", "category": "HANDLE"},
                    {"sku": prefix + ("CARRO" if is_sliding else "BISAGRA"), "name": "Carro DEMO" if is_sliding else "Bisagra DEMO",
                     "qty": "2", "unit": "EA", "category": "ROLLER" if is_sliding else "HINGE"}],
            })
            prices.append({"sku": sku, "unit": "KIT", "unit_cost": str(rng.randrange(18000, 60001))})
        by_sku = {article["sku"]: article for article in articles}
        glazing = {}
        for thickness in ("4.00", "5.00", "6.00", "24.00"):
            bead = prefix + ("JQ-10" if thickness == "24.00" else "JQ-24" if thickness == "4.00" else "JQ-14")
            glazing[thickness] = {"glass_thickness_mm": thickness,
                "bead_article": {key: value for key, value in by_sku[bead].items() if key != "name"},
                "bead_width_mm": by_sku[bead]["face_width_mm"], "gasket_interior_mm": "3.00", "gasket_exterior_mm": "3.00", "cut_add_mm": "9.00"}
        glasses = [{"sku": prefix + "VIDRIO-4-16-4", "glass_spec": "4-16-4 Float Incoloro"},
                   {"sku": prefix + "VIDRIO-4", "glass_spec": "4 Float Incoloro"}]
        for glass in glasses:
            prices.append({"sku": glass["sku"], "unit": "M2", "unit_cost": str(rng.randrange(18000, 45001))})
        params = {
            "system_code": code, "system_family": family, "depth_mm": depth, "material": material,
            "sash_overlap_mm": "8.00", "glass_clearance_white_mm": "3.00", "glass_clearance_foil_mm": "5.00",
            "rebate_depth_mm": "15.00", "end_milling_overlap_mm": "4.00", "corner_bracket_loss_mm": "2.00" if material == "ALUMINIUM" else "0.00",
            "hook_depth_mm": "0.00", "door_threshold_mm": "30.00", "door_bottom_clearance_mm": "20.00", "door_leaf_side_clearance_mm": "7.00",
            "finishes": ["WHITE", "FOILED"], "dimensional_limits": limits,
            "effective_profile_articles": {a["role"]: {key: value for key, value in a.items() if key != "name"} for a in articles if a["role"] != "GLAZING_BEAD"},
            "glazing_bead_rules": glazing, "available_hardware_kits": kits,
            "sliding": ({"pulley_height_mm": "12.00", "central_overlap_mm": "40.00", "lateral_clearance_mm": "0.00",
                "end_add_mm": "6.00", "glazing_deduction_width_mm": "20.00", "glazing_deduction_height_mm": "20.00",
                "rail_type": "dual", "rail_count": 2, "separate_rail": True, "interlock_required": True} if is_sliding else None),
        }
        result.append({"code": code, "name": name + " · DEMO", "is_demo": True, "version": 2,
                       "source": SOURCE, "seed": SEED, "params": params, "articles": articles,
                       "glasses": glasses, "prices": prices})
    return result
