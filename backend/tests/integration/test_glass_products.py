"""D02 authority, publication, tenant boundaries and sealed supplier orders."""
from copy import deepcopy
from datetime import date
from decimal import Decimal as D
from uuid import UUID, uuid4
from urllib.parse import parse_qs, urlparse

import pytest
from django.db import DatabaseError, transaction

from authentication.errors import ContractAPIException
from authentication.rls import authenticated_rls_context
from catalogs import glass
from catalogs.demo_glass import demo_glass_product, demo_safety_rules
from backend.tests.catalog_interchange_fixture import candidate
from backend.tests.integration.test_catalog_interchange import imported
from backend.tests.integration.test_shot09_documentary import (
    documentary_tenant as documentary_tenant, as_user, _seed_project, _freeze, _tenant,
)
from backend.tests.integration.test_shot10_catalog_api import (
    real_rows as real_rows, database_access as database_access, client_for, set_role,
)
from ingest import catalog_review
from documents.service import revision_snapshot
from pricing.repository import rows, one, commercial_backend
from pricing.service import preview, apply_operation, position_cost
from production.glass_orders import glass_order, glass_csv
from production.service import release_production
from projects.serializers import PositionWriteSerializer
from projects.service import create_project, save_position, position_row, position_public
from documents.service import prepare_documentary_inputs, save_documentary_inputs
from pricing.repository import admin_write

pytestmark = pytest.mark.rls_integration


@pytest.mark.parametrize("direction", ["INWARD", "OUTWARD"])
def test_structured_door_safety_covers_preview_save_and_repricing(real_rows, direction):
    org = real_rows.organizations["A"]
    set_role(real_rows, "ESTIMATOR")
    client = client_for(real_rows)
    system = one("SELECT id FROM public.profile_systems WHERE code='DEMO_PUERTA_70' AND version=3")["id"]
    options = client.get(f"/api/v1/projects/design-options/{system}/")
    assert options.status_code == 200, options.data
    choice = next(item for item in options.data["glass_specs"] if item["sku"].endswith("-GLASS-LOWE"))
    node = {"id": "B1", "type": "BAY", "opening_use": "DOOR",
        "opening": {"movement": "TURN", "hinge_side": "LEFT", "direction": direction,
            "leaf_role": "SINGLE", "fixed_in_sash": False},
        "glass_article_sku": choice["sku"], "glass_spec": choice["spec"],
        "glass_product": choice["product"], "glass_thickness_mm": choice["total_thickness_mm"]}
    project = client.post("/api/v1/projects/", {"name": "D03 sourced door safety",
        "client_name": "Synthetic fixture"}, format="json")
    assert project.status_code == 201, project.data
    payload = {"quantity": 1, "location_tag": "Puerta vidriada", "design": {
        "system_id": str(system), "nominal_width_mm": "1000", "nominal_height_mm": "2200",
        "color": "WHITE", "parametric_tree": node}}
    path = f"/api/v1/projects/{project.data['id']}/positions/"
    saved = client.post(path, payload, format="json")
    assert saved.status_code == 201, saved.data

    set_role(real_rows, "WORKSHOP_MANAGER")
    rules_path = "/api/v1/catalogs/glass/rules/"
    current = client.get(rules_path)
    rule = {**demo_safety_rules()[0], "mandatory": True}
    configured = client.put(rules_path, {"items": [rule]}, format="json",
        HTTP_IF_MATCH='"' + current.data["revision"] + '"')
    assert configured.status_code == 200, configured.data
    piece = saved.data["bom"]["glasses"][0]
    preview_payload = {"system_id": str(system), "product": choice["product"],
        "width_mm": piece["width_mm"], "height_mm": piece["height_mm"],
        "opening_use": "DOOR", "opening_type": "FIXED"}
    report = client.post("/api/v1/catalogs/glass/preview/", preview_payload, format="json")
    assert report.status_code == 200, report.data
    assert any(item["blocking"] and item["code"] == rule["code"] for item in report.data["findings"])
    legacy_preview = {**preview_payload, "opening_type": "DOOR_ENTRY"}
    legacy_preview.pop("opening_use")
    legacy = client.post("/api/v1/catalogs/glass/preview/", legacy_preview, format="json")
    assert legacy.status_code == 200, legacy.data
    assert any(item["blocking"] and item["code"] == rule["code"] for item in legacy.data["findings"])
    control = client.post("/api/v1/catalogs/glass/preview/", {**preview_payload,
        "opening_use": "WINDOW", "opening_type": "FIXED"}, format="json")
    assert control.status_code == 200, control.data
    assert not any(item["code"] == rule["code"] for item in control.data["findings"])

    set_role(real_rows, "ESTIMATOR")
    rejected = client.post(path, payload, format="json")
    assert rejected.status_code == 422, rejected.data
    assert rejected.data["error"]["code"] == "glass_rule_required"

    class Repo:
        org_id = org

        def cost(self, *_):
            pytest.fail("Safety must block before any price is computed.")

    with authenticated_rls_context(real_rows.tokens["A"].claims):
        position = position_row(org, saved.data["id"])
        with pytest.raises(ContractAPIException) as error:
            position_cost(Repo(), position, {})
        assert error.value.contract_code == "glass_rule_required"


@pytest.mark.parametrize("sku,net_mm", [("DEMO_60-VIDRIO-4", "4.00"),
    ("DEMO_60-VIDRIO-4-16-4", "8.00")])
def test_post_d02_notation_uses_the_same_authority_on_discovery_and_save(real_rows, sku, net_mm):
    set_role(real_rows, "ESTIMATOR")
    client = client_for(real_rows)
    system = one("SELECT id FROM public.profile_systems WHERE code='DEMO_60' AND version=3")["id"]
    options = client.get(f"/api/v1/projects/design-options/{system}/")
    assert options.status_code == 200, options.data
    choice = next(item for item in options.data["glass_specs"] if item["sku"] == sku)
    project = client.post("/api/v1/projects/", {"name": "D03 historical glass notation",
        "client_name": "Synthetic fixture"}, format="json")
    assert project.status_code == 201, project.data
    payload = {"quantity": 1, "location_tag": "Vidrio del catálogo", "design": {
        "system_id": str(system), "nominal_width_mm": "1000", "nominal_height_mm": "1000",
        "color": "WHITE", "parametric_tree": {"id": "B1", "type": "BAY", "opening_type": "FIXED",
            "glass_article_sku": sku, "glass_product": choice["product"], "glass_spec": choice["spec"],
            "glass_thickness_mm": choice["total_thickness_mm"], "sill_height_mm": "900"}}}
    path = f"/api/v1/projects/{project.data['id']}/positions/"
    saved = client.post(path, payload, format="json")
    assert saved.status_code == 201, saved.data
    reopened = client.get(f"/api/v1/positions/{saved.data['id']}/")
    assert reopened.status_code == 200, reopened.data
    assert reopened.data["design"]["parametric_tree"]["glass_product"] == choice["product"]
    assert reopened.data["bom"]["glasses"][0]["thickness_net_mm"] == net_mm
    forged = deepcopy(payload)
    forged["design"]["parametric_tree"]["glass_product"]["properties"]["ug"] = {
        "value": "1.1", "source": "Undeclared synthetic claim"}
    rejected = client.post(path, forged, format="json")
    assert rejected.status_code == 409, rejected.data
    assert rejected.data["error"]["code"] == "glass_authority_changed"


def test_structured_recipe_survives_save_price_freeze_and_supplier_order(documentary_tenant):
    org, _, users, _ = documentary_tenant
    owner = users["OWNER"]
    # Reuse only the pre-existing commercial fixture, never its legacy design.
    _seed_project(org, owner)
    with as_user(owner):
        system = one("SELECT id FROM public.profile_systems WHERE code='DEMO_60' AND version=2")["id"]
        product = next(item for item in glass.load_products(system, org)
            if item["technical_sku"] == "DEMO_60-GLASS-SAFE")["resolved_product"].model_dump(mode="json")
        cost_list = one("SELECT id FROM public.cost_lists WHERE org_id=%s", [org])["id"]
        required = rows("SELECT commercial_sku AS sku,purchase_unit AS unit FROM public.profile_purchase_mappings "
            "WHERE profile_article_id IN (SELECT id FROM public.profile_articles WHERE system_id=%s) "
            "UNION SELECT commercial_sku,purchase_unit FROM public.reinforcement_articles WHERE system_id=%s "
            "UNION SELECT technical_sku,'M2' FROM public.glass_purchase_mappings WHERE system_id=%s", [system, system, system])
        required += [{"sku": value, "unit": unit} for key, unit in (("tempering_sku", "M2"),
            ("polishing_sku", "M"), ("drilling_sku", "EA"), ("bars_per_m_sku", "M"), ("bars_per_crossing_sku", "EA"))
            if (value := product["billing"].get(key))]
        for item in required:
            if not rows("SELECT id FROM public.cost_list_items WHERE cost_list_id=%s AND sku=%s", [cost_list, item["sku"]]):
                admin_write("cost-items", org, {"cost_list_id": cost_list, "sku": item["sku"], "unit": item["unit"],
                    "item_type": "FIXTURE", "unit_cost": D("100")}, "D02 reviewed synthetic rate")
        project = create_project(org, owner, {"name": "D02 structured round trip", "client_name": "Fixture",
            "client_rut": "1-9", "client_email": "client@example.test", "client_phone": "+56900000000", "delivery_address": "Valdivia"})
        payload = {"quantity": 3, "location_tag": "Dormitorio", "design": {"system_id": str(system),
            "nominal_width_mm": "850", "nominal_height_mm": "1200", "color": "WHITE", "parametric_tree": {
                "id": "B1", "type": "BAY", "opening_type": "FIXED", "glass_article_sku": "DEMO_60-GLASS-SAFE",
                "glass_product": product, "glass_spec": "3+3 PVB 0,38 / 13,62 aire / 4 templado", "glass_thickness_mm": "24",
                "sill_height_mm": "900", "glass_processing": {"polished_edges": ["TOP"], "holes": 2,
                    "bars_vertical": 1, "bars_horizontal": 1}}}}
        serializer = PositionWriteSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        position = save_position(org, project["id"], serializer.validated_data)
        reopened = position_public(position_row(org, position["id"]))
        assert reopened["design"]["parametric_tree"]["glass_product"] == product
        assert reopened["bom"] == position["bom"]
        prepared = prepare_documentary_inputs(org_id=org, project_id=project["id"])["positions"][0]
        save_documentary_inputs(org_id=org, actor_id=owner, project_id=project["id"], data={
            "payment_terms": "50 % anticipo y saldo contra entrega", "quotation_valid_until": date(2026, 10, 25), "positions": [{
                "position_id": position["id"], "calculation_hash": prepared["calculation_hash"], "location_tag": "Dormitorio",
                "manufacturing_placement_policy_id": prepared["placement_options"][0]["id"],
                "handle_requirement_policy_id": prepared["handle_options"][0]["id"],
                "reinforcement_cut_policy_id": prepared["reinforcement_options"][0]["id"],
                "workshop_annotations": prepared["workshop_suggestions"], "structural_inputs": [],
                "glass_polishing": prepared["polishing_suggestions"], "handle_intents": [],
                "accessory_schedule": {"schema_version": 1, "coverage": "NONE_REQUIRED", "items": []},
                "legacy_handle_migration_confirmed": True}]})
        with commercial_backend():
            priced = preview(org, _tenant(org, "OWNER"), {"project_id": project["id"], "pricing_mode": "COST_PLUS_MARGIN", "currency": "CLP",
                "effective_date": date(2026, 9, 10), "context_code": "DEFAULT", "discount_pct": D("0"), "target_margin": D("0.35"),
                "segment": "RETAIL", "confirmed": False, "reason": "D02 reviewed price", "_actor_id": owner})
            apply_operation(org, owner, "OWNER", UUID(priced["id"]), "D02 apply", False)
        frozen = _freeze(org, owner, project["id"], UUID(priced["id"]))
        _, snapshot = revision_snapshot(org_id=org, version_id=UUID(frozen["id"]))
        assert snapshot["positions"][0]["parametric_tree"]["glass_product"] == product
    with as_user(users["WORKSHOP_MANAGER"]):
        released = release_production(org_id=org, actor_id=users["WORKSHOP_MANAGER"], version_id=UUID(frozen["id"]))
        report = glass_order(org_id=org, order_ids=[UUID(item["id"]) for item in released["orders"]], app_url="https://example.test")
    piece = snapshot["bom"][0]["engine_result"]["glasses"][0]
    row = report["rows"][0]
    assert D(row["width_mm"]) == D(piece["width_mm"]) and D(row["height_mm"]) == D(piece["height_mm"])
    assert row["processing"] == payload["design"]["parametric_tree"]["glass_processing"]
    assert row["quantity"] == 3 and len(report["labels"]) == 3
    assert "PVB" in row["composition"] and "templado" in row["composition"]


def test_variant_on_global_series_is_immutable_and_cannot_be_forged(real_rows):
    set_role(real_rows, "WORKSHOP_MANAGER")
    client = client_for(real_rows)
    system = one("SELECT id FROM public.profile_systems WHERE code='DEMO_60' AND version=2")["id"]
    product = demo_glass_product("DEMO_60", "LOWE").model_dump(mode="json")
    payload = {"system_id": str(system), "technical_sku": "TEST-D02-VARIANT", "purchasing_sku": "BUY-D02",
        "manufacturer_name": "Proveedor de prueba", "version": 1, "product": product, "confirmed": True}
    response = client.post("/api/v1/catalogs/glass/variants/", payload, format="json")
    assert response.status_code == 201, response.data
    persisted = response.data["product"]
    tree = {"id": "B1", "type": "BAY", "glass_article_sku": payload["technical_sku"], "glass_product": persisted}
    org = real_rows.organizations["A"]
    with authenticated_rls_context(real_rows.tokens["A"].claims):
        glass.validate_design_products(org, system, tree)
        stripped = deepcopy(tree)
        stripped.pop("glass_product")
        with pytest.raises(ContractAPIException) as error:
            glass.validate_design_products(org, system, stripped)
        assert error.value.contract_code == "glass_authority_required"
        forged = deepcopy(tree)
        forged["glass_product"]["properties"]["ug"] = {"value": "1.1", "source": "Ficha inventada"}
        with pytest.raises(ContractAPIException) as error:
            glass.validate_design_products(org, system, forged)
        assert error.value.contract_code == "glass_authority_changed"
        forged["glass_product"]["authority_id"] = "not-an-id"
        with pytest.raises(ContractAPIException) as error:
            glass.validate_design_products(org, system, forged)
        assert error.value.status_code == 400
    with authenticated_rls_context(real_rows.tokens["B"].claims):
        assert not rows("SELECT id FROM public.catalog_glass_compositions WHERE mapping_id=%s", [response.data["mapping_id"]])
        with pytest.raises(ContractAPIException) as error:
            glass.validate_design_products(real_rows.organizations["B"], system, tree)
        assert error.value.contract_code == "glass_authority_required"
    replay = client.post("/api/v1/catalogs/glass/variants/", payload, format="json")
    assert replay.status_code == 409
    set_role(real_rows, "ESTIMATOR")
    payload["technical_sku"] += "-DENIED"
    assert client.post("/api/v1/catalogs/glass/variants/", payload, format="json").status_code == 403


def test_preview_official_and_demo_rules_and_write_permissions(real_rows):
    set_role(real_rows, "WORKSHOP_MANAGER")
    client = client_for(real_rows)
    path = "/api/v1/catalogs/glass/rules/"
    current = client.get(path)
    rule = demo_safety_rules()[0]
    replaced = client.put(path, {"items": [rule]}, format="json", HTTP_IF_MATCH='"' + current.data["revision"] + '"')
    assert replaced.status_code == 200, replaced.data
    assert client.put(path, {"items": []}, format="json", HTTP_IF_MATCH='"' + current.data["revision"] + '"').status_code == 409
    system = one("SELECT id FROM public.profile_systems WHERE code='DEMO_60' AND version=2")["id"]
    payload = {"system_id": str(system), "product": demo_glass_product("DEMO_60", "LOWE").model_dump(mode="json"),
        "width_mm": "700", "height_mm": "1800", "opening_type": "DOOR_ENTRY"}
    report = client.post("/api/v1/catalogs/glass/preview/", payload, format="json")
    assert report.status_code == 200, report.data
    warning = next(value for value in report.data["findings"] if value["code"] == rule["code"])
    assert not warning["blocking"] and warning["source"] == rule["source"]
    assert "DEMO_60-GLASS-SAFE" in report.data["alternative_skus"]
    official = {**rule, "mandatory": True, "synthetic": False, "source": "Norma aportada por la organización"}
    result = client.put(path, {"items": [official]}, format="json", HTTP_IF_MATCH='"' + replaced.data["revision"] + '"')
    assert result.status_code == 200
    payload["product"] = demo_glass_product("DEMO_60", "SAFE").model_dump(mode="json")
    report = client.post("/api/v1/catalogs/glass/preview/", payload, format="json")
    assert any(value["blocking"] and value["code"] == rule["code"] for value in report.data["findings"])
    assert not report.data["alternative_skus"]
    set_role(real_rows, "ESTIMATOR")
    assert client.put(path, {"items": []}, format="json").status_code == 403
    assert client.get(path).status_code == 200
    set_role(real_rows, "INSTALLER")
    assert client.post("/api/v1/catalogs/glass/preview/", payload, format="json").status_code == 403


def test_legacy_notation_cannot_bypass_mandatory_sidelight_rule(real_rows):
    set_role(real_rows, "WORKSHOP_MANAGER")
    client = client_for(real_rows)
    path = "/api/v1/catalogs/glass/rules/"
    current = client.get(path)
    rule = {**demo_safety_rules()[1], "mandatory": True}
    response = client.put(path, {"items": [rule]}, format="json",
        HTTP_IF_MATCH='"' + current.data["revision"] + '"')
    assert response.status_code == 200, response.data
    system = one("SELECT id FROM public.profile_systems WHERE code='DEMO_60' AND version=2")["id"]
    set_role(real_rows, "ESTIMATOR")
    project = client.post("/api/v1/projects/", {"name": "Mandatory legacy safety", "client_name": "Fixture"}, format="json")
    assert project.status_code == 201, project.data
    position = client.post(f"/api/v1/projects/{project.data['id']}/positions/", {
        "location_tag": "Lateral de puerta", "quantity": 1,
        "design": {"system_id": str(system), "nominal_width_mm": "1000.00", "nominal_height_mm": "1000.00", "color": "WHITE",
            "parametric_tree": {"id": "B1", "type": "BAY", "opening_type": "FIXED", "is_sidelight": True,
                "glass_article_sku": "DEMO_60-VIDRIO-4-16-4", "glass_spec": "4-16-4", "glass_thickness_mm": "24.00"}}}, format="json")
    assert position.status_code == 422, position.data
    assert position.data["error"]["code"] == "glass_rule_required"
    reopened = client.get(f"/api/v1/projects/{project.data['id']}/")
    assert reopened.status_code == 200 and not reopened.data["positions"]


def test_rule_only_ingestion_retains_history_and_undo(documentary_tenant):
    org, _, users, _ = documentary_tenant
    actor = users["OWNER"]
    with as_user(actor):
        original = glass.rules_snapshot(org)
        saved = glass.replace_safety_rules(org, actor, [demo_safety_rules()[1]], '"' + original["revision"] + '"')
    source = candidate("Reglas de vidrio", {**demo_safety_rules()[0], "required_classes": ["A", "B", "C"]}, key="rule", row=5, method="MANUAL")
    import_id, items = imported(org, actor, [source])
    with as_user(actor):
        diff = catalog_review.preview(org_id=org, import_id=import_id, items=items)
        assert not diff["errors"], diff["errors"]
        result = catalog_review.publish(org_id=org, actor_id=actor, import_id=import_id, items=items, review_token=diff["review_token"])
        assert not result["errors"]
        assert {item["code"] for item in glass.rules_snapshot(org)["items"]} == {"DEMO-DOOR", "DEMO-SIDELIGHT"}
        catalog_review.undo_publication(org_id=org, actor_id=actor, import_id=import_id)
        assert glass.rules_snapshot(org)["items"] == saved["items"]
        assert len(rows("SELECT id FROM public.glass_safety_rule_revisions WHERE org_id=%s", [org])) == 3
    with pytest.raises(DatabaseError), transaction.atomic():
        rows("UPDATE public.glass_safety_rule_revisions SET payload='[]' WHERE org_id=%s RETURNING id", [org])


def test_twelve_work_orders_read_the_frozen_bom_and_qr_targets(documentary_tenant):
    org, _, users, _ = documentary_tenant
    owner = users["OWNER"]
    project, first, _ = _seed_project(org, owner, apply_pricing=False)
    for index in range(2, 13):
        position = uuid4()
        one("INSERT INTO public.project_positions SELECT (jsonb_populate_record(NULL::public.project_positions, "
            "to_jsonb(p)||jsonb_build_object('id',%s::text,'position_index',%s,'quantity',2,'location_tag',%s))).* "
            "FROM public.project_positions p WHERE id=%s RETURNING id", [position, index, f"Dormitorio {index}", first])
        one("INSERT INTO public.position_documentary_inputs SELECT (jsonb_populate_record(NULL::public.position_documentary_inputs, "
            "to_jsonb(p)||jsonb_build_object('id',gen_random_uuid(),'position_id',%s::text))).* "
            "FROM public.position_documentary_inputs p WHERE position_id=%s RETURNING position_id", [position, first])
    with as_user(owner), commercial_backend():
        priced = preview(org, _tenant(org, "OWNER"), {"project_id": project, "pricing_mode": "COST_PLUS_MARGIN", "currency": "CLP",
            "effective_date": date(2026, 9, 10), "context_code": "DEFAULT", "discount_pct": D("0"), "target_margin": D("0.35"),
            "segment": "RETAIL", "confirmed": False, "reason": "D02 exact batch", "_actor_id": owner})
        apply_operation(org, owner, "OWNER", UUID(priced["id"]), "D02 reviewed apply", False)
    frozen = _freeze(org, owner, project, UUID(priced["id"]))
    with as_user(users["WORKSHOP_MANAGER"]):
        release = release_production(org_id=org, actor_id=users["WORKSHOP_MANAGER"], version_id=UUID(frozen["id"]))
        order_ids = [UUID(item["id"]) for item in release["orders"]]
        assert len(order_ids) == 12
        report = glass_order(org_id=org, order_ids=order_ids, app_url="https://example.test")
        _, snapshot = revision_snapshot(org_id=org, version_id=UUID(frozen["id"]))
    assert len(report["rows"]) == 12 and len(report["labels"]) == 24
    assert {row["position_index"] for row in report["rows"]} == set(range(1, 13))
    by_position = {str(item["position_id"]): item for item in snapshot["bom"]}
    positions = {item["position_index"]: item for item in snapshot["positions"]}
    for row in report["rows"]:
        bom = by_position[str(positions[row["position_index"]]["id"])]
        glass_piece = bom["engine_result"]["glasses"][row["piece_index"] - 1]
        assert D(row["width_mm"]) == D(glass_piece["width_mm"])
        assert D(row["height_mm"]) == D(glass_piece["height_mm"])
        assert row["quantity"] == bom["quantity"]
    facts = {str(item["infill_id"]) for fact in snapshot["manufacturing"] for item in fact["infills"] if item["kind"] == "GLASS"}
    assert all(parse_qs(urlparse(label["link"]).query)["piece"][0] in facts for label in report["labels"])
    assert glass_csv(report).startswith(b"\xef\xbb\xbf")
