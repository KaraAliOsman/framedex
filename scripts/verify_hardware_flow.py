"""Local D04 acceptance: real saved products, pricing, sealing and issued PDF."""
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
from engine.tests.hardware_cases import hardware_case_inputs  # noqa: E402
from dekopen_engine.hardware_classes import hardware_picking  # noqa: E402
from dekopen_engine.models import HardwareItem  # noqa: E402
from decimal import Decimal  # noqa: E402


def main() -> None:
    if not fixture.DJANGO.startswith(("http://127.0.0.1:", "http://localhost:", "http://host.docker.internal:")):
        raise SystemExit("D04 acceptance may only use the owned local stack")
    token = fixture.login("demo-estimator@fixture.dekopen.local")
    def api(method, path, data=None):
        return fixture.api(token, method, path, data)
    systems = api("GET", "/catalogs/systems/")["items"]
    portal_only = "--portal-only" in sys.argv
    state_path = ROOT / (".run/d04-portal-state.json" if portal_only else ".run/d04-flow-state.json")
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else None
    project = state["project"] if state else api("POST", "/projects/", {"name": "D04 · 12 posiciones de herrajes · aceptación DEMO",
        "client_name": "Cliente de referencia", "client_rut": "1-9", "client_email": "client@example.test",
        "client_phone": "+56900000000", "delivery_address": "Valdivia"})
    records = state["records"] if state else []
    for index in range(12):
        label, params, node, _ = hardware_case_inputs()[index%4]
        name = label+"-"+str(index+1)
        code = ("DEMO_60", "DEMO_60", "DEMO_CORREDERA_60", "DEMO_PUERTA_70")[index%4]
        if any(row["name"] == name for row in records):
            continue
        system = next(row for row in systems if row["code"] == code and row["version"] == 4)
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
        label = name+" · DEMO"
        position = api("POST", f"/projects/{project['id']}/positions/", {"location_tag": label,
            "quantity": index%3+1, "design": {"system_id": system["id"], "nominal_width_mm": width,
                "nominal_height_mm": height, "color": "WHITE", "parametric_tree": tree}})
        reopened = api("GET", f"/positions/{position['id']}/")
        assert reopened["bom"] == position["bom"], name + " BOM changed on reopen"
        records.append({"name": name, "position_id": position["id"], "tree": tree,
            "bom": position["bom"], "system_id": system["id"]})
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps({"project": project, "records": records}), encoding="utf-8")
        print("PASA saved/reopened " + name, flush=True)
    current = api("GET", f"/projects/{project['id']}/")
    versions = current.get("versions") or []
    if versions:
        frozen = next(row for row in versions if row["revision_code"] == current["current_revision"])
    else:
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
                     "structural_basis": "DEMO · carga ficticia del ensayo D04; no es cálculo de viento ni certificación para una obra"}
                    for span in position["workshop_targets"]["spans"]],
                "glass_polishing": position.get("polishing_suggestions") or [], "handle_intents": [],
                "accessory_schedule": {"schema_version": 1, "coverage": "NONE_REQUIRED", "items": []},
                "legacy_handle_migration_confirmed": True})
        api("PUT", f"/documents/projects/{project['id']}/inputs/", {"payment_terms": "50 % anticipo y saldo contra entrega",
            "quotation_valid_until": "2026-10-25", "positions": inputs})
        if current.get("current_pricing_operation_id"):
            priced = {"id": current["current_pricing_operation_id"]}
        else:
            priced = api("POST", "/pricing/preview/", {"project_id": project["id"], "pricing_mode": "COST_PLUS_MARGIN",
                "context_code": "DEFAULT", "currency": "CLP", "effective_date": date(2026, 10, 6).isoformat(),
                "discount_pct": "0", "target_margin": "0.35", "segment": "RETAIL", "reason": "D04 · revisión de tipologías"})
            api("POST", f"/pricing/operations/{priced['id']}/apply/", {"confirmed": True, "reason": "D04 · precio revisado"})
        frozen = api("POST", f"/documents/projects/{project['id']}/freeze/", {"pricing_operation_id": priced["id"], "confirmed": True})
    if portal_only:
        out = ROOT / "docs/redesign/captures/herrajes-clases/recorrido"
        (out / "portal-fixture.json").write_text(json.dumps({"project_id": project["id"], "version_id": frozen["id"],
            "result": "PASA · revisión cotizada sin liberación a producción; enlace solo en memoria"}), encoding="utf-8")
        print("PASA D04 portal fixture · sealed quotation without production release", flush=True)
        return
    wm = fixture.login("demo-manager@fixture.dekopen.local")
    fixture.api(wm,"POST","/production/work-centers/seed-defaults/")
    released = fixture.api(wm,"POST",f"/production/versions/{frozen['id']}/release/")
    orders = released["orders"]
    picking = fixture.api(wm,"GET",f"/production/versions/{frozen['id']}/hardware-picking/")
    expected=[]
    for index,row in enumerate(records):
        expected.extend((HardwareItem.model_validate_json(json.dumps(item)),index%3+1,f"Posición {index+1}") for item in row["bom"]["hardware_items"])
    actual = {(row["sku"], row["cut_length_mm"], row["source"]): Decimal(row["quantity"]) for row in picking["rows"]}
    engine = {(row["sku"], str(row["cut_length_mm"]) if row["cut_length_mm"] is not None else None,
        row["source"]): row["quantity"] for row in hardware_picking(expected)}
    assert actual == engine, "Revision picking must match every component and exact cut length"
    for order in orders:
        detail=fixture.api(wm,"GET",f"/production/orders/{order['id']}/")
        assert detail["hardware_picking"] and detail["hardware_machining"]
        assert any(step["code"]=="MACHINING" for step in detail["steps"])
    artifact = api("POST", "/documents/artifacts/", {"document_type": "DOC-01", "format": "PDF", "project_version_id": frozen["id"]})
    if artifact.get("job"):
        for _ in range(120):
            job = api("GET", f"/jobs/{artifact['job']['id']}/")
            if job["status"] == "SUCCEEDED":
                break
            if job["status"].startswith("FAILED"):
                raise AssertionError("D04 issued PDF job failed")
            time.sleep(0.5)
        assert job["status"] == "SUCCEEDED"
    artifacts = api("GET", f"/documents/projects/{project['id']}/artifacts/")["artifacts"]
    document = next(row for row in artifacts if row["document_type"] == "DOC-01" and row["format"] == "PDF")
    access = api("POST", f"/documents/artifacts/{document['id']}/access/")
    storage_url = access["signed_url"].replace("127.0.0.1", "host.docker.internal") if os.name != "nt" else access["signed_url"]
    response = httpx.get(storage_url, timeout=120)
    assert response.status_code == 200 and response.content.startswith(b"%PDF")
    out = ROOT / "docs/redesign/captures/herrajes-clases/recorrido"
    out.mkdir(parents=True, exist_ok=True)
    fixture.api(wm,"POST",f"/production/orders/{orders[0]['id']}/optimize/",{"strategy":"fast"})
    pack = httpx.get(f"{fixture.DJANGO}/api/v1/production/orders/{orders[0]['id']}/production-pack/",
        headers={"Authorization":f"Bearer {wm}","X-Organization-ID":fixture.ORG_ID},timeout=120)
    assert pack.status_code == 200 and pack.content.startswith(b"%PDF"), "D04 production pack did not render"
    (out / "pack-herrajes.pdf").write_bytes(pack.content)
    (out / "cotizacion-12-posiciones.pdf").write_bytes(response.content)
    evidence = {"project_id": project["id"], "version_id": frozen["id"], "positions": records, "orders":[order["id"] for order in orders], "picking":picking,
        "production_allowed": frozen["production_allowed"], "documentary_complete": frozen["documentary_complete"],
        "authority": "DEMO v4 · sin certificación de fabricante ni coordenadas de mecanizado inventadas",
        "result": "PASA · guardado, reapertura, precio, sellado y PDF emitido", "currency": "CLP"}
    (out / "flujo-12-posiciones.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print("PASA D04 full HTTP flow · 12 positions · exact component picking · issued PDF", flush=True)


if __name__ == "__main__":
    main()
