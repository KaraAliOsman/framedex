"""Physical print contracts: density, addresses, fonts, exactness and Unicode."""

from copy import deepcopy
import csv
from decimal import Decimal
from io import StringIO
from math import ceil
import json
import re
import subprocess
import sys
from urllib.parse import parse_qs, urlsplit

import pytest
from weasyprint import HTML

from backend.tests.test_physical_piece_addresses import twelve_positions
from backend.tests.test_quote_document_v2 import fitz as pymupdf
from documents.renderers import _url_fetcher
from production.cut_documents import compact_bar_svg, pack_html
from production.cut_labels import labels_html
from production.cut_manifest import grouped_cuts, ordered_pieces
from production.dxf import dxf_files
from production.pieces import addressed_plan, physical_labels
from production.service import _cnc_bars_csv, _cnc_sheets_csv, _optimization_fingerprint


def revision(count):
    snapshot, combined = twelve_positions()
    snapshot["positions"] = snapshot["positions"][:1]
    snapshot["manufacturing"] = snapshot["manufacturing"][:2]
    combined["bars"]["workshop_cut_plan"] = combined["bars"]["workshop_cut_plan"][:2]
    combined["sheets"] = combined["sheets"][:1]
    for fact in snapshot["manufacturing"]:
        for infill in fact["infills"]:
            infill.update(kind="GLASS", rect={"width_mm":"960.00", "height_mm":"960.00"},
                          composition="4/12/4", technical_sku="GLASS-BASE")
    source = deepcopy(snapshot)
    plans = []
    snapshot = {"positions": [], "manufacturing": []}
    for index in range(1, count + 1):
        pid = f"position-{index}"
        # Domain release creates one OT per position. The complete revision
        # stays in scope so the 100th order preserves global P100 addresses.
        fact = deepcopy(source)
        fact["positions"][0].update(id=pid, position_index=index)
        remap = {}
        for unit in fact["manufacturing"]:
            unit.update(position_id=pid, position_index=index)
            for member in unit["members"]:
                remap[member["member_id"]] = f"{index}-{member['member_id']}"
                member["member_id"] = remap[member["member_id"]]
                member["identity"]["position_id"] = pid
            for reinf in unit["reinforcements"]:
                reinf["parent_member_id"] = remap[reinf["parent_member_id"]]
                reinf["reinforcement_id"] = f"{index}-{reinf['reinforcement_id']}"
            for infill in unit["infills"]:
                infill["infill_id"] = f"{index}-{infill['infill_id']}"
                infill["position_id"] = pid
        snapshot["positions"].extend(fact["positions"])
        snapshot["manufacturing"].extend(fact["manufacturing"])
        plan = deepcopy(combined)
        plan["color"] = "WHITE"
        for piece in ordered_pieces(plan):
            piece["source_position_id"] = pid
        plans.append(plan)
    return snapshot, plans


def render(source):
    return HTML(string=source, url_fetcher=_url_fetcher).render()


def parse_dxf(source):
    # Keep the native parsers isolated and parse the actual DXF under the
    # same warnings-as-errors policy as the repository.
    command = """import sys,json,ezdxf
doc=ezdxf.read(sys.stdin)
print(json.dumps({'version':doc.dxfversion,'units':doc.units,
    'texts':[entity.dxf.text for entity in doc.modelspace().query('TEXT')],
    'line_x':[entity.dxf.start.x for entity in doc.modelspace().query('LINE')]}))
"""
    result = subprocess.run([sys.executable, "-W", "error", "-c", command],
                            input=source, text=True, capture_output=True, check=True)
    return json.loads(result.stdout)


def assert_print_text(page):
    spans = [span for block in page.get_text("dict")["blocks"] if "lines" in block
             for line in block["lines"] for span in line["spans"] if span["text"].strip()]
    assert spans and all(span["size"] >= 7.999 for span in spans)
    for index, left in enumerate(spans):
        rect = pymupdf.Rect(left["bbox"])
        assert rect.x0 >= -0.1 and rect.x1 <= page.rect.width + 0.1
        assert rect.y0 >= -0.1 and rect.y1 <= page.rect.height + 0.1
        for right in spans[index + 1:]:
            overlap = rect & pymupdf.Rect(right["bbox"])
            assert overlap.is_empty or overlap.width < 0.2 or overlap.height < 0.2, (left["text"], right["text"])


@pytest.mark.parametrize("positions", [1, 12, 100])
def test_revision_orders_print_with_density_and_exact_closure(positions):
    snapshot, plans = revision(positions)
    assert len(plans) == positions
    for index, plan in enumerate(plans, 1):
        original = deepcopy(plan)
        display = addressed_plan(snapshot, plan, order_id=f"order-{index}")
        bars = display["bars"]["workshop_cut_plan"]
        html = pack_html(order={"id":f"order-{index}", "order_code":f"OT-{index:06}",
                        "payload":{"position_id":f"position-{index}"}},
                        optimization=display, snapshot=snapshot, fingerprint=_optimization_fingerprint(plan))
        assert html.count("cierra exacto") == len(bars)
        assert "diferencia sin asignar" not in html
        doc = render(html)
        # Two fixed sections: parent relations and scoped glazing/nesting.
        assert len(doc.pages) <= ceil(len(bars) / 3) + 2
        pdf = pymupdf.open(stream=doc.write_pdf(), filetype="pdf")
        for page in pdf:
            assert_print_text(page)
            assert f"OT-{index:06}" in page.get_text()
        text = "\n".join(page.get_text() for page in pdf)
        assert f"P{index:02}-U01-I01" in text
        assert "960" in text and "4/12/4" in text
        assert plan == original
        for bar in bars:
            assert Decimal(bar["stock_length_mm"]) == (
                sum((Decimal(cut["length_mm"]) for cut in bar["cuts"]), Decimal(0))
                + Decimal(bar["kerf_total_mm"]) + Decimal(bar["head_trim_mm"])
                + Decimal(bar["tail_trim_mm"]) + Decimal(bar["remainder_mm"]))


def test_every_artifact_keeps_the_same_physical_sequence_and_qr():
    snapshot, plans = revision(1)
    display = addressed_plan(snapshot, plans[0], order_id="order-1")
    ordered = [piece["piece_code"] for piece in ordered_pieces(display)]
    labels = physical_labels(display, snapshot=snapshot, order_code="OT-000001",
                             fingerprint="a" * 64, next_station="Soldadura")
    assert [label["code"] for label in labels] == ordered
    csv_codes = [row["piece_label"] for csv_text in (_cnc_bars_csv(display), _cnc_sheets_csv(display))
                 for row in csv.DictReader(StringIO(csv_text))]
    assert csv_codes == ordered
    files = dxf_files(display)
    dxf_codes = []
    for name in ["bars.dxf", *sorted(name for name in files if name != "bars.dxf")]:
        document = parse_dxf(files[name])
        dxf_codes.extend(text.split(" ")[0] for text in document["texts"] if text.split(" ")[0] in ordered)
    assert dxf_codes == ordered
    source = pack_html(order={"order_code":"OT-000001", "id":"order-1"},
                       optimization=display, snapshot=snapshot, fingerprint="a" * 64)
    doc = render(source)
    # Read actual laid-out cells, rather than codes from the HTML alone.
    cut_codes = []
    sheet_codes = []
    for page in doc.pages:
        for box in page._page_box.descendants():
            if type(box).__name__ != "TableCellBox" or box.element is None:
                continue
            value = "".join(box.element.itertext())
            if value in ordered:
                if box.element.get("class") == "technical-label":
                    # Parent-relation and glazing rosters repeat addresses;
                    # keep the first physical ledger appearance per address.
                    if value.endswith("I01"):
                        sheet_codes.append(value)
                    elif value not in cut_codes:
                        cut_codes.append(value)
    assert cut_codes == ordered[:len(cut_codes)]
    assert list(dict.fromkeys(sheet_codes)) == ordered[len(cut_codes):]
    for paper in ("LETTER", "A4", "ROLL_100_50"):
        doc = render(labels_html({"labels":labels, "paper":paper, "is_demo":True}))
        pdf = pymupdf.open(stream=doc.write_pdf(), filetype="pdf")
        codes = [match for page in pdf for match in re.findall(r"P\d+-U\d+-(?:M\d+(?:-R)?|I\d+)", page.get_text())]
        assert codes == ordered
        for page in pdf:
            assert_print_text(page)
            assert "DEMO" in page.get_text()
        if paper == "ROLL_100_50":
            assert len(pdf) == len(ordered)
            assert abs(pdf[0].rect.width - 100 * 72 / 25.4) < 0.02
            assert abs(pdf[0].rect.height - 50 * 72 / 25.4) < 0.02
    for label in labels:
        query = parse_qs(urlsplit(label["qr_payload"]).query)
        assert query["piece"] == [label["code"]]
        assert query["identity"] == [label["stable_id"]]


def test_dxf_unicode_and_submillimetre_geometry_are_not_rounded():
    snapshot, plans = revision(1)
    display = addressed_plan(snapshot, plans[0], order_id="order-1")
    bar = display["bars"]["workshop_cut_plan"][0]
    bar["commercial_sku"] = "PERFIL-Ñ"
    cut = bar["cuts"][0]
    cut.update(role="GLAZING_BEAD", workshop_sku="JUNQUILLO-Ñ", length_mm="1000.000123")
    source = dxf_files(display)["bars.dxf"]
    doc = parse_dxf(source)
    assert doc["version"] == "AC1021" and doc["units"] == 4
    assert any("Junquillo" in text and "Ñ" in text for text in doc["texts"])
    assert "1015.000123" in source
    assert any(abs(value - 1015.000123) < 1e-9 for value in doc["line_x"])


def test_grouping_never_merges_unequal_settings_or_loses_addresses():
    snapshot, plans = revision(1)
    display = addressed_plan(snapshot, plans[0], order_id="order-1")
    bars = display["bars"]["workshop_cut_plan"]
    for key, value in (("length_mm","1000.01"), ("angle_left","44.99"), ("angle_right","45.01")):
        altered = deepcopy(display)
        altered["bars"]["workshop_cut_plan"][0]["cuts"][1][key] = value
        assert len(grouped_cuts(altered)) == len(grouped_cuts(display)) + 1
    other = deepcopy(bars[0])
    other.update(bar_index=3, color="BLACK")
    for cut in other["cuts"]:
        cut["piece_code"] += "-B"
        cut["piece_stable_id"] += "-B"
    display["bars"]["workshop_cut_plan"].append(other)
    groups = grouped_cuts(display)
    assert len(groups) == 3
    assert sum(group["quantity"] for group in groups) == sum(len(bar["cuts"]) for bar in display["bars"]["workshop_cut_plan"])
    assert len({piece["stable_id"] for group in groups for piece in group["pieces"]}) == 10


def test_narrow_cut_callouts_keep_real_print_size_and_distinct_lanes():
    import xml.etree.ElementTree as ET
    bar = {"stock_length_mm":"6000", "head_trim_mm":"15", "kerf_mm":"5",
           "cuts":[{"sequence":index, "length_mm":"5", "piece_code":f"P01-U01-M{index:02}"}
                   for index in range(1, 61)]}
    tree = ET.fromstring(compact_bar_svg(bar))
    texts = tree.findall("{http://www.w3.org/2000/svg}text")
    assert len(texts) == 60 and all(Decimal(text.attrib["font-size"]) >= Decimal("2.823") for text in texts)
    assert len({(text.attrib["x"],text.attrib["y"]) for text in texts}) == 60


def test_next_station_uses_the_real_material_route_and_does_not_guess():
    from production.cut_manifest import next_piece_station
    route = [{"code":"CUT","label":"Corte"}, {"code":"CUT_STEEL","label":"Corte de acero"},
             {"code":"WELD","label":"Soldadura"}, {"code":"GLAZE","label":"Acristalado"}]
    assert next_piece_station({"role":"FRAME"}, route) == "Soldadura"
    assert next_piece_station({"source_kind":"REINFORCEMENT"}, route) == "Soldadura"
    assert next_piece_station({"role":"GLAZING_BEAD"}, route) == "Acristalado"
    assert next_piece_station({"width_mm":"810"}, route) == "Acristalado"
    assert "Sin dato" in next_piece_station({"role":"GLAZING_BEAD"}, route[:-1])
    assert "Sin dato" in next_piece_station({"role":"FRAME"}, [])
