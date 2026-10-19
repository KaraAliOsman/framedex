"""Company sections and invitation acceptance use explicit typed commands."""

from contextlib import contextmanager

from django.db import DatabaseError
from django.http import HttpResponse
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
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
from projects import company, design_defaults, finish_references, materials
from projects.serializers import DesignDefaultsSerializer, OrgBrandingWriteSerializer
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


class CompanyDesignDefaultsWriteSerializer(StrictSerializer):
    values = DesignDefaultsSerializer()


class CompanyDesignDefaultsSerializer(serializers.Serializer):
    values = DesignDefaultsSerializer()
    updated_at = serializers.DateTimeField(required=False, allow_null=True)


class CompanyDesignDefaultsView(APIView):
    """Usual series, finish and glass that seed new windows (company level)."""

    parser_classes = [DecimalJSONParser]

    @extend_schema(
        operation_id="company_design_defaults",
        responses={200: CompanyDesignDefaultsSerializer, **ERRORS},
        **SCHEMA,
    )
    def get(self, request):
        with scope(request, ("OWNER", "ESTIMATOR", "WORKSHOP_MANAGER")) as (_, _, org):
            return response(design_defaults.company_defaults(org))

    @extend_schema(
        operation_id="company_design_defaults_save",
        request=CompanyDesignDefaultsWriteSerializer,
        responses={200: CompanyDesignDefaultsSerializer, **ERRORS},
        **SCHEMA,
    )
    def put(self, request):
        data = validate(CompanyDesignDefaultsWriteSerializer, request.data)
        with scope(request, ("OWNER", "ESTIMATOR")) as (_, _, org):
            return response(design_defaults.save_company_defaults(org, data))


class FinishReferenceSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    finish_code = serializers.CharField()
    original_type = serializers.CharField()
    tile_mm = serializers.CharField()
    grain = serializers.ChoiceField(choices=["ALONG", "ACROSS", "NONE"])
    version = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class FinishReferenceListSerializer(serializers.Serializer):
    items = FinishReferenceSerializer(many=True)


class FinishReferenceUpdateSerializer(StrictSerializer):
    name = serializers.CharField(required=False, max_length=120)
    tile_mm = serializers.CharField(required=False, max_length=12)
    grain = serializers.ChoiceField(required=False, choices=["ALONG", "ACROSS", "NONE"])


_UPLOAD_FIELDS = {
    "file": {"type": "string", "format": "binary"},
    "name": {"type": "string"},
    "finish_code": {"type": "string"},
    "tile_mm": {"type": "string"},
    "grain": {"type": "string", "enum": ["ALONG", "ACROSS", "NONE"]},
    "x": {"type": "string"},
    "y": {"type": "string"},
    "size": {"type": "string"},
}


class FinishReferencesView(APIView):
    """Private library of the company's own material samples."""

    @extend_schema(
        operation_id="finish_references_list",
        responses={200: FinishReferenceListSerializer, **ERRORS},
        **SCHEMA,
    )
    def get(self, request):
        with scope(request, ("OWNER", "ESTIMATOR", "WORKSHOP_MANAGER")) as (_, _, org):
            return response(finish_references.list_references(org))

    @extend_schema(
        operation_id="finish_references_create",
        request={"multipart/form-data": {"type": "object", "properties": _UPLOAD_FIELDS, "required": ["file", "name", "finish_code"]}},
        responses={201: FinishReferenceSerializer, **ERRORS},
        **SCHEMA,
    )
    def post(self, request):
        file_obj = request.FILES.get("file") if hasattr(request, "FILES") else None
        if file_obj is None:
            raise contract_error(400, "finish_reference_missing", "Adjunta una imagen PNG, JPEG o WebP.")
        if file_obj.size and file_obj.size > finish_references.MAX_UPLOAD_BYTES:
            raise contract_error(400, "finish_reference_size_invalid", "La imagen debe pesar hasta 8 MB.")
        content = file_obj.read()
        data = {key: request.data.get(key) for key in ("name", "finish_code", "tile_mm", "grain", "x", "y", "size")}
        with scope(request, ("OWNER", "ESTIMATOR")) as (token, _, org):
            return response(finish_references.create_reference(org, token.user_id, data, content), status=201)


class FinishReferenceView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(
        operation_id="finish_references_update",
        request=FinishReferenceUpdateSerializer,
        responses={200: FinishReferenceSerializer, **ERRORS},
        **SCHEMA,
    )
    def patch(self, request, reference_id):
        data = validate(FinishReferenceUpdateSerializer, request.data)
        with scope(request, ("OWNER", "ESTIMATOR")) as (_, _, org):
            return response(finish_references.update_reference(org, reference_id, data))

    @extend_schema(
        operation_id="finish_references_archive",
        responses={200: FinishReferenceListSerializer, **ERRORS},
        **SCHEMA,
    )
    def delete(self, request, reference_id):
        with scope(request, ("OWNER", "ESTIMATOR")) as (_, _, org):
            return response(finish_references.archive_reference(org, reference_id))


class FinishReferenceImageView(APIView):
    @extend_schema(
        operation_id="finish_references_image",
        responses={200: {"type": "string", "format": "binary"}, **ERRORS},
        **{
            **SCHEMA,
            "parameters": [
                *SCHEMA["parameters"],
                OpenApiParameter("variant", str, enum=["prepared", "original"], required=False),
            ],
        },
    )
    def get(self, request, reference_id):
        variant = "original" if request.query_params.get("variant") == "original" else "prepared"
        with scope(request, ("OWNER", "ESTIMATOR", "WORKSHOP_MANAGER")) as (_, _, org):
            content, content_type = finish_references.reference_image(org, reference_id, variant)
        return HttpResponse(content, content_type=content_type, headers={"Cache-Control": "private, max-age=600"})


class MaterialRowSerializer(serializers.Serializer):
    reference = serializers.CharField()
    name = serializers.CharField()
    finish = serializers.CharField(allow_null=True)
    unit = serializers.CharField()
    count = serializers.IntegerField()
    length_mm = serializers.CharField(allow_null=True)
    length_m = serializers.CharField(allow_null=True)
    area_m2 = serializers.CharField(allow_null=True)
    windows = serializers.ListField(child=serializers.CharField())


class MaterialGroupsSerializer(serializers.Serializer):
    profiles = MaterialRowSerializer(many=True)
    reinforcements = MaterialRowSerializer(many=True)
    glass = MaterialRowSerializer(many=True)
    hardware = MaterialRowSerializer(many=True)
    other = MaterialRowSerializer(many=True)


class WindowMaterialsSerializer(serializers.Serializer):
    position_id = serializers.UUIDField()
    label = serializers.CharField()
    quantity = serializers.IntegerField()
    materials = MaterialGroupsSerializer()


class MaterialsFreshnessSerializer(serializers.Serializer):
    latest_revision = serializers.CharField(allow_null=True)
    latest_version_id = serializers.UUIDField(required=False)
    design_changed = serializers.BooleanField()


class ProjectMaterialsSerializer(serializers.Serializer):
    consolidated = MaterialGroupsSerializer()
    windows = WindowMaterialsSerializer(many=True)
    freshness = MaterialsFreshnessSerializer()


class CutMissingSerializer(serializers.Serializer):
    cause = serializers.CharField()
    action = serializers.CharField()
    path = serializers.CharField()
    window = serializers.CharField(required=False)
    detail = serializers.CharField(required=False)


class CutProfileSerializer(serializers.Serializer):
    code = serializers.CharField()
    kerf_mm = serializers.CharField()
    head_trim_mm = serializers.CharField()
    tail_trim_mm = serializers.CharField()


class CutDraftSerializer(serializers.Serializer):
    state = serializers.ChoiceField(choices=["READY", "MISSING", "EMPTY"])
    missing = CutMissingSerializer(many=True)
    profile = CutProfileSerializer(required=False)
    stock_source = serializers.CharField(required=False)
    bars = serializers.ListField(child=serializers.DictField(), required=False)
    purchase = serializers.ListField(child=serializers.DictField(), required=False)
    unplaced = serializers.ListField(child=serializers.DictField(), required=False)
    metrics = serializers.DictField(required=False, allow_null=True)


MATERIAL_ROLES = ("OWNER", "ESTIMATOR", "WORKSHOP_MANAGER")


class ProjectMaterialsView(APIView):
    """What the work's saved design consumes, per window and consolidated."""

    @extend_schema(
        operation_id="project_materials",
        responses={200: ProjectMaterialsSerializer, **ERRORS},
        **SCHEMA,
    )
    def get(self, request, project_id):
        with scope(request, MATERIAL_ROLES) as (_, _, org):
            return response(materials.project_materials(org, project_id))


class ProjectCutDraftView(APIView):
    """Draft cut of the whole work with declared stock and cutting profile, or
    the exact missing authorities. Reading it never releases an order."""

    @extend_schema(
        operation_id="project_cut_draft",
        responses={200: CutDraftSerializer, **ERRORS},
        **SCHEMA,
    )
    def get(self, request, project_id):
        with scope(request, MATERIAL_ROLES) as (_, _, org):
            return response(materials.cut_draft(org, project_id))
