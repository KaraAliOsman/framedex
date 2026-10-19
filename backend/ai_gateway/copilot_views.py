"""Dirección final 05 — HTTP edge for the global copilot: threads, timeline,
attachments and the single approval of a prepared set.

None of these endpoints calls the model: listing history, reopening a
thread, uploading or viewing a file are free. Continuing work goes through
the agent/messages endpoints under the current role, capability and budget.
"""

from __future__ import annotations

from uuid import UUID

from django.http import HttpResponse
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_gateway import attachments, jobs, threads
from ai_gateway.serializers import (
    AiAttachmentDetailSerializer,
    AiAttachmentListSerializer,
    AiAttachmentMatrixSerializer,
    AiAttachmentSerializer,
    AiAttachmentUploadSerializer,
    AiJobDetailSerializer,
    AiThreadCreateSerializer,
    AiThreadListSerializer,
    AiThreadQuerySerializer,
    AiThreadSerializer,
    AiThreadUpdateSerializer,
    AiTimelineSerializer,
)
from authentication.errors import contract_error
from authentication.serializers import ACTIVE_ORGANIZATION_HEADER
from documents.views import ERRORS, documentary_scope, validate

_CALLERS = ("OWNER", "ESTIMATOR", "WORKSHOP_MANAGER")
_WRITERS = ("OWNER", "ESTIMATOR")


def _thread_error(error: threads.ThreadError):
    raise contract_error(404 if error.code == "ai_thread_not_found" else 400, error.code, error.detail) from None


def _attachment_error(error: attachments.AttachmentError):
    raise contract_error(error.status, error.code, error.detail) from None


class AiThreadCollectionView(APIView):
    @extend_schema(
        operation_id="ai_threads_list",
        parameters=[
            ACTIVE_ORGANIZATION_HEADER,
            OpenApiParameter("q", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
            OpenApiParameter("archived", OpenApiTypes.BOOL, OpenApiParameter.QUERY, required=False),
            OpenApiParameter("cursor", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
        ],
        responses={200: AiThreadListSerializer, **ERRORS},
        tags=["ai"],
    )
    def get(self, request):
        query = validate(AiThreadQuerySerializer, request.query_params.dict())
        with documentary_scope(request, _CALLERS) as (token, _, org_id):
            try:
                return Response(threads.list_threads(
                    org_id=org_id, user_id=token.user_id, query=query.get("q") or "",
                    archived=bool(query.get("archived")), cursor=query.get("cursor") or None,
                ))
            except threads.ThreadError as error:
                _thread_error(error)

    @extend_schema(
        operation_id="ai_threads_create",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=AiThreadCreateSerializer,
        responses={201: AiThreadSerializer, **ERRORS},
        tags=["ai"],
    )
    def post(self, request):
        data = validate(AiThreadCreateSerializer, request.data)
        with documentary_scope(request, _CALLERS) as (token, _, org_id):
            # «Nuevo» never deletes or archives the previous conversation.
            thread = threads.create(org_id=org_id, user_id=token.user_id, title=data.get("title") or "",
                                    interaction_mode=data["interaction_mode"], autonomy=data["autonomy"])
            return Response(thread, status=201)


class AiThreadView(APIView):
    @extend_schema(
        operation_id="ai_thread_get",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        responses={200: AiThreadSerializer, **ERRORS},
        tags=["ai"],
    )
    def get(self, request, thread_id: UUID):
        with documentary_scope(request, _CALLERS) as (token, _, org_id):
            try:
                return Response(threads.require(org_id=org_id, user_id=token.user_id, thread_id=thread_id))
            except threads.ThreadError as error:
                _thread_error(error)

    @extend_schema(
        operation_id="ai_thread_update",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=AiThreadUpdateSerializer,
        responses={200: AiThreadSerializer, **ERRORS},
        tags=["ai"],
    )
    def patch(self, request, thread_id: UUID):
        data = validate(AiThreadUpdateSerializer, request.data)
        with documentary_scope(request, _CALLERS) as (token, _, org_id):
            try:
                return Response(threads.update(org_id=org_id, user_id=token.user_id, thread_id=thread_id, **data))
            except threads.ThreadError as error:
                _thread_error(error)


class AiThreadTimelineView(APIView):
    @extend_schema(
        operation_id="ai_thread_timeline",
        parameters=[
            ACTIVE_ORGANIZATION_HEADER,
            OpenApiParameter("cursor", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
        ],
        responses={200: AiTimelineSerializer, **ERRORS},
        tags=["ai"],
    )
    def get(self, request, thread_id: UUID):
        cursor = str(request.query_params.get("cursor") or "")[:200] or None
        with documentary_scope(request, _CALLERS) as (token, _, org_id):
            try:
                return Response(threads.timeline(org_id=org_id, user_id=token.user_id, thread_id=thread_id,
                                                 cursor=cursor))
            except threads.ThreadError as error:
                _thread_error(error)


class AiThreadAttachmentsView(APIView):
    @extend_schema(
        operation_id="ai_thread_attachments",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        responses={200: AiAttachmentListSerializer, **ERRORS},
        tags=["ai"],
    )
    def get(self, request, thread_id: UUID):
        with documentary_scope(request, _CALLERS) as (token, _, org_id):
            try:
                threads.require(org_id=org_id, user_id=token.user_id, thread_id=thread_id)
            except threads.ThreadError as error:
                _thread_error(error)
            return Response({"items": attachments.list_for_thread(org_id=org_id, user_id=token.user_id,
                                                                  thread_id=thread_id)})


class AiAttachmentCollectionView(APIView):
    parser_classes = [MultiPartParser, JSONParser]

    @extend_schema(
        operation_id="ai_attachments_formats",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        responses={200: AiAttachmentMatrixSerializer, **ERRORS},
        tags=["ai"],
    )
    def get(self, request):
        with documentary_scope(request, _CALLERS):
            return Response(attachments.matrix())

    @extend_schema(
        operation_id="ai_attachments_upload",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request={"multipart/form-data": AiAttachmentUploadSerializer},
        responses={201: AiAttachmentSerializer, **ERRORS},
        tags=["ai"],
    )
    def post(self, request):
        data = validate(AiAttachmentUploadSerializer, request.data)
        upload = data["file"]
        with documentary_scope(request, _CALLERS) as (token, _, org_id):
            try:
                # Upload stores and extracts; it never calls the model.
                item = attachments.upload(
                    org_id=org_id, user_id=token.user_id, file_name=upload.name,
                    content=upload.read(attachments.MAX_FILE_BYTES + 1),
                    thread_id=data.get("thread_id"),
                )
            except attachments.AttachmentError as error:
                _attachment_error(error)
            except threads.ThreadError as error:
                _thread_error(error)
            return Response(item, status=201)


class AiAttachmentView(APIView):
    @extend_schema(
        operation_id="ai_attachment_get",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        responses={200: AiAttachmentDetailSerializer, **ERRORS},
        tags=["ai"],
    )
    def get(self, request, attachment_id: UUID):
        with documentary_scope(request, _CALLERS) as (token, _, org_id):
            try:
                return Response(attachments.detail(org_id=org_id, user_id=token.user_id,
                                                   attachment_id=attachment_id))
            except attachments.AttachmentError as error:
                _attachment_error(error)


class AiAttachmentContentView(APIView):
    @extend_schema(
        operation_id="ai_attachment_content",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        responses={200: {"type": "string", "format": "binary"}, **ERRORS},
        tags=["ai"],
    )
    def get(self, request, attachment_id: UUID):
        with documentary_scope(request, _CALLERS) as (token, _, org_id):
            try:
                raw, media_type, file_name = attachments.content(
                    org_id=org_id, user_id=token.user_id, attachment_id=attachment_id)
            except attachments.AttachmentError as error:
                _attachment_error(error)
        response = HttpResponse(raw, content_type=media_type)
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        safe = file_name.encode("ascii", "replace").decode("ascii").replace('"', "")
        # Never rendered inline as active content: documents download,
        # images/PDF are shown by the viewer from this private response.
        disposition = "inline" if media_type in ("application/pdf", "image/png", "image/jpeg", "image/webp") else "attachment"
        response["Content-Disposition"] = f'{disposition}; filename="{safe}"'
        return response


class AiJobApproveView(APIView):
    """«Con aprobación»: one approval applies the prepared coherent set of the
    latest round through the same idempotent project services the manual
    review uses. Each change keeps its undo. Consequential actions (emit,
    send, buy, release, pay, publish) are never part of this set.

    The quote step of flow A11 (price + «Borrador» PDF) runs after the
    positions, outside the job transaction and with the person's own session
    — price authority and owner MFA are the person's, never the worker's.
    «Omitir todo» continues the delegated chain through this same endpoint."""

    @extend_schema(
        operation_id="ai_job_approve",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=None,
        responses={200: AiJobDetailSerializer, **ERRORS},
        tags=["ai"],
    )
    def post(self, request, job_id: UUID):
        from ai_gateway import quote_flow
        from ai_gateway.agent import _apply_document_layout, _apply_reversible
        from ai_gateway.postconditions import refresh_receipt

        with documentary_scope(request, _WRITERS) as (token, _, org_id):
            job = jobs.get_job(org_id=org_id, user_id=token.user_id, job_id=job_id)
            if job is None:
                raise contract_error(404, "ai_job_not_found", "El trabajo no existe.")
            if job["state"] in ("QUEUED", "PLANNING", "RUNNING"):
                raise contract_error(409, "ai_job_running", "Espera a que termine la preparación.")
            transcript = list(job.get("transcript") or [])
            turn_index = next((index for index in range(len(transcript) - 1, -1, -1)
                               if isinstance(transcript[index], dict) and transcript[index].get("role") == "agent"), None)
            if turn_index is None:
                raise contract_error(409, "ai_job_nothing_to_approve", "No hay cambios preparados.")
            resolved = {
                (int(item.get("turn_index", -1)), int(item.get("step_index", -1)))
                for item in job.get("outcomes") or []
                if isinstance(item, dict) and item.get("action") in ("applied", "declined", "undone")
            }
            entries: list[dict] = []
            quotes: list[int] = []
            steps = list(transcript[turn_index].get("steps") or [])
            for index, step in enumerate(steps):
                if step.get("applied") or (turn_index, index) in resolved:
                    continue
                if step.get("kind") == "quote_draft":
                    quotes.append(index)
                    continue
                if step.get("kind") not in ("project_ops", "document_layout"):
                    continue
                try:
                    applied = (
                        _apply_document_layout(org_id, step) if step["kind"] == "document_layout"
                        else _apply_reversible(org_id, token.user_id, step, f"ai:{job_id}:{turn_index}:{index}")
                    )
                except Exception as error:  # noqa: BLE001 — a stale change stays visible with its cause
                    step["apply_error"] = str(getattr(error, "public_detail", None) or "La obra cambió; vuelve a preparar este cambio.")[:240]
                    entries.append({"turn_index": turn_index, "step_index": index, "action": "apply_failed",
                                    "ops": [], "recorded_by": "human"})
                    continue
                step["applied"] = applied
                entries.append({
                    "turn_index": turn_index, "step_index": index, "action": "applied", "recorded_by": "human",
                    "ops": ([str(op.get("op") if isinstance(op, dict) else op)[:80] for op in step.get("ops") or []][:200]
                            if step["kind"] == "project_ops" else ["document_layout"]),
                    **({"operation_id": applied["operation_id"]} if step["kind"] == "project_ops" else {}),
                })
            if not entries and not quotes:
                raise contract_error(409, "ai_job_nothing_to_approve", "No quedan cambios por aprobar.")
            transcript[turn_index] = {**transcript[turn_index], "steps": steps}
            if entries:
                jobs.store_approval(job_id=job_id, transcript=transcript, entries=entries)

        if quotes:
            failed_positions = any(entry["action"] == "apply_failed" for entry in entries)
            quote_entries: list[dict] = []
            for index in quotes:
                step = steps[index]
                result = (
                    {"status": "blocked", "cause": "Primero deben quedar guardadas las ventanas.", "operation_id": None, "pdf": False}
                    if failed_positions else quote_flow.prepare(request, UUID(str(step["project_id"])))
                )
                if result["status"] == "applied":
                    step["applied"] = {"pricing_operation_id": result["operation_id"], "pdf": True,
                                       "project_id": str(step["project_id"])}
                    step.pop("apply_error", None)
                    quote_entries.append({"turn_index": turn_index, "step_index": index, "action": "applied",
                                          "ops": ["quote_draft"], "recorded_by": "human"})
                else:
                    step["apply_error"] = result["cause"]
                    if result.get("operation_id"):
                        step["applied_price"] = result["operation_id"]
                    quote_entries.append({"turn_index": turn_index, "step_index": index, "action": "apply_failed",
                                          "ops": ["quote_draft"], "recorded_by": "human"})
            with documentary_scope(request, _WRITERS) as (token, _, org_id):
                transcript[turn_index] = {**transcript[turn_index], "steps": steps}
                jobs.store_approval(job_id=job_id, transcript=transcript, entries=quote_entries)

        with documentary_scope(request, _WRITERS) as (token, _, org_id):
            job = jobs.get_job(org_id=org_id, user_id=token.user_id, job_id=job_id)
            receipt = refresh_receipt(org_id=org_id, job=job)
            if receipt is not None:
                jobs.set_receipt(job_id=job_id, receipt=receipt)
            job = jobs.get_job(org_id=org_id, user_id=token.user_id, job_id=job_id)
            return Response(job)
