from __future__ import annotations

import pytest

from decimal import Decimal

from dekopen_engine import RailType, SystemParams, calculate_geometry
from engine.tests.test_shot06_core import core_node

@pytest.mark.xfail(
    strict=True,
    reason="G8 sliding-3L geometry not yet supported",
)
def test_g8_sliding_3l_is_declared_deferred() -> None:
    raise NotImplementedError("G8 sliding-3L is not yet supported")


@pytest.mark.xfail(
    strict=True,
    reason="G9 sliding-4L geometry not yet supported",
)
def test_g9_sliding_4l_is_declared_deferred() -> None:
    raise NotImplementedError("G9 sliding-4L is not yet supported")


@pytest.mark.xfail(
    strict=True,
    reason="G11 double-door geometry not yet supported",
)
def test_g11_double_door_is_declared_deferred() -> None:
    raise NotImplementedError("G11 double-door is not yet supported")


@pytest.mark.xfail(
    strict=True,
    reason="G12 large-fixed geometry not yet supported",
)
def test_g12_large_fixed_is_declared_deferred() -> None:
    raise NotImplementedError("G12 large-fixed is not yet supported")


@pytest.mark.xfail(strict=True, raises=NotImplementedError, reason="G10 monorail geometry not yet supported")
def test_g10_monorail_is_declared_deferred(demo_60_params: SystemParams) -> None:
    node = core_node("G5").model_copy(update={
        "id": "G10", "width_mm": Decimal("3000.00"), "height_mm": Decimal("2400.00"),
    })
    params = demo_60_params.model_copy(update={"rail_type": RailType.MONO})
    result = calculate_geometry(node, params)
    assert result.glasses and result.hardware_items
