"""P02 local-fixture acceptance: HTTP addresses and real sealed artifacts.

Run with the isolated development stack environment. Never prints credentials;
only the fixture organization's existing twelve-position revision is exercised.
"""
from __future__ import annotations

import csv
from decimal import Decimal
from io import BytesIO, StringIO
import json
import os
from pathlib import Path
import re
from urllib.parse import parse_qs, quote, urlsplit

import httpx
import psycopg
from pypdf import PdfReader

import dev_fixture as fx

OUT = Path("docs/redesign/captures/identificadores-humanos/recorrido")
PATTERN = r"P\d{2}-U\d{2}-(?:M\d{2}(?:-R)?|I\d{2})"


def main() -> None:
    target = urlsplit(os.environ["DATABASE_URL"])
    if target.hostname not in {"127.0.0.1", "localhost", "host.docker.internal"} or target.port != 25332:
        raise SystemExit("This verifier only operates on the owned framedex-cola fixture.")
    token = fx.login("demo-manager@fixture.dekopen.local")
    headers = {"Authorization": "Bearer " + token, "X-Organization-ID": fx.ORG_ID}

    def api(method, path, body=None):
        return fx.api(token, method, path, body)

    def file(path):
        response = httpx.get(fx.DJANGO + "/api/v1" + path, headers=headers, timeout=120)
        response.raise_for_status()
        return response.content

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        revision = conn.execute("""SELECT v.id, p.id FROM project_versions v JOIN projects p ON p.id=v.project_id
            WHERE p.org_id=%s AND v.production_allowed AND
            (SELECT count(*) FROM project_positions pp WHERE pp.project_id=p.id)=12 AND
            (SELECT count(*) FROM orders o WHERE o.project_version_id=v.id AND o.order_type='WORKSHOP_OT')=12
            ORDER BY p.created_at DESC LIMIT 1""", [fx.ORG_ID]).fetchone()
    assert revision, "Need a real twelve-position production-capable fixture revision"
    version, project = map(str, revision)
    state = api("GET", f"/purchasing/versions/{version}/")
    order_type = "SUPPLIER_PROFILE_PO"
    requirements = [row for row in state["requirements"] if row["order_type"] == order_type and not row["claimed"]]
    if requirements:
        eligibility = api("POST", f"/purchasing/versions/{version}/eligibilities/", {
            "order_type": order_type, "supplier_identity": "P02-DEMO-SUPPLIER",
            "supplier_name": "Proveedor de aceptación · DEMO", "supplier_details": {"email": "proveedor@example.test"},
            "eligible_requirement_keys": [row["requirement_key"] for row in requirements],
            "evidence": {"basis": "Aceptación P02 sobre catálogo sintético DEMO", "reference": "P02"},
            "version": 1, "confirmed": True,
        })
        for row in requirements:
            api("PUT", f"/purchasing/requirements/{row['id']}/allocation/", {"supplier_eligibility_id": eligibility["id"]})
        api("POST", f"/purchasing/versions/{version}/confirm/", {"order_type": order_type, "confirmed": True})
    state = api("GET", f"/purchasing/versions/{version}/")
    order = next(row for row in state["orders"] if row["order_type"] == order_type)
    assert re.fullmatch(r"OC-\d{6,}", order["order_code"])
    if order["status"] == "DRAFT":
        api("POST", f"/purchasing/orders/{order['id']}/send/", {
            "confirmed": True, "expected_at": "2026-10-20", "sent_to": "proveedor@example.test",
        })
    receiving_path = f"/inventory/orders/{order['id']}/receiving/"
    receiving = api("GET", receiving_path)
    lines = [{"order_line_id": row["id"], "received_qty": str(row["outstanding_qty"]),
        "damaged_qty": "0", "rack_location": "P02-A", "lot_code": "P02-DEMO"}
        for row in receiving["lines"] if Decimal(str(row["outstanding_qty"])) > 0]
    if lines:
        payload = {"receipt_key": "P02-acceptance-" + order["id"], "note": "Recepción de aceptación · DEMO", "lines": lines}
        first = api("POST", f"/inventory/orders/{order['id']}/receipts/", payload)
        assert first == api("POST", f"/inventory/orders/{order['id']}/receipts/", payload)
    receiving = api("GET", receiving_path)
    receipt = receiving["receipts"][0]
    assert re.fullmatch(r"REC-\d{6,}", receipt["receipt_code"])
    OUT.mkdir(parents=True, exist_ok=True)
    work_orders = api("POST", f"/production/versions/{version}/release/")["orders"]
    assert len(work_orders) == 12, "Domain creates one OT per position, twelve per revision"
    records = []
    for work in work_orders:
        oid = work["id"]
        path = f"/production/orders/{oid}"
        detail = api("GET", path + "/")
        optimization = detail["payload"].get("optimization") or {}
        if not optimization or optimization.get("invalidated"):
            api("POST", path + "/optimize/", {"color": "WHITE", "strategy": "auto"})
            detail = api("GET", path + "/")
            optimization = detail["payload"]["optimization"]
        codes = {cut["piece_code"] for bar in optimization["bars"]["workshop_cut_plan"] for cut in bar["cuts"]}
        codes.update(piece["piece_code"] for sheet in optimization.get("sheets", []) for piece in sheet["placements"])
        assert None not in codes
        api("POST", path + "/packing/")
        tags = api("GET", path + "/labels/")
        labels = tags["piece_labels"]
        assert {label["code"] for label in labels} == codes and len(labels) == len(codes)
        for label in labels:
            address = parse_qs(urlsplit(label["qr_payload"]).query)
            assert address == {"order": [oid], "piece": [label["code"]], "identity": [label["stable_id"]]}
        for unit in tags["labels"]:
            scan = api("GET", "/production/pieces/" + quote(unit["qr_payload"], safe="") + "/trace/")
            assert scan["matches"]
            assert all(match["work_order"]["id"] == oid and
                match["location"]["piece"]["unit_index"] == unit["unit_index"] for match in scan["matches"])
        api("POST", path + "/cnc-export/")
        csv_codes = set()
        for filename in ("bars.csv", *( ["sheets.csv"] if optimization.get("sheets") else [])):
            data = file(path + "/cnc-export/" + filename)
            (OUT / (work["order_code"] + "-" + filename)).write_bytes(data)
            body = "\n".join(line for line in data.decode().splitlines() if not line.startswith("#"))
            csv_codes.update(row["piece_label"] for row in csv.DictReader(StringIO(body)))
        exported = api("POST", path + "/dxf-export/")
        dxf_codes = set()
        for filename in exported["files"]:
            filename = filename if isinstance(filename, str) else filename["name"]
            data = file(path + "/dxf-export/" + filename)
            (OUT / (work["order_code"] + "-" + filename)).write_bytes(data)
            dxf_codes.update(re.findall(PATTERN, data.decode()))
        pdf = file(path + "/cut-pack/")
        (OUT / (work["order_code"] + "-corte.pdf")).write_bytes(pdf)
        text = "\n".join(page.extract_text() for page in PdfReader(BytesIO(pdf)).pages)
        pdf_codes = set(re.findall(PATTERN, text))
        assert codes == csv_codes == dxf_codes == pdf_codes, (work["order_code"], codes ^ pdf_codes, codes ^ dxf_codes)
        assert not re.search(r"\d\.0{4}|\d+[.,]\d{2,}%", text)
        production = file(path + "/production-pack/")
        assert production.startswith(b"%PDF-")
        (OUT / (work["order_code"] + "-produccion.pdf")).write_bytes(production)
        scan = api("GET", "/production/pieces/" + quote(labels[0]["code"], safe="") + "/trace/")
        assert any(match["work_order"]["id"] == oid and match["location"]["piece"]["code"] == labels[0]["code"] for match in scan["matches"])
        records.append({"order": oid, "code": work["order_code"], "labels": sorted(codes), "equal_artifacts": True})
        print(work["order_code"], len(codes), "web/PDF/CSV/DXF/QR PASS", flush=True)
    remnants = api("GET", "/inventory/remnants/")["remnants"]
    remnant = next((row for row in remnants if row.get("notes") == "P02 · aceptación DEMO"), None)
    if remnant is None:
        authority = api("GET", "/inventory/bar-authorities/")["authorities"][0]
        remnant = api("POST", "/inventory/remnants/", {"kind": "BAR", "stock_authority_id": authority["id"],
            "length_mm": "850", "rack_location": "P02-R", "notes": "P02 · aceptación DEMO"})
        remnant = remnant.get("remnant", remnant)
    assert re.fullmatch(r"RT-\d{6,}", remnant["code"])
    tag = api("GET", f"/inventory/remnants/{remnant['id']}/label/")
    assert parse_qs(urlsplit(tag["qr_payload"]).query)["remnant"] == [remnant["id"]]
    addresses = {}
    for code in (order["order_code"], receipt["receipt_code"], remnant["code"], work_orders[0]["order_code"]):
        found = api("GET", "/search/?q=" + quote(code))
        match = next(row for row in found["results"] if row["title"] == code)
        addresses[code] = match["path"]
    report = {"project": project, "version": version, "order": order, "receipt": receipt,
        "remnant": remnant, "work_orders": records, "addresses": addresses, "result": "PASS"}
    (OUT / "http-flow.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(".run/p02-flow-state.json").write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
    print("OC/REC replay/RT/command addresses PASS; twelve real position OTs verified", flush=True)


if __name__ == "__main__":
    main()
