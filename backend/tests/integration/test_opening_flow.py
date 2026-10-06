"""Physical openings use real catalog/RLS, pricing and immutable manufacturing."""
from datetime import date
from decimal import Decimal as D
from uuid import UUID

import pytest

from backend.tests.integration.test_shot09_documentary import (
    documentary_tenant as documentary_tenant, as_user, _seed_project, _tenant)
from catalogs.glass import load_products
from documents.service import prepare_documentary_inputs, save_documentary_inputs, revision_snapshot, freeze_revision_a
from documents.repository import DocumentaryError
from engine.tests.opening_cases import typologies
from pricing.repository import admin_write, commercial_backend, one, rows
from pricing.service import preview, apply_operation
from projects.serializers import PositionWriteSerializer
from projects.service import create_project, save_position, position_row, position_public

pytestmark = pytest.mark.rls_integration


@pytest.mark.parametrize("include_lateral", [False, True])
def test_all_physical_openings_save_price_seal_and_keep_leaf_purchase_sources(documentary_tenant, include_lateral):
    org, _, users, _ = documentary_tenant
    owner = users["OWNER"]
    _seed_project(org, owner)
    with as_user(owner):
        cost_list = one("SELECT id FROM cost_lists WHERE org_id=%s", [org])["id"]
        required = rows("SELECT sku,unit FROM catalog_demo_prices WHERE system_id IN (SELECT id FROM profile_systems WHERE version=3) "
            "UNION SELECT p.commercial_sku,p.purchase_unit FROM profile_purchase_mappings p JOIN profile_articles a ON a.id=p.profile_article_id "
            "JOIN profile_systems s ON s.id=a.system_id WHERE s.version=3 "
            "UNION SELECT a.commercial_sku,a.purchase_unit FROM reinforcement_articles a JOIN profile_systems s ON s.id=a.system_id WHERE s.version=3")
        for item in required:
            if not rows("SELECT id FROM cost_list_items WHERE cost_list_id=%s AND sku=%s", [cost_list, item["sku"]]):
                admin_write("cost-items", org, {"cost_list_id": cost_list, "sku": item["sku"], "unit": item["unit"],
                    "item_type": "FIXTURE", "unit_cost": D("100")}, "D03 declared synthetic test rates")
        project = create_project(org, owner, {"name": "D03 21 typologies DEMO", "client_name": "Fixture",
            "client_rut": "1-9", "client_email": "client@example.test", "client_phone": "+56900000000", "delivery_address": "Valdivia"})
        originals = {}
        for name, (code, node) in typologies().items():
            if not include_lateral and name == "DOOR-SIDELIGHT":
                continue
            system = one("SELECT id FROM profile_systems WHERE code=%s AND version=3", [code])["id"]
            glass = next(row for row in load_products(system, org) if row["technical_sku"].endswith("-GLASS-SAFE"))
            tree = node.model_dump(mode="json", exclude_none=True)
            width, height = tree.pop("width_mm"), tree.pop("height_mm")
            def infill(target):
                if target["type"] == "BAY":
                    target.update(glass_article_sku=glass["technical_sku"],
                        glass_product=glass["resolved_product"].model_dump(mode="json"), sill_height_mm="900")
                for child in target.get("children", []):
                    infill(child)
            infill(tree)
            serializer = PositionWriteSerializer(data={"location_tag": name, "quantity": 1, "design": {
                "system_id": str(system), "nominal_width_mm": width, "nominal_height_mm": height,
                "color": "WHITE", "parametric_tree": tree}})
            serializer.is_valid(raise_exception=True)
            position = save_position(org, project["id"], serializer.validated_data)
            assert position_public(position_row(org, position["id"]))["bom"] == position["bom"]
            originals[str(position["id"])] = position["bom"]
        prepared = prepare_documentary_inputs(org_id=org, project_id=project["id"])
        inputs = []
        for position in prepared["positions"]:
            annotations = {}
            for row in position["workshop_suggestions"]:
                key = (row["bay_id"], row.get("leaf_id"))
                annotations[key] = {**annotations.get(key, {}), **{k: v for k, v in row.items() if v is not None}}
            inputs.append({"position_id": position["position_id"], "calculation_hash": position["calculation_hash"],
                "location_tag": position["location_tag"], "manufacturing_placement_policy_id": position["placement_options"][0]["id"],
                "handle_requirement_policy_id": position["handle_options"][0]["id"],
                "reinforcement_cut_policy_id": position["reinforcement_options"][0]["id"],
                "workshop_annotations": list(annotations.values()), "structural_inputs": [
                    {"target_id": span["target_id"], "required_ix_cm4": "1.00",
                     "structural_basis": "DEMO · carga ficticia del ensayo D03; no es cálculo de viento ni certificación para una obra"}
                    for span in position["workshop_targets"]["spans"]],
                "glass_polishing": position["polishing_suggestions"], "handle_intents": [],
                "accessory_schedule": {"schema_version": 1, "coverage": "NONE_REQUIRED", "items": []},
                "legacy_handle_migration_confirmed": True})
        save_documentary_inputs(org_id=org, actor_id=owner, project_id=project["id"], data={
            "payment_terms": "Anticipo 50 %", "quotation_valid_until": date(2026, 10, 25), "positions": inputs})
        with commercial_backend():
            priced = preview(org, _tenant(org, "OWNER"), {"project_id": project["id"], "pricing_mode": "COST_PLUS_MARGIN",
                "currency": "CLP", "effective_date": date(2026, 10, 6), "context_code": "DEFAULT", "discount_pct": D("0"),
                "target_margin": D("0.35"), "segment": "RETAIL", "confirmed": False, "reason": "D03 reviewed price", "_actor_id": owner})
            apply_operation(org, owner, "OWNER", UUID(priced["id"]), "D03 apply", False)
        try:
            frozen = freeze_revision_a(org_id=org, actor_id=owner, project_id=project["id"],
                pricing_operation_id=UUID(priced["id"]), confirmed=True, allow_incomplete_workshop=True)
        except DocumentaryError as error:
            pytest.fail(str(error.extra))
        _, snapshot = revision_snapshot(org_id=org, version_id=UUID(frozen["id"]))
        assert len(snapshot["positions"]) == (21 if include_lateral else 20)
        for position in snapshot["positions"]:
            assert position.get("opening_leaves", []) == originals[str(position["id"])].get("opening_leaves", [])
        # The synthetic catalog has no certified inertia for the lateral's
        # post. Quotation may seal; production must preserve that exact blocker.
        assert frozen["production_allowed"] is (not include_lateral)
        if include_lateral:
            lateral = next(p for p in snapshot["positions"] if p["location_tag"] == "DOOR-SIDELIGHT")
            evidence = next(row for row in snapshot["inspector"] if str(row["position_id"]) == str(lateral["id"]))
            assert not evidence["production_allowed"]
            assert any(finding["rule_id"] == "R05" for finding in evidence["result"]["findings"])
        else:
            assert frozen["documentary_complete"]
