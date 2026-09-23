"""HTTP surface for the customer approval portal."""

from __future__ import annotations

from contextlib import contextmanager
import logging
from uuid import UUID

from django.db import DatabaseError
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.errors import contract_error
from documents.repository import DocumentaryError
from documents.views import ERRORS, documentary_scope, validate
from portal import service
from portal.serializers import (
    DecideRequestSerializer,
    PortalQuoteSerializer,
    ShareQuoteResponseSerializer,
)

logger = logging.getLogger(__name__)

_WRITERS = ("OWNER", "ESTIMATOR")


@contextmanager
def public_portal_errors():
    try:
        yield
    except DocumentaryError as error:
        if error.code in ("project_not_found", "version_not_found", "quote_not_found"):
            raise contract_error(404, error.code, "El enlace de cotización no existe.") from error
        if error.code == "quote_expired":
            raise contract_error(
                410, error.code, "Este enlace de cotización expiró; solicita uno nuevo."
            ) from error
        raise contract_error(
            422, error.code, "La acción sobre la cotización fue rechazada."
        ) from error
    except serializers.ValidationError as error:
        raise contract_error(
            400, "portal_payload_invalid", "Revisa la decisión ingresada."
        ) from error
    except DatabaseError as error:
        logger.warning("Portal transaction rejected (%s)", type(error).__name__)
        raise contract_error(
            409, "portal_transaction_rejected", "La operación fue rechazada por la base."
        ) from error


class ProjectQuoteLinkView(APIView):
    @extend_schema(
        operation_id="project_quote_link_create",
        description="Mint a customer-approval link for the latest sealed version.",
        request=None,
        responses={200: ShareQuoteResponseSerializer, **ERRORS},
    )
    def post(self, request, project_id: UUID):
        with public_portal_errors(), documentary_scope(request, _WRITERS) as (
            token,
            _,
            org_id,
        ):
            output = service.share_quote(
                org_id=org_id, project_id=project_id, actor_id=token.user_id
            )
            output["path"] = f"/cotizacion/{output['token']}"
            return Response(output)


class PortalQuoteView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="portal_quote_retrieve",
        description="Public quote summary behind a share token.",
        responses={200: PortalQuoteSerializer, **ERRORS},
    )
    def get(self, request, token: str):
        with public_portal_errors():
            return Response(service.portal_quote(token))


class PortalQuoteDecisionView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="portal_quote_decide",
        description="Customer approves or declines the shared quote.",
        request=DecideRequestSerializer,
        responses={200: PortalQuoteSerializer, **ERRORS},
    )
    def post(self, request, token: str):
        data = validate(DecideRequestSerializer, request.data)
        with public_portal_errors():
            output = service.decide_quote(
                token=token,
                decision=str(data["decision"]),
                decided_by=str(data["decided_by"]).strip(),
                note=str(data.get("note") or "").strip() or None,
            )
            return Response(output)
