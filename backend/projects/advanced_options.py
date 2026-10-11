"""Public technical catalog projections. No price or private source files."""

from dekopen_engine.advanced_openings import ADVANCED_NAMES
from dekopen_engine.geometry import calculate_geometry
from dekopen_engine.models import OpeningMovement, OpeningUse, ParametricNode, SystemParams
import json


def advanced_availability(params: SystemParams) -> list[dict]:
    result = []
    for movement, use in [
        *(
            (motion, OpeningUse.WINDOW)
            for motion in ADVANCED_NAMES
            if motion is not OpeningMovement.FOLD
        ),
        (OpeningMovement.FOLD, OpeningUse.DOOR),
        (OpeningMovement.SLIDE, OpeningUse.DOOR),
    ]:
        caps = [
            cap
            for cap in params.opening_capabilities
            if cap.movement is movement and cap.use is use
        ]
        systems = [
            name
            for name, capabilities in params.compatible_opening_systems
            if any(
                cap.movement is movement and cap.use is use and cap.advanced_recipes
                for cap in capabilities
            )
        ]
        available = any(cap.advanced_recipes for cap in caps)
        result.append(
            {
                "movement": movement.value,
                "use": use.value,
                "label": "Puerta corredera"
                if movement is OpeningMovement.SLIDE
                else ADVANCED_NAMES[movement],
                "available": available,
                "reason": "Esquemas con fuente y herrajes declarados."
                if available
                else "Sin dato: esta serie no declara receta, perfiles y herrajes para esta apertura. Elige una serie compatible o declara su autoridad en Catálogo.",
                "compatible_systems": systems,
                "schemes": [recipe.scheme for cap in caps for recipe in cap.advanced_recipes],
            }
        )
    return result


def advanced_previews(params: SystemParams, glass_choices: list[dict]) -> list[dict]:
    glass = next((item for item in glass_choices if item["compatible"] and item["spec"]), None)
    result = []
    for cap in params.opening_capabilities:
        for recipe in cap.advanced_recipes:
            entry = {
                "recipe_code": recipe.code,
                "movement": cap.movement.value,
                "use": cap.use.value,
                "opening_leaves": [],
                "glass_sku": None,
                "reason": "",
            }
            if glass is None:
                entry["reason"] = (
                    "Sin dato: declara un vidrio compatible para calcular la vista previa."
                )
            else:
                node = ParametricNode.model_validate_json(
                    json.dumps(
                        {
                            "id": "preview",
                            "type": "BAY",
                            "width_mm": str(recipe.starter_width_mm),
                            "height_mm": str(recipe.starter_height_mm),
                            "opening": {
                                "movement": cap.movement.value,
                                "direction": cap.direction.value,
                                "leaf_role": "SINGLE",
                                "fixed_in_sash": False,
                                "hinge_side": "NONE",
                            },
                            "opening_use": cap.use.value,
                            "opening_recipe_code": recipe.code,
                            "glass_spec": glass["spec"],
                            "glass_thickness_mm": glass["total_thickness_mm"],
                            "glass_article_sku": glass["sku"],
                            "glass_product": glass["product"],
                        }
                    )
                )
                try:
                    calculated = calculate_geometry(node, params, finish=params.finishes[0])
                    entry["opening_leaves"] = [
                        leaf.model_dump(mode="json") for leaf in calculated.opening_leaves
                    ]
                    entry["glass_sku"] = glass["sku"]
                except (ValueError, NotImplementedError) as error:
                    entry["reason"] = str(error)
            result.append(entry)
    return result
