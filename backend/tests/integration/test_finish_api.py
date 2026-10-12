"""Finish preview HTTP permission, tenant scope and missing-authority contracts."""
from uuid import uuid4

import pytest
from django.db import connection, transaction

from backend.tests.integration.test_rls_context_integration import real_rows as real_rows
from backend.tests.integration.test_shot10_catalog_api import client_for, set_role
from authentication.rls import authenticated_rls_context
from catalogs import service

pytestmark = pytest.mark.rls_integration


@pytest.fixture(autouse=True)
def database_access(django_db_blocker):
    with django_db_blocker.unblock(), transaction.atomic():
        yield
        transaction.set_rollback(True)


def design():
    with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM profile_systems WHERE code='DEMO_60' AND version=5")
        system=str(cursor.fetchone()[0])
    return {"system_id":system,"nominal_width_mm":"900.00","nominal_height_mm":"850.00",
        "color":"WHITE_WALNUT","baseline_color":"WHITE","parametric_tree":{"id":"vano","type":"BAY",
            "opening_type":"FIXED","glass_thickness_mm":"24.00","glass_spec":"4-16-4"}}


def test_estimator_gets_honest_unknown_price_without_cost_rules(real_rows):
    set_role(real_rows,"ESTIMATOR")
    response=client_for(real_rows).post("/api/v1/projects/finish-preview/",design(),format="json")
    assert response.status_code==200,response.data
    assert response.data["delta_price_net"] is None and "completa las reglas" in response.data["reason"]
    assert response.data["description"]=="Nogal exterior / Blanco interior"


@pytest.mark.parametrize("role",["OPERATOR","INSTALLER","WORKSHOP_MANAGER"])
def test_finish_price_requires_commercial_role(real_rows,role):
    set_role(real_rows,role)
    response=client_for(real_rows).post("/api/v1/projects/finish-preview/",design(),format="json")
    assert response.status_code==403


def test_invalid_combination_returns_action_and_source_contract(real_rows):
    set_role(real_rows,"ESTIMATOR")
    response=client_for(real_rows).post("/api/v1/projects/finish-preview/",{**design(),"color":"CREAM_WALNUT"},format="json")
    assert response.status_code==422
    assert response.data["error"]["code"]=="finish_combination_invalid"


def test_private_finish_chart_is_invisible_to_another_tenant(real_rows):
    org=real_rows.organizations["A"]
    set_role(real_rows,"WORKSHOP_MANAGER")
    with authenticated_rls_context(real_rows.tokens["A"].claims):
        source=service.retrieve(service.SYSTEMS,org,design()["system_id"])
        draft={key:source[key] for key in service.SYSTEMS.fields}
        draft.update(code="D05-PRIVATE-"+str(uuid4())[:8],name="Carta privada de ensayo",version=1)
        private=service.create(service.SYSTEMS,org,draft)
        assert private["finish_authority"]==source["finish_authority"]
    with authenticated_rls_context(real_rows.tokens["B"].claims),connection.cursor() as cursor:
        cursor.execute("SELECT finish_authority FROM profile_systems WHERE id=%s",[private["id"]])
        assert cursor.fetchone() is None


def test_human_catalog_write_keeps_exact_decimal_strings(real_rows):
    """The HTTP serializer must preserve D05's string-valued SQL authority."""
    set_role(real_rows, "WORKSHOP_MANAGER")
    with authenticated_rls_context(real_rows.tokens["A"].claims):
        source = service.retrieve(service.SYSTEMS, real_rows.organizations["A"], design()["system_id"])
    draft = {key: source[key] for key in service.SYSTEMS.fields}
    draft.update(code="D05-HTTP-" + str(uuid4())[:8], name="Carta HTTP de ensayo · DEMO", version=1)
    exact = "0.123456789123456789"
    draft["finish_authority"]["colors"][0]["linear_rgb"][0] = exact
    client = client_for(real_rows)
    created = client.post("/api/v1/catalogs/systems/", draft, format="json")
    assert created.status_code == 201, created.data
    chart = created.data["finish_authority"]
    assert chart["colors"][0]["linear_rgb"][0] == exact
    path = f"/api/v1/catalogs/systems/{created.data['id']}/"
    chart["colors"][0]["name"] = "Blanco revisado · DEMO"
    updated = client.patch(path, {"finish_authority": chart}, format="json",
        HTTP_IF_MATCH='"' + created.data["revision"] + '"')
    assert updated.status_code == 200, updated.data
    assert client.get(path).data["finish_authority"]["colors"][0]["linear_rgb"][0] == exact


@pytest.mark.parametrize("color", ["WHITE", "WHITE_WALNUT"])
def test_finish_calculation_inspection_layout_and_cut_share_one_exact_authority(real_rows, color):
    set_role(real_rows, "ESTIMATOR")
    request = {key: value for key, value in design().items() if key != "baseline_color"}
    request["color"] = color
    client = client_for(real_rows)
    calculated = client.post("/api/v1/engine/calculate/", request, format="json")
    assert calculated.status_code == 200, calculated.data
    assert calculated.data["finish"]["combination"]["code"] == color
    assert all(cut["stock_color"] == color for cut in calculated.data["profile_cuts"])
    inspected = client.post("/api/v1/engine/inspect/", request, format="json")
    assert inspected.status_code == 200, inspected.data
    layout = client.post("/api/v1/engine/layout/", request, format="json")
    assert layout.status_code == 200, layout.data
    optimized = client.post("/api/v1/engine/optimize-cut/", request, format="json")
    assert optimized.status_code == 200, optimized.data
    assert inspected.data["source_calculation_hash"] == calculated.data["calculation_hash"]
    assert layout.data["calculation_hash"] == calculated.data["calculation_hash"]
    assert optimized.data["source_calculation_hash"] == calculated.data["calculation_hash"]
