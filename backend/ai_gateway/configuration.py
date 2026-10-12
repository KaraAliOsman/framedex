"""OWNER operational settings. Credentials are environment-only, never a field."""

from decimal import Decimal
import json
import os

from ai_gateway import usage
from ai_gateway.providers import _mock_enabled
from authentication.errors import contract_error
from billing.wallet import financial_transaction
from pricing.repository import rows

PROVIDERS = ("MIMO", "OPENAI", "OPENROUTER", "DEEPSEEK", "QWEN", "MOCK")
CAUSES = {
    "ai_provider_unavailable": "Falta la credencial o la dirección segura del proveedor. Configúralas en el servidor y vuelve a probar.",
    "ai_provider_auth": "La credencial fue rechazada. Reemplázala en el servidor y vuelve a probar.",
    "ai_provider_quota": "El proveedor llegó a su límite de uso. Revisa la cuota de su cuenta y vuelve a probar.",
    "ai_provider_rejected": "El proveedor rechazó esta configuración. Revisa el modelo y su protocolo.",
    "ai_provider_timeout": "El proveedor no respondió dentro del tiempo configurado. Reintenta o revisa el tiempo máximo.",
    "ai_provider_mock_disabled": "El modo de prueba está deshabilitado en el servidor. Elige un proveedor real.",
    "ai_tools_unsupported": "Este modelo no admite herramientas nativas. Elige el modo automático o JSON validado.",
    "ai_budget_exceeded": "Se alcanzó el presupuesto mensual. Ajusta el límite para volver a usar la IA.",
    "ai_connection_oracle_failed": "El proveedor respondió, pero no superó el caso mínimo. Revisa el modelo y vuelve a probar.",
    "ai_operation_in_progress": "La solicitud está en curso o ya consultó al proveedor. Revisa Trabajos antes de iniciar otra.",
}


def cause(code):
    return CAUSES.get(code, "No se pudo obtener una respuesta válida. Reintenta y revisa la conexión del proveedor.")


def effective_model(route):
    return route["provider_model"] if route.get("tenant_model") else os.environ.get(f"AI_GATEWAY_{route['provider']}_MODEL") or route["provider_model"]


def route_signature(route):
    return (route["provider"], effective_model(route),
            route.get("connection_updated_at") or route.get("updated_at"), route.get("timeout_s", 60), route.get("retries", 2),
            route.get("tools_mode", "AUTO"))


def get(org_id):
    from ai_gateway.service import _route
    with financial_transaction(org_id):
        stored = rows("SELECT * FROM public.ai_settings WHERE org_id=%s", [str(org_id)])
        routes = []
        for capability in usage.CAPABILITIES:
            route = _route(capability, org_id)
            if route is None:
                raise contract_error(503, "ai_capability_unknown", "Falta una ruta de IA en el servidor. Revisa la instalación.")
            provider = route["provider"]
            model = effective_model(route)
            configured = _mock_enabled() if provider == "MOCK" else bool(os.environ.get(f"AI_GATEWAY_{provider}_API_KEY") and os.environ.get(f"AI_GATEWAY_{provider}_BASE_URL"))
            state = "UNTESTED"
            configured_after = route.get("connection_updated_at") or route.get("updated_at")
            latest = rows("SELECT status,error_code,completed_at FROM public.ai_provider_usage WHERE org_id=%s AND capability=%s AND provider=%s AND provider_model=%s AND status <> 'RUNNING' AND (%s::timestamptz IS NULL OR created_at >= %s) ORDER BY completed_at DESC LIMIT 1", [str(org_id), capability, provider, model, configured_after, configured_after])
            last = latest[0] if latest else None
            if last:
                state = "CONNECTED" if last["status"] == "SUCCEEDED" else "ERROR"
            checked_at = last["completed_at"] if last else None
            if route.get("checked_at") and (checked_at is None or route["checked_at"] >= checked_at):
                state = route["connection_state"]
                checked_at = route["checked_at"]
            if not configured:
                state = "MISSING_CREDENTIAL"
            routes.append({"capability": capability, "provider": provider, "provider_model": model,
                           "timeout_s": route.get("timeout_s", 60), "retries": route.get("retries", 2),
                           "tools_mode": route.get("tools_mode", "AUTO"), "credits_cost": route["credits_cost"],
                           "input_usd_per_million": str(route["input_usd_per_million"]) if route.get("input_usd_per_million") is not None else None,
                           "output_usd_per_million": str(route["output_usd_per_million"]) if route.get("output_usd_per_million") is not None else None,
                           "credential_configured": configured, "test_mode": provider == "MOCK", "state": state,
                           "last_cause": cause(route.get("connection_code") or last.get("error_code")) if state == "ERROR" and last else
                                         cause(route.get("connection_code")) if state == "ERROR" else None,
                           "checked_at": str(checked_at) if checked_at else None})
    return {"revision": stored[0]["revision"] if stored else 1, "routes": routes,
            "mock_available": _mock_enabled(), "usage": usage.summary(org_id)}


def save(org_id, user_id, data):
    from ai_gateway.service import _route
    with financial_transaction(org_id):
        rows("INSERT INTO public.ai_settings(org_id) VALUES(%s) ON CONFLICT DO NOTHING RETURNING org_id", [str(org_id)])
        updated = rows("UPDATE public.ai_settings SET monthly_budget_credits=%s, revision=revision+1,updated_at=now(),updated_by=%s,budget_notice_at=NULL WHERE org_id=%s AND revision=%s RETURNING revision", [data["monthly_budget_credits"], str(user_id), str(org_id), data["expected_revision"]])
        if not updated:
            raise contract_error(409, "ai_settings_conflict", "Otro dueño cambió estos ajustes. Recarga antes de guardar.")
        for route in data["routes"]:
            if route["provider"] == "MOCK" and not _mock_enabled():
                raise contract_error(409, "ai_provider_mock_disabled", cause("ai_provider_mock_disabled"))
            current = _route(route["capability"], org_id)
            transport_changed = any(route[key] != (effective_model(current) if key == "provider_model" else current.get(key, default))
                                    for key, default in (("provider", None), ("provider_model", None), ("timeout_s", 60), ("retries", 2), ("tools_mode", "AUTO")))
            rates = ("input_usd_per_million", "output_usd_per_million")
            tariff_changed = any((Decimal(str(route[key])) if route[key] is not None else None) != current.get(key) for key in rates)
            if not transport_changed and not tariff_changed:
                continue
            # Tariffs affect future sealed costs, not the tested connection.
            # A transport timestamp isolates each capability from budget edits
            # and invalidates an in-flight probe even after changing A→B→A.
            rows("INSERT INTO public.ai_capability_routes(org_id,capability,provider,provider_model,timeout_s,retries,tools_mode,input_usd_per_million,output_usd_per_million,connection_updated_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,CASE WHEN %s THEN now() ELSE %s::timestamptz END) ON CONFLICT(org_id,capability) DO UPDATE SET provider=excluded.provider,provider_model=excluded.provider_model,timeout_s=excluded.timeout_s,retries=excluded.retries,tools_mode=excluded.tools_mode,input_usd_per_million=excluded.input_usd_per_million,output_usd_per_million=excluded.output_usd_per_million,revision=ai_capability_routes.revision+CASE WHEN %s THEN 1 ELSE 0 END,connection_updated_at=CASE WHEN %s THEN now() ELSE ai_capability_routes.connection_updated_at END,connection_state=CASE WHEN %s THEN 'UNTESTED' ELSE ai_capability_routes.connection_state END,connection_code=CASE WHEN %s THEN NULL ELSE ai_capability_routes.connection_code END,checked_at=CASE WHEN %s THEN NULL ELSE ai_capability_routes.checked_at END RETURNING capability",
                 [str(org_id), route["capability"], route["provider"], route["provider_model"], route["timeout_s"], route["retries"], route["tools_mode"], route["input_usd_per_million"], route["output_usd_per_million"], transport_changed, current.get("connection_updated_at") or current.get("updated_at"), *([transport_changed] * 5)])
    return get(org_id)


def probe(org_id, user_id, data):
    """IA1 E03 reduced to its explicit width/height intent, no project mutation.
    Exact oracle and pure engine evaluation of a copy precede green status.
    """
    from ai_gateway.service import invoke, _route
    from projects.design_assist import DESIGN_ASSIST_SYSTEM, _summary
    from projects.ops_registry import catalog_for, calculate_product
    from engine_api.repository import SystemParamsRepository
    from dekopen_engine.design_operations import apply_operations, validate_operation, BY_NAME
    systems = SystemParamsRepository().list_visible(org_id)
    if not systems:
        raise contract_error(409, "ai_probe_catalog_required", "La prueba necesita una serie visible. Importa un catálogo o prepara el catálogo DEMO antes de probar.")
    catalog = None
    for system in systems:
        candidate = catalog_for(org_id, system.id)
        if candidate["params"].finishes:
            catalog = candidate
            break
    if catalog is None:
        raise contract_error(409, "ai_probe_catalog_required", "La prueba necesita una serie con acabados declarados. Completa el catálogo antes de probar.")
    product = {"version": "product-v2", "assembly": {
        "modules": [{"id": "m1", "width_mm": "1500.00", "height_mm": "1200.00",
        "tree": {"id": "root", "type": "BAY", "opening_type": "FIXED"}}], "couplings": []}}
    if catalog.get("glass_skus"):
        product = apply_operations(product, [{"op": "set_glass", "module": "m1", "sku": sorted(catalog["glass_skus"])[0]}], params=catalog["params"], catalog=catalog, finish=next(iter(catalog["params"].finishes)))["product"]
    with financial_transaction(org_id):
        tested_route = _route("design_assist", org_id)
    result = invoke(org_id=org_id, user_id=user_id, capability="design_assist", tool_name="connection_test", operation_key=data["operation_key"],
                    input_payload={"prompt": "hazla de 1,8 metros de ancho por 1350 de alto", "product": _summary(product),
                        "ops_contract": [BY_NAME["set_total_width"], BY_NAME["set_height"]]},
                    provider_options={"system": DESIGN_ASSIST_SYSTEM + "\nConvierte las unidades declaradas por el usuario a milímetros antes de proponer medidas.", "json_output": True,
                        "response_schema": {"type": "object", "additionalProperties": False, "required": ["ops", "notes"],
                            "properties": {"ops": {"type": "array", "maxItems": 5, "items": {"type": "object"}}, "notes": {"type": "string"}}}})
    try:
        document = json.loads(result["output"])
        for operation in document["ops"]:
            validate_operation(operation)
        after = apply_operations(product, document["ops"], params=catalog["params"], catalog=catalog, finish=next(iter(catalog["params"].finishes)))["product"]
        assembly = after.get("assembly", after)
        modules = assembly["modules"]
        valid = len(modules) == 1 and Decimal(str(modules[0]["width_mm"])) == Decimal("1800") and Decimal(str(modules[0]["height_mm"])) == Decimal("1350")
        evaluation = calculate_product(org_id, after, system.id, next(iter(catalog["params"].finishes)), catalog)
        valid = valid and evaluation["status"] in {"VALID", "MANUFACTURING_INCOMPLETE"} and not any(issue.get("severity") == "error" for issue in evaluation.get("issues", []))
        usage.note(org_id, result.get("usage_id"), "calculate_position", "OK" if valid else "ERROR")
    except (ValueError, KeyError, TypeError, AttributeError):
        valid = False
    # A first probe also needs a tenant row. Otherwise an invalid engine
    # oracle would disappear behind the successful HTTP exchange on GET.
    def record_oracle():
        with financial_transaction(org_id):
            rows("SELECT capability FROM public.ai_capability_routes WHERE org_id=%s AND capability='design_assist' FOR UPDATE", [str(org_id)])
            route = _route("design_assist", org_id)
            if route_signature(route) != route_signature(tested_route):
                return False
            if not route.get("tenant_model"):
                inserted = rows("INSERT INTO public.ai_capability_routes(org_id,capability,provider,provider_model,connection_updated_at) VALUES(%s,'design_assist',%s,%s,%s) ON CONFLICT DO NOTHING RETURNING capability",
                                [str(org_id), tested_route["provider"], effective_model(tested_route), tested_route.get("updated_at")])
                if not inserted:
                    return False
            rows("UPDATE public.ai_capability_routes SET connection_state=%s,connection_code=%s,checked_at=now() WHERE org_id=%s AND capability='design_assist' RETURNING capability",
                 ["CONNECTED" if valid else "ERROR", None if valid else "ai_connection_oracle_failed", str(org_id)])
            return True
    if not usage.independent(record_oracle):
        raise contract_error(409, "ai_settings_conflict", "Los ajustes de IA cambiaron durante la prueba. Vuelve a probar la configuración actual.")
    if not valid:
        raise contract_error(503, "ai_connection_oracle_failed", cause("ai_connection_oracle_failed"))
    usage.note(org_id, result.get("usage_id"), "validate_operations")
    return {"passed": True, "case_id": "E03", "test_mode": result.get("test_mode", False), "tokens_prompt": result["tokens_prompt"], "tokens_completion": result["tokens_completion"], "credits_debited": result["credits_debited"], "latency_ms": result["latency_ms"]}
