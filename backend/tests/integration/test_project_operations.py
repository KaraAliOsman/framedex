"""IA2: real atomic edits, tenant boundaries, identity-preserving undo."""

from uuid import UUID, uuid4

from django.db import DatabaseError, transaction
import pytest

from authentication.errors import ContractAPIException
from backend.tests.integration.test_extras_services import fixture
from backend.tests.integration.test_shot09_documentary import documentary_tenant as documentary_tenant, as_user
from pricing.repository import commercial_backend, rows
from projects.project_ops import apply_project_operations, preview_project_operations, snapshot, signature, undo_project_operations
from projects.serializers import PositionWriteSerializer
from projects.service import create_project, save_position, positions, project_row

pytestmark = pytest.mark.rls_integration


def setup_project(org, owner):
    design = fixture(org, owner)
    with as_user(owner):
        project = create_project(org, owner, {"name": "Operaciones DEMO", "client_name": "Ensayo"})
        data = PositionWriteSerializer(data={"location_tag": "Segundo piso", "quantity": 2,
            "design": {**design, "nominal_width_mm": str(design["nominal_width_mm"]), "nominal_height_mm": str(design["nominal_height_mm"])}})
        data.is_valid(raise_exception=True)
        position = save_position(org, project["id"], data.validated_data)
    return project, position


def apply(org, user, project, ops, key=None):
    preview = preview_project_operations(org, user, project, ops)
    result = apply_project_operations(org, user, project, {"ops": ops, "before_sig": preview["before_sig"], "operation_key": key or str(uuid4())})
    return preview, result


def test_preview_is_read_only_apply_idempotent_and_undo_restores_identity(documentary_tenant):
    org, _, users, _ = documentary_tenant
    owner = users["OWNER"]
    project, position = setup_project(org, owner)
    pid = project["id"]
    ops = [{"op": "duplicate_position", "position_id": str(position["id"]), "count": 4, "location": "Dormitorios"}]
    with as_user(owner):
        before = snapshot(org, pid)
        preview = preview_project_operations(org, owner, pid, ops)
        assert signature(snapshot(org, pid)) == signature(before)
        assert len(preview["diff"]) == 4
        key = str(uuid4())
        request = {"ops": ops, "before_sig": preview["before_sig"], "operation_key": key}
        result = apply_project_operations(org, owner, pid, request)
        repeated = apply_project_operations(org, owner, pid, request)
        assert result["operation_id"] == repeated["operation_id"]
        copies = result["project"]["positions"][1:]
        assert len(copies) == 4
        assert all(p["quantity"] == 2 and p["location_tag"] == "Dormitorios" and p["design"] == position["design"] for p in copies)
        restored = undo_project_operations(org, owner, pid, UUID(result["operation_id"]))
        assert len(restored["project"]["positions"]) == 1
        assert restored["project"]["positions"][0]["id"] == position["id"]
        assert undo_project_operations(org, owner, pid, UUID(result["operation_id"]))["state"] == "UNDONE"


def test_remove_can_restore_the_original_position_and_measurement_evidence(documentary_tenant):
    from backend.tests.integration.test_opening_mounting import mounting_position
    from projects.mounting import measurement_record
    org, _, users, _ = documentary_tenant
    owner = users["OWNER"]
    project, position, _, _ = mounting_position(org, owner)
    with as_user(owner):
        evidence = measurement_record(org, position["id"], "REV-A")
        _, result = apply(org, owner, project["id"], [{"op": "remove_position", "position_id": str(position["id"])}])
        assert positions(org, project["id"]) == []
        restored = undo_project_operations(org, owner, project["id"], UUID(result["operation_id"]))
        assert restored["project"]["positions"][0]["id"] == position["id"]
        assert measurement_record(org, position["id"], "REV-A") == evidence
        assert restored["project"]["positions"][0]["measurements"]["current"] is True


def test_stale_proposal_and_later_edit_refuse_apply_or_undo(documentary_tenant):
    org, _, users, _ = documentary_tenant
    owner = users["OWNER"]
    project, position = setup_project(org, owner)
    with as_user(owner):
        ops = [{"op": "set_quantity", "position_id": str(position["id"]), "quantity": 4}]
        first = preview_project_operations(org, owner, project["id"], ops)
        _, result = apply(org, owner, project["id"], [{"op": "set_location", "position_id": str(position["id"]), "location": "Cocina"}])
        with pytest.raises(ContractAPIException) as error:
            apply_project_operations(org, owner, project["id"], {"ops": ops, "before_sig": first["before_sig"], "operation_key": str(uuid4())})
        assert error.value.contract_code == "proposal_stale"
        apply(org, owner, project["id"], ops)
        with pytest.raises(ContractAPIException) as error:
            undo_project_operations(org, owner, project["id"], UUID(result["operation_id"]))
        assert error.value.contract_code == "undo_stale"


def test_project_ops_are_tenant_scoped_and_evidence_is_immutable(documentary_tenant):
    org, other, users, other_user = documentary_tenant
    owner = users["OWNER"]
    project, position = setup_project(org, owner)
    with as_user(owner):
        ops = [{"op": "set_location", "position_id": str(position["id"]), "location": "Cocina"}]
        _, result = apply(org, owner, project["id"], ops)
        with pytest.raises(DatabaseError), transaction.atomic(), commercial_backend():
            rows("UPDATE project_edit_operations SET request='[]'::jsonb WHERE id=%s RETURNING id", [result["operation_id"]])
        with pytest.raises(DatabaseError), transaction.atomic(), commercial_backend():
            rows("INSERT INTO project_edit_operations(org_id,project_id,actor_id,operation_key,state,request,before_state,after_state) VALUES(%s,%s,%s,%s,'APPLIED','[]','{}','{}') RETURNING id", [org, project["id"], other_user, str(uuid4())])
    with as_user(other_user), commercial_backend():
        assert rows("SELECT id FROM project_edit_operations WHERE org_id=%s", [org]) == []
        with pytest.raises(DatabaseError), transaction.atomic():
            rows("INSERT INTO project_edit_operations(org_id,project_id,actor_id,operation_key,state,request,before_state,after_state) VALUES(%s,%s,%s,%s,'APPLIED','[]','{}','{}') RETURNING id", [other, project["id"], other_user, str(uuid4())])
    with as_user(users["WORKSHOP_MANAGER"]), commercial_backend():
        assert rows("SELECT id FROM project_edit_operations WHERE org_id=%s", [org]) == []


def test_failed_batch_cannot_partially_save(documentary_tenant):
    org, _, users, _ = documentary_tenant
    owner = users["OWNER"]
    project, position = setup_project(org, owner)
    with as_user(owner):
        before = snapshot(org, project["id"])
        from dekopen_engine.design_operations import OperationError
        with pytest.raises(OperationError):
            preview_project_operations(org, owner, project["id"], [
                {"op": "set_quantity", "position_id": str(position["id"]), "quantity": 4},
                {"op": "remove_position", "position_id": str(uuid4())}])
        assert signature(snapshot(org, project["id"])) == signature(before)
        assert project_row(org, project["id"])["status"] == "DRAFT"
