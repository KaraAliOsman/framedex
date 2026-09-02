from __future__ import annotations

import pytest

from dekopen_engine import ParametricNode, SystemParams, calculate_geometry


@pytest.mark.xfail(strict=True, reason="SHOT-06: hardware_kits resolution")
def test_g3_hardware_kit_resolution_is_deferred(
    demo_60_params: SystemParams,
    g3_node: ParametricNode,
) -> None:
    result = calculate_geometry(g3_node, demo_60_params)
    assert result.hardware_items


@pytest.mark.xfail(
    strict=True,
    reason="SHOT-06B: G8 extended geometry deferred by PLAN_SHOTS",
)
def test_g8_sliding_3l_is_declared_deferred() -> None:
    raise NotImplementedError("G8 is outside SHOT-03")


@pytest.mark.xfail(
    strict=True,
    reason="SHOT-06B: G9 extended geometry deferred by PLAN_SHOTS",
)
def test_g9_sliding_4l_is_declared_deferred() -> None:
    raise NotImplementedError("G9 is outside SHOT-03")


@pytest.mark.xfail(
    strict=True,
    reason="SHOT-06B: G11 extended geometry deferred by PLAN_SHOTS",
)
def test_g11_double_door_is_declared_deferred() -> None:
    raise NotImplementedError("G11 is outside SHOT-03")


@pytest.mark.xfail(
    strict=True,
    reason="SHOT-06B: G12 extended geometry deferred by PLAN_SHOTS",
)
def test_g12_large_fixed_is_declared_deferred() -> None:
    raise NotImplementedError("G12 is outside SHOT-03")
