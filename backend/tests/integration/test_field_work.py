"""P23 commands under real PostgreSQL: replay, privacy, seal and source preservation."""

import base64
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from django.db import connection, DatabaseError, transaction
import pytest

from authentication.errors import ContractAPIException
from backend.tests.integration.test_shot09_documentary import (
    documentary_tenant as documentary_tenant,
    as_user,
    _seed_project,
    _freeze,
    _tenant,
)
from backend.tests.integration.test_shot08_pricing import owner_client
from backend.tests.integration.test_opening_mounting import mounting_position
from backend.tests.test_delivery_confirmations import _PNG
from documents.repository import one, rows, decoded, json_text, documentary_backend
from production import field, service, confirmations, dispatch_notes

pytestmark = pytest.mark.rls_integration
PHOTO = base64.b64encode(_PNG).decode("ascii")


class Storage:
    values = {}

    def upload_immutable(self, key, content, media):
        assert key not in self.values or self.values[key] == content
        self.values[key] = content

    def signed_url(self, key, expires_in=600):
        assert key in self.values
        return "https://private.example.test/" + key

    def delete_object(self, key):
        self.values.pop(key, None)


@pytest.fixture(autouse=True)
def external_storage(monkeypatch):
    Storage.values = {}
    monkeypatch.setattr(field, "SupabaseDocumentStorage", Storage)
    monkeypatch.setattr(confirmations, "SupabaseDocumentStorage", Storage)
    monkeypatch.setattr(dispatch_notes, "SupabaseDocumentStorage", Storage)


def new_measurement(org, users):
    project, position, surveys, _ = mounting_position(org, users["OWNER"])
    body = {
        "operation_key": uuid4(),
        "project_id": UUID(str(project["id"])),
        "kind": "MEASUREMENT",
        "assigned_to": users["INSTALLER"],
        "planned_on": date(2026, 10, 11),
        "team": "Medición norte",
        "address": "Av. Prat 123, Santiago",
        "units": [{"position_id": UUID(str(position["id"])), "unit_index": 1}],
    }
    with as_user(users["WORKSHOP_MANAGER"]):
        visit = field.schedule(org, users["WORKSHOP_MANAGER"], body)["visit"]
    survey = surveys[0].model_dump(mode="json")
    survey["widths_mm"] = [survey["widths_mm"][0]] * 3
    survey["heights_mm"] = [survey["heights_mm"][0]] * 3
    survey["origin"] = "SITE"
    return body, visit, position, survey


def cmd(position, **extra):
    return {
        "operation_key": uuid4(),
        "kind": "MEASURE",
        "position_id": UUID(str(position["id"])),
        "unit_index": 1,
        "photo_b64": PHOTO,
        "note": "Comprobación en obra",
        **extra,
    }


def test_scoped_agenda_and_receipts_do_not_become_capabilities(documentary_tenant):
    org, other, users, other_user = documentary_tenant
    body, visit, position, survey = new_measurement(org, users)
    with as_user(users["WORKSHOP_MANAGER"]):
        assert field.schedule(org, users["WORKSHOP_MANAGER"], body)["visit"]["id"] == visit["id"]
    with as_user(users["INSTALLER"]):
        workspace = field.workspace(org, users["INSTALLER"])
        assert (
            len(workspace["visits"]) == 1
            and workspace["projects"] == []
            and workspace["assignees"] == []
        )
        private = {
            "price_net",
            "cost_net",
            "total_price_net",
            "client_email",
            "notes_internal",
            "pricing",
            "snapshot_json",
            "cost_rate",
            "selling_rate",
            "total_cost",
            "total_price",
        }
        assert not any(f'"{name}"' in json_text(workspace) for name in private)
        result = field.command(
            org, users["INSTALLER"], visit["id"], cmd(position, measurements=[survey])
        )
        assert result["applied"]
    with as_user(other_user):
        assert rows("SELECT id FROM public.field_visits WHERE org_id=%s", [org]) == []
        assert rows("SELECT id FROM public.field_assets WHERE org_id=%s", [org]) == []
        assert rows("SELECT operation_key FROM public.field_receipts WHERE org_id=%s", [org]) == []
        with pytest.raises(Exception):
            field.asset_access(org, other_user, result["result"]["photo"]["id"])
    client = owner_client(users["INSTALLER"])
    assert (
        client.get("/api/v1/production/field/", HTTP_X_ORGANIZATION_ID=str(other)).status_code
        == 403
    )
    assert (
        client.post(
            "/api/v1/production/field/schedule/",
            field.public(body),
            format="json",
            HTTP_X_ORGANIZATION_ID=str(org),
        ).status_code
        == 403
    )


def test_lost_reply_replays_once_and_changed_payload_conflicts(documentary_tenant):
    org, _, users, _ = documentary_tenant
    _, visit, position, survey = new_measurement(org, users)
    data = cmd(position, measurements=[survey])
    with as_user(users["INSTALLER"]):
        first = field.command(org, users["INSTALLER"], visit["id"], data)
        again = field.command(org, users["INSTALLER"], visit["id"], data)
        assert first == again
        assert (
            one("SELECT count(*) AS n FROM field_events WHERE visit_id=%s", [visit["id"]])["n"] == 1
        )
        assert (
            one(
                "SELECT count(*) AS n FROM field_assets WHERE visit_id=%s AND kind='PHOTO'",
                [visit["id"]],
            )["n"]
            == 1
        )
        with pytest.raises(ContractAPIException) as error:
            field.command(org, users["INSTALLER"], visit["id"], {**data, "note": "Otros datos"})
        assert error.value.status_code == 409
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE tenancy_memberships SET is_active=false WHERE org_id=%s AND user_id=%s",
            [org, users["INSTALLER"]],
        )
    with as_user(users["INSTALLER"]), pytest.raises(ContractAPIException) as error:
        field.command(org, users["INSTALLER"], visit["id"], data)
    assert error.value.status_code == 403


def test_invalid_image_rolls_back_and_evidence_cannot_be_rewritten(documentary_tenant):
    org, _, users, _ = documentary_tenant
    _, visit, position, survey = new_measurement(org, users)
    with as_user(users["INSTALLER"]):
        with pytest.raises(ContractAPIException), transaction.atomic():
            field.command(
                org,
                users["INSTALLER"],
                visit["id"],
                cmd(position, photo_b64=base64.b64encode(b"PNG").decode(), measurements=[survey]),
            )
        assert rows("SELECT id FROM field_assets WHERE visit_id=%s", [visit["id"]]) == []
        result = field.command(
            org, users["INSTALLER"], visit["id"], cmd(position, measurements=[survey])
        )
        for table in ("field_assets", "field_events", "field_receipts"):
            with pytest.raises(DatabaseError), transaction.atomic(), documentary_backend():
                rows(
                    f"UPDATE {table} SET org_id=%s WHERE visit_id=%s RETURNING org_id",
                    [org, visit["id"]],
                )
        asset = result["result"]["photo"]
        assert field.asset_access(org, users["INSTALLER"], asset["id"])["signed_url"].startswith(
            "https://private."
        )
    with pytest.raises(DatabaseError), transaction.atomic():
        rows(
            "INSERT INTO field_assets(org_id,visit_id,position_id,unit_index,kind,storage_object_key,media_type,file_sha256,byte_size,payload_json,created_by) "
            "VALUES(%s,%s,%s,2,'PHOTO','invalid','image/png',%s,1,'{}',%s) RETURNING id",
            [org, visit["id"], position["id"], "a" * 64, users["OWNER"]],
        )


def dispatched(org, users, *, delivered=True, send=True):
    project, position, operation = _seed_project(org, users["OWNER"])
    frozen = _freeze(org, users["OWNER"], project, operation)
    with as_user(users["WORKSHOP_MANAGER"]):
        service.release_production(
            org_id=org, version_id=UUID(frozen["id"]), actor_id=users["WORKSHOP_MANAGER"]
        )
        with documentary_backend():
            order = one(
                "SELECT id,order_code FROM orders WHERE org_id=%s AND project_version_id=%s AND order_type='WORKSHOP_OT'",
                [org, frozen["id"]],
            )
            rows("UPDATE orders SET status='COMPLETED' WHERE id=%s RETURNING id", [order["id"]])
        service.generate_packing_manifest(
            org_id=org, order_id=order["id"], actor_id=users["WORKSHOP_MANAGER"]
        )
        if send:
            service.schedule_delivery(
                org_id=org,
                order_id=order["id"],
                actor_id=users["WORKSHOP_MANAGER"],
                scheduled_date="2026-10-11",
                time_window="AM",
                address="Obra Norte",
            )
            service.dispatch_work_order(
                org_id=org, order_id=order["id"], actor_id=users["WORKSHOP_MANAGER"]
            )
            service.transition_delivery(
                org_id=org,
                order_id=order["id"],
                actor_id=users["WORKSHOP_MANAGER"],
                to_status="ON_ROUTE",
            )
    if delivered and send:
        with as_user(users["INSTALLER"]):
            confirmations.confirm_delivery(
                org_id=org,
                order_id=order["id"],
                actor_id=users["INSTALLER"],
                receiver_name="Cliente DEMO",
                receiver_rut="12.345.678-5",
                signature_b64=PHOTO,
                payment=None,
            )
    body = {
        "operation_key": uuid4(),
        "project_id": project,
        "project_version_id": UUID(frozen["id"]),
        "kind": "INSTALLATION" if send else "DELIVERY",
        "assigned_to": users["INSTALLER"],
        "planned_on": date(2026, 10, 11),
        "team": "Instalación norte",
        "units": [{"position_id": position, "unit_index": 1, "order_id": order["id"]}],
    }
    with as_user(users["WORKSHOP_MANAGER"]):
        visit = field.schedule(org, users["WORKSHOP_MANAGER"], body)["visit"]
    return body, visit, order, frozen


def test_mobile_chain_partial_reception_and_field_remake_preserve_source(documentary_tenant):
    org, _, users, _ = documentary_tenant
    body, visit, order, frozen = dispatched(org, users)
    unit = visit["context"]["units"][0]
    check = {
        "operation_key": uuid4(),
        "kind": "CHECK",
        "position_id": UUID(unit["position_id"]),
        "unit_index": 1,
        "scan": unit["label_code"],
        "photo_b64": PHOTO,
        "checks": dict.fromkeys(field.CHECKS, True),
    }
    with as_user(users["INSTALLER"]):
        field.command(org, users["INSTALLER"], visit["id"], check)
        incident = field.command(
            org,
            users["INSTALLER"],
            visit["id"],
            {
                **check,
                "operation_key": uuid4(),
                "kind": "INCIDENT",
                "incident_kind": "DAMAGE",
                "note": "Perfil golpeado en obra",
            },
        )
        receipt = {
            "operation_key": uuid4(),
            "kind": "RECEIVE",
            "receiver_name": "Cliente DEMO",
            "receiver_rut": "12.345.678-5",
            "signature_b64": PHOTO,
            "confirmed": True,
        }
        act = field.command(org, users["INSTALLER"], visit["id"], receipt)
        assert field.command(org, users["INSTALLER"], visit["id"], receipt) == act
    original = one("SELECT status,payload_json FROM orders WHERE id=%s", [order["id"]])
    assert original["status"] == "DISPATCHED"  # Unit 2 still has no installation act.
    with as_user(users["WORKSHOP_MANAGER"]):
        solved = field.command(
            org,
            users["WORKSHOP_MANAGER"],
            visit["id"],
            {
                "operation_key": uuid4(),
                "kind": "RESOLVE",
                "incident_id": incident["result"]["incident"]["id"],
                "resolution_kind": "REMAKE",
                "confirmed": True,
                "note": "Reponer una unidad dañada conservando la fuente",
            },
        )
        remake = one(
            "SELECT payload_json,status FROM orders WHERE id=%s",
            [solved["result"]["resolution"]["remake_order_id"]],
        )
        payload = decoded(remake["payload_json"])
        assert payload["quantity"] == 1 and payload["field_incident"]["source_unit_index"] == 1
        assert (
            not {"optimization", "packing", "cnc_export", "dxf_export", "operations_export"}
            & payload.keys()
        )
    assert original == one("SELECT status,payload_json FROM orders WHERE id=%s", [order["id"]])
    actrow = one(
        "SELECT storage_object_key,file_sha256,payload_json FROM field_assets WHERE visit_id=%s AND kind='ACT'",
        [visit["id"]],
    )
    assert Storage.values[actrow["storage_object_key"]].startswith(b"%PDF")
    with pytest.raises(DatabaseError), transaction.atomic():
        rows(
            "UPDATE field_assets SET payload_json='{}' WHERE visit_id=%s RETURNING id",
            [visit["id"]],
        )
    assert actrow == one(
        "SELECT storage_object_key,file_sha256,payload_json FROM field_assets WHERE visit_id=%s AND kind='ACT'",
        [visit["id"]],
    )


def checked(org, users, visit):
    unit = visit["context"]["units"][0]
    with as_user(users["INSTALLER"]):
        return field.command(
            org,
            users["INSTALLER"],
            visit["id"],
            {
                "operation_key": uuid4(),
                "kind": "CHECK",
                "position_id": UUID(unit["position_id"]),
                "unit_index": unit["unit_index"],
                "scan": unit["label_code"],
                "photo_b64": PHOTO,
                "checks": dict.fromkeys(field.CHECKS, True),
            },
        )


def receive_body(kind="RECEIVE", **extra):
    return {
        "operation_key": uuid4(),
        "kind": kind,
        "receiver_name": "Ana Pérez",
        "receiver_rut": "12.345.678-5",
        "signature_b64": PHOTO,
        "confirmed": True,
        **extra,
    }


def test_partial_act_requires_signed_delivery_for_exact_unit(documentary_tenant):
    org, _, users, _ = documentary_tenant
    _, visit, _, _ = dispatched(org, users, delivered=False)
    checked(org, users, visit)
    with as_user(users["INSTALLER"]), pytest.raises(ContractAPIException) as error:
        field.command(org, users["INSTALLER"], visit["id"], receive_body())
    assert "entrega firmada" in str(error.value.detail)
    assert rows("SELECT id FROM field_assets WHERE visit_id=%s AND kind='ACT'", [visit["id"]]) == []


def test_load_depart_and_client_delivery_seal_one_exact_trip(documentary_tenant):
    org, _, users, _ = documentary_tenant
    _, visit, order, _ = dispatched(org, users, send=False)
    with as_user(users["WORKSHOP_MANAGER"]):
        with pytest.raises(ContractAPIException):
            field.command(
                org,
                users["WORKSHOP_MANAGER"],
                visit["id"],
                {"operation_key": uuid4(), "kind": "DEPART", "confirmed": True},
            )
    unit = visit["context"]["units"][0]
    with as_user(users["INSTALLER"]):
        field.command(
            org,
            users["INSTALLER"],
            visit["id"],
            {
                "operation_key": uuid4(),
                "kind": "LOAD",
                "position_id": UUID(unit["position_id"]),
                "unit_index": 1,
                "scan": unit["label_code"],
            },
        )
        with pytest.raises(ContractAPIException) as error:
            field.command(
                org,
                users["INSTALLER"],
                visit["id"],
                {"operation_key": uuid4(), "kind": "DEPART", "confirmed": True},
            )
        assert error.value.status_code == 403
    with as_user(users["WORKSHOP_MANAGER"]):
        departure = {"operation_key": uuid4(), "kind": "DEPART", "confirmed": True}
        first = field.command(org, users["WORKSHOP_MANAGER"], visit["id"], departure)
        assert field.command(org, users["WORKSHOP_MANAGER"], visit["id"], departure) == first
        assert len(rows("SELECT id FROM dispatch_notes WHERE work_order_id=%s", [order["id"]])) == 1
    with as_user(users["INSTALLER"]):
        body = receive_body("DELIVER")
        result = field.command(org, users["INSTALLER"], visit["id"], body)
        assert result["visit"]["status"] == "CLOSED"
        assert field.command(org, users["INSTALLER"], visit["id"], body) == result
    assert one(
        "SELECT unit_indexes FROM delivery_confirmations c JOIN deliveries d ON d.id=c.delivery_id WHERE c.order_id=%s",
        [order["id"]],
    )["unit_indexes"] == [1]
    assert one("SELECT status FROM orders WHERE id=%s", [order["id"]])["status"] == "DISPATCHED"


def test_service_act_never_credits_installation_and_whole_order_needs_both_units(
    documentary_tenant,
):
    org, _, users, _ = documentary_tenant
    body, visit, order, _ = dispatched(org, users)
    service_body = {
        **body,
        "operation_key": uuid4(),
        "kind": "SERVICE",
        "units": [{**body["units"][0], "unit_index": 2}],
    }
    with as_user(users["WORKSHOP_MANAGER"]):
        service_visit = field.schedule(org, users["WORKSHOP_MANAGER"], service_body)["visit"]
    with as_user(users["INSTALLER"]):
        field.command(
            org,
            users["INSTALLER"],
            service_visit["id"],
            receive_body(photo_b64=PHOTO, note="Regulación y comprobación del herraje"),
        )
    checked(org, users, visit)
    with as_user(users["INSTALLER"]):
        field.command(org, users["INSTALLER"], visit["id"], receive_body())
    assert one("SELECT status FROM orders WHERE id=%s", [order["id"]])["status"] == "DISPATCHED"
    with as_user(users["WORKSHOP_MANAGER"]):
        warranty_context={**visit["context"],"approved_at":"2026-10-01T10:00:00-03:00","warranty_terms":{"warranty_days":365,"warranty_start":"INSTALLATION"}}
        assert field.warranty(org,warranty_context,order["id"],1)["expires_on"] is not None
        assert field.warranty(org,warranty_context,order["id"],2)["expires_on"] is None
        second = field.schedule(
            org,
            users["WORKSHOP_MANAGER"],
            {**service_body, "operation_key": uuid4(), "kind": "INSTALLATION"},
        )["visit"]
    checked(org, users, second)
    with as_user(users["INSTALLER"]):
        field.command(org, users["INSTALLER"], second["id"], receive_body())
    assert one("SELECT status FROM orders WHERE id=%s", [order["id"]])["status"] == "INSTALLED"


def test_two_installers_have_distinct_tenant_codes_and_live_assurance(documentary_tenant):
    from authentication.rls import authenticated_rls_context

    org, _, users, _ = documentary_tenant
    _, visit, position, _ = new_measurement(org, users)
    second_actor = uuid4()
    rows(
        "INSERT INTO tenancy_memberships(org_id,user_id,role) VALUES(%s,%s,'INSTALLER') RETURNING user_id",
        [org, second_actor],
    )
    with as_user(users["WORKSHOP_MANAGER"]):
        field.command(
            org,
            users["WORKSHOP_MANAGER"],
            visit["id"],
            {"operation_key": uuid4(), "kind": "CANCEL"},
        )
        second = field.schedule(
            org,
            users["WORKSHOP_MANAGER"],
            {
                "operation_key": uuid4(),
                "kind": "MEASUREMENT",
                "project_id": visit["project_id"],
                "assigned_to": second_actor,
                "planned_on": date(2026, 10, 12),
                "team": "Segundo equipo",
                "address": "Obra Norte",
                "units": [{"position_id": position["id"], "unit_index": 1}],
            },
        )["visit"]
    reports = []
    for actor, target in ((users["INSTALLER"], visit), (second_actor, second)):
        with as_user(actor):
            reports.append(
                field.command(
                    org,
                    actor,
                    target["id"],
                    cmd(position, kind="INCIDENT", incident_kind="MEASURE", note="Vano comprobado"),
                )["result"]["incident"]["code"]
            )
    assert reports == ["INC-000001", "INC-000002"]
    rows("UPDATE tenancy_organizations SET require_mfa=true WHERE id=%s RETURNING id", [org])
    with (
        authenticated_rls_context(
            {"sub": str(second_actor), "role": "authenticated", "aal": "aal1"}
        ),
        documentary_backend(),
    ):
        assert rows("SELECT id FROM field_visits WHERE org_id=%s", [org]) == []
        with pytest.raises(ContractAPIException) as error:
            field.workspace(org, second_actor)
        assert error.value.status_code == 403


def test_reviewed_measurement_replays_without_changing_source(documentary_tenant):
    org, _, users, _ = documentary_tenant
    _, visit, position, survey = new_measurement(org, users)
    with as_user(users["INSTALLER"]):
        event = field.command(
            org, users["INSTALLER"], visit["id"], cmd(position, measurements=[survey])
        )
    request = {
        "measurement_event_id": UUID(event["event_id"]),
        "reason": "Verificación de vano DEMO",
        "confirmed": False,
    }
    with as_user(users["OWNER"]):
        proposal = field.review_measurement(
            org, users["OWNER"], visit["id"], request, _tenant(org, "OWNER")
        )
        applied = field.review_measurement(
            org,
            users["OWNER"],
            visit["id"],
            {**request, "confirmed": True, "proposal_token": proposal["proposal_token"]},
            _tenant(org, "OWNER"),
        )
        assert applied["applied"]
        assert (
            field.review_measurement(
                org,
                users["OWNER"],
                visit["id"],
                {**request, "confirmed": True},
                _tenant(org, "OWNER"),
            )
            == applied
        )


def test_additive_customer_choice_is_warranty_authority(documentary_tenant):
    from backend.tests.integration.test_proposal_v2 import issue, response
    from portal.service import decide_quote

    org, _, users, _ = documentary_tenant
    _, _, version, token = issue(org, users["OWNER"])
    with as_user(users["WORKSHOP_MANAGER"]):
        assert field.approval_date(org, version) is None
    decide_quote(**response(token))
    with as_user(users["WORKSHOP_MANAGER"]):
        approved = field.approval_date(org, version)
        assert approved is not None
        result = field.warranty(
            org,
            {
                "warranty_terms": {"warranty_days": 365, "warranty_start": "APPROVAL"},
                "approved_at": approved,
            },
            None,
        )
        assert result["expires_on"] is not None
        assert (
            field.warranty(
                org,
                {
                    "warranty_terms": {"warranty": "Dos años en texto sin autoridad"},
                    "approved_at": approved,
                },
                None,
            )["expires_on"]
            is None
        )


def test_fabricated_measurement_opens_one_corrective_draft_and_preserves_source(documentary_tenant):
    from backend.tests.integration.test_opening_mounting import seed_rule
    from engine.tests.mounting_cases import mounting_cases

    org, _, users, _ = documentary_tenant
    case = mounting_cases()["IN_OPENING"]
    with as_user(users["OWNER"]):
        system = one("SELECT id FROM profile_systems WHERE code='DEMO_60' AND version=1")["id"]
        seed_rule(org, system, case["rule"])
    _, visit, order, frozen = dispatched(org, users)
    unit = visit["context"]["units"][0]
    original = one("SELECT status,payload_json FROM orders WHERE id=%s", [order["id"]])
    frozen_bytes = one(
        "SELECT snapshot_json,bom_hash,snapshot_sha256 FROM project_versions WHERE id=%s",
        [frozen["id"]],
    )
    with as_user(users["INSTALLER"]):
        event = field.command(
            org,
            users["INSTALLER"],
            visit["id"],
            {
                "operation_key": uuid4(),
                "kind": "MEASURE",
                "position_id": UUID(unit["position_id"]),
                "unit_index": 1,
                "photo_b64": PHOTO,
                "measurements": [case["survey"]],
            },
        )
    request = {
        "measurement_event_id": UUID(event["event_id"]),
        "reason": "Corregir una unidad fabricada",
        "confirmed": False,
    }
    with as_user(users["OWNER"]):
        proposed = field.review_measurement(
            org, users["OWNER"], visit["id"], request, _tenant(org, "OWNER")
        )
        assert proposed["price_change"]["delta_net"] is not None
        applied = field.review_measurement(
            org,
            users["OWNER"],
            visit["id"],
            {**request, "confirmed": True, "proposal_token": proposed["proposal_token"]},
            _tenant(org, "OWNER"),
        )
        assert applied["applied"] and applied["project_id"] != visit["project_id"]
        assert (
            one(
                "SELECT quantity FROM project_positions WHERE project_id=%s",
                [applied["project_id"]],
            )["quantity"]
            == 1
        )
        assert (
            field.review_measurement(
                org, users["OWNER"], visit["id"], request, _tenant(org, "OWNER")
            )
            == applied
        )
    assert original == one("SELECT status,payload_json FROM orders WHERE id=%s", [order["id"]])
    assert frozen_bytes == one(
        "SELECT snapshot_json,bom_hash,snapshot_sha256 FROM project_versions WHERE id=%s",
        [frozen["id"]],
    )


def test_missing_material_creates_additional_oc_without_releasing_original_claims(
    documentary_tenant,
):
    from backend.tests.integration.test_shot09_documentary import _eligibility_data
    from purchasing.service import (
        create_eligibility,
        allocate_requirement,
        confirm_order_type_batch,
    )

    org, _, users, _ = documentary_tenant
    _, visit, order, frozen = dispatched(org, users)
    unit = visit["context"]["units"][0]
    with as_user(users["INSTALLER"]):
        incident = field.command(
            org,
            users["INSTALLER"],
            visit["id"],
            {
                "operation_key": uuid4(),
                "kind": "INCIDENT",
                "position_id": UUID(unit["position_id"]),
                "unit_index": 1,
                "incident_kind": "MISSING",
                "scan": unit["label_code"],
                "photo_b64": PHOTO,
                "note": "Falta material sellado de esta unidad",
            },
        )
    with as_user(users["WORKSHOP_MANAGER"]), documentary_backend():
        requirements = rows(
            "SELECT id,requirement_key,order_type::text FROM purchase_requirement_lines WHERE org_id=%s AND project_version_id=%s AND quantity>=1 ORDER BY id",
            [org, frozen["id"]],
        )
        selected = requirements[0]
        lines = rows(
            "SELECT id,requirement_key FROM purchase_requirement_lines WHERE org_id=%s AND project_version_id=%s AND order_type=%s",
            [org, frozen["id"], selected["order_type"]],
        )
        eligibility = create_eligibility(
            org_id=org,
            actor_id=users["WORKSHOP_MANAGER"],
            version_id=UUID(frozen["id"]),
            data=_eligibility_data(
                selected["order_type"], [r["requirement_key"] for r in lines], "Reposiciones DEMO"
            ),
        )
        for line in lines:
            allocate_requirement(
                org_id=org,
                actor_id=users["WORKSHOP_MANAGER"],
                requirement_id=line["id"],
                eligibility_id=UUID(eligibility["id"]),
            )
        originals, _ = confirm_order_type_batch(
            org_id=org,
            actor_id=users["WORKSHOP_MANAGER"],
            version_id=UUID(frozen["id"]),
            order_type=selected["order_type"],
            confirmed=True,
        )
        original = one(
            "SELECT payload_json,order_snapshot_hash FROM orders WHERE id=%s", [originals[0]["id"]]
        )
        result = field.command(
            org,
            users["WORKSHOP_MANAGER"],
            visit["id"],
            {
                "operation_key": uuid4(),
                "kind": "RESOLVE",
                "incident_id": UUID(incident["result"]["incident"]["id"]),
                "resolution_kind": "PURCHASE",
                "confirmed": True,
                "note": "Reponer el faltante físico",
                "requirement_id": selected["id"],
                "quantity": 1,
            },
        )
        replacement = result["result"]["resolution"]["purchase_order_id"]
        assert replacement != originals[0]["id"]
        assert original == one(
            "SELECT payload_json,order_snapshot_hash FROM orders WHERE id=%s", [originals[0]["id"]]
        )
        payload = decoded(
            one("SELECT payload_json FROM orders WHERE id=%s", [replacement])["payload_json"]
        )
        assert payload["field_incident"]["id"] == incident["result"]["incident"]["id"]
        assert len(payload["lines"]) == 1 and str(payload["lines"][0]["quantity"]) in (
            "1",
            "1.0000",
        )
        with pytest.raises(DatabaseError, match="purchase_requirement_capacity_exceeded"), transaction.atomic():
            rows("INSERT INTO order_requirement_lines(org_id,order_id,requirement_line_id,quantity,field_authorization_id) SELECT org_id,order_id,requirement_line_id,quantity,field_authorization_id FROM order_requirement_lines WHERE order_id=%s RETURNING id", [replacement])
        from purchasing.service import send_order
        from inventory.service import order_receiving, receive_order
        close = {"operation_key":uuid4(),"kind":"CLOSE","incident_id":incident["result"]["incident"]["id"],"note":"Reposición recibida"}
        with pytest.raises(ContractAPIException, match="Recibe la compra"):
            field.command(org,users["WORKSHOP_MANAGER"],visit["id"],close)
        send_order(org_id=org,actor_id=users["WORKSHOP_MANAGER"],order_id=UUID(replacement),confirmed=True)
        receiving = order_receiving(org_id=org,order_id=UUID(replacement))
        receive_order(org_id=org,actor_id=users["WORKSHOP_MANAGER"],order_id=UUID(replacement),receipt_key="P23-replacement",note="Faltante recibido",lines=[{"order_line_id":UUID(line["id"]),"received_qty":Decimal(line["ordered_qty"]),"damaged_qty":Decimal(0)} for line in receiving["lines"]])
        assert one("SELECT status FROM orders WHERE id=%s",[replacement])["status"]=="FULFILLED"
        field.command(org,users["WORKSHOP_MANAGER"],visit["id"],close)
        assert one("SELECT status FROM field_incidents WHERE id=%s",[close["incident_id"]])["status"]=="CLOSED"
    assert one("SELECT status FROM orders WHERE id=%s", [order["id"]])["status"] == "DISPATCHED"


def test_service_diagnosis_signed_visit_and_close_do_not_install_another_unit(documentary_tenant):
    org, _, users, _ = documentary_tenant
    _, visit, order, _ = dispatched(org, users)
    unit = visit["context"]["units"][0]
    with as_user(users["INSTALLER"]):
        incident = field.command(org,users["INSTALLER"],visit["id"],{"operation_key":uuid4(),"kind":"INCIDENT","position_id":UUID(unit["position_id"]),"unit_index":1,"incident_kind":"ADJUSTMENT","note":"Regular cierre de la hoja","photo_b64":PHOTO})["result"]["incident"]
    with as_user(users["WORKSHOP_MANAGER"]):
        field.command(org,users["WORKSHOP_MANAGER"],visit["id"],{"operation_key":uuid4(),"kind":"DIAGNOSE","incident_id":incident["id"],"note":"Ajustar el herraje sellado"})
        resolved = field.command(org,users["WORKSHOP_MANAGER"],visit["id"],{"operation_key":uuid4(),"kind":"RESOLVE","incident_id":incident["id"],"resolution_kind":"SERVICE","note":"Visita de regulación","planned_on":date(2026,10,12),"assigned_to":users["INSTALLER"],"confirmed":True})
        service_id = resolved["result"]["resolution"]["service_visit_id"]
        with pytest.raises(ContractAPIException, match="Cierra la visita"):
            field.command(org,users["WORKSHOP_MANAGER"],visit["id"],{"operation_key":uuid4(),"kind":"CLOSE","incident_id":incident["id"],"note":"Regulación completada"})
    with as_user(users["INSTALLER"]):
        receipt = {"operation_key":uuid4(),"kind":"RECEIVE","receiver_name":"Cliente DEMO","receiver_rut":"12.345.678-5","signature_b64":PHOTO,"photo_b64":PHOTO,"note":"Herraje regulado y verificado","confirmed":True}
        first = field.command(org,users["INSTALLER"],service_id,receipt)
        assert first == field.command(org,users["INSTALLER"],service_id,receipt)
    with as_user(users["WORKSHOP_MANAGER"]):
        field.command(org,users["WORKSHOP_MANAGER"],visit["id"],{"operation_key":uuid4(),"kind":"CLOSE","incident_id":incident["id"],"note":"Servicio recibido por el cliente"})
        assert one("SELECT status FROM field_incidents WHERE id=%s",[incident["id"]])["status"]=="CLOSED"
    assert one("SELECT status FROM orders WHERE id=%s",[order["id"]])["status"]=="DISPATCHED"


def test_cancelled_predeparture_trip_releases_units_and_qr_identity_is_exact(documentary_tenant):
    org, _, users, _ = documentary_tenant
    body, visit, _, _ = dispatched(org,users,send=False)
    unit=visit["context"]["units"][0]
    with as_user(users["INSTALLER"]):
        assert field.scan_unit(unit,unit["qr_value"],org)["unit_index"]==1
        with pytest.raises(Exception):
            field.scan_unit(unit,unit["qr_value"]+"-forged",org)
        with pytest.raises(ContractAPIException):
            field.scan_unit(unit,f"/production?order={uuid4()}&piece=P01-U01-M01",org)
    with as_user(users["WORKSHOP_MANAGER"]):
        cancel={"operation_key":uuid4(),"kind":"CANCEL","note":"Reagendar sin salida"}
        field.command(org,users["WORKSHOP_MANAGER"],visit["id"],cancel)
        assert field.command(org,users["WORKSHOP_MANAGER"],visit["id"],cancel)["visit"]["status"]=="CANCELLED"
        replacement=field.schedule(org,users["WORKSHOP_MANAGER"],{**body,"operation_key":uuid4()})
        assert replacement["visit"]["id"]!=visit["id"]
        assert one("SELECT count(*) AS n FROM deliveries WHERE order_id=%s AND status='SCHEDULED'",[unit["order_id"]])["n"]==1
