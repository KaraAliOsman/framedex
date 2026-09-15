"""Real PostgreSQL SHOT-09 freeze, evidence, order, and artifact invariants."""

from collections.abc import Sequence
from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from django.db import connection, DatabaseError, transaction
import pytest

from authentication.rls import authenticated_rls_context
from authentication.types import Membership, TenantContext
from dekopen_engine.documentary_canonical import documentary_sha256_v1
from engine_api.adapter import calculate_from_api
from engine_api.repository import SystemParamsRepository
from pricing.repository import admin_write, audit_reason, commercial_backend, json_text, one, rows
from pricing.service import apply_operation, preview

import documents.artifacts as artifacts_module
from documents.artifacts import generate_artifact
from documents.repository import DocumentaryError, documentary_backend
from documents.renderers import _doc01
from documents.service import (
    freeze_revision_a,
    revision_snapshot,
    save_documentary_inputs,
)
from purchasing.service import (
    allocate_requirement,
    confirm_order_type_batch,
    create_eligibility,
    purchasing_state,
    send_order,
)

pytestmark = pytest.mark.rls_integration
D = Decimal


@contextmanager
def as_user(user_id: UUID):
    with authenticated_rls_context({"sub": str(user_id), "role": "authenticated", "aal": "aal2"}):
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('request.jwt.claim.sub',%s,true)", [str(user_id)])
        audit_reason("SHOT-09 integration authority")
        yield


@pytest.fixture
def documentary_tenant(django_db_blocker):
    with django_db_blocker.unblock():
        if connection.vendor != "postgresql":
            pytest.fail("SHOT-09 requires real PostgreSQL; never skipped")
        with transaction.atomic():
            org, other = uuid4(), uuid4()
            users = {
                role: uuid4()
                for role in ("OWNER", "ESTIMATOR", "WORKSHOP_MANAGER", "INSTALLER")
            }
            other_user = uuid4()
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO public.tenancy_organizations(id,name,tax_id) VALUES(%s,%s,%s),(%s,%s,%s)",
                    [org, "Documentary A", str(org), other, "Documentary B", str(other)],
                )
                for role, user_id in users.items():
                    cursor.execute(
                        "INSERT INTO public.tenancy_memberships(org_id,user_id,role) VALUES(%s,%s,%s)",
                        [org, user_id, role],
                    )
                cursor.execute(
                    "INSERT INTO public.tenancy_memberships(org_id,user_id,role) VALUES(%s,%s,'OWNER')",
                    [other, other_user],
                )
            yield org, other, users, other_user
            transaction.set_rollback(True)


def _tenant(org: UUID, role: str) -> TenantContext:
    membership = Membership(organization_id=org, organization_name="Fixture", role=role)
    return TenantContext(active_organization=membership, memberships=(membership,))


def _seed_project(org: UUID, owner: UUID, *, valid_annotations: bool = True) -> tuple[
    UUID, UUID, UUID
]:
    system_id = UUID(str(one("SELECT id FROM public.profile_systems WHERE code='DEMO_60'")["id"]))
    project_id = UUID(str(one(
        "INSERT INTO public.projects(org_id,code,name,client_name,client_rut,client_email,"
        "client_phone,delivery_address,created_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
        [org, f"P-{uuid4().hex[:8]}", "Proyecto documental", "Cliente Demo", "1-9",
         "cliente@example.test", "+56900000000", "Obra Norte", owner],
    )["id"]))
    tree = {
        "id": "B1",
        "type": "BAY",
        "opening_type": "FIXED",
        "glass_spec": "4-12-4 Float Incoloro",
        "glass_thickness_mm": "24.00",
        "glass_article_sku": "GLASS-BASE",
    }
    with as_user(owner):
        params = SystemParamsRepository().load_visible(system_id, org)
        result = calculate_from_api(
            parametric_tree=tree,
            nominal_width_mm=D("1000.00"),
            nominal_height_mm=D("1000.00"),
            color="WHITE",
            params=params,
        )
    position_id = UUID(str(one(
        "INSERT INTO public.project_positions(org_id,project_id,position_index,location_tag,quantity,"
        "typology,system_id,width_mm,height_mm,parametric_tree,bom_snapshot) "
        "VALUES(%s,%s,1,NULL,2,'FIXED',%s,1000.00,1000.00,%s::jsonb,%s::jsonb) RETURNING id",
        [org, project_id, system_id, json_text(tree), result.model_dump_json()],
    )["id"]))
    with as_user(owner):
        cost_list = admin_write(
            "cost-lists", org,
            {"supplier_name": "Fixture", "currency": "CLP", "valid_from": date(2026, 9, 1)},
            "SHOT-09 fixture list",
        )
        for sku, unit in (
            ("DEMO-BAR-MARCO", "BAR"),
            ("DEMO-BAR-JQ-10", "BAR"),
            ("DEMO-STEEL-BAR-MARCO", "BAR"),
            ("GLASS-BASE", "M2"),
        ):
            admin_write(
                "cost-items", org,
                {"cost_list_id": cost_list["id"], "sku": sku, "item_type": "FIXTURE",
                 "unit": unit, "unit_cost": D("100.0000")},
                "SHOT-09 fixture item",
            )
        admin_write(
            "rules", org,
            {"pricing_mode": "COST_PLUS_MARGIN", "default_margin_pct": D("0.3500"),
             "tax_rate_pct": D("0.1900"), "waste_factor_pct": D("0.0800"),
             "labor_rate_per_m2": D("15.00"), "installation_rate_per_m2": D("12.00")},
            "SHOT-09 fixture rules",
        )
        with commercial_backend():
            operation = preview(org, _tenant(org, "OWNER"), {
                "project_id": project_id,
                "pricing_mode": "COST_PLUS_MARGIN",
                "currency": "CLP",
                "effective_date": date(2026, 9, 10),
                "context_code": "DEFAULT",
                "discount_pct": D("0"),
                "target_margin": D("0.35"),
                "segment": "RETAIL",
                "confirmed": False,
                "reason": "SHOT-09 exact preview",
                "_actor_id": owner,
            })
            apply_operation(
                org, owner, "OWNER", UUID(operation["id"]),
                "SHOT-09 exact apply", False,
            )
    operation_id = UUID(operation["id"])
    with as_user(owner), documentary_backend():
        policies = one(
            "SELECT placement.id AS placement_id,handles.id AS handle_id,steel.id AS steel_id "
            "FROM public.profile_systems system "
            "JOIN public.manufacturing_placement_policies placement ON placement.system_id=system.id "
            "JOIN public.handle_requirement_policies handles ON handles.system_id=system.id "
            "JOIN public.reinforcement_cut_policies steel ON steel.system_id=system.id "
            "WHERE system.id=%s AND placement.org_id IS NULL AND handles.org_id IS NULL "
            "AND steel.org_id IS NULL",
            [system_id],
        )
        annotations = ([{
            "bay_id": "B1",
            "leaf_id": None,
            "bottom_drain_holes_mm": [D("100"), D("500"), D("900")],
            "closing_points_perimeter_mm": None,
            "continuous_width_mm": D("1000"),
            "finish_class": "WHITE",
            "has_coupler": False,
        }] if valid_annotations else [])
        save_documentary_inputs(
            org_id=org,
            actor_id=owner,
            project_id=project_id,
            data={
                "payment_terms": "50% anticipo, 50% contra entrega",
                "quotation_valid_until": date(2026, 10, 14),
                "positions": [{
                    "position_id": position_id,
                    "location_tag": "FACHADA-NORTE",
                    "manufacturing_placement_policy_id": policies["placement_id"],
                    "handle_requirement_policy_id": policies["handle_id"],
                    "reinforcement_cut_policy_id": policies["steel_id"],
                    "workshop_annotations": annotations,
                    "structural_inputs": [],
                    "glass_polishing": [{
                        "schema_version": 1,
                        "bay_id": "B1",
                        "leaf_id": None,
                        "edges": {"top": False, "right": False, "bottom": False, "left": False},
                    }],
                    "handle_intents": [],
                    "accessory_schedule": {
                        "schema_version": 1, "coverage": "NONE_REQUIRED", "items": [],
                    },
                    "legacy_handle_migration_confirmed": False,
                }],
            },
        )
    return project_id, position_id, operation_id


def _freeze(org: UUID, owner: UUID, project_id: UUID, operation_id: UUID):
    with as_user(owner):
        return freeze_revision_a(
            org_id=org, actor_id=owner, project_id=project_id,
            pricing_operation_id=operation_id, confirmed=True,
        )


def test_exact_applied_freeze_is_idempotent_immutable_and_tenant_bound(documentary_tenant) -> None:
    org, other, users, other_user = documentary_tenant
    project_id, _, operation_id = _seed_project(org, users["OWNER"])
    with as_user(users["OWNER"]), commercial_backend():
        preview_only = preview(org, _tenant(org, "OWNER"), {
            "project_id": project_id, "pricing_mode": "COST_PLUS_MARGIN",
            "currency": "CLP", "effective_date": date(2026, 9, 10),
            "context_code": "DEFAULT", "discount_pct": D("0"),
            "target_margin": D("0.35"), "segment": "RETAIL", "confirmed": False,
            "reason": "Unapplied operation must not freeze", "_actor_id": users["OWNER"],
        })
    with pytest.raises(DocumentaryError, match="applied_pricing_authority_required"):
        _freeze(org, users["OWNER"], project_id, UUID(preview_only["id"]))
    frozen = _freeze(org, users["OWNER"], project_id, operation_id)
    assert frozen["created"] is True and frozen["revision_code"] == "REV-A"
    assert frozen["bom_hash"] != frozen["snapshot_sha256"]
    again = _freeze(org, users["OWNER"], project_id, operation_id)
    assert again["created"] is False and again["id"] == frozen["id"]
    with pytest.raises(DatabaseError), transaction.atomic(), as_user(users["OWNER"]):
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE public.project_versions SET snapshot_json='{}' WHERE id=%s",
                [frozen["id"]],
            )
    with pytest.raises(DatabaseError), transaction.atomic(), as_user(users["OWNER"]), commercial_backend():
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE public.pricing_operations SET reason='drift' WHERE id=%s",
                [operation_id],
            )
    with as_user(users["OWNER"]):
        version, snapshot = revision_snapshot(UUID(frozen["id"]), org)
    assert version["bom_hash"] == snapshot["bom_hash"]
    assert snapshot["pricing"]["operation_id"] == str(operation_id)
    assert snapshot["realized_waste"] == {"status": "NOT_RECORDED", "value": None}
    with as_user(other_user), pytest.raises(DocumentaryError, match="project_version_not_found"):
        revision_snapshot(UUID(frozen["id"]), other)


def test_stored_default_green_is_ignored_and_red_blocks_freeze(documentary_tenant) -> None:
    org, _, users, _ = documentary_tenant
    project_id, position_id, operation_id = _seed_project(
        org, users["OWNER"], valid_annotations=False
    )
    assert one("SELECT inspector_status::text FROM public.project_positions WHERE id=%s", [position_id])[
        "inspector_status"
    ] == "GREEN"
    with pytest.raises(DocumentaryError, match="inspector_red_blocks"):
        _freeze(org, users["OWNER"], project_id, operation_id)
    assert rows("SELECT id FROM public.project_versions WHERE project_id=%s", [project_id]) == []


def _eligibility_data(order_type: str, keys: list[str], supplier: str) -> dict[str, object]:
    return {
        "order_type": order_type,
        "supplier_identity": supplier,
        "supplier_name": f"Proveedor {supplier}",
        "supplier_details": {"tax_id": "1-9", "email": "supplier@example.test",
                             "phone": "", "address": "Chile"},
        "eligible_requirement_keys": sorted(keys),
        "evidence": {"basis": "Selección humana explícita", "reference": "TEST", "valid_until": None},
        "version": 1,
        "confirmed": True,
    }


class FakeStorage:
    uploads: dict[str, bytes] = {}
    upload_calls = 0
    deleted: list[str] = []

    def upload_immutable(self, object_key: str, content: bytes, content_type: str) -> None:
        FakeStorage.upload_calls += 1
        prior = self.uploads.get(object_key)
        if prior is not None and prior != content:
            raise AssertionError("immutable storage collision")
        self.uploads[object_key] = content

    def delete_object(self, object_key: str) -> None:
        FakeStorage.deleted.append(object_key)
        self.uploads.pop(object_key, None)

    def signed_url(self, object_key: str) -> str:
        return f"http://127.0.0.1:25321/signed/{object_key}"


def test_order_types_confirm_independently_and_artifacts_do_not_send(
    documentary_tenant, monkeypatch: pytest.MonkeyPatch,
) -> None:
    org, _, users, _ = documentary_tenant
    FakeStorage.uploads = {}
    FakeStorage.upload_calls = 0
    FakeStorage.deleted = []
    project_id, _, operation_id = _seed_project(org, users["OWNER"])
    frozen = _freeze(org, users["OWNER"], project_id, operation_id)
    version_id = UUID(frozen["id"])
    with as_user(users["WORKSHOP_MANAGER"]):
        state = purchasing_state(org, version_id)
        original_quantities = {
            item["requirement_key"]: item["quantity"] for item in state["requirements"]
        }
        by_type: dict[str, list[dict[str, object]]] = {}
        for requirement in state["requirements"]:
            by_type.setdefault(requirement["order_type"], []).append(requirement)
        eligibility_ids = {}
        for order_type, requirements in by_type.items():
            eligibility = create_eligibility(
                org_id=org, actor_id=users["WORKSHOP_MANAGER"], version_id=version_id,
                data=_eligibility_data(
                    order_type,
                    [str(item["requirement_key"]) for item in requirements],
                    f"SUPPLIER-{order_type}",
                ),
            )
            eligibility_ids[order_type] = UUID(eligibility["id"])
            for requirement in requirements:
                allocate_requirement(
                    org_id=org,
                    actor_id=users["WORKSHOP_MANAGER"],
                    requirement_id=UUID(str(requirement["id"])),
                    eligibility_id=eligibility_ids[order_type],
                )
        glass_orders = confirm_order_type_batch(
            org_id=org, actor_id=users["WORKSHOP_MANAGER"], version_id=version_id,
            order_type="SUPPLIER_GLASS_PO", confirmed=True,
        )
        assert len(glass_orders) == 1
        state = purchasing_state(org, version_id)
        assert {item["order_type"] for item in state["orders"]} == {"SUPPLIER_GLASS_PO"}
        profile_orders = confirm_order_type_batch(
            org_id=org, actor_id=users["WORKSHOP_MANAGER"], version_id=version_id,
            order_type="SUPPLIER_PROFILE_PO", confirmed=True,
        )
        assert confirm_order_type_batch(
            org_id=org, actor_id=users["WORKSHOP_MANAGER"], version_id=version_id,
            order_type="SUPPLIER_PROFILE_PO", confirmed=True,
        ) == profile_orders
        assert {
            item["requirement_key"]: item["quantity"]
            for item in purchasing_state(org, version_id)["requirements"]
        } == original_quantities
        with pytest.raises(DatabaseError), transaction.atomic():
            allocate_requirement(
                org_id=org,
                actor_id=users["WORKSHOP_MANAGER"],
                requirement_id=UUID(str(by_type["SUPPLIER_GLASS_PO"][0]["id"])),
                eligibility_id=eligibility_ids["SUPPLIER_GLASS_PO"],
            )

        monkeypatch.setattr("documents.artifacts.SupabaseDocumentStorage", FakeStorage)
        glass_order_id = UUID(glass_orders[0]["id"])
        profile_order_id = UUID(profile_orders[0]["id"])
        glass_artifact = generate_artifact(
            org_id=org, actor_id=users["WORKSHOP_MANAGER"], role="WORKSHOP_MANAGER",
            project_version_id=version_id, order_id=glass_order_id,
            document_type="DOC-02", file_format="XLSX",
        )
        assert generate_artifact(
            org_id=org, actor_id=users["WORKSHOP_MANAGER"], role="WORKSHOP_MANAGER",
            project_version_id=version_id, order_id=glass_order_id,
            document_type="DOC-02", file_format="XLSX",
        )["id"] == glass_artifact["id"]
        generate_artifact(
            org_id=org, actor_id=users["WORKSHOP_MANAGER"], role="WORKSHOP_MANAGER",
            project_version_id=version_id, order_id=profile_order_id,
            document_type="DOC-04", file_format="XLSX",
        )
        assert FakeStorage.upload_calls == 2
        with documentary_backend():
            assert one("SELECT status::text FROM public.orders WHERE id=%s", [glass_order_id])[
                "status"
            ] == "DRAFT"
        with pytest.raises(DocumentaryError, match="confirmation"):
            send_order(
                org_id=org, actor_id=users["WORKSHOP_MANAGER"],
                order_id=glass_order_id, confirmed=False,
            )
        sent = send_order(
            org_id=org, actor_id=users["WORKSHOP_MANAGER"],
            order_id=glass_order_id, confirmed=True,
        )
        assert sent["status"] == "SENT"


def test_historical_render_uses_frozen_snapshot_after_catalog_change(documentary_tenant) -> None:
    org, _, users, _ = documentary_tenant
    project_id, _, operation_id = _seed_project(org, users["OWNER"])
    frozen = _freeze(org, users["OWNER"], project_id, operation_id)
    with as_user(users["OWNER"]):
        _, snapshot = revision_snapshot(UUID(frozen["id"]), org)
    before = _doc01(snapshot)
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE public.profile_articles SET name='LATER CATALOG CHANGE' WHERE sku='MARCO'"
        )
    with as_user(users["OWNER"]):
        _, loaded = revision_snapshot(UUID(frozen["id"]), org)
    assert _doc01(loaded) == before
    assert documentary_sha256_v1(loaded) == documentary_sha256_v1(snapshot)


def test_failed_artifact_registration_removes_the_uploaded_object(
    documentary_tenant, monkeypatch: pytest.MonkeyPatch,
) -> None:
    org, _, users, _ = documentary_tenant
    FakeStorage.uploads = {}
    FakeStorage.upload_calls = 0
    FakeStorage.deleted = []
    project_id, _, operation_id = _seed_project(org, users["OWNER"])
    frozen = _freeze(org, users["OWNER"], project_id, operation_id)
    version_id = UUID(frozen["id"])
    monkeypatch.setattr("documents.artifacts.SupabaseDocumentStorage", FakeStorage)
    original_one = artifacts_module.one

    def failing_one(
        query: object, parameters: Sequence[object] = (), code: str = ""
    ) -> dict[str, object]:
        if str(query).lstrip().upper().startswith("INSERT INTO PUBLIC.DOCUMENT_ARTIFACTS"):
            raise DatabaseError("forced_registration_failure")
        return original_one(query, parameters, code)

    monkeypatch.setattr(artifacts_module, "one", failing_one)
    with as_user(users["OWNER"]), pytest.raises(
        DatabaseError, match="forced_registration_failure"
    ):
        generate_artifact(
            org_id=org, actor_id=users["OWNER"], role="OWNER",
            project_version_id=version_id, order_id=None,
            document_type="DOC-01", file_format="PDF",
        )
    assert FakeStorage.upload_calls == 1
    assert len(FakeStorage.deleted) == 1
    with documentary_backend():
        assert not rows(
            "SELECT id FROM public.document_artifacts WHERE storage_object_key=%s",
            [FakeStorage.deleted[0]],
        )
