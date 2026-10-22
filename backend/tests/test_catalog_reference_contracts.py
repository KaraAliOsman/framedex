"""Technical drafts cannot accept client-computed output or shared price data."""

from decimal import Decimal

import pytest

from catalogs.reference_serializers import SetupProgressInputSerializer, TrialInputSerializer, TrialVerificationSerializer


def trial_data():
    return {"nominal_width_mm": "1200", "nominal_height_mm": "1100", "color": "WHITE",
        "parametric_tree": {"id": "trial", "type": "BAY", "opening_type": "TURN_LEFT"}}


@pytest.mark.parametrize("value", [1200, "NaN", "Infinity", "-1", "0", "1200.001"])
def test_dimensions_require_positive_exact_decimal_strings(value):
    serializer = TrialInputSerializer(data={**trial_data(), "nominal_width_mm": value})
    assert not serializer.is_valid()


def test_manual_dimensions_are_parsed_in_python_and_client_output_is_rejected():
    serializer = TrialInputSerializer(data={**trial_data(), "manual_values": {"profile_cuts:0:length_mm": "1206.01"}})
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["manual_values"]["profile_cuts:0:length_mm"] == Decimal("1206.01")
    serializer = TrialInputSerializer(data={**trial_data(), "expected_output": {"profile_cuts": []}})
    assert not serializer.is_valid()


def test_confirmation_requires_explicit_human_approval():
    for value in (False, None):
        serializer = TrialVerificationSerializer(data={**trial_data(), "confirmed": value,
            "revision": "revision", "calculation_token": "token"})
        assert not serializer.is_valid()


@pytest.mark.parametrize("state", [{"unit_cost": "1234"}, {"prices": []}, {"trial": {**trial_data(), "cost": "1234"}}])
def test_shared_setup_does_not_store_confidential_price_drafts(state):
    serializer = SetupProgressInputSerializer(data={"step": 3, "revision": 1, "state": state})
    assert not serializer.is_valid()


def test_setup_accepts_technical_trial_and_bounded_steps():
    serializer = SetupProgressInputSerializer(data={"step": 4, "revision": 1, "state": {"trial": trial_data()}})
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["state"]["trial"]["nominal_width_mm"] == Decimal("1200")
    for step in (0, 6):
        serializer = SetupProgressInputSerializer(data={"step": step, "revision": 1, "state": {}})
        assert not serializer.is_valid()
