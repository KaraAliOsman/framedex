from __future__ import annotations

from contextlib import nullcontext

import pytest
from rest_framework.test import APIClient

import authentication.views
from authentication.tenancy import MembershipRepository
from backend.tests.factories import ORG_A_ID, ORG_B_ID, authenticated_identity, membership


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def configure_memberships(
    monkeypatch: pytest.MonkeyPatch,
    memberships: tuple[object, ...],
) -> None:
    monkeypatch.setattr(
        authentication.views,
        "authenticated_rls_context",
        lambda claims: nullcontext(),
    )
    monkeypatch.setattr(
        MembershipRepository,
        "list_active_for_user",
        lambda self, user_id: memberships,
    )


def test_auth_me_requires_bearer(client: APIClient) -> None:
    response = client.get("/api/v1/auth/me/")
    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "authentication_required",
            "detail": "Authentication is required",
        }
    }


def test_auth_me_returns_single_active_membership(
    client: APIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    user, token = authenticated_identity()
    client.force_authenticate(user=user, token=token)
    configure_memberships(monkeypatch, (membership(),))

    response = client.get("/api/v1/auth/me/")

    assert response.status_code == 200
    assert response.json() == {
        "user": {"id": str(user.id), "email": "user@example.com"},
        "aal": "aal1",
        "active_organization": {
            "id": str(ORG_A_ID),
            "name": "Taller A",
            "role": "ESTIMATOR",
        },
        "memberships": [
            {
                "organization_id": str(ORG_A_ID),
                "organization_name": "Taller A",
                "role": "ESTIMATOR",
            }
        ],
    }


def test_auth_me_multiple_memberships_returns_selection_contract(
    client: APIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    user, token = authenticated_identity()
    client.force_authenticate(user=user, token=token)
    configure_memberships(
        monkeypatch,
        (membership(), membership(ORG_B_ID, name="Taller B")),
    )

    response = client.get("/api/v1/auth/me/")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "organization_selection_required"
    assert len(response.json()["memberships"]) == 2


def test_owner_aal1_is_rejected_and_aal2_passes(
    client: APIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    configure_memberships(monkeypatch, (membership(role="OWNER"),))
    user, aal1 = authenticated_identity(aal="aal1")
    client.force_authenticate(user=user, token=aal1)
    rejected = client.get("/api/v1/auth/me/")
    assert rejected.status_code == 403
    assert rejected.json() == {
        "error": {
            "code": "mfa_required",
            "detail": "OWNER requires aal2",
            "required_aal": "aal2",
        }
    }

    _, aal2 = authenticated_identity(aal="aal2")
    client.force_authenticate(user=user, token=aal2)
    assert client.get("/api/v1/auth/me/").status_code == 200
