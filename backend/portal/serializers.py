"""Contract serializers for the customer-approval portal."""

from decimal import Decimal

from rest_framework import serializers
from engine_api.finish_serializers import ResolvedFinishSerializer
from pricing.serializers import StrictSerializer
from projects.rut import valid_rut


class ShareQuoteResponseSerializer(serializers.Serializer):
    token = serializers.CharField()
    expires_at = serializers.DateTimeField()
    path = serializers.CharField()


class PortalOrganizationSerializer(serializers.Serializer):
    brand_schema = serializers.IntegerField(allow_null=True, required=False)
    brand_primary_color = serializers.CharField(required=False)
    portal_attribution = serializers.BooleanField(required=False)
    name = serializers.CharField(allow_null=True, allow_blank=True)
    tax_id = serializers.CharField(allow_null=True, allow_blank=True)
    commercial_name = serializers.CharField(allow_null=True, allow_blank=True)
    brand_address = serializers.CharField(allow_null=True, allow_blank=True)
    brand_phone = serializers.CharField(allow_null=True, allow_blank=True)
    brand_email = serializers.CharField(allow_null=True, allow_blank=True)
    brand_logo_url = serializers.CharField(allow_null=True, allow_blank=True)


class CommercialHardwareSerializer(serializers.Serializer):
    handle_name = serializers.CharField(allow_null=True)
    handle_color = serializers.CharField(allow_null=True)
    options = serializers.ListField(child=serializers.CharField())
    synthetic = serializers.BooleanField()


class PortalOpeningSerializer(serializers.Serializer):
    module_index = serializers.IntegerField()
    width_mm = serializers.CharField()
    height_mm = serializers.CharField()
    rule_name = serializers.CharField()
    synthetic = serializers.BooleanField()


class PortalPositionSerializer(serializers.Serializer):
    system_name = serializers.CharField(required=False)
    is_demo = serializers.BooleanField(required=False)
    unit_price_gross = serializers.CharField(allow_null=True, required=False)
    line_price_gross = serializers.CharField(allow_null=True, required=False)
    unit_rounding_adjustment = serializers.CharField(allow_null=True, required=False)
    opening_leaves = serializers.ListField(child=serializers.JSONField(), required=False)
    resolved_finish = ResolvedFinishSerializer(required=False, allow_null=True)
    id = serializers.CharField(allow_blank=True)
    position_index = serializers.IntegerField(allow_null=True)
    quantity = serializers.IntegerField(allow_null=True)
    typology = serializers.CharField(allow_null=True, allow_blank=True)
    location_tag = serializers.CharField(allow_null=True, allow_blank=True)
    width_mm = serializers.CharField(allow_blank=True)
    height_mm = serializers.CharField(allow_blank=True)
    opening_measurements = PortalOpeningSerializer(many=True,required=False)
    color_interior = serializers.CharField(allow_null=True, allow_blank=True)
    color_exterior = serializers.CharField(allow_null=True, allow_blank=True)
    glass_specs = serializers.ListField(child=serializers.CharField())
    commercial_hardware = CommercialHardwareSerializer(many=True, required=False)
    finish = serializers.CharField(allow_null=True, allow_blank=True)
    price_net = serializers.CharField(allow_null=True)
    discount_pct = serializers.CharField(allow_null=True, allow_blank=True)
    parametric_tree = serializers.JSONField(allow_null=True)


class PortalPaymentSerializer(serializers.Serializer):
    simulated = serializers.BooleanField(required=False)
    status = serializers.CharField()
    collected = serializers.CharField()
    balance = serializers.CharField()


class PortalOptionSerializer(serializers.Serializer):
    quote_pdf_url = serializers.CharField(allow_null=True)
    payment_terms = serializers.CharField(allow_null=True, allow_blank=True)
    notes_commercial = serializers.CharField(allow_null=True, allow_blank=True)
    revision_code = serializers.CharField()
    snapshot_sha256 = serializers.CharField()
    currency = serializers.CharField()
    total_price_gross = serializers.CharField(allow_null=True)
    display_total_gross = serializers.CharField(allow_null=True)
    rounding_adjustment = serializers.CharField(allow_null=True)
    price_cause = serializers.CharField(allow_null=True)
    price_source = serializers.CharField()
    consent_text = serializers.CharField(allow_null=True)
    positions = PortalPositionSerializer(many=True)
    extras = serializers.ListField(child=serializers.DictField())
    commercial_terms = serializers.JSONField()
    payment_schedule = serializers.ListField(child=serializers.DictField())


class PortalQuoteSerializer(serializers.Serializer):
    options = PortalOptionSerializer(many=True, required=False)
    selected_revision = serializers.CharField(required=False)
    offering_sha256 = serializers.CharField(required=False)
    display_total_gross = serializers.CharField(allow_null=True, required=False)
    rounding_adjustment = serializers.CharField(allow_null=True, required=False)
    price_cause = serializers.CharField(allow_null=True, required=False)
    price_source = serializers.CharField(required=False)
    consent_text = serializers.CharField(allow_null=True, required=False)
    commercial_terms = serializers.JSONField(required=False)
    payment_schedule = serializers.ListField(child=serializers.DictField(), required=False)
    payment_provider = serializers.ChoiceField(choices=['FLOW','SIMULATED'], allow_null=True, required=False)
    validity_days = serializers.IntegerField(allow_null=True, required=False)
    successor_path = serializers.CharField(allow_null=True, required=False)
    schema = serializers.CharField()
    organization = PortalOrganizationSerializer()
    project_code = serializers.CharField()
    project_name = serializers.CharField()
    client_name = serializers.CharField()
    revision_code = serializers.CharField()
    emitted_at = serializers.DateTimeField()
    currency = serializers.CharField()
    payment_terms = serializers.CharField(allow_null=True, allow_blank=True)
    notes_commercial = serializers.CharField(allow_null=True, allow_blank=True)
    total_price_net = serializers.CharField(allow_null=True)
    total_price_tax = serializers.CharField(allow_null=True)
    total_price_gross = serializers.CharField(allow_null=True)
    extras = serializers.ListField(child=serializers.DictField())
    positions = PortalPositionSerializer(many=True)
    payment = PortalPaymentSerializer(allow_null=True)
    payment_url = serializers.CharField(allow_null=True)
    valid_until = serializers.CharField(allow_null=True)
    validity_expired = serializers.BooleanField()
    superseded = serializers.BooleanField()
    expires_at = serializers.DateTimeField()
    approval_status = serializers.CharField()
    decided_by = serializers.CharField(allow_null=True)
    decided_at = serializers.DateTimeField(allow_null=True)
    decided_note = serializers.CharField(allow_null=True)
    quote_pdf_url = serializers.CharField(allow_null=True)


class ApprovalRecordSerializer(serializers.Serializer):
    evidence = serializers.JSONField(allow_null=True, required=False)
    selected_revision = serializers.CharField(allow_null=True, required=False)
    decision_kind = serializers.CharField(allow_null=True, required=False)
    position_index = serializers.IntegerField(allow_null=True, required=False)
    id = serializers.CharField()
    link_source = serializers.ChoiceField(choices=["SHARE", "DOCUMENT"], required=False)
    status = serializers.CharField()
    revision_code = serializers.CharField()
    decided_by = serializers.CharField(allow_null=True)
    decided_at = serializers.DateTimeField(allow_null=True)
    decided_note = serializers.CharField(allow_null=True)
    expires_at = serializers.DateTimeField()
    created_at = serializers.DateTimeField()
    original_expires_at = serializers.DateTimeField(required=False)
    link_state = serializers.ChoiceField(choices=["ACTIVE","VIEWED","SUPERSEDED","EXPIRED","REVOKED","APPROVED","DECLINED","CHANGES_REQUESTED"], required=False)
    revoked_at = serializers.DateTimeField(allow_null=True)
    view_count = serializers.IntegerField()
    last_viewed_at = serializers.DateTimeField(allow_null=True)


class InternalApprovalSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True, max_length=500)


class InternalApprovalResultSerializer(serializers.Serializer):
    project_status = serializers.CharField()


class PortalPayRequestSerializer(StrictSerializer):
    operation_key = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=0, min_value=Decimal('1'))
    payer_email = serializers.EmailField(max_length=254)


class PortalPayResultSerializer(serializers.Serializer):
    url = serializers.CharField()
    simulated = serializers.BooleanField()


class PortalPayReturnSerializer(serializers.Serializer):
    portal_path = serializers.CharField()
    status = serializers.CharField()
    simulated = serializers.BooleanField()
    amount = serializers.CharField()


class DecideRequestSerializer(StrictSerializer):
    decision = serializers.ChoiceField(choices=["APPROVED", "CHANGES_REQUESTED", "DECLINED"])
    decided_by = serializers.CharField(max_length=255, allow_blank=True, required=False, default='')
    decided_rut = serializers.CharField(required=False, allow_blank=True, max_length=32)
    note = serializers.CharField(required=False, allow_blank=True, max_length=500)
    selected_revision = serializers.RegexField(r'^REV-[A-Z]+$')
    expected_offering_sha256 = serializers.RegexField(r'^[0-9a-f]{64}$')
    expected_selected_sha256 = serializers.RegexField(r'^[0-9a-f]{64}$')
    confirmed = serializers.BooleanField(required=False, default=False)
    consent_text = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    position_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, value):
        if value['decision'] == 'APPROVED':
            errors = {}
            if not value.get('decided_by', '').strip():
                errors['decided_by'] = 'Indique su nombre completo.'
            if not valid_rut(value.get('decided_rut')):
                errors['decided_rut'] = 'Ingrese un RUT válido, con su dígito verificador.'
            if not value.get('confirmed') or not value.get('consent_text'):
                errors['confirmed'] = 'Marque la aceptación de la propuesta y sus condiciones.'
            if errors:
                raise serializers.ValidationError(errors)
        if value['decision'] == 'CHANGES_REQUESTED' and not value.get('note', '').strip():
            raise serializers.ValidationError({'note': 'Describa el cambio que necesita.'})
        return value
