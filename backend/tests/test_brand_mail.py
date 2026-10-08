"""White-label, contrast, MIME and capability encryption regressions."""

from io import BytesIO
from uuid import uuid4

from cryptography.exceptions import InvalidTag
import pytest

from backend.tests.test_documents_contract import revision_snapshot
from documents.renderers import _brand_block, _doc01, render_pdf_document
from notifications import adapters, crypto, templates
from notifications.serializers import MailSendSerializer, MailRecoverySerializer
from projects.brand_color import PAPER, TEAL, contrast, effective_color, snapshot_preferences


def test_mail_job_result_exposes_only_delivery_state(monkeypatch):
    from types import SimpleNamespace
    from notifications import handlers

    monkeypatch.setattr(
        handlers,
        "dispatch",
        lambda **kwargs: {"state": "SENT", "id": uuid4(), "recipient": "private@example.invalid"},
    )
    assert handlers.deliver_job(
        {"mail_id": uuid4()}, SimpleNamespace(org_id=uuid4()), lambda progress: None
    ) == {"state": "SENT"}


@pytest.mark.parametrize(
    "color", ["#FFFFFF", "#F5F7F6", "#CCCCCC", "url(javascript:bad)", "<script>"]
)
def test_color_fallback_is_aa_and_cannot_inject_css(color):
    effective, fallback = effective_color(color)
    assert fallback and effective == TEAL
    assert contrast(effective, PAPER) >= 4.5


@pytest.mark.parametrize("color", ["#075f5a", "#161c1f", "#733B20"])
def test_valid_issuer_color_is_preserved(color):
    assert effective_color(color) == (color.upper(), False)


def test_new_preferences_and_legacy_documents_have_distinct_behavior():
    org = {
        "name": "Fábrica Sur",
        "commercial_name": "Fábrica Sur",
        "brand_primary_color": "#FFFFFF",
    }
    preferences = snapshot_preferences(org)
    assert preferences["document_attribution"] is False
    assert preferences["portal_attribution"] is True
    assert preferences["brand_primary_color"] == TEAL
    legacy = _brand_block(org)
    assert "Generado con DEKOPEN" in legacy
    assert "DEKOPEN" not in _brand_block({**org, **preferences})
    assert "Emisor sin identificar" in _brand_block({"brand_schema": 1})
    assert "DEKOPEN" in _brand_block(None)
    assert _brand_block(org) == legacy


def test_customer_doc01_has_no_platform_brand_even_in_pdf():
    from pypdf import PdfReader

    snapshot = revision_snapshot()
    snapshot["organization"] = {
        "name": "Fábrica Sur",
        **snapshot_preferences({"brand_primary_color": "#733B20"}),
    }
    assert "DEKOPEN" not in _doc01(snapshot)
    content, _ = render_pdf_document("DOC-01", snapshot, pdf_identifier="p25-white-label")
    text = "\n".join(page.extract_text() for page in PdfReader(BytesIO(content)).pages)
    assert "Fábrica Sur" in text and "DEKOPEN" not in text


@pytest.mark.parametrize("kind", templates.KINDS)
def test_mail_clients_get_mime_html_text_and_correct_issuer(kind, settings):
    settings.MAIL_FROM_ADDRESS = "correo@example.invalid"
    message = templates.render(
        kind,
        organization={"name": "Fábrica Sur", "brand_primary_color": "#733B20"},
        reference="Referencia sellada",
        body="Texto <seguro> para revisar.",
    )
    internal = kind in {"MAGIC_LINK", "APPROVAL", "ORDER_BLOCKED"}
    for part in ("html", "text", "subject", "from_name"):
        assert ("DEKOPEN" in message[part]) == internal
    assert "<seguro>" not in message["html"]
    mime = adapters.mime_message(message, mail_id=uuid4(), recipient="cliente@example.invalid")
    assert mime.get_body(preferencelist=("html",)).get_content_type() == "text/html"
    assert mime.get_body(preferencelist=("plain",)).get_content_type() == "text/plain"
    images = [part for part in mime.walk() if part.get_content_maintype() == "image"]
    assert len(images) == int(internal)
    if internal:
        assert images[0]["Content-ID"] == "<issuer>"
        assert images[0].get_payload(decode=True).startswith(b"\x89PNG")


def test_portal_capability_is_encrypted_and_bound_to_tenant_row(settings):
    settings.MAIL_ENCRYPTION_KEY = "stable-unit-key"
    org_id, mail_id = uuid4(), uuid4()
    original = {
        "html": '<a href="https://quote.example.invalid/cotizacion/secret-token">Revisar</a>'
    }
    sealed = crypto.seal(original, org_id=org_id, mail_id=mail_id)
    assert "secret-token" not in sealed
    assert crypto.open_message(sealed, org_id=org_id, mail_id=mail_id) == original
    with pytest.raises(InvalidTag):
        crypto.open_message(sealed, org_id=uuid4(), mail_id=mail_id)
    with pytest.raises(InvalidTag):
        crypto.open_message(sealed, org_id=org_id, mail_id=uuid4())


def test_customer_send_and_uncertain_recovery_require_explicit_click():
    data = {"expected_source_id": str(uuid4()), "expected_recipient": "cliente@example.invalid"}
    assert not MailSendSerializer(data=data).is_valid()
    assert not MailSendSerializer(data={**data, "confirmed": False}).is_valid()
    assert MailSendSerializer(data={**data, "confirmed": True}).is_valid()
    assert not MailRecoverySerializer(
        data={"expected_attempt": 1, "confirmed_remote_absence": False}
    ).is_valid()
    assert MailRecoverySerializer(
        data={"expected_attempt": 1, "confirmed_remote_absence": True}
    ).is_valid()
