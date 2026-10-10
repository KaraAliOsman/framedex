"""Structured commercial declarations; never parse money from free text."""

from decimal import Decimal

from rest_framework import serializers

from dekopen_engine.commercial import PricingError
from dekopen_engine.quotation import payment_amounts
from engine_api.serializers import DecimalStringField
from pricing.serializers import StrictSerializer


class PaymentMilestoneSerializer(StrictSerializer):
    label = serializers.CharField(max_length=120, allow_blank=False)
    share = DecimalStringField(max_digits=7, decimal_places=6, min_value=Decimal("0.000001"), max_value=Decimal("1"))


class CommercialTermsSerializer(StrictSerializer):
    payment_schedule = PaymentMilestoneSerializer(many=True, required=False, allow_empty=True)
    delivery_text = serializers.CharField(max_length=1000, allow_blank=True, required=False)
    installation_text = serializers.CharField(max_length=1000, allow_blank=True, required=False)
    exclusions = serializers.CharField(max_length=4000, allow_blank=True, required=False)
    warranty = serializers.CharField(max_length=4000, allow_blank=True, required=False)
    jurisdiction = serializers.CharField(max_length=1000, allow_blank=True, required=False)

    def validate_payment_schedule(self, value):
        if len(value) > 12:
            raise serializers.ValidationError("El calendario admite hasta doce hitos.")
        try:
            payment_amounts(Decimal("100"), [item["share"] for item in value], "CLP")
        except PricingError as error:
            raise serializers.ValidationError("Las proporciones del calendario deben sumar 100 %.") from error
        return value


class DocumentPreferencesSerializer(StrictSerializer):
    piece_label_paper = serializers.ChoiceField(choices=["LETTER", "A4", "ROLL_100_50"], required=False)
    remnant_destination = serializers.CharField(max_length=80, allow_blank=False, required=False)
    remnant_age_days = serializers.IntegerField(min_value=1, max_value=3650, required=False)
    quotation_preview_minutes = serializers.IntegerField(required=False, min_value=5, max_value=60)
    quotation_valid_days = serializers.IntegerField(required=False, min_value=1, max_value=365)
    paper = serializers.ChoiceField(choices=["LETTER", "OFICIO", "A4"])
    accent = serializers.ChoiceField(choices=["TEAL", "TEAL_DARK", "GRAPHITE"])
    legal_footer = serializers.CharField(max_length=240, allow_blank=True)
    commercial_terms = CommercialTermsSerializer()
