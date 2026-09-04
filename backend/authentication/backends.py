"""DRF authentication adapter for verified Supabase access tokens."""

from __future__ import annotations

from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.request import Request

from authentication.errors import invalid_token
from authentication.jwt_verifier import get_token_verifier
from authentication.types import SupabaseUser, VerifiedSupabaseToken


class SupabaseJWTAuthentication(BaseAuthentication):
    keyword = b"bearer"

    def authenticate(
        self, request: Request
    ) -> tuple[SupabaseUser, VerifiedSupabaseToken] | None:
        header = get_authorization_header(request).split()
        if not header:
            return None
        if len(header) != 2 or header[0].lower() != self.keyword:
            raise invalid_token()
        try:
            token = header[1].decode("ascii")
        except UnicodeDecodeError as error:
            raise invalid_token() from error
        verified = get_token_verifier().verify(token)
        return SupabaseUser(id=verified.user_id, email=verified.email), verified

    def authenticate_header(self, request: Request) -> str:
        return "Bearer"
