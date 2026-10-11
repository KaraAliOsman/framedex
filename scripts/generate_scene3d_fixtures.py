"""Motor-backed 3D render fixtures; no manufacturing arithmetic in the UI."""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "engine" / "src"))

from backend.catalogs.demo_advanced import advanced_manifest  # noqa: E402
from backend.catalogs.demo_openings import opening_manifest  # noqa: E402
from dekopen_engine.geometry import calculate_geometry  # noqa: E402
from dekopen_engine.snapshot import result_payload  # noqa: E402
from dekopen_engine.models import ParametricNode  # noqa: E402
from engine.tests.advanced_cases import advanced_node, advanced_params, advanced_typologies  # noqa: E402
from engine.tests.opening_cases import opening_params, typologies  # noqa: E402


def fixtures() -> list[dict[str, object]]:
    records = {(r["code"], "advanced"): r for r in advanced_manifest()}
    records.update({(r["code"], "physical"): r for r in opening_manifest()})
    cases = [(name, code, node, "physical") for name, (code, node) in typologies().items()]
    cases += [(code + "/" + recipe, code, advanced_node(code, recipe), "advanced")
              for code, recipe in advanced_typologies()]
    symbols = json.loads((ROOT / "engine/tests/fixtures/symbols/cases.json").read_text(encoding="utf-8"))
    for symbol in symbols:
        if symbol["view"] != "interior" or symbol["name"].startswith("Diagrama reservado"):
            continue
        module = symbol["product"]["assembly"]["modules"][0]
        if module["tree"].get("sliding_layout"):
            tree = {**module["tree"], "opening": {**module["tree"]["opening"], "movement": "SLIDE"}}
            node = ParametricNode.model_validate_json(json.dumps({**tree, "width_mm": module["width_mm"], "height_mm": module["height_mm"], "glass_thickness_mm": "24", "glass_spec": "4-16-4 Float Incoloro", "glass_article_sku": "DEMO-GLASS"}))
            cases.append((symbol["name"], "DEMO_CORREDERA_60", node, "physical"))
    output = []
    for name, code, node, family in cases:
        record = records[(code, family)]
        params = advanced_params(code) if family == "advanced" else opening_params(code)
        result = result_payload(calculate_geometry(node, params, finish="WHITE"))
        tree = json.loads(node.model_dump_json(exclude_none=True))
        width, height = tree.pop("width_mm"), tree.pop("height_mm")
        output.append({
            "name": name, "synthetic": True,
            "source": "engine/tests/fixtures/symbols/cases.json (P05 layout evaluated by D03 motor)" if node.sliding_layout else "engine/tests/golden_advanced_openings.json" if family == "advanced" else "engine/tests/golden_openings.json",
            "product": {"version": "product-v2", "assembly": {"modules": [
                {"id": "m1", "width_mm": width, "height_mm": height, "tree": tree}
            ], "couplings": []}},
            "openingFacts": {"m1": result.get("opening_leaves", [])},
            "finish": result.get("finish"),
            "options": {
                "profiles": [{key: item.get(key) for key in ("sku", "role", "name", "material", "face_width_mm", "section")} for item in record["articles"]],
                "hardware_kits": record["params"].get("available_hardware_kits", []),
                "rebate_depth_mm": record["params"].get("rebate_depth_mm"),
                "sash_overlap_mm": record["params"].get("sash_overlap_mm"),
            },
        })
    return output


if __name__ == "__main__":
    path = ROOT / "engine/tests/fixtures/scene3d.json"
    data = (json.dumps(fixtures(), ensure_ascii=False, indent=2) + "\n").encode()
    if "--check" in sys.argv:
        if path.read_bytes().replace(b"\r\n", b"\n") != data:
            raise SystemExit("3D fixtures differ from their motor authority")
    else:
        path.write_bytes(data)
    print("40 motor-backed 3D fixtures verified.")
