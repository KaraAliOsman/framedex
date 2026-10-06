"""Recover the declared combination without changing historical identities."""

import json
from collections.abc import Mapping
from datetime import datetime
from zoneinfo import ZoneInfo

from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.errors import contract_error
from authentication.serializers import ACTIVE_ORGANIZATION_HEADER
from dekopen_engine.catalog_rules import CatalogRuleError
from dekopen_engine.commercial import PricingError, PricingMode
from dekopen_engine.weight import MissingFabricationAuthority
from engine_api.serializers import EngineCalculateRequestSerializer
from engine_api.repository import SystemNotFound, UnsupportedCatalogContract
from pricing.repository import PricingRepository, commercial_backend, rows
from pricing.views import scope, validate, ERRORS


def position_finish_code(position: Mapping[str, object]) -> str:
    raw = position.get("bom_snapshot")
    if isinstance(raw, str):
        raw = json.loads(raw)
    if isinstance(raw, dict) and raw.get("finish"):
        return str(raw["finish"]["combination"]["code"])
    interior, exterior = position.get("color_interior"), position.get("color_exterior")
    if interior == exterior and isinstance(interior, str):
        return interior
    # Old bicolor positions used this exact manufacturing identity.
    return "FOILED"


class FinishPreviewRequestSerializer(EngineCalculateRequestSerializer):
    baseline_color = serializers.CharField(max_length=50)


class FinishPreviewResponseSerializer(serializers.Serializer):
    delta_price_net = serializers.CharField(allow_null=True)
    currency = serializers.CharField()
    baseline_description = serializers.CharField()
    description = serializers.CharField()
    source = serializers.CharField()
    reason = serializers.CharField(allow_null=True)


def finish_preview(org_id, data):
    from engine_api.repository import SystemParamsRepository
    from dekopen_engine.finishes import resolve_finish, finish_selling_delta
    from pricing.service import position_cost, configured_unit_price, pricing_public_detail
    from projects.service import _typology
    params = SystemParamsRepository().load_visible(data["system_id"], org_id)
    selected = resolve_finish(params, data["color"])
    baseline = resolve_finish(params, data["baseline_color"])
    if selected is None or baseline is None:
        raise contract_error(422, "finish_authority_missing", "Sin dato: esta serie no declara una carta por caras. Completa el catálogo.")
    def description(finish):
        return f"{finish.exterior.name} exterior / {finish.interior.name} interior"
    response = {"delta_price_net": None, "currency": "CLP", "baseline_description": description(baseline),
        "description": description(selected), "source": selected.combination.surcharge.source, "reason": None}
    with commercial_backend():
        currency = rows("SELECT currency FROM public.tenancy_organizations WHERE id=%s", [org_id])[0]["currency"]
        response["currency"] = currency
        rules = rows("SELECT * FROM public.pricing_rules WHERE org_id=%s", [org_id])
        if not rules:
            return {**response, "reason": "Sin dato: completa las reglas de precio en Ajustes."}
        repo = PricingRepository(org_id, datetime.now(ZoneInfo("America/Santiago")).date(), currency, None)
        totals = []
        try:
            mode = PricingMode(rules[0]["pricing_mode"])
            if mode == PricingMode.TARGET_GROSS_MARGIN_PROJECT:
                return {**response, "reason": "Sin dato por posición: el margen objetivo requiere calcular el proyecto completo en Precios."}
            calculated_rules = {**rules[0], **{field: repo.convert(rules[0][field], currency)
                for field in ("labor_rate_per_m2", "installation_rate_per_m2")}}
            for code in (data["baseline_color"], data["color"]):
                position = {"system_id": data["system_id"],
                    "width_mm": data["nominal_width_mm"], "height_mm": data["nominal_height_mm"],
                    "color_interior": code, "color_exterior": code, "parametric_tree": data["parametric_tree"],
                    "typology": _typology(data["parametric_tree"])}
                cost, area, result, _ = position_cost(repo, position, calculated_rules)
                finish = resolve_finish(params, code)
                position.update(color_interior=finish.interior.code, color_exterior=finish.exterior.code)
                price = configured_unit_price(repo, mode, position, cost=cost, area=area,
                    result=result, margin=rules[0]["default_margin_pct"], context_code="DEFAULT")
                if price < cost:
                    raise PricingError("negative_margin")
                totals.append(price)
        except PricingError as error:
            return {**response, "reason": "Sin dato: " + pricing_public_detail(error.code)}
        response["delta_price_net"] = str(finish_selling_delta(totals[0], totals[1]))
        response["source"] += "; tarifa y modo predeterminado configurados en Ajustes › Precios; precio neto indicativo por posición, sin descuento, contexto predeterminado"
        return response


class FinishPreviewView(APIView):
    @extend_schema(operation_id="projectFinishPreview", request=FinishPreviewRequestSerializer,
        responses={200: FinishPreviewResponseSerializer, **ERRORS}, parameters=[ACTIVE_ORGANIZATION_HEADER])
    def post(self, request):
        data = validate(FinishPreviewRequestSerializer, request.data)
        try:
            with scope(request, {"OWNER", "ESTIMATOR"}) as (_, _, org_id):
                result = finish_preview(org_id, data)
            return Response(result)
        except SystemNotFound as error:
            raise contract_error(404, "system_not_found", "La serie no está disponible. Elige otra serie.") from error
        except CatalogRuleError as error:
            raise contract_error(422, error.code, str(error)) from error
        except (MissingFabricationAuthority, UnsupportedCatalogContract) as error:
            raise contract_error(409, "finish_authority_missing", str(error)) from error
        except ValueError as error:
            raise contract_error(422, "finish_preview_invalid", "No se puede calcular el cambio: revisa medidas, aperturas y vidrio.") from error
