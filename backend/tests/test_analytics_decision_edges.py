"""Pure HTTP-edge validation; calculations are exercised in SQL/golden tests."""

from decimal import Decimal
import pytest
from analytics.decision_serializers import (
    ActualReportRequestSerializer,
    AnalyticsPreferenceSerializer,
)
from analytics.decision_views import csv_cell


@pytest.mark.parametrize("text", ["=SUM(A1:A2)", "+formula", "-formula", "@SUM(1)", "\t=1"])
def test_textual_csv_formulas_are_neutralized(text):
    assert csv_cell(text) == "'" + text


@pytest.mark.parametrize("text", ["-40.0", "0", "42.001", None])
def test_exact_numeric_csv_values_keep_their_sign(text):
    assert csv_cell(text) == ("" if text is None else text)


def test_period_preference_has_explicit_bounds():
    for days in (0, 367, "unknown"):
        assert not AnalyticsPreferenceSerializer(data={"period_days": days}).is_valid()


def test_float_money_cannot_lose_digits_after_serializer_validation():
    field = ActualReportRequestSerializer().fields["other_cost"]
    assert field.run_validation("12345678901234567890.12345678") == Decimal(
        "12345678901234567890.12345678"
    )
    with pytest.raises(Exception):
        field.run_validation("-0.01")
