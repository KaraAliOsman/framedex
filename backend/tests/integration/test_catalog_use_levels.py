"""DEKOPEN 2: real pricing with suggestions and physical-output confirmation."""

from datetime import date, timedelta
from contextlib import contextmanager
from decimal import Decimal
from uuid import UUID, uuid4

from django.db import connection, transaction, DatabaseError
import pytest

from authentication.errors import ContractAPIException
from authentication.rls import catalog_backend
from catalogs import series
from catalogs.authority import catalog_authority_gate
from catalogs.readiness import catalog_readiness
from catalogs.use_levels import require_use, series_use, technical_fingerprint
from engine_api.adapter import calculate_from_api
from engine_api.repository import SystemParamsRepository, SystemNotFound
from pricing.repository import admin_write, commercial_backend, json_text, one
from pricing.service import apply_operation, preview
from documents.artifacts import generate_artifact
from documents.repository import DocumentaryError
from documents.service import freeze_revision_a, prepare_documentary_inputs, save_documentary_inputs, revision_snapshot
from production.service import release_production

from .test_catalog_series_sheet import create, pro6004_input
from .test_shot08_pricing import owner_client
from .test_shot09_documentary import as_user, _tenant, FakeStorage, documentary_tenant as documentary_tenant

pytestmark = pytest.mark.rls_integration
D = Decimal


@contextmanager
def fixture_write():
    with connection.cursor() as cursor:
        cursor.execute("SET LOCAL ROLE NONE")
    try:
        yield
    finally:
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL ROLE authenticated")


def tree():
    return {"id": "B1", "type": "BAY", "opening_type": "TURN_LEFT", "glass_spec": "4-16-4",
        "glass_thickness_mm": "24", "glass_article_sku": "GLASS-24"}


def priced_series(org, actor):
    # Explicit synthetic workshop facts; these do not claim manufacturer data.
    supplied = pro6004_input()
    profiles = [{**item, "commercial_length_mm": "6500.00"} for item in supplied["profiles"]]
    sheet = create(org, actor, profiles=profiles)
    with fixture_write():
        for profile in sheet["tabs"]["profiles"]:
            one("INSERT INTO public.profile_purchase_mappings(org_id,profile_article_id,commercial_sku,manufacturer_name,purchase_unit) "
                "VALUES(%s,%s,%s,'SYNTHETIC workshop','BAR') RETURNING id", [org, profile["id"], profile["sku"]])
            if profile["reinforcement_sku"]:
                one("INSERT INTO public.reinforcement_articles(org_id,system_id,parent_profile_article_id,sku,commercial_sku,name,stock_length_mm,purchase_unit,is_default) "
                    "VALUES(%s,%s,%s,%s,%s,'SYNTHETIC steel',6000,'BAR',true) RETURNING id",
                    [org, sheet["id"], profile["id"], profile["reinforcement_sku"], profile["reinforcement_sku"]])
    with catalog_backend():
        one("INSERT INTO public.glass_purchase_mappings(org_id,system_id,technical_sku,purchasing_sku,manufacturer_name,purchase_unit,version,provenance,glass_spec) "
            "VALUES(%s,%s,'GLASS-24','GLASS-24','SYNTHETIC glass','EA',1,'{}','4-16-4') RETURNING id", [org, sheet["id"]])
    price_list = admin_write("cost-lists", org, {"supplier_name": "SYNTHETIC workshop", "currency": "CLP", "valid_from": date(2026, 1, 1)}, "Synthetic DK2 prices")
    for sku, unit, price in (("PRO-F", "BAR", "12000"), ("PRO-S", "BAR", "15000"), ("PRO-B", "BAR", "5000"),
            ("STEEL-F", "BAR", "8000"), ("STEEL-S", "BAR", "8000"), ("GLASS-24", "M2", "20000"), ("PRO-TURN", "KIT", "12000"),
            ("SCREW-F", "EA", "20"), ("SCREW-S", "EA", "20")):
        admin_write("cost-items", org, {"cost_list_id": price_list["id"], "sku": sku, "item_type": "SYNTHETIC",
            "unit": unit, "unit_cost": D(price)}, "Synthetic DK2 cost")
    return series.series_sheet(org, sheet["id"])


def verify(org, system, actor):
    fingerprint = technical_fingerprint(org, system)
    with catalog_backend():
        one("UPDATE public.catalog_series_setup SET verified_at=now(),verified_by=%s,verified_hash=%s "
            "WHERE org_id=%s AND system_id=%s RETURNING system_id", [actor, fingerprint, org, system])


def test_drawable_does_not_require_inspector_glazing_or_prices(documentary_tenant):
    org, _, users, _ = documentary_tenant
    with as_user(users["OWNER"]):
        sheet = create(org, users["OWNER"], glazing=[], hardware=[])
        usage = sheet["usage"]
        assert usage["level"] == "DRAWABLE"
        assert usage["suggested_count"] > 0
        assert next(item for item in usage["levels"] if item["level"] == "DRAWABLE")["ok"]
        assert not catalog_readiness(sheet["id"], org)["quote_ready"]


def test_pro6004_quotes_with_suggestions_and_cuts_only_after_confirmation_and_verification(documentary_tenant, monkeypatch):
    org, _, users, _ = documentary_tenant
    actor = users["OWNER"]
    with as_user(actor):
        sheet = priced_series(org, actor)
        assert sheet["usage"]["level"] == "QUOTABLE", sheet["usage"]["pending"]
        assert catalog_readiness(sheet["id"], org)["quote_ready"]
        params = SystemParamsRepository().load_visible(sheet["id"], org)
        result = calculate_from_api(parametric_tree=tree(), nominal_width_mm=D("1200"),
            nominal_height_mm=D("1100"), color="WHITE", params=params)
        assert result.profile_cuts and result.glasses and result.assumptions
        project = one("INSERT INTO public.projects(org_id,code,name,client_name,created_by) "
            "VALUES(%s,%s,'SYNTHETIC quote','SYNTHETIC client',%s) RETURNING id", [org, uuid4().hex[:10], actor])["id"]
        position = one("INSERT INTO public.project_positions(org_id,project_id,position_index,quantity,typology,system_id,width_mm,height_mm,parametric_tree,bom_snapshot) "
            "VALUES(%s,%s,1,1,'TURN_LEFT',%s,1200,1100,%s::jsonb,%s::jsonb) RETURNING id",
            [org, project, sheet["id"], json_text(tree()), result.model_dump_json()])["id"]
        admin_write("rules", org, {"pricing_mode": "COST_PLUS_MARGIN", "default_margin_pct": D("0.35"),
            "tax_rate_pct": D("0.19"), "waste_factor_pct": D("0.08"), "labor_rate_per_m2": D("15000"),
            "installation_rate_per_m2": D("0")}, "Synthetic DK2 rule")
        with commercial_backend():
            priced = preview(org, _tenant(org, "OWNER"), {"project_id": project, "pricing_mode": "COST_PLUS_MARGIN",
                "currency": "CLP", "effective_date": date(2026, 10, 21), "context_code": "DEFAULT",
                "discount_pct": D("0"), "target_margin": D("0.35"), "segment": "RETAIL", "confirmed": False,
                "reason": "SYNTHETIC real price", "_actor_id": actor})
        assert priced["id"]
        assert D(priced["total_cost"]) > 0
        assert priced["positions_breakdown"][0]["composition"]
        with commercial_backend():
            apply_operation(org, actor, "OWNER", UUID(priced["id"]), "SYNTHETIC apply", False)
        prepared = prepare_documentary_inputs(org_id=org, project_id=project)
        assert not prepared["positions"][0]["production_ready"]
        inputs = {"position_id": position, "calculation_hash": prepared["positions"][0]["calculation_hash"],
            "location_tag": "SYNTHETIC", "manufacturing_placement_policy_id": None,
            "handle_requirement_policy_id": None, "reinforcement_cut_policy_id": None,
            "workshop_annotations": [], "structural_inputs": [], "glass_polishing": [],
            "handle_intents": [], "accessory_schedule": None, "legacy_handle_migration_confirmed": False}
        documentary = {"payment_terms": "SYNTHETIC transfer", "quotation_valid_until": date.today() + timedelta(days=30),
            "positions": [inputs]}
        wrong_policy = one("SELECT id FROM manufacturing_placement_policies WHERE org_id IS NULL LIMIT 1")["id"]
        with pytest.raises(DatabaseError), transaction.atomic():
            save_documentary_inputs(org_id=org, actor_id=actor, project_id=project,
                data={**documentary, "positions": [{**inputs, "manufacturing_placement_policy_id": wrong_policy}]})
        save_documentary_inputs(org_id=org, actor_id=actor, project_id=project, data=documentary)
        frozen = freeze_revision_a(org_id=org, actor_id=actor, project_id=project,
            pricing_operation_id=UUID(priced["id"]), confirmed=True, allow_incomplete_workshop=True)
        assert not frozen["production_allowed"] and not frozen["documentary_complete"]
        _, snapshot = revision_snapshot(UUID(frozen["id"]), org)
        assert snapshot["bom"][0]["engine_result"]["assumptions"]
        assert snapshot["positions"][0]["catalog_authority_gate"]["workshop_pending"]
        FakeStorage.uploads, FakeStorage.deleted, FakeStorage.upload_calls = {}, [], 0
        monkeypatch.setattr("documents.artifacts.SupabaseDocumentStorage", FakeStorage)
        artifact, created = generate_artifact(org_id=org, actor_id=actor, role="OWNER", project_version_id=UUID(frozen["id"]),
            order_id=None, document_type="DOC-01", file_format="PDF")
        assert created and artifact["document_type"] == "DOC-01"
        with pytest.raises(DocumentaryError, match="production_document_blocked"):
            generate_artifact(org_id=org, actor_id=actor, role="OWNER", project_version_id=UUID(frozen["id"]),
                order_id=None, document_type="DOC-03", file_format="PDF")
        assert one("SELECT id FROM public.project_positions WHERE id=%s", [position])["id"] == position
        with pytest.raises(ContractAPIException) as blocked:
            require_use(org, sheet["id"], "MANUFACTURABLE")
        assert blocked.value.extra["required_level"] == "MANUFACTURABLE"
        assert any(item["origin"] == "SUGGESTED" for item in blocked.value.extra["pending"])
        assert any(item["field"] == "verified_at" for item in blocked.value.extra["pending"])
        with fixture_write():
            one("INSERT INTO public.cutting_profiles(org_id,code,name,kerf_mm,head_trim_mm,tail_trim_mm,is_default) "
                "VALUES(%s,'DK2','SYNTHETIC saw',4,5,5,true) RETURNING id", [org])
    client = owner_client(actor)
    payload = {"system_id": str(sheet["id"]), "parametric_tree": tree(), "nominal_width_mm": "1200",
        "nominal_height_mm": "1100", "color": "WHITE"}
    path = "/api/v1/engine/optimize-cut/"
    response = client.post(path, payload, format="json", HTTP_X_ORGANIZATION_ID=str(org))
    assert response.status_code == 422, response.data
    assert response.json()["pending"]
    with as_user(actor):
        sheet = series.series_sheet(org, sheet["id"])
        suggested = [{key: item[key] for key in ("resource", "row_id", "field")} for item in sheet["cells"] if item["origin"] == "SUGGESTED"]
        series.confirm_cells(org, sheet["id"], actor, {"revision": sheet["revision"], "cells": suggested})
        assert series_use(org, sheet["id"])["suggested_count"] == 0
        with pytest.raises(ContractAPIException):
            require_use(org, sheet["id"], "MANUFACTURABLE")
        verify(org, sheet["id"], actor)
        assert require_use(org, sheet["id"], "MANUFACTURABLE")["verified"]
    response = client.post(path, payload, format="json", HTTP_X_ORGANIZATION_ID=str(org))
    assert response.status_code == 200, response.data
    assert response.json()["metrics"]["bars"] > 0
    with as_user(actor):
        # Confirmation today cannot rewrite yesterday's quote-only decision.
        def forbidden(*args, **kwargs):
            raise AssertionError("Release consulted mutable catalog")
        monkeypatch.setattr("catalogs.use_levels.series_use", forbidden)
        with pytest.raises(DocumentaryError, match="catalog_use_incomplete") as frozen_block:
            release_production(org_id=org, version_id=UUID(frozen["id"]), actor_id=actor)
        assert frozen_block.value.extra["pending"]


def test_verification_requires_exact_current_fingerprint_and_tenant_scope(documentary_tenant):
    org, other, users, foreign = documentary_tenant
    with as_user(users["OWNER"]):
        sheet = create(org, users["OWNER"])
        with catalog_backend():
            one("UPDATE public.catalog_series_setup SET verified_at=now(),verified_by=%s,verified_hash=%s "
                "WHERE system_id=%s RETURNING system_id", [users["OWNER"], "sha256:" + "a" * 64, sheet["id"]])
        assert not series_use(org, sheet["id"])["verified"]
    with as_user(foreign), pytest.raises(SystemNotFound), transaction.atomic():
        series_use(other, sheet["id"])


def test_examples_remain_explicitly_synthetic(documentary_tenant):
    org, _, users, _ = documentary_tenant
    with as_user(users["OWNER"]):
        system = one("SELECT id FROM profile_systems WHERE code='DEMO_60' AND version=2")["id"]
        usage = series_use(org, system)
        assert usage["is_example"] and not usage["verified"]
        assert next(item for item in usage["levels"] if item["level"] == "QUOTABLE")["ok"], [(item["rule"], item["action"]) for item in usage["pending"]]
        assert next(item for item in usage["levels"] if item["level"] == "MANUFACTURABLE")["ok"]


def test_current_cell_confirmation_supersedes_stale_row_review_but_keeps_physical_checks(documentary_tenant):
    org, _, users, _ = documentary_tenant
    actor = users["OWNER"]
    with as_user(actor):
        sheet = priced_series(org, actor)
        system = sheet["tabs"]["rules"]
        series.service.review(series.service.SYSTEMS, org, sheet["id"], actor,
            expected_revision='"' + system["revision"] + '"')
        sheet = series.series_sheet(org, sheet["id"])
        sheet = series.edit_cells(org, sheet["id"], actor, {"revision": sheet["revision"], "changes": [{
            "resource": "systems", "row_id": sheet["id"], "field": "glass_clearance_white_mm", "value": "4.25"}]})
        assert sheet["tabs"]["rules"]["review_pending"]
        suggested = [{key: item[key] for key in ("resource", "row_id", "field")}
            for item in sheet["cells"] if item["origin"] == "SUGGESTED"]
        series.confirm_cells(org, sheet["id"], actor, {"revision": sheet["revision"], "cells": suggested})
        verify(org, sheet["id"], actor)
        usage = require_use(org, sheet["id"], "MANUFACTURABLE")
        params = SystemParamsRepository().load_visible(sheet["id"], org)
        process = {"resolved_via": "system", "profile": {"code": "SYNTHETIC"}}
        arguments = {"system_id": sheet["id"], "org_id": org, "params": params, "process_facts": process}
        legacy = catalog_authority_gate(**arguments)
        assert not legacy["review"]["ok"] and not legacy["ok"]
        current = catalog_authority_gate(**arguments, usage=usage)
        assert current["ok"] and current["usage"]["verified"]
        assert current["review"] == legacy["review"]
        assert not catalog_authority_gate(**{**arguments, "process_facts": {}}, usage=usage)["ok"]
        assert not catalog_authority_gate(**{**arguments,
            "params": params.model_copy(update={"rebate_depth_mm": None})}, usage=usage)["ok"]
