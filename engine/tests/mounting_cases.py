from typing import Any
from dekopen_engine.mounting import MountingRule, OpeningSurvey, derive_fabrication


def mounting_cases() -> dict[str, Any]:
    results = {}
    for kind, clearance, frame, overlap in [
        ("IN_OPENING", "10", "0", "0"),
        ("SUBFRAME", "5", "20", "0"),
        ("OVERLAP", "0", "0", "25"),
        ("RENOVATION", "3", "15", "0"),
    ]:
        side = {"clearance_mm": clearance, "frame_mm": frame, "extension_mm": "0", "overlap_mm": overlap}
        rule = MountingRule.model_validate({"code": kind, "name": kind, "kind": kind,
            "source": "DEMO · ensayo de montaje sin certificación", "synthetic": True,
            "tolerance_mm": "3", **{name: side for name in ("left", "right", "top", "bottom")}, "extras": []})
        survey = OpeningSurvey.model_validate({"rule_code": kind, "rule_revision": 1,
            "widths_mm": ["1524", "1520", "1522"], "heights_mm": ["1220", "1221", "1222"],
            "wall": "CONCRETE", "origin": "SITE"})
        results[kind] = {"rule": rule.model_dump(mode="json"), "survey": survey.model_dump(mode="json"),
                         "result": derive_fabrication(survey, rule).model_dump(mode="json")}
    return results
