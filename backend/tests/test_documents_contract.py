from io import BytesIO

from openpyxl import load_workbook
import pytest

from dekopen_engine.documentary_canonical import file_sha256
from documents.artifacts import _require_document_role
from documents.renderers import _doc01, _doc06, _doc07, render_pdf_document
from documents.repository import DocumentaryError
from documents.serializers import HandleIntentSerializer
from documents.storage import SIGNED_URL_TTL_SECONDS, SupabaseDocumentStorage
from documents.xlsx import render_order_xlsx


def revision_snapshot() -> dict[str, object]:
    return {
        "schema_version": 1,
        "canonical_version": "DOCUMENTARY_CANONICAL_V1",
        "revision": "REV-A",
        "sealed_at": "2026-09-14T12:00:00Z",
        "bom_hash": "a" * 64,
        "production_allowed": True,
        "documentary_complete": True,
        "project": {
            "code": "P-001",
            "client_name": "Cliente <Seguro>",
            "delivery_address": "Obra Norte",
            "currency": "CLP",
            "total_price_net": "100000",
            "total_price_tax": "19000",
            "total_price_gross": "119000",
            "payment_terms": "50% anticipo, 50% contra entrega",
            "quotation_valid_until": "2026-10-14",
            "notes_commercial": "Incluye instalación",
        },
        "positions": [{
            "position_index": 1,
            "location_tag": "FACHADA-NORTE",
            "width_mm": "1000.00",
            "height_mm": "1200.00",
            "quantity": 2,
            "color_interior": "WHITE",
            "color_exterior": "WHITE",
            "parametric_tree": {
                "id": "B1", "type": "BAY", "glass_spec": "4-12-4 Float Incoloro",
                "children": [],
            },
        }],
        "inspector": [{"config": {"R10": {"tolerance_mm": "1.50"}}}],
        "pricing": {
            "input_snapshot": {"cost_lines": [[1, "60000.00"]]},
            "applied_total_cost_net": "60000.00",
        },
        "realized_waste": {"status": "NOT_RECORDED", "value": None},
        "manufacturing": [],
        "purchase_requirements": {"stock_groups": []},
    }


def order_snapshot(order_type: str) -> dict[str, object]:
    glass = order_type == "SUPPLIER_GLASS_PO"
    return {
        "order": {
            "order_code": "PO-ABC123",
            "order_type": order_type,
            "supplier_name": "Proveedor Exacto",
            "project_code": "P-001",
            "confirmed_at": "2026-09-14T12:00:00Z",
        },
        "revision": {
            "revision_code": "REV-A",
            "bom_hash": "a" * 64,
            "snapshot_sha256": "b" * 64,
        },
        "lines": [{
            "requirement_key": "c" * 64,
            "category": "GLASS" if glass else "PROFILE",
            "technical_skus": ["TECH-01"],
            "purchasing_sku": "BUY-01",
            "physical_stock_identity": None if glass else "STOCK-01",
            "quantity": 2,
            "unit": "EA" if glass else "BAR",
            "source_trace": ["d" * 64, "e" * 64],
            "specification": ({
                "composition": "4-12-4 Float Incoloro",
                "oriented_width_mm": "876.00",
                "oriented_height_mm": "1076.00",
                "polishing": {"top": True, "right": False, "bottom": False, "left": True},
                "location_tag": "FACHADA-NORTE",
            } if glass else {
                "stock_length_mm": "5800.00",
                "cutting_profile_id": "CUT-PROLINE",
            }),
        }],
    }


def test_client_document_escapes_input_and_never_contains_raw_cost() -> None:
    html = _doc01(revision_snapshot())
    assert "Cliente &lt;Seguro&gt;" in html
    assert "60000.00" not in html
    assert "119000" in html


def test_qc_is_blank_and_cost_report_uses_frozen_not_recorded_authority() -> None:
    qc = _doc06(revision_snapshot())
    assert "Diferencia ≤ 1.50 mm" in qc
    assert "________________" in qc
    cost = _doc07(revision_snapshot())
    assert "60000.00" in cost
    assert "NO REGISTRADA" in cost
    assert "valor: —" in cost
    invalid = {**revision_snapshot(), "realized_waste": {"status": "RECORDED", "value": "0"}}
    with pytest.raises(DocumentaryError, match="realized_waste_authority_invalid"):
        _doc07(invalid)


def test_pdf_producer_emits_concrete_file_with_distinct_hash(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEASYPRINT_DLL_DIRECTORIES", "C:\\msys64\\ucrt64\\bin")
    content, media_type = render_pdf_document(
        "DOC-01", revision_snapshot(), pdf_identifier="b" * 64
    )
    assert content.startswith(b"%PDF-")
    assert media_type == "application/pdf"
    assert file_sha256(content) not in {"a" * 64, "b" * 64}


def test_xlsx_is_deterministic_exact_text_and_no_formula_authority() -> None:
    first, media_type = render_order_xlsx("DOC-02", order_snapshot("SUPPLIER_GLASS_PO"))
    second, _ = render_order_xlsx("DOC-02", order_snapshot("SUPPLIER_GLASS_PO"))
    assert first == second
    assert media_type.endswith("sheet")
    workbook = load_workbook(BytesIO(first), read_only=True, data_only=False)
    try:
        sheet = workbook["Pedido de vidrios"]
        assert sheet["E8"].value == "876.00"
        assert sheet["F8"].value == "1076.00"
        assert sheet["G8"].value == 2
        assert sheet["I8"].value == "TOP/LEFT"
        assert not any(
            isinstance(cell.value, str) and cell.value.startswith("=")
            for row in sheet.iter_rows() for cell in row
        )
    finally:
        workbook.close()
    profile, _ = render_order_xlsx("DOC-04", order_snapshot("SUPPLIER_PROFILE_PO"))
    profile_workbook = load_workbook(BytesIO(profile), read_only=True)
    try:
        assert profile_workbook["Pedido de perfiles"]["F8"].value == "5800.00"
    finally:
        profile_workbook.close()


def test_handle_transport_rejects_derived_manufacturing_fields() -> None:
    serializer = HandleIntentSerializer(data={
        "bay_id": "B1",
        "handle_domain_slot": "PRIMARY",
        "requested_height_mm": "1000.00",
        "vertical_reference": "OUTER_BOTTOM",
        "manufacturing_x_mm": "50.00",
    })
    assert not serializer.is_valid()


def test_document_role_matrix_keeps_doc07_owner_only() -> None:
    _require_document_role("DOC-07", "OWNER")
    for role in ("ESTIMATOR", "WORKSHOP_MANAGER", "INSTALLER"):
        with pytest.raises(DocumentaryError, match="document_access_denied"):
            _require_document_role("DOC-07", role)
    _require_document_role("DOC-02", "WORKSHOP_MANAGER")
    _require_document_role("DOC-01", "ESTIMATOR")


class FakeResponse:
    status_code = 200

    def json(self):
        return {"signedURL": "/storage/v1/object/sign/documents/key?token=transient"}


class FakeClient:
    request_json: dict[str, object] | None = None

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def post(self, url, **kwargs):
        FakeClient.request_json = kwargs.get("json")
        return FakeResponse()


def test_signed_url_uses_fixed_ttl_and_is_not_artifact_identity(
    settings, monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings.SUPABASE_URL = "http://127.0.0.1:25321"
    settings.SUPABASE_SERVICE_ROLE_KEY = "local-test-service-key"
    settings.SUPABASE_STORAGE_BUCKET_DOCS = "documents"
    monkeypatch.setattr("documents.storage.httpx.Client", FakeClient)
    signed = SupabaseDocumentStorage().signed_url("org_x/projects/p/rev/doc.pdf")
    assert FakeClient.request_json == {"expiresIn": SIGNED_URL_TTL_SECONDS}
    assert "token=transient" in signed
