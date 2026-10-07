"""Read-only technical choices for the manual estimator, without cost information."""

from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.views import APIView

from catalogs.serializers import ProfileSectionSerializer, SystemDimensionalLimitSerializer
from dekopen_engine.catalog_rules import FAMILY_OPENINGS
from engine_api.repository import SystemParamsRepository
from pricing.repository import rows
from pricing.views import ERRORS, scope
from projects.views import READ_ROLES, SCHEMA, response
from catalogs.glass import load_products
from dekopen_engine.glass_composition import glass_mass_per_m2, net_glass_thickness, total_glass_thickness, relative_glass_prices
from pricing.repository import commercial_backend, PricingRepository
from dekopen_engine.commercial import PricingError
from django.utils import timezone
from dekopen_engine.openings import opening_label
from dekopen_engine.models import Opening
from engine_api.finish_serializers import FinishAuthoritySerializer


class ProfileChoiceSerializer(serializers.Serializer):
    sku = serializers.CharField()
    role = serializers.CharField()
    name = serializers.CharField()
    material = serializers.CharField()
    face_width_mm = serializers.CharField()
    section = ProfileSectionSerializer(required=False, allow_null=True)


class CouplerChoiceSerializer(serializers.Serializer):
    sku = serializers.CharField()
    name = serializers.CharField()
    material = serializers.CharField()
    face_width_mm = serializers.CharField()
    section = ProfileSectionSerializer(required=False, allow_null=True)


class GlazingBeadChoiceSerializer(serializers.Serializer):
    glass_thickness_mm = serializers.CharField()
    bead_width_mm = serializers.CharField()
    sku = serializers.CharField()
    section = ProfileSectionSerializer(required=False, allow_null=True)


def _section_json(section):
    return None if section is None else section.model_dump()


class KitComponentSerializer(serializers.Serializer):
    sku = serializers.CharField()
    name = serializers.CharField()
    qty = serializers.CharField()
    unit = serializers.CharField()
    category = serializers.CharField()


class KitChoiceSerializer(serializers.Serializer):
    sku = serializers.CharField()
    name = serializers.CharField()
    opening_type = serializers.CharField()
    # The leaf envelope the kit is rated for — Studio ranks/selects against
    # these bounds instead of treating every kit as interchangeable.
    min_leaf_width_mm = serializers.CharField()
    max_leaf_width_mm = serializers.CharField()
    min_leaf_height_mm = serializers.CharField()
    max_leaf_height_mm = serializers.CharField()
    max_leaf_weight_kg = serializers.CharField()
    # The kit's own mass — engine adds it to the leaf for the weight axis.
    weight_kg = serializers.CharField(allow_null=True)
    # The declared kit bill — HANDLE/HINGE/LOCK/ROLLER/… lines with real
    # quantities. The design surface uses it to bind visual hardware to the
    # selected kit instead of inventing positions and counts (phase-03).
    contents = KitComponentSerializer(many=True)
    class_authority = serializers.JSONField(required=False, allow_null=True)


class HandleSlotSerializer(serializers.Serializer):
    opening_type = serializers.CharField()
    leaf_slot = serializers.CharField(allow_null=True)
    leaf_handedness = serializers.CharField(allow_null=True)
    handle_domain_slot = serializers.CharField()
    host_member_side = serializers.CharField()
    horizontal_reference = serializers.CharField()
    horizontal_offset_mm = serializers.CharField()
    permitted_vertical_references = serializers.ListField(child=serializers.CharField())
    mounting_min_from_leaf_top_mm = serializers.CharField()
    mounting_max_from_leaf_top_mm = serializers.CharField()


class HandlePolicySerializer(serializers.Serializer):
    policy_id = serializers.CharField()
    version = serializers.IntegerField()
    slots = HandleSlotSerializer(many=True)


class GlassSpecChoiceSerializer(serializers.Serializer):
    sku = serializers.CharField()
    spec = serializers.CharField(allow_null=True)
    product = serializers.JSONField(required=False, allow_null=True)
    total_thickness_mm = serializers.CharField(required=False, allow_null=True)
    net_thickness_mm = serializers.CharField(required=False, allow_null=True)
    weight_kg_m2 = serializers.CharField(required=False, allow_null=True)
    compatible = serializers.BooleanField(required=False)
    review_reason = serializers.CharField(required=False, allow_blank=True)
    relative_price = serializers.CharField(required=False)


class PanelChoiceSerializer(serializers.Serializer):
    sku = serializers.CharField()
    name = serializers.CharField()
    thickness_mm = serializers.CharField()


class DesignOptionsSerializer(serializers.Serializer):
    extra_definitions = serializers.ListField(child=serializers.JSONField(),required=False)
    finish_authority = FinishAuthoritySerializer(allow_null=True, required=False)
    system_id = serializers.UUIDField()
    system_family = serializers.CharField(allow_null=True)
    is_demo = serializers.BooleanField()
    compatible_openings = serializers.ListField(child=serializers.CharField())
    opening_capabilities = serializers.ListField(child=serializers.JSONField(), required=False)
    paired_leaf_rule = serializers.JSONField(allow_null=True, required=False)
    dimensional_limits = SystemDimensionalLimitSerializer(many=True)
    profiles = ProfileChoiceSerializer(many=True)
    glazing_thicknesses = serializers.ListField(child=serializers.CharField())
    hardware_kits = KitChoiceSerializer(many=True)
    # Declared handle-mounting authority for the system — null when no policy
    # is on file. The design surface must not silently invent positions.
    handle_policy = HandlePolicySerializer(allow_null=True)
    glass_skus = serializers.ListField(child=serializers.CharField())
    glass_specs = GlassSpecChoiceSerializer(many=True)
    colors = serializers.ListField(child=serializers.CharField())
    coupler_skus = serializers.ListField(child=serializers.CharField())
    coupler_profiles = CouplerChoiceSerializer(many=True)
    glazing_beads = GlazingBeadChoiceSerializer(many=True)
    panel_skus = serializers.ListField(child=serializers.CharField())
    panel_choices = PanelChoiceSerializer(many=True)
    rebate_depth_mm = serializers.CharField()
    sash_overlap_mm = serializers.CharField()
    depth_mm = serializers.CharField()


class DesignOptionsView(APIView):
    @extend_schema(
        operation_id="project_design_options",
        responses={200: DesignOptionsSerializer, **ERRORS},
        **SCHEMA,
    )
    def get(self, request, system_id):
        with scope(request, READ_ROLES) as (_, _, org):
            repository = SystemParamsRepository()
            params = repository.load_visible(system_id, org)
            names = repository.load_article_names(system_id, org)
            couplers = repository.load_coupler_articles(system_id, org)
            handle_policy = repository.load_handle_policy(system_id, org)
            # Latest version wins; an org-scoped mapping outranks the global
            # recipe for the same technical SKU — same resolution the confirm
            # endpoint applies when it binds the glass authority.
            glass_rows = load_products(system_id, org)
            rates = {}
            with commercial_backend():
                currency = rows("SELECT currency FROM public.tenancy_organizations WHERE id=%s", [org])[0]["currency"]
                prices = PricingRepository(org, timezone.localdate(), currency)
                for item in glass_rows:
                    try:
                        rates[item["technical_sku"]] = prices.cost(item["technical_sku"], "M2")
                    except PricingError:
                        pass  # Unresolved cost is displayed explicitly below.
            relative = relative_glass_prices(rates)
            glass_choices = []
            from projects.extras import public_definition
            for item in glass_rows:
                product = item["resolved_product"]
                total = total_glass_thickness(product.composition) if product else None
                net = net_glass_thickness(product.composition) if product else None
                mass = glass_mass_per_m2(product) if product else None
                glass_choices.append({"sku": item["technical_sku"], "spec": item["glass_spec"],
                    "product": product.model_dump(mode="json") if product else None,
                    "total_thickness_mm": None if total is None else str(total),
                    "net_thickness_mm": None if net is None else str(net),
                    "weight_kg_m2": None if mass is None else str(mass),
                    "compatible": total is not None and total in params.glazing_bead_rules,
                    "review_reason": item.get("review_reason") or "",
                    "relative_price": relative.get(item["technical_sku"], "Sin dato · falta precio vigente")})
            return response(
                {
                    "system_id": system_id,
                    "extra_definitions": [public_definition(item)
                        for item in params.extra_authority.definitions if item.scope == "POSITION"] if params.extra_authority else [],
                    "finish_authority": params.finish_authority.model_dump(mode="json") if params.finish_authority else None,
                    "system_family": params.system_family.value if params.system_family else None,
                    "is_demo": bool(rows("SELECT is_demo FROM public.profile_systems WHERE id=%s", [system_id])[0]["is_demo"]),
                    "compatible_openings": sorted(opening.value for opening in FAMILY_OPENINGS[params.system_family])
                        if params.system_family else [],
                    "opening_capabilities": [{**cap.model_dump(mode="json"), "choices": [
                        {"opening": (opening := Opening(movement=cap.movement, hinge_side=hinge,
                            direction=cap.direction, leaf_role=cap.leaf_role, fixed_in_sash=cap.fixed_in_sash)).model_dump(mode="json"),
                         "label": opening_label(opening, cap.use)} for hinge in cap.hinge_sides]}
                        for cap in params.opening_capabilities],
                    "paired_leaf_rule": params.paired_leaf_rule.model_dump(mode="json") if params.paired_leaf_rule else None,
                    "dimensional_limits": [rule.model_dump() for rule in params.dimensional_limits],
                    "profiles": [
                        {
                            "sku": item.sku,
                            "role": item.role.value,
                            "name": names.get(item.sku, item.sku),
                            "material": item.material.value,
                            "face_width_mm": str(item.face_width_mm),
                            "section": _section_json(item.section),
                        }
                        for item in params.effective_profile_articles.values()
                    ],
                    "glazing_thicknesses": [
                        str(value) for value in sorted(params.glazing_bead_rules)
                    ],
                    "hardware_kits": [
                        {
                            "sku": item.sku,
                            "name": item.name,
                            "opening_type": item.opening_type,
                            "min_leaf_width_mm": str(item.min_leaf_width_mm),
                            "max_leaf_width_mm": str(item.max_leaf_width_mm),
                            "min_leaf_height_mm": str(item.min_leaf_height_mm),
                            "max_leaf_height_mm": str(item.max_leaf_height_mm),
                            "max_leaf_weight_kg": str(item.max_leaf_weight_kg),
                            "weight_kg": None if item.weight_kg is None else str(item.weight_kg),
                            "class_authority": None if item.class_authority is None else item.class_authority.model_dump(mode="json"),
                            "contents": [
                                {
                                    "sku": component.sku,
                                    "name": component.name,
                                    "qty": str(component.qty),
                                    "unit": component.unit,
                                    "category": component.category,
                                }
                                for component in item.contents
                            ],
                        }
                        for item in params.available_hardware_kits
                    ],
                    "handle_policy": (
                        None
                        if handle_policy is None
                        else {
                            "policy_id": handle_policy.policy_id,
                            "version": handle_policy.version,
                            "slots": [
                                {
                                    "opening_type": slot.opening_type.value,
                                    "leaf_slot": slot.leaf_slot,
                                    "leaf_handedness": slot.leaf_handedness,
                                    "handle_domain_slot": slot.handle_domain_slot,
                                    "host_member_side": slot.host_member_side.value,
                                    "horizontal_reference": slot.horizontal_reference,
                                    "horizontal_offset_mm": str(slot.horizontal_offset_mm),
                                    "permitted_vertical_references": [
                                        reference.value
                                        for reference in slot.permitted_vertical_references
                                    ],
                                    "mounting_min_from_leaf_top_mm": str(
                                        slot.mounting_min_from_leaf_top_mm
                                    ),
                                    "mounting_max_from_leaf_top_mm": str(
                                        slot.mounting_max_from_leaf_top_mm
                                    ),
                                }
                                for slot in handle_policy.slots
                            ],
                        }
                    ),
                    "glass_skus": [item["technical_sku"] for item in glass_rows],
                    "glass_specs": glass_choices,
                    "colors": list(params.finishes),
                    "coupler_skus": sorted(couplers),
                    "coupler_profiles": [
                        {
                            "sku": item.sku,
                            "name": names.get(item.sku, item.sku),
                            "material": item.material.value,
                            "face_width_mm": str(item.face_width_mm),
                            "section": _section_json(item.section),
                        }
                        for item in sorted(couplers.values(), key=lambda article: article.sku)
                    ],
                    "glazing_beads": [
                        {
                            "glass_thickness_mm": str(thickness),
                            "bead_width_mm": str(rule.bead_width_mm),
                            "sku": rule.bead_article.sku,
                            "section": _section_json(rule.bead_article.section),
                        }
                        for thickness, rule in sorted(params.glazing_bead_rules.items())
                    ],
                    "panel_skus": sorted(params.available_panel_rules),
                    "panel_choices": [
                        {
                            "sku": item.sku,
                            "name": item.name,
                            "thickness_mm": str(item.thickness_mm),
                        }
                        for item in sorted(
                            params.available_panel_rules.values(),
                            key=lambda panel: panel.sku,
                        )
                    ],
                    "rebate_depth_mm": str(params.rebate_depth_mm),
                    "sash_overlap_mm": str(params.sash_overlap_mm),
                    "depth_mm": str(params.depth_mm),
                }
            )
