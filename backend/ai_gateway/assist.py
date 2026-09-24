"""Contextual Ask: question + surface → bounded typed context → provider answer.

The trust contract is the mandate's spine: the provider only answers inside a
server-built projection, it can propose navigation but never a mutation, and
an unknown answer is refused rather than invented. """

from __future__ import annotations

import json
import re
from typing import Any
from uuid import UUID

from ai_gateway import service as gateway
from ai_gateway.context import REQUIRED_REFS, _ContextError, build_context
from authentication.errors import contract_error

CAPABILITY = "context_assist"
MAX_QUESTION = 2000
MAX_ANSWER = 4000
MAX_ACTIONS = 4
MAX_LABEL = 80
MAX_WARNINGS = 8
MAX_WARNING = 240

# Actions the surface may propose. v1 is navigate-only — an AI answer can point
# at where the action lives, it can never execute one. Paths are allowlisted to
# the app's own routes so a provider response can never become an open redirect
# or a javascript: URL.
_ALLOWED_PATHS = re.compile(
    r"^/(dashboard|projects|production|purchasing|catalogs|clients|pricing|settings)"
    r"(/[0-9a-zA-Z\-_/]*)?$|^/$"
)

ASK_SYSTEM = """Eres el asistente contextual de DEKOPEN, una aplicación profesional de ventanas y puertas (español chileno).

Recibes un JSON con:
- "question": la pregunta del usuario.
- "surface": la superficie donde el usuario está trabajando.
- "context": una proyección tipada y limitada de los datos reales de su organización — es la ÚNICA fuente de verdad que tienes.

Respondes SOLO un JSON:
{
  "answer": "respuesta breve y concreta en español (máx. ~120 palabras)",
  "actions": [{"kind": "navigate", "path": "/ruta-de-la-app", "label": "qué muestra"}],
  "warnings": ["alertas opcionales si detectas algo relevante en el contexto"]
}

Reglas:
- Responde SOLO con lo que el contexto muestra. Si el dato no está en el contexto, dilo claramente ("no tengo ese dato") y sugiere dónde encontrarlo — nunca inventes medidas, precios, SKU, nombres o estados.
- Los valores técnicos (dimensiones, precios, cantidades) solo pueden citar números que estén literalmente en el contexto.
- "actions" solo puede proponer navegación dentro de la app (rutas que empiezan con /dashboard, /projects, /production, /purchasing, /catalogs, /clients, /pricing o /settings). Máximo 4.
- "warnings" para problemas reales que el contexto evidencie (ej. escasez de material, una revisión sin congelar). Máximo 8.
- Sin texto fuera del JSON."""


def _answer(document: Any) -> dict:
    if not isinstance(document, dict) or not isinstance(document.get("answer"), str):
        raise contract_error(
            502,
            "ai_assist_bad_output",
            "El asistente devolvió una respuesta inválida.",
        )
    answer = document["answer"].strip()
    if not answer:
        raise contract_error(
            502,
            "ai_assist_bad_output",
            "El asistente devolvió una respuesta inválida.",
        )
    actions = []
    raw_actions = document.get("actions")
    if isinstance(raw_actions, list):
        for item in raw_actions:
            # Cap counts *valid* actions — a padded list of junk must not push
            # real ones out of the response.
            if len(actions) >= MAX_ACTIONS:
                break
            if not isinstance(item, dict):
                continue
            path = item.get("path")
            label = item.get("label")
            if (
                item.get("kind") == "navigate"
                and isinstance(path, str)
                and _ALLOWED_PATHS.match(path)
            ):
                actions.append(
                    {
                        "kind": "navigate",
                        "path": path,
                        "label": (str(label).strip() or path)[:MAX_LABEL],
                    }
                )
    warnings = []
    raw_warnings = document.get("warnings")
    if isinstance(raw_warnings, list):
        for item in raw_warnings:
            if len(warnings) >= MAX_WARNINGS:
                break
            if isinstance(item, str) and item.strip():
                warnings.append(item.strip()[:MAX_WARNING])
    return {
        "answer": answer[:MAX_ANSWER],
        "actions": actions,
        "warnings": warnings,
    }


def ask(
    *,
    org_id: UUID,
    user_id: UUID,
    surface: str,
    refs: dict | None,
    question: str,
    operation_key: str,
) -> dict:
    if surface not in REQUIRED_REFS:
        raise contract_error(
            400,
            "ai_surface_unknown",
            "La superficie solicitada no tiene proyección de contexto.",
        )
    missing = [name for name in REQUIRED_REFS[surface] if name not in (refs or {})]
    if missing:
        raise contract_error(
            400,
            "ai_context_ref_required",
            f"Esta superficie requiere la referencia '{missing[0]}'.",
        )
    try:
        context = build_context(org_id, surface, refs)
    except _ContextError as error:
        if error.code == "ai_context_ref_invalid":
            raise contract_error(
                400,
                "ai_context_ref_invalid",
                "La referencia de contexto no es válida.",
            ) from None
        raise contract_error(
            404,
            "ai_context_not_found",
            "El contexto solicitado no existe o no está disponible.",
        ) from None
    envelope = gateway.invoke(
        org_id=org_id,
        user_id=user_id,
        capability=CAPABILITY,
        operation_key=operation_key,
        tool_name="context_assist",
        provider_options={"system": ASK_SYSTEM, "json_output": True},
        input_payload={
            "question": question[:MAX_QUESTION],
            "surface": surface,
            "context": context,
        },
    )
    try:
        document = json.loads(envelope["output"])
    except (json.JSONDecodeError, TypeError):
        raise contract_error(
            502,
            "ai_assist_bad_output",
            "El asistente devolvió una respuesta inválida.",
        ) from None
    validated = _answer(document)
    return {
        "audit_id": envelope["audit_id"],
        "model": envelope["model"],
        "credits_debited": envelope["credits_debited"],
        **validated,
    }


__all__ = ["ask"]
