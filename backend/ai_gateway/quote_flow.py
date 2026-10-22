"""Flow A11 — engine price and the canonical «Borrador» PDF of a work.

Runs with the person's own request (price authority, owner MFA, RLS),
outside any open transaction, through the same services the manual
«Calcular precio de la obra» uses: a pricing preview with the company's
current rules, its application (never a discount, never a commercial
number) and the draft render. Any missing authority — costs, technical
catalog, owner approval — comes back as a blocked cause; nothing is
invented.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

REASON = "Precio preparado por el asistente con las reglas vigentes de la empresa"


# Causes the person can act on; commercial conditions are a human decision
# the assistant never fills in.
_DOCUMENT_CAUSES = {
    "project_documentary_inputs_required": "faltan las condiciones comerciales (forma de pago y vigencia); "
                                           "complétalas en Cotización › Preparar",
    "applied_pricing_authority_required": "falta un precio aplicado vigente",
}


def _document_cause(error) -> str:
    code = getattr(error, "contract_code", None) or getattr(error, "code", None)
    if code in _DOCUMENT_CAUSES:
        return _DOCUMENT_CAUSES[code]
    detail = getattr(error, "public_detail", None) or getattr(error, "detail", None)
    return str(detail or "el borrador no se pudo generar")


def _blocked(cause: str) -> dict:
    return {"status": "blocked", "cause": cause[:240], "operation_id": None, "pdf": False}


def prepare(request, project_id: UUID) -> dict:
    from authentication.errors import ContractAPIException
    from authentication.views import verified_request_token
    from dekopen_engine.commercial import PricingError
    from documents import issuance
    from documents.repository import DocumentaryError
    from documents.views import documentary_scope
    from pricing.repository import commercial_backend, rows
    from pricing.serializers import PriceRequestSerializer
    from pricing.service import apply_operation, pricing_public_detail
    from pricing.simple_policy import read_policy
    from pricing.views import _preview_with_retry, scope as pricing_scope
    from projects import service as projects_service

    try:
        with pricing_scope(request, ("OWNER", "ESTIMATOR")) as (_, _, org_id):
            currency = rows("SELECT currency FROM public.tenancy_organizations WHERE id=%s", [str(org_id)])[0]["currency"]
            project = projects_service.project_public(org_id, projects_service.project_row(org_id, project_id))
            with commercial_backend():
                simple = not read_policy(org_id)["use_advanced"]
        applied_id = project.get("current_pricing_operation_id")
        if simple and not applied_id:
            # Simple pricing (P04): the working price is automatic. The draft
            # renders from it; the price is applied only when issuing.
            working = project.get("working_price") or {}
            if working.get("state") != "READY":
                return _blocked(str(working.get("reason") or "El precio de trabajo de la obra aún no está listo."))
        elif not applied_id:
            serializer = PriceRequestSerializer(data={
                "project_id": str(project_id),
                "pricing_mode": "COST_PLUS_MARGIN",
                "currency": currency if currency in ("CLP", "USD") else "CLP",
                "effective_date": datetime.now(ZoneInfo("America/Santiago")).date().isoformat(),
                "reason": REASON,
            })
            if not serializer.is_valid():
                return _blocked("No se pudo preparar el cálculo de precio.")
            token = verified_request_token(request)
            try:
                operation = _preview_with_retry(token, dict(token.claims), request.headers.get("X-Organization-ID"),
                                                serializer.validated_data)
            except PricingError as error:
                return _blocked(pricing_public_detail(error.code))
            if operation.get("state") == "PENDING":
                return _blocked("El precio requiere la aprobación del dueño antes de aplicarse.")
            with pricing_scope(request, ("OWNER", "ESTIMATOR")) as (token, tenant, org_id):
                with commercial_backend():
                    apply_operation(org_id, token.user_id, tenant.active_organization.role,
                                    UUID(str(operation["id"])), REASON, False)
            applied_id = operation["id"]
        try:
            with documentary_scope(request, ("OWNER", "ESTIMATOR")) as (token, _, org_id):
                content = issuance.draft_preview(org_id=org_id, actor_id=token.user_id, project_id=project_id)
            pdf_cause = None if content.startswith(b"%PDF") else "El borrador no se pudo generar."
        except (ContractAPIException, DocumentaryError) as error:
            pdf_cause = _document_cause(error)
        if pdf_cause:
            # The price stays applied (reversible: «Retirar precio» with an
            # audit reason); the receipt says both facts, never one.
            priced = "Precio aplicado con las reglas vigentes" if applied_id else "Precio de trabajo listo"
            return {"status": "blocked", "operation_id": str(applied_id) if applied_id else None, "pdf": False,
                    "cause": f"{priced}; el PDF borrador no se generó: {pdf_cause}"[:240]}
        return {"status": "applied", "cause": None, "operation_id": str(applied_id) if applied_id else None,
                "pdf": True}
    except PricingError as error:
        return _blocked(pricing_public_detail(error.code))
    except (ContractAPIException, DocumentaryError) as error:
        return _blocked(_document_cause(error).capitalize())
    except Exception:  # noqa: BLE001 — the receipt names the step as blocked; never a fake success
        return _blocked("No se pudo calcular el precio con los datos actuales.")


__all__ = ["prepare"]
