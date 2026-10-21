"""Exercise real grants, RLS, immutable reports and revision-bound data."""
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from django.db import DatabaseError, transaction
from authentication.errors import ContractAPIException
from authentication.rls import catalog_backend
from backend.tests.integration.test_shot09_documentary import (
    documentary_tenant as documentary_tenant, as_user, _seed_project, _freeze,
)
from backend.tests.integration.thermal_fixture import reviewed_case, freeze_reviewed_case
from documents.repository import documentary_backend
from documents.service import revision_snapshot
from pricing.repository import one, rows
from projects import thermal
from projects import project_ops

pytestmark = pytest.mark.rls_integration


def test_least_price_compliant_candidate_preview_apply_and_undo(documentary_tenant):
    org,_,users,_=documentary_tenant
    actor=users["OWNER"]
    project,position,system,_,report=reviewed_case(org,actor,with_alternatives=True,baseline_ug="4.0")
    assert report["assessment"]["verdict"] == "FAIL"
    with as_user(actor):
        candidate=thermal.alternatives(org,project,position)
        assert candidate["candidate"] is not None,candidate["reason"]
        selected=candidate["candidate"]
        assert selected["glass_sku"] == "THERMAL-CHEAP"
        assert selected["assessment"]["verdict"] == "PASS"
        from dekopen_engine.design_operations import apply_operations
        from projects.ops_registry import catalog_for, sale_price
        catalog = catalog_for(org, system)
        expensive = apply_operations(selected["product"], [{"op":"set_glass","module":selected["product"]["assembly"]["modules"][0]["id"],"sku":"THERMAL-EXPENSIVE"}],
            params=catalog["params"], catalog=catalog, finish="WHITE")["product"]
        expensive_price = sale_price(org, expensive, system, "WHITE", 2)
        assert Decimal(selected["price"]["net"]) < Decimal(expensive_price["net"])
        assert selected["delta_net"] > 0
        before=thermal.project_report(org,project)
        ops=[{"op":"apply_to_positions","filter":{"position_ids":[str(position)]},
            "ops":[{"op":"set_glass","module":"*","sku":selected["glass_sku"]}]}]
        simulation=project_ops.preview_project_operations(org,actor,project,ops)
        delta=simulation["simulations"][0]["thermal_delta"]
        assert delta["after"]["uw"] == Decimal("1.36624")
        assert delta["delta_uw"] == Decimal("-2.24576")
        assert thermal.project_report(org,project) == before
        applied=project_ops.apply_project_operations(org,actor,project,{"ops":ops,"before_sig":simulation["before_sig"],"operation_key":str(uuid4())})
        assert thermal.project_report(org,project)["assessment"]["verdict"] == "PASS"
        project_ops.undo_project_operations(org,actor,project,UUID(applied["operation_id"]))
        assert thermal.project_report(org,project)["assessment"] == before["assessment"]


def test_revoking_known_source_never_changes_sealed_thermal_or_pdf(documentary_tenant):
    from documents.renderers import render_pdf_document
    org,_,users,_=documentary_tenant
    actor=users["OWNER"]
    project,position,system,reports,_=reviewed_case(org,actor)
    frozen=freeze_reviewed_case(org,actor,project,position)
    assert not frozen["production_allowed"]
    with as_user(actor):
        _,snapshot=revision_snapshot(UUID(frozen["id"]),org)
        from catalogs.frozen_use import manufacturing_pending
        pending=manufacturing_pending(snapshot)
        assert any(item["field"] == "verified_at" for item in pending)
        assert snapshot["thermal"]["assessment"]["verdict"] == "PASS"
        before,_=render_pdf_document("DOC-01",snapshot,pdf_identifier="thermal-sealed-regression")
        sealed=thermal.project_report(org,project)
        thermal.review_report(org,system,UUID(reports[0]["id"]),actor,"REVOKED")
        assert thermal.project_report(org,project) == sealed
        _,again=revision_snapshot(UUID(frozen["id"]),org)
        after,_=render_pdf_document("DOC-01",again,pdf_identifier="thermal-sealed-regression")
        assert after == before


def test_reviewed_geometry_exact_uw_stale_inputs_and_revoke(documentary_tenant):
    org, other, users, foreign = documentary_tenant
    actor = users["OWNER"]
    project, position, system, reports, report = reviewed_case(org, actor)
    metric = report["assessment"]["positions"][0]["thermal"]
    assert metric["uw"] == Decimal("1.36624") and metric["air_class"] == 3, metric["missing"]
    assert report["assessment"]["verdict"] == "PASS"
    with as_user(users["ESTIMATOR"]):
        assert thermal.project_report(org, project)["assessment"]["verdict"] == "PASS"
        assert not rows("SELECT id FROM public.project_thermal_inputs WHERE org_id=%s", [other])
        with pytest.raises(ContractAPIException) as caught:
            thermal.save_inputs(org, project, users["ESTIMATOR"], report["inputs"], None)
        assert caught.value.contract_code == "thermal_inputs_stale"
        with pytest.raises(DatabaseError), transaction.atomic():
            one("UPDATE public.catalog_thermal_authorities SET uf=0.5 WHERE id=%s RETURNING id", [reports[0]["id"]])
    with as_user(foreign):
        assert not rows("SELECT id FROM public.catalog_thermal_authorities WHERE system_id=%s", [system])
        assert not rows("SELECT id FROM public.project_thermal_inputs WHERE project_id=%s", [project])
    with as_user(actor):
        with pytest.raises(DatabaseError, match="thermal_report_immutable"), transaction.atomic(), catalog_backend():
            one("UPDATE public.catalog_thermal_authorities SET uf=0.5 WHERE id=%s RETURNING id", [reports[0]["id"]])
        thermal.review_report(org, system, UUID(reports[0]["id"]), actor, "REVOKED")
        after = thermal.project_report(org, project)
        assert after["assessment"]["positions"][0]["thermal"]["uw"] is None
        assert after["assessment"]["verdict"] == "UNKNOWN"


def test_demonstration_input_never_certifies_and_sealed_report_is_immutable(documentary_tenant):
    org, _, users, _ = documentary_tenant
    actor = users["OWNER"]
    project, position, operation = _seed_project(org, actor)
    with as_user(actor):
        saved = thermal.save_inputs(org, project, actor, {"include_doc01":True}, None)
        assert saved["assessment"]["verdict"] == "UNKNOWN"
        assert saved["assessment"]["positions"][0]["thermal"]["uw"] is None
        frozen = _freeze(org, actor, project, operation)
        _, snapshot = revision_snapshot(UUID(frozen["id"]), org)
        with documentary_backend():
            assert snapshot["thermal"]["assessment"] == thermal.service.decoded(
                one("SELECT snapshot_json->'thermal'->'assessment' AS value FROM public.project_versions WHERE id=%s", [frozen["id"]])["value"])
        sealed = thermal.project_report(org, project)
        assert sealed["sealed"] and sealed["inputs"]["include_doc01"]
        assert sealed["assessment"]["verdict"] == "UNKNOWN"
        with pytest.raises(ContractAPIException) as caught:
            thermal.save_inputs(org, project, actor, {}, None)
        assert caught.value.contract_code == "thermal_revision_required"
        with pytest.raises(DatabaseError, match="thermal_input_revision_required"), transaction.atomic(), documentary_backend():
            one("UPDATE public.project_thermal_inputs SET inputs='{}' WHERE project_id=%s RETURNING id", [project])
        assert thermal.project_report(org, project) == sealed
