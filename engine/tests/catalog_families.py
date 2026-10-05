"""Family-specific synthetic catalog shared with the deterministic v2 seed."""

import json
from decimal import Decimal
from typing import Any

from backend.catalogs.demo_fixture import manifest
from dekopen_engine import BayOpeningType, NodeType, ParametricNode, SystemParams, calculate_geometry


def family_params(code: str) -> SystemParams:
    record = next(record for record in manifest() if record["code"] == code)
    return SystemParams.model_validate_json(json.dumps(record["params"]))


def family_cases() -> dict[str, dict[str, Any]]:
    cases = {}
    for code in ("DEMO_60", "DEMO_70", "DEMO_CORREDERA_60"):
        params = family_params(code)
        sliding = params.sliding is not None
        for finish in ("WHITE", "FOILED"):
            node = ParametricNode(id="bay", type=NodeType.BAY, width_mm=Decimal("1800"),
                height_mm=Decimal("1400"), opening_type=BayOpeningType.SLIDING_2L if sliding else BayOpeningType.TURN_LEFT,
                glass_thickness_mm=Decimal("24"), glass_spec="4-16-4 Float Incoloro")
            if not sliding:
                node = ParametricNode(id="split", type=NodeType.SPLIT_V, width_mm=Decimal("1800"),
                    height_mm=Decimal("1400"), split_offset_mm=Decimal("900"),
                    mullion_profile_sku=f"{code}-POSTE-V",
                    children=[node.model_copy(update={"id": "fixed", "width_mm": None, "height_mm": None,
                                "opening_type": BayOpeningType.FIXED}),
                              node.model_copy(update={"id": "turn", "width_mm": None, "height_mm": None})])
            result = calculate_geometry(node, params, is_foiled=finish != "WHITE", finish=finish)
            cases[f"{code}-{finish}"] = result.model_dump(mode="json")
    return cases
