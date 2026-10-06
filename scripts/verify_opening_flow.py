"""Local D03 acceptance: real saved products, pricing, sealing and issued PDF."""
from datetime import date
import json
import os
from pathlib import Path
import sys
import time

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "engine/src"))
sys.path.insert(0, str(ROOT / "backend"))
import dev_fixture as fixture  # noqa: E402
from engine.tests.opening_cases import typologies  # noqa: E402
from dekopen_engine.openings import opening_label  # noqa: E402


def main() -> None:
    if not fixture.DJANGO.startswith(("http://127.0.0.1:", "http://localhost:", "http://host.docker.internal:")):
        raise SystemExit("D03 acceptance may only use the owned local stack")
    token = fixture.login("demo-estimator@fixture.dekopen.local")
    def api(method, path, data=None):
        return fixture.api(token, method, path, data)
    systems = api("GET", "/catalogs/systems/")["items"]
    state_path = ROOT / ".run/d03-flow-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else None
    project = state["project"] if state else api("POST", "/projects/", {"name": "D03 · 21 aperturas · aceptación DEMO",
        "client_name": "Cliente de referencia", "client_rut": "1-9", "client_email": "client@example.test",
        "client_phone": "+56900000000", "delivery_address": "Valdivia"})
    records = state["records"] if state else []
    for name, (code, node) in typologies().items():
        if any(row["name"] == name for row in records):
            continue
        system = next(row for row in systems if row["code"] == code and row["version"] == 3)
        options = api("GET", f"/projects/design-options/{system['id']}/")
        glass = next(row for row in options["glass_specs"] if row["sku"].endswith("-GLASS-SAFE"))
        tree = node.model_dump(mode="json", exclude_none=True)
        width, height = tree.pop("width_mm"), tree.pop("height_mm")
        def infill(target):
            if target["type"] == "BAY":
                target.update(glass_article_sku=glass["sku"], glass_product=glass["product"],
                    glass_spec=glass["spec"], glass_thickness_mm=glass["total_thickness_mm"], sill_height_mm="900")
            for child in target.get("children", []):
                infill(child)
        infill(tree)
        label = opening_label(node.opening, node.opening_use, node.hinged_layout) if node.opening else "Puerta con lateral fijo"
        position = api("POST", f"/projects/{project['id']}/positions/", {"location_tag": label,
            "quantity": 1, "design": {"system_id": system["id"], "nominal_width_mm": width,
                "nominal_height_mm": height, "color": "WHITE", "parametric_tree": tree}})
        reopened = api("GET", f"/positions/{position['id']}/")
        assert reopened["bom"] == position["bom"], name + " BOM changed on reopen"
        records.append({"name": name, "position_id": position["id"], "tree": tree,
            "bom": position["bom"], "system_id": system["id"]})
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps({"project": project, "records": records}), encoding="utf-8")
        print("PASA saved/reopened " + name, flush=True)
    prepared = api("GET", f"/documents/projects/{project['id']}/inputs/")
    inputs = []
    for position in prepared["positions"]:
        annotations = {}
        for row in position["workshop_suggestions"]:
            key = (row["bay_id"], row.get("leaf_id"))
            annotations[key] = {**annotations.get(key, {}), **{key: value for key, value in row.items() if value is not None}}
        inputs.append({"position_id": position["position_id"], "calculation_hash": position["calculation_hash"],
            "location_tag": position["location_tag"], "manufacturing_placement_policy_id": position["placement_options"][0]["id"],
            "handle_requirement_policy_id": position["handle_options"][0]["id"],
            "reinforcement_cut_policy_id": position["reinforcement_options"][0]["id"],
            "workshop_annotations": list(annotations.values()), "structural_inputs": [
                {"target_id": span["target_id"], "required_ix_cm4": "1.00",
                 "structural_basis": "DEMO · carga ficticia del ensayo D03; no es cálculo de viento ni certificación para una obra"}
                for span in position["workshop_targets"]["spans"]],
            "glass_polishing": position.get("polishing_suggestions") or [], "handle_intents": [],
            "accessory_schedule": {"schema_version": 1, "coverage": "NONE_REQUIRED", "items": []},
            "legacy_handle_migration_confirmed": True})
    api("PUT", f"/documents/projects/{project['id']}/inputs/", {"payment_terms": "50 % anticipo y saldo contra entrega",
        "quotation_valid_until": "2026-10-25", "positions": inputs})
    current = api("GET", f"/projects/{project['id']}/")
    if current.get("current_pricing_operation_id"):
        priced = {"id": current["current_pricing_operation_id"]}
    else:
        priced = api("POST", "/pricing/preview/", {"project_id": project["id"], "pricing_mode": "COST_PLUS_MARGIN",
            "context_code": "DEFAULT", "currency": "CLP", "effective_date": date(2026, 10, 6).isoformat(),
            "discount_pct": "0", "target_margin": "0.35", "segment": "RETAIL", "reason": "D03 · revisión de tipologías"})
        api("POST", f"/pricing/operations/{priced['id']}/apply/", {"confirmed": True, "reason": "D03 · precio revisado"})
    frozen = api("POST", f"/documents/projects/{project['id']}/freeze/", {"pricing_operation_id": priced["id"], "confirmed": True})
    artifact = api("POST", "/documents/artifacts/", {"document_type": "DOC-01", "format": "PDF", "project_version_id": frozen["id"]})
    if artifact.get("job"):
        for _ in range(120):
            job = api("GET", f"/jobs/{artifact['job']['id']}/")
            if job["status"] == "SUCCEEDED":
                break
            if job["status"].startswith("FAILED"):
                raise AssertionError("D03 issued PDF job failed")
            time.sleep(0.5)
        assert job["status"] == "SUCCEEDED"
    artifacts = api("GET", f"/documents/projects/{project['id']}/artifacts/")["artifacts"]
    document = next(row for row in artifacts if row["document_type"] == "DOC-01" and row["format"] == "PDF")
    access = api("POST", f"/documents/artifacts/{document['id']}/access/")
    storage_url = access["signed_url"].replace("127.0.0.1", "host.docker.internal") if os.name != "nt" else access["signed_url"]
    response = httpx.get(storage_url, timeout=120)
    assert response.status_code == 200 and response.content.startswith(b"%PDF")
    out = ROOT / "docs/redesign/captures/aperturas-tipologias/recorrido"
    out.mkdir(parents=True, exist_ok=True)
    (out / "cotizacion-21-aperturas.pdf").write_bytes(response.content)
    evidence = {"project_id": project["id"], "version_id": frozen["id"], "positions": records,
        "production_allowed": frozen["production_allowed"], "documentary_complete": frozen["documentary_complete"],
        "structural_fixture": "DEMO · carga ficticia de ensayo; el catálogo no declara inercia para certificar el montante del lateral",
        "result": "PASA · guardado, reapertura, precio, sellado y PDF emitido", "currency": "CLP"}
    (out / "flujo-21-aperturas.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print("PASA D03 full HTTP flow · 21 typologies · issued PDF", flush=True)


if __name__ == "__main__":
    main()
