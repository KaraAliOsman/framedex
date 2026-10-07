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


def test_new_operation_cannot_use_a_legacy_alias_to_bypass_physical_capability(product: dict[str, Any]) -> None:
    from engine.tests.opening_cases import opening_params
    params = opening_params("DEMO_60")
    with pytest.raises(OperationError) as error:
        apply(product, [{"op": "set_opening", "module": "m1", "opening": "SLIDING_2L"}], params)
    assert error.value.code == "opening_incompatible"
    assert product["assembly"]["modules"][0]["tree"]["opening_type"] == "FIXED"


def test_new_hinged_alias_resolves_the_same_physical_authority_as_the_ui() -> None:
    import json
    from dekopen_engine.geometry import calculate_geometry
    from dekopen_engine.models import ParametricNode
    from engine.tests.hardware_cases import hardware_case_inputs
    _, params, source, _ = hardware_case_inputs()[0]
    product = {"version": "product-v2", "assembly": {"couplings": [], "modules": [{
        "id": "m1", "width_mm": str(source.width_mm), "height_mm": str(source.height_mm),
        "tree": source.model_dump(mode="json")} ]}}
    changed = apply(product, [{"op": "set_opening", "module": "m1", "opening": "TILT_TURN_LEFT"}], params)
    tree = changed["product"]["assembly"]["modules"][0]["tree"]
    assert tree["opening_type"] is None
    assert source.opening is not None
    assert tree["opening"] == source.opening.model_dump(mode="json")
    actual = calculate_geometry(ParametricNode.model_validate_json(json.dumps(tree)), params)
    expected = calculate_geometry(source, params)
    assert actual == expected


def test_historical_alias_does_not_authorize_new_sliding_edit(product: dict[str, Any], demo_60_params: SystemParams) -> None:
    from dekopen_engine.design_operations import editable_legacy_openings
    from engine.tests.opening_cases import opening_params
    assert demo_60_params.uses_legacy_rules and demo_60_params.system_family is None
    assert "FIXED" in editable_legacy_openings(demo_60_params)
    assert not any(value.startswith("SLIDING") for value in editable_legacy_openings(demo_60_params))
    assert "SLIDING_2L" in editable_legacy_openings(opening_params("DEMO_CORREDERA_60"))
    with pytest.raises(OperationError) as error:
        apply(product, [{"op": "set_opening", "module": "m1", "opening": "SLIDING_2L"}], demo_60_params)
    assert error.value.code == "opening_incompatible"
    # Reading a historical tree remains exact; only the new edit is refused.
    historical = deepcopy(product)
    historical["assembly"]["modules"][0]["tree"]["opening_type"] = "SLIDING_2L"
    resized = apply(historical, [{"op": "resize", "module": "m1", "delta_width_mm": "100"}], demo_60_params)
    assert resized["product"]["assembly"]["modules"][0]["tree"]["opening_type"] == "SLIDING_2L"


def test_new_alias_edit_obeys_declared_family_even_with_legacy_authority(product: dict[str, Any], demo_60_params: SystemParams) -> None:
    from dekopen_engine.models import SystemFamily
    params = demo_60_params.model_copy(update={"system_family": SystemFamily.CASEMENT, "legacy_authority": True})
    assert params.uses_legacy_rules
    with pytest.raises(OperationError) as error:
        apply(product, [{"op": "set_opening", "module": "m1", "opening": "SLIDING_2L"}], params)
    assert error.value.code == "opening_incompatible"
    assert product["assembly"]["modules"][0]["tree"]["opening_type"] == "FIXED"


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


@pytest.mark.parametrize("recipe,expected", [("6 Float Incoloro", "6.00"), ("4-16-4", "24.00"),
                                             ("4+4", None), ("Sin composición declarada", None)])
def test_legacy_glass_change_never_inherits_previous_package_thickness(
    product: dict[str, Any], demo_60_params: SystemParams, recipe: str, expected: str | None,
) -> None:
    product["assembly"]["modules"][0]["tree"]["glass_thickness_mm"] = "12.00"
    changed = apply_operations(product, [{"op": "set_glass", "module": "m1", "sku": "NEW"}],
        params=demo_60_params, finish="WHITE", catalog={"glass_skus": {"NEW"}, "glass_specs": {"NEW": recipe}})["product"]
    bay = changed["assembly"]["modules"][0]["tree"]
    assert bay["glass_thickness_mm"] == expected and bay["glass_spec"] == recipe
    assert bay["glass_product"] is None
    assert product["assembly"]["modules"][0]["tree"]["glass_thickness_mm"] == "12.00"


def test_declared_bay_fields_and_copied_tree_preserve_manufacturing_identity(product: dict[str, Any], demo_60_params: SystemParams) -> None:
    changed = apply(product, [{"op": "set_bay_spec", "module": "m1", "bay": "b1", "patch": {
        "hardware_set_sku": None, "sill_height_mm": "500", "is_sidelight": True,
        "door_handedness": None, "glass_processing": None, "hardware_selection": None}}], demo_60_params)["product"]
    bay = changed["assembly"]["modules"][0]["tree"]
    assert bay["id"] == "left" and bay["sill_height_mm"] == "500" and bay["is_sidelight"] is True
    split = apply(product, [{"op": "split_bay", "bay": "b1", "axis": "H", "from": "START", "offset_mm": "400"}], demo_60_params)["product"]
    result = apply(changed, [{"op": "set_module_tree", "module": "m1", "tree": split["assembly"]["modules"][0]["tree"]}], demo_60_params)["product"]
    assert result["assembly"]["modules"][0]["id"] == "m1"
    assert result["assembly"]["modules"][0]["tree"] == split["assembly"]["modules"][0]["tree"]
    assert changed["assembly"]["modules"][0]["tree"] == bay


def test_missing_glass_and_frameless_supports_remain_explicit(product: dict[str, Any], demo_60_params: SystemParams) -> None:
    changed = apply(product, [{"op": "clear_glass_thickness", "module": "m1"},
        {"op": "set_frameless", "module": "m1", "spec": {"supports": [], "fittings": []}}], demo_60_params)["product"]
    module = changed["assembly"]["modules"][0]
    assert module["tree"]["glass_thickness_mm"] is None
    assert module["frameless"] == {"supports": [], "fittings": []}
    restored = apply(changed, [{"op": "set_frameless", "module": "m1", "spec": None}], demo_60_params)["product"]
    assert "frameless" not in restored["assembly"]["modules"][0]


def test_extras_retain_only_declared_selections_and_opening_dimensions(product: dict[str, Any], demo_60_params: SystemParams) -> None:
    selection = {"code": "SILL", "sides": ["BOTTOM"], "overhang_left_mm": "50", "overhang_right_mm": "100"}
    changed = apply(product, [{"op": "set_extras", "module": "m1", "extras": [selection], "context": {
        "opening_width_mm": "1600", "opening_height_mm": "1300"}}], demo_60_params)["product"]
    tree = changed["assembly"]["modules"][0]["tree"]
    assert tree["extras"] == [selection] and "quantity" not in tree["extras"][0]
    assert tree["extra_context"] == {"opening_width_mm": "1600", "opening_height_mm": "1300"}
    with pytest.raises(OperationError):
        validate_operation({"op": "set_extras", "module": "m1", "extras": [{**selection, "overhang_left_mm": 1.5}]})


def test_seam_and_swap_preserve_total_and_physical_connections(product: dict[str, Any], demo_60_params: SystemParams) -> None:
    graph = apply(product, [{"op": "add_unit", "side": "right"}], demo_60_params)["product"]
    ids = [module["id"] for module in graph["assembly"]["modules"]]
    changed = apply(graph, [{"op": "resize_seam", "left": ids[0], "right": ids[1], "delta_mm": "200"},
        {"op": "swap_modules", "module": ids[0], "other": ids[1]}], demo_60_params)["product"]
    assert [m["width_mm"] for m in changed["assembly"]["modules"]] == ["1300.00", "1700.00"]
    assert sum(Decimal(m["width_mm"]) for m in changed["assembly"]["modules"]) == Decimal("3000")
    assert changed["assembly"]["couplings"][0]["modules"] == ids[::-1]
    with pytest.raises(OperationError):
        apply(graph, [{"op": "resize_seam", "left": ids[0], "right": ids[1], "delta_mm": "2000"}], demo_60_params)


def test_coupler_requires_real_catalog_and_clear_is_explicit(product: dict[str, Any], demo_60_params: SystemParams) -> None:
    graph = apply(product, [{"op": "add_unit", "side": "right"}], demo_60_params)["product"]
    coupling = graph["assembly"]["couplings"][0]["id"]
    with pytest.raises(OperationError):
        apply(graph, [{"op": "set_coupler_sku", "coupling": coupling, "sku": "INVENTED"}], demo_60_params)
    result = apply_operations(graph, [{"op": "set_coupler_sku", "coupling": coupling, "sku": "REAL"}],
        params=demo_60_params, finish="WHITE", catalog={"coupler_skus": {"REAL"}})["product"]
    assert result["assembly"]["couplings"][0]["coupler_profile_sku"] == "REAL"
    cleared = apply(result, [{"op": "set_coupler_sku", "coupling": coupling, "sku": None}], demo_60_params)["product"]
    assert cleared["assembly"]["couplings"][0]["coupler_profile_sku"] is None


def test_contour_edits_and_decimal_resize_preserve_topology(product: dict[str, Any], demo_60_params: SystemParams) -> None:
    module = product["assembly"]["modules"][0]
    module["contour"] = {"vertices": [{"x_mm": "0", "y_mm": "0"}, {"x_mm": "1500", "y_mm": "0"},
        {"x_mm": "1500", "y_mm": "1200"}, {"x_mm": "0", "y_mm": "1200"}], "bulges": ["200", None, None, None]}
    changed = apply(product, [{"op": "set_contour_vertex", "module": "m1", "index": 1, "x_mm": "100", "y_mm": "0", "from": "END"},
        {"op": "set_contour_bulge", "module": "m1", "index": 0, "rise_mm": "150"},
        {"op": "set_module_width", "module": "m1", "width_mm": "3000"},
        {"op": "set_height", "height_mm": "2400"}], demo_60_params)["product"]
    contour = changed["assembly"]["modules"][0]["contour"]
    assert contour["vertices"][1] == {"x_mm": "2800.00", "y_mm": "0.00"}
    assert contour["bulges"] == ["300.00", None, None, None]
    with pytest.raises(OperationError):
        apply(product, [{"op": "set_contour_vertex", "module": "m1", "index": 9, "x_mm": "0", "y_mm": "0"}], demo_60_params)
