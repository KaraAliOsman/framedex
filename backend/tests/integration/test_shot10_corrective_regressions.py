"""Integration regression tests for SHOT-10 corrective issues."""

from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from authentication.errors import ContractAPIException
from backend.tests.integration.test_shot09_documentary import (
    FakeStorage,
    _seed_project,
    _tenant,
    as_user,
    documentary_tenant as documentary_tenant,
)
from dekopen_engine.commercial import PricingError
from documents.artifacts import generate_artifact
from documents.repository import DocumentaryError, documentary_backend, one
from documents.service import (
    freeze_revision_a,
    prepare_documentary_inputs,
    save_documentary_inputs,
    revision_snapshot,
)
from pricing.repository import commercial_backend
from pricing.service import apply_operation, preview
from projects import service
from catalogs import service as catalog_service

pytestmark = pytest.mark.rls_integration
D = Decimal


def price_current(org, actor, role, project_id):
    with commercial_backend():
        operation = preview(
            org,
            _tenant(org, role),
            {
                "project_id": project_id,
                "pricing_mode": "COST_PLUS_MARGIN",
                "context_code": "DEFAULT",
                "currency": "CLP",
                "effective_date": date.today().isoformat(),
                "discount_pct": D("0.0000"),
                "target_margin": D("0.35"),
                "segment": "RETAIL",
                "reason": "Corrective test quote",
                "confirmed": False,
                "_actor_id": actor,
            },
        )
        apply_operation(
            org,
            actor,
            role,
            UUID(operation["id"]),
            "Commercial quote apply",
            False,
        )
    return UUID(operation["id"])


def test_missing_workshop_freeze_allows_doc01_blocks_doc03_doc05_doc06(
    documentary_tenant, monkeypatch: pytest.MonkeyPatch
):
    org, _, users, _ = documentary_tenant
    owner = users["OWNER"]
    FakeStorage.uploads = {}
    FakeStorage.upload_calls = 0
    FakeStorage.deleted = []
    monkeypatch.setattr("documents.artifacts.SupabaseDocumentStorage", FakeStorage)

    # 1. Verify prepare_documentary_inputs does NOT invent authority (drains, polishing edges)
    raw_project_id, _, _ = _seed_project(org, owner, valid_annotations=False)
    with as_user(owner):
        with documentary_backend():
            one(
                "UPDATE public.position_documentary_inputs SET glass_polishing='[]'::jsonb WHERE project_id=%s RETURNING id",
                [raw_project_id],
            )
        prepared = prepare_documentary_inputs(org_id=org, project_id=raw_project_id)
        assert len(prepared["positions"]) == 1
        pos_inputs = prepared["positions"][0]
        # Absence must be preserved: no synthesized coordinates or false-edge dictionaries
        assert pos_inputs["workshop_annotations"] == []
        assert pos_inputs["glass_polishing"] == []
        assert pos_inputs["structural_inputs"] == []
        assert pos_inputs["handle_intents"] == []

    # 2. Freeze project with missing workshop annotations directly
    project_id, _, operation_id = _seed_project(org, owner, valid_annotations=False)

    with as_user(owner):
        # Without allow_incomplete_workshop, red inspector blocks freeze
        with pytest.raises(DocumentaryError, match="inspector_red_blocks"):
            freeze_revision_a(
                org_id=org,
                actor_id=owner,
                project_id=project_id,
                pricing_operation_id=operation_id,
                confirmed=True,
                allow_incomplete_workshop=False,
            )

        # With allow_incomplete_workshop=True, quotation freeze succeeds with production_allowed=False
        frozen = freeze_revision_a(
            org_id=org,
            actor_id=owner,
            project_id=project_id,
            pricing_operation_id=operation_id,
            confirmed=True,
            allow_incomplete_workshop=True,
        )
        assert frozen["production_allowed"] is False
        assert frozen["documentary_complete"] is False

        # DOC-01 (commercial quote) must succeed without monkeypatching
        doc01, created = generate_artifact(
            org_id=org,
            actor_id=owner,
            role="OWNER",
            project_version_id=UUID(frozen["id"]),
            order_id=None,
            document_type="DOC-01",
            file_format="PDF",
        )
        assert doc01["document_type"] == "DOC-01"

        # Production / workshop artifacts must fail closed
        for doc_type in ("DOC-03", "DOC-05", "DOC-06"):
            with pytest.raises(DocumentaryError) as exc_info:
                generate_artifact(
                    org_id=org,
                    actor_id=owner,
                    role="OWNER",
                    project_version_id=UUID(frozen["id"]),
                    order_id=None,
                    document_type=doc_type,
                    file_format="PDF",
                )
            assert str(exc_info.value) == "production_document_blocked"


def test_invalid_annotation_target_fails_closed(documentary_tenant):
    org, _, users, _ = documentary_tenant
    owner = users["OWNER"]
    project_id, position_id, _ = _seed_project(org, owner, valid_annotations=True)

    with as_user(owner), documentary_backend():
        policies = one(
            "SELECT placement.id AS placement_id, handles.id AS handle_id, steel.id AS steel_id "
            "FROM public.profile_systems system "
            "JOIN public.manufacturing_placement_policies placement ON placement.system_id=system.id "
            "JOIN public.handle_requirement_policies handles ON handles.system_id=system.id "
            "JOIN public.reinforcement_cut_policies steel ON steel.system_id=system.id "
            "WHERE placement.org_id IS NULL AND handles.org_id IS NULL AND steel.org_id IS NULL LIMIT 1"
        )
        # Invalid bay_id "B99" that does not exist in single bay geometry
        with pytest.raises(DocumentaryError) as exc_info:
            save_documentary_inputs(
                org_id=org,
                actor_id=owner,
                project_id=project_id,
                data={
                    "payment_terms": "Contado",
                    "quotation_valid_until": date(2026, 10, 1),
                    "positions": [{
                        "position_id": position_id,
                        "manufacturing_placement_policy_id": policies["placement_id"],
                        "handle_requirement_policy_id": policies["handle_id"],
                        "reinforcement_cut_policy_id": policies["steel_id"],
                        "workshop_annotations": [{
                            "bay_id": "B99",
                            "leaf_id": None,
                            "bottom_drain_holes_mm": [D("100")],
                            "closing_points_perimeter_mm": None,
                            "continuous_width_mm": D("1000"),
                            "finish_class": "WHITE",
                            "has_coupler": False,
                        }],
                        "structural_inputs": [],
                        "glass_polishing": [],
                        "handle_intents": [],
                        "accessory_schedule": {"schema_version": 1, "coverage": "NONE_REQUIRED", "items": []},
                        "legacy_handle_migration_confirmed": False,
                    }],
                },
            )
        assert str(exc_info.value) == "workshop_annotation_target_invalid"


def test_successor_stale_replay_rejected_with_409(documentary_tenant):
    org, _, users, _ = documentary_tenant
    owner = users["OWNER"]
    project_id, _, op_a = _seed_project(org, owner, valid_annotations=True)

    with as_user(owner):
        # Freeze REV-A
        freeze_revision_a(
            org_id=org,
            actor_id=owner,
            project_id=project_id,
            pricing_operation_id=op_a,
            confirmed=True,
        )

        # Open REV-B with expected_current_revision="REV-A"
        succ_b = service.start_successor(org, project_id, expected_current_revision="REV-A")
        assert succ_b["successor_created"] is True
        assert succ_b["current_revision"] == "REV-B"
        assert succ_b["status"] == "DRAFT"

        # Idempotent retry with same expected_current_revision="REV-A" succeeds without re-creating
        retry_b = service.start_successor(org, project_id, expected_current_revision="REV-A")
        assert retry_b["successor_created"] is False
        assert retry_b["current_revision"] == "REV-B"

        # Freeze REV-B
        op_b = price_current(org, owner, "OWNER", project_id)
        freeze_revision_a(
            org_id=org,
            actor_id=owner,
            project_id=project_id,
            pricing_operation_id=op_b,
            confirmed=True,
        )

        # Now project is at REV-B (QUOTED). Replaying stale expected_current_revision="REV-A" must fail closed with 409
        with pytest.raises(ContractAPIException) as exc_info:
            service.start_successor(org, project_id, expected_current_revision="REV-A")
        assert exc_info.value.status_code == 409
        assert exc_info.value.contract_code == "successor_source_stale"


def test_partial_project_update_and_empty_delta(documentary_tenant):
    org, _, users, _ = documentary_tenant
    owner = users["OWNER"]

    with as_user(owner):
        project = service.create_project(org, owner, {"name": "Proyecto Para Patch"})
        project_id = project["id"]
        # Update only notes_commercial
        updated = service.update_project(
            org,
            project_id,
            {
                "expected_updated_at": project["updated_at"],
                "notes_commercial": "Condiciones especiales actualizadas",
            },
        )
        assert updated["notes_commercial"] == "Condiciones especiales actualizadas"
        assert updated["name"] == project["name"]

        # Update with only expected_updated_at (empty delta)
        fresh = service.project_row(org, project_id)
        noop = service.update_project(
            org,
            project_id,
            {"expected_updated_at": fresh["updated_at"]},
        )
        assert UUID(str(noop["id"])) == project_id


@pytest.mark.parametrize(
    "role",
    ["FRAME", "SASH", "MULLION_V", "MULLION_H", "INVERSOR", "COUPLER", "ADDITIONAL", "THRESHOLD"],
)
def test_catalog_singleton_role_uniqueness(documentary_tenant, role):
    org, _, users, _ = documentary_tenant
    owner = users["OWNER"]

    with as_user(owner):
        # Create a private system
        system = catalog_service.create(
            catalog_service.SYSTEMS,
            org,
            {
                "name": "Sistema Singleton Test",
                "code": f"SYS-{uuid4().hex[:6].upper()}",
                "depth_mm": D("60.00"),
                "material": "PVC",
                "chamber_count": 3,
                "sash_overlap_mm": D("8.00"),
                "glass_clearance_white_mm": D("4.00"),
                "glass_clearance_foil_mm": D("4.00"),
                "pulley_height_mm": D("0.00"),
                "central_overlap_mm": D("0.00"),
                "sliding_lateral_clearance_mm": D("0.00"),
                "sliding_end_add_mm": D("0.00"),
                "corner_bracket_loss_mm": D("0.00"),
                "hook_depth_mm": D("0.00"),
                "door_threshold_mm": D("0.00"),
                "door_bottom_clearance_mm": D("0.00"),
                "rail_type": "dual",
                "sliding_glazing_deduction_width_mm": D("0.00"),
                "sliding_glazing_deduction_height_mm": D("0.00"),
                "door_leaf_side_clearance_mm": D("0.00"),
                "chamber_clearance_mm": None,
                "version": 1,
                "is_active": True,
            },
        )

        first = catalog_service.create(
            catalog_service.ARTICLES,
            org,
            {
                "system_id": system["id"],
                "sku": f"{role}-{uuid4().hex[:6].upper()}",
                "name": "Perfil Principal",
                "role": role,
                "material": "PVC",
                "face_width_mm": D("60.00"),
                "commercial_length_mm": D("6000.00"),
                "welding_loss_mm": D("6.00"),
                "reinforcement_sku": None,
                "reinforcement_gap_mm": D("15.00"),
                "weight_kg_m": D("1.2000"),
                "steel_weight_kg_m": D("0.0000"),
            },
        )
        assert first["role"] == role

        # Every non-bead role resolves to one effective article per system.
        with pytest.raises(ContractAPIException) as exc_info:
            catalog_service.create(
                catalog_service.ARTICLES,
                org,
                {
                    "system_id": system["id"],
                    "sku": f"{role}-2-{uuid4().hex[:6].upper()}",
                    "name": "Segundo Perfil",
                    "role": role,
                    "material": "PVC",
                    "face_width_mm": D("60.00"),
                    "commercial_length_mm": D("6000.00"),
                    "welding_loss_mm": D("6.00"),
                    "reinforcement_sku": None,
                    "reinforcement_gap_mm": D("15.00"),
                    "weight_kg_m": D("1.2000"),
                    "steel_weight_kg_m": D("0.0000"),
                },
            )
        assert exc_info.value.status_code == 409
        assert exc_info.value.contract_code == "catalog_write_conflict"


@pytest.mark.parametrize("missing", ["accessories", "polishing", "both"])
def test_absent_authority_is_never_synthesized(documentary_tenant, monkeypatch, missing):
    org, _, users, _ = documentary_tenant
    owner = users["OWNER"]
    project_id, _, operation_id = _seed_project(org, owner)
    monkeypatch.setattr("documents.artifacts.SupabaseDocumentStorage", FakeStorage)
    with as_user(owner), documentary_backend():
        if missing in ("accessories", "both"):
            one("UPDATE public.position_documentary_inputs SET accessory_schedule=NULL "
                "WHERE project_id=%s RETURNING id", [project_id])
        if missing in ("polishing", "both"):
            one("UPDATE public.position_documentary_inputs SET glass_polishing='[]' "
                "WHERE project_id=%s RETURNING id", [project_id])
        prepared = prepare_documentary_inputs(org_id=org, project_id=project_id)
        if missing in ("accessories", "both"):
            assert prepared["positions"][0]["accessory_schedule"] is None
        else:
            assert prepared["positions"][0]["accessory_schedule"]["coverage"] == "NONE_REQUIRED"
        with pytest.raises(DocumentaryError, match="purchase_authority_incomplete"):
            freeze_revision_a(org_id=org, actor_id=owner, project_id=project_id,
                              pricing_operation_id=operation_id, confirmed=True)
        frozen = freeze_revision_a(org_id=org, actor_id=owner, project_id=project_id,
                                  pricing_operation_id=operation_id, confirmed=True,
                                  allow_incomplete_workshop=True)
        assert not frozen["documentary_complete"] and not frozen["production_allowed"]
        _, snapshot = revision_snapshot(UUID(frozen["id"]), org)
        assert snapshot["purchase_requirements"] is None
        if missing in ("polishing", "both"):
            assert snapshot["positions"][0]["glass_polishing"] == []
        if missing in ("accessories", "both"):
            assert snapshot["positions"][0]["accessory_schedule"] is None
        with documentary_backend():
            assert one("SELECT count(*) AS n FROM public.purchase_projections "
                       "WHERE project_version_id=%s", [frozen["id"]])["n"] == 0
        artifact, _ = generate_artifact(org_id=org, actor_id=owner, role="OWNER",
            project_version_id=UUID(frozen["id"]), order_id=None,
            document_type="DOC-01", file_format="PDF")
        assert artifact["document_type"] == "DOC-01"
        for kind, fmt, order in (("DOC-02", "XLSX", uuid4()), ("DOC-04", "PDF", uuid4()),
                                 ("DOC-03", "PDF", None), ("DOC-05", "PDF", None)):
            with pytest.raises(DocumentaryError, match="production_document_blocked"):
                generate_artifact(org_id=org, actor_id=owner, role="OWNER",
                    project_version_id=UUID(frozen["id"]), order_id=order,
                    document_type=kind, file_format=fmt)


def test_same_bay_geometry_change_invalidates_documentary_authority(documentary_tenant):
    org, _, users, _ = documentary_tenant
    owner = users["OWNER"]
    project_id, position_id, operation_id = _seed_project(org, owner)
    with as_user(owner):
        freeze_revision_a(org_id=org, actor_id=owner, project_id=project_id,
                          pricing_operation_id=operation_id, confirmed=True)
        service.start_successor(org, project_id, expected_current_revision="REV-A")
        previous = prepare_documentary_inputs(org_id=org, project_id=project_id)
        current = service.position_public(service.position_row(org, position_id))
        design = dict(current["design"])
        design["nominal_width_mm"] = D("1500")
        design["nominal_height_mm"] = D(design["nominal_height_mm"])
        service.save_position(org, project_id, {
            "expected_updated_at": current["updated_at"], "location_tag": "FACHADA-NORTE",
            "quantity": current["quantity"], "design": design,
        }, position_id=position_id)
        prepared = prepare_documentary_inputs(org_id=org, project_id=project_id)
        evidence = prepared["positions"][0]
        assert evidence["calculation_hash"] != previous["positions"][0]["calculation_hash"]
        assert evidence["workshop_annotations"] == []
        assert evidence["glass_polishing"] == []
        assert evidence["accessory_schedule"] is None
        assert prepared["payment_terms"] == previous["payment_terms"]
        old_input = {key: value for key, value in previous["positions"][0].items()
                     if key not in ("system_name", "placement_options", "handle_options", "reinforcement_options")}
        with pytest.raises(DocumentaryError, match="documentary_calculation_identity_stale"):
            save_documentary_inputs(org_id=org, actor_id=owner, project_id=project_id,
                data={"payment_terms": previous["payment_terms"],
                      "quotation_valid_until": previous["quotation_valid_until"],
                      "positions": [old_input]})
        operation = price_current(org, owner, "OWNER", project_id)
        with pytest.raises(DocumentaryError, match="documentary_calculation_identity_stale"):
            freeze_revision_a(org_id=org, actor_id=owner, project_id=project_id,
                              pricing_operation_id=operation, confirmed=True,
                              allow_incomplete_workshop=True)


def test_catalog_mutation_after_applied_cannot_strand_project(documentary_tenant):
    from django.db import connection, DatabaseError, transaction
    org, _, users, _ = documentary_tenant
    owner = users["OWNER"]
    project_id, position_id, operation_id = _seed_project(org, owner)
    with connection.cursor() as cursor:
        cursor.execute("RESET ROLE")
    with pytest.raises(DatabaseError, match="catalog_authority_referenced"), transaction.atomic():
        one("UPDATE public.profile_articles SET welding_loss_mm=welding_loss_mm+1 "
            "WHERE system_id=(SELECT system_id FROM public.project_positions WHERE id=%s) "
            "AND role='FRAME' RETURNING id", [position_id])
    with as_user(owner):
        frozen = freeze_revision_a(org_id=org, actor_id=owner, project_id=project_id,
                                  pricing_operation_id=operation_id, confirmed=True)
        assert frozen["documentary_complete"]
        assert service.project_row(org, project_id)["status"] == "QUOTED"


def test_applied_draft_recovery_preserves_history_and_requires_repricing(documentary_tenant):
    from pricing.repository import rows
    org, _, users, _ = documentary_tenant
    owner = users["OWNER"]
    project_id, position_id, operation_id = _seed_project(org, owner)
    with as_user(owner):
        with pytest.raises(PricingError, match="commercial_revision_required"):
            price_current(org, owner, "OWNER", project_id)
        with commercial_backend():
            previous = one("SELECT * FROM public.pricing_operations WHERE id=%s", [operation_id])
        reset = service.reset_draft_pricing(org, project_id, operation_id, "Correct technical inputs")
        assert not reset["pricing_current"]
        with commercial_backend():
            assert one("SELECT * FROM public.pricing_operations WHERE id=%s", [operation_id]) == previous
        audit = rows("SELECT new_record->>'pricing_reset_at' AS reset_at FROM public.price_audit_logs WHERE entity_id=%s "
                     "AND reason='Correct technical inputs'", [project_id])
        assert audit and audit[-1]["reset_at"] is not None
        service.editable(org, project_id)
        with pytest.raises(DocumentaryError, match="applied_pricing_authority_required"):
            freeze_revision_a(org_id=org, actor_id=owner, project_id=project_id,
                              pricing_operation_id=operation_id, confirmed=True)
        operation = price_current(org, owner, "OWNER", project_id)
        with pytest.raises(ContractAPIException, match="Recarga"):
            service.reset_draft_pricing(org, project_id, operation_id, "Stale replay")
        frozen = freeze_revision_a(org_id=org, actor_id=owner, project_id=project_id,
                                  pricing_operation_id=operation, confirmed=True)
        assert frozen["documentary_complete"]
        with pytest.raises(ContractAPIException):
            service.reset_draft_pricing(org, project_id, operation, "Cannot reset history")


def test_backend_readiness_excludes_incomplete_system(documentary_tenant):
    from backend.tests.integration.catalog_fixture import copy_fixed_catalog
    from catalogs.readiness import catalog_readiness
    org, other, users, _ = documentary_tenant
    system = copy_fixed_catalog(org)
    with as_user(users["OWNER"]):
        readiness = catalog_readiness(system, org)
        assert not readiness["quote_ready"]
        assert "manufacturing" in readiness["reasons"]
        assert "inspection" in readiness["reasons"]
        assert not catalog_readiness(system, other)["quote_ready"]
        demo = one("SELECT id FROM public.profile_systems WHERE code='DEMO_60'")["id"]
        assert catalog_readiness(demo, org)["quote_ready"]


@pytest.mark.parametrize("coverage", ["NONE_REQUIRED", "DECLARED"])
def test_explicit_accessory_coverage_survives_prepare_and_freeze(documentary_tenant, coverage):
    from pricing.repository import json_text
    org, _, users, _ = documentary_tenant
    owner = users["OWNER"]
    project, _, operation = _seed_project(org, owner)
    schedule = {"schema_version": 1, "coverage": coverage, "items": []}
    if coverage == "DECLARED":
        schedule["items"] = [{"obligation_id": "seal", "obligation_kind": "SEALING",
            "technical_sku": "SEAL", "purchasing_sku": "BUY-SEAL", "manufacturer_name": "Fixture",
            "order_type": "SUPPLIER_PROFILE_PO", "unit": "EA", "quantity_per_position_unit": 1,
            "description": "Explicit sealing"}]
    with as_user(owner), documentary_backend():
        one("UPDATE public.position_documentary_inputs SET accessory_schedule=%s::jsonb "
            "WHERE project_id=%s RETURNING id", [json_text(schedule), project])
        assert prepare_documentary_inputs(org_id=org, project_id=project)["positions"][0]["accessory_schedule"] == schedule
        frozen = freeze_revision_a(org_id=org, actor_id=owner, project_id=project,
                                  pricing_operation_id=operation, confirmed=True)
        _, snapshot = revision_snapshot(UUID(frozen["id"]), org)
        assert snapshot["positions"][0]["accessory_schedule"]["coverage"] == coverage


def test_pricing_reset_marker_cannot_be_written_directly(documentary_tenant):
    from django.db import DatabaseError, transaction
    org, _, users, _ = documentary_tenant
    project, _, _ = _seed_project(org, users["OWNER"])
    with as_user(users["OWNER"]), pytest.raises(DatabaseError), transaction.atomic():
        one("UPDATE public.projects SET pricing_reset_at=clock_timestamp() WHERE id=%s RETURNING id", [project])


@pytest.mark.parametrize("case", ["null_tenant", "installer", "other_tenant"])
def test_catalog_reservation_requires_editing_membership(documentary_tenant, case):
    from django.db import DatabaseError, transaction
    org, other, users, _ = documentary_tenant
    demo = one("SELECT id FROM public.profile_systems WHERE code='DEMO_60'")["id"]
    actor = users["INSTALLER"] if case == "installer" else users["OWNER"]
    tenant = None if case == "null_tenant" else other if case == "other_tenant" else org
    with as_user(actor), pytest.raises(DatabaseError), transaction.atomic():
        one("SELECT private.reserve_catalog_authority(%s,%s)", [demo, tenant])


def test_readiness_requires_default_frame_reinforcement(documentary_tenant):
    import json
    from backend.tests.integration.catalog_fixture import copy_fixed_catalog
    from catalogs.readiness import catalog_readiness
    from pricing.repository import rows, json_text
    org, _, users, _ = documentary_tenant
    system = copy_fixed_catalog(org)
    demo = one("SELECT id FROM public.profile_systems WHERE code='DEMO_60'")["id"]
    for row in rows("SELECT * FROM public.glass_purchase_mappings WHERE system_id=%s", [demo]):
        if isinstance(row["provenance"], str):
            row["provenance"] = json.loads(row["provenance"])
        row.update(id=uuid4(), system_id=system, org_id=org)
        one("INSERT INTO public.glass_purchase_mappings SELECT "
            "(jsonb_populate_record(NULL::public.glass_purchase_mappings,%s::jsonb)).* RETURNING id",
            [json_text(row)])
    one("UPDATE public.profile_articles SET reinforcement_sku=NULL "
        "WHERE system_id=%s AND role='FRAME' RETURNING id", [system])
    with as_user(users["OWNER"]):
        assert "purchase" not in catalog_readiness(system, org)["reasons"]
    rows("DELETE FROM public.reinforcement_articles WHERE system_id=%s RETURNING id", [system])
    with as_user(users["OWNER"]):
        assert "purchase" in catalog_readiness(system, org)["reasons"]
