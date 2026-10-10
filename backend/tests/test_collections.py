from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from rest_framework.exceptions import APIException

from documents.legal import INTERNAL_LEGEND
from documents.renderers import _invoice_body, _credit_note_body, _receipt_body
from projects import collection_settings, fiscal_adapter, collection_reminders, invoices, payment_links
from projects import payments, simulated_flow


@contextmanager
def noop():
    yield


def payload():
    return {"invoice_code": "FAC-0001", "credit_code": "NC-0001", "document_kind": "FACTURA",
        "receipt_code": "RC-0001", "issued_at": "2026-10-10T15:00:00Z", "revision_code": "REV-A", "bom_hash": "a" * 64,
        "organization": {"name": "Taller Demo", "tax_id": "1-9", "giro": "Ventanas", "brand_address": "Taller Norte"},
        "project": {"code": "P-000001", "name": "Casa", "client_name": "Cliente Demo", "client_rut": "1-9", "client_address": "Obra Norte", "currency": "CLP"},
        "deal": {"total_net": "1000", "total_tax": "190", "total_gross": "1190", "currency": "CLP"},
        "balance": {"collected": "595", "amount_due": "595", "deal_total": "1190", "remaining": "595"},
        "invoice": {"invoice_code": "FAC-0001", "issued_at": "2026-10-10"},
        "positions": [{"position_index": 1, "typology": "FIXED", "quantity": 2, "width_mm": "1000", "height_mm": "1200", "price_net": "1000", "discount_pct": "0.2"}],
        "pricing": {"result": {"line_detail": [{"position_index": 1, "unit_price": "625"}]}},
        "payment": {"kind": "ANTICIPO", "method": "OTHER", "amount": "595", "recorded_at": "2026-10-10", "simulated": True, "actor_label": "Simulador Flow"}}


def test_internal_invoice_and_boleta_use_exact_legend_human_lines_discount_and_tax():
    data = payload()
    for kind, title in [("FACTURA", "Factura interna"), ("BOLETA", "Boleta interna")]:
        data["document_kind"] = kind
        html = _invoice_body(data)
        assert INTERNAL_LEGEND in html and title in html
        assert "Unitario neto" in html and "$500" in html and "$1.000" in html
        assert "Fijo" in html and "FIXED" not in html
        assert "Descuento" in html and "$250" in html
        assert "IVA 19 %" in html and "$190" in html
        assert "aaaaaaaaaaaa" in html and "Taller Norte" in html and "Obra Norte" in html
        assert "TED" not in html and "Timbre" not in html


def test_rounding_explains_sealed_total_without_adding_a_second_adjustment_line():
    data = payload()
    data["positions"][0].update(price_net="1001", discount_pct="0")
    data["deal"].update(total_net="1001", total_tax="190", total_gross="1191")
    data["balance"]["includes_simulation"] = True
    html = _invoice_body(data)
    assert "cantidad × unitario + ajuste de moneda" in html and "$−1" in html
    assert "El cobrado y saldo incluyen pagos simulados." in html
    assert "Ajuste de redondeo incluido en el neto</td>" not in html


def test_credit_note_keeps_reference_and_partial_credit_exact():
    data = {**payload(), "credit_amount_gross": "357", "credit_partial": True}
    html = _credit_note_body(data)
    assert INTERNAL_LEGEND in html and "Abono parcial" in html
    assert "$300" in html and "$57" in html and "$357" in html and "$833" in html


def test_simulated_receipt_declares_provenance_and_date():
    html = _receipt_body(payload())
    assert "Pago simulado — no se movió dinero" in html and "Simulador Flow" in html
    assert "10-10-2026" in html


def test_readiness_excludes_secrets_and_requires_certificate_and_certification(monkeypatch):
    monkeypatch.setattr(collection_settings, "documentary_backend", noop)
    monkeypatch.setattr(collection_settings, "preferences", lambda _: {**collection_settings.DEFAULTS, "sii_active": True, "sii_certified": True})
    monkeypatch.setattr(collection_settings, "rows", lambda sql, _: [{"id": uuid4()}] if "sii_certificates" in sql else [])
    monkeypatch.setenv("SII_WS_ENVIO_URL", "https://palena.sii.cl/cgi_dte/UPL/DTEUpload")
    monkeypatch.setenv("SII_WS_TOKEN", "server-only-test-value")
    output = collection_settings.status(uuid4())
    assert output["sii_connected"] is True and output["flow_connected"] is False
    assert "server-only-test-value" not in str(output)
    monkeypatch.delenv("SII_WS_TOKEN")
    assert collection_settings.status(uuid4())["sii_connected"] is False


def test_simulator_disabled_cannot_generate_fiscal_evidence(monkeypatch):
    monkeypatch.setattr(fiscal_adapter, "preferences", lambda _: {"simulation_enabled": False})
    with pytest.raises(APIException) as error:
        fiscal_adapter.simulate(org_id=uuid4(), project_id=uuid4(), actor_id=uuid4(), actor_label="Owner", data={})
    assert error.value.contract_code == "collection_simulation_disabled"


def test_ai_never_supplies_amounts_dates_or_unsupported_placeholders():
    values = {"cliente": "Cliente", "proyecto": "Casa", "monto": "$595", "vencimiento": "01-10-2026"}
    template = "{cliente}: Su pago de {proyecto} por {monto}, vencido el {vencimiento}, está pendiente. Revise su estado."
    assert collection_reminders.bind_template(template, values) == template.format(**values)
    for invalid in [template + " Total 999", template.replace("{monto}", "$595"), template + " {otro}", template + " 19 %"]:
        with pytest.raises(ValueError):
            collection_reminders.bind_template(invalid, values)


def test_document_kind_validated_at_service_before_sql():
    with pytest.raises(APIException):
        invoices.issue_invoice(org_id=uuid4(), actor_id=uuid4(), project={}, document_kind="DTE")


def test_payment_link_expiry_is_explicit_without_altering_paid_history():
    row = {"id": uuid4(), "operation_key": "abc", "kind": "SALDO", "amount": Decimal("500"), "payer_email": "test@example.test",
        "subject": "Prueba", "status": "PENDING", "environment": "simulated", "expires_at": datetime.now(timezone.utc)-timedelta(days=1),
        "url": None, "project_payment_id": None, "created_at": "2026-10-01", "updated_at": "2026-10-01"}
    assert payment_links._public_link(row)["status"] == "EXPIRED"
    row["status"] = "PAID"
    assert payment_links._public_link(row)["status"] == "PAID"


@pytest.mark.parametrize("token", ["wrong", "inválido", "\ud800", "", None])
def test_invalid_payer_capability_is_unavailable_without_reading_project(monkeypatch, token):
    monkeypatch.setattr(simulated_flow, "provider_scope", noop)
    monkeypatch.setattr(simulated_flow, "rows", lambda *a: [{"flow_token": "test-only-capability"}])
    with pytest.raises(APIException) as error:
        simulated_flow._capability(uuid4(), token)
    assert error.value.status_code == 404
    assert error.value.contract_code == "payment_link_not_found"


def test_event_dates_follow_santiago_and_require_complete_delivery(monkeypatch):
    monkeypatch.setattr(payments, "documentary_backend", noop)
    trips = [{"unit_indexes": [1], "created_at": datetime(2026, 10, 10, 2, tzinfo=timezone.utc)}]
    def observed(sql, params):
        if "customer_approvals" in sql:
            assert "project_version_id=%s" in sql and params[-1] == "version"
            return [{"decided_at": datetime(2026, 10, 10, 2, tzinfo=timezone.utc)}]
        if "FROM public.orders" in sql:
            return [{"id": "order", "payload_json": {"quantity": 2}}]
        if "FROM public.deliveries" in sql:
            return trips
        raise AssertionError(sql)
    monkeypatch.setattr(payments, "rows", observed)
    deal = {"total": Decimal("1190"), "currency": "CLP", "version_id": "version",
        "commercial_terms": {"payment_schedule": [{"label": "Anticipo", "share": "0.5", "due_event": "APPROVAL"},
                                                   {"label": "Saldo", "share": "0.5", "due_event": "DELIVERY"}]}}
    def projection():
        return payments.collection_projection(org_id=uuid4(), project_id=uuid4(), deal=deal, payments=[], today=date(2026, 10, 10))
    incomplete = projection()
    assert incomplete.milestones[0].due_on == date(2026, 10, 9)
    assert incomplete.milestones[1].due_on is None
    trips.append({"unit_indexes": [2], "created_at": datetime(2026, 10, 10, 4, tzinfo=timezone.utc)})
    assert projection().milestones[1].due_on == date(2026, 10, 10)


def test_stale_collection_reminder_cannot_queue_a_send(monkeypatch):
    monkeypatch.setattr(collection_reminders, "documentary_backend", noop)
    monkeypatch.setattr(collection_reminders, "mail_backend", noop)
    monkeypatch.setattr(collection_reminders.transaction, "atomic", noop)
    monkeypatch.setattr(collection_reminders, "project_row", lambda *a, **k: {})
    monkeypatch.setattr(collection_reminders, "one", lambda *a: {"source_hash": "old"})
    monkeypatch.setattr(collection_reminders, "rows", lambda *a: [])
    monkeypatch.setattr(collection_reminders, "source", lambda **k: {"source_hash": "current"})
    queued = []
    monkeypatch.setattr(collection_reminders, "seal_mail", lambda **k: queued.append(k))
    with pytest.raises(APIException) as error:
        collection_reminders.send(org_id=uuid4(), project_id=uuid4(), actor_id=uuid4(),
            data={"reminder_id": uuid4(), "confirmed": True})
    assert error.value.contract_code == "collection_reminder_stale" and queued == []


def test_collection_smtp_preflight_rejects_payment_changed_after_click(monkeypatch):
    from notifications import service
    row = {"id": uuid4(), "org_id": uuid4(), "project_id": uuid4(), "kind": "COLLECTION", "state": "QUEUED",
           "content_ciphertext": "opaque", "recipient": "client@example.test"}
    monkeypatch.setattr(service.transaction, "atomic", noop)
    monkeypatch.setattr(service, "mail_backend", noop)
    monkeypatch.setattr(service, "one", lambda sql, *a: {"source_hash": "old"} if "collection_reminders" in sql else row)
    monkeypatch.setattr(service, "_log", lambda *a, **k: None)
    monkeypatch.setattr(service.crypto, "open_message", lambda *a, **k: {"collection_reminder_id": str(uuid4())})
    monkeypatch.setattr(collection_reminders, "source", lambda **k: {"source_hash": "changed"})
    monkeypatch.setattr(service, "_finish", lambda row, state, error=None: {"state": state})
    delivery = []
    monkeypatch.setattr(service.adapters, "deliver", lambda *a, **k: delivery.append(k))
    assert service.dispatch(org_id=row["org_id"], mail_id=row["id"]) == {"state": "FAILED"}
    assert delivery == []
