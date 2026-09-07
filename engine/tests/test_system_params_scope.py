"""Canonical SHOT-06 scope: 27 mapped, 22 consumed, 2 metadata, 3 reserved."""

import ast
from collections.abc import Callable
from decimal import Decimal
import inspect

import pytest

from dekopen_engine import ParametricNode, SystemParams, calculate_geometry
from dekopen_engine import geometry, hardware, weight
from engine.tests.test_shot06_core import core_node

CORE_CONSUMERS: dict[str, Callable[..., object]] = {
    "material": geometry.compute_geometry,
    "effective_profile_articles": geometry._article,
    "glazing_bead_rules": geometry.resolve_bead_rule,
    "rebate_depth_mm": geometry._pocket_dimension,
    "end_milling_overlap_mm": geometry._walk_node,
    "sash_overlap_mm": geometry.single_rectangular_sash_geometry,
    "glass_clearance_white_mm": geometry.compute_geometry,
    "glass_clearance_foil_mm": geometry.compute_geometry,
    "pulley_height_mm": geometry._append_bay,
    "central_overlap_mm": geometry._append_bay,
    "sliding_end_add_mm": geometry._append_bay,
    "door_threshold_mm": geometry._append_door,
    "door_bottom_clearance_mm": geometry._append_door,
    "rail_type": hardware.evaluate_hardware_candidates,
    "pvc_weight_kg_m": weight.base_leaf_weight,
    "steel_weight_kg_m": weight.base_leaf_weight,
    "hardware_kit_weight_kg": weight.with_hardware_weight,
    "available_hardware_kits": hardware.evaluate_hardware_candidates,
    "sliding_glazing_deduction_width_mm": geometry._append_leaf,
    "sliding_glazing_deduction_height_mm": geometry._append_leaf,
    "door_leaf_side_clearance_mm": geometry._append_door,
    "available_panel_rules": geometry._append_leaf,
}
METADATA = {"system_code", "depth_mm"}
RESERVED = {"sliding_lateral_clearance_mm", "corner_bracket_loss_mm", "hook_depth_mm"}


def test_every_system_parameter_has_an_explicit_scope() -> None:
    assert len(CORE_CONSUMERS) == 22 and len(METADATA) == 2 and len(RESERVED) == 3
    assert set(CORE_CONSUMERS) | METADATA | RESERVED == set(SystemParams.model_fields)
    for field, consumer in CORE_CONSUMERS.items():
        reads = {
            node.attr for node in ast.walk(ast.parse(inspect.getsource(consumer)))
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
            and node.value.id == "params" and isinstance(node.ctx, ast.Load)
        }
        assert field in reads, f"{field} has lost its real consumer {consumer.__name__}"


@pytest.mark.parametrize("field", sorted(RESERVED))
@pytest.mark.parametrize("case", ["G3", "G5", "G6", "G7"])
def test_reserved_parameters_do_not_change_core_results(
    field: str, case: str, demo_60_params: SystemParams, g3_node: ParametricNode,
) -> None:
    node = g3_node if case == "G3" else core_node(case)
    before = calculate_geometry(node, demo_60_params)
    changed = demo_60_params.model_copy(update={field: Decimal("123.45")})
    assert calculate_geometry(node, changed) == before
