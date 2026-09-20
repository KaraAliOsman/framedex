"""Schema-backed manual catalogs and exact hardware component quantities."""

from decimal import Decimal, InvalidOperation

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from pricing.serializers import StrictSerializer
from dekopen_engine.geometry import SUPPORTED_OPENING_TYPES
from dekopen_engine.hardware import normalize_opening_type
from dekopen_engine.models import BayOpeningType

KIT_OPENING_TYPES = sorted(
    {
        normalize_opening_type(opening)
        for opening in SUPPORTED_OPENING_TYPES
        if opening is not BayOpeningType.FIXED
    }
)


class ExactDecimalField(serializers.DecimalField):
    def to_internal_value(self, data):
        if isinstance(data, (bool, float)):
            raise serializers.ValidationError("Use an exact decimal string.")
        return super().to_internal_value(data)


def decimal_field(digits, places, **kwargs):
    return ExactDecimalField(
        max_digits=digits,
        decimal_places=places,
        coerce_to_string=True,
        **kwargs,
    )


def integer_field():
    return serializers.IntegerField(
        min_value=-2147483648,
        max_value=2147483647,
    )


@extend_schema_field({"type": "string", "format": "decimal"})
class QuantityField(serializers.Field):
    """JSONB quantities have no schema-authorized fixed decimal scale."""

    def to_internal_value(self, data):
        if isinstance(data, bool) or not isinstance(data, (str, int, Decimal)):
            raise serializers.ValidationError("Use an exact decimal string.")
        try:
            value = Decimal(data)
        except (InvalidOperation, ValueError):
            raise serializers.ValidationError("Invalid quantity.") from None
        if not value.is_finite() or value <= 0:
            raise serializers.ValidationError("Quantity must be finite and positive.")
        return value

    def to_representation(self, value):
        return str(value)


class SystemWriteSerializer(StrictSerializer):
    name = serializers.CharField(max_length=150)
    code = serializers.CharField(max_length=50)
    depth_mm = decimal_field(10, 2, min_value=Decimal("0.01"))
    material = serializers.ChoiceField(choices=["PVC", "ALUMINIUM"])
    chamber_count = serializers.IntegerField(min_value=1, max_value=2147483647)
    sash_overlap_mm = decimal_field(4, 2, min_value=Decimal("0.00"))
    glass_clearance_white_mm = decimal_field(4, 2, min_value=Decimal("0.00"))
    glass_clearance_foil_mm = decimal_field(4, 2, min_value=Decimal("0.00"))
    pulley_height_mm = decimal_field(4, 2, min_value=Decimal("0.00"))
    central_overlap_mm = decimal_field(4, 2, min_value=Decimal("0.00"))
    sliding_lateral_clearance_mm = decimal_field(4, 2, min_value=Decimal("0.00"))
    sliding_end_add_mm = decimal_field(4, 2, min_value=Decimal("0.00"))
    corner_bracket_loss_mm = decimal_field(4, 2, min_value=Decimal("0.00"))
    hook_depth_mm = decimal_field(4, 2, min_value=Decimal("0.00"))
    door_threshold_mm = decimal_field(4, 2, min_value=Decimal("0.00"))
    door_bottom_clearance_mm = decimal_field(4, 2, min_value=Decimal("0.00"))
    rail_type = serializers.ChoiceField(choices=["dual", "mono"])
    sliding_glazing_deduction_width_mm = decimal_field(10, 2, min_value=Decimal("0.00"))
    sliding_glazing_deduction_height_mm = decimal_field(10, 2, min_value=Decimal("0.00"))
    door_leaf_side_clearance_mm = decimal_field(10, 2, min_value=Decimal("0.00"))
    chamber_clearance_mm = decimal_field(
        10,
        2,
        allow_null=True,
        required=False,
        min_value=Decimal("0.01"),
    )
    version = serializers.IntegerField(min_value=1, max_value=2147483647)
    is_active = serializers.BooleanField()


class ArticleWriteSerializer(StrictSerializer):
    system_id = serializers.UUIDField()
    sku = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=255)
    role = serializers.ChoiceField(
        choices=[
            "FRAME",
            "SASH",
            "MULLION_V",
            "MULLION_H",
            "INVERSOR",
            "GLAZING_BEAD",
            "COUPLER",
            "ADDITIONAL",
            "THRESHOLD",
        ]
    )
    material = serializers.ChoiceField(choices=["PVC", "ALUMINIUM"])
    face_width_mm = decimal_field(10, 2, min_value=Decimal("0.01"))
    commercial_length_mm = decimal_field(10, 2, min_value=Decimal("0.01"))
    welding_loss_mm = decimal_field(10, 2, min_value=Decimal("0.00"))
    reinforcement_sku = serializers.CharField(
        max_length=100,
        allow_null=True,
        allow_blank=True,
        required=False,
    )
    reinforcement_gap_mm = decimal_field(10, 2, min_value=Decimal("0.00"))
    weight_kg_m = decimal_field(8, 4, min_value=Decimal("0.0001"))
    steel_weight_kg_m = decimal_field(8, 4, min_value=Decimal("0.0000"))


class BeadWriteSerializer(StrictSerializer):
    system_id = serializers.UUIDField()
    glass_thickness_mm = decimal_field(6, 2, min_value=Decimal("0.01"))
    bead_article_id = serializers.UUIDField()
    bead_width_mm = decimal_field(6, 2, min_value=Decimal("0.01"))
    gasket_interior_mm = decimal_field(6, 2, min_value=Decimal("0.00"))
    gasket_exterior_mm = decimal_field(6, 2, min_value=Decimal("0.00"))
    cut_add_mm = decimal_field(6, 2, min_value=Decimal("0.00"))
    is_active = serializers.BooleanField()


class CatalogHardwareComponentSerializer(StrictSerializer):
    sku = serializers.CharField()
    name = serializers.CharField()
    qty = QuantityField()
    unit = serializers.CharField()


class KitWriteSerializer(StrictSerializer):
    def validate(self, attrs):
        effective = {**(self.instance or {}), **attrs}
        for axis in ("width", "height"):
            lower, upper = f"min_leaf_{axis}_mm", f"max_leaf_{axis}_mm"
            if lower in effective and upper in effective and effective[lower] > effective[upper]:
                raise serializers.ValidationError({upper: "Maximum must not be below minimum."})
        return attrs

    system_id = serializers.UUIDField(allow_null=True)
    sku = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=255)
    opening_type = serializers.ChoiceField(choices=KIT_OPENING_TYPES)
    min_leaf_width_mm = decimal_field(10, 2, min_value=Decimal("0.01"))
    max_leaf_width_mm = decimal_field(10, 2, min_value=Decimal("0.01"))
    min_leaf_height_mm = decimal_field(10, 2, min_value=Decimal("0.01"))
    max_leaf_height_mm = decimal_field(10, 2, min_value=Decimal("0.01"))
    max_leaf_weight_kg = decimal_field(6, 2, min_value=Decimal("0.01"))
    rail_type = serializers.ChoiceField(choices=["dual", "mono"])
    carriages_qty = serializers.IntegerField(min_value=0, max_value=2147483647)
    stay_arms_qty = serializers.IntegerField(min_value=0, max_value=2147483647)
    contents = CatalogHardwareComponentSerializer(many=True)
    weight_kg = decimal_field(8, 2, allow_null=True, required=False, min_value=Decimal("0.01"))
    carriage_capacity_kg = decimal_field(
        8,
        2,
        allow_null=True,
        required=False,
        min_value=Decimal("0.01"),
    )
    is_active = serializers.BooleanField()


class CatalogReadinessSerializer(serializers.Serializer):
    quote_ready = serializers.BooleanField()
    scope = serializers.CharField()
    reasons = serializers.ListField(child=serializers.CharField())


class SystemResponseSerializer(SystemWriteSerializer):
    readiness = CatalogReadinessSerializer(read_only=True)
    revision = serializers.CharField(read_only=True)
    read_only = serializers.BooleanField()
    id = serializers.UUIDField()
    is_global = serializers.BooleanField()
    is_demo = serializers.BooleanField()


class ArticleResponseSerializer(ArticleWriteSerializer):
    revision = serializers.CharField(read_only=True)
    read_only = serializers.BooleanField()
    id = serializers.UUIDField()


class BeadResponseSerializer(BeadWriteSerializer):
    revision = serializers.CharField(read_only=True)
    read_only = serializers.BooleanField()
    id = serializers.UUIDField()


class KitResponseSerializer(KitWriteSerializer):
    revision = serializers.CharField(read_only=True)
    read_only = serializers.BooleanField()
    id = serializers.UUIDField()


class SystemListSerializer(serializers.Serializer):
    items = SystemResponseSerializer(many=True)


class ArticleListSerializer(serializers.Serializer):
    items = ArticleResponseSerializer(many=True)


class BeadListSerializer(serializers.Serializer):
    items = BeadResponseSerializer(many=True)


class KitListSerializer(serializers.Serializer):
    items = KitResponseSerializer(many=True)


class CatalogFilterSerializer(StrictSerializer):
    system_id = serializers.UUIDField(required=False)
