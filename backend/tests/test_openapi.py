from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
OPENAPI = ROOT / "backend" / "openapi.yaml"


def test_openapi_contains_only_authorized_shot_08_paths_and_bearer_security() -> None:
    schema = yaml.safe_load(OPENAPI.read_text(encoding="utf-8"))
    assert set(schema["paths"]) == {
        "/api/v1/auth/me/",
        "/api/v1/engine/calculate/",
        "/api/v1/engine/systems/",
        "/api/v1/engine/inspect/",
        "/api/v1/engine/optimize-cut/",
        "/api/v1/pricing/admin/{resource}/",
        "/api/v1/pricing/preview/",
        "/api/v1/pricing/operations/",
        "/api/v1/pricing/operations/{operation_id}/apply/",
        "/api/v1/pricing/drafts/",
        "/api/v1/pricing/import/",
    }
    bearer = schema["components"]["securitySchemes"]["SupabaseBearer"]
    assert bearer == {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}


def test_engine_response_includes_shot06_and_excludes_inspector() -> None:
    schema = yaml.safe_load(OPENAPI.read_text(encoding="utf-8"))
    assert set(schema["components"]["schemas"]["EngineCalculateResponse"]["properties"]) == {
        "calculation_hash", "profile_cuts", "reinforcements", "glasses",
        "panels", "hardware_items", "leaf_weights",
    }


def test_openapi_documents_active_org_and_mfa_selection_errors() -> None:
    schema = yaml.safe_load(OPENAPI.read_text(encoding="utf-8"))
    for path, method in (
        ("/api/v1/auth/me/", "get"),
        ("/api/v1/engine/calculate/", "post"),
        ("/api/v1/engine/systems/", "get"),
        ("/api/v1/engine/inspect/", "post"),
        ("/api/v1/engine/optimize-cut/", "post"),
        ("/api/v1/pricing/admin/{resource}/", "post"),
        ("/api/v1/pricing/preview/", "post"),
        ("/api/v1/pricing/operations/", "get"),
        ("/api/v1/pricing/operations/{operation_id}/apply/", "post"),
        ("/api/v1/pricing/drafts/", "post"),
        ("/api/v1/pricing/import/", "post"),
    ):
        header = next(p for p in schema["paths"][path][method]["parameters"] if p["name"] == "X-Organization-ID")
        assert header["in"] == "header"
        assert header["schema"]["format"] == "uuid"
    assert "required_aal" in schema["components"]["schemas"]["ErrorDetail"]["properties"]
    assert "memberships" in schema["components"]["schemas"]["ErrorResponse"]["properties"]
