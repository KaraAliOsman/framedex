"""P16: actual catalog, emission and immutable source authority under RLS."""
from uuid import UUID

import pytest
from django.db import DatabaseError, transaction

from authentication.errors import ContractAPIException
from backend.tests.integration.catalog_fixture import copy_fixed_catalog
from backend.tests.integration.test_shot09_documentary import (
    _seed_project, as_user, documentary_tenant as documentary_tenant,
)
from backend.tests.integration.test_catalog_interchange import imported
from catalogs import service, evidence
from catalogs.authority import catalog_authority_gate
from catalogs.readiness import catalog_readiness
from documents.repository import DocumentaryError
from documents.service import freeze_revision_a, revision_snapshot
from engine_api.repository import SystemParamsRepository
from ingest import catalog_review, catalog_sources
from pricing.repository import one, json_text
from production.service import process_facts_snapshot, release_production

pytestmark = pytest.mark.rls_integration


@pytest.mark.parametrize("incomplete", [False, True])
def test_catalog_and_emission_use_same_authority_predicate(documentary_tenant, incomplete):
    org, _, users, _ = documentary_tenant
    system = copy_fixed_catalog(org) if incomplete else one(
        "SELECT id FROM profile_systems WHERE code='DEMO_60' AND version=1")["id"]
    if incomplete:
        one("UPDATE profile_articles SET welding_loss_mm=NULL WHERE system_id=%s AND role='FRAME' RETURNING id", [system])
    with as_user(users["OWNER"]):
        params = SystemParamsRepository().load_visible(system, org)
        facts = one("SELECT material::text,process_profile_id::text FROM profile_systems WHERE id=%s", [system])
        process = process_facts_snapshot(org_id=org, engine_result={}, system_facts=facts)
        catalog = catalog_readiness(system, org)
        consumed = catalog_authority_gate(system_id=system, org_id=org, params=params,
            process_facts=process,
            profile_skus={article.sku for article in params.effective_profile_articles.values()},
            hardware_skus={kit.sku for kit in params.available_hardware_kits})
        for rule in ("process", "fabrication", "review"):
            assert catalog["authority_gate"][rule] == consumed[rule]
        assert catalog["authority_gate"]["ok"] == consumed["ok"]
        assert consumed["fabrication"]["ok"] is (not incomplete)
        if incomplete:
            blocker = next(blocker for level in catalog["levels"] for blocker in level["blockers"] if blocker["code"] == "fabrication")
            frame = one("SELECT id FROM profile_articles WHERE system_id=%s AND role='FRAME'", [system])
            assert any(target["row_id"] == str(frame["id"]) and "record=" in target["href"] for target in blocker["targets"])


def test_seal_retains_gate_release_does_not_read_mutable_catalog(documentary_tenant, monkeypatch):
    org, _, users, _ = documentary_tenant
    actor = users["OWNER"]
    project, _, operation = _seed_project(org, actor)
    with as_user(actor):
        frozen = freeze_revision_a(org_id=org, actor_id=actor, project_id=project, pricing_operation_id=operation, confirmed=True)
        _, snapshot = revision_snapshot(UUID(frozen["id"]), org)
        assert snapshot["positions"][0]["catalog_authority_gate"]["ok"]
        def forbidden(*args, **kwargs):
            raise AssertionError("release consulted mutable catalog authority")
        monkeypatch.setattr("catalogs.authority.catalog_authority_gate", forbidden)
        assert release_production(org_id=org, version_id=UUID(frozen["id"]), actor_id=actor)["orders"]


def test_missing_process_is_quote_only_at_seal_and_not_releasable(documentary_tenant, monkeypatch):
    org, _, users, _ = documentary_tenant
    actor = users["OWNER"]
    project, _, operation = _seed_project(org, actor)
    original = process_facts_snapshot
    def incomplete(**kwargs):
        facts = original(**kwargs)
        return {**facts, "resolved_via": "generic_fallback"}
    monkeypatch.setattr("documents.service.process_facts_snapshot", incomplete)
    with as_user(actor):
        frozen = freeze_revision_a(org_id=org, actor_id=actor, project_id=project, pricing_operation_id=operation, confirmed=True, allow_incomplete_workshop=True)
        _, snapshot = revision_snapshot(UUID(frozen["id"]), org)
        assert not frozen["production_allowed"]
        assert snapshot["positions"][0]["catalog_authority_gate"]["process"]["state"] == "BLOCK"
        with pytest.raises(DocumentaryError, match="version_not_releasable"):
            release_production(org_id=org, version_id=UUID(frozen["id"]), actor_id=actor)


def test_correction_and_timeline_survive_publication_and_undo(documentary_tenant):
    org, _, users, _ = documentary_tenant
    actor = users["OWNER"]
    import_id, items = imported(org, actor)
    profile = next(item for item in items if item["key"] == "Perfiles:2") if any(item["key"] == "Perfiles:2" for item in items) else next(item for item in items if "face_width_mm" in item["values"])
    original = profile["values"]["face_width_mm"]
    profile["values"]["face_width_mm"] = "55.01"
    with as_user(actor):
        preview = catalog_review.preview(org_id=org, import_id=import_id, items=items)
        assert not preview["errors"]
        catalog_sources.record_review(org_id=org, import_id=import_id, actor_id=actor, items=items, review_token=preview["review_token"], errors=[])
        published = catalog_review.publish(org_id=org, actor_id=actor, import_id=import_id, items=items, review_token=preview["review_token"])
        article = next(item for item in published["created"] if item["table"] == "profile_articles" and item["key"] == profile["key"])
        attestation = one("SELECT * FROM catalog_parameter_evidence WHERE row_id=%s AND field_name='face_width_mm'", [article["row_id"]])
        assert attestation["extraction_method"] == "HUMAN_CORRECTION"
        assert attestation["source_import_id"] == import_id
        assert json_text(original) == attestation["original_value"]
        visible = service.retrieve(service.ARTICLES, org, article["row_id"])
        assert visible["authority_provenance"]["state"] == "REVIEWED"
        catalog_review.undo_publication(org_id=org, actor_id=actor, import_id=import_id)
        history = catalog_sources.timeline(org, import_id)["items"]
        assert [event["action"] for event in history] == ["REVIEW_READY", "REVIEW", "PUBLISH", "UNDO"]
        assert one("SELECT source_import_id FROM catalog_parameter_evidence WHERE id=%s", [attestation["id"]])["source_import_id"] == import_id
        with pytest.raises(DatabaseError), transaction.atomic():
            one("UPDATE catalog_import_events SET action='FAILED' WHERE import_id=%s RETURNING id", [import_id])


def test_global_authority_cannot_make_foreign_source_visible(documentary_tenant):
    org, other, users, _ = documentary_tenant
    foreign = copy_fixed_catalog(other)
    global_system = one("SELECT id FROM profile_systems WHERE code='DEMO_60' AND version=1")["id"]
    with as_user(users["WORKSHOP_MANAGER"]):
        with pytest.raises(ContractAPIException):
            evidence.declare_evidence(org_id=org, actor_id=users["WORKSHOP_MANAGER"], values={
                "authority_table": "profile_systems", "row_id": foreign, "field_name": "depth_mm", "source_document": "foreign.pdf"})
        visible = service.retrieve(service.SYSTEMS, org, global_system)
        assert visible["authority_provenance"]["state"] == "DEMO"
        assert not evidence.list_evidence(org_id=org, system_id=global_system) or all(
            item["org_id"] in (None, str(org)) for item in evidence.list_evidence(org_id=org, system_id=global_system))


def test_manufacturing_blockers_address_missing_policy_instead_of_process(documentary_tenant):
    org, _, users, _ = documentary_tenant
    system = copy_fixed_catalog(org)
    with as_user(users["WORKSHOP_MANAGER"]):
        workspace = service.system_workspace(org, system)
        policies = workspace["manufacturing_policies"]
        missing = [policy for policy in policies if not policy["valid"]]
        assert missing
        assert all(policy["id"] is None for policy in missing)
        blocker = next(blocker for level in workspace["system"]["readiness"]["levels"]
                       for blocker in level["blockers"] if blocker["code"] == "manufacturing")
        assert {target["field"] for target in blocker["targets"]} == {policy["kind"] for policy in missing}
        assert all("anchor=ws.policy-" in target["href"] for target in blocker["targets"])
