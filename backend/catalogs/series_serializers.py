"""Typed DEKOPEN 2 series sheet, template and atomic cell contracts."""

from rest_framework import serializers

from catalogs.serializers import (
    ArticleResponseSerializer, ArticleWriteSerializer, BeadResponseSerializer,
    BeadWriteSerializer, KitResponseSerializer, KitWriteSerializer,
    SystemResponseSerializer, SystemWriteSerializer, WorkspaceGlassSerializer,
    PurchaseMappingRowSerializer, ReinforcementRowSerializer,
)
from pricing.serializers import StrictSerializer
from catalogs.use_serializers import CatalogUseSerializer

RESOURCES = ("systems", "articles", "glazing", "hardware-kits")


class OptionalTemplateFields:
    required_fields = ()
    excluded_fields = ()

    def get_fields(self):
        fields = super().get_fields()
        for name in self.excluded_fields:
            fields.pop(name, None)
        for name, field in fields.items():
            field.required = name in self.required_fields
        return fields


class TemplateSystemInputSerializer(OptionalTemplateFields, SystemWriteSerializer):
    excluded_fields = ("name", "code", "version", "is_active")


class TemplateProfileInputSerializer(OptionalTemplateFields, ArticleWriteSerializer):
    required_fields = ("sku", "name", "role", "face_width_mm")
    excluded_fields = ("system_id",)
    screw_sku = serializers.CharField(max_length=100, required=False)


class TemplateGlazingInputSerializer(OptionalTemplateFields, BeadWriteSerializer):
    required_fields = ("bead_sku", "glass_thickness_mm", "bead_width_mm")
    excluded_fields = ("system_id", "bead_article_id")
    bead_sku = serializers.CharField(max_length=100)


class TemplateHardwareInputSerializer(OptionalTemplateFields, KitWriteSerializer):
    required_fields = ("sku", "name", "opening_type", "contents")
    excluded_fields = ("system_id",)


class SeriesCreateSerializer(StrictSerializer):
    template_id = serializers.CharField(max_length=100)
    template_version = serializers.IntegerField(min_value=1)
    name = serializers.CharField(max_length=150)
    code = serializers.CharField(max_length=50)
    manufacturer = serializers.CharField(max_length=255, required=False)
    rules = TemplateSystemInputSerializer(required=False)
    profiles = TemplateProfileInputSerializer(many=True, max_length=200, required=False)
    glazing = TemplateGlazingInputSerializer(many=True, max_length=200, required=False)
    hardware = TemplateHardwareInputSerializer(many=True, max_length=200, required=False)


class FamilyTemplateSerializer(serializers.Serializer):
    id = serializers.CharField()
    version = serializers.IntegerField()
    name = serializers.CharField()
    origin = serializers.ChoiceField(choices=["SUGGESTED"])
    source_ref = serializers.CharField()
    notes = serializers.ListField(child=serializers.CharField())
    system = serializers.JSONField()
    profile_defaults = serializers.JSONField()
    reinforcement_defaults = serializers.JSONField(allow_null=True)
    hardware_defaults = serializers.JSONField()
    glazing_defaults = serializers.JSONField()
    prices = serializers.ListField()


class FamilyTemplateListSerializer(serializers.Serializer):
    items = FamilyTemplateSerializer(many=True)


class SeriesCellSerializer(serializers.Serializer):
    resource = serializers.ChoiceField(choices=RESOURCES)
    row_id = serializers.UUIDField()
    field = serializers.CharField(max_length=250)
    value = serializers.CharField(allow_null=True)
    origin = serializers.ChoiceField(choices=["MANUAL", "WORKSHOP", "SUGGESTED"], allow_null=True)
    source_ref = serializers.CharField(allow_null=True)
    set_by = serializers.UUIDField(allow_null=True)
    set_at = serializers.DateTimeField(allow_null=True)
    version_id = serializers.UUIDField(allow_null=True)


class SeriesPriceSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    cost_list_id = serializers.UUIDField()
    sku = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    unit = serializers.CharField()
    unit_cost = serializers.CharField()
    currency = serializers.CharField()
    valid_from = serializers.DateField()
    valid_to = serializers.DateField(allow_null=True)


class SeriesPricesTabSerializer(serializers.Serializer):
    can_view = serializers.BooleanField()
    items = SeriesPriceSerializer(many=True)
    purchase_mappings = PurchaseMappingRowSerializer(many=True)
    reinforcements = ReinforcementRowSerializer(many=True)


class SeriesGlazingTabSerializer(serializers.Serializer):
    beads = BeadResponseSerializer(many=True)
    glasses = WorkspaceGlassSerializer(many=True)
    finishes = serializers.ListField(child=serializers.CharField())
    finish_rules = serializers.JSONField(allow_null=True)


class SeriesTypologiesTabSerializer(serializers.Serializer):
    dimensional_limits = serializers.JSONField()
    opening_capabilities = serializers.JSONField(allow_null=True)


class SeriesTabsSerializer(serializers.Serializer):
    profiles = ArticleResponseSerializer(many=True)
    rules = SystemResponseSerializer()
    hardware = KitResponseSerializer(many=True)
    glazing_colors = SeriesGlazingTabSerializer()
    typologies = SeriesTypologiesTabSerializer()
    prices = SeriesPricesTabSerializer()


class SeriesSetupSerializer(serializers.Serializer):
    template_id = serializers.CharField(allow_null=True)
    template_version = serializers.IntegerField(allow_null=True)
    verified_at = serializers.DateTimeField(allow_null=True)
    verified_by = serializers.UUIDField(allow_null=True)


class SeriesSheetSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    revision = serializers.CharField()
    setup = SeriesSetupSerializer()
    usage = CatalogUseSerializer()
    tabs = SeriesTabsSerializer()
    cells = SeriesCellSerializer(many=True)


class CellAddressSerializer(StrictSerializer):
    resource = serializers.ChoiceField(choices=RESOURCES)
    row_id = serializers.UUIDField()
    field = serializers.CharField(max_length=250)


class CellChangeSerializer(CellAddressSerializer):
    value = serializers.JSONField(allow_null=True)


class SeriesBatchEditSerializer(StrictSerializer):
    revision = serializers.CharField()
    changes = CellChangeSerializer(many=True, min_length=1, max_length=5000)


class SeriesBatchConfirmSerializer(StrictSerializer):
    revision = serializers.CharField()
    cells = CellAddressSerializer(many=True, min_length=1, max_length=5000)


class CellHistoryRowSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    version = serializers.IntegerField()
    previous_id = serializers.UUIDField(allow_null=True)
    value = serializers.CharField(allow_null=True)
    previous_value = serializers.CharField(allow_null=True)
    origin = serializers.ChoiceField(choices=["MANUAL", "WORKSHOP", "SUGGESTED"])
    source_ref = serializers.CharField()
    set_by = serializers.UUIDField()
    set_at = serializers.DateTimeField()


class CellHistorySerializer(serializers.Serializer):
    items = CellHistoryRowSerializer(many=True)
