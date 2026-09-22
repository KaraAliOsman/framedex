from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
OPENAPI = ROOT / "backend" / "openapi.yaml"


def test_openapi_contains_only_authorized_shot_11_paths_and_bearer_security() -> None:
    schema = yaml.safe_load(OPENAPI.read_text(encoding="utf-8"))
    assert set(schema["paths"]) == {
        "/api/v1/billing/wallet/",
        "/api/v1/billing/",
        "/api/v1/billing/flow/confirm/{order_id}/",
        "/api/v1/billing/flow/register/{operation_id}/",
        "/api/v1/billing/flow/refund/{operation_id}/",
        "/api/v1/billing/commerce/", "/api/v1/billing/checkout/",
        "/api/v1/billing/change/abandon/", "/api/v1/billing/change/preview/", "/api/v1/billing/change/confirm/", "/api/v1/billing/sync/",
        "/api/v1/billing/flow/plan/{offer_id}/", "/api/v1/billing/flow/registration-return/{operation_id}/",
        "/api/v1/projects/",
        "/api/v1/projects/{project_id}/",
        "/api/v1/projects/{project_id}/clone/",
        "/api/v1/projects/{project_id}/successor/",
        "/api/v1/projects/{project_id}/reset-pricing/",
        "/api/v1/projects/{project_id}/positions/",
        "/api/v1/projects/design-options/{system_id}/",
        "/api/v1/positions/{position_id}/",
        "/api/v1/catalogs/systems/",
        "/api/v1/catalogs/systems/{row_id}/",
        "/api/v1/catalogs/articles/",
        "/api/v1/catalogs/articles/{row_id}/",
        "/api/v1/catalogs/glazing/",
        "/api/v1/catalogs/glazing/{row_id}/",
        "/api/v1/catalogs/hardware-kits/",
        "/api/v1/catalogs/hardware-kits/{row_id}/",
        "/api/v1/auth/me/",
        "/api/v1/engine/calculate/",
        "/api/v1/engine/assembly/calculate/",
        "/api/v1/engine/layout/",
        "/api/v1/engine/systems/",
        "/api/v1/engine/inspect/",
        "/api/v1/engine/optimize-cut/",
        "/api/v1/pricing/admin/{resource}/",
        "/api/v1/pricing/preview/",
        "/api/v1/pricing/operations/",
        "/api/v1/pricing/operations/{operation_id}/apply/",
        "/api/v1/pricing/drafts/",
        "/api/v1/pricing/import/",
        "/api/v1/documents/projects/{project_id}/freeze/",
        "/api/v1/documents/projects/{project_id}/inputs/",
        "/api/v1/documents/artifacts/",
        "/api/v1/documents/artifacts/{artifact_id}/access/",
        "/api/v1/purchasing/versions/",
        "/api/v1/purchasing/versions/{version_id}/",
        "/api/v1/purchasing/versions/{version_id}/eligibilities/",
        "/api/v1/purchasing/versions/{version_id}/confirm/",
        "/api/v1/purchasing/requirements/{requirement_id}/allocation/",
        "/api/v1/purchasing/orders/{order_id}/send/",
    }
    bearer = schema["components"]["securitySchemes"]["SupabaseBearer"]
    assert bearer == {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}


def test_engine_response_includes_shot06_and_excludes_inspector() -> None:
    schema = yaml.safe_load(OPENAPI.read_text(encoding="utf-8"))
    assert set(schema["components"]["schemas"]["EngineCalculateResponse"]["properties"]) == {
        "calculation_hash", "profile_cuts", "reinforcements", "glasses",
        "panels", "hardware_items", "leaf_weights",
    }


def test_persisted_quotation_color_is_white_without_narrowing_generic_engine_schema() -> None:
    schema = yaml.safe_load(OPENAPI.read_text(encoding="utf-8"))["components"]["schemas"]
    assert schema["WhiteColorEnum"]["enum"] == ["WHITE"]
    assert schema["ColorEnum"]["enum"] == ["WHITE", "FOILED"]
    assert schema["PositionDesignRequest"]["properties"]["color"] == {
        "$ref": "#/components/schemas/WhiteColorEnum"
    }
    assert schema["PositionDesign"]["properties"]["color"] == {
        "$ref": "#/components/schemas/WhiteColorEnum"
    }
    assert schema["PositionResponse"]["properties"]["design"] == {
        "$ref": "#/components/schemas/PositionDesign"
    }
    assert schema["DraftPositionRequest"]["properties"]["color"] == {
        "$ref": "#/components/schemas/WhiteColorEnum"
    }
    finish = schema["WorkshopAnnotationRequest"]["properties"]["finish_class"]
    assert {item.get("$ref") for item in finish["oneOf"]} >= {
        "#/components/schemas/WhiteColorEnum"
    }
    assert schema["EngineCalculateRequestRequest"]["properties"]["color"]["type"] == "string"


def test_openapi_documents_active_org_and_mfa_selection_errors() -> None:
    schema = yaml.safe_load(OPENAPI.read_text(encoding="utf-8"))
    for path, method in (
        ("/api/v1/auth/me/", "get"),
        ("/api/v1/engine/calculate/", "post"),
        ("/api/v1/engine/layout/", "post"),
        ("/api/v1/engine/systems/", "get"),
        ("/api/v1/engine/inspect/", "post"),
        ("/api/v1/engine/optimize-cut/", "post"),
        ("/api/v1/pricing/admin/{resource}/", "post"),
        ("/api/v1/pricing/preview/", "post"),
        ("/api/v1/pricing/operations/", "get"),
        ("/api/v1/pricing/operations/{operation_id}/apply/", "post"),
        ("/api/v1/pricing/drafts/", "post"),
        ("/api/v1/pricing/import/", "post"),
        ("/api/v1/documents/projects/{project_id}/freeze/", "post"),
        ("/api/v1/documents/projects/{project_id}/inputs/", "put"),
        ("/api/v1/documents/artifacts/", "post"),
        ("/api/v1/documents/artifacts/{artifact_id}/access/", "post"),
        ("/api/v1/purchasing/versions/", "get"),
        ("/api/v1/purchasing/versions/{version_id}/", "get"),
        ("/api/v1/purchasing/versions/{version_id}/eligibilities/", "post"),
        ("/api/v1/purchasing/versions/{version_id}/confirm/", "post"),
        ("/api/v1/projects/{project_id}/successor/", "post"),
        ("/api/v1/projects/{project_id}/reset-pricing/", "post"),
        ("/api/v1/purchasing/requirements/{requirement_id}/allocation/", "put"),
        ("/api/v1/purchasing/orders/{order_id}/send/", "post"),
    ):
        header = next(p for p in schema["paths"][path][method]["parameters"] if p["name"] == "X-Organization-ID")
        assert header["in"] == "header"
        assert header["schema"]["format"] == "uuid"
    assert "required_aal" in schema["components"]["schemas"]["ErrorDetail"]["properties"]
    assert "memberships" in schema["components"]["schemas"]["ErrorResponse"]["properties"]
