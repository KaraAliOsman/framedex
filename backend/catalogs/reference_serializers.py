"""Exact input contracts for a resumable setup and human window confirmation."""

from decimal import Decimal

from rest_framework import serializers

from engine_api.serializers import DecimalStringField
from authentication.serializers import ErrorResponseSerializer
from catalogs.series_serializers import CellChangeSerializer
from pricing.serializers import StrictSerializer


class TrialInputSerializer(StrictSerializer):
    nominal_width_mm = DecimalStringField(max_digits=10, decimal_places=2, min_value=Decimal("0.01"))
    nominal_height_mm = DecimalStringField(max_digits=10, decimal_places=2, min_value=Decimal("0.01"))
    color = serializers.CharField(max_length=50)
    parametric_tree = serializers.JSONField()
    manual_values = serializers.DictField(child=DecimalStringField(max_digits=10, decimal_places=2,
        min_value=Decimal("0.01")), required=False)

    def validate_manual_values(self, value):
        if len(value) > 500:
            raise serializers.ValidationError("Compara hasta 500 medidas por ventana.")
        return value


class TrialProposalInputSerializer(TrialInputSerializer):
    measurement_key = serializers.CharField(max_length=100)
    target_mm = DecimalStringField(max_digits=10, decimal_places=2, min_value=Decimal("0.01"))


class TrialVerificationSerializer(TrialInputSerializer):
    revision = serializers.CharField()
    calculation_token = serializers.CharField(max_length=4000)
    confirmed = serializers.BooleanField()
    confirm_suggested = serializers.BooleanField(default=False)

    def validate_confirmed(self, value):
        if value is not True:
            raise serializers.ValidationError("Confirma el despiece completo antes de guardar la prueba.")
        return value


class TrialMeasurementSerializer(serializers.Serializer):
    key = serializers.CharField()
    group = serializers.ChoiceField(choices=["profile_cuts", "reinforcements", "glasses"])
    index = serializers.IntegerField()
    field = serializers.CharField()
    sku = serializers.CharField()
    role = serializers.CharField()
    quantity = serializers.IntegerField()
    value_mm = serializers.CharField()
    angle_left = serializers.CharField(allow_null=True)
    angle_right = serializers.CharField(allow_null=True)
    manual_mm = serializers.CharField(allow_null=True)
    difference_mm = serializers.CharField(allow_null=True)
    matches = serializers.BooleanField(allow_null=True)


class TrialResponseSerializer(serializers.Serializer):
    measurements = TrialMeasurementSerializer(many=True)
    result = serializers.JSONField()
    calculation_token = serializers.CharField()


class TrialProposalSerializer(serializers.Serializer):
    label = serializers.CharField()
    previous = serializers.CharField()
    value = serializers.CharField()
    change = CellChangeSerializer()
    measurements = TrialMeasurementSerializer(many=True)
    result = serializers.JSONField()


class TrialProposalsSerializer(serializers.Serializer):
    revision = serializers.CharField()
    items = TrialProposalSerializer(many=True)


class ReferenceWindowSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    system_id = serializers.UUIDField(required=False)
    technical_hash = serializers.CharField()
    verified_at = serializers.DateTimeField()
    verified_by = serializers.UUIDField()
    input = serializers.JSONField(required=False)
    expected_output = serializers.JSONField(required=False)


class ReferenceWindowListSerializer(serializers.Serializer):
    items = ReferenceWindowSerializer(many=True)


class SetupStateSerializer(StrictSerializer):
    # Prices stay in the owner's price APIs. Shared setup state carries only
    # technical drafts and references to imports, whose permissions still apply.
    trial = TrialInputSerializer(required=False)
    manual_import_id = serializers.UUIDField(required=False, allow_null=True)
    prices_file_name = serializers.CharField(max_length=255, required=False)


class SetupProgressInputSerializer(StrictSerializer):
    step = serializers.IntegerField(min_value=1, max_value=5)
    revision = serializers.IntegerField(min_value=1)
    state = SetupStateSerializer()


class SetupProgressSerializer(serializers.Serializer):
    step = serializers.IntegerField()
    revision = serializers.IntegerField()
    state = SetupStateSerializer()


class ReferenceStateSerializer(serializers.Serializer):
    output = serializers.JSONField(allow_null=True)
    error = serializers.CharField(allow_null=True)
    measurements = TrialMeasurementSerializer(many=True)


class ReferenceChangeSerializer(serializers.Serializer):
    system_id = serializers.UUIDField()
    reference_id = serializers.UUIDField()
    expected_output = serializers.JSONField()
    before = ReferenceStateSerializer()
    after = ReferenceStateSerializer()


class ReferenceChangeReviewSerializer(serializers.Serializer):
    changes = ReferenceChangeSerializer(many=True)
    review_token = serializers.CharField()


class ReferenceChangeErrorSerializer(ErrorResponseSerializer):
    golden_review = ReferenceChangeReviewSerializer(required=False)
