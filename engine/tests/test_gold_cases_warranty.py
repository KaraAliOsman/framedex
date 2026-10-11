import json
from pathlib import Path

from engine.tests.warranty_cases import warranty_cases


def test_golden_warranty_dates_require_sealed_authority() -> None:
    assert warranty_cases() == json.loads(
        Path(__file__).with_name("golden_warranty.json").read_text()
    )
