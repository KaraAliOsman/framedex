from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import date
from decimal import Decimal
from threading import Barrier
from uuid import UUID

from django.db import connections
import pytest

from authentication.errors import ContractAPIException
from authentication.tenancy import Membership, TenantContext
from backend.tests.integration.test_shot09_documentary import (
    _freeze,
    _seed_project,
    as_user,
    documentary_committed_tenant as documentary_committed_tenant,
    documentary_tenant as documentary_tenant,
)
from documents.repository import DocumentaryError, documentary_backend
from documents.service import freeze_revision_a, revision_snapshot
from pricing.repository import commercial_backend, one, rows
from purchasing.service import purchasing_state
from pricing.service import apply_operation, preview
from projects import service
from projects.serializers import PositionWriteSerializer

pytestmark = pytest.mark.rls_integration
D = Decimal


def tenant(org, role):
    membership = Membership(organization_id=org, organization_name="Fixture", role=role)
    return TenantContext(active_organization=membership, memberships=(membership,))


def price_current(org, actor, role, project_id):
    with commercial_backend():
        operation = preview(
            org,
            tenant(org, role),
            {
                "project_id": project_id,
                "pricing_mode": "COST_PLUS_MARGIN",
                "currency": "CLP",
                "effective_date": date(2026, 9, 19),
                "context_code": "DEFAULT",
                "discount_pct": D("0"),
                "target_margin": D("0.35"),
                "segment": "RETAIL",
                "confirmed": False,
                "reason": "SHOT-10 successor preview",
                "_actor_id": actor,
            },
        )
        apply_operation(
            org,
            actor,
            role,
            UUID(operation["id"]),
            "SHOT-10 successor apply",
            False,
        )
    return UUID(operation["id"])


def test_revision_b_reprices_and_freezes_without_mutating_revision_a(documentary_tenant):
    org, _, users, _ = documentary_tenant
    owner = users["OWNER"]
    project_id, position_id, operation_a = _seed_project(org, owner)
    frozen_a = _freeze(org, owner, project_id, operation_a)

    with as_user(owner), documentary_backend():
        historical_a = one(
            "SELECT snapshot_json::text AS snapshot,bom_hash,snapshot_sha256,emitted_at "
            "FROM public.project_versions WHERE id=%s",
            [frozen_a["id"]],
        )
        projection_a = one(
            "SELECT id,projection_hash,snapshot_json::text AS snapshot "
            "FROM public.purchase_projections WHERE project_version_id=%s",
            [frozen_a["id"]],
        )
        historical_orders = rows(
            "SELECT id,status::text,payload_json::text AS payload FROM public.orders "
            "WHERE project_version_id=%s ORDER BY id",
            [frozen_a["id"]],
        )
        historical_artifacts = rows(
            "SELECT id,file_sha256,storage_object_key FROM public.document_artifacts "
            "WHERE project_version_id=%s ORDER BY id",
            [frozen_a["id"]],
        )

    with as_user(owner):
        project = service.project_public(org, service.project_row(org, project_id), detail=True)
        assert project["status"] == "QUOTED"
        assert project["current_revision"] == "REV-A"
        cloned = service.clone_project(
            org,
            owner,
            project_id,
            {"expected_updated_at": project["updated_at"]},
        )
        assert cloned["status"] == "DRAFT"
        assert cloned["current_revision"] == "REV-A"
        assert cloned["pricing_current"] is False
        assert cloned["versions"] == []
        assert cloned["positions"][0]["id"] != position_id
        opened = service.start_successor(org, project_id)
        assert opened["successor_created"] is True
        assert opened["status"] == "DRAFT"
        assert opened["current_revision"] == "REV-B"
        assert opened["pricing_current"] is False
        assert opened["total_price_gross"] == "0.00"
        replay = service.start_successor(org, project_id)
        assert replay["successor_created"] is False
        assert replay["current_revision"] == "REV-B"

        position = service.position_public(service.position_row(org, position_id))
        serializer = PositionWriteSerializer(
            data={
                "location_tag": position["location_tag"],
                "quantity": 3,
                "design": deepcopy(position["design"]),
            }
        )
        assert serializer.is_valid(), serializer.errors
        update = serializer.validated_data
        update["expected_updated_at"] = position["updated_at"]
        changed = service.save_position(org, project_id, update, position_id=position_id)
        assert changed["quantity"] == 3

        with pytest.raises(DocumentaryError, match="applied_pricing_authority_required"):
            freeze_revision_a(
                org_id=org,
                actor_id=owner,
                project_id=project_id,
                pricing_operation_id=operation_a,
                confirmed=True,
            )

        operation_b = price_current(org, owner, "OWNER", project_id)
        protected = service.position_public(service.position_row(org, position_id))
        protected_data = serializer.validated_data
        protected_data["expected_updated_at"] = protected["updated_at"]
        with pytest.raises(ContractAPIException) as caught:
            service.save_position(org, project_id, protected_data, position_id=position_id)
        assert caught.value.contract_code == "commercial_revision_required"
        frozen_b = freeze_revision_a(
            org_id=org,
            actor_id=owner,
            project_id=project_id,
            pricing_operation_id=operation_b,
            confirmed=True,
        )
        assert frozen_b["revision_code"] == "REV-B"
        assert service.project_row(org, project_id)["status"] == "QUOTED"

    with as_user(owner), documentary_backend():
        assert one(
            "SELECT snapshot_json::text AS snapshot,bom_hash,snapshot_sha256,emitted_at "
            "FROM public.project_versions WHERE id=%s",
            [frozen_a["id"]],
        ) == historical_a
        assert one(
            "SELECT id,projection_hash,snapshot_json::text AS snapshot "
            "FROM public.purchase_projections WHERE project_version_id=%s",
            [frozen_a["id"]],
        ) == projection_a
        assert rows(
            "SELECT id,status::text,payload_json::text AS payload FROM public.orders "
            "WHERE project_version_id=%s ORDER BY id",
            [frozen_a["id"]],
        ) == historical_orders
        assert rows(
            "SELECT id,file_sha256,storage_object_key FROM public.document_artifacts "
            "WHERE project_version_id=%s ORDER BY id",
            [frozen_a["id"]],
        ) == historical_artifacts
        versions = rows(
            "SELECT revision_code,authority_version,pricing_operation_id FROM public.project_versions "
            "WHERE project_id=%s ORDER BY revision_code",
            [project_id],
        )
        assert versions == [
            {
                "revision_code": "REV-A",
                "authority_version": "SHOT10_V1",
                "pricing_operation_id": operation_a,
            },
            {
                "revision_code": "REV-B",
                "authority_version": "SHOT10_V1",
                "pricing_operation_id": operation_b,
            },
        ]
        assert one(
            "SELECT state,COALESCE(revision_code,'REV-A') AS revision_code "
            "FROM public.pricing_operations WHERE id=%s",
            [operation_a],
        ) == {"state": "APPLIED", "revision_code": "REV-A"}
    with as_user(owner):
        version_a, snapshot_a = revision_snapshot(UUID(frozen_a["id"]), org)
        assert version_a["revision_code"] == "REV-A"
        assert snapshot_a["revision"] == "REV-A"
        assert purchasing_state(org, UUID(frozen_a["id"]))["version"]["revision_code"] == "REV-A"


def test_owner_and_estimator_can_start_successors(documentary_tenant):
    org, _, users, _ = documentary_tenant
    project_id, _, operation_a = _seed_project(org, users["OWNER"])
    _freeze(org, users["OWNER"], project_id, operation_a)
    with as_user(users["OWNER"]):
        assert service.start_successor(org, project_id)["current_revision"] == "REV-B"
        operation_b = price_current(org, users["OWNER"], "OWNER", project_id)
        freeze_revision_a(
            org_id=org,
            actor_id=users["OWNER"],
            project_id=project_id,
            pricing_operation_id=operation_b,
            confirmed=True,
        )
    with as_user(users["ESTIMATOR"]):
        assert service.start_successor(org, project_id)["current_revision"] == "REV-C"


def test_source_drift_fails_closed(documentary_tenant):
    org, _, users, _ = documentary_tenant
    project_id, _, operation_id = _seed_project(org, users["OWNER"])
    _freeze(org, users["OWNER"], project_id, operation_id)
    with as_user(users["OWNER"]):
        with commercial_backend():
            rows(
                "UPDATE public.projects SET name='Unexpected drift' WHERE id=%s RETURNING id",
                [project_id],
            )
        with pytest.raises(ContractAPIException) as caught:
            service.start_successor(org, project_id)
        assert caught.value.contract_code == "revision_source_drift"
        assert service.project_row(org, project_id)["current_revision"] == "REV-A"


def test_concurrent_successor_requests_create_exactly_one_revision_b(documentary_committed_tenant):
    org, _, users, _ = documentary_committed_tenant
    owner = users["OWNER"]
    project_id, _, operation_id = _seed_project(org, owner)
    _freeze(org, owner, project_id, operation_id)
    barrier = Barrier(2)

    def open_successor():
        connections.close_all()
        try:
            with as_user(owner):
                barrier.wait(timeout=30)
                result = service.start_successor(org, project_id)
                return result["successor_created"], result["current_revision"]
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: open_successor(), range(2)))
    assert sorted(outcomes) == [(False, "REV-B"), (True, "REV-B")]
    with as_user(owner), documentary_backend():
        assert rows(
            "SELECT revision_code FROM public.project_versions WHERE project_id=%s",
            [project_id],
        ) == [{"revision_code": "REV-A"}]
    with as_user(owner):
        assert service.project_row(org, project_id)["current_revision"] == "REV-B"
