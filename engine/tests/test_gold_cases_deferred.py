from __future__ import annotations

import pytest

from decimal import Decimal

from dekopen_engine import RailType, SystemParams, calculate_geometry
from engine.tests.test_shot06_core import core_node

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


@pytest.mark.xfail(strict=True, raises=NotImplementedError, reason="SHOT-24: G10 monorail geometry deferred by PLAN_SHOTS")
def test_g10_monorail_is_declared_deferred(demo_60_params: SystemParams) -> None:
    node = core_node("G5").model_copy(update={
        "id": "G10", "width_mm": Decimal("3000.00"), "height_mm": Decimal("2400.00"),
    })
    params = demo_60_params.model_copy(update={"rail_type": RailType.MONO})
    result = calculate_geometry(node, params)
    assert result.glasses and result.hardware_items
