from __future__ import annotations

import time
from types import SimpleNamespace
from uuid import UUID

from cryptography.hazmat.primitives.asymmetric import rsa
import httpx
import jwt
import pytest
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from authentication.backends import SupabaseJWTAuthentication
from authentication.errors import ContractAPIException
from authentication.jwt_verifier import (
    AuthServerTokenVerifier,
    JWKSTokenVerifier,
    _validated_token,
)

ISSUER = "https://project.supabase.co/auth/v1"
USER_ID = "10000000-0000-0000-0000-000000000001"


def claims(**changes: object) -> dict[str, object]:
    result: dict[str, object] = {
        "sub": USER_ID,
        "exp": int(time.time()) + 600,
        "iss": ISSUER,
        "aud": "authenticated",
        "role": "authenticated",
        "email": "user@example.com",
    }
    result.update(changes)
    return result


def test_missing_bearer_is_left_for_drf_permission() -> None:
    request = Request(APIRequestFactory().get("/api/v1/auth/me/"))
    assert SupabaseJWTAuthentication().authenticate(request) is None


def test_malformed_bearer_is_invalid_token() -> None:
    request = Request(
        APIRequestFactory().get(
            "/api/v1/auth/me/", HTTP_AUTHORIZATION="Bearer one two"
        )
    )
    with pytest.raises(ContractAPIException, match="Invalid token"):
        SupabaseJWTAuthentication().authenticate(request)


@pytest.mark.parametrize("role", ("anon", "service_role"))
def test_non_application_roles_are_rejected(role: str) -> None:
    with pytest.raises(ContractAPIException):
        _validated_token("token", claims(role=role), issuer=ISSUER)


@pytest.mark.parametrize(
    "changes",
    (
        {"exp": int(time.time()) - 1},
        {"iss": "https://attacker.invalid/auth/v1"},
        {"aud": "anon"},
        {"sub": "not-a-uuid"},
        {"sub": None},
        {"aal": []},
        {"aal": {}},
        {"aal": None},
        {"aal": "aal3"},
    ),
)
def test_invalid_required_claims_are_rejected(changes: dict[str, object]) -> None:
    with pytest.raises(ContractAPIException):
        _validated_token("token", claims(**changes), issuer=ISSUER)


def test_missing_aal_defaults_to_aal1() -> None:
    verified = _validated_token("token", claims(), issuer=ISSUER)
    assert verified.aal == "aal1"
    assert verified.user_id == UUID(USER_ID)


def test_valid_asymmetric_jwt_is_accepted() -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = jwt.encode(claims(aal="aal2"), private_key, algorithm="RS256", headers={"kid": "k1"})
    verifier = JWKSTokenVerifier("https://project.supabase.co")
    verifier.key_client = SimpleNamespace(
        get_signing_key_from_jwt=lambda unused: SimpleNamespace(key=private_key.public_key())
    )

    verified = verifier.verify(token)

    assert verified.user_id == UUID(USER_ID)
    assert verified.aal == "aal2"


def test_invalid_signature_is_rejected() -> None:
    signer = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = jwt.encode(claims(), signer, algorithm="RS256", headers={"kid": "k1"})
    verifier = JWKSTokenVerifier("https://project.supabase.co")
    verifier.key_client = SimpleNamespace(
        get_signing_key_from_jwt=lambda unused: SimpleNamespace(key=other.public_key())
    )

    with pytest.raises(ContractAPIException):
        verifier.verify(token)


def test_jwks_rejects_algorithm_outside_allowlist() -> None:
    token = jwt.encode(claims(), "s" * 32, algorithm="HS256")
    with pytest.raises(ContractAPIException):
        JWKSTokenVerifier("https://project.supabase.co").verify(token)


def test_auth_server_requires_matching_returned_user(monkeypatch: pytest.MonkeyPatch) -> None:
    token = jwt.encode(claims(), "local-secret-that-is-at-least-32-bytes", algorithm="HS256")
    response = httpx.Response(
        200,
        json={"id": USER_ID, "email": "user@example.com"},
        request=httpx.Request("GET", f"{ISSUER}/user"),
    )
    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: response)
    verifier = AuthServerTokenVerifier("https://project.supabase.co", "anon-key", 5)

    assert verifier.verify(token).user_id == UUID(USER_ID)

    mismatch = httpx.Response(
        200,
        json={"id": "10000000-0000-0000-0000-000000000002"},
        request=httpx.Request("GET", f"{ISSUER}/user"),
    )
    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: mismatch)
    with pytest.raises(ContractAPIException):
        verifier.verify(token)
