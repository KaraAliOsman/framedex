"""IA2: real atomic edits, tenant boundaries, identity-preserving undo."""

from uuid import UUID, uuid4

from django.db import DatabaseError, transaction
from decimal import Decimal, ROUND_HALF_UP
import pytest

from authentication.errors import ContractAPIException
from backend.tests.integration.test_extras_services import fixture
from backend.tests.integration.test_shot09_documentary import documentary_tenant as documentary_tenant, as_user
from pricing.repository import commercial_backend, rows
from projects.project_ops import apply_project_operations, preview_project_operations, project_operation_state, snapshot, signature, undo_project_operations
from projects.serializers import PositionWriteSerializer
from projects.service import create_project, save_position, positions, project_row
from backend.tests.integration.test_opening_mounting import client_for

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
        assert project_operation_state(org, pid, key) == {"operation_id": None, "state": "PROPOSED"}
        request = {"ops": ops, "before_sig": preview["before_sig"], "operation_key": key}
        result = apply_project_operations(org, owner, pid, request)
        repeated = apply_project_operations(org, owner, pid, request)
        assert result["operation_id"] == repeated["operation_id"]
        assert project_operation_state(org, pid, key) == {"operation_id": result["operation_id"], "state": "APPLIED"}
        copies = result["project"]["positions"][1:]
        assert len(copies) == 4
        assert all(p["quantity"] == 2 and p["location_tag"] == "Dormitorios" and p["design"] == position["design"] for p in copies)
        restored = undo_project_operations(org, owner, pid, UUID(result["operation_id"]))
        assert len(restored["project"]["positions"]) == 1
        assert restored["project"]["positions"][0]["id"] == position["id"]
        assert undo_project_operations(org, owner, pid, UUID(result["operation_id"]))["state"] == "UNDONE"
        assert project_operation_state(org, pid, key) == {"operation_id": result["operation_id"], "state": "UNDONE"}


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


@pytest.mark.parametrize("role", ["OWNER", "ESTIMATOR", "WORKSHOP_MANAGER", "INSTALLER"])
def test_preview_and_apply_require_real_project_writer_permission(documentary_tenant, role):
    org, _, users, _ = documentary_tenant
    project, position = setup_project(org, users["OWNER"])
    client = client_for(users[role])
    ops = [{"op": "set_quantity", "position_id": str(position["id"]), "quantity": 3}]
    path = f"/api/v1/projects/{project['id']}/operations/"
    state = client.get(path + "state/", {"operation_key": str(uuid4())}, HTTP_X_ORGANIZATION_ID=str(org))
    assert state.status_code == (403 if role in {"WORKSHOP_MANAGER", "INSTALLER"} else 200), state.content
    preview = client.post(path + "preview/", {"ops": ops}, format="json", HTTP_X_ORGANIZATION_ID=str(org))
    if role in {"WORKSHOP_MANAGER", "INSTALLER"}:
        assert preview.status_code == 403, preview.content
        result = client.post(path + "apply/", {"ops": ops, "before_sig": "0" * 64,
            "operation_key": str(uuid4())}, format="json", HTTP_X_ORGANIZATION_ID=str(org))
        assert result.status_code == 403, result.content
        return
    assert preview.status_code == 200, preview.content
    simulation = preview.json()["simulations"][0]
    assert simulation["before"]["quantity"] == 2 and simulation["quantity"] == 3
    before_price, after_price = simulation["before"]["price"], simulation["price"]
    if after_price["net"] is not None:
        assert Decimal(after_price["net"]) == (Decimal(after_price["unit_net"]) * 3).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        assert Decimal(after_price["delta_net"]) == Decimal(after_price["net"]) - Decimal(before_price["net"])
    else:
        assert after_price["reason"] and after_price["delta_net"] is None
    result = client.post(path + "apply/", {"ops": ops, "before_sig": preview.json()["before_sig"],
        "operation_key": str(uuid4())}, format="json", HTTP_X_ORGANIZATION_ID=str(org))
    assert result.status_code == 200, result.content
    assert result.json()["project"]["positions"][0]["quantity"] == 3


def test_creation_requires_explicit_catalog_selections_and_all_diffs_have_simulations(documentary_tenant):
    org, _, users, _ = documentary_tenant
    owner = users["OWNER"]
    project, position = setup_project(org, owner)
    design = position["design"]
    glass = design["parametric_tree"]["glass_article_sku"]
    op = {"op": "add_position", "system_id": str(design["system_id"]), "template": "FIXED",
          "dims": {"width_mm": "1500", "height_mm": "1400"}, "location": "Cocina",
          "glass_sku": glass, "color": design["color"]}
    with as_user(owner):
        from dekopen_engine.design_operations import OperationError
        for field in ("glass_sku", "color"):
            with pytest.raises(OperationError):
                preview_project_operations(org, owner, project["id"], [{key: value for key, value in op.items() if key != field}])
        created = preview_project_operations(org, owner, project["id"], [op])
        assert created["simulations"][0]["before"]["product"] is None
        assert created["simulations"][0]["product"]["assembly"]["modules"]
        removed = preview_project_operations(org, owner, project["id"], [{"op": "remove_position", "position_id": str(position["id"])}])
        assert removed["simulations"][0]["product"] is None
        assert removed["simulations"][0]["before"]["product"]["assembly"]["modules"]
        copied = preview_project_operations(org, owner, project["id"], [{"op": "duplicate_position", "position_id": str(position["id"]), "count": 4, "location": "Dormitorios"}])
        assert len(copied["simulations"]) == len(copied["diff"]) == 4


def test_project_operation_history_cannot_be_deleted_even_with_elevated_database_role(documentary_tenant):
    from django.db import connection
    org, _, users, _ = documentary_tenant
    owner = users["OWNER"]
    project, position = setup_project(org, owner)
    with as_user(owner):
        _, result = apply(org, owner, project["id"], [{"op": "set_quantity", "position_id": str(position["id"]), "quantity": 3}])
    with pytest.raises(DatabaseError, match="project_edit_evidence_immutable"), transaction.atomic(), connection.cursor() as cursor:
        cursor.execute("SET LOCAL ROLE NONE")
        cursor.execute("DELETE FROM public.project_edit_operations WHERE id=%s", [result["operation_id"]])


def test_invalid_design_in_shared_simulation_returns_a_public_422(documentary_tenant):
    org, _, users, _ = documentary_tenant
    _, position = setup_project(org, users["OWNER"])
    from projects.ops_registry import product_from_position
    with as_user(users["OWNER"]):
        from projects.service import position_row
        product = product_from_position(position_row(org, position["id"]))
    product["assembly"]["modules"][0]["tree"]["unexpected_field"] = "invalid"
    result = client_for(users["ESTIMATOR"]).post("/api/v1/projects/operations/simulate/", {
        "system_id": str(position["design"]["system_id"]), "color": position["design"]["color"],
        "product": product, "ops": [{"op": "split_bay", "module": "single", "bay": "b1", "axis": "V", "from": "CENTER"}],
    }, format="json", HTTP_X_ORGANIZATION_ID=str(org))
    assert result.status_code == 422, result.content
    assert result.json()["error"]["code"] == "design_operation_invalid"
    assert "unexpected_field" not in result.json()["error"]["detail"]


def test_shared_preview_includes_engine_leaf_and_handle_authority_for_both_drawings(documentary_tenant):
    from projects.ops_registry import product_from_position, simulate_ops
    from projects.service import position_row
    org, _, users, _ = documentary_tenant
    _, position = setup_project(org, users["OWNER"])
    with as_user(users["OWNER"]):
        product = product_from_position(position_row(org, position["id"]))
        result = simulate_ops(org, product, [
            {"op": "set_module_width", "module": "single", "width_mm": "1000"},
            {"op": "set_opening", "module": "single", "opening": "TURN_LEFT"},
        ], position["design"]["system_id"], position["design"]["color"])
    assert result["valid"]
    assert result["before"]["engine"]["status"] == "VALID"
    assert result["before"]["engine"]["modules"][0]["result"].get("opening_leaves", []) == []
    leaf = result["engine"]["modules"][0]["result"]["opening_leaves"][0]
    assert leaf["opening"]["hinge_side"] == "LEFT"
    assert leaf["handle"]["side"] == "RIGHT"
    assert Decimal(leaf["width_mm"]) > 0 and Decimal(leaf["height_mm"]) > 0
    before, after = result["before"]["price"], result["price"]
    assert before["net"] is not None and after["net"] is not None
    # A visible CLP delta must reconcile its two visible integer amounts.
    for price in (before, after):
        assert Decimal(price["net"]) == Decimal(price["net"]).quantize(Decimal("1"))
        assert Decimal(price["net"]) == Decimal(price["unit_net"]).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    assert Decimal(after["delta_net"]) + Decimal(before["net"]) == Decimal(after["net"])
