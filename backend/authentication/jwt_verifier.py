"""Cryptographic Supabase access-token verification."""

from __future__ import annotations

from functools import lru_cache
import time
from typing import Protocol, cast
from uuid import UUID

from django.conf import settings
import httpx
import jwt

from authentication.errors import ContractAPIException, invalid_token
from authentication.types import AssuranceLevel, VerifiedSupabaseToken

ALLOWED_JWKS_ALGORITHMS = ("ES256", "RS256", "EdDSA")


class TokenVerifier(Protocol):
    def verify(self, token: str) -> VerifiedSupabaseToken: ...


def _validated_token(
    token: str,
    claims: dict[str, object],
    *,
    issuer: str,
    returned_user: dict[str, object] | None = None,
) -> VerifiedSupabaseToken:
    required = ("sub", "exp", "iss", "aud", "role")
    if any(name not in claims for name in required):
        raise invalid_token()
    if claims.get("iss") != issuer or claims.get("role") != "authenticated":
        raise invalid_token()

    audience = claims.get("aud")
    if audience != "authenticated" and not (
        isinstance(audience, list) and "authenticated" in audience
    ):
        raise invalid_token()

    expires_at = claims.get("exp")
    if isinstance(expires_at, bool) or not isinstance(expires_at, int):
        raise invalid_token()
    if expires_at <= int(time.time()):
        raise invalid_token()

    subject = claims.get("sub")
    if not isinstance(subject, str):
        raise invalid_token()
    try:
        user_id = UUID(subject)
    except ValueError as error:
        raise invalid_token() from error

    if returned_user is not None and returned_user.get("id") != subject:
        raise invalid_token()

    raw_aal = claims.get("aal", "aal1")
    if not isinstance(raw_aal, str) or raw_aal not in {"aal1", "aal2"}:
        raise invalid_token()
    aal = cast(AssuranceLevel, raw_aal)

    email_value = (
        returned_user.get("email") if returned_user is not None else claims.get("email")
    )
    email = email_value if isinstance(email_value, str) else ""
    return VerifiedSupabaseToken(
        access_token=token,
        claims=claims,
        user_id=user_id,
        email=email,
        aal=aal,
    )


class JWKSTokenVerifier:
    def __init__(self, supabase_url: str) -> None:
        self.issuer = f"{supabase_url}/auth/v1"
        self.key_client = jwt.PyJWKClient(f"{self.issuer}/.well-known/jwks.json")

    def verify(self, token: str) -> VerifiedSupabaseToken:
        try:
            header = jwt.get_unverified_header(token)
            if header.get("alg") not in ALLOWED_JWKS_ALGORITHMS:
                raise invalid_token()
            signing_key = self.key_client.get_signing_key_from_jwt(token)
            decoded = jwt.decode(
                token,
                signing_key.key,
                algorithms=list(ALLOWED_JWKS_ALGORITHMS),
                audience="authenticated",
                issuer=self.issuer,
                options={"require": ["sub", "exp", "iss", "aud", "role"]},
            )
        except ContractAPIException:
            raise
        except (jwt.PyJWTError, ValueError) as error:
            raise invalid_token() from error
        return _validated_token(token, dict(decoded), issuer=self.issuer)


class AuthServerTokenVerifier:
    def __init__(self, supabase_url: str, anon_key: str, timeout_seconds: int) -> None:
        self.issuer = f"{supabase_url}/auth/v1"
        self.user_url = f"{self.issuer}/user"
        self.anon_key = anon_key
        self.timeout_seconds = timeout_seconds

    def verify(self, token: str) -> VerifiedSupabaseToken:
        if not self.anon_key:
            raise invalid_token()
        try:
            response = httpx.get(
                self.user_url,
                headers={
                    "apikey": self.anon_key,
                    "Authorization": f"Bearer {token}",
                },
                timeout=self.timeout_seconds,
            )
            if response.status_code != 200:
                raise invalid_token()
            returned_user = response.json()
            if not isinstance(returned_user, dict):
                raise invalid_token()
            decoded = jwt.decode(
                token,
                options={
                    "verify_signature": False,
                    "verify_exp": False,
                    "verify_aud": False,
                    "verify_iss": False,
                },
            )
            if not isinstance(decoded, dict):
                raise invalid_token()
        except ContractAPIException:
            raise
        except (httpx.HTTPError, jwt.PyJWTError, ValueError) as error:
            raise invalid_token() from error
        return _validated_token(
            token,
            dict(decoded),
            issuer=self.issuer,
            returned_user=dict(returned_user),
        )


@lru_cache(maxsize=4)
def _build_verifier(
    mode: str,
    supabase_url: str,
    anon_key: str,
    timeout_seconds: int,
) -> TokenVerifier:
    if mode == "jwks":
        return JWKSTokenVerifier(supabase_url)
    if mode == "auth_server":
        return AuthServerTokenVerifier(supabase_url, anon_key, timeout_seconds)
    raise RuntimeError("SUPABASE_JWT_VERIFY_MODE must be 'jwks' or 'auth_server'")


def get_token_verifier() -> TokenVerifier:
    return _build_verifier(
        str(settings.SUPABASE_JWT_VERIFY_MODE),
        str(settings.SUPABASE_URL),
        str(settings.SUPABASE_ANON_KEY),
        int(settings.SUPABASE_JWT_HTTP_TIMEOUT_SECONDS),
    )
