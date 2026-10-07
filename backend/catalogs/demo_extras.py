"""Synthetic v6 accessories. Declared prices are DEMO, never certification."""

from copy import deepcopy
from decimal import Decimal
import json
from typing import Any

from backend.catalogs.demo_finishes import finish_manifest
from dekopen_engine.extra_models import ExtraAuthority

SOURCE = "Accesorios sintéticos DEKOPEN v6; semilla 20270103; sin certificación"


def extra_manifest() -> list[dict[str, Any]]:
    records = deepcopy(finish_manifest())
    for record in records:
        params, code = record["params"], record["code"]
        record["name"] = record["name"].replace("acabados v5", "extras v6")
        record["version"] = 6
        definitions = []
        for name, role, basis, face, rate in (("Vierteaguas", "SILL", "SILL", "30.00", "5000"),
                ("Ensanche", "FRAME_EXTENSION", "SIDES", "30.00", "4000"),
                ("Tapajuntas", "COVER_TRIM", "SIDES", "25.00", "3500")):
            sku = code+"-EXTRA-"+role
            article = {"sku": sku, "name": name+" · DEMO", "role": role, "material": params["material"],
                "face_width_mm": face, "commercial_length_mm": "6000.00", "welding_loss_mm": "0.00",
                "reinforcement_gap_mm": None, "weight_kg_m": "0.5000", "steel_weight_kg_m": None,
                "reinforcement_sku": None, "reinforcement_rule": None,
                "cut_rule": {"angle_degrees": 90, "welding_loss_per_end_mm": "0.00", "joint_deduction_per_end_mm": "0.00",
                    "meeting_deduction_mm": "0.00", "cut_step_mm": "0.01", "rounding": "UP", "source": SOURCE}}
            record["articles"].append(article)
            params["effective_profile_articles"][role] = {key:value for key,value in article.items() if key != "name"}
            record["prices"].append({"sku": "COMPRA-"+sku, "unit": "BAR", "unit_cost": str(Decimal(rate)*6)})
            for combo in params["finish_authority"]["combinations"]:
                commercial = "COMPRA-V6-"+sku+"-"+combo["code"]
                record["finish_bindings"].append({"sku": sku, "finish": combo["code"], "commercial_sku": commercial})
                params["finish_profile_skus"][combo["code"]][sku] = commercial
                record["prices"].append({"sku": commercial, "unit": "BAR", "unit_cost": str(Decimal(rate)*6)})
            definitions.append({"code": role, "name": name, "scope": "POSITION", "kind": "PROFILE", "basis": basis,
                "unit": "M", "currency": "CLP", "cost_rate": rate, "selling_rate": str(Decimal(rate)*Decimal("1.50")),
                "source": SOURCE, "synthetic": True, "profile_role": role,
                "default_sides": ["LEFT", "RIGHT"] if role == "FRAME_EXTENSION" else ["TOP", "RIGHT", "BOTTOM", "LEFT"] if basis == "SIDES" else [],
                "default_overhang_mm": "30.00" if basis == "SILL" else "0.00",
                "suggestion": "WINDOW" if role == "SILL" else "OPENING_GAP" if role == "FRAME_EXTENSION" else "NONE"})
        for suffix, name, movements, rate, handle in (
                ("SCREEN_FIXED", "Mosquitero fijo a medida", [], "22000", False),
                ("SCREEN_ROLL", "Mosquitero enrollable a medida", ["TURN", "TILT_TURN", "TOP_HUNG"], "42000", False),
                ("SCREEN_SLIDE", "Mosquitero corredera a medida", ["SLIDE", "LIFT_SLIDE"], "36000", False),
                ("SPECIAL_HANDLE", "Manilla especial", ["TURN", "TILT_TURN", "TOP_HUNG", "SLIDE"], "12000", True),
                ("LIMITER", "Limitador de apertura", ["TURN", "TILT_TURN", "TOP_HUNG"], "6500", False),
                ("VENT", "Aireador", [], "18000", False)):
            definitions.append({"code": suffix, "name": name, "scope": "POSITION", "kind": "SCREEN" if suffix.startswith("SCREEN") else "FITTING",
                "basis": "WINDOW" if suffix == "SCREEN_FIXED" else "LEAF" if movements else "WINDOW", "unit": "EA",
                "sku": code+"-EXTRA-"+suffix, "currency": "CLP", "cost_rate": rate,
                "selling_rate": str(Decimal(rate)*Decimal("1.50")), "source": SOURCE, "synthetic": True,
                "allowed_movements": movements, "replaces_handle": handle,
                "suggestion": "MOVING_LEAF" if suffix == "SCREEN_ROLL" else "NONE"})
        authority = ExtraAuthority.model_validate_json(json.dumps({"schema_version":1, "definitions":definitions,"source":SOURCE}))
        params["extra_authority"] = authority.model_dump(mode="json")
    return records
