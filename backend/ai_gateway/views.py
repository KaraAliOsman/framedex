"""AI gateway HTTP edge — the only entry point for provider calls (PRD-13)."""

from __future__ import annotations

from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_gateway import service
from ai_gateway import jobs
from ai_gateway.metrics import ai_metrics
from ai_gateway.agent import act
from ai_gateway.assist import ask
from ai_gateway.context import _ContextError
from ai_gateway.providers import ProviderError
from ai_gateway.serializers import (
    AiAgentRequestSerializer,
    AiAgentResponseSerializer,
    AiAskRequestSerializer,
    AiAskResponseSerializer,
    AiInvokeRequestSerializer,
    AiInvokeResponseSerializer,
    AiJobDetailSerializer,
    AiJobMessageSerializer,
    AiJobOutcomeResponseSerializer,
    AiJobOutcomeSerializer,
    AiJobSerializer,
    AiMetricsSerializer,
)
from ai_gateway.context import REQUIRED_REFS as AGENT_REQUIRED_REFS
from authentication.errors import ContractAPIException, contract_error
from authentication.serializers import ACTIVE_ORGANIZATION_HEADER
from documents.views import ERRORS, documentary_scope, validate

# Ask and invoke answer inside the caller's RLS projection exactly like the
# agent loop — a workshop manager who may run the agent must also be able to
# ask, or the two AI surfaces contradict each other (review WM6).
_AGENT_CALLERS = ("OWNER", "ESTIMATOR", "WORKSHOP_MANAGER")
_CALLERS = _AGENT_CALLERS
# Generic invoke exists for the member-facing raw capabilities only. Every
# richer capability has its own validated endpoint — letting a caller pick
# 'agent'/'catalog_compile' here would bypass context builders and output
# validation while spending org credits.
_MEMBER_CAPABILITIES = frozenset({"nlp_command", "discount_suggest"})


def _record_failure(request, *, goal, job_id, error, surface=None, refs=None,
                    transcript_before=None):
    """§07-B — the round's rollback undid every job write; a fresh RLS scope
    writes FAILED_RETRYABLE so the workspace can show and resume the failed
    job instead of losing it silently."""
    code = str(
        getattr(error, "contract_code", None)
        or getattr(error, "code", None)
        or "ai_job_failed"
    )[:120]
    try:
        with documentary_scope(request, _AGENT_CALLERS) as (token, _, org_id):
            if job_id is None:
                jobs.create_failed_job(
                    org_id=org_id,
                    user_id=token.user_id,
                    surface=surface,
                    refs=refs or {},
                    goal=goal,
                    error_code=code,
                )
            else:
                jobs.record_failure(
                    job_id=job_id,
                    transcript_before=list(transcript_before or []),
                    goal=goal,
                    error_code=code,
                )
    except Exception:  # failure bookkeeping must never mask the real error
        pass


def _raise_agent_error(error: Exception):
    if isinstance(error, _ContextError):
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
    if isinstance(error, ProviderError):
        raise contract_error(
            503,
            error.code,
            "El proveedor de IA no está disponible en este momento.",
        ) from None
    if isinstance(error, ValueError) and str(error) == "ai_job_terminal":
        raise contract_error(
            409, "ai_job_terminal", "El trabajo ya terminó."
        ) from None
    raise error


class AiInvokeView(APIView):
    @extend_schema(
        operation_id="ai_invoke",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=AiInvokeRequestSerializer,
        responses={200: AiInvokeResponseSerializer, **ERRORS},
        tags=["ai"],
    )
    def post(self, request):
        data = validate(AiInvokeRequestSerializer, request.data)
        if str(data["capability"]) not in _MEMBER_CAPABILITIES:
            raise contract_error(
                422,
                "ai_capability_forbidden",
                "Esa capacidad se usa desde su propia superficie.",
            )
        with documentary_scope(request, _CALLERS) as (token, _, org_id):
            try:
                return Response(
                    service.invoke(
                        org_id=org_id,
                        user_id=token.user_id,
                        capability=str(data["capability"]),
                        operation_key=str(data["operation_key"]),
                        input_payload=dict(data["input_payload"]),
                        # tool_name is audit attribution — the member cannot
                        # relabel a row as another tool (review AI-05).
                        tool_name=None,
                    )
                )
            except ProviderError as error:
                raise contract_error(
                    503,
                    error.code,
                    "El proveedor de IA no está disponible en este momento.",
                ) from None


class AiAskView(APIView):
    """Contextual "Preguntar a DEKOPEN" — the question and surface come from
    the client; every fact in the context is queried server-side under the
    caller's RLS. The provider answers inside that projection only."""

    @extend_schema(
        operation_id="ai_ask",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=AiAskRequestSerializer,
        responses={200: AiAskResponseSerializer, **ERRORS},
        tags=["ai"],
    )
    def post(self, request):
        data = validate(AiAskRequestSerializer, request.data)
        with documentary_scope(request, _CALLERS) as (token, _, org_id):
            try:
                return Response(
                    ask(
                        org_id=org_id,
                        user_id=token.user_id,
                        surface=str(data["surface"]),
                        refs=dict(data.get("refs") or {}),
                        question=str(data["question"]),
                        operation_key=str(data["operation_key"]),
                    )
                )
            except ProviderError as error:
                raise contract_error(
                    503,
                    error.code,
                    "El proveedor de IA no está disponible en este momento.",
                ) from None


class AiAgentView(APIView):
    """The agent surface: a goal becomes a bounded observe → plan → propose
    loop. Queries run server-side inside typed projections; every emitted
    step is validated before it reaches the client, and nothing consequential
    executes without the human clicking on the real surface."""

    @extend_schema(
        operation_id="ai_agent",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=AiAgentRequestSerializer,
        responses={200: AiAgentResponseSerializer, **ERRORS},
        tags=["ai"],
    )
    def post(self, request):
        data = validate(AiAgentRequestSerializer, request.data)
        surface = str(data["surface"])
        refs = dict(data.get("refs") or {})
        # The agent only reads projections and proposes steps — the workshop
        # manager's surface needs it as much as the estimator's. Errors must
        # unwind the request transaction BEFORE failure bookkeeping: catching
        # inside the scope would commit the doomed RUNNING job and strand it.
        executing = False
        try:
            with documentary_scope(request, _AGENT_CALLERS) as (token, _, org_id):
                missing_refs = [
                    name
                    for name in AGENT_REQUIRED_REFS.get(surface, ())
                    if name not in refs
                ]
                if missing_refs:
                    raise contract_error(
                        400,
                        "ai_context_ref_required",
                        f"Esta superficie requiere la referencia '{missing_refs[0]}'.",
                    )
                executing = True
                return Response(
                    act(
                        org_id=org_id,
                        user_id=token.user_id,
                        surface=surface,
                        refs=refs,
                        goal=str(data["goal"]),
                        product=data.get("product"),
                        history=list(data.get("history") or []),
                        operation_key=str(data["operation_key"]),
                    )
                )
        except ContractAPIException as failure:
            # Contract errors raised inside act() are execution failures —
            # the job must still surface as FAILED_RETRYABLE; validation,
            # authorization and missing-ref errors before execution never
            # reach the job and only propagate.
            if executing:
                _record_failure(
                    request,
                    goal=str(data["goal"]),
                    job_id=None,
                    surface=surface,
                    refs=refs,
                    error=failure,
                )
            raise
        except Exception as failure:
            _record_failure(
                request,
                goal=str(data["goal"]),
                job_id=None,
                surface=surface,
                refs=refs,
                error=failure,
            )
            _raise_agent_error(failure)


class AiJobCollectionView(APIView):
    """The caller's recent AI jobs — the workspace's left rail."""

    @extend_schema(
        operation_id="ai_job_list",
        parameters=[
            OpenApiParameter(
                "before", OpenApiTypes.DATETIME, OpenApiParameter.QUERY,
                description="Cursor: return jobs created before this timestamp "
                "(the last row's created_at) — older pages of the job rail.",
            ),
            OpenApiParameter(
                "before_id", OpenApiTypes.UUID, OpenApiParameter.QUERY,
                description="Tie-breaker: the last row's id — jobs sharing the "
                "cursor's timestamp paginate by id so nothing falls between pages.",
            ),
        ],
        responses={200: AiJobSerializer(many=True), **ERRORS},
        tags=["ai"],
    )
    def get(self, request):
        with documentary_scope(request, _AGENT_CALLERS) as (token, _, org_id):
            return Response(
                jobs.list_jobs(
                    org_id=org_id,
                    user_id=token.user_id,
                    before=request.query_params.get("before"),
                    before_id=request.query_params.get("before_id"),
                )
            )


class AiJobView(APIView):
    """One job with its full transcript; DELETE cancels a live run."""

    @extend_schema(
        operation_id="ai_job_retrieve",
        responses={200: AiJobDetailSerializer, **ERRORS},
        tags=["ai"],
    )
    def get(self, request, job_id):
        with documentary_scope(request, _AGENT_CALLERS) as (token, _, org_id):
            job = jobs.get_job(
                org_id=org_id, user_id=token.user_id, job_id=job_id
            )
            if job is None:
                raise contract_error(
                    404, "ai_job_not_found", "El trabajo no existe."
                )
            return Response(job)

    @extend_schema(
        operation_id="ai_job_cancel",
        responses={200: AiJobSerializer, **ERRORS},
        tags=["ai"],
    )
    def delete(self, request, job_id):
        with documentary_scope(request, _AGENT_CALLERS) as (token, _, org_id):
            job = jobs.get_job(
                org_id=org_id, user_id=token.user_id, job_id=job_id
            )
            if job is None:
                raise contract_error(
                    404, "ai_job_not_found", "El trabajo no existe."
                )
            if not jobs.cancel_job(job_id=job_id):
                raise contract_error(
                    409, "ai_job_terminal", "El trabajo ya terminó."
                )
            return Response(
                jobs.get_job(
                    org_id=org_id, user_id=token.user_id, job_id=job_id
                )
            )


class AiJobMessagesView(APIView):
    """§07-B follow-up instructions: appends a user turn and runs the agent
    again inside the same job — transcript, plan and artifacts keep
    accumulating; the earlier result is never deleted."""

    @extend_schema(
        operation_id="ai_job_message_create",
        request=AiJobMessageSerializer,
        responses={200: AiAgentResponseSerializer, **ERRORS},
        tags=["ai"],
    )
    def post(self, request, job_id):
        data = validate(AiJobMessageSerializer, request.data)
        # Errors must unwind the request transaction BEFORE failure
        # bookkeeping — a caught-in-scope exception would commit the resumed
        # RUNNING state and the failed turn would append twice.
        executing = False
        try:
            with documentary_scope(request, _AGENT_CALLERS) as (token, _, org_id):
                job = jobs.get_job(
                    org_id=org_id, user_id=token.user_id, job_id=job_id
                )
                if job is None:
                    raise contract_error(
                        404, "ai_job_not_found", "El trabajo no existe."
                    )
                if job["state"] == "CANCELED":
                    raise contract_error(
                        409, "ai_job_terminal", "El trabajo está cancelado."
                    )
                history = [
                    {
                        "role": turn.get("role"),
                        "text": turn.get("text") or turn.get("reply") or "",
                    }
                    for turn in job.get("transcript") or []
                    if isinstance(turn, dict)
                ]
                try:
                    jobs.resume_job(
                        job_id=job_id,
                        transcript=list(job.get("transcript") or []),
                    )
                except ValueError as error:
                    if str(error) == "ai_job_terminal":
                        raise contract_error(
                            409, "ai_job_terminal", "El trabajo ya terminó."
                        ) from None
                    raise contract_error(
                        409,
                        "ai_job_running",
                        "Ya hay una instrucción en curso en este trabajo.",
                    ) from None
                # The product rides with each message — the client sends the
                # position's live representation, so design ops evaluate the
                # current design, never a snapshot stored at job creation.
                executing = True
                return Response(
                    act(
                        org_id=org_id,
                        user_id=token.user_id,
                        surface=str(job["surface"]),
                        refs=dict(job.get("refs") or {}),
                        goal=str(data["message"]),
                        product=data.get("product"),
                        history=history,
                        operation_key=str(
                            request.headers.get("X-Operation-Key")
                            or f"{job_id}:{len(history)}"
                        ),
                        job=job,
                    )
                )
        except ContractAPIException as failure:
            # Only a round that actually claimed the job records failure —
            # errors before the claim (404, conflicts, validation) leave the
            # job untouched.
            if executing:
                _record_failure(
                    request,
                    goal=str(data["message"]),
                    job_id=job_id,
                    error=failure,
                    transcript_before=job.get("transcript"),
                )
            raise
        except Exception as failure:
            # The rollback restored the job's pre-resume state — the failed
            # turn appends exactly once here, marked FAILED_RETRYABLE, and
            # only if the row still carries the generation we claimed.
            _record_failure(
                request,
                goal=str(data["message"]),
                job_id=job_id,
                error=failure,
                transcript_before=job.get("transcript") if executing else None,
            )
            _raise_agent_error(failure)


class AiJobOutcomeView(APIView):
    """§08 measurement — the client reports what the human did with a
    proposed step. Idempotent: a retried report dedupes on
    (turn, step, action) and answers 200 with recorded=false instead of
    double-counting."""

    @extend_schema(
        operation_id="ai_job_outcome_create",
        request=AiJobOutcomeSerializer,
        responses={200: AiJobOutcomeResponseSerializer, **ERRORS},
        tags=["ai"],
    )
    def post(self, request, job_id):
        data = validate(AiJobOutcomeSerializer, request.data)
        with documentary_scope(request, _AGENT_CALLERS) as (token, _, org_id):
            job = jobs.get_job(
                org_id=org_id, user_id=token.user_id, job_id=job_id
            )
            if job is None:
                raise contract_error(
                    404, "ai_job_not_found", "El trabajo no existe."
                )
            result = jobs.record_outcome(
                org_id=org_id,
                user_id=token.user_id,
                job_id=job_id,
                entry=data,
            )
            return Response(result)


class AiMetricsView(APIView):
    """§08 measurement — org-level AI metrics over the trailing window."""

    @extend_schema(
        operation_id="ai_metrics",
        parameters=[
            ACTIVE_ORGANIZATION_HEADER,
            OpenApiParameter(
                "days", OpenApiTypes.INT, location=OpenApiParameter.QUERY
            ),
        ],
        responses={200: AiMetricsSerializer, **ERRORS},
        tags=["ai"],
    )
    def get(self, request):
        try:
            days = int(request.query_params.get("days") or 30)
        except (TypeError, ValueError):
            raise contract_error(
                400, "ai_metrics_days_invalid", "El período no es válido."
            ) from None
        if not 1 <= days <= 365:
            raise contract_error(
                400, "ai_metrics_days_invalid", "El período no es válido."
            )
        with documentary_scope(request, _AGENT_CALLERS) as (_, _, org_id):
            return Response(ai_metrics(org_id=org_id, days=days))
