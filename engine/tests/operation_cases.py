"""Exact editing plans whose manufacturing geometry is frozen by goldgen."""

from copy import deepcopy
from decimal import Decimal
import json
from typing import Any

from dekopen_engine.design_operations import apply_operations
from dekopen_engine.commercial import indicative_line_net
from dekopen_engine.geometry import compute_geometry
from dekopen_engine.models import ParametricNode
from dekopen_engine.product import ProductModel, evaluate_product
from engine.tests.catalog import demo_60_params


def operation_cases() -> dict[str, Any]:
    params = demo_60_params()
    before: dict[str, Any] = {"version": "product-v2", "assembly": {"modules": [{"id": "m1", "width_mm": "1500.00", "height_mm": "1200.00",
        "tree": {"id": "b1", "type": "BAY", "opening_type": "FIXED", "glass_thickness_mm": "4.00", "glass_spec": "4"}}], "couplings": []}}
    plans: dict[str, list[dict[str, Any]]] = {
        "TRANSOM_FROM_TOP": [{"op": "split_bay", "bay": "b1", "axis": "H", "from": "START", "offset_mm": "400"}],
        "THREE_BAYS": [{"op": "equalize_bays", "module": "m1", "axis": "V", "count": 3},
                       {"op": "set_opening", "module": "m1", "bay": "b1", "opening": "TURN_LEFT"},
                       {"op": "set_opening", "module": "m1", "bay": "b3", "opening": "TURN_RIGHT"}],
        "RESIZE_EXACT": [{"op": "resize", "module": "m1", "delta_width_mm": "200"}],
        "FLOOR_HANDLE": [{"op": "set_module_width", "module": "m1", "width_mm": "1000"},
                         {"op": "set_opening", "module": "m1", "opening": "TURN_LEFT"},
                         {"op": "set_handle_height", "bay": "b1", "height_mm": "1050", "reference": "FLOOR", "sill_height_mm": "500"}],
    }
    result = {}
    for name, ops in plans.items():
        output = apply_operations(before, ops, params=params, catalog={}, finish="WHITE")
        module = output["product"]["assembly"]["modules"][0]
        root = deepcopy(module["tree"])
        root.update(width_mm=module["width_mm"], height_mm=module["height_mm"])
        calculation = compute_geometry(ParametricNode.model_validate_json(json.dumps(root)), params, finish="WHITE")
        assert calculation.manufacturing_trace is not None
        assert calculation.result is not None
        result[name] = {"before": before, "ops": ops, "after": output["product"],
                        "trace": calculation.manufacturing_trace.model_dump(mode="json"),
                        "glass": [glass.model_dump(mode="json") for glass in calculation.result.glasses]}
    outline = deepcopy(before)
    outline["assembly"]["modules"][0].update(width_mm="1200.00", contour={
        "vertices": [{"x_mm": "0", "y_mm": "0"}, {"x_mm": "1200", "y_mm": "900"},
                     {"x_mm": "0", "y_mm": "1200"}], "bulges": ["100", None, None]})
    contour_ops = [{"op": "set_module_width", "module": "m1", "width_mm": "2400"}]
    after = apply_operations(outline, contour_ops, params=params, catalog={}, finish="WHITE")["product"]
    evaluation = evaluate_product(ProductModel.model_validate_json(json.dumps(after)), params, finish="WHITE")
    result["DIAGONAL_CONTOUR_RESIZE"] = {"before": outline, "ops": contour_ops, "after": after,
                                        "evaluation": evaluation.model_dump(mode="json")}
    result["INDICATIVE_QUANTITY_NET"] = {"USD": str(indicative_line_net(Decimal("9007199254740992.02"), 3, "USD")),
        "CLP": str(indicative_line_net(Decimal("123.50"), 3, "CLP")),
        "ABSENT": str(indicative_line_net(Decimal("0"), 0, "CLP"))}
    for label, recipe in {"MONOLITHIC": "6 Float Incoloro", "DVH": "4-16-4", "LAMINATED_UNKNOWN_PVB": "4+4"}.items():
        output = apply_operations(before, [{"op": "set_glass", "module": "m1", "sku": "NEW"}],
            params=params, finish="WHITE", catalog={"glass_skus": {"NEW"}, "glass_specs": {"NEW": recipe}})
        result[f"LEGACY_GLASS_{label}"] = {"before": before, "recipe": recipe, "after": output["product"]}
    from engine.tests.opening_cases import opening_params, typologies
    from engine.tests.hardware_cases import hardware_case_inputs
    french_code, french = typologies()["FRENCH-LEFT"]
    sliding = hardware_case_inputs()[2]
    for label, source, authority in [("FRENCH_COMMON_HANDLE", french, opening_params(french_code)),
                                      ("SLIDING_COMMON_HANDLE", sliding[2], sliding[1])]:
        initial = {"version": "product-v2", "assembly": {"couplings": [], "modules": [{
            "id": "m1", "width_mm": str(source.width_mm), "height_mm": str(source.height_mm),
            "tree": source.model_dump(mode="json")} ]}}
        changed = apply_operations(initial, [{"op": "set_handle_height", "module": "m1", "bay": source.id,
            "height_mm": "600", "reference": "LEAF_BOTTOM", "all_handles": True}],
            params=authority, finish="WHITE", catalog={})["product"]
        module = changed["assembly"]["modules"][0]
        calculation = compute_geometry(ParametricNode.model_validate_json(json.dumps({**module["tree"],
            "width_mm": module["width_mm"], "height_mm": module["height_mm"]})), authority, finish="WHITE")
        assert calculation.manufacturing_trace is not None
        assert calculation.result is not None
        result[label] = {"before": initial, "after": changed, "trace": calculation.manufacturing_trace.model_dump(mode="json"),
                         "hardware": [item.model_dump(mode="json") for item in calculation.result.hardware_items]}
    return result
