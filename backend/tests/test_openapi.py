from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
OPENAPI = ROOT / "backend" / "openapi.yaml"


def test_openapi_contains_only_shot_04_paths_and_bearer_security() -> None:
    schema = yaml.safe_load(OPENAPI.read_text(encoding="utf-8"))
    assert set(schema["paths"]) == {
        "/api/v1/auth/me/",
        "/api/v1/engine/calculate/",
    }
    bearer = schema["components"]["securitySchemes"]["SupabaseBearer"]
    assert bearer == {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}


def test_engine_response_excludes_future_fields() -> None:
    schema_text = OPENAPI.read_text(encoding="utf-8")
    assert "calculation_hash" not in schema_text
    assert "inspector" not in schema_text


def test_openapi_documents_active_org_and_mfa_selection_errors() -> None:
    schema = yaml.safe_load(OPENAPI.read_text(encoding="utf-8"))
    for path, method in (("/api/v1/auth/me/", "get"), ("/api/v1/engine/calculate/", "post")):
        header = next(p for p in schema["paths"][path][method]["parameters"] if p["name"] == "X-Organization-ID")
        assert header["in"] == "header"
        assert header["schema"]["format"] == "uuid"
    assert "required_aal" in schema["components"]["schemas"]["ErrorDetail"]["properties"]
    assert "memberships" in schema["components"]["schemas"]["ErrorResponse"]["properties"]
