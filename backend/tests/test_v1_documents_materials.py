"""v1 06–08: quotation compositions, workshop layouts, materials/cut draft,
CNC adapter contract and the assistant's document_layout step."""

from datetime import datetime, timezone
from decimal import Decimal as D
import warnings

import pytest

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message=r"builtin type (SwigPyPacked|SwigPyObject|swigvarlink) has no __module__ attribute", category=DeprecationWarning)
    import fitz

from backend.tests.doc01_cases import proposal_case
from backend.tests.test_documents_contract import revision_snapshot
from dekopen_engine import BayOpeningType, NodeType, ParametricNode, calculate_geometry
from dekopen_engine.cutting import CutMaterial, CuttingProfile, MissingCuttingProfile, MissingStockAuthority, StockRule
from documents import quotation
from documents.renderers import render_pdf_document
from documents.repository import DocumentaryError
from engine.tests.catalog import demo_60_params
from engine.tests.test_purchasing import position_source, project_one
from engine.tests.test_shot06_core import core_node


def _text(pdf: bytes) -> str:
    with fitz.open(stream=pdf, filetype="pdf") as document:
        return " ".join(" ".join(page.get_text().split()) for page in document)


def _case(template: str | None = None, acceptance: str | None = None) -> dict:
    snapshot = proposal_case(3)
    prefs = snapshot["organization"]["document_preferences"]
    if template:
        prefs["quotation_template"] = template
    if acceptance:
        prefs["acceptance_mode"] = acceptance
    return snapshot


# ---------------------------------------------------------------- quotation


def test_legacy_snapshot_keeps_project_composition_and_signature():
    snapshot = _case()
    for key in ("quotation_template", "acceptance_mode", "quotation_layout"):
        snapshot["organization"]["document_preferences"].pop(key, None)
    layout = quotation.resolve_layout(snapshot)
    assert layout["template"] == "PROYECTO"
    assert layout["acceptance"] == "SIGNATURE"


def test_company_then_work_then_request_resolve_the_layout():
    snapshot = _case("ESENCIAL")
    snapshot["organization"]["document_preferences"]["quotation_layout"] = {"drawing_size": "L", "unit_prices": False}
    snapshot["project"]["document_layout"] = {"template": "PROYECTO", "hidden": ["terms", "positions"], "order": ["commercial"]}
    layout = quotation.resolve_layout(snapshot)
    assert layout["template"] == "PROYECTO"
    assert layout["drawing_size"] == "L" and layout["unit_prices"] is False
    # Windows and the commercial summary can never be hidden.
    assert layout["hidden"] == {"terms"}
    assert layout["order"][0] == "commercial"
    assert quotation.resolve_layout(snapshot, "ALTERNATIVAS")["template"] == "ALTERNATIVAS"


@pytest.mark.parametrize("template", ["ESENCIAL", "PROYECTO", "ALTERNATIVAS"])
def test_three_compositions_render_the_same_sealed_total_once_per_condition(template):
    snapshot = _case(template, "NONE")
    snapshot["project"]["commercial_label"] = "N.º 7"
    pdf, _ = render_pdf_document("DOC-01", snapshot, pdf_identifier="v1-layout", portal_url="https://example.test/c/token-abc")
    text = _text(pdf)
    assert "N.º 7" in text and "COT-P-000123" not in text
    # Conditions are printed once, not repeated in the header column.
    assert text.count("20 días hábiles desde la aprobación") == 1
    # Without an acceptance policy the link only lets the customer consult it.
    assert "Consulta en línea" in text and "Nombre y RUT" not in text
    assert "example.test" in text and "token-abc" not in text


def test_signature_policy_prints_signature_and_draft_never_does():
    snapshot = _case("ESENCIAL", "SIGNATURE")
    assert "Nombre y RUT" in _text(render_pdf_document("DOC-01", snapshot, pdf_identifier="sig")[0])
    snapshot["draft"] = True
    text = _text(render_pdf_document("DOC-01", snapshot, pdf_identifier="draft")[0])
    assert "Borrador" in text and "Nombre y RUT" not in text


def test_alternatives_compare_without_adding_to_the_total():
    snapshot = _case("ALTERNATIVAS")
    alternative = proposal_case(2)
    snapshot["alternatives"] = [{"revision": "REV-A", "project": alternative["project"], "positions": alternative["positions"]}]
    text = _text(render_pdf_document("DOC-01", snapshot, pdf_identifier="alt")[0])
    assert "Opciones para su obra" in text and "no se suman al total" in text


# ------------------------------------------------------------ workshop layouts


def _workshop_snapshot() -> dict:
    position, bindings = position_source(
        core_node("G6").model_copy(update={"glass_article_sku": "GLASS-TECH"}), demo_60_params(),
        position_id="11111111-1111-1111-1111-111111111111", position_index=1, quantity=2)
    snapshot = revision_snapshot()
    snapshot["purchase_requirements"] = project_one(position, bindings).model_dump(mode="json")
    return snapshot


@pytest.mark.parametrize("layout,title", [("COMPACTA", "Corte · lista compacta"), ("VENTANA", "Corte · por ventana"),
                                          ("OBRA", "Pedido por obra")])
def test_workshop_layouts_render_the_same_bars(layout, title):
    snapshot = _workshop_snapshot()
    text = _text(render_pdf_document("DOC-05", snapshot, pdf_identifier="w", layout=layout)[0])
    assert title in text
    bars = sum(int(group["purchased_bar_count"]) for group in snapshot["purchase_requirements"]["stock_groups"])
    if layout == "OBRA":
        assert f"Total de barras de la obra: {bars}" in text
        assert "No es una orden de compra" in text


def test_compact_list_counts_every_cut_once():
    snapshot = _workshop_snapshot()
    from documents.workshop_layouts import cut_compact
    html = cut_compact(snapshot)
    cuts = sum(len(bar["cuts"]) for group in snapshot["purchase_requirements"]["stock_groups"] for bar in group["bars"])
    counted = sum(int(cell) for cell in __import__("re").findall(r'<td class="num">(\d+)</td><td>[^<]*</td><td>', html))
    assert counted == cuts


def test_workshop_layouts_refuse_unreleased_revisions():
    snapshot = _workshop_snapshot()
    snapshot["production_allowed"] = False
    with pytest.raises(DocumentaryError):
        render_pdf_document("DOC-05", snapshot, pdf_identifier="w", layout="VENTANA")


# ------------------------------------------------------------ materials / cut


@pytest.fixture
def materials_env(monkeypatch):
    from projects import materials
    params = demo_60_params()
    positions = []
    for index, (kind, width, height, quantity) in enumerate([("FIXED", "1200", "1400", 2), ("TILT_TURN_LEFT", "1000", "1400", 1)], 1):
        node = ParametricNode(id=f"b{index}", type=NodeType.BAY, opening_type=BayOpeningType(kind), width_mm=D(width),
                              height_mm=D(height), glass_spec="4-16-4", glass_thickness_mm=D("24"))
        positions.append({"id": f"00000000-0000-4000-8000-00000000000{index}", "position_index": index,
                          "location_tag": f"Dormitorio {index}", "quantity": quantity,
                          "system_id": "11111111-1111-4111-8111-111111111111", "color_interior": "WHITE",
                          "result": calculate_geometry(node, params), "color": "WHITE",
                          "updated_at": datetime.now(timezone.utc)})
    monkeypatch.setattr(materials, "_positions", lambda org, project: positions)
    monkeypatch.setattr(materials, "_profile_names", lambda org, systems, skus: {})
    monkeypatch.setattr(materials, "_article_titles", lambda org, names, systems: {})
    monkeypatch.setattr(materials, "_freshness", lambda org, project, rows: {"latest_revision": None, "design_changed": False})
    state = {"missing_sku": None, "no_profile": False}

    class Repository:
        def profile_stock(self, system, org, sku, color):
            if sku == state["missing_sku"]:
                raise MissingStockAuthority("unknown length")
            return StockRule(stock_authority_id=f"S-{sku}", workshop_sku=sku, commercial_sku=f"BUY-{sku}", manufacturer_name="DEMO",
                             purchase_unit="BAR", material=CutMaterial.PVC, color=color, stock_length_mm=D("6000"))

        def reinforcement_stock(self, system, org, parent, requested, color):
            sku = requested or f"STEEL-{parent}"
            return StockRule(stock_authority_id=f"R-{sku}", workshop_sku=sku, commercial_sku=f"BUY-{sku}", manufacturer_name="DEMO",
                             purchase_unit="BAR", material=CutMaterial.STEEL, color=color, stock_length_mm=D("6000")), None

        def cutting_profile(self, org, code=None):
            if state["no_profile"]:
                raise MissingCuttingProfile
            return CuttingProfile(id="c", code="DEMO", kerf_mm=D("4"), head_trim_mm=D("15"), tail_trim_mm=D("15"))

    monkeypatch.setattr(materials, "CuttingRepository", Repository)
    # This fixture tests the cut plan over resolved synthetic engineering data;
    # catalog confirmation and verification are covered by live integrations.
    monkeypatch.setattr("catalogs.use_levels.series_use", lambda *_args, **_kwargs: {
        "levels": [{"level": "MANUFACTURABLE", "ok": True, "pending": []}]})
    return materials, positions, state


def test_consolidated_consumption_multiplies_each_window_quantity(materials_env):
    materials, positions, _ = materials_env
    listed = materials.project_materials("org", "project")
    expected = sum(cut.length_mm * cut.qty * position["quantity"] for position in positions for cut in position["result"].profile_cuts)
    total = sum(D(row["length_mm"]) for row in listed["consolidated"]["profiles"])
    assert total == expected
    glass = listed["consolidated"]["glass"][0]
    assert glass["unit"] == "m²" and glass["count"] == 3
    # Per-window lists are per unit; the consolidated list carries the windows.
    assert listed["windows"][0]["quantity"] == 2
    windows = {window for row in listed["consolidated"]["profiles"] for window in row["windows"]}
    assert windows == {"V1 · Dormitorio 1", "V2 · Dormitorio 2"}


def test_cut_draft_places_every_piece_of_every_unit(materials_env):
    materials, positions, _ = materials_env
    draft = materials.cut_draft("org", "project")
    assert draft["state"] == "READY" and draft["stock_source"] == "NEW_BARS"
    placed = sum(len(bar["cuts"]) for bar in draft["bars"])
    expected = sum(sum(cut.qty for cut in p["result"].profile_cuts) * p["quantity"] for p in positions) + \
        sum(sum(steel.qty for steel in p["result"].reinforcements) * p["quantity"] for p in positions)
    assert placed == expected and not draft["unplaced"]
    assert all(cut["window"].startswith("V") for bar in draft["bars"] for cut in bar["cuts"])
    assert sum(line["qty_bars"] for line in draft["purchase"]) == draft["metrics"]["purchased_bars"]


def test_cut_draft_reports_exact_missing_authorities_without_partial_plan(materials_env):
    materials, positions, state = materials_env
    sku = positions[1]["result"].profile_cuts[0].sku
    state.update(missing_sku=sku, no_profile=True)
    draft = materials.cut_draft("org", "project")
    assert draft["state"] == "MISSING" and "bars" not in draft
    causes = " ".join(item["cause"] for item in draft["missing"])
    assert sku in causes and "perfil de corte" in causes
    assert {item["path"] for item in draft["missing"]} >= {"/catalogs/systems", "/settings/general?section=production"}


# ---------------------------------------------------------------- CNC adapters


def test_cnc_adapter_contract_never_claims_homologation_without_evidence():
    from production import cnc_adapters
    assert cnc_adapters.level_label("neutral-ops-v1") == "Intercambio neutro"
    assert "sin implementar" in cnc_adapters.level_label("vendor-x")
    with pytest.raises(ValueError):
        cnc_adapters.AdapterContract("vendor-x", "X", "MACHINE_ADAPTER", "manual")
    with pytest.raises(ValueError):
        cnc_adapters.AdapterContract("vendor-x", "X", "HOMOLOGATED", "manual", ("sample.nc",))
    with pytest.raises(LookupError):
        cnc_adapters.processor("vendor-x")


# ------------------------------------------------------- assistant document step


def test_document_layout_step_validates_the_same_object_and_never_hides_windows():
    from ai_gateway.agent import _document_layout_step
    rejected: list = []
    refs = {"project_id": "00000000-0000-4000-8000-000000000001"}
    step = _document_layout_step({"kind": "document_layout", "layout": {"template": "PROYECTO", "drawing_size": "L"},
                                  "label": "Diseño para obra grande", "apply": True},
                                 refs=refs, context={"editable": True}, may_draft=True, rejected=rejected)
    assert step["layout"] == {"template": "PROYECTO", "drawing_size": "L"} and step["apply_requested"] is True
    assert _document_layout_step({"layout": {"hidden": ["positions"]}}, refs=refs, context={}, may_draft=True,
                                 rejected=rejected) is None
    assert _document_layout_step({"layout": {"template": "ESENCIAL"}, "apply": True}, refs=refs, context={},
                                 may_draft=False, rejected=rejected)["apply_requested"] is False
    assert _document_layout_step({"layout": {"template": "ESENCIAL"}}, refs={}, context={}, may_draft=True,
                                 rejected=rejected) is None
    assert [item["reason"] for item in rejected] == ["layout_invalid", "project_not_editable"]


def test_design_identity_ignores_transport_and_prices():
    from projects import materials
    sealed = {"id": "p1", "quantity": 1, "system_id": "s", "width_mm": D("1200.00"), "height_mm": "1400",
              "color_interior": "WHITE", "color_exterior": "WHITE", "parametric_tree": {"id": "root", "type": "BAY"},
              "price_net": "198000"}
    stored = {"id": "p1", "quantity": 1, "system_id": "s", "width_mm": "1200", "height_mm": D("1400.00"),
              "color_interior": "WHITE", "color_exterior": "WHITE", "parametric_tree": '{"type": "BAY", "id": "root"}',
              "price_net": "205000"}
    assert materials._design(sealed) == materials._design(stored)
    assert materials._design({**stored, "width_mm": "1201"}) != materials._design(sealed)
