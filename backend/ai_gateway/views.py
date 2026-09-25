"""AI gateway HTTP edge — the only entry point for provider calls (PRD-13)."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_gateway import service
from ai_gateway import jobs
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
    AiJobSerializer,
)
from ai_gateway.context import REQUIRED_REFS as AGENT_REQUIRED_REFS
from authentication.errors import ContractAPIException, contract_error
from authentication.serializers import ACTIVE_ORGANIZATION_HEADER
from documents.views import ERRORS, documentary_scope, validate

_CALLERS = ("OWNER", "ESTIMATOR")
_AGENT_CALLERS = ("OWNER", "ESTIMATOR", "WORKSHOP_MANAGER")


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
        with documentary_scope(request, _CALLERS) as (token, _, org_id):
            try:
                return Response(
                    service.invoke(
                        org_id=org_id,
                        user_id=token.user_id,
                        capability=str(data["capability"]),
                        operation_key=str(data["operation_key"]),
                        input_payload=dict(data["input_payload"]),
                        tool_name=str(data.get("tool_name") or "") or None,
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
        responses={200: AiJobSerializer(many=True), **ERRORS},
        tags=["ai"],
    )
    def get(self, request):
        with documentary_scope(request, _AGENT_CALLERS) as (token, _, org_id):
            return Response(
                jobs.list_jobs(org_id=org_id, user_id=token.user_id)
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
