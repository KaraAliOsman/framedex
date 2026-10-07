from decimal import Decimal
import json
from pathlib import Path

import pytest

from dekopen_engine.mounting import MountingRule, OpeningSurvey, derive_fabrication
from engine.tests.mounting_cases import mounting_cases


def test_gold_cases_mounting() -> None:
    assert mounting_cases() == json.loads(Path(__file__).with_name("golden_mounting.json").read_text(encoding="utf-8"))


def test_minimum_samples_and_manual_override_remain_visible() -> None:
    case = mounting_cases()["IN_OPENING"]
    survey = OpeningSurvey.model_validate({**case["survey"], "override": {
        "width_mm": "1510", "height_mm": "1200", "reason": "Medida fijada por técnico en obra"}})
    result = derive_fabrication(survey, MountingRule.model_validate(case["rule"]))
    assert result.width.opening_mm == Decimal("1520")
    assert result.width.derived_mm == Decimal("1500")
    assert result.width.fabrication_mm == Decimal("1510")
    assert result.width.deviation_mm == Decimal("10")
    assert len(result.warnings) == 2


@pytest.mark.parametrize("samples", [["0"], ["1500", "1499"], [True], [1500.01], ["1500.001"], ["NaN"], ["Infinity"]])
def test_rejects_untrustworthy_samples(samples: list[object]) -> None:
    with pytest.raises(ValueError):
        OpeningSurvey.model_validate({**mounting_cases()["IN_OPENING"]["survey"], "widths_mm": samples})


def test_no_fabrication_when_allowances_consume_opening() -> None:
    case = mounting_cases()["SUBFRAME"]
    with pytest.raises(ValueError, match="no positiva"):
        derive_fabrication(OpeningSurvey.model_validate({**case["survey"], "widths_mm": ["40"]}),
                           MountingRule.model_validate(case["rule"]))
