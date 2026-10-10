"""P14 real PostgreSQL: CRUD RBAC, immutable evidence and reviewed generations."""
from copy import deepcopy
import hashlib
import json
from uuid import UUID

from django.db import DatabaseError, transaction
import pytest

from backend.tests.integration.test_shot09_documentary import documentary_tenant as documentary_tenant, as_user, _seed_project, _freeze
from backend.tests.integration.test_shot08_pricing import owner_client
from backend.tests.integration.test_operator_station import setup_work
from documents.repository import documentary_backend, one, rows
from engine.tests.test_cnc_authorization import SECTION
from engine.tests.test_operations import _member, _unit
from dekopen_engine.models import ProfileRole
from dekopen_engine.operations import operations_from_plan
from dekopen_engine.cnc_authorization import section_fingerprint
from production import cnc

pytestmark = pytest.mark.rls_integration


def tool_body():
    return {"code":"end_mill","name":"Fresa DEMO de prueba","kind":"END_MILL",
            "diameter_mm":"10","working_length_mm":"30","max_depth_mm":"20",
            "compatible_kinds":["END_MACHINING"],"authority_source":"Fixture P14 no certificado"}


def machine_body(tool_id):
    return {"code":"CNC-P14","name":"Fresadora DEMO","machine_type":"END_MILLER",
            "controller_family":"NEUTRAL","coordinate_systems":["MEMBER_PLAN"],
            "supported_kinds":["END_MACHINING"],"supported_faces":["START_EDGE","END_EDGE"],
            "axes":["X"],"max_member_length_mm":"6000","safe_margin_mm":"10",
            "clamp_zones":[{"start_mm":"450","end_mm":"550","label":"Mordaza A"}],
            "clamps_declared":True,"tool_ids":[tool_id],"postprocessor_id":"neutral-ops-v1",
            "postprocessor_version":"1","authority_source":"Sujeción DEMO revisada",
            "profile_setups":[{"profile_sku":"WS-P1","section_fingerprint":section_fingerprint(SECTION),
                "loading_orientation":"EXTERIOR_UP","axial_datum":"MEMBER_START","source":"Fixture de montaje"}]}


def declare(client, org):
    headers = {"HTTP_X_ORGANIZATION_ID":str(org)}
    tool = client.post("/api/v1/production/cnc/tools/",tool_body(),format="json",**headers)
    assert tool.status_code == 201,tool.data
    machine = client.post("/api/v1/production/cnc/machines/",machine_body(tool.json()["id"]),format="json",**headers)
    assert machine.status_code == 201,machine.data
    return tool.json(), machine.json()


def test_crud_returns_updated_rows_audits_retirement_and_is_private(documentary_tenant):
    org,other,users,other_user = documentary_tenant
    manager,estimator = owner_client(users["WORKSHOP_MANAGER"]),owner_client(users["ESTIMATOR"])
    tool,machine = declare(manager,org)
    assert isinstance(tool["diameter_mm"], str)
    assert isinstance(machine["max_member_length_mm"], str)
    headers = {"HTTP_X_ORGANIZATION_ID":str(org)}
    response = manager.patch(f'/api/v1/production/cnc/tools/{tool["id"]}/',
        {"name":"Fresa revisada","active":False},format="json",**headers)
    assert response.status_code == 200,response.data
    assert response.json()["name"] == "Fresa revisada" and response.json()["active"] is False
    stale = manager.patch(f'/api/v1/production/cnc/tools/{tool["id"]}/',
        {"name":"Obsolete tool review","expected_revision":tool["authority_revision"]},format="json",**headers)
    assert stale.status_code == 422 and stale.data["error"]["code"] == "cnc_authority_stale"
    response = manager.patch(f'/api/v1/production/cnc/machines/{machine["id"]}/',
        {"name":"Célula revisada","active":False},format="json",**headers)
    assert response.status_code == 200 and response.json()["name"] == "Célula revisada"
    stale = manager.patch(f'/api/v1/production/cnc/machines/{machine["id"]}/',
        {"name":"Obsolete machine review","expected_revision":machine["authority_revision"]},format="json",**headers)
    assert stale.status_code == 422 and stale.data["error"]["code"] == "cnc_authority_stale"
    assert estimator.post("/api/v1/production/cnc/tools/",tool_body(),format="json",**headers).status_code == 403
    assert estimator.patch(f'/api/v1/production/cnc/machines/{machine["id"]}/',
        {"active":True},format="json",**headers).status_code == 403
    with as_user(other_user):
        assert cnc.list_tools(org_id=org) == [] and cnc.list_machines(org_id=org) == []
        assert rows("SELECT * FROM cnc_authority_events WHERE org_id=%s",[org]) == []
    with as_user(users["WORKSHOP_MANAGER"]):
        events = rows("SELECT action,previous,current FROM cnc_authority_events WHERE org_id=%s ORDER BY created_at",[org])
        assert len(events) == 4 and [e["action"] for e in events] == ["CREATE","CREATE","RETIRE","RETIRE"]
        with documentary_backend(),pytest.raises(DatabaseError),transaction.atomic():
            rows("DELETE FROM cnc_tools WHERE id=%s RETURNING id",[tool["id"]])
        with documentary_backend(),pytest.raises(DatabaseError),transaction.atomic():
            rows("UPDATE cnc_authority_events SET actor_label='changed' WHERE org_id=%s RETURNING id",[org])
    with as_user(users["ESTIMATOR"]),pytest.raises(DatabaseError),transaction.atomic():
        cnc.update_tool(org_id=org,tool_id=UUID(tool["id"]),data={"active":True})
    with as_user(users["WORKSHOP_MANAGER"]),documentary_backend(),pytest.raises(DatabaseError),transaction.atomic():
        rows("UPDATE cnc_machines SET org_id=%s WHERE id=%s RETURNING id",[other,machine["id"]])


def physical_bundle(order):
    unit = _unit(members=[_member(ProfileRole.MULLION_V,"990","5")])
    member = unit.members[0]
    return {"order":{"id":str(order),"status":"RELEASED","order_code":"OT-P12-DEMO"},
            "ops":operations_from_plan(bars=[],fact_units=[unit]),"ops_issues":[],
            "fact_units":[unit],"member_labels":{member.member_id:"P01-U01-M01"},
            "member_lengths":{member.member_id:member.cut_length_mm},"sections":{member.member_id:SECTION},
            "declared_gaps":[{"kind":"DRAINAGE","detail":"Emisor no implementado","source":"Anotación sellada"}],
            "identity":{"order_code":"OT-P12-DEMO","project_code":"P12-DEMO","revision_code":"REV-A","position_id":"pos-1","plan_seed":"42"},
            "input_fingerprint":"a"*64}


def test_preview_confirmation_replay_staleness_download_and_immutable_history(documentary_tenant,monkeypatch):
    org,_,users,_ = documentary_tenant
    _,_,order,_ = setup_work(org,users)
    manager = owner_client(users["WORKSHOP_MANAGER"])
    tool,machine = declare(manager,org)
    bundle = physical_bundle(order)
    monkeypatch.setattr(cnc,"_order_ops",lambda **kwargs:deepcopy(bundle))
    member_id = bundle["fact_units"][0].members[0].member_id
    headers = {"HTTP_X_ORGANIZATION_ID":str(org)}
    base = f"/api/v1/production/orders/{order}/cnc/"
    body = {"machine_id":machine["id"],"member_id":member_id}
    preview = manager.post(base+"preview/",body,format="json",**headers)
    assert preview.status_code == 200,preview.data
    review = preview.json()
    assert review["verdict"] == "WARN" and len(review["declared_unemitted"]) == 1
    assert review["preview"]["marks"][1]["x_mm"] == "1000"
    confirmed = {**body,"expected_preview":review["review_fingerprint"],"confirmed":True}
    denied = manager.post(base+"programs/",{**confirmed,"confirmed":False},format="json",**headers)
    assert denied.status_code == 422 and denied.data["error"]["code"] == "cnc_preview_required"
    first = manager.post(base+"programs/",confirmed,format="json",**headers)
    assert first.status_code == 201,first.data
    replay = manager.post(base+"programs/",confirmed,format="json",**headers)
    assert replay.status_code == 201 and replay.json()["id"] == first.json()["id"]
    assert replay.json()["files"] == first.json()["files"]
    program = first.json()
    manifest = json.loads(program["files"]["manifest.json"])
    assert manifest["plan_seed"] == "42" and manifest["plan_fingerprint"] == "a"*64
    for name, content in program["files"].items():
        response = manager.get(f'/api/v1/production/cnc/programs/{program["id"]}/file/{name}',**headers)
        assert response.status_code == 200,response.content
        assert response.content.decode() == content
        if name != "manifest.json":
            assert hashlib.sha256(response.content).hexdigest() == manifest["files"][name]["sha256"]
    saved = one("SELECT files::text FROM cnc_programs WHERE id=%s",[program["id"]])["files"]
    assert manager.get(base+"programs/",**headers).json()["programs"][0]["status"] == "CURRENT"
    with as_user(users["WORKSHOP_MANAGER"]),documentary_backend(),pytest.raises(DatabaseError),transaction.atomic():
        rows("UPDATE cnc_programs SET files='{}' WHERE id=%s RETURNING id",[program["id"]])
    bundle["input_fingerprint"] = "b"*64
    stale = manager.post(base+"programs/",confirmed,format="json",**headers)
    assert stale.status_code == 422 and stale.data["error"]["code"] == "cnc_preview_stale"
    assert manager.get(f'/api/v1/production/cnc/programs/{program["id"]}/file/operations.json',**headers).status_code == 422
    newer = manager.post(base+"preview/",body,format="json",**headers).json()
    assert newer["diff"]["has_previous"] and newer["diff"]["added"] == []
    second = manager.post(base+"programs/",{**confirmed,"expected_preview":newer["review_fingerprint"]},format="json",**headers)
    assert second.status_code == 201,second.data
    history = manager.get(base+"programs/",**headers).json()["programs"]
    assert history[1]["replacement_id"] == second.json()["id"]
    assert one("SELECT files::text FROM cnc_programs WHERE id=%s",[program["id"]])["files"] == saved
    manager.patch(f'/api/v1/production/cnc/tools/{tool["id"]}/',{"active":False},format="json",**headers)
    blocked = manager.post(base+"preview/",body,format="json",**headers).json()
    assert blocked["verdict"] == "BLOCK"
    assert any(v["code"] == "no_compatible_tool" for v in blocked["blockers"])
    assert manager.get(base+"programs/",**headers).json()["programs"][0]["status"] == "SUPERSEDED"


def test_new_freeze_seals_sections_and_never_rewrites_an_existing_version(documentary_tenant):
    org,_,users,_ = documentary_tenant
    project,_,operation = _seed_project(org,users["OWNER"])
    version = _freeze(org,users["OWNER"],project,operation)
    first = one("SELECT snapshot_json::text FROM project_versions WHERE id=%s",[version["id"]])["snapshot_json"]
    snapshot = json.loads(first)
    assert "profile_sections" in snapshot["positions"][0]
    _freeze(org,users["OWNER"],project,operation)
    assert one("SELECT snapshot_json::text FROM project_versions WHERE id=%s",[version["id"]])["snapshot_json"] == first
