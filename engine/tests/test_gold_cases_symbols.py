"""Shared, frozen DIN cases consumed by the Python and TS renderers."""
import json
from decimal import Decimal as D
from pathlib import Path
from typing import Any

import pytest

from dekopen_engine.drawing import dimension_chains
from dekopen_engine.geometry import calculate_geometry, sliding_travel, validate_sliding_layout
from dekopen_engine.models import Opening, ParametricNode, SlidingLayout, SystemParams
from dekopen_engine.symbols import opening_symbol_lines

CASES = json.loads((Path(__file__).parent / "fixtures/symbols/cases.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_shared_opening_primitives(case: dict[str, Any]) -> None:
    from dekopen_engine.models import SlidingTravel
    for leaf, expected in zip(case["leaves"], case["expected"], strict=True):
        opening = Opening.model_validate_json(json.dumps(leaf["opening"]))
        lines = opening_symbol_lines(opening, x=D(leaf["x_mm"]), y=D(leaf["y_mm"]),
            width=D(leaf["width_mm"]), height=D(leaf["height_mm"]), mirror=False,
            exterior=case["view"] == "exterior",
            travel=SlidingTravel(leaf["travel"]) if leaf["travel"] else None)
        actual = [{"symbol": line.symbol, "dashed": line.dashed,
                   "points": [[D(1200)-x if case["view"] == "exterior" else x, y] for x, y in line.points]}
                  for line in lines]
        frozen = [{**line, "points": [[D(x), D(y)] for x, y in line["points"]]} for line in expected["lines"]]
        assert actual == frozen


def test_old_sliding_bytes_and_bom_remain_exact(demo_60_params: SystemParams) -> None:
    raw: dict[str, Any] = {"id": "slider", "type": "BAY", "width_mm": "1200.00", "height_mm": "1200.00",
           "opening_type": "SLIDING", "glass_thickness_mm": "4.00", "glass_spec": "4",
           "sliding_layout": {"tracks": 2, "panels": [
               {"slot": "S1", "kind": "MOVING", "track": 0},
               {"slot": "S2", "kind": "MOVING", "track": 1}]}}
    old = ParametricNode.model_validate_json(json.dumps(raw))
    assert old.model_dump(mode="json")["sliding_layout"] == raw["sliding_layout"]
    original = calculate_geometry(old, demo_60_params)
    for index, panel in enumerate(raw["sliding_layout"]["panels"]):
        panel["travel"] = "RIGHT" if index == 0 else "LEFT"
    declared = ParametricNode.model_validate_json(json.dumps(raw))
    assert calculate_geometry(declared, demo_60_params) == original
    assert old.sliding_layout is not None
    assert [sliding_travel(panel, i, 2) for i, panel in enumerate(old.sliding_layout.panels)] == ["RIGHT", "LEFT"]


@pytest.mark.parametrize("travels", [["LEFT", "LEFT"], ["RIGHT", "RIGHT"]])
def test_travel_into_jamb_is_rejected(travels: list[str], demo_60_params: SystemParams) -> None:
    layout = SlidingLayout.model_validate_json(json.dumps({"tracks": 2, "panels": [
        {"slot": f"S{i}", "kind": "MOVING", "track": i, "travel": travel} for i, travel in enumerate(travels)]}))
    with pytest.raises(ValueError, match="jamba"):
        validate_sliding_layout(layout, demo_60_params)


def test_null_moving_and_travelling_fixed_are_rejected() -> None:
    for kind, travel in [("MOVING", None), ("FIXED", "LEFT")]:
        with pytest.raises(ValueError):
            SlidingLayout.model_validate_json(json.dumps({"tracks": 2, "panels": [
                {"slot": "S1", "kind": kind, "track": None, "travel": travel}]}))


def test_oxxo_both_declared_arrangements_and_adjacent_track_guard(demo_60_params: SystemParams) -> None:
    for travel in ([None, "LEFT", "RIGHT", None], [None, "RIGHT", "LEFT", None]):
        raw: dict[str, Any] = {"tracks": 2, "panels": [{"slot": f"S{i}", "kind": "FIXED" if i in (0, 3) else "MOVING",
              "track": None if i in (0, 3) else i-1, "travel": direction} for i, direction in enumerate(travel)]}
        validate_sliding_layout(SlidingLayout.model_validate_json(json.dumps(raw)), demo_60_params)
        raw["panels"][2]["track"] = 0
        with pytest.raises(ValueError, match="share a track"):
            validate_sliding_layout(SlidingLayout.model_validate_json(json.dumps(raw)), demo_60_params)


def test_nested_axis_chains_exact_and_outside_leaf_levels() -> None:
    tree = ParametricNode.model_validate_json(json.dumps({"id": "v", "type": "SPLIT_V", "split_offset_mm": "400.50",
        "children": [{"id": "h", "type": "SPLIT_H", "split_offset_mm": "350.25", "children": [
            {"id": "a", "type": "BAY", "opening_type": "FIXED"}, {"id": "b", "type": "BAY", "opening_type": "FIXED"}]},
            {"id": "c", "type": "BAY", "opening_type": "FIXED"}]}))
    facts = dimension_chains(tree, D("1200"), D("1400"))
    assert [(chain.axis, chain.level, [segment.value_mm for segment in chain.segments]) for chain in facts.chains] == [
        ("V", 0, [D("400.50"), D("799.50")]), ("H", 0, [D("350.25"), D("1049.75")])]
    assert [(bay.bay_id, bay.x_mm, bay.y_mm, bay.width_mm, bay.height_mm) for bay in facts.bays] == [
        ("a", D(0), D(0), D("400.50"), D("350.25")),
        ("b", D(0), D("350.25"), D("400.50"), D("1049.75")),
        ("c", D("400.50"), D(0), D("799.50"), D("1400"))]


def test_half_circle_inset_keeps_exact_crown_and_springline() -> None:
    from dekopen_engine.contour import Contour, offset_contour
    contour = Contour.model_validate_json(json.dumps({"vertices": [
        {"x_mm":"0","y_mm":"0"},{"x_mm":"1200","y_mm":"0"},
        {"x_mm":"1200","y_mm":"1000"},{"x_mm":"0","y_mm":"1000"}],
        "bulges":[None,None,"600",None]}))
    inset = offset_contour(contour, D("40"))
    assert inset.bulges == [None,None,D("560"),None]
    assert [(point.x_mm,point.y_mm) for point in inset.vertices] == [
        (D("40"),D("40")),(D("1160"),D("40")),(D("1160"),D("1000")),(D("40"),D("1000"))]


def test_historical_handle_datum_is_literal_and_missing_stays_missing() -> None:
    tree = ParametricNode.model_validate_json(json.dumps({"id":"b", "type":"BAY", "opening_type":"TURN_LEFT", "handle_height_mm":"1000.50"}))
    facts = dimension_chains(tree, D(1200), D(1400))
    assert facts.authored_handles[0].y_mm == D("399.50")
    assert facts.authored_handles[0].height_from_bottom_mm == D("1000.50")
    assert dimension_chains(tree.model_copy(update={"handle_height_mm":None}), D(1200), D(1400)).authored_handles == []


def test_arch_drawing_dimension_uses_exact_crown_not_nominal_springline() -> None:
    from dekopen_engine.contour import Contour, contour_bounds
    from dekopen_engine.product import ProductModel, elevation_drawing_envelope
    for rise in ("600", "300"):
        contour = Contour.arch_top(D("1200"), D("1000"), D(rise))
        assert contour_bounds(contour) == (D(0), D(0), D(1200), D(1000) + D(rise))
        product = ProductModel.model_validate_json(json.dumps({"version":"product-v2", "assembly":{
            "modules":[{"id":"m1", "width_mm":"1200", "height_mm":"1000",
                "contour":contour.model_dump(mode="json"), "tree":{"id":"b", "type":"BAY", "opening_type":"FIXED"}}],
            "couplings":[]}}))
        envelope = elevation_drawing_envelope(product.assembly)
        assert envelope.height_mm == D(1000) + D(rise)
        assert envelope.width_mm == D(1200)


def test_shared_assembly_drawing_facts_stay_exact() -> None:
    from dekopen_engine.product import ProductModel, elevation_drawing_envelope
    fixtures = json.loads((Path(__file__).parent / "fixtures/symbols/assemblies.json").read_text(encoding="utf-8"))
    for fixture in fixtures:
        product = ProductModel.model_validate_json(json.dumps(fixture["product"]))
        assert elevation_drawing_envelope(product.assembly).model_dump(mode="json") == fixture["elevation"]
        for module in product.assembly.modules:
            assert dimension_chains(module.tree, module.width_mm, module.height_mm).model_dump(mode="json") == fixture["drawing"][module.id]
        assert all(coupling.coupler_profile_sku is None for coupling in product.assembly.couplings)
