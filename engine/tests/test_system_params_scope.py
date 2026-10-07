"""Canonical SHOT-06 scope: 25 mapped, 20 consumed, 2 metadata, 3 reserved."""

import ast
from collections.abc import Callable
from decimal import Decimal
import inspect

import pytest

from dekopen_engine import ParametricNode, SystemParams, calculate_geometry
from dekopen_engine import catalog_rules, finishes, geometry, hardware, openings
from engine.tests.test_shot06_core import core_node

CORE_CONSUMERS: dict[str, Callable[..., object]] = {
    "material": geometry.compute_geometry,
    "effective_profile_articles": geometry._article,
    "glazing_bead_rules": geometry.resolve_bead_rule,
    "rebate_depth_mm": geometry.rebate_depth,
    "end_milling_overlap_mm": geometry._end_milling_overlap,
    "sash_overlap_mm": geometry.single_rectangular_sash_geometry,
    "glass_clearance_white_mm": geometry.compute_geometry,
    "glass_clearance_foil_mm": geometry.compute_geometry,
    "pulley_height_mm": catalog_rules.sliding_parameters,
    "central_overlap_mm": catalog_rules.sliding_parameters,
    "sliding_end_add_mm": catalog_rules.sliding_parameters,
    "door_threshold_mm": geometry._append_door,
    "door_bottom_clearance_mm": geometry._append_door,
    "rail_type": hardware.evaluate_hardware_candidates,
    "available_hardware_kits": hardware.evaluate_hardware_candidates,
    "sliding_glazing_deduction_width_mm": catalog_rules.sliding_parameters,
    "sliding_glazing_deduction_height_mm": catalog_rules.sliding_parameters,
    "door_leaf_side_clearance_mm": geometry._append_door,
    "available_panel_rules": geometry._append_leaf,
    "rail_count": catalog_rules.sliding_parameters,
    "system_family": catalog_rules.validate_family,
    "sliding": catalog_rules.sliding_parameters,
    "dimensional_limits": catalog_rules.validate_leaf_limits,
    "opening_capabilities": openings.resolve_capability,
    "paired_leaf_rule": geometry._append_paired_leaves,
    "compatible_opening_systems": openings.resolve_capability,
    "finish_authority": finishes.resolve_finish,
    "finish_profile_skus": finishes.resolve_finish,
}
METADATA = {"system_code", "depth_mm"}
RESERVED = {"sliding_lateral_clearance_mm", "corner_bracket_loss_mm", "hook_depth_mm"}
# Input-validity authority consumed by the API adapter (finish membership gates
# `color`), not a formula input — `backend/engine_api/adapter.py` reads it.
API_BOUNDARY = {"finishes", "legacy_authority"}


def test_every_system_parameter_has_an_explicit_scope() -> None:
    assert (
        len(CORE_CONSUMERS) == 28
        and len(METADATA) == 2
        and len(RESERVED) == 3
        and len(API_BOUNDARY) == 2
    )
    assert (
        set(CORE_CONSUMERS) | METADATA | RESERVED | API_BOUNDARY
        == set(SystemParams.model_fields)
    )
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
