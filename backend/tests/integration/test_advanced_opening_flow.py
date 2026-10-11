"""D08 sourced recipes save, price and seal under real tenant permissions."""
from datetime import date
from decimal import Decimal as D
from uuid import UUID

import pytest

from backend.tests.integration.test_shot09_documentary import (
    documentary_tenant as documentary_tenant, as_user, _seed_project, _tenant,
)
from catalogs.glass import load_products
from documents.service import prepare_documentary_inputs, save_documentary_inputs, revision_snapshot, freeze_revision_a
from engine.tests.advanced_cases import advanced_node, advanced_typologies
from pricing.repository import admin_write, commercial_backend, one, rows
from pricing.service import preview, apply_operation
from projects.serializers import PositionWriteSerializer
from projects.service import create_project, save_position, position_row, position_public

pytestmark = pytest.mark.rls_integration


def test_fourteen_advanced_recipes_save_price_and_seal_without_basic_aliases(documentary_tenant):
    org, other_org, users, _ = documentary_tenant
    owner = users["OWNER"]
    _seed_project(org, owner)
    with as_user(owner):
        cost_list = one("SELECT id FROM cost_lists WHERE org_id=%s", [org])["id"]
        required = rows("SELECT sku,unit FROM catalog_demo_prices WHERE system_id IN (SELECT id FROM profile_systems WHERE version=8) "
            "UNION SELECT p.commercial_sku,p.purchase_unit FROM profile_purchase_mappings p JOIN profile_articles a ON a.id=p.profile_article_id "
            "JOIN profile_systems s ON s.id=a.system_id WHERE s.version=8 "
            "UNION SELECT a.commercial_sku,a.purchase_unit FROM reinforcement_articles a JOIN profile_systems s ON s.id=a.system_id WHERE s.version=8")
        for item in required:
            if not rows("SELECT id FROM cost_list_items WHERE cost_list_id=%s AND sku=%s", [cost_list, item["sku"]]):
                admin_write("cost-items", org, {"cost_list_id": cost_list, "sku": item["sku"], "unit": item["unit"],
                    "item_type": "FIXTURE", "unit_cost": D("100")}, "D08 declared synthetic rates, no certificate")
        project = create_project(org, owner, {"name": "D08 14 recetas DEMO", "client_name": "Fixture",
            "client_rut": "1-9", "client_email": "client@example.test", "client_phone": "+56900000000", "delivery_address": "Valdivia"})
        originals = {}
        for code, recipe in advanced_typologies():
            node = advanced_node(code, recipe)
            system = one("SELECT id FROM profile_systems WHERE code=%s AND version=8", [code])["id"]
            glass = next(row for row in load_products(system, org) if row["resolved_product"] is not None)
            tree = node.model_dump(mode="json", exclude_none=True)
            width, height = tree.pop("width_mm"), tree.pop("height_mm")
            tree.update(glass_article_sku=glass["technical_sku"], glass_product=glass["resolved_product"].model_dump(mode="json"), sill_height_mm="900")
            serializer = PositionWriteSerializer(data={"location_tag": code+"/"+recipe, "quantity": 1, "design": {
                "system_id": str(system), "nominal_width_mm": width, "nominal_height_mm": height, "color": "WHITE", "parametric_tree": tree}})
            serializer.is_valid(raise_exception=True)
            position = save_position(org, project["id"], serializer.validated_data)
            assert position_public(position_row(org, position["id"]))["bom"] == position["bom"]
            assert all(leaf["advanced"]["recipe_code"] == recipe for leaf in position["bom"]["opening_leaves"])
            assert not position["design"]["parametric_tree"].get("opening_type")
            originals[str(position["id"])] = position["bom"]
        prepared = prepare_documentary_inputs(org_id=org, project_id=project["id"])
        inputs = []
        for position in prepared["positions"]:
            annotations = {}
            for row in position["workshop_suggestions"]:
                key = (row["bay_id"], row.get("leaf_id"))
                annotations[key] = {**annotations.get(key, {}), **{k: v for k, v in row.items() if v is not None}}
            inputs.append({"position_id": position["position_id"], "calculation_hash": position["calculation_hash"], "location_tag": position["location_tag"],
                "manufacturing_placement_policy_id": position["placement_options"][0]["id"], "handle_requirement_policy_id": position["handle_options"][0]["id"],
                "reinforcement_cut_policy_id": position["reinforcement_options"][0]["id"], "workshop_annotations": list(annotations.values()),
                "structural_inputs": [{"target_id": span["target_id"], "required_ix_cm4": "1.00", "structural_basis": "DEMO · carga sintética D08; no certificado de obra"} for span in position["workshop_targets"]["spans"]],
                "glass_polishing": position["polishing_suggestions"], "handle_intents": [], "accessory_schedule": {"schema_version": 1, "coverage": "NONE_REQUIRED", "items": []},
                "legacy_handle_migration_confirmed": True})
        save_documentary_inputs(org_id=org, actor_id=owner, project_id=project["id"], data={"payment_terms": "Anticipo 50 %",
            "quotation_valid_until": date(2026, 10, 25), "positions": inputs})
        with commercial_backend():
            priced = preview(org, _tenant(org, "OWNER"), {"project_id": project["id"], "pricing_mode": "COST_PLUS_MARGIN", "currency": "CLP", "effective_date": date(2026, 10, 6),
                "context_code": "DEFAULT", "discount_pct": D("0"), "target_margin": D("0.35"), "segment": "RETAIL", "confirmed": False, "reason": "D08 reviewed price", "_actor_id": owner})
            apply_operation(org, owner, "OWNER", UUID(priced["id"]), "D08 apply", False)
        from backend.tests.integration.mounting_fixture import confirm_fixture_measurements
        from documents.service import _canonical_bom_transport
        from pricing.service import decoded
        snapshot = decoded(one("SELECT input_snapshot FROM pricing_operations WHERE org_id=%s AND id=%s", [org, priced["id"]])["input_snapshot"])
        for position in snapshot["positions"]:
            original = originals[str(position["position_id"])]
            stored = {key: value for key, value in original.items() if key != "calculation_hash"}
            assert position["bom"] == _canonical_bom_transport(stored)
        for pos in rows('SELECT id FROM project_positions WHERE org_id=%s AND project_id=%s', [org, project['id']]):
            confirm_fixture_measurements(org, pos['id'])
        frozen = freeze_revision_a(org_id=org, actor_id=owner, project_id=project["id"], pricing_operation_id=UUID(priced["id"]), confirmed=True, allow_incomplete_workshop=True)
        _, snapshot = revision_snapshot(org_id=org, version_id=UUID(frozen["id"]))
        assert len(snapshot["positions"]) == 14
        for position in snapshot["positions"]:
            assert position["opening_leaves"] == originals[str(position["id"])]["opening_leaves"]
        assert other_org != org
        assert not rows("SELECT id FROM project_positions WHERE org_id=%s AND project_id=%s", [other_org, project["id"]])
