import json
from pathlib import Path

from engine.tests.operation_cases import operation_cases


def test_editing_plans_have_exact_frozen_manufacturing_geometry() -> None:
    stored = json.loads(Path(__file__).with_name("golden_design_operations.json").read_text(encoding="utf-8"))
    assert operation_cases() == stored
