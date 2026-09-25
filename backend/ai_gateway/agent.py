"""The DEKOPEN agent: goal → server-side queries → validated step plan.

The loop is honest by construction: the provider may observe additional
surfaces only through the same typed projections a screen would use (query
steps are executed server-side and their results fed back), it may propose
navigation to entities those projections named, it may emit design ops only
through the design-assist validator, and it may prepare consequential actions
(emission, release, payment) only as deep links the human still clicks. It
can never write manufacturing truth, call a provider directly, or act on an
entity the context did not show it."""

from __future__ import annotations

import json
import re
from typing import Any
from uuid import UUID

from ai_gateway import jobs, service as gateway
from ai_gateway.assist import (
    _ALLOWED_PATHS,
    _PATH_UUID,
    _context_refs,
    _grounded,
    _grounding_values,
)
from ai_gateway.context import REQUIRED_REFS, _BUILDERS, _ContextError, build_context
from authentication.errors import contract_error
from projects import design_assist, service as projects_service

CAPABILITY = "agent"

# §07-D — canonical tool registry. Every step/query/artifact resolves to one
# named tool so the model, the transcript and the workspace share a single
# vocabulary. Mutations never execute here: ops/prepare only produce the
# preview a human confirms on the real surface.
QUERY_TOOLS = {
    "dashboard": "get_dashboard",
    "projects": "search_entities",
    "project": "get_project",
    "position": "get_position",
    "quotation": "get_quotation",
    "catalog": "get_catalog",
    "production": "get_production_state",
    "work_order": "get_work_order",
    "clients": "get_clients",
    "purchasing": "get_inventory_state",
    "settings": "get_settings",
}

PREPARE_TOOLS = {
    "emit_revision": "generate_document_preview",
    "release_work_order": "prepare_production_plan",
    "optimize_work_order": "prepare_production_plan",
    "register_payment": "prepare_payment",
    "upload_document": "generate_document_preview",
    "review_catalog": "create_catalog_candidates",
    "upload_certificate": "generate_document_preview",
}

ARTIFACT_TOOLS = {
    "product_draft": "create_product_draft",
    "quote_draft": "create_quote_draft",
    "catalog_candidates": "create_catalog_candidates",
    "purchase_plan": "prepare_purchase_plan",
    "production_plan": "prepare_production_plan",
    "message": "create_message_draft",
    "comparison": "create_comparison",
    "document_preview": "generate_document_preview",
}

MAX_GOAL = 2000
MAX_REPLY = 4000
MAX_STEPS = 8
MAX_QUERIES = 3
MAX_ROUNDS = 3  # invokes: goal → up to two observe-and-replan turns
MAX_LABEL = 80
MAX_WARNINGS = 8
MAX_WARNING = 240

# Consequential actions the agent may PREPARE as a card. Each action binds to
# the real route where the action lives — the human still confirms there; the
# agent never executes. {placeholder}s must be filled with a UUID a projection
# showed this turn; a path that doesn't match its action's template is dropped.
PREPARE_ROUTES: dict[str, tuple[str, tuple[str, ...]]] = {
    "emit_revision": ("/projects/{project_id}/pricing", ("project_id",)),
    "register_payment": ("/projects/{project_id}", ("project_id",)),
    "upload_document": ("/projects/{project_id}", ("project_id",)),
    "release_work_order": ("/production", ()),
    "optimize_work_order": ("/production", ()),
    "review_catalog": ("/catalogs/systems", ()),
    "upload_certificate": ("/settings/general", ()),
}

AGENT_SYSTEM = """Eres DEKOPEN Agente — el agente completo de una aplicación profesional de ventanas y puertas (español chileno).

Recibes un JSON con:
- "goal": lo que el usuario quiere lograr.
- "surface": la superficie donde está trabajando.
- "context": proyección tipada de los datos REALES de su organización — tu única fuente de verdad.
- "observations": resultados de las consultas que pediste en turnos anteriores de esta misma meta.
- "history": la conversación previa.
- "actions": los tipos de paso permitidos.
- "product": (solo en surface="position") el diseño en edición: modules[] y couplings[] con sus ids y medidas reales — son los refs válidos para "ops".

Respondes SOLO un JSON:
{
  "reply": "qué encontraste / qué hiciste / qué falta — breve y concreto en español",
  "steps": [pasos],
  "warnings": ["alertas reales que el contexto evidencia"]
}

Tipos de paso:
- {"kind":"query","surface":"projects|project|position|quotation|catalog|production|work_order|clients|purchasing|dashboard|settings","refs":{...}} — pide los datos de otra superficie; el servidor la ejecuta y el resultado vuelve a ti en la siguiente ronda. Úsalo SIEMPRE que la meta toque datos que el contexto no tiene. refs lleva los ids requeridos (project_id, position_id, work_order_id; system_id para profundizar en un sistema de catálogo) y solo puedes consultar ids que el contexto u observaciones anteriores te mostraron. Máximo 3 por ronda.
- {"kind":"navigate","path":"/ruta","label":"..."} — navegación dentro de la app. Todo UUID en el path debe venir del contexto o de una observación.
- {"kind":"ops","ops":[...],"label":"..."} — SOLO cuando el usuario está en una posición de diseño (surface="position" y el pedido trae "product"). Cada op usa EXACTAMENTE los campos del contrato — nunca "refs", "value" ni otros nombres:
  set_module_count {count} | add_unit {side:"left"|"right"} | remove_unit {module} | duplicate_module {module} | add_stacked_unit {module} | insert_module {coupling} | remove_coupling {coupling} | set_coupling_kind {coupling, kind:"INLINE|STACKED|TEE|CORNER"} | set_module_width {module, width_mm} | set_total_width {width_mm} | set_height {height_mm} | equalize_widths {} | equalize_angles {} | set_coupling_angle {coupling, angle_deg} | set_opening {module, opening:"FIXED|TURN_LEFT|TURN_RIGHT|TILT_TURN_LEFT|TILT_TURN_RIGHT|SLIDING_2L|AWNING|DOOR_ENTRY"} | set_glass {module, sku} | set_glass_thickness {module, mm} | set_panel {module, sku|null}
  "module"/"coupling" toman el "ref" (id) de product.modules[]/product.couplings[]; para una unidad creada por add_unit en la misma secuencia usa "added_m1"... ("added_c1"... para uniones nuevas). Las medidas solo pueden citar números de la meta.
- {"kind":"prepare","action":"emit_revision|release_work_order|optimize_work_order|register_payment|upload_document|review_catalog|upload_certificate","path":"/ruta","label":"..."} — prepara una acción consecuente; la persona la confirma en la superficie real. Nunca la ejecutes tú. El "path" DEBE seguir la plantilla de actions.prepare_routes[action] rellenando {id} con el UUID real de la entidad (uno que el contexto o las observaciones ya mostraron).

Reglas duras:
- Solo citas números (medidas, precios, cantidades, SKUs, ids) que estén literalmente en el contexto, las observaciones o la meta del usuario. Nada inventado.
- "query" es cómo miras: si la meta requiere datos que no ves, consulta antes de responder. Si tras dos rondas sigues sin el dato, dilo claramente.
- Los pasos se ejecutan en orden: tus "query" ya vienen resueltas; los "navigate"/"ops"/"prepare" la persona los confirma. Máximo 8 pasos en total.
- Meta ambigua → reply explicando lo que falta y cero pasos de mutación. Jamás adivines medidas, ids ni estados.
- Sin texto fuera del JSON."""


def _query_key(surface: str, refs: dict) -> str:
    """Dedupe identity for a query — (surface, refs), never the surface
    alone: comparing two projects needs `project` queried once per id."""
    normalized = ",".join(f"{key}={refs[key]}" for key in sorted(refs))
    return f"{surface}|{normalized}"


def _queries(
    *,
    org_id: UUID,
    document: Any,
    seen: set[str],
    observed: frozenset[str],
) -> tuple[list[dict], frozenset[str]]:
    """Execute the model's query steps — each is just another typed
    projection under the caller's RLS. Failed lookups return their error code
    as the observation: the model learns the entity doesn't exist for this
    caller instead of crashing the turn. Refs may only name entities an
    earlier projection actually returned — a hallucinated UUID is an error
    observation, not a fetch."""
    steps = document.get("steps") if isinstance(document, dict) else None
    observations: list[dict] = []
    refs_union: frozenset[str] = frozenset()
    for item in steps if isinstance(steps, list) else []:
        if len(observations) >= MAX_QUERIES:
            break
        if not isinstance(item, dict) or item.get("kind") != "query":
            continue
        surface = item.get("surface")
        refs = item.get("refs") or {}
        # Shape validation precedes _query_key — it assumes dict refs, so a
        # malformed value must be rejected before the key is computed.
        if (
            not isinstance(surface, str)
            or surface not in _BUILDERS
            or not isinstance(refs, dict)
            or not all(
                isinstance(key, str)
                and isinstance(value, (str, int))
                and not isinstance(value, bool)
                for key, value in refs.items()
            )
        ):
            continue
        if _query_key(surface, refs) in seen:
            continue
        seen.add(_query_key(surface, refs))
        needed = REQUIRED_REFS.get(surface, ())
        if any(name not in refs for name in needed):
            observations.append(
                {"surface": surface, "refs": refs, "error": "ai_context_ref_invalid"}
            )
            continue
        if not all(str(value) in observed for value in refs.values()):
            observations.append(
                {"surface": surface, "refs": refs, "error": "ai_context_ref_unobserved"}
            )
            continue
        try:
            context = build_context(org_id, surface, refs)
        except _ContextError as error:
            observations.append(
                {"surface": surface, "refs": refs, "error": error.code}
            )
            continue
        refs_union = refs_union | _context_refs(context)
        observations.append({"surface": surface, "refs": refs, "context": context})
    return observations, refs_union


def _prepare_path_valid(action: str, path: str) -> bool:
    """A prepare link must equal its action's route template — every
    {placeholder} filled by a real UUID — so "Ir a la cotización" can never
    resolve to /dashboard."""
    template = PREPARE_ROUTES.get(action)
    if template is None:
        return False
    pattern = re.escape(template[0])
    for name in template[1]:
        pattern = pattern.replace(rf"\{{{name}\}}", _PATH_UUID.pattern)
    return bool(re.fullmatch(pattern, path))


def _step_out(item: dict, *, context_refs: frozenset[str]) -> dict | None:
    """Navigate / prepare steps survive only when their path is allowlisted
    AND every UUID in it names an entity a projection actually returned."""
    kind = item.get("kind")
    label = str(item.get("label") or "").strip()[:MAX_LABEL]
    if kind not in ("navigate", "prepare"):
        return None
    path = item.get("path")
    if not isinstance(path, str) or not _ALLOWED_PATHS.match(path):
        return None
    if not all(ref in context_refs for ref in _PATH_UUID.findall(path)):
        return None
    if kind == "navigate":
        return {
            "kind": "navigate",
            "tool": "navigate",
            "path": path,
            "label": label or path,
        }
    action = item.get("action")
    if not isinstance(action, str) or not _prepare_path_valid(action, path):
        return None
    return {
        "kind": "prepare",
        "tool": PREPARE_TOOLS.get(action, "prepare_action"),
        "action": action,
        "path": path,
        "label": label or action,
    }


def _act(
    *,
    org_id: UUID,
    user_id: UUID,
    surface: str,
    refs: dict,
    goal: str,
    product: Any,
    history: list,
    operation_key: str,
) -> dict:
    context = build_context(org_id, surface, refs)
    contexts = [context]
    seen_queries = {_query_key(surface, refs)}
    observed_refs = _context_refs(context)
    observations: list[dict] = []
    all_observations: list[dict] = []
    debited = 0
    audit_id = ""
    model = ""
    document: Any = {}
    for round_index in range(MAX_ROUNDS):
        envelope = gateway.invoke(
            org_id=org_id,
            user_id=user_id,
            capability=CAPABILITY,
            # Each round is its own audited invocation — the suffix keeps
            # round keys distinct so a client retry replays every round
            # instead of the second call replaying the first's output.
            operation_key=f"{operation_key}:r{round_index}",
            tool_name="agent",
            provider_options={"system": AGENT_SYSTEM, "json_output": True},
            input_payload={
                "goal": goal,
                "surface": surface,
                "context": context,
                "observations": observations,
                "history": history,
                "actions": {
                    "query_surfaces": sorted(REQUIRED_REFS),
                    "prepare_actions": sorted(PREPARE_ROUTES),
                    "prepare_routes": {
                        action: route for action, (route, _params) in PREPARE_ROUTES.items()
                    },
                    "ops_available": surface == "position" and product is not None,
                },
                "product": product,
                "product_fields": (
                    "product.modules[].id|width_mm|height_mm|contour|frameless "
                    "y product.couplings[].id|angle_deg|kind|modules|edges"
                    if surface == "position" and product is not None
                    else None
                ),
            },
        )
        debited += int(envelope["credits_debited"])
        audit_id = envelope["audit_id"]
        model = envelope["model"]
        try:
            document = json.loads(envelope["output"])
        except (json.JSONDecodeError, TypeError):
            raise contract_error(
                502,
                "ai_agent_bad_output",
                "El agente devolvió una respuesta inválida.",
            ) from None
        if not isinstance(document, dict):
            raise contract_error(
                502,
                "ai_agent_bad_output",
                "El agente devolvió una respuesta inválida.",
            )
        observations, new_observed = _queries(
            org_id=org_id,
            document=document,
            seen=seen_queries,
            observed=observed_refs,
        )
        observed_refs = observed_refs | new_observed
        all_observations.extend(observations)
        contexts.extend(
            observation["context"]
            for observation in observations
            if isinstance(observation.get("context"), dict)
        )
        # Any observation — success or error — informs the next round; an
        # entity that doesn't exist for this caller is a finding the model
        # should report, not a reason to stop mid-thought.
        if not observations:
            break

    reply = document.get("reply") if isinstance(document.get("reply"), str) else ""
    reply = reply.strip()[:MAX_REPLY]
    if not reply:
        raise contract_error(
            502,
            "ai_agent_bad_output",
            "El agente devolvió una respuesta inválida.",
        )
    grounding = _grounding_values(
        {"context": context, "observations": all_observations}, goal
    )
    if not _grounded(reply, grounding):
        raise contract_error(
            502,
            "ai_agent_ungrounded",
            "El agente citó datos que no están en el contexto.",
        )
    warnings = [
        str(item).strip()[:MAX_WARNING]
        for item in (document.get("warnings") or [])
        if isinstance(item, str) and item.strip()
    ][:MAX_WARNINGS]

    context_refs = frozenset().union(*(_context_refs(c) for c in contexts))

    # Ops steps ride the design-assist contract: they only exist when the
    # caller is on a position surface with a live product, and they validate
    # against the position's own catalog authority — never a client field.
    summary = catalog = declared = None
    if surface == "position" and product is not None and "position_id" in refs:
        summary = design_assist._summary(product)
        if summary is not None:
            position = projects_service.position_row(org_id, refs["position_id"])
            catalog = design_assist._catalog(UUID(str(position["system_id"])), org_id)
            declared = design_assist._declared_values(goal)

    steps: list[dict] = []
    rejected: list[dict] = []
    for item in document.get("steps") or []:
        if len(steps) >= MAX_STEPS:
            break
        if not isinstance(item, dict):
            continue
        kind = item.get("kind")
        if kind == "query":
            continue  # executed above — `queries` reports them as provenance
        if kind == "ops":
            if summary is None or catalog is None or declared is None:
                continue
            ops, dropped = design_assist._validate_ops(
                item.get("ops"), summary, catalog, declared
            )
            rejected.extend(dropped)
            if ops:
                steps.append(
                    {
                        "kind": "ops",
                        "tool": "preview_commands",
                        "ops": ops,
                        "label": str(item.get("label") or "").strip()[:MAX_LABEL]
                        or "Cambios de diseño",
                    }
                )
            continue
        out = _step_out(item, context_refs=context_refs)
        if out is not None:
            steps.append(out)

    context_refs_all = context_refs

    raw_artifacts = [
        item.get("artifact")
        for item in (document.get("steps") or [])
        if isinstance(item, dict) and item.get("kind") == "artifact"
    ]
    validated_artifacts = [
        {**artifact, "tool": ARTIFACT_TOOLS.get(artifact.get("kind"), "create_draft")}
        for artifact in jobs.artifacts(raw_artifacts, context_refs_all)
    ]
    claims, references, dropped_claims = jobs.claims_and_references(
        document.get("claims"), context_refs_all
    )
    if dropped_claims:
        warnings.append(
            f"{dropped_claims} afirmación(es) sin evidencia en contexto descartada(s)"
        )
    model_refs = jobs._references(document.get("references"), context_refs_all)
    for ref in model_refs:
        if ref not in references:
            references.append(ref)
    plan = [
        {"label": str(item.get("label") or "").strip()[:200]}
        for item in (document.get("plan") or [])
        if isinstance(item, dict) and str(item.get("label") or "").strip()
    ][:6]
    questions = [
        str(item).strip()[:400]
        for item in (document.get("questions") or [])
        if isinstance(item, str) and item.strip()
    ][:3]

    return {
        "audit_id": audit_id,
        "model": model,
        "credits_debited": debited,
        "reply": reply,
        "plan": plan,
        "claims": claims,
        "references": references,
        "questions": questions,
        "artifacts": validated_artifacts,
        "steps": steps,
        "queries": [
            # The caller's own surface was already consulted — report it as
            # provenance even when the model never queried anything else.
            {
                "surface": surface,
                "tool": QUERY_TOOLS.get(surface, "get_context"),
                "status": "ok",
            },
            *[
                {
                    "surface": observation["surface"],
                    "tool": QUERY_TOOLS.get(observation["surface"], "get_context"),
                    "status": "ok" if "context" in observation else "error",
                }
                for observation in all_observations
            ],
        ],
        "warnings": warnings,
        "rejected": rejected,
    }


def act(
    *,
    org_id: UUID,
    user_id: UUID,
    surface: str,
    refs: dict,
    goal: str,
    product: Any,
    history: list,
    operation_key: str,
    job: dict | None = None,
) -> dict:
    """§07-B — every agent run is a durable job. The transcript carries the
    user's turn plus the model's grounded round; artifacts, claims and
    warnings land on the row so the workspace can inspect them after the
    conversation scrolls. On a failed round the exception propagates: the
    caller records FAILED_RETRYABLE after the request rolls back, so the
    failure itself survives the transaction."""
    job = job or jobs.create_job(
        org_id=org_id, user_id=user_id, surface=surface, refs=refs, goal=goal
    )
    transcript = list(job.get("transcript") or [])
    transcript.append({"role": "user", "text": goal[:MAX_GOAL]})
    result = _act(
        org_id=org_id,
        user_id=user_id,
        surface=surface,
        refs=refs,
        goal=goal,
        product=product,
        history=history,
        operation_key=operation_key,
    )

    has_actions = any(
        step.get("kind") in ("prepare", "ops") for step in result["steps"]
    )
    state = (
        "WAITING_FOR_USER"
        if result["questions"]
        else "WAITING_FOR_APPROVAL" if has_actions else "SUCCEEDED"
    )
    transcript.append(
        {
            "role": "agent",
            "reply": result["reply"],
            "plan": result["plan"],
            "queries": result["queries"],
            "claims": result["claims"],
            "references": result["references"],
            "questions": result["questions"],
            "artifacts": result["artifacts"],
            "steps": result["steps"],
            "warnings": result["warnings"],
        }
    )
    # The job's artifact shelf accumulates across rounds — a question-only
    # follow-up must not wipe drafts an earlier turn produced. Each turn's
    # own artifacts stay attributed in the transcript entry.
    artifacts = (
        list(job.get("artifacts") or []) + result["artifacts"]
    )[-jobs.MAX_ARTIFACTS_TOTAL:]
    jobs.finish_job(
        job_id=UUID(job["id"]),
        state=state,
        transcript=transcript,
        plan=result["plan"],
        artifacts=artifacts,
        warnings=result["warnings"],
        result=result,
    )
    result["job_id"] = job["id"]
    result["state"] = state
    result["transcript"] = transcript
    # The transcript entry above already captured this round's own list —
    # the response mirrors the accumulated shelf like the job row does.
    result["artifacts"] = artifacts
    return result
