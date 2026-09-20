from decimal import Decimal as D

import pytest

from dekopen_engine.geometry import compute_geometry
from dekopen_engine.layout import node_layout
from dekopen_engine.models import ParametricNode, NodeType, SystemParams
from engine.tests.test_tree_geometry import _fixed_bay


@pytest.mark.parametrize("kind,width,height,offset", [
    ("SPLIT_V", "1200", "1000", "300"),
    ("SPLIT_V", "2000", "1000", "500"),
    ("SPLIT_H", "2000", "1200", "300"),
])
def test_layout_uses_axis_dimension(
    demo_60_params: SystemParams, kind: str, width: str, height: str, offset: str,
) -> None:
    root = ParametricNode(id="split", type=NodeType(kind), width_mm=D(width), height_mm=D(height),
        split_offset_mm=D(offset), mullion_profile_sku="POSTE-V" if kind == "SPLIT_V" else "POSTE-H",
        children=[_fixed_bay("a"), _fixed_bay("b")])
    layout = node_layout(compute_geometry(root, demo_60_params))[0]
    first, second = map(D, layout["child_weights"])
    assert first / (first + second) == D("0.25")
    assert layout["vertical"]["half"] == str((D(width) / 2).quantize(D("0.01")))
    assert layout["horizontal"]["half"] == str((D(height) / 2).quantize(D("0.01")))


def test_nested_shortcut_uses_traversal_parent_not_root(demo_60_params: SystemParams) -> None:
    nested = ParametricNode(id="inner", type=NodeType.SPLIT_H, split_offset_mm=D("350"),
        mullion_profile_sku="POSTE-H", children=[_fixed_bay("a"), _fixed_bay("b")])
    root = ParametricNode(id="outer", type=NodeType.SPLIT_V,
        width_mm=D("2000"), height_mm=D("1200"), split_offset_mm=D("500"),
        mullion_profile_sku="POSTE-V", children=[nested, _fixed_bay("c")])
    computation = compute_geometry(root, demo_60_params)
    layout = {item["node_id"]: item for item in node_layout(computation)}
    assert D(layout["inner"]["height_mm"]) == D("1080")
    assert D(layout["inner"]["horizontal"]["half"]) == D("540")
    assert D(layout["inner"]["horizontal"]["one_third"]) == D("360")
    assert D(layout["inner"]["horizontal"]["two_thirds"]) == D("720")
    assert D(layout["inner"]["width_mm"]) < D("500")
