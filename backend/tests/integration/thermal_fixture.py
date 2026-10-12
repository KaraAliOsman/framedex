"""Isolated reviewed inputs for workflow tests; no production certification.

All source labels explicitly say test. Values must never seed a customer catalog.
"""
from uuid import UUID, uuid4
from copy import deepcopy
from decimal import Decimal

from backend.tests.integration.catalog_fixture import copy_fixed_catalog, decode_jsonb_columns
from backend.tests.integration.test_shot09_documentary import _seed_project, as_user
from catalogs import evidence
from engine_api.repository import SystemParamsRepository
from pricing.repository import json_text, one, rows
from projects import service, thermal
from projects.thermal_views import ThermalAuthoritySerializer, ThermalInputSerializer
from authentication.rls import catalog_backend
from pricing.repository import commercial_backend
from datetime import date


def reviewed_case(org, actor, *, with_alternatives=False, baseline_ug="1.1"):
    project_id, position_id, _ = _seed_project(org, actor, apply_pricing=False)
    system_id = copy_fixed_catalog(org)
    source_system=one("SELECT id FROM public.profile_systems WHERE code='DEMO_60' AND version=1")["id"]
    for table in ("manufacturing_placement_policies","handle_requirement_policies","reinforcement_cut_policies"):
        for source in rows(f"SELECT * FROM public.{table} WHERE system_id=%s AND org_id IS NULL",[source_system]):
            source=decode_jsonb_columns(table,source)
            one(f"INSERT INTO public.{table} SELECT (jsonb_populate_record(NULL::public.{table},%s::jsonb)).* RETURNING id",
                [json_text({**source,"id":uuid4(),"system_id":system_id,"org_id":org})])
    one("UPDATE public.profile_systems SET name='Prueba térmica aislada · sin certificación',"
        "data_provenance='MANUAL',is_demo=FALSE "
        "WHERE id=%s RETURNING id", [system_id])
    rows("UPDATE public.profile_articles SET data_provenance='MANUAL' WHERE system_id=%s RETURNING id", [system_id])
    mapping = one("SELECT * FROM public.glass_purchase_mappings WHERE system_id=%s AND technical_sku='VIDRIO-BASE' ORDER BY version DESC LIMIT 1", [system_id])
    mapping = decode_jsonb_columns("glass_purchase_mappings", mapping)
    mapping_id = uuid4()
    one("INSERT INTO public.glass_purchase_mappings SELECT (jsonb_populate_record(NULL::public.glass_purchase_mappings,%s::jsonb)).* RETURNING id",
        [json_text({**mapping,"id":mapping_id,"version":1,"technical_sku":"THERMAL-BASE","purchasing_sku":"THERMAL-BASE","glass_spec":"4-16-4"})])
    from catalogs.glass import recipe_payload
    glass_product = recipe_payload({"glass_spec":"4-16-4","source":"Prueba matemática aislada, sin certificación"}, synthetic=False)["product"]
    glass_product["composition"]["layers"][1]["spacer"] = "WARM_EDGE"
    one("INSERT INTO public.catalog_glass_compositions(org_id,system_id,mapping_id,status,product,legacy_spec) VALUES(%s,%s,%s,'PARSED',%s::jsonb,'4-16-4') RETURNING id",
        [org,system_id,mapping_id,json_text(glass_product)])
    from pricing.repository import admin_write
    with as_user(actor):
        with commercial_backend():
            cost_list=rows("SELECT id FROM public.cost_lists WHERE org_id=%s AND currency='CLP' ORDER BY valid_from DESC,id",[org])[0]
            exists=rows("SELECT id FROM public.cost_list_items WHERE cost_list_id=%s AND sku='THERMAL-BASE'",[cost_list["id"]])
        if not exists:
            admin_write("cost-items",org,{"cost_list_id":cost_list["id"],"sku":"THERMAL-BASE","item_type":"FIXTURE","unit":"M2","unit_cost":Decimal("100")},"Prueba térmica aislada")
    variants = []
    if with_alternatives:
        from pricing.repository import admin_write
        with as_user(actor):
            cost_list=rows("SELECT id FROM public.cost_lists WHERE org_id=%s AND currency='CLP' ORDER BY valid_from DESC,id",[org])[0]
            for sku,ug,cost,gas in (("THERMAL-CHEAP","1.1","1000","AIR"),("THERMAL-EXPENSIVE","0.9","2000","ARGON")):
                product=deepcopy(glass_product)
                product["name"]=f"Prueba aislada {sku.lower()} · sin certificación"
                product["composition"]["layers"][0]["plies"][0].update(type="LOW_E",coating_face=2)
                product["composition"]["layers"][1]["gas"]=gas
                new_id=uuid4()
                with catalog_backend():
                    one("INSERT INTO public.glass_purchase_mappings SELECT (jsonb_populate_record(NULL::public.glass_purchase_mappings,%s::jsonb)).* RETURNING id",
                        [json_text({**mapping,"id":new_id,"version":1,"technical_sku":sku,"purchasing_sku":sku,"glass_spec":"4-16-4"})])
                    one("INSERT INTO public.catalog_glass_compositions(org_id,system_id,mapping_id,status,product,legacy_spec) VALUES(%s,%s,%s,'PARSED',%s::jsonb,'4-16-4') RETURNING id",
                        [org,system_id,new_id,json_text(product)])
                with commercial_backend():
                    exists=rows("SELECT id FROM public.cost_list_items WHERE cost_list_id=%s AND sku=%s",[cost_list["id"],sku])
                if not exists:
                    admin_write("cost-items",org,{"cost_list_id":cost_list["id"],"sku":sku,"item_type":"FIXTURE","unit":"M2","unit_cost":Decimal(cost)},"Prueba térmica aislada")
                variants.append((sku,ug,product))
    tree = service.decoded(one("SELECT parametric_tree FROM public.project_positions WHERE id=%s", [position_id])["parametric_tree"])
    tree["glass_spec"] = "4-16-4"
    tree["glass_article_sku"] = "THERMAL-BASE"
    one("UPDATE public.project_positions SET system_id=%s,parametric_tree=%s::jsonb WHERE id=%s RETURNING id", [system_id, json_text(tree), position_id])
    with as_user(actor):
        system = thermal._system(org, system_id)
        params = SystemParamsRepository().load_visible(system_id, org)
        for table, row, fields in [("profile_systems", system, ["rebate_depth_mm", "glass_clearance_white_mm"]),
            *[("profile_articles", row, ["face_width_mm"]) for row in rows(
                "SELECT id,face_width_mm FROM public.profile_articles WHERE system_id=%s AND role='FRAME'", [system_id])]]:
            for field in fields:
                declared = evidence.declare_evidence(org_id=org, actor_id=actor, values={
                    "authority_table":table, "row_id":row["id"], "field_name":field, "value_text":str(row[field]),
                    "unit":"mm", "scope":"SYSTEM", "source_document":"Caso matemático aislado; no usar en obra",
                    "source_page":1, "source_url":"https://example.test/thermal", "extraction_method":"MANUAL",
                    "canonical_value":str(row[field]), "original_value":str(row[field]),
                })
                evidence.review_evidence(org_id=org, evidence_id=UUID(declared["id"]), actor_id=actor, state="REVIEWED")
        row = service.position_row(org, position_id)
        from documents.service import _position_calculations
        calculations, _ = _position_calculations(tree=service.decoded(row["parametric_tree"]),
            width_mm=row["width_mm"], height_mm=row["height_mm"], color=row["color_interior"],
            params=params, system_id=system_id, org_id=org)
        geometry = thermal.thermal_geometry(calculations[0][1])
        catalog = thermal.catalog_reports(org, system_id)
        glass = next(item for item in catalog["glasses"] if item["sku"] == geometry.panes[0].glass_sku)
        common = {"profile_skus":list(geometry.profile_skus), "opening_types":["FIXED"],
            "min_width_mm":"1000", "max_width_mm":"1000", "min_height_mm":"1000", "max_height_mm":"1000",
            "source_document":"Prueba aislada sin certificado · no usar en obra", "source_url":"https://example.test/thermal",
            "source_page":"Caso manual 1", "laboratory":"Fixture de prueba, sin acreditación real",
            "report_date":"2026-01-01", "valid_until":"2027-12-31", "standard":"ISO10077-1 · prueba",
            "applicability":"Solo fixture de aceptación; no acredita productos ni edificios", "synthetic":False}
        inputs = [{**common,"kind":"FRAME","uf":"1.5"},
            {**common,"kind":"GLASS","glass_sku":glass["sku"],"ug":baseline_ug,"solar_factor":"0.55"},
            {**common,"kind":"SPACER","glass_sku":glass["sku"],"spacer_code":glass["spacer"],"psi_g":"0.05"},
            {**common,"kind":"PERFORMANCE","source_position_id":str(position_id),"air_class":3,"air_pressure_pa":"100","water_class":"7A","wind_class":"C3",
             "standard":"NCh3296/NCh3297 · prueba", "laboratory_registration":"Registro simulado solo para tests"}]
        reports = []
        for values in inputs:
            serializer = ThermalAuthoritySerializer(data=values)
            assert serializer.is_valid(), serializer.errors
            report = thermal.declare_report(org, system_id, actor, serializer.validated_data)
            thermal.review_report(org, system_id, UUID(report["id"]), actor, "REVIEWED")
            reports.append(report)
        for sku,ug,product in variants:
            alternate=deepcopy(tree)
            alternate.update(glass_article_sku=sku,glass_product=product)
            with commercial_backend():
                one("UPDATE public.project_positions SET parametric_tree=%s::jsonb WHERE id=%s RETURNING id",[json_text(alternate),position_id])
            for values in (
                {**common,"kind":"GLASS","glass_sku":sku,"ug":ug,"solar_factor":"0.5"},
                {**common,"kind":"SPACER","glass_sku":sku,"spacer_code":"WARM_EDGE","psi_g":"0.05"},
                {**inputs[-1]},
            ):
                serializer=ThermalAuthoritySerializer(data=values)
                assert serializer.is_valid(),serializer.errors
                source=thermal.declare_report(org,system_id,actor,serializer.validated_data)
                thermal.review_report(org,system_id,UUID(source["id"]),actor,"REVIEWED")
        with commercial_backend():
            one("UPDATE public.project_positions SET parametric_tree=%s::jsonb WHERE id=%s RETURNING id",[json_text(tree),position_id])
        values = {"zone":"F","zone_source":"Zonificación de fixture, no es una obra","use":"HEALTH" if with_alternatives else "RESIDENTIAL",
            "walls_m2":{"N":"10","E":"10","S":"10","W":"10"}, "exposed_wall_area_m2":"40",
            "wall_source":"Plano de prueba aislada", "envelope_complete":True,"regulatory_scope_confirmed":True,
            "regulatory_calculation_source":"Memoria simulada de prueba", "regulatory_method_confirmed":True,
            "positions":[{"position_id":str(position_id),"orientation":"N","surface":"WALL"}], "include_doc01":True}
        serializer = ThermalInputSerializer(data=values)
        assert serializer.is_valid(), serializer.errors
        report = thermal.save_inputs(org, project_id, actor, serializer.validated_data, None)
    return project_id, position_id, system_id, reports, report


def freeze_reviewed_case(org,actor,project,position):
    """Price and seal the current evaluated fixture through public services."""
    from pricing.service import preview,apply_operation
    from backend.tests.integration.test_shot09_documentary import _tenant
    from documents.service import prepare_documentary_inputs,save_documentary_inputs,freeze_revision_a
    from documents.repository import documentary_backend
    from backend.tests.integration.mounting_fixture import confirm_fixture_measurements
    with as_user(actor):
        row=service.position_row(org,position)
        service.save_position(org,project,{"location_tag":"Prueba térmica · fachada Norte","quantity":row["quantity"],
            "expected_updated_at":row["updated_at"],"design":{"system_id":row["system_id"],
                "nominal_width_mm":row["width_mm"],"nominal_height_mm":row["height_mm"],
                "color":row["color_interior"],"parametric_tree":service.decoded(row["parametric_tree"])}},position_id=position)
        confirm_fixture_measurements(org,position)
        with commercial_backend():
            operation=preview(org,_tenant(org,"OWNER"),{"project_id":project,"pricing_mode":"COST_PLUS_MARGIN",
                "currency":"CLP","effective_date":date(2026,10,11),"context_code":"DEFAULT",
                "discount_pct":Decimal(0),"target_margin":Decimal("0.35"),"segment":"RETAIL",
                "confirmed":False,"reason":"Prueba térmica aislada","_actor_id":actor})
            apply_operation(org,actor,"OWNER",UUID(operation["id"]),"Prueba térmica aislada",False)
        with documentary_backend():
            prepared=prepare_documentary_inputs(org_id=org,project_id=project)
            keys=("position_id","calculation_hash","location_tag","manufacturing_placement_policy_id",
                "handle_requirement_policy_id","reinforcement_cut_policy_id","workshop_annotations",
                "structural_inputs","glass_polishing","handle_intents","accessory_schedule","legacy_handle_migration_confirmed")
            data={"payment_terms":"Solo prueba aislada, sin oferta comercial","quotation_valid_until":date(2026,10,26),
                "positions":[{key:item[key] for key in keys} for item in prepared["positions"]]}
            for item,source in zip(data["positions"],prepared["positions"],strict=True):
                for field,options in (("manufacturing_placement_policy_id","placement_options"),
                    ("handle_requirement_policy_id","handle_options"),("reinforcement_cut_policy_id","reinforcement_options")):
                    item[field]=source[options][0]["id"]
            save_documentary_inputs(org_id=org,actor_id=actor,project_id=project,data=data)
        return freeze_revision_a(org_id=org,actor_id=actor,project_id=project,pricing_operation_id=UUID(operation["id"]),confirmed=True)
