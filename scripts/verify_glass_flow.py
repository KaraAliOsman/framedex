"""Fixture acceptance only: real HTTP quote, sealed BOM and supplier exports."""

import json
import sys
import time
from pathlib import Path
from decimal import Decimal
import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dev_fixture as fx

est = fx.login("demo-estimator@fixture.dekopen.local")
wm = fx.login("demo-manager@fixture.dekopen.local")


def api(method, path, body=None):
    return fx.api(est, method, path, body)


systems = api("GET", "/catalogs/systems/")["items"]
system = next(item for item in systems if item["code"] == "DEMO_60" and item["version"] == 2)
options = api("GET", f"/projects/design-options/{system['id']}/")
products = {item["sku"]: item for item in options["glass_specs"]}
project = api(
    "POST",
    "/projects/",
    {
        "name": "D02 · pedido vidriero · 12 posiciones DEMO",
        "client_name": "Cliente de prueba D02",
        "client_rut": "1-9",
        "client_email": "cliente@example.test",
        "client_phone": "+56900000000",
        "delivery_address": "Obra de prueba · Valdivia",
    },
)
positions = []
for index in range(1, 13):
    item = products["DEMO_60-GLASS-" + ("SAFE" if index % 2 else "LOWE")]
    tree = {
        "id": "B1",
        "type": "BAY",
        "opening_type": "FIXED",
        "glass_product": item["product"],
        "glass_article_sku": item["sku"],
        "glass_spec": item["spec"],
        "glass_thickness_mm": item["total_thickness_mm"],
        "sill_height_mm": "900",
        "glass_processing": {
            "polished_edges": ["TOP"] if index % 2 else [],
            "holes": 1 if index % 2 else 0,
            "bars_vertical": 0 if index % 2 else 1,
            "bars_horizontal": 0 if index % 2 else 1,
        },
    }
    position = api(
        "POST",
        f"/projects/{project['id']}/positions/",
        {
            "location_tag": f"Dormitorio {index}",
            "quantity": index % 3 + 1,
            "design": {
                "system_id": system["id"],
                "nominal_width_mm": str(750 + index * 20),
                "nominal_height_mm": str(1100 + index * 25),
                "color": "WHITE",
                "parametric_tree": tree,
            },
        },
    )
    positions.append(position)
prepared = api("GET", f"/documents/projects/{project['id']}/inputs/")
inputs = []
for p in prepared["positions"]:
    inputs.append(
        {
            "position_id": p["position_id"],
            "calculation_hash": p["calculation_hash"],
            "location_tag": p["location_tag"],
            "manufacturing_placement_policy_id": p["placement_options"][0]["id"],
            "handle_requirement_policy_id": p["handle_options"][0]["id"],
            "reinforcement_cut_policy_id": p["reinforcement_options"][0]["id"],
            "workshop_annotations": p["workshop_suggestions"],
            "structural_inputs": p.get("structural_inputs", []),
            "glass_polishing": p.get("polishing_suggestions") or [],
            "handle_intents": [],
            "accessory_schedule": {"schema_version": 1, "coverage": "NONE_REQUIRED", "items": []},
            "legacy_handle_migration_confirmed": True,
        }
    )
api(
    "PUT",
    f"/documents/projects/{project['id']}/inputs/",
    {
        "payment_terms": "50 % anticipo y 50 % contra entrega",
        "quotation_valid_until": "2026-10-25",
        "positions": inputs,
    },
)
operation = api(
    "POST",
    "/pricing/preview/",
    {
        "project_id": project["id"],
        "pricing_mode": "COST_PLUS_MARGIN",
        "context_code": "DEFAULT",
        "currency": "CLP",
        "effective_date": "2026-10-05",
        "discount_pct": "0",
        "target_margin": "0.35",
        "segment": "RETAIL",
        "reason": "D02 · verificación de mínimo y recargos",
    },
)
api(
    "POST",
    f"/pricing/operations/{operation['id']}/apply/",
    {"confirmed": True, "reason": "D02 · precio revisado"},
)
frozen = api(
    "POST",
    f"/documents/projects/{project['id']}/freeze/",
    {"pricing_operation_id": operation["id"], "confirmed": True},
)
fx.api(wm, "POST", "/production/work-centers/seed-defaults/")
released = fx.api(wm, "POST", f"/production/versions/{frozen['id']}/release/")
ids = [item["id"] for item in released["orders"]]
report = fx.api(wm, "GET", "/production/glass-orders/?orders=" + ",".join(ids))
assert len(report["rows"]) == 12
by_index = {p["position_index"]: p for p in positions}
for row in report["rows"]:
    piece = by_index[row["position_index"]]["bom"]["glasses"][row["piece_index"] - 1]
    assert Decimal(row["width_mm"]) == Decimal(piece["width_mm"]) and Decimal(
        row["height_mm"]
    ) == Decimal(piece["height_mm"])
    assert row["quantity"] == by_index[row["position_index"]]["quantity"]
    assert "DEMO" in " ".join(row["instructions"])
out = Path("docs/redesign/captures/vidrios-compuestos/recorrido")
out.mkdir(parents=True, exist_ok=True)
headers = {"Authorization": "Bearer " + wm, "X-Organization-ID": fx.ORG_ID}
for extension in ("PDF", "CSV"):
    response = httpx.get(
        fx.DJANGO + "/api/v1/production/glass-orders/",
        params={"orders": ",".join(ids), "export_format": extension},
        headers=headers,
        timeout=120,
    )
    assert response.status_code == 200, extension + " export failed"
    (out / ("pedido-12-posiciones." + extension.lower())).write_bytes(response.content)
artifact = api(
    "POST",
    "/documents/artifacts/",
    {"document_type": "DOC-01", "format": "PDF", "project_version_id": frozen["id"]},
)
if artifact.get("job"):
    for _ in range(60):
        job = api("GET", f"/jobs/{artifact['job']['id']}/")
        if job["status"] == "SUCCEEDED":
            break
        if job["status"].startswith("FAILED"):
            raise AssertionError("DOC-01 job failed")
        time.sleep(0.5)
    assert job["status"] == "SUCCEEDED", "DOC-01 job did not complete"
artifacts = api("GET", f"/documents/projects/{project['id']}/artifacts/")["artifacts"]
doc = next(
    value for value in artifacts if value["document_type"] == "DOC-01" and value["format"] == "PDF"
)
access = api("POST", f"/documents/artifacts/{doc['id']}/access/")
document = httpx.get(access["signed_url"], timeout=120)
assert document.status_code == 200
(out / "cotizacion-12-posiciones.pdf").write_bytes(document.content)
evidence = {
    "project_id": project["id"],
    "version_id": frozen["id"],
    "orders": ids,
    "positions": len(report["rows"]),
    "labels": len(report["labels"]),
    "result": "PASA · precio, sellado, emisión, OT, pedido, procesos y dimensiones exactas",
}
(out / "flujo-12-posiciones.json").write_text(
    json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(evidence, ensure_ascii=False))
