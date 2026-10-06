"""Exact, reviewable color rules; synthetic examples never certify a supplier."""

from decimal import Decimal
import json
from typing import Any

from backend.catalogs.demo_finishes import finish_manifest
from dekopen_engine.geometry import calculate_geometry
from dekopen_engine.finishes import finish_surcharge
from dekopen_engine.models import ParametricNode, SystemParams


def finish_context(code: str = "DEMO_60") -> tuple[SystemParams, ParametricNode]:
    record = next(row for row in finish_manifest() if row["code"] == code)
    params = SystemParams.model_validate_json(json.dumps(record["params"]))
    node = ParametricNode.model_validate_json(json.dumps({"id": "vano", "type": "BAY",
        "width_mm": "900", "height_mm": "850", "opening_type": "FIXED",
        "glass_thickness_mm": "24", "glass_spec": "4-16-4", "glass_article_sku": code+"-GLASS"}))
    return params, node


def finish_cases() -> dict[str, Any]:
    cases = {}
    for label, code, finish in (("pvc-blanco", "DEMO_60", "WHITE"),
        ("pvc-nogal-exterior", "DEMO_60", "WHITE_WALNUT"),
        ("pvc-antracita-interior", "DEMO_60", "ANTHRACITE_WHITE"),
        ("pvc-coextruido", "DEMO_60", "COEX_GREY"),
        ("aluminio-ral", "DEMO_ALU_PRACTICABLE", "WHITE_RAL7016"),
        ("aluminio-anodizado", "DEMO_ALU_PRACTICABLE", "ANODIZED_SILVER"),
        ("aluminio-madera", "DEMO_ALU_PRACTICABLE", "WOOD_WALNUT")):
        params, node = finish_context(code)
        result = calculate_geometry(node, params, finish=finish)
        cases[label] = {"bom": result.model_dump(mode="json"),
            "profile_cost": "100000", "surcharge": str(finish_surcharge(result, Decimal(100000), "CLP"))}
    return cases
