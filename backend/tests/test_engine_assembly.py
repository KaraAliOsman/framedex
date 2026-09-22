from __future__ import annotations

from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from backend.tests.factories import (
    SYSTEM_ID,
)
from backend.tests.test_engine_api import configure_api
from dekopen_engine.models import (
    EffectiveProfileArticle,
    MaterialType,
    ProfileRole,
)
from engine_api.adapter import (
    InvalidEngineRequest,
    parse_product_model,
)
from engine_api.repository import SystemParamsRepository

COUPLER_ARTICLE = EffectiveProfileArticle(
    sku="ACOPLE-60",
    role=ProfileRole.COUPLER,
    material=MaterialType.PVC,
    face_width_mm=Decimal("40.00"),
    welding_loss_mm=Decimal("0.00"),
    reinforcement_gap_mm=Decimal("0.00"),
    weight_kg_m=Decimal("0.9000"),
    steel_weight_kg_m=None,
    reinforcement_sku=None,
)


def configure_assembly_api(
    client: APIClient,
    monkeypatch: pytest.MonkeyPatch,
    couplers: dict[str, EffectiveProfileArticle] | None = None,
) -> None:
    configure_api(client, monkeypatch)
    monkeypatch.setattr(
        SystemParamsRepository,
        "load_coupler_articles",
        lambda self, system_id, active_org_id: couplers or {},
    )


def bow_product(angle: str = "15", coupler_sku: str | None = None) -> dict[str, object]:
    def module(index: int) -> dict[str, object]:
        return {
            "id": f"m{index}",
            "width_mm": "700.00",
            "height_mm": "1400.00",
            "tree": {
                "id": f"m{index}",
                "type": "BAY",
                "opening_type": "FIXED",
                "glass_thickness_mm": "4.00",
                "glass_spec": "4",
            },
        }

    return {
        "version": "product-v2",
        "assembly": {
            "modules": [module(1), module(2), module(3)],
            "couplings": [
                {"id": "c1", "angle_deg": angle, "coupler_profile_sku": coupler_sku},
                {"id": "c2", "angle_deg": angle, "coupler_profile_sku": coupler_sku},
            ],
        },
    }


def bow_request(product: dict[str, object] | None = None) -> dict[str, object]:
    return {
        "system_id": str(SYSTEM_ID),
        "nominal_width_mm": "2100.00",
        "nominal_height_mm": "1400.00",
        "color": "WHITE",
        "product": product or bow_product(),
    }


class TestAssemblyParse:
    def test_rejects_wrong_version(self) -> None:
        with pytest.raises(InvalidEngineRequest):
            parse_product_model({"version": "product-v3", "assembly": {}})

    def test_rejects_unknown_module_fields(self) -> None:
        product = bow_product()
        product["assembly"]["modules"][0]["surprise"] = True
        with pytest.raises(InvalidEngineRequest):
            parse_product_model(product)

    def test_rejects_duplicate_module_ids(self) -> None:
        product = bow_product()
        product["assembly"]["modules"][1]["id"] = "m1"
        with pytest.raises(InvalidEngineRequest):
            parse_product_model(product)

    def test_rejects_non_string_decimals(self) -> None:
        product = bow_product()
        product["assembly"]["modules"][0]["width_mm"] = 700
        with pytest.raises(InvalidEngineRequest):
            parse_product_model(product)


class TestAssemblyEndpoint:
    def test_bow_without_couplers_is_manufacturing_incomplete(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        client = APIClient()
        configure_assembly_api(client, monkeypatch)
        response = client.post(
            "/api/v1/engine/assembly/calculate/", bow_request(), format="json"
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "MANUFACTURING_INCOMPLETE"
        codes = {issue["code"] for issue in payload["issues"]}
        assert codes == {"coupler_profile_missing"}
        assert len(payload["plan"]["modules"]) == 3
        assert len(payload["plan"]["couplings"]) == 2
        assert len(payload["plan"]["front_chain"]) == 4
        assert len(payload["modules"]) == 3
        assert payload["bom"] is not None
        assert any(
            cut["sku"] == "MARCO" for cut in payload["bom"]["profile_cuts"]
        )
        assert payload["calculation_hash"].startswith("sha256:")

    def test_bow_with_catalog_couplers_is_valid(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        client = APIClient()
        configure_assembly_api(
            client, monkeypatch, couplers={"ACOPLE-60": COUPLER_ARTICLE}
        )
        request = bow_request(bow_product(coupler_sku="ACOPLE-60"))
        response = client.post(
            "/api/v1/engine/assembly/calculate/", request, format="json"
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "VALID"
        assert payload["issues"] == []
        coupler_cuts = [
            cut
            for cut in payload["bom"]["profile_cuts"]
            if cut["role"] == "COUPLER"
        ]
        assert [cut["length_mm"] for cut in coupler_cuts] == [
            "1400.00",
            "1400.00",
        ]

    def test_fold_back_geometry_returns_invalid_status_not_http_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        client = APIClient()
        configure_assembly_api(client, monkeypatch)
        response = client.post(
            "/api/v1/engine/assembly/calculate/",
            bow_request(bow_product(angle="95")),
            format="json",
        )
        assert response.status_code == 200
        assert response.json()["status"] == "INVALID"

    def test_malformed_product_is_400(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        client = APIClient()
        configure_assembly_api(client, monkeypatch)
        response = client.post(
            "/api/v1/engine/assembly/calculate/",
            bow_request({"version": "product-v2"}),
            format="json",
        )
        assert response.status_code == 400
