# /// script
# dependencies = ["Pillow", "zxing-cpp==3.1.1", "pypdfium2==5.10.1"]
# ///
"""Decode captured label pixels: uv run scripts/verify_human_codes_qr_pixels.py."""

import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from PIL import Image
import pypdfium2
import zxingcpp


def main() -> None:
    folder = Path(__file__).resolve().parents[1] / "docs/redesign/captures/identificadores-humanos/recorrido"
    flow = json.loads((folder / "http-flow.json").read_text(encoding="utf-8"))
    records = []
    for screenshot in sorted(folder.glob("etiqueta-retazo-*.png")):
        with Image.open(screenshot) as picture:
            decoded = zxingcpp.read_barcodes(picture)
        payloads = [item.text for item in decoded if item.valid]
        assert any(parse_qs(urlsplit(payload).query).get("code") == [flow["remnant"]["code"]] and
            parse_qs(urlsplit(payload).query).get("remnant") == [flow["remnant"]["id"]] for payload in payloads), screenshot.name
        records.append({"capture": screenshot.name, "decoded": payloads})
    assert len(records) == 8
    for order in flow["work_orders"]:
        for kind in ("corte", "produccion"):
            path = folder / f"{order['code']}-{kind}.pdf"
            document = pypdfium2.PdfDocument(path)
            try:
                page_index = len(document) - 1 if kind == "corte" else 0
                picture = document[page_index].render(scale=3).to_pil()
                payloads = [item.text for item in zxingcpp.read_barcodes(picture) if item.valid]
            finally:
                document.close()
            assert any(parse_qs(urlsplit(payload).query).get("order") == [order["order"]] for payload in payloads), path.name
            records.append({"document": path.name, "page": page_index + 1, "decoded": payloads})
    assert len(records) == 32
    for theme in ("light", "dark"):
        for kind in ("retazo-impreso", "etiquetas-impresas"):
            path = folder / f"{kind}-{theme}.pdf"
            document = pypdfium2.PdfDocument(path)
            try:
                payloads = [item.text for page in document for item in zxingcpp.read_barcodes(page.render(scale=3).to_pil()) if item.valid]
                if kind == "retazo-impreso":
                    assert len(document) == 1
                    assert len(payloads) == 1 and parse_qs(urlsplit(payloads[0]).query).get("code") == [flow["remnant"]["code"]]
                else:
                    first = flow["work_orders"][0]
                    scanned = {parse_qs(urlsplit(payload).query)["piece"][0] for payload in payloads}
                    expected = {*first["labels"], first["code"] + "-U01"}
                    assert scanned == expected, scanned ^ expected
                    assert all(parse_qs(urlsplit(payload).query).get("order") == [first["order"]] for payload in payloads)
            finally:
                document.close()
            records.append({"document": path.name, "decoded": payloads})
    assert len(records) == 36
    (folder / "qr-pixels.json").write_text(json.dumps({"result": "PASS", "decoder": "zxing-cpp 3.1.1", "records": records}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("P02: 8 label captures, 24 workshop PDFs and 4 browser prints decoded from pixels.")


if __name__ == "__main__":
    main()
