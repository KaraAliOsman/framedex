"""D04 real DB: sourced class import, RLS and exact preview contracts."""

import json
from uuid import uuid4

import pytest
from django.db import connection, transaction

from authentication.rls import authenticated_rls_context
from backend.tests.integration.test_rls_context_integration import real_rows as real_rows
from backend.tests.integration.test_shot10_catalog_api import client_for, set_role
from catalogs.demo_hardware import hardware_manifest
from catalogs import service

pytestmark = pytest.mark.rls_integration


@pytest.fixture(autouse=True)
def database_access(django_db_blocker):
    with django_db_blocker.unblock(),transaction.atomic():
        yield
        transaction.set_rollback(True)


def system_id():
    with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM public.profile_systems WHERE code='DEMO_60' AND version=4 AND is_global")
        return str(cursor.fetchone()[0])


@pytest.mark.parametrize("role",["ESTIMATOR","WORKSHOP_MANAGER"])
def test_preview_reads_v4_exact_components_and_nullable_price(real_rows,role):
    set_role(real_rows,role)
    response=client_for(real_rows).post("/api/v1/projects/hardware-preview/",{
        "system_id":system_id(),"bay_id":"vano","width_mm":"1000.00","height_mm":"1400.00","color":"WHITE",
        "parametric_tree":{"id":"vano","type":"BAY","opening_use":"WINDOW","opening":{"movement":"TILT_TURN","hinge_side":"LEFT","direction":"INWARD","leaf_role":"SINGLE","fixed_in_sash":False},"glass_spec":"4-16-4","glass_thickness_mm":"24.00"}},format="json")
    assert response.status_code==200,response.data
    assert response.data["is_demo"]
    selected=next(row for row in response.data["leaves"][0]["candidates"] if row["selected"])
    assert selected["compatible"] and selected["resolution"]["source"]
    assert isinstance(selected["resolution"]["exact_leaf_weight_kg"],str)
    assert all(isinstance(component["qty"],str) for component in selected["contents"])


@pytest.mark.parametrize("role",["OPERATOR","INSTALLER"])
def test_floor_role_cannot_ask_for_commercial_price(real_rows,role):
    set_role(real_rows,role)
    response=client_for(real_rows).post("/api/v1/projects/hardware-preview/",{
        "system_id":system_id(),"bay_id":"vano","width_mm":"1000.00","height_mm":"1400.00","color":"WHITE","parametric_tree":{"id":"vano","type":"BAY"}},format="json")
    assert response.status_code==403


def test_owned_class_import_and_other_tenant_isolation(real_rows):
    set_role(real_rows,"WORKSHOP_MANAGER")
    org=real_rows.organizations["A"]
    body=hardware_manifest()[0]["params"]["available_hardware_kits"][0]
    body.update(system_id=system_id(),sku="D04-OWNED-"+str(uuid4())[:8],is_active=True)
    body["class_authority"]["family_code"]="D04-OWNED"
    with authenticated_rls_context(real_rows.tokens["A"].claims):
        source = service.retrieve(service.SYSTEMS,org,body["system_id"])
        draft = {key:source[key] for key in service.SYSTEMS.fields}
        draft.update(code="D04-PRIVATE-"+str(uuid4())[:8],name="Autoridad privada de ensayo",version=1)
        private = service.create(service.SYSTEMS,org,draft)
        body["system_id"] = private["id"]
        saved=service.create(service.KITS,org,body)
        assert service.retrieve(service.KITS,org,saved["id"])["class_authority"]==body["class_authority"]
        assert any(kit["sku"]==body["sku"] for kit in service.list_rows(service.KITS,org))
    with authenticated_rls_context(real_rows.tokens["B"].claims),connection.cursor() as cursor:
        cursor.execute("SELECT class_authority FROM public.hardware_kits WHERE id=%s",[saved["id"]])
        assert cursor.fetchone() is None


def test_old_seed_kits_and_versions_are_preserved():
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM public.hardware_kits k JOIN public.profile_systems s ON s.id=k.system_id WHERE s.version=3 AND k.class_authority IS NULL")
        assert cursor.fetchone()[0]>0
        cursor.execute("SELECT public.hardware_class_authority_valid(%s::JSONB)",[json.dumps(hardware_manifest()[0]["params"]["available_hardware_kits"][0]["class_authority"])])
        assert cursor.fetchone()[0]
