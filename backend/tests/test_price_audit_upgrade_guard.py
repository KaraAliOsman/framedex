"""The upgrade gate accepts its new ordinal while detecting historical damage."""

from copy import deepcopy

import pytest

from scripts.check_advanced_opening_upgrade import assert_historical_rows


def records():
    before = {"price_audit_logs": [{"id": "old", "new_value": "1234.5678", "old_value": "0.0000",
        "reason": "Historical reason", "created_at": "2026-10-21T00:00:00Z", "actor_user_id": "actor",
        "new_record": {"unit_cost": "1234.5678"}}]}
    after = deepcopy(before)
    after["price_audit_logs"][0]["event_order"] = 42
    return before, after


def test_only_new_identity_metadata_may_be_added_to_an_old_event():
    before, after = records()
    assert_historical_rows(before, after)
    with pytest.raises(AssertionError):
        assert_historical_rows(after, before)


@pytest.mark.parametrize("field", ["new_value", "old_value", "reason", "created_at", "actor_user_id", "new_record"])
def test_every_original_audit_field_is_still_compared(field):
    before, after = records()
    after["price_audit_logs"][0][field] = "changed"
    with pytest.raises(AssertionError, match="rewrote historical price_audit_logs"):
        assert_historical_rows(before, after)


@pytest.mark.parametrize("ordinal", [None, 0, -1, "42", True])
def test_missing_or_invalid_ordinal_is_rejected(ordinal):
    before, after = records()
    after["price_audit_logs"][0]["event_order"] = ordinal
    with pytest.raises(AssertionError, match="Invalid price audit ordinal"):
        assert_historical_rows(before, after)


def test_missing_added_duplicate_and_preexisting_modified_events_are_rejected():
    before, after = records()
    with pytest.raises(AssertionError, match="audit rows changed"):
        assert_historical_rows(before, {"price_audit_logs": []})
    after["price_audit_logs"].append({**after["price_audit_logs"][0], "id": "extra"})
    with pytest.raises(AssertionError, match="audit rows changed"):
        assert_historical_rows(before, after)
    before["price_audit_logs"].append({**before["price_audit_logs"][0], "id": "extra"})
    with pytest.raises(AssertionError, match="ordinals must be distinct"):
        assert_historical_rows(before, after)
    before, after = records()
    before["price_audit_logs"][0]["event_order"] = 41
    with pytest.raises(AssertionError, match="rewrote historical"):
        assert_historical_rows(before, after)


def test_unknown_added_column_is_not_silently_ignored():
    before, after = records()
    after["price_audit_logs"][0]["unexpected"] = None
    with pytest.raises(AssertionError, match="rewrote historical"):
        assert_historical_rows(before, after)
