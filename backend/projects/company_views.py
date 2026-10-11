"""Company sections and invitation acceptance use explicit typed commands."""

from contextlib import contextmanager

from django.db import DatabaseError
from django.http import HttpResponse
from drf_spectacular.utils import extend_schema, OpenApiTypes
from rest_framework import serializers
from rest_framework.views import APIView

from authentication.errors import contract_error
from authentication.rls import authenticated_rls_context
from authentication.views import verified_request_token
from pricing.serializers import StrictSerializer
from pricing.views import (
    DecimalJSONParser,
    ERRORS,
    scope as pricing_scope,
    validate,
    public_pricing_errors,
)
from projects import company
from projects.serializers import OrgBrandingWriteSerializer
from projects.views import SCHEMA, response
from documents.views import public_documentary_errors

ROLES = ("OWNER", "ESTIMATOR", "WORKSHOP_MANAGER", "OPERATOR", "INSTALLER")

COMPANY_ERRORS = {
    "company_invitation_key_conflict": (
        409,
        "Esta confirmación ya se usó para otra invitación. Recarga antes de preparar un nuevo envío.",
    ),
    "company_last_owner": (409, "Conserva al menos un dueño activo antes de cambiar este acceso."),
    "company_stale_edit": (409, "Otra persona cambió la empresa. Recarga antes de guardar."),
    "company_user_stale": (
        409,
        "Otro administrador cambió el acceso. Recarga antes de reemplazarlo.",
    ),
    "company_rut_invalid": (400, "Revisa el RUT legal y su dígito verificador."),
    "company_invitation_pending": (
        409,
        "Ya hay una invitación pendiente para este correo. Revisa su estado o revócala antes de crear otra.",
    ),
    "company_user_already_active": (409, "Este correo ya tiene acceso activo a la empresa."),
    "company_invitation_mfa_required": (
        403,
        "La empresa o el rol exige segundo factor. Configúralo y vuelve a aceptar.",
    ),
    "company_invitation_membership_exists": (
        409,
        "Este usuario ya tiene un acceso registrado. El dueño debe revisar o reactivar su membresía.",
    ),
    "company_invitation_not_available": (
        404,
        "La invitación venció o fue revocada. Pide un nuevo enlace al dueño.",
    ),
    "company_invitation_not_pending": (
        409,
        "La invitación ya cambió de estado. Actualiza la lista antes de revocarla.",
    ),
}


@contextmanager
def company_errors():
    try:
        yield
    except DatabaseError as error:
        code = getattr(getattr(error.__cause__, "diag", None), "message_primary", "")
        if code not in COMPANY_ERRORS:
            raise
        status, detail = COMPANY_ERRORS[code]
        raise contract_error(status, code, detail) from error


@contextmanager
def scope(request, allowed=("OWNER",)):
    with pricing_scope(request, allowed) as context, company_errors():
        yield context


class CompanySerializer(serializers.Serializer):
    name = serializers.CharField()
    tax_id = serializers.CharField()
    currency = serializers.ChoiceField(choices=("CLP", "USD"))
    base_currency = serializers.ChoiceField(choices=("CLP", "USD"), read_only=True)
    require_mfa = serializers.BooleanField()
    updated_at = serializers.DateTimeField()


class CompanyWriteSerializer(StrictSerializer):
    name = serializers.CharField(max_length=255)
    tax_id = serializers.CharField(max_length=50)
    currency = serializers.ChoiceField(choices=("CLP", "USD"))
    require_mfa = serializers.BooleanField()
    expected_updated_at = serializers.DateTimeField()


class CompanyUserSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    email = serializers.CharField()
    role = serializers.ChoiceField(choices=ROLES)
    is_active = serializers.BooleanField()
    updated_at = serializers.DateTimeField()


class CompanyUserWriteSerializer(StrictSerializer):
    role = serializers.ChoiceField(choices=ROLES)
    is_active = serializers.BooleanField()
    expected_updated_at = serializers.DateTimeField()


class InvitationSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=ROLES)
    created_at = serializers.DateTimeField()
    expires_at = serializers.DateTimeField()
    accepted_at = serializers.DateTimeField(allow_null=True)
    revoked_at = serializers.DateTimeField(allow_null=True)
    mail_id = serializers.UUIDField(allow_null=True)


class CompanyUsersSerializer(serializers.Serializer):
    items = CompanyUserSerializer(many=True)
    invitations = InvitationSerializer(many=True)


class InvitationWriteSerializer(StrictSerializer):
    operation_key = serializers.UUIDField()
    email = serializers.EmailField(max_length=255)
    role = serializers.ChoiceField(choices=ROLES)
    confirmed = serializers.BooleanField()

    def validate_confirmed(self, value):
        if not value:
            raise serializers.ValidationError("Confirma el correo y rol antes de invitar.")
        return value


class InvitationTokenSerializer(StrictSerializer):
    token = serializers.RegexField(r"^[A-Za-z0-9_-]{40,100}$", write_only=True)


class InvitationInspectSerializer(serializers.Serializer):
    organization_name = serializers.CharField()
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=ROLES)
    expires_at = serializers.DateTimeField()
    accepted = serializers.BooleanField(allow_null=True)


class InvitationAcceptedSerializer(serializers.Serializer):
    organization_id = serializers.UUIDField()


class NumberingSerializer(serializers.Serializer):
    prefix = serializers.CharField()
    next_number = serializers.IntegerField()


class NumberingListSerializer(serializers.Serializer):
    items = NumberingSerializer(many=True)


class CompanyPreviewSerializer(StrictSerializer):
    version_id = serializers.UUIDField()
    branding = OrgBrandingWriteSerializer(required=False)


class CompanyView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(
        operation_id="company_get", responses={200: CompanySerializer, **ERRORS}, **SCHEMA
    )
    def get(self, request):
        with scope(request, ROLES) as (_, _, org):
            return response(company.get_company(org))

    @extend_schema(
        operation_id="company_save",
        request=CompanyWriteSerializer,
        responses={200: CompanySerializer, **ERRORS},
        **SCHEMA,
    )
    def put(self, request):
        data = validate(CompanyWriteSerializer, request.data)
        with scope(request) as (_, _, org):
            return response(company.save_company(org, data))


class CompanyUsersView(APIView):
    @extend_schema(
        operation_id="company_users", responses={200: CompanyUsersSerializer, **ERRORS}, **SCHEMA
    )
    def get(self, request):
        with scope(request) as (_, _, org):
            return response(company.users(org))


class CompanyUserView(APIView):
    @extend_schema(
        operation_id="company_user_update",
        request=CompanyUserWriteSerializer,
        responses={200: CompanyUsersSerializer, **ERRORS},
        **SCHEMA,
    )
    def put(self, request, identity):
        data = validate(CompanyUserWriteSerializer, request.data)
        with scope(request) as (_, _, org):
            return response(company.change_user(org, identity, data))


class CompanyInvitationsView(APIView):
    @extend_schema(
        operation_id="company_invite",
        request=InvitationWriteSerializer,
        responses={201: CompanyUsersSerializer, **ERRORS},
        **SCHEMA,
    )
    def post(self, request):
        data = validate(InvitationWriteSerializer, request.data)
        with scope(request) as (token, _, org):
            return response(company.invite(org, token.user_id, data), status=201)


class CompanyInvitationView(APIView):
    @extend_schema(
        operation_id="company_invitation_revoke",
        responses={200: CompanyUsersSerializer, **ERRORS},
        **SCHEMA,
    )
    def delete(self, request, identity):
        with scope(request) as (_, _, org):
            return response(company.revoke_invitation(org, identity))


class InvitationInspectView(APIView):
    @extend_schema(
        operation_id="invitation_inspect",
        request=InvitationTokenSerializer,
        responses={200: InvitationInspectSerializer, **ERRORS},
        tags=["auth"],
    )
    def post(self, request):
        data = validate(InvitationTokenSerializer, request.data)
        token = verified_request_token(request)
        with public_pricing_errors(), authenticated_rls_context(token.claims), company_errors():
            return response(company.invitation(data["token"]))


class InvitationAcceptView(APIView):
    @extend_schema(
        operation_id="invitation_accept",
        request=InvitationTokenSerializer,
        responses={200: InvitationAcceptedSerializer, **ERRORS},
        tags=["auth"],
    )
    def post(self, request):
        data = validate(InvitationTokenSerializer, request.data)
        token = verified_request_token(request)
        with public_pricing_errors(), authenticated_rls_context(token.claims), company_errors():
            return response(company.accept_invitation(data["token"]))


class CompanyNumberingView(APIView):
    @extend_schema(
        operation_id="company_numbering",
        responses={200: NumberingListSerializer, **ERRORS},
        **SCHEMA,
    )
    def get(self, request):
        with scope(request, ROLES) as (_, _, org):
            return response(
                {"items": company.rows("SELECT * FROM private.company_numbering(%s)", [org])}
            )


class CompanyPreviewView(APIView):
    @extend_schema(
        operation_id="company_document_preview",
        request=CompanyPreviewSerializer,
        responses={200: OpenApiTypes.BINARY, **ERRORS},
        **SCHEMA,
    )
    def post(self, request):
        data = validate(CompanyPreviewSerializer, request.data)
        with public_documentary_errors(), scope(request, ("OWNER", "ESTIMATOR")) as (_, _, org):
            result = HttpResponse(company.preview(org, data), content_type="application/pdf")
            result["Cache-Control"] = "private, no-store"
            result["Content-Disposition"] = 'inline; filename="vista-previa.pdf"'
            return result
