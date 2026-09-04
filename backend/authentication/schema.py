"""OpenAPI security-scheme registration for drf-spectacular."""

from drf_spectacular.extensions import OpenApiAuthenticationExtension


class SupabaseJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "authentication.backends.SupabaseJWTAuthentication"
    name = "SupabaseBearer"

    def get_security_definition(self, auto_schema: object) -> dict[str, str]:
        return {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
