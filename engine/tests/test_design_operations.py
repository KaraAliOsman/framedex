"""Editing outcomes, atomicity and exact derived effects from the shared registry."""
from copy import deepcopy
from decimal import Decimal

import pytest
from typing import Any
from dekopen_engine.models import SystemParams

from dekopen_engine.design_operations import OperationError, REGISTRY, apply_operations, fingerprint, validate_operation


@pytest.fixture
def product() -> dict[str, Any]:
    return {"version": "product-v2", "assembly": {"modules": [{"id": "m1", "width_mm": "1500.00", "height_mm": "1200.00",
        "tree": {"id": "left", "type": "BAY", "opening_type": "FIXED", "glass_thickness_mm": "4.00", "glass_spec": "4"}}], "couplings": []}}


def apply(product: dict[str, Any], ops: list[dict[str, Any]], params: SystemParams) -> dict[str, Any]:
    return apply_operations(product, ops, params=params, finish="WHITE",
        catalog={"glass_skus": {"FLOAT"}, "glass_specs": {"FLOAT": "4"}, "panel_skus": set(), "thicknesses": {Decimal("4")}})


@pytest.mark.parametrize("definition", REGISTRY, ids=lambda item: item["name"])
def test_all_examples_pass_their_own_strict_schema(definition: dict[str, Any]) -> None:
    for example in definition["examples"]:
        assert validate_operation(example) == example
        with pytest.raises(OperationError):
            validate_operation({**example, "provider_invented_field": "x"})


def test_compound_three_bays_preserves_one_frame_and_exact_global_axes(product: dict[str, Any], demo_60_params: SystemParams) -> None:
    result = apply(product, [{"op": "equalize_bays", "module": "m1", "axis": "V", "count": 3},
        {"op": "set_opening", "module": "m1", "bay": "b1", "opening": "TURN_LEFT"},
        {"op": "set_opening", "module": "m1", "bay": "b2", "opening": "FIXED"},
        {"op": "set_opening", "module": "m1", "bay": "b3", "opening": "TURN_RIGHT"}], demo_60_params)
    modules = result["product"]["assembly"]["modules"]
    assert len(modules) == 1
    tree = modules[0]["tree"]
    assert Decimal(tree["split_offset_mm"]) == Decimal("500")
    half = demo_60_params.effective_profile_articles[next(role for role in demo_60_params.effective_profile_articles if role.value == "MULLION_V")].face_width_mm / 2
    assert Decimal(tree["children"][1]["split_offset_mm"]) + Decimal("500") + half == Decimal("1000")
    assert [tree["children"][0]["opening_type"], *[n["opening_type"] for n in tree["children"][1]["children"]]] == ["TURN_LEFT", "FIXED", "TURN_RIGHT"]


def test_transom_from_top_and_center_split_have_exact_offsets(product: dict[str, Any], demo_60_params: SystemParams) -> None:
    top = apply(product, [{"op": "split_bay", "bay": "b1", "axis": "H", "from": "START", "offset_mm": "400"}], demo_60_params)
    assert top["product"]["assembly"]["modules"][0]["tree"]["split_offset_mm"] == "400.00"
    assert top["ops"][0]["base_sig"] == fingerprint(product)
    center = apply(product, [{"op": "split_bay", "bay": "b1", "axis": "V", "from": "CENTER"}], demo_60_params)
    assert center["product"]["assembly"]["modules"][0]["tree"]["split_offset_mm"] == "750.00"


def test_derived_resize_is_exact_and_input_remains_untouched(product: dict[str, Any], demo_60_params: SystemParams) -> None:
    before = deepcopy(product)
    result = apply(product, [{"op": "resize", "module": "m1", "delta_width_mm": "200"}], demo_60_params)
    assert result["product"]["assembly"]["modules"][0]["width_mm"] == "1700.00"
    assert product == before


def test_failed_second_operation_leaves_no_partial_mutation(product: dict[str, Any], demo_60_params: SystemParams) -> None:
    before = deepcopy(product)
    with pytest.raises(OperationError, match="marco"):
        apply(product, [{"op": "resize", "module": "m1", "delta_width_mm": "200"},
                        {"op": "set_module_width", "module": "m1", "width_mm": "0"}], demo_60_params)
    assert product == before


def test_floor_handle_requires_explicit_installation_height(product: dict[str, Any], demo_60_params: SystemParams) -> None:
    with pytest.raises(OperationError) as caught:
        apply(product, [{"op": "set_handle_height", "bay": "b1", "height_mm": "1050", "reference": "FLOOR"}], demo_60_params)
    assert caught.value.code == "installation_height_required"


def test_move_size_and_remove_have_exact_child_geometry(product: dict[str, Any], demo_60_params: SystemParams) -> None:
    from dekopen_engine.design_operations import _layout
    from dekopen_engine.models import ProfileRole
    split = apply(product, [{"op": "split_bay", "bay": "b1", "axis": "V", "from": "CENTER"}], demo_60_params)["product"]
    sized = apply(split, [{"op": "set_bay_size", "bay": "b1", "axis": "V", "size_mm": "600"}], demo_60_params)["product"]
    module = sized["assembly"]["modules"][0]
    assert _layout(module, demo_60_params, "WHITE")["left"][0] == Decimal("600")
    moved = apply(sized, [{"op": "move_divider", "divider": "d1", "offset_mm": "900", "from": "END"}], demo_60_params)["product"]
    assert moved["assembly"]["modules"][0]["tree"]["split_offset_mm"] == "600.00"
    removed = apply(moved, [{"op": "remove_divider", "divider": "d1"}], demo_60_params)["product"]
    assert removed["assembly"]["modules"][0]["tree"]["type"] == "BAY"
    assert removed["assembly"]["modules"][0]["width_mm"] == "1500.00"
    assert demo_60_params.effective_profile_articles[ProfileRole.FRAME].face_width_mm > 0


def test_handle_datum_is_resolved_from_real_leaf_geometry(product: dict[str, Any], demo_60_params: SystemParams) -> None:
    from engine.tests.operation_cases import operation_cases
    from dekopen_engine.geometry import compute_geometry
    from dekopen_engine.models import ParametricNode
    import json
    case = operation_cases()["FLOOR_HANDLE"]
    module = case["after"]["assembly"]["modules"][0]
    leaf = case["trace"]["leaves"][0]
    bottom = Decimal(module["height_mm"]) - Decimal(leaf["direct_rect"]["y_mm"]) - Decimal(leaf["direct_rect"]["height_mm"])
    assert Decimal(module["tree"]["handle_height_mm"]) + Decimal("500") + bottom == Decimal("1050")
    top = apply(case["after"], [{"op": "set_handle_height", "bay": "b1", "height_mm": "400", "reference": "LEAF_TOP"}], demo_60_params)["product"]
    node = {**top["assembly"]["modules"][0]["tree"], "width_mm": module["width_mm"], "height_mm": module["height_mm"]}
    calculation = compute_geometry(ParametricNode.model_validate_json(json.dumps(node)), demo_60_params, finish="WHITE")
    assert Decimal(node["handle_height_mm"]) + Decimal("400") == calculation.leaves[0].finished_height_mm


def test_sliding_tracks_and_flip_use_physical_opening_authority(product: dict[str, Any]) -> None:
    from engine.tests.opening_cases import opening_params
    from dekopen_engine.models import ParametricNode
    from dekopen_engine.openings import normalize_opening_tree
    import json
    params = opening_params("DEMO_CORREDERA_60")
    changed = apply(product, [{"op": "set_sliding_layout", "bay": "b1", "panels": "XX", "tracks": 2}], params)["product"]
    node = changed["assembly"]["modules"][0]["tree"]
    assert [panel["track"] for panel in node["sliding_layout"]["panels"]] == [0, 1]
    with pytest.raises(ValueError):
        apply(product, [{"op": "set_sliding_layout", "bay": "b1", "panels": "XX", "tracks": 2, "panel_tracks": [0, 0]}], params)
    params = opening_params("DEMO_60")
    physical = {"movement": "TILT_TURN", "hinge_side": "LEFT", "direction": "INWARD", "leaf_role": "SINGLE", "fixed_in_sash": False}
    changed = apply(product, [{"op": "set_opening", "module": "m1", "opening": physical}, {"op": "flip_handing", "bay": "b1"}], params)["product"]
    node = changed["assembly"]["modules"][0]["tree"]
    normalize_opening_tree(ParametricNode.model_validate_json(json.dumps(node)), params)
    assert node["opening"]["hinge_side"] == "RIGHT"
    assert node["opening_type"] is None


def test_travel_support_and_catalog_attributes_are_never_guessed(product: dict[str, Any], demo_60_params: SystemParams) -> None:
    with pytest.raises(OperationError) as error:
        apply(product, [{"op": "set_travel", "bay": "b1", "travel_mm": "600"}], demo_60_params)
    assert error.value.code == "travel_not_supported"
    glass = apply(product, [{"op": "set_glass", "module": "m1", "composition": "4"}], demo_60_params)["product"]
    assert glass["assembly"]["modules"][0]["tree"]["glass_article_sku"] == "FLOAT"
    with pytest.raises(OperationError):
        apply(product, [{"op": "set_glass", "module": "m1", "composition": "Inexistente"}], demo_60_params)
