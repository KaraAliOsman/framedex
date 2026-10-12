"""Local D05 HTTP acceptance: real finishes, prices, immutable revision and PDF."""
from datetime import date
import json
import os
from pathlib import Path
import sys
import time
from uuid import uuid5

import httpx
import psycopg

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
import dev_fixture as fixture  # noqa: E402


def main() -> None:
    portal_only = "--portal-only" in sys.argv
    if not fixture.DJANGO.startswith(("http://127.0.0.1:", "http://localhost:", "http://host.docker.internal:")):
        raise SystemExit("D05 requires the owned local stack")
    # Populate only new synthetic catalog prices in the existing fixture list.
    cost_list = str(uuid5(fixture.NS, "cost-list"))
    with psycopg.connect(fixture.DB) as connection:
        prices = connection.execute("SELECT sku,unit,unit_cost FROM catalog_demo_prices WHERE system_id IN (SELECT id FROM profile_systems WHERE version=5)").fetchall()
    for sku, unit, cost in prices:
        fixture.sql("INSERT INTO cost_list_items(id,org_id,cost_list_id,sku,unit,item_type,unit_cost) VALUES(%s,%s,%s,%s,%s,'FIXTURE',%s) ON CONFLICT(cost_list_id,sku) DO NOTHING",
            (str(uuid5(fixture.NS,"d05-cost/"+sku)),fixture.ORG_ID,cost_list,sku,unit,cost))
    token=fixture.login("demo-estimator@fixture.dekopen.local")
    def api(method,path,data=None):
        return fixture.api(token,method,path,data)
    systems=api("GET","/catalogs/systems/")["items"]
    state_path=ROOT/(".run/d05-portal-state.json" if portal_only else ".run/d05-flow-state.json")
    state=json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else None
    project=state["project"] if state else api("POST","/projects/",{"name":"D05 · acabados por caras · aceptación DEMO",
        "client_name":"Cliente de referencia","client_rut":"1-9","client_email":"client@example.test",
        "client_phone":"+56900000000","delivery_address":"Valdivia"})
    records=state["records"] if state else []
    for code,finish in [("DEMO_60","WHITE"),("DEMO_60","WHITE_WALNUT"),("DEMO_60","ANTHRACITE_WHITE"),
        ("DEMO_60","COEX_GREY"),("DEMO_ALU_PRACTICABLE","WHITE_RAL7016"),
        ("DEMO_ALU_PRACTICABLE","ANODIZED_SILVER"),("DEMO_ALU_PRACTICABLE","WOOD_WALNUT")]:
        if any(row["name"]==finish for row in records):
            continue
        system=next(row for row in systems if row["code"]==code and row["version"]==5)
        options=api("GET",f"/projects/design-options/{system['id']}/")
        glass=next(row for row in options["glass_specs"] if row["sku"].endswith("-GLASS-SAFE"))
        tree={"id":"vano","type":"BAY","opening_type":"FIXED","glass_article_sku":glass["sku"],
            "glass_product":glass["product"],"glass_spec":glass["spec"],"glass_thickness_mm":glass["total_thickness_mm"],"sill_height_mm":"900"}
        design={"system_id":system["id"],"nominal_width_mm":"900.00","nominal_height_mm":"850.00","color":finish,"parametric_tree":tree}
        position=api("POST",f"/projects/{project['id']}/positions/",{"location_tag":f"Posición {len(records)+1} · DEMO","quantity":1,"design":design})
        reopened=api("GET",f"/positions/{position['id']}/")
        assert reopened["bom"]==position["bom"] and reopened["design"]["color"]==finish
        price=api("POST","/projects/finish-preview/",{**design,"baseline_color":"WHITE"})
        assert price["delta_price_net"] is not None
        records.append({"name":finish,"position_id":position["id"],"system_id":system["id"],"bom":position["bom"],"price":price})
        state_path.write_text(json.dumps({"project":project,"records":records}),encoding="utf-8")
        print("PASA saved/reopened and price "+finish,flush=True)
    current=api("GET",f"/projects/{project['id']}/")
    if current.get("versions"):
        frozen=next(row for row in current["versions"] if row["revision_code"]==current["current_revision"])
    else:
        prepared=api("GET",f"/documents/projects/{project['id']}/inputs/")
        positions=[]
        for pos in prepared["positions"]:
            annotations={}
            for row in pos["workshop_suggestions"]:
                key=(row["bay_id"],row.get("leaf_id"))
                annotations[key]={**annotations.get(key,{}),**{k:v for k,v in row.items() if v is not None}}
            positions.append({"position_id":pos["position_id"],"calculation_hash":pos["calculation_hash"],"location_tag":pos["location_tag"],
                "manufacturing_placement_policy_id":pos["placement_options"][0]["id"],"handle_requirement_policy_id":pos["handle_options"][0]["id"],
                "reinforcement_cut_policy_id":pos["reinforcement_options"][0]["id"],"workshop_annotations":list(annotations.values()),
                "structural_inputs":[],"glass_polishing":pos["polishing_suggestions"],"handle_intents":[],
                "accessory_schedule":{"schema_version":1,"coverage":"NONE_REQUIRED","items":[]},"legacy_handle_migration_confirmed":True})
        api("PUT",f"/documents/projects/{project['id']}/inputs/",{"payment_terms":"50 % anticipo y saldo contra entrega","quotation_valid_until":"2026-10-25","positions":positions})
        priced={"id":current["current_pricing_operation_id"]} if current.get("current_pricing_operation_id") else api("POST","/pricing/preview/",{
            "project_id":project["id"],"pricing_mode":"COST_PLUS_MARGIN","context_code":"DEFAULT","currency":"CLP",
            "effective_date":date(2026,10,6).isoformat(),"discount_pct":"0","target_margin":"0.35","segment":"RETAIL","reason":"D05 · precio revisado"})
        if not current.get("current_pricing_operation_id"):
            api("POST",f"/pricing/operations/{priced['id']}/apply/",{"confirmed":True,"reason":"D05 · precio revisado"})
        frozen=api("POST",f"/documents/projects/{project['id']}/freeze/",{"pricing_operation_id":priced["id"],"confirmed":True})
    released = {"orders": []}
    if not portal_only:
        manager=fixture.login("demo-manager@fixture.dekopen.local")
        released=fixture.api(manager,"POST",f"/production/versions/{frozen['id']}/release/")
        for order in released["orders"]:
            fixture.api(manager,"POST",f"/production/orders/{order['id']}/optimize/",{"strategy":"fast"})
    artifact=api("POST","/documents/artifacts/",{"document_type":"DOC-01","format":"PDF","project_version_id":frozen["id"]})
    if artifact.get("job"):
        for _ in range(120):
            job=api("GET",f"/jobs/{artifact['job']['id']}/")
            if job["status"]=="SUCCEEDED":
                break
            assert not job["status"].startswith("FAILED"),"Issued finish PDF failed"
            time.sleep(.5)
        assert job["status"]=="SUCCEEDED"
    artifacts=api("GET",f"/documents/projects/{project['id']}/artifacts/")["artifacts"]
    document=next(row for row in artifacts if row["document_type"]=="DOC-01" and row["format"]=="PDF")
    access=api("POST",f"/documents/artifacts/{document['id']}/access/")
    url=access["signed_url"].replace("127.0.0.1","host.docker.internal") if os.name!="nt" else access["signed_url"]
    response=httpx.get(url,timeout=120)
    assert response.status_code==200 and response.content.startswith(b"%PDF")
    out=ROOT/"docs/redesign/captures/colores-acabados/recorrido"
    out.mkdir(parents=True,exist_ok=True)
    (out/"cotizacion-acabados.pdf").write_bytes(response.content)
    (out/("portal-fixture.json" if portal_only else "flujo-7-acabados.json")).write_text(json.dumps({"project_id":project["id"],"version_id":frozen["id"],"positions":records,
        "orders":[o["id"] for o in released["orders"]],"result":"PASA · guardar, reabrir, precio, emisión, producción y PDF",
        "authority":"DEMO v5 · datos sintéticos sin certificación"},ensure_ascii=False,indent=2),encoding="utf-8")
    print("PASA D05 HTTP flow · 7 finishes · immutable revision · " + ("quoted portal" if portal_only else "color-specific stock") + " · issued PDF",flush=True)


if __name__=="__main__":
    main()
