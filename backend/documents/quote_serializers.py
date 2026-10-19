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
    due_on = serializers.DateField(required=False, allow_null=True)
    due_event = serializers.ChoiceField(choices=("APPROVAL", "DELIVERY"), required=False, allow_null=True)


class CommercialTermsSerializer(StrictSerializer):
    payment_schedule = PaymentMilestoneSerializer(many=True, required=False, allow_empty=True)
    delivery_text = serializers.CharField(max_length=1000, allow_blank=True, required=False)
    installation_text = serializers.CharField(max_length=1000, allow_blank=True, required=False)
    exclusions = serializers.CharField(max_length=4000, allow_blank=True, required=False)
    warranty = serializers.CharField(max_length=4000, allow_blank=True, required=False)
    warranty_days = serializers.IntegerField(min_value=1, max_value=36500, required=False, allow_null=True)
    warranty_start = serializers.ChoiceField(choices=("APPROVAL", "DELIVERY", "INSTALLATION"), required=False, allow_null=True)
    jurisdiction = serializers.CharField(max_length=1000, allow_blank=True, required=False)

    def validate(self, value):
        if bool(value.get("warranty_days")) != bool(value.get("warranty_start")):
            raise serializers.ValidationError("Declara juntos el plazo de garantía y el hecho que lo inicia.")
        return value

    def validate_payment_schedule(self, value):
        if len(value) > 12:
            raise serializers.ValidationError("El calendario admite hasta doce hitos.")
        try:
            payment_amounts(Decimal("100"), [item["share"] for item in value], "CLP")
        except PricingError as error:
            raise serializers.ValidationError("Las proporciones del calendario deben sumar 100 %.") from error
        return value


QUOTATION_BLOCKS = ["intro", "client", "hero", "summary", "positions", "alternatives", "commercial", "terms", "services", "acceptance", "closing"]


class LayoutTextsSerializer(StrictSerializer):
    intro = serializers.CharField(max_length=2000, allow_blank=True, required=False)
    closing = serializers.CharField(max_length=2000, allow_blank=True, required=False)
    notes = serializers.CharField(max_length=2000, allow_blank=True, required=False)


class QuotationLayoutSerializer(StrictSerializer):
    """Editable composition of a quotation: family, block order/visibility,
    editorial texts and presentation. Never numbers: those come sealed from
    the calculation."""

    template = serializers.ChoiceField(choices=["ESENCIAL", "PROYECTO", "ALTERNATIVAS"], required=False)
    order = serializers.ListField(child=serializers.ChoiceField(choices=QUOTATION_BLOCKS), required=False, max_length=20)
    hidden = serializers.ListField(child=serializers.ChoiceField(choices=QUOTATION_BLOCKS), required=False, max_length=20)
    texts = LayoutTextsSerializer(required=False)
    drawing_size = serializers.ChoiceField(choices=["S", "M", "L"], required=False)
    unit_prices = serializers.BooleanField(required=False)

    def validate_hidden(self, value):
        if {"positions", "commercial"} & set(value):
            raise serializers.ValidationError("Las ventanas y el resumen comercial no se pueden ocultar.")
        return value


class DocumentPreferencesSerializer(StrictSerializer):
    portal_successor_link = serializers.BooleanField(required=False)
    piece_label_paper = serializers.ChoiceField(choices=["LETTER", "A4", "ROLL_100_50"], required=False)
    remnant_destination = serializers.CharField(max_length=80, allow_blank=False, required=False)
    remnant_age_days = serializers.IntegerField(min_value=1, max_value=3650, required=False)
    quotation_preview_minutes = serializers.IntegerField(required=False, min_value=5, max_value=60)
    quotation_valid_days = serializers.IntegerField(required=False, min_value=1, max_value=365)
    paper = serializers.ChoiceField(choices=["LETTER", "OFICIO", "A4"])
    accent = serializers.ChoiceField(choices=["TEAL", "TEAL_DARK", "GRAPHITE"])
    legal_footer = serializers.CharField(max_length=240, allow_blank=True)
    commercial_terms = CommercialTermsSerializer()
    quotation_template = serializers.ChoiceField(choices=["ESENCIAL", "PROYECTO", "ALTERNATIVAS"], required=False)
    acceptance_mode = serializers.ChoiceField(choices=["NONE", "PORTAL", "SIGNATURE"], required=False)
    quotation_layout = QuotationLayoutSerializer(required=False)


class DocumentPreferencesPatchSerializer(DocumentPreferencesSerializer):
    """Save only the section edited by the user; preserve other sections."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False
