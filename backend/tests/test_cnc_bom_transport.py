"""Leaf fixtures bind identical numeric facts across historical transports."""

from copy import deepcopy
import json

from dekopen_engine.models import EngineResult
from dekopen_engine.snapshot import result_payload
from documents.service import _canonical_bom_transport, _same_documentary_value


def test_default_extra_overhang_transport_is_exact_and_real_drift_still_differs():
    raw = {
        "profile_cuts": [], "reinforcements": [], "glasses": [],
        "extra_suggestions": [{"name": "Mosquitero DEMO", "source": "Fixture",
            "cause": "Hoja móvil", "selection": {"code": "SCREEN_ROLL",
                "overhang_left_mm": "0", "overhang_right_mm": "0"}}],
    }
    canonical = result_payload(EngineResult.model_validate_json(json.dumps(raw)), exclude_unset=True)
    assert _same_documentary_value(_canonical_bom_transport(raw), canonical)
    changed = deepcopy(raw)
    changed["extra_suggestions"][0]["selection"]["overhang_left_mm"] = "0.01"
    assert not _same_documentary_value(_canonical_bom_transport(changed), canonical)
    changed = deepcopy(raw)
    changed["extra_suggestions"][0]["source"] = "A different authority"
    assert not _same_documentary_value(_canonical_bom_transport(changed), canonical)
    assert "panels" not in _canonical_bom_transport(raw)
    assert raw["extra_suggestions"][0]["selection"]["overhang_left_mm"] == "0"
