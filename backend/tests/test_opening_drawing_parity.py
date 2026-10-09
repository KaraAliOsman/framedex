import json
import re
from decimal import Decimal as D
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from dekopen_engine.models import Opening, SlidingTravel
from documents.renderers import _opening_symbol_svg, _PAL_TECH, _physical_leaf_svg, _position_svg

CASES = json.loads((Path(__file__).resolve().parents[2] / "engine/tests/fixtures/symbols/cases.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("fixture", CASES, ids=lambda fixture: fixture["name"])
def test_pdf_renderer_matches_shared_primitives(fixture):
    for leaf, expected in zip(fixture["leaves"], fixture["expected"], strict=True):
        opening = Opening.model_validate_json(json.dumps(leaf["opening"]))
        fragment = _opening_symbol_svg(opening, D(leaf["x_mm"]), D(leaf["y_mm"]), D(leaf["width_mm"]),
            D(leaf["height_mm"]), _PAL_TECH, exterior=fixture["view"] == "exterior",
            travel=SlidingTravel(leaf["travel"]) if leaf["travel"] else None)
        paths = list(ET.fromstring('<g>'+fragment+'</g>'))
        actual = []
        for path in paths:
            numbers = [D(number) for number in re.findall(r"-?\d+(?:\.\d+)?", path.get("d"))]
            points = [[D(1200)-x if fixture["view"] == "exterior" else x, y] for x,y in zip(numbers[::2],numbers[1::2],strict=True)]
            actual.append({"symbol":path.get("data-symbol"), "points":points, "dashed":"stroke-dasharray" in path.attrib})
        assert actual == [{**line,"points":[[D(x),D(y)] for x,y in line["points"]]} for line in expected["lines"]]
        if leaf["handle"]:
            out=[]
            _physical_leaf_svg(leaf,out,_PAL_TECH,(D(0),D(0)),fixture["view"]=="exterior")
            handle=ET.fromstring(''.join(out)).find("path[@data-handle]")
            numbers=[D(number) for number in re.findall(r"-?\d+(?:\.\d+)?",handle.get("d"))]
            assert [D(1200)-numbers[0] if fixture["view"]=="exterior" else numbers[0],numbers[1]] == list(map(D,expected["handle"]))


def test_special_shapes_have_glazing_and_no_door_arc():
    directory=Path(__file__).resolve().parents[2]/"engine/tests/fixtures/symbols"
    for shape in json.loads((directory/"contours.json").read_text(encoding="utf-8")):
        product={"version":"product-v2","assembly":{"modules":[{"id":"m1","width_mm":shape["width_mm"],
            "height_mm":shape["height_mm"],"contour":shape["contour"],"tree":{"id":"b1","type":"BAY","opening_type":"FIXED"}}],"couplings":[]}}
        svg=_position_svg({"position_index":1,"parametric_tree":product})
        root=ET.fromstring(svg)
        glass=root.find(".//{*}path[@data-contour-glass]")
        assert glass is not None and glass.get("fill")==_PAL_TECH["bay_fill"]
        assert "Vista interior" in svg
    door=_position_svg({"position_index":2,"width_mm":"1000","height_mm":"2100","parametric_tree":{
        "id":"b1","type":"BAY","opening_type":"DOOR_ENTRY","door_handedness":"LEFT"}})
    assert "data-symbol=\"turn_left\"" in door
    assert not re.search(r'd="[^\"]*A ',door)


def test_unequal_sliding_bays_keep_local_plan_coordinates_and_half_up_dimensions():
    from documents.drawing import annotations
    def bay(name):
        return {"id": name, "type": "BAY", "opening_type": "SLIDING", "sliding_layout": {
            "tracks": 2, "panels": [{"slot": name+"-1", "kind": "MOVING", "track": 0, "travel": "RIGHT"},
                {"slot": name+"-2", "kind": "MOVING", "track": 1, "travel": "LEFT"}]}}
    tree = {"id": "split", "type": "SPLIT_V", "split_offset_mm": "400.5", "children": [bay("a"), bay("b")]}
    fragment, _, _, _, _ = annotations(tree, x=D(100), y=D(0), width=D(1200), height=D(1400), handles=[], color="black", exterior=True)
    root = ET.fromstring('<g>'+fragment+'</g>')
    panels = {line.get("data-plan-slot"): line for line in root.findall('line[@data-plan-slot]')}
    assert D(panels["a-1"].get("x2")) < D("500.5")
    assert D(panels["b-1"].get("x1")) > D("500.5")
    assert "401 mm" in fragment
    assert all("scale(-1 1)" in text.get("transform") for text in root.findall('text'))


def test_portal_passes_sealed_geometry_without_private_manufacturing_fields():
    from portal.service import _sealed_positions
    leaf = {**CASES[2]["leaves"][0], "bay_id": "m1|b1", "leaf_id": None,
        "use": "WINDOW", "source": "private kit source", "cost": "12345"}
    position = {"id":"p", "width_mm":"1200", "height_mm":"1400", "opening_leaves":[leaf], "parametric_tree":CASES[2]["product"]}
    version = {"snapshot_json": {"positions":[position]}}
    projected = _sealed_positions(version)[0]["opening_leaves"][0]
    assert projected["x_mm"] == leaf["x_mm"]
    assert projected["opening"] == leaf["opening"]
    assert projected["source"] == "Revisión emitida"
    assert "cost" not in projected
    assert position["opening_leaves"][0]["source"] == "private kit source"


def test_short_dimension_segments_use_separate_label_lanes():
    from documents.drawing import annotations
    tree = {"id":"v", "type":"SPLIT_V", "split_offset_mm":"50", "children":[
        {"id":"a", "type":"BAY", "opening_type":"FIXED"},
        {"id":"b", "type":"BAY", "opening_type":"FIXED"}]}
    fragment, _, _, _, _ = annotations(tree, x=D(0), y=D(0), width=D(100), height=D(1400),
        handles=[], color="black", font_mm=D(20))
    root = ET.fromstring('<g>'+fragment+'</g>')
    labels = [label for label in root.findall('text') if label.text == '50 mm']
    assert len(labels) == 2
    assert abs(D(labels[0].get('y')) - D(labels[1].get('y'))) >= D(40)


def test_legacy_door_never_invents_handle_or_hinge():
    svg = _position_svg({"position_index":1, "width_mm":"1000", "height_mm":"2100",
        "parametric_tree":{"id":"b", "type":"BAY", "opening_type":"DOOR_ENTRY"}}, commercial=True)
    assert 'Sin dato: bisagras' in svg
    assert 'data-symbol="turn_' not in svg
    assert 'data-handle' not in svg


@pytest.mark.parametrize("view", ["interior", "exterior"])
def test_stacked_modules_keep_all_dimensions_on_separate_gutters(view):
    fixtures = json.loads((Path(__file__).resolve().parents[2] / "engine/tests/fixtures/symbols/assemblies.json").read_text(encoding="utf-8"))
    fixture = next(case for case in fixtures if case["name"] == "apilado")
    root = ET.fromstring(_position_svg({"position_index":1, "parametric_tree":fixture["product"]}, view=view))
    labels = [text for text in root.findall('.//{*}text') if (text.text or '').endswith(' mm')]
    coordinates = [(D(text.get('x')), D(text.get('y'))) for text in labels]
    assert len(coordinates) == len(set(coordinates))
    assert {text.text for text in labels} >= {'400 mm', '600 mm', '800 mm', '900 mm', '1\u2009200 mm', '1\u2009600 mm'}
    if view == 'exterior':
        assert all('scale(-1 1)' in text.get('transform', '') for text in root.findall('.//{*}text') if (text.text or '').startswith('Módulo'))
