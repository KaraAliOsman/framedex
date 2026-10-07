"""D05 real RLS: exact price, sealed faces, physical purchase and optimization."""
from datetime import date
from decimal import Decimal as D
from uuid import UUID

import pytest
from backend.tests.integration.test_shot09_documentary import (
    documentary_tenant as documentary_tenant, as_user, _seed_project, _tenant)
from catalogs.glass import load_products
from documents.service import prepare_documentary_inputs, save_documentary_inputs, revision_snapshot, freeze_revision_a
from documents.repository import DocumentaryError, documentary_backend
from documents.renderers import _doc01, _commercial_palette
from pricing.repository import admin_write, commercial_backend, one, rows
from pricing.service import preview, apply_operation
from production.service import release_production, optimize_work_order
from projects.serializers import PositionWriteSerializer
from projects.service import create_project, save_position, position_row, position_public
from projects.finishes import finish_preview

pytestmark = pytest.mark.rls_integration


def test_finishes_seal_price_purchase_portal_and_bicolor_production(documentary_tenant):
    org, other_org, users, other_user = documentary_tenant
    owner = users["OWNER"]
    _seed_project(org, owner)
    with as_user(owner):
        cost_list = one("SELECT id FROM cost_lists WHERE org_id=%s", [org])["id"]
        required = rows("SELECT sku,unit FROM catalog_demo_prices WHERE system_id IN (SELECT id FROM profile_systems WHERE version=5) "
            "UNION SELECT a.commercial_sku,a.purchase_unit FROM reinforcement_articles a JOIN profile_systems s ON s.id=a.system_id WHERE s.version=5")
        for item in required:
            if not rows("SELECT id FROM cost_list_items WHERE cost_list_id=%s AND sku=%s", [cost_list,item["sku"]]):
                admin_write("cost-items", org, {"cost_list_id":cost_list,"sku":item["sku"],"unit":item["unit"],
                    "item_type":"FIXTURE","unit_cost":D("100")}, "D05 sourced synthetic test prices")
        project = create_project(org,owner,{"name":"D05 bicolor DEMO","client_name":"Fixture","client_rut":"1-9",
            "client_email":"client@example.test","client_phone":"+56900000000","delivery_address":"Valdivia"})
        originals = {}
        for index,(code,finish) in enumerate([("DEMO_60","WHITE"),("DEMO_60","WHITE_WALNUT"),("DEMO_60","ANTHRACITE_WHITE"),
            ("DEMO_60","COEX_GREY"),("DEMO_ALU_PRACTICABLE","WHITE_RAL7016"),
            ("DEMO_ALU_PRACTICABLE","ANODIZED_SILVER"),("DEMO_ALU_PRACTICABLE","WOOD_WALNUT")],1):
            system = UUID(str(one("SELECT id FROM profile_systems WHERE code=%s AND version=5",[code])["id"]))
            glass = next(row for row in load_products(system,org) if row["technical_sku"].endswith("-GLASS-SAFE"))
            design={"system_id":str(system),"nominal_width_mm":"900.00","nominal_height_mm":"850.00","color":finish,
                "parametric_tree":{"id":"vano","type":"BAY","opening_type":"FIXED","glass_thickness_mm":"24.00",
                    "glass_spec":"4-16-4","glass_article_sku":glass["technical_sku"],"glass_product":glass["resolved_product"].model_dump(mode="json"),"sill_height_mm":"900"}}
            serializer=PositionWriteSerializer(data={"location_tag":f"Posición {index} · DEMO","quantity":1,"design":design})
            serializer.is_valid(raise_exception=True)
            position=save_position(org,project["id"],serializer.validated_data)
            public=position_public(position_row(org,position["id"]))
            assert public["design"]["color"]==finish and public["bom"]==position["bom"]
            assert position_row(org,position["id"])["color_interior"]==position["bom"]["finish"]["interior"]["code"]
            preview_data=finish_preview(org,{**serializer.validated_data["design"],"baseline_color":"WHITE"})
            assert preview_data["delta_price_net"] is not None
            if finish=="WHITE":
                assert D(preview_data["delta_price_net"])==0
            else:
                assert D(preview_data["delta_price_net"])>0
            originals[str(position["id"])]=position["bom"]
        prepared=prepare_documentary_inputs(org_id=org,project_id=project["id"])
        inputs=[]
        for pos in prepared["positions"]:
            annotations={}
            for row in pos["workshop_suggestions"]:
                key=(row["bay_id"],row.get("leaf_id"))
                annotations[key]={**annotations.get(key,{}),**{k:v for k,v in row.items() if v is not None}}
            inputs.append({"position_id":pos["position_id"],"calculation_hash":pos["calculation_hash"],"location_tag":pos["location_tag"],
                "manufacturing_placement_policy_id":pos["placement_options"][0]["id"],"handle_requirement_policy_id":pos["handle_options"][0]["id"],
                "reinforcement_cut_policy_id":pos["reinforcement_options"][0]["id"],"workshop_annotations":list(annotations.values()),
                "structural_inputs":[],"glass_polishing":pos["polishing_suggestions"],"handle_intents":[],
                "accessory_schedule":{"schema_version":1,"coverage":"NONE_REQUIRED","items":[]},"legacy_handle_migration_confirmed":True})
        save_documentary_inputs(org_id=org,actor_id=owner,project_id=project["id"],data={"payment_terms":"Anticipo 50 %",
            "quotation_valid_until":date(2026,10,25),"positions":inputs})
        with commercial_backend():
            priced=preview(org,_tenant(org,"OWNER"),{"project_id":project["id"],"pricing_mode":"COST_PLUS_MARGIN","currency":"CLP",
                "effective_date":date(2026,10,6),"context_code":"DEFAULT","discount_pct":D(0),"target_margin":D("0.35"),"segment":"RETAIL",
                "confirmed":False,"reason":"D05 reviewed price","_actor_id":owner})
            apply_operation(org,owner,"OWNER",UUID(priced["id"]),"D05 apply",False)
        try:
            from backend.tests.integration.mounting_fixture import confirm_fixture_measurements
            for pos in rows('SELECT id FROM project_positions WHERE org_id=%s AND project_id=%s',[org,project['id']]):
                confirm_fixture_measurements(org,pos['id'])
            frozen=freeze_revision_a(org_id=org,actor_id=owner,project_id=project["id"],pricing_operation_id=UUID(priced["id"]),confirmed=True,allow_incomplete_workshop=True)
        except DocumentaryError as error:
            pytest.fail(str(error.extra))
        _,snapshot=revision_snapshot(org_id=org,version_id=UUID(frozen["id"]))
        assert frozen["production_allowed"] and frozen["documentary_complete"]
        for pos in snapshot["positions"]:
            assert pos["resolved_finish"]["combination"]["code"]==originals[str(pos["id"])]["finish"]["combination"]["code"]
        html=_doc01(snapshot)
        assert "Nogal exterior / Blanco interior" in html and "aproximado" in html
        assert all(code not in html for code in ("ANTHRACITE", "WALNUT", "COEX_GREY", "ANODIZED_SILVER", "WOOD_WALNUT"))
        bicolor=next(pos for pos in snapshot["positions"] if pos["resolved_finish"]["combination"]["code"]=="WHITE_WALNUT")
        assert _commercial_palette(bicolor,"interior")!=_commercial_palette(bicolor,"exterior")
        with documentary_backend():
            requirements=rows("SELECT specification FROM purchase_requirement_lines WHERE project_version_id=%s AND org_id=%s AND order_type='SUPPLIER_PROFILE_PO'",[frozen["id"],org])
        assert requirements
        released=release_production(org_id=org,version_id=UUID(frozen["id"]),actor_id=owner)
        assert len(released["orders"])==7
        for order in released["orders"]:
            optimized=optimize_work_order(org_id=org,order_id=UUID(order["id"]),actor_id=owner,color="",strategy="fast")
            assert optimized
        _,after=revision_snapshot(org_id=org,version_id=UUID(frozen["id"]))
        assert snapshot==after
    with as_user(other_user),pytest.raises(DocumentaryError,match="version_not_found"):
        revision_snapshot(org_id=other_org,version_id=UUID(frozen["id"]))
