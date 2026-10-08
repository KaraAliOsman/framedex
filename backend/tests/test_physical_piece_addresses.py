"""One set of physical codes across 12-position web, PDF, CSV, DXF and QR."""

from copy import deepcopy
import csv
from io import StringIO
import re
from urllib.parse import parse_qs, urlsplit

from backend.tests.test_production import _cutpack_snapshot, _cutpack_optimization
from documents.renderers import _cut_member_map, _piece_labels
from production.cut_pack import _pack_html
from production.dxf import dxf_files
from production.pieces import addressed_plan, physical_labels, without_addresses
from production.service import _cnc_bars_csv, _cnc_sheets_csv, _optimization_fingerprint
from production.trace import _plan_bars, _plan_sheets


def twelve_positions():
    snapshot = {"positions": [], "manufacturing": []}
    plan = {"bars": {"workshop_cut_plan": [], "metrics": {}}, "sheets": []}
    for index in range(1, 13):
        source = _cutpack_snapshot()
        optimized = _cutpack_optimization()
        pid = f"position-{index}"
        snapshot["positions"].append({"id": pid, "position_index": index})
        for fact in source["manufacturing"]:
            fact.update(position_id=pid, position_index=index)
            remap = {item["member_id"]: f"{index}-{item['member_id']}" for item in fact["members"]}
            for member in fact["members"]:
                member["identity"]["position_id"] = pid
                member["member_id"] = remap[member["member_id"]]
            for reinf in fact["reinforcements"]:
                reinf["parent_member_id"] = remap[reinf["parent_member_id"]]
                reinf["reinforcement_id"] = f"{index}-{reinf['reinforcement_id']}"
            fact["infills"] = [{"infill_id": f"infill-{index}-{fact['repetition_index']}",
                "position_id": pid, "bay_id": "B1", "leaf_id": None}]
            snapshot["manufacturing"].append(fact)
        for bar in optimized["bars"]["workshop_cut_plan"]:
            bar["bar_index"] = len(plan["bars"]["workshop_cut_plan"]) + 1
            for cut in bar["cuts"]:
                cut["source_position_id"] = pid
                cut["piece_id"] = f"spec-{index}-{cut['sequence']}"
            plan["bars"]["workshop_cut_plan"].append(bar)
        plan["sheets"].append({"sheet_index": index, "purchasing_sku": "GLASS-BASE",
            "sheet_width_mm": "2400.00", "sheet_height_mm": "1800.00", "yield_pct": "41.333333",
            "placements": [{"piece_id": f"panel-{index}-{unit}", "unit_index": unit,
                "source_position_id": pid, "bay_id": "B1", "leaf_id": None,
                "x_mm": str((unit - 1) * 1000), "y_mm": "0", "width_mm": "960.00",
                "height_mm": "960.00", "rotated": False} for unit in (1, 2)]})
    return snapshot, plan


def test_twelve_position_piece_codes_match_every_artifact_and_do_not_change_plan():
    from weasyprint import HTML
    from pypdf import PdfReader
    from io import BytesIO
    from documents.renderers import _url_fetcher

    snapshot, plan = twelve_positions()
    original = deepcopy(plan)
    fingerprint = _optimization_fingerprint(plan)
    display = addressed_plan(snapshot, plan, order_id="order-12")
    assert without_addresses(display) == plan
    codes = {piece["piece_code"] for bar in display["bars"]["workshop_cut_plan"] for piece in bar["cuts"]}
    codes.update(piece["piece_code"] for sheet in display["sheets"] for piece in sheet["placements"])
    assert None not in codes and len(codes) == 96
    assert plan == original and _optimization_fingerprint(plan) == fingerprint
    assert display == addressed_plan(snapshot, plan, order_id="order-12")
    web = {cut["code"] for bar in _plan_bars(display) for cut in bar["cuts"]}
    web.update(piece["code"] for sheet in _plan_sheets(display) for piece in sheet["pieces"])
    csv_codes = set()
    for source in (_cnc_bars_csv(display), _cnc_sheets_csv(display)):
        csv_codes.update(row["piece_label"] for row in csv.DictReader(StringIO(source)))
    dxf = "\n".join(dxf_files(display).values())
    pattern = r"P\d{2}-U\d{2}-(?:M\d{2}(?:-R)?|I\d{2})"
    dxf_codes = set(re.findall(pattern, dxf))
    labels = _piece_labels(snapshot)
    html = _pack_html(order={"order_code": "OT-TEST-12"}, optimization=display,
        snapshot=snapshot, labels=labels, cut_map=_cut_member_map(snapshot, labels),
        infills={}, bar_meta={}, remnant_racks={}, fingerprint=fingerprint)
    pdf = HTML(string=html, url_fetcher=_url_fetcher).write_pdf()
    text = "\n".join(page.extract_text() for page in PdfReader(BytesIO(pdf)).pages)
    pdf_codes = set(re.findall(pattern, text))
    tags = physical_labels(display)
    tag_codes = {tag["code"] for tag in tags}
    assert web == csv_codes == dxf_codes == pdf_codes == tag_codes == codes
    assert len(tags) == len(codes)
    for tag in tags:
        address = urlsplit(tag["qr_payload"])
        assert address.path == "/production"
        assert parse_qs(address.query) == {"order": ["order-12"], "piece": [tag["code"]], "identity": [tag["stable_id"]]}
    # The only long hex is the abbreviated titleblock fingerprint.
    body = html.split('<main', 1)[1]
    assert not re.search(r"[a-f0-9]{10,}", re.sub(r'<svg.*?</svg>', '', body, flags=re.S))
    assert not re.search(r"\d\.0{4}|\d+[.,]\d{2,}%", text)
