import json
from copy import deepcopy
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

import pytest
from dekopen_engine.analytics import (
    actual_cost,
    average,
    bar_reading,
    margin_bridge,
    number,
    ratio,
    total,
)
from engine.tests.analytics_cases import analytics_cases


def test_manual_bridge_and_each_peso_occurs_once() -> None:
    case = analytics_cases()
    assert case == json.loads(Path(__file__).with_name("golden_analytics.json").read_text())
    # 42×10 + 3×20 + 20 = 500; 3×10 + 0.5×20 = 40.
    bridge = case["bridge"]
    assert Decimal(bridge["real_cost"]) == 540 and Decimal(bridge["real_profit"]) == 360
    assert bridge["real_margin"] == "0.4" and Decimal(bridge["delta_profit"]) == -40
    assert [d["amount"] for d in bridge["drivers"]] == ["10", "10", "-10", "-10", "-40.0"]
    assert sum(Decimal(d["amount"]) for d in bridge["drivers"]) == Decimal("-40")
    # Discount −100 is already in net 900: subtracting it again would give −140.
    assert bridge["discount"] == "-100"
    assert case["bars"] == {"waste_ratio": "0.05", "utilization": "0.9", "cause": None}
    # 20 − 4 + 2 + 1 − credit 3 = 16, with waste 2 + 2 = 4 included.
    assert case["recovered"]["cost"] == "16.0"
    assert case["recovered"]["materials"] == "12.0" and case["recovered"]["waste"] == "4"
    assert case["wire"] == {"small": "0.00000001", "zero": "0.00000000"}
    assert case["remnant_quantities"] == {"bar": "0.5", "sheet": "1.875"}


def test_context_precision_is_not_an_input_to_analytics() -> None:
    expected = analytics_cases()
    fraction = ratio("1", "3")
    with localcontext() as context:
        context.prec = 6
        assert analytics_cases() == expected
        assert ratio("1", "3") == fraction


def test_missing_evidence_never_sums_a_complete_subset() -> None:
    assert total(["10", None, "20"]) is None
    assert total([]) is None and average([]) is None and ratio(1, 0) is None
    assert bar_reading(
        input_mm="6000", productive_mm="5400", waste_mm="300", reusable_mm="300", complete=False
    )["cause"]
    partial = actual_cost(materials=[], labor=[], other=None, credit=None, closed=False)
    assert partial["cost"] is None and partial["lines"] == []
    case = analytics_cases()
    quote: dict[str, Any] = {
        "net": "900",
        "cost": "500",
        "materials": "400",
        "waste": "40",
        "labor": "50",
        "other": "10",
        "discount": "-100",
    }
    assert margin_bridge(quote=quote, base=[case["base"]], remakes=[partial])["real_margin"] is None
    quote["composition_known"] = False
    assert margin_bridge(quote=quote, base=[case["base"]], remakes=[])["drivers"] == []


@pytest.mark.parametrize("value", [True, "NaN", "Infinity", "-0.01", 0.1])
def test_invalid_measurement_is_rejected(value: object) -> None:
    with pytest.raises((ValueError, ArithmeticError)):
        number(value)


def test_impossible_cut_and_loss_are_not_repaired() -> None:
    with pytest.raises(ValueError, match="actual_cut_does_not_close"):
        bar_reading(input_mm="6000", productive_mm="5400", waste_mm="301", reusable_mm="300")
    material = {
        "id": "m",
        "kind": "CONSUMPTION",
        "quantity": "1",
        "unit_cost": "10",
        "waste_quantity": "2",
    }
    with pytest.raises(ValueError, match="invalid_waste_quantity"):
        actual_cost(
            materials=[material],
            labor=[{"id": "s", "hours": "0", "hourly_rate": "0"}],
            other="0",
            credit="0",
            closed=True,
        )
    material = deepcopy(material)
    material.update(kind="RETURN", waste_quantity="0.1")
    with pytest.raises(ValueError, match="invalid_waste_quantity"):
        actual_cost(
            materials=[material],
            labor=[{"id": "s", "hours": "0", "hourly_rate": "0"}],
            other="0",
            credit="0",
            closed=True,
        )
