"""Independent v8 advanced-opening cases; all fixtures are explicitly DEMO."""

import json
from typing import Any

from backend.catalogs.demo_advanced import advanced_manifest
from dekopen_engine.models import ParametricNode, SystemParams
from dekopen_engine.geometry import calculate_geometry
from dekopen_engine.snapshot import result_payload


def advanced_params(code: str) -> SystemParams:
    record = next(record for record in advanced_manifest() if record["code"] == code)
    return SystemParams.model_validate_json(json.dumps(record["params"]))


def advanced_node(code: str, recipe_code: str) -> ParametricNode:
    record = next(record for record in advanced_manifest() if record["code"] == code)
    cap = next(
        cap for cap in record["params"]["opening_capabilities"] if cap.get("advanced_recipes")
    )
    recipe = next(recipe for recipe in cap["advanced_recipes"] if recipe["code"] == recipe_code)
    return ParametricNode.model_validate_json(
        json.dumps(
            {
                "id": "bay",
                "type": "BAY",
                "width_mm": recipe["starter_width_mm"],
                "height_mm": recipe["starter_height_mm"],
                "opening": {
                    "movement": cap["movement"],
                    "hinge_side": "NONE",
                    "direction": cap["direction"],
                    "leaf_role": "SINGLE",
                    "fixed_in_sash": False,
                },
                "opening_use": cap["use"],
                "opening_recipe_code": recipe_code,
                "glass_thickness_mm": "24",
                "glass_spec": record["glasses"][0]["glass_spec"],
                "glass_article_sku": record["glasses"][0]["sku"],
            }
        )
    )


def advanced_typologies() -> list[tuple[str, str]]:
    return [
        (record["code"], recipe["code"])
        for record in advanced_manifest()
        for cap in record["params"]["opening_capabilities"]
        for recipe in cap.get("advanced_recipes", [])
    ]


def advanced_cases() -> dict[str, Any]:
    return {
        code + "/" + recipe: result_payload(
            calculate_geometry(advanced_node(code, recipe), advanced_params(code), finish="WHITE")
        )
        for code, recipe in advanced_typologies()
    }
