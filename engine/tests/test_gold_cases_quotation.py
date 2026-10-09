import json
from pathlib import Path

from engine.tests.quotation_cases import quotation_cases


def test_sealed_line_display_discount_and_payments_remain_exact() -> None:
    assert quotation_cases() == json.loads(Path(__file__).with_name("golden_quotation.json").read_text())
