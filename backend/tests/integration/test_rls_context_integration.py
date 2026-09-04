"""Real Auth, Django and PostgreSQL RLS: no mocked identity, cursor or policy."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from decimal import Decimal
import json
import os
import secrets
import base64
from uuid import UUID, uuid4

from django.conf import settings
from django.db import connection
import httpx
import pytest
from pytest_django.plugin import DjangoDbBlocker
from rest_framework.test import APIClient

from authentication.jwt_verifier import AuthServerTokenVerifier
from authentication.rls import authenticated_rls_context
from authentication.tenancy import MembershipRepository, resolve_tenant_context
from authentication.types import VerifiedSupabaseToken
from backend.tests.test_engine_api import g1_request, g4_request
from dekopen_engine import ProfileRole
from engine_api.repository import SystemNotFound, SystemParamsRepository

pytestmark = pytest.mark.rls_integration


@dataclass(frozen=True)
class RLSFixtures:
    tokens: dict[str, VerifiedSupabaseToken]
    organizations: dict[str, UUID]
    systems: dict[str, UUID]
    demo_system: UUID


@pytest.fixture(scope="module")
def real_rows(django_db_blocker: DjangoDbBlocker) -> Iterator[RLSFixtures]:
    if connection.vendor != "postgresql":
        pytest.fail("Real RLS gate requires the local Supabase DATABASE_URL; never skipped")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not service_key or not settings.SUPABASE_ANON_KEY:
        pytest.fail("Real RLS gate requires local Auth fixture credentials; never skipped")

    organizations = {name: uuid4() for name in ("A", "B", "inactive")}
    systems = {name: uuid4() for name in organizations}
    tokens: dict[str, VerifiedSupabaseToken] = {}
    created_users: list[UUID] = []
    verifier = AuthServerTokenVerifier(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY, 5)
    with django_db_blocker.unblock(), httpx.Client(timeout=10) as auth:
        try:
            for name in ("A", "B", "both", "none"):
                email = f"shot04-rls-{uuid4()}@example.com"
                password = secrets.token_urlsafe(32)
                created = auth.post(
                    f"{settings.SUPABASE_URL}/auth/v1/admin/users",
                    headers={"apikey": service_key, "Authorization": f"Bearer {service_key}"},
                    json={"email": email, "password": password, "email_confirm": True},
                )
                assert created.status_code in (200, 201), "Local Auth Admin fixture creation failed"
                user_id = UUID(created.json()["id"])
                created_users.append(user_id)
                signed_in = auth.post(
                    f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password",
                    headers={"apikey": settings.SUPABASE_ANON_KEY},
                    json={"email": email, "password": password},
                )
                assert signed_in.status_code == 200, "Local Auth fixture sign-in failed"
                tokens[name] = verifier.verify(signed_in.json()["access_token"])
                assert tokens[name].user_id == user_id

            with connection.cursor() as cursor:
                for name, org_id in organizations.items():
                    cursor.execute(
                        "INSERT INTO public.tenancy_organizations (id, name, tax_id) "
                        "VALUES (%s, %s, %s)",
                        [org_id, f"RLS {name}", f"RLS-{org_id}"],
                    )
                    cursor.execute(
                        "INSERT INTO public.profile_systems "
                        "(id, org_id, name, code, depth_mm, is_global, is_active) "
                        "VALUES (%s, %s, %s, %s, 60.00, FALSE, TRUE)",
                        [systems[name], org_id, f"System {name}", f"RLS_{name}"],
                    )
                    cursor.execute(
                        "INSERT INTO public.profile_articles "
                        "(system_id, org_id, sku, name, role, face_width_mm) "
                        "VALUES (%s, %s, %s, %s, 'FRAME', 60.00)",
                        [systems[name], org_id, f"FRAME-{name}", f"Frame {name}"],
                    )
                    cursor.execute(
                        "INSERT INTO public.projects "
                        "(org_id, code, name, client_name, created_by) "
                        "VALUES (%s, 'RLS-FIXTURE', 'RLS fixture', 'Fixture only', %s)",
                        [org_id, tokens["both"].user_id],
                    )
                    cursor.execute(
                        "INSERT INTO public.cost_lists (org_id, supplier_name, valid_from) "
                        "VALUES (%s, 'RLS fixture', DATE '2026-09-02')",
                        [org_id],
                    )
                for user, org, active in (
                    ("A", "A", True), ("B", "B", True),
                    ("both", "A", True), ("both", "B", True),
                    ("both", "inactive", False),
                ):
                    cursor.execute(
                        "INSERT INTO public.tenancy_memberships "
                        "(org_id, user_id, role, is_active) VALUES (%s, %s, 'ESTIMATOR', %s)",
                        [organizations[org], tokens[user].user_id, active],
                    )
                cursor.execute("SELECT id FROM public.profile_systems WHERE code = 'DEMO_60'")
                demo_system = cursor.fetchone()[0]
            yield RLSFixtures(tokens, organizations, systems, demo_system)
        finally:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM public.tenancy_organizations WHERE id = ANY(%s)",
                    [list(organizations.values())],
                )
            for user_id in created_users:
                deleted = auth.delete(
                    f"{settings.SUPABASE_URL}/auth/v1/admin/users/{user_id}",
                    headers={"apikey": service_key, "Authorization": f"Bearer {service_key}"},
                )
                assert deleted.status_code == 200, "Local Auth fixture cleanup failed"
            connection.close()


@pytest.fixture(autouse=True)
def real_database_access(
    real_rows: RLSFixtures, django_db_blocker: DjangoDbBlocker
) -> Iterator[None]:
    with django_db_blocker.unblock():
        yield


def assert_no_context() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT current_user, current_setting('request.jwt.claims', true), auth.uid()"
        )
        role, claims, user_id = cursor.fetchone()
    assert role not in ("authenticated", "service_role")
    assert claims in (None, "")
    assert user_id is None


def test_verified_claims_auth_uid_and_role_then_commit_cleanup(real_rows: RLSFixtures) -> None:
    token = real_rows.tokens["A"]
    with authenticated_rls_context(token.claims):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT auth.uid(), current_user, current_setting('request.jwt.claims', true)"
            )
            user_id, role, claims = cursor.fetchone()
        assert user_id == token.user_id
        assert role == "authenticated"
        assert json.loads(claims) == token.claims
    assert_no_context()


@pytest.mark.parametrize("tenant", ["A", "B"])
def test_tenants_cannot_read_each_others_projects_or_costs(
    real_rows: RLSFixtures, tenant: str
) -> None:
    with authenticated_rls_context(real_rows.tokens[tenant].claims):
        with connection.cursor() as cursor:
            cursor.execute("SELECT org_id FROM public.projects")
            assert {row[0] for row in cursor.fetchall()} == {real_rows.organizations[tenant]}
            cursor.execute("SELECT org_id FROM public.cost_lists")
            assert {row[0] for row in cursor.fetchall()} == {real_rows.organizations[tenant]}
        params = SystemParamsRepository().load_visible(
            real_rows.demo_system, real_rows.organizations[tenant]
        )
        assert params.system_code == "DEMO_60"
        assert params.central_overlap_mm == Decimal("40.00")
    assert_no_context()


def test_multi_membership_active_org_does_not_mix_catalog_rows(real_rows: RLSFixtures) -> None:
    token = real_rows.tokens["both"]
    with authenticated_rls_context(token.claims):
        memberships = MembershipRepository().list_active_for_user(token.user_id)
        assert {item.organization_id for item in memberships} == {
            real_rows.organizations["A"], real_rows.organizations["B"]
        }
        context = resolve_tenant_context(memberships, str(real_rows.organizations["A"]))
        active_org = context.active_organization.organization_id
        repository = SystemParamsRepository()
        params = repository.load_visible(real_rows.systems["A"], active_org)
        assert params.effective_profile_articles[ProfileRole.FRAME].sku == "FRAME-A"
        with pytest.raises(SystemNotFound):
            repository.load_visible(real_rows.systems["B"], active_org)
    assert_no_context()


def test_rollback_clears_claims_and_role(real_rows: RLSFixtures) -> None:
    with pytest.raises(RuntimeError, match="force rollback"):
        with authenticated_rls_context(real_rows.tokens["both"].claims):
            raise RuntimeError("force rollback")
    assert_no_context()


def test_no_leak_between_open_connections_or_successive_requests(real_rows: RLSFixtures) -> None:
    probe = connection.copy(alias="rls_probe")
    try:
        with authenticated_rls_context(real_rows.tokens["A"].claims):
            with probe.cursor() as cursor:
                cursor.execute("SELECT auth.uid(), current_user")
                user_id, role = cursor.fetchone()
            assert user_id is None
            assert role not in ("authenticated", "service_role")
        assert_no_context()
        with authenticated_rls_context(real_rows.tokens["B"].claims):
            with connection.cursor() as cursor:
                cursor.execute("SELECT auth.uid(), current_user")
                user_id, role = cursor.fetchone()
            assert user_id == real_rows.tokens["B"].user_id
            assert role == "authenticated"
        assert_no_context()
    finally:
        probe.close()


@pytest.mark.parametrize(
    ("user", "org", "expected_status", "code"),
    [
        ("A", None, 200, None),
        ("B", "B", 200, None),
        ("both", None, 409, "organization_selection_required"),
        ("both", "A", 200, None),
        ("both", "inactive", 403, "organization_access_denied"),
        ("A", "B", 403, "organization_access_denied"),
        ("none", None, 403, "no_active_membership"),
    ],
)
def test_real_bearer_auth_me_uses_rls_and_cleans_up_each_request(
    real_rows: RLSFixtures, user: str, org: str | None,
    expected_status: int, code: str | None,
) -> None:
    client = APIClient()
    headers = {"HTTP_AUTHORIZATION": f"Bearer {real_rows.tokens[user].access_token}"}
    if org is not None:
        headers["HTTP_X_ORGANIZATION_ID"] = str(real_rows.organizations[org])
    response = client.get("/api/v1/auth/me/", **headers)
    assert response.status_code == expected_status
    if code is not None:
        assert response.json()["error"]["code"] == code
    else:
        assert response.json()["user"]["id"] == str(real_rows.tokens[user].user_id)
        assert response.json()["active_organization"]["id"] == str(
            real_rows.organizations[org or user]
        )
    assert_no_context()


@pytest.mark.parametrize("case", ["G1", "G4"])
def test_real_bearer_and_db_adapter_preserve_engine_geometry(
    real_rows: RLSFixtures, case: str
) -> None:
    payload = g1_request() if case == "G1" else g4_request()
    payload["system_id"] = str(real_rows.demo_system)
    response = APIClient().post(
        "/api/v1/engine/calculate/", payload, format="json",
        HTTP_AUTHORIZATION=f"Bearer {real_rows.tokens['A'].access_token}",
    )
    assert response.status_code == 200
    result = response.json()
    if case == "G1":
        assert {cut["length_mm"] for cut in result["profile_cuts"] if cut["role"] == "FRAME"} == {
            "1006.00"
        }
        assert result["glasses"][0]["width_mm"] == "910.00"
        assert result["glasses"][0]["height_mm"] == "910.00"
    else:
        mullion = next(cut for cut in result["profile_cuts"] if cut["role"] == "MULLION_V")
        assert mullion["length_mm"] == "1380.00"
        widths = {piece["bay_id"]: piece["width_mm"] for piece in result["glasses"]}
        assert widths == {"bay_fixed": "830.00", "bay_ob": "696.00"}
    assert result["hardware_items"] == []
    assert set(result) == {"profile_cuts", "reinforcements", "glasses", "hardware_items"}
    assert_no_context()


def test_multi_org_api_rejects_system_b_when_a_is_selected(real_rows: RLSFixtures) -> None:
    client = APIClient()
    headers = {
        "HTTP_AUTHORIZATION": f"Bearer {real_rows.tokens['both'].access_token}",
        "HTTP_X_ORGANIZATION_ID": str(real_rows.organizations["A"]),
    }
    payload = g1_request()
    payload["system_id"] = str(real_rows.demo_system)
    allowed = client.post("/api/v1/engine/calculate/", payload, format="json", **headers)
    assert allowed.status_code == 200
    assert allowed.json()["glasses"][0]["width_mm"] == "910.00"
    payload["system_id"] = str(real_rows.systems["B"])
    denied = client.post("/api/v1/engine/calculate/", payload, format="json", **headers)
    assert denied.status_code == 404
    assert denied.json()["error"]["code"] == "system_not_found"
    assert_no_context()


def test_modified_sub_or_aal_cannot_enter_rls(real_rows: RLSFixtures) -> None:
    original = real_rows.tokens["A"]
    header, _, signature = original.access_token.split(".")
    forged = dict(original.claims, sub=str(real_rows.tokens["B"].user_id), aal="aal2")
    payload = base64.urlsafe_b64encode(json.dumps(forged).encode()).decode().rstrip("=")
    response = APIClient().get(
        "/api/v1/auth/me/", HTTP_AUTHORIZATION=f"Bearer {header}.{payload}.{signature}"
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_token"
    assert_no_context()
