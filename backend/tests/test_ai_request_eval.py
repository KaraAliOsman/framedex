"""P08 evaluation over recorded proposals: windows read from synthetic
requests are accepted only with measures and quantity the request states.

Reports the share of correct windows (≥ 90 %) and requires zero accepted
measures that the request does not contain."""

from decimal import Decimal
from pathlib import Path

import yaml

from ai_gateway import evals, origins

CASES = yaml.safe_load(
    (Path(evals.__file__).with_name("request_cases.yaml")).read_text(encoding="utf-8"))["cases"]


def _op(window: dict) -> dict:
    return {"op": "add_position", "system_id": "s", "template": "FIXED", "location": window["location"],
            "dims": {"width_mm": window["width_mm"], "height_mm": window["height_mm"]},
            "quantity": window["quantity"], "glass_sku": "g", "color": "WHITE"}


def test_request_eval_set_with_the_agent_cases_reaches_thirty():
    agent_cases = yaml.safe_load((Path(evals.__file__).with_name("cases.yaml")).read_text(encoding="utf-8"))["cases"]
    assert len(CASES) + len(agent_cases) >= 30


def test_recorded_requests_accept_correct_windows_and_never_invented_measures():
    correct = expected = invented = 0
    for case in CASES:
        kept, cited, refused = origins.bind([_op(window) for window in case["proposed"]], [case["request"]])
        accepted = [op["location"] for op in kept]
        assert accepted == case["expected"], case["id"]
        assert [item["location"] for item in refused] == case["refused"], case["id"]
        expected += len(case["expected"])
        correct += sum(location in accepted for location in case["expected"])
        stated = origins.measures_mm(case["request"])
        invented += sum(Decimal(op["dims"][field]) not in stated for op in kept for field in ("width_mm", "height_mm"))
        assert all(case["request"][item["start"]:item["end"]] == item["quote"] for item in cited), case["id"]
    assert correct / expected >= 0.9
    assert invented == 0
