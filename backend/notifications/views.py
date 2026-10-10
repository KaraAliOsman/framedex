from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.errors import contract_error
from authentication.serializers import ACTIVE_ORGANIZATION_HEADER
from documents.views import ERRORS, documentary_scope, validate
from notifications import adapters, service, templates
from notifications.serializers import (
    MailExampleSerializer,
    MailIntegrationSerializer,
    MailPreviewSerializer,
    MailRecordSerializer,
    MailRecoverySerializer,
    MailSendSerializer,
)

READERS = ("OWNER", "ESTIMATOR", "WORKSHOP_MANAGER")
WRITERS = ("OWNER", "ESTIMATOR")


class MailIntegrationView(APIView):
    @extend_schema(
        operation_id="mail_integration_status",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        responses={200: MailIntegrationSerializer, **ERRORS},
    )
    def get(self, request):
        with documentary_scope(request, READERS):
            return Response(adapters.integration())


class MailListView(APIView):
    @extend_schema(
        operation_id="mail_list",
        parameters=[
            ACTIVE_ORGANIZATION_HEADER,
            OpenApiParameter("project_id", type={"type": "string", "format": "uuid"}),
        ],
        responses={200: MailRecordSerializer(many=True), **ERRORS},
    )
    def get(self, request):
        from uuid import UUID

        project_id = request.query_params.get("project_id")
        try:
            project_id = UUID(project_id) if project_id else None
        except ValueError:
            raise contract_error(
                400, "mail_filter_invalid", "La obra indicada no es válida."
            ) from None
        with documentary_scope(request, READERS) as (_, _, org_id):
            return Response(service.recent(org_id=org_id, project_id=project_id))


class QuoteMailView(APIView):
    @extend_schema(
        operation_id="quote_mail_preview",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        responses={200: MailPreviewSerializer, **ERRORS},
    )
    def get(self, request, project_id):
        with documentary_scope(request, WRITERS) as (_, _, org_id):
            return Response(
                service.preview(service.quote_source(org_id=org_id, project_id=project_id))
            )

    @extend_schema(
        operation_id="quote_mail_send",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=MailSendSerializer,
        responses={200: MailRecordSerializer, **ERRORS},
    )
    def post(self, request, project_id):
        data = validate(MailSendSerializer, request.data)
        with documentary_scope(request, WRITERS) as (token, tenant, org_id):
            return Response(
                service.send_quote(
                    org_id=org_id,
                    project_id=project_id,
                    actor_id=token.user_id,
                    role=tenant.active_organization.role,
                    data=data,
                )
            )


class PaymentMailView(APIView):
    @extend_schema(
        operation_id="payment_mail_preview",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        responses={200: MailPreviewSerializer, **ERRORS},
    )
    def get(self, request, project_id, payment_id):
        with documentary_scope(request, WRITERS) as (_, _, org_id):
            return Response(
                service.preview(
                    service.payment_source(
                        org_id=org_id, project_id=project_id, payment_id=payment_id
                    )
                )
            )

    @extend_schema(
        operation_id="payment_mail_send",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=MailSendSerializer,
        responses={200: MailRecordSerializer, **ERRORS},
    )
    def post(self, request, project_id, payment_id):
        data = validate(MailSendSerializer, request.data)
        with documentary_scope(request, WRITERS) as (token, _, org_id):
            return Response(
                service.send_payment(
                    org_id=org_id,
                    project_id=project_id,
                    payment_id=payment_id,
                    actor_id=token.user_id,
                    data=data,
                )
            )


class MailRecoverView(APIView):
    @extend_schema(
        operation_id="mail_recover",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=MailRecoverySerializer,
        responses={200: MailRecordSerializer, **ERRORS},
    )
    def post(self, request, mail_id):
        data = validate(MailRecoverySerializer, request.data)
        with documentary_scope(request, READERS) as (token, tenant, org_id):
            if tenant.active_organization.role == 'WORKSHOP_MANAGER':
                from documents.repository import documentary_backend,one
                with documentary_backend():
                    row=one('SELECT kind FROM mail_outbox WHERE org_id=%s AND id=%s',[org_id,mail_id],'mail_not_found')
                if row['kind'] != 'PURCHASE':
                    raise contract_error(403,'documentary_permission_denied','El taller puede recuperar solo correos de compras.')
            return Response(
                service.recover(
                    org_id=org_id,
                    mail_id=mail_id,
                    actor_id=token.user_id,
                    expected_attempt=data["expected_attempt"],
                )
            )


class MailExamplesView(APIView):
    @extend_schema(
        operation_id="mail_examples",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        responses={200: MailExampleSerializer(many=True), **ERRORS},
    )
    def get(self, request):
        if settings.PRODUCTION:
            raise contract_error(
                404, "mail_preview_disabled", "La vista de desarrollo no está disponible."
            )
        with documentary_scope(request, WRITERS) as (_, _, org_id):
            from projects.org_branding import branding_for_snapshot

            with service.documentary_backend():
                org = branding_for_snapshot(org_id=org_id)
            return Response(
                [
                    {
                        "kind": kind,
                        "html": templates.preview_html(
                            templates.render(
                                kind,
                                organization=org,
                                reference="Vista previa · sin envío",
                                body={
                                    "MAGIC_LINK": "Tu enlace permite entrar una sola vez. Si no lo solicitaste, ignora este correo.",
                                    "QUOTE": "Su cotización está disponible para revisión. El envío real incorpora el documento emitido y un enlace de acceso a su revisión.",
                                    "APPROVAL": "El cliente aprobó la cotización. Revisa la obra antes de liberar a producción.",
                                    "PAYMENT": "Su pago quedó registrado. El envío real conserva el importe del comprobante emitido; esta vista previa no contiene cifras de una operación.",
                                    "ORDER_BLOCKED": "La orden quedó bloqueada. Revisa la causa registrada antes de continuar el trabajo.",
                                }[kind],
                                action_url=f"{settings.DEKOPEN_PUBLIC_APP_URL}/login"
                                if kind == "MAGIC_LINK"
                                else None,
                                logo=service._logo(org) if kind in {"QUOTE", "PAYMENT"} else None,
                            )
                        ),
                    }
                    for kind in templates.KINDS
                ]
            )
