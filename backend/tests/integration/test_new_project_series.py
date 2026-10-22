"""The first work retains its chosen series within the tenant boundary."""

import pytest

from pricing.repository import one

from .test_catalog_series_sheet import create
from .test_shot08_pricing import owner_client
from .test_shot09_documentary import as_user, documentary_tenant as documentary_tenant

pytestmark = pytest.mark.rls_integration


def test_create_project_persists_series_and_seeds_future_windows(documentary_tenant):
    org, _, users, _ = documentary_tenant
    actor = users["OWNER"]
    with as_user(actor):
        sheet = create(org, actor)
    client = owner_client(actor)
    headers = {"HTTP_X_ORGANIZATION_ID": str(org)}
    response = client.post("/api/v1/projects/", {
        "name": "Primera obra", "design_defaults": {"system_id": str(sheet["id"])},
    }, format="json", **headers)
    assert response.status_code == 201, response.data
    assert response.data["design_defaults"] == {"system_id": str(sheet["id"])}
    assert response.data["effective_design_defaults"]["system_id"] == {
        "value": str(sheet["id"]), "source": "project",
    }
    reopened = client.get(f"/api/v1/projects/{response.data['id']}/", **headers)
    assert reopened.data["design_defaults"] == response.data["design_defaults"]


def test_unavailable_series_prevents_creating_a_partial_project(documentary_tenant):
    org, other, users, other_actor = documentary_tenant
    actor = users["OWNER"]
    with as_user(other_actor):
        private_id = create(other, other_actor)["id"]
    response = owner_client(actor).post("/api/v1/projects/", {
        "name": "Must not be created", "design_defaults": {"system_id": str(private_id)},
    }, format="json", HTTP_X_ORGANIZATION_ID=str(org))
    assert response.status_code == 400
    with as_user(actor):
        assert not one("SELECT count(*) AS n FROM public.projects WHERE org_id=%s", [org])["n"]
