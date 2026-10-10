from copy import deepcopy
from datetime import date

import pytest

from documents.issuance import _requirements
from documents.preferences import document_preferences
from documents.service import _prepared_valid_until
from documents.repository import DocumentaryError
from projects.rut import valid_rut


def test_new_validity_uses_declared_org_default_and_preserves_history(monkeypatch):
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    from uuid import uuid4

    monkeypatch.setattr("documents.service.one", lambda *args: {"document_preferences": {"quotation_valid_days": 23}})
    today = datetime.now(ZoneInfo("America/Santiago")).date()
    assert _prepared_valid_until({}, uuid4()) == today + timedelta(days=23)
    assert _prepared_valid_until({"quotation_valid_until": date(2026, 1, 1)}, uuid4()) == date(2026, 1, 1)
    assert _prepared_valid_until({"payment_terms": "Historical text"}, uuid4()) is None
    assert document_preferences({})["quotation_valid_days"] == 15
    assert document_preferences({})["quotation_preview_minutes"] == 30


@pytest.mark.parametrize(
    "value", ["12.345.678-5", "123456785", " 12 345 678-5 ", "11.111.111-1", "6.000.000-K"]
)
def test_rut_module_eleven_accepts_declared_identity(value):
    assert valid_rut(value)


@pytest.mark.parametrize(
    "value", [None, "", "12.345.678-4", "00000000-0", "1-9", "12345678-X", "1234<script>5"]
)
def test_rut_module_eleven_rejects_invalid_identity(value):
    assert not valid_rut(value)


def complete():
    return {
        "project": {
            "client_name": "Cliente",
            "client_rut": "12345678-5",
            "client_email": "cliente@example.test",
            "delivery_address": "Obra Norte",
            "quotation_valid_until": date(2999, 1, 1),
            "payment_terms": "Por hitos",
            "total_price_gross": "1435471",
            "currency": "CLP",
            "commercial_terms": {
                "payment_schedule": [
                    {"label": "Al aprobar", "share": "0.5"},
                    {"label": "Entrega", "share": "0.5"},
                ],
                "delivery_text": "20 días",
                "installation_text": "Incluida",
                "exclusions": "Pintura",
                "warranty": "12 meses",
            },
        }
    }


def test_complete_quote_is_validated_without_changing_its_engine_numbers():
    snapshot = complete()
    before = deepcopy(snapshot)
    _requirements(snapshot)
    assert snapshot == before


@pytest.mark.parametrize(
    "field",
    [
        "client_name",
        "client_rut",
        "client_email",
        "delivery_address",
        "quotation_valid_until",
        "payment_terms",
        "payment_schedule",
        "delivery_text",
        "installation_text",
        "exclusions",
        "warranty",
    ],
)
def test_missing_quote_field_has_precise_actionable_target(field):
    snapshot = complete()
    target = (
        snapshot["project"]["commercial_terms"]
        if field in snapshot["project"]["commercial_terms"]
        else snapshot["project"]
    )
    target[field] = [] if field == "payment_schedule" else ""
    with pytest.raises(DocumentaryError) as error:
        _requirements(snapshot)
    assert error.value.code == "quotation_fields_required"
    expected = "payment_schedule" if field == "payment_terms" else field
    assert expected in {item["field"] for item in error.value.extra["missing_fields"]}
