"""Schema-backed manual catalogs and exact hardware component quantities."""

from decimal import Decimal, InvalidOperation
import json

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from pricing.serializers import StrictSerializer
from dekopen_engine.geometry import SUPPORTED_OPENING_TYPES
from dekopen_engine.hardware import normalize_opening_type
from dekopen_engine.models import (
    BayOpeningType,
    ProfileRole,
    SystemFamily,
    HARDWARE_COMPONENT_CATEGORIES,
    polygon_self_intersects,
)
from catalogs.evidence import EVIDENCE_TABLES, EVIDENCE_SCOPES, EVIDENCE_UNITS
from dekopen_engine.models import OpeningCapability, PairedLeafRule
from pydantic import TypeAdapter
from pricing.repository import json_text
from dekopen_engine.hardware_classes import parse_hardware_class

KIT_OPENING_TYPES = sorted(
    {
        normalize_opening_type(opening)
        for opening in SUPPORTED_OPENING_TYPES
        if opening is not BayOpeningType.FIXED
    } | {"TILT"}
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


class CompleteAuthoritySerializer(StrictSerializer):
    def validate(self, attrs):
        missing = {key for key, field in self.fields.items() if field.required} - attrs.keys()
        if missing:
            raise serializers.ValidationError({key: "Falta este dato de la fuente." for key in sorted(missing)})
        return attrs


class ProfileCutRuleSerializer(CompleteAuthoritySerializer):
    angle_degrees = serializers.ChoiceField(choices=[45, 90])
    welding_loss_per_end_mm = decimal_field(10, 2, min_value=Decimal("0"))
    joint_deduction_per_end_mm = decimal_field(10, 2, min_value=Decimal("0"))
    meeting_deduction_mm = decimal_field(10, 2, min_value=Decimal("0"))
    cut_step_mm = decimal_field(10, 2, min_value=Decimal("0.01"))
    rounding = serializers.ChoiceField(choices=["UP", "NEAREST", "DOWN"])
    source = serializers.CharField(max_length=1000)


class ProfileReinforcementRuleSerializer(CompleteAuthoritySerializer):
    reinforcement_sku = serializers.CharField(max_length=100)
    reinforcement_type = serializers.CharField(max_length=100)
    minimum_length_mm = decimal_field(10, 2, min_value=Decimal("0"))
    required_finishes = serializers.ListField(child=serializers.CharField(max_length=50))
    required_non_white = serializers.BooleanField()
    cut_deduction_mm = decimal_field(10, 2, min_value=Decimal("0"))
    screws_per_m = decimal_field(10, 4, min_value=Decimal("0.0001"))
    screw_sku = serializers.CharField(max_length=100)
    screw_weight_kg = decimal_field(10, 6, min_value=Decimal("0"), required=False, allow_null=True)
    source = serializers.CharField(max_length=1000)


class SlidingSystemParametersSerializer(CompleteAuthoritySerializer):
    pulley_height_mm = decimal_field(10, 2, min_value=Decimal("0"))
    central_overlap_mm = decimal_field(10, 2, min_value=Decimal("0"))
    lateral_clearance_mm = decimal_field(10, 2, min_value=Decimal("0"))
    end_add_mm = decimal_field(10, 2, min_value=Decimal("0"))
    glazing_deduction_width_mm = decimal_field(10, 2, min_value=Decimal("0"))
    glazing_deduction_height_mm = decimal_field(10, 2, min_value=Decimal("0"))
    rail_type = serializers.ChoiceField(choices=["dual", "mono"])
    rail_count = serializers.IntegerField(min_value=1, max_value=2147483647)
    separate_rail = serializers.BooleanField()
    interlock_required = serializers.BooleanField()


class SystemDimensionalLimitSerializer(CompleteAuthoritySerializer):
    opening_type = serializers.ChoiceField(choices=[item.value for item in BayOpeningType])
    min_leaf_width_mm = decimal_field(10, 2, min_value=Decimal("0.01"))
    max_leaf_width_mm = decimal_field(10, 2, min_value=Decimal("0.01"))
    min_leaf_height_mm = decimal_field(10, 2, min_value=Decimal("0.01"))
    max_leaf_height_mm = decimal_field(10, 2, min_value=Decimal("0.01"))
    max_leaf_weight_kg = decimal_field(10, 4, min_value=Decimal("0.0001"), required=False, allow_null=True)
    min_aspect_ratio = decimal_field(10, 4, min_value=Decimal("0.0001"))
    max_aspect_ratio = decimal_field(10, 4, min_value=Decimal("0.0001"))
    source = serializers.CharField(max_length=1000)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        for lower, upper in (("min_leaf_width_mm", "max_leaf_width_mm"),
                             ("min_leaf_height_mm", "max_leaf_height_mm"),
                             ("min_aspect_ratio", "max_aspect_ratio")):
            if attrs[lower] > attrs[upper]:
                raise serializers.ValidationError({upper: "El máximo debe ser mayor o igual al mínimo."})
        return attrs


class OpeningAuthorityJSONField(serializers.JSONField):
    """Nested catalog Decimals cross HTTP as exact strings, never JSON floats."""

    def to_representation(self, value):
        return json.loads(json_text(value))

    def to_internal_value(self, value):
        # CatalogJSONParser already preserves JSON numeric lexemes as Decimal;
        # service validation also receives the first serializer's Decimals.
        try:
            value = json.loads(json_text(value))
        except (TypeError, ValueError):
            self.fail("invalid")
        return super().to_internal_value(value)


class SystemWriteSerializer(StrictSerializer):
    system_family = serializers.ChoiceField(choices=[item.value for item in SystemFamily])
    sliding_parameters = SlidingSystemParametersSerializer(required=False, allow_null=True)
    dimensional_limits = SystemDimensionalLimitSerializer(many=True, required=False)
    opening_capabilities = OpeningAuthorityJSONField(required=False, allow_null=True)
    paired_leaf_rule = OpeningAuthorityJSONField(required=False, allow_null=True)

    def validate_opening_capabilities(self, value):
        if value is None:
            return None
        try:
            capabilities = TypeAdapter(tuple[OpeningCapability, ...]).validate_json(json_text(value))
            if len(capabilities) > 100:
                raise ValueError("Demasiadas capacidades.")
            signatures = [(cap.use, cap.movement, cap.direction, cap.leaf_role, cap.fixed_in_sash, hinge)
                          for cap in capabilities for hinge in cap.hinge_sides]
            if len(signatures) != len(set(signatures)):
                raise ValueError("Capacidades contradictorias.")
            return [cap.model_dump() for cap in capabilities]
        except (ValueError, TypeError):
            raise serializers.ValidationError("Completa las capacidades con movimiento, bisagras, dirección, rol, herrajes y fuente.") from None

    def validate_paired_leaf_rule(self, value):
        if value is None:
            return None
        try:
            return PairedLeafRule.model_validate_json(json_text(value)).model_dump()
        except (ValueError, TypeError):
            raise serializers.ValidationError("Completa los traslapes y descuentos del inversor con su fuente.") from None

    def validate(self, attrs):
        effective = {**(self.instance or {}), **attrs}
        family = effective.get("system_family")
        legacy = ("pulley_height_mm", "central_overlap_mm", "sliding_lateral_clearance_mm",
                  "sliding_end_add_mm", "sliding_glazing_deduction_width_mm",
                  "sliding_glazing_deduction_height_mm", "rail_type")
        if family is not None:
            for capability in effective.get("opening_capabilities") or []:
                movement, use = capability["movement"], capability["use"]
                if ((use == "DOOR") != (family == "DOOR") or
                    family == "FACADE_FIXED" and movement != "FIXED" or
                    family in ("SLIDING", "LIFT_SLIDE") and movement not in ("FIXED", "SLIDE", "LIFT_SLIDE") or
                    family == "CASEMENT" and movement in ("SLIDE", "LIFT_SLIDE")):
                    raise serializers.ValidationError({"opening_capabilities": "La capacidad no corresponde a esta familia de sistema."})
            if any(effective.get(key) is not None for key in legacy):
                raise serializers.ValidationError({key: "Este parámetro vive en la ficha de corredera."
                    for key in legacy if effective.get(key) is not None})
            sliding = effective.get("sliding_parameters")
            if family in ("SLIDING", "LIFT_SLIDE") and sliding is None:
                raise serializers.ValidationError({"sliding_parameters": "Faltan los parámetros de corredera de la fuente."})
            if family not in ("SLIDING", "LIFT_SLIDE") and sliding is not None:
                raise serializers.ValidationError({"sliding_parameters": "Esta familia no admite parámetros de corredera."})
            from dekopen_engine.catalog_rules import FAMILY_OPENINGS
            limits = effective.get("dimensional_limits", [])
            openings = [rule["opening_type"] for rule in limits]
            if len(openings) != len(set(openings)):
                raise serializers.ValidationError({"dimensional_limits": "Hay aperturas duplicadas."})
            if any(BayOpeningType(opening) not in FAMILY_OPENINGS[SystemFamily(family)] for opening in openings):
                raise serializers.ValidationError({"dimensional_limits": "La apertura del límite no corresponde a esta familia."})
        return attrs
    name = serializers.CharField(max_length=150)
    code = serializers.CharField(max_length=50)
    depth_mm = decimal_field(10, 2, min_value=Decimal("0.01"))
    material = serializers.ChoiceField(choices=["PVC", "ALUMINIUM"])
    chamber_count = serializers.IntegerField(min_value=1, max_value=2147483647)
    sash_overlap_mm = decimal_field(4, 2, min_value=Decimal("0.00"))
    glass_clearance_white_mm = decimal_field(4, 2, min_value=Decimal("0.00"))
    glass_clearance_foil_mm = decimal_field(4, 2, min_value=Decimal("0.00"))
    pulley_height_mm = decimal_field(4, 2, min_value=Decimal("0.00"), required=False, allow_null=True)
    central_overlap_mm = decimal_field(4, 2, min_value=Decimal("0.00"), required=False, allow_null=True)
    sliding_lateral_clearance_mm = decimal_field(4, 2, min_value=Decimal("0.00"), required=False, allow_null=True)
    sliding_end_add_mm = decimal_field(4, 2, min_value=Decimal("0.00"), required=False, allow_null=True)
    corner_bracket_loss_mm = decimal_field(4, 2, min_value=Decimal("0.00"))
    hook_depth_mm = decimal_field(4, 2, min_value=Decimal("0.00"))
    door_threshold_mm = decimal_field(4, 2, min_value=Decimal("0.00"))
    door_bottom_clearance_mm = decimal_field(4, 2, min_value=Decimal("0.00"))
    rail_type = serializers.ChoiceField(choices=["dual", "mono"], required=False, allow_null=True)
    sliding_glazing_deduction_width_mm = decimal_field(10, 2, min_value=Decimal("0.00"), required=False, allow_null=True)
    sliding_glazing_deduction_height_mm = decimal_field(10, 2, min_value=Decimal("0.00"), required=False, allow_null=True)
    door_leaf_side_clearance_mm = decimal_field(10, 2, min_value=Decimal("0.00"))
    rebate_depth_mm = decimal_field(
        10, 2, min_value=Decimal("0.00"), required=False, allow_null=True
    )
    end_milling_overlap_mm = decimal_field(
        10, 2, min_value=Decimal("0.00"), required=False, allow_null=True
    )
    chamber_clearance_mm = decimal_field(
        10,
        2,
        allow_null=True,
        required=False,
        min_value=Decimal("0.01"),
    )
    version = serializers.IntegerField(min_value=1, max_value=2147483647)
    is_active = serializers.BooleanField()
    # §06 system identity — NULL means unknown, never invented.
    manufacturer = serializers.CharField(
        max_length=255, required=False, allow_null=True, allow_blank=True
    )
    family = serializers.CharField(
        max_length=150, required=False, allow_null=True, allow_blank=True
    )
    applications = serializers.ListField(
        child=serializers.CharField(max_length=60), required=False
    )
    # Finishes the series actually sells — the estimator's finish picker is
    # this list, never a fixed enum. Empty/missing ⇒ ["WHITE"].
    finishes = serializers.ListField(
        child=serializers.CharField(max_length=50, allow_blank=False),
        required=False,
    )

    def validate_finishes(self, value):
        seen: list[str] = []
        for finish in value:
            canonical = finish.strip().upper()
            if canonical and canonical not in seen:
                seen.append(canonical)
        # An empty declaration can't mean "sells nothing" — WHITE is the
        # baseline every PVC/ALU series offers.
        return seen or ["WHITE"]
    # Declared process authority — bound rows must be global or org-owned.
    process_profile_id = serializers.UUIDField(required=False, allow_null=True)


class SectionPointSerializer(StrictSerializer):
    x_mm = decimal_field(10, 2)
    y_mm = decimal_field(10, 2)


class SectionAxisSerializer(StrictSerializer):
    name = serializers.CharField(max_length=50)
    y_mm = decimal_field(10, 2)


class SectionImportCandidateSerializer(serializers.Serializer):
    index = serializers.IntegerField()
    tag = serializers.CharField()
    points = serializers.ListField(child=serializers.ListField(child=serializers.CharField()))
    area = serializers.CharField()


class SectionImportResponseSerializer(serializers.Serializer):
    document_path = serializers.CharField()
    format = serializers.CharField()
    parser_version = serializers.CharField()
    mm_per_unit = serializers.CharField(allow_null=True)
    candidates = SectionImportCandidateSerializer(many=True)
    warnings = serializers.ListField(child=serializers.CharField())


class ProfileSectionSerializer(StrictSerializer):
    """Simplified technical cross-section; POLYGON is declared, DXF_REFERENCE
    carries the manufacturer-drawing provenance in `drawing_ref`."""

    source = serializers.ChoiceField(choices=["POLYGON", "DXF_REFERENCE"])
    polygon = SectionPointSerializer(many=True)
    depth_mm = decimal_field(10, 2, min_value=Decimal("0.01"))
    axes = SectionAxisSerializer(many=True, required=False)
    drawing_ref = serializers.CharField(
        max_length=500, allow_null=True, allow_blank=True, required=False
    )
    orientation = serializers.ChoiceField(
        choices=["EXTERIOR_DOWN", "EXTERIOR_UP", "EXTERIOR_LEFT", "EXTERIOR_RIGHT"],
        required=False,
        default="EXTERIOR_DOWN",
    )
    local_origin = serializers.ChoiceField(
        choices=["TOP_LEFT", "TOP_RIGHT", "BOTTOM_LEFT", "BOTTOM_RIGHT", "CENTROID"],
        required=False,
        default="TOP_LEFT",
    )

    def validate_axes(self, value):
        # Under a propagated partial update an axis row may validate with a
        # missing name or y_mm — an incomplete axis must never persist (the
        # engine decoder would reject the stored section on load).
        for axis in value:
            if "name" not in axis or "y_mm" not in axis:
                raise serializers.ValidationError(
                    "Each section axis needs a name and y_mm."
                )
        return value

    def validate_polygon(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("A section polygon needs at least 3 points.")
        points = []
        for point in value:
            if "x_mm" not in point or "y_mm" not in point:
                raise serializers.ValidationError(
                    "Each section point needs x_mm and y_mm."
                )
            points.append((point["x_mm"], point["y_mm"]))
        if len(set(points)) != len(points):
            raise serializers.ValidationError("A section polygon cannot repeat vertices.")
        area = Decimal(0)
        for index, (x1, y1) in enumerate(points):
            x2, y2 = points[(index + 1) % len(points)]
            area += x1 * y2 - x2 * y1
        if area == 0:
            raise serializers.ValidationError("A section polygon must enclose area.")
        if polygon_self_intersects(points):
            raise serializers.ValidationError(
                "A section polygon cannot self-intersect."
            )
        return value

    def validate(self, attrs):
        # `partial=True` propagates into this nested serializer on article
        # PATCHes — a section write must still be complete: the column stores
        # the shape wholesale, never a field-level merge.
        missing = {"source", "polygon", "depth_mm"} - set(attrs)
        if missing:
            raise serializers.ValidationError(
                {key: "This field is required for a complete section." for key in sorted(missing)}
            )
        if attrs.get("source") == "DXF_REFERENCE" and not (
            attrs.get("drawing_ref") or ""
        ).strip():
            raise serializers.ValidationError(
                {"drawing_ref": "A manufacturer-drawing section needs its drawing reference."}
            )
        return attrs


class ArticleWriteSerializer(StrictSerializer):
    cut_rule = ProfileCutRuleSerializer(required=False, allow_null=True)
    reinforcement_rule = ProfileReinforcementRuleSerializer(required=False, allow_null=True)
    system_id = serializers.UUIDField()
    sku = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=255)
    section = ProfileSectionSerializer(required=False, allow_null=True)
    role = serializers.ChoiceField(
        choices=[role.value for role in ProfileRole]
    )
    material = serializers.ChoiceField(choices=["PVC", "ALUMINIUM"])
    face_width_mm = decimal_field(10, 2, min_value=Decimal("0.01"))
    # Fabrication fields may be omitted or NULL — UNKNOWN is a legitimate
    # state; nothing downstream may invent a missing stock length, weld loss
    # or weight.
    commercial_length_mm = decimal_field(
        10, 2, min_value=Decimal("0.01"), required=False, allow_null=True
    )
    welding_loss_mm = decimal_field(
        10, 2, min_value=Decimal("0.00"), required=False, allow_null=True
    )
    reinforcement_sku = serializers.CharField(
        max_length=100,
        allow_null=True,
        allow_blank=True,
        required=False,
    )
    reinforcement_gap_mm = decimal_field(
        10, 2, min_value=Decimal("0.00"), required=False, allow_null=True
    )
    weight_kg_m = decimal_field(8, 4, min_value=Decimal("0.0001"), required=False, allow_null=True)
    steel_weight_kg_m = decimal_field(
        8, 4, min_value=Decimal("0.0000"), required=False, allow_null=True
    )


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
    category = serializers.ChoiceField(
        choices=list(HARDWARE_COMPONENT_CATEGORIES), default="OTHER"
    )


class KitWriteSerializer(StrictSerializer):
    def validate(self, attrs):
        effective = {**(self.instance or {}), **attrs}
        for axis in ("width", "height"):
            lower, upper = f"min_leaf_{axis}_mm", f"max_leaf_{axis}_mm"
            if lower in effective and upper in effective and effective[lower] > effective[upper]:
                raise serializers.ValidationError({upper: "Maximum must not be below minimum."})
        if effective.get("class_authority") is not None and effective.get("contents"):
            raise serializers.ValidationError({"contents": "Una clase expandible declara sus componentes en la autoridad. Deja vacío el contenido histórico para evitar dos fuentes."})
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
    class_authority = serializers.JSONField(required=False, allow_null=True)

    def validate_class_authority(self, value):
        if value is None:
            return None
        def reject_float(item):
            if isinstance(item, float):
                raise serializers.ValidationError("Usa texto decimal exacto en las reglas de herrajes.")
            if isinstance(item, dict):
                for child in item.values():
                    reject_float(child)
            elif isinstance(item, list):
                for child in item:
                    reject_float(child)
        reject_float(value)
        try:
            return parse_hardware_class(value).model_dump(mode="json")
        except (ValueError, TypeError) as error:
            raise serializers.ValidationError(str(error)) from error


class ReadinessBlockerSerializer(serializers.Serializer):
    code = serializers.CharField()
    missing_authority = serializers.CharField()
    affected = serializers.CharField()
    why = serializers.CharField()
    action = serializers.CharField()


class ReadinessLevelSerializer(serializers.Serializer):
    level = serializers.CharField()
    ok = serializers.BooleanField(required=False)
    state = serializers.CharField(required=False)
    blockers = ReadinessBlockerSerializer(many=True)


class CatalogReadinessSerializer(serializers.Serializer):
    quote_ready = serializers.BooleanField()
    scope = serializers.CharField()
    reasons = serializers.ListField(child=serializers.CharField())
    levels = ReadinessLevelSerializer(many=True, required=False)
    process_via = serializers.CharField(required=False, allow_null=True)


class ProvenanceFieldsMixin(serializers.Serializer):
    """Read-only provenance/review state — written only by import jobs and
    the technical-review endpoint, never by catalog CRUD."""

    data_provenance = serializers.ChoiceField(
        choices=["SEED_SYNTHETIC", "MANUAL", "IMPORT", "LEGACY_UNVERIFIED"],
        read_only=True,
    )
    technical_reviewed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    technical_reviewed_by = serializers.UUIDField(read_only=True, allow_null=True)
    review_pending = serializers.BooleanField(read_only=True, default=False)


class SystemResponseSerializer(ProvenanceFieldsMixin, SystemWriteSerializer):
    system_family = serializers.ChoiceField(choices=[item.value for item in SystemFamily], allow_null=True)
    readiness = CatalogReadinessSerializer(read_only=True)
    revision = serializers.CharField(read_only=True)
    read_only = serializers.BooleanField()
    id = serializers.UUIDField()
    is_global = serializers.BooleanField()
    is_demo = serializers.BooleanField()


class ArticleResponseSerializer(ProvenanceFieldsMixin, ArticleWriteSerializer):
    revision = serializers.CharField(read_only=True)
    read_only = serializers.BooleanField()
    id = serializers.UUIDField()
    section_revision = serializers.IntegerField(read_only=True)
    section_revised_at = serializers.DateTimeField(read_only=True, allow_null=True)
    section_revised_by = serializers.UUIDField(read_only=True, allow_null=True)


class BeadResponseSerializer(ProvenanceFieldsMixin, BeadWriteSerializer):
    revision = serializers.CharField(read_only=True)
    read_only = serializers.BooleanField()
    id = serializers.UUIDField()


class KitResponseSerializer(ProvenanceFieldsMixin, KitWriteSerializer):
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


class ReinforcementRowSerializer(serializers.Serializer):
    """A declared reinforcement profile bound to a parent article — steel
    authority the workspace surfaces alongside the profile it stiffens."""

    id = serializers.UUIDField()
    org_id = serializers.UUIDField(allow_null=True)
    system_id = serializers.UUIDField()
    parent_profile_article_id = serializers.UUIDField()
    sku = serializers.CharField()
    commercial_sku = serializers.CharField()
    name = serializers.CharField()
    manufacturer_name = serializers.CharField(allow_null=True)
    supplier_name = serializers.CharField(allow_null=True)
    stock_length_mm = serializers.CharField()
    thickness_mm = serializers.CharField(allow_null=True)
    ix_cm4 = serializers.CharField(allow_null=True)
    purchase_unit = serializers.CharField()
    is_default = serializers.BooleanField()
    is_active = serializers.BooleanField()


class PurchaseMappingRowSerializer(serializers.Serializer):
    """Catalog article → commercial purchase identity."""

    id = serializers.UUIDField()
    org_id = serializers.UUIDField(allow_null=True)
    profile_article_id = serializers.UUIDField()
    commercial_sku = serializers.CharField()
    manufacturer_name = serializers.CharField()
    supplier_name = serializers.CharField(allow_null=True)
    purchase_unit = serializers.CharField()
    is_active = serializers.BooleanField()


class ProcessProfileRowSerializer(serializers.Serializer):
    """The declared manufacturing process a system binds — stations, corner
    method, glazing/QC/pack flags. org_id NULL = a global authority."""

    id = serializers.UUIDField()
    org_id = serializers.UUIDField(allow_null=True)
    code = serializers.CharField()
    version = serializers.IntegerField()
    label = serializers.CharField()
    material = serializers.CharField(allow_null=True)
    product_kind = serializers.CharField(allow_null=True)
    joining_method = serializers.CharField()
    corner_process = serializers.CharField()
    cleaning_process = serializers.BooleanField()
    stations = serializers.ListField()
    operation_station_map = serializers.DictField()
    sash_assembly_required = serializers.BooleanField()
    hardware_station = serializers.BooleanField()
    glazing = serializers.BooleanField()
    qc = serializers.BooleanField()
    packaging = serializers.BooleanField()
    optional_operations = serializers.ListField()
    machine_neutral_machining = serializers.ListField()
    provenance = serializers.DictField()


class SystemWorkspaceSerializer(serializers.Serializer):
    """The §06 system home: identity + readiness + the entities bound to
    this system across every catalog domain, in one fetch."""

    system = SystemResponseSerializer()
    articles = ArticleResponseSerializer(many=True)
    beads = BeadResponseSerializer(many=True)
    kits = KitResponseSerializer(many=True)
    reinforcements = ReinforcementRowSerializer(many=True)
    purchase_mappings = PurchaseMappingRowSerializer(many=True)
    process_profile = ProcessProfileRowSerializer(allow_null=True)


class ProcessProfileOptionSerializer(serializers.Serializer):
    """Compact option for the system→process-profile binding picker."""

    id = serializers.UUIDField()
    org_id = serializers.UUIDField(allow_null=True)
    code = serializers.CharField()
    version = serializers.IntegerField()
    label = serializers.CharField()
    material = serializers.CharField(allow_null=True)
    product_kind = serializers.CharField(allow_null=True)


class ProcessProfileOptionListSerializer(serializers.Serializer):
    items = ProcessProfileOptionSerializer(many=True)


class EvidenceInputSerializer(serializers.Serializer):
    """Member-side declaration of a parameter's source. Review stamps are
    not client-writable — the server sets them on the review endpoint."""

    authority_table = serializers.ChoiceField(choices=sorted(EVIDENCE_TABLES))
    row_id = serializers.UUIDField()
    field_name = serializers.CharField(max_length=80)
    value_text = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=120)
    unit = serializers.ChoiceField(
        choices=list(EVIDENCE_UNITS), required=False, allow_null=True)
    scope = serializers.ChoiceField(
        choices=list(EVIDENCE_SCOPES), required=False, default="SYSTEM")
    applicability = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=300)
    source_document = serializers.CharField(max_length=300)
    source_page = serializers.IntegerField(
        required=False, allow_null=True, min_value=1)
    source_url = serializers.URLField(required=False, allow_null=True)


class EvidenceReviewInputSerializer(serializers.Serializer):
    review_state = serializers.ChoiceField(choices=["REVIEWED", "REJECTED"])


class EvidenceRowSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    org_id = serializers.UUIDField(allow_null=True)
    authority_table = serializers.CharField()
    row_id = serializers.UUIDField()
    field_name = serializers.CharField()
    value_text = serializers.CharField(allow_null=True)
    unit = serializers.CharField(allow_null=True)
    scope = serializers.CharField()
    applicability = serializers.CharField(allow_null=True)
    source_document = serializers.CharField()
    source_page = serializers.IntegerField(allow_null=True)
    source_url = serializers.CharField(allow_null=True)
    declared_by = serializers.UUIDField()
    declared_at = serializers.CharField()
    review_state = serializers.CharField()
    reviewed_by = serializers.UUIDField(allow_null=True)
    reviewed_at = serializers.CharField(allow_null=True)


class EvidenceListSerializer(serializers.Serializer):
    items = EvidenceRowSerializer(many=True)
