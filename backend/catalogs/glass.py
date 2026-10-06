"""Catalog glass authority; structured recipes are additive immutable versions."""

from __future__ import annotations

from hashlib import sha256
from decimal import Decimal
import json
from uuid import UUID, uuid4

from django.db import transaction
from rest_framework import serializers

from authentication.errors import contract_error
from authentication.rls import catalog_backend
from catalogs import service
from dekopen_engine.glass import migrate_glass_spec
from dekopen_engine.glass_composition import (
    GlassProduct, GlassSafetyRule, GlassBilling, GlassLimits, GlassProperties,
    SupplierValue, SupplierSafety,
    assess_glass, assess_glass_safety,
)
from pricing.repository import rows, json_text
from pricing.serializers import StrictSerializer


class GlassCompositionWriteSerializer(StrictSerializer):
    mapping_id = serializers.UUIDField()
    system_id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=["PARSED", "UNKNOWN"])
    product = serializers.JSONField(allow_null=True)
    review_reason = serializers.CharField(max_length=1000, allow_blank=True)

    def validate_product(self, value):
        if value is None:
            return None
        try:
            return GlassProduct.model_validate_json(json_text(value)).model_dump(mode="json")
        except ValueError as error:
            raise serializers.ValidationError(str(error)) from error


COMPOSITIONS = service.Resource("catalog_glass_compositions", GlassCompositionWriteSerializer, backend_lock=True)


def recipe_payload(values, *, synthetic=False):
    """Same source/candidates pathway as the original D01 catalog import."""
    migrated = migrate_glass_spec(values.get("glass_spec"))
    if migrated["status"] == "UNKNOWN":
        return {"status": "UNKNOWN", "product": None, "review_reason": migrated["reason"]}
    source = values.get("source") or "Notación histórica; datos de proveedor pendientes de revisión"
    properties = {}
    for key in ("ug", "solar_factor", "light_transmittance", "weight_kg_m2"):
        if values.get(key) is not None:
            properties[key] = SupplierValue(value=Decimal(str(values[key])), source=source)
    if values.get("safety_class"):
        properties["safety_class"] = SupplierSafety(value=values["safety_class"], source=source)
    limits = {key: values[key] for key in GlassLimits.model_fields if values.get(key) is not None and key != "source"}
    billing = {key: values[key] for key in GlassBilling.model_fields if values.get(key) is not None and key != "source"}
    product = GlassProduct.model_validate_json(json_text({
        "name": values.get("name") or values.get("glass_spec") or "Vidrio pendiente de revisión",
        "composition": migrated["composition"], "source": source, "synthetic": synthetic,
        "properties": GlassProperties(**properties).model_dump(mode="json"),
        "limits": {**limits, "source": source} if limits else {},
        "billing": {**billing, "source": source} if billing else {},
    }))
    return {"status": "PARSED", "product": product.model_dump(mode="json"), "review_reason": migrated["reason"]}


def product_for_mapping(mapping):
    """The legacy fallback parses metadata without mutating a sealed design."""
    value = mapping.get("product")
    if isinstance(value, str):
        value = json.loads(value)
    legacy_spec = mapping.get("legacy_spec")
    if legacy_spec is None and mapping.get("status") is None:
        # Mappings inserted after D02 have no backfilled composition row. Their
        # historical notation must resolve identically on discovery and save.
        legacy_spec = mapping.get("glass_spec")
    if not value and legacy_spec is not None:
        value = recipe_payload({"glass_spec": legacy_spec}, synthetic=mapping.get("is_demo", False))["product"]
    if value is None:
        return None
    product = GlassProduct.model_validate_json(json_text(value))
    return product.model_copy(update={"authority_id": str(mapping["mapping_id"])})


def load_products(system_id, org_id):
    found = rows(
        "SELECT DISTINCT ON (g.technical_sku) g.id AS mapping_id,g.technical_sku,g.glass_spec,"
        "g.purchasing_sku,g.manufacturer_name,g.version,c.product::text,c.status,c.review_reason,"
        "c.legacy_spec,s.is_demo FROM public.glass_purchase_mappings g "
        "JOIN public.profile_systems s ON s.id=g.system_id "
        "LEFT JOIN public.catalog_glass_compositions c ON c.mapping_id=g.id "
        "WHERE g.system_id=%s AND (g.org_id=%s OR g.org_id IS NULL) "
        "ORDER BY g.technical_sku,g.org_id NULLS LAST,g.version DESC",
        [system_id, org_id],
    )
    # Historical rows inserted by old clients need the same deterministic
    # parse preview, still with no technical certification inferred.
    for mapping in found:
        mapping["resolved_product"] = product_for_mapping(mapping)
    return found


def validate_design_products(org_id, system_id, tree):
    declared = []

    def visit(value):
        if not isinstance(value, dict):
            return
        if value.get("type") == "BAY" and (value.get("glass_product") is not None or value.get("glass_article_sku")):
            declared.append(value)
        for child in value.get("children") or []:
            visit(child)

    if isinstance(tree, dict) and tree.get("version") == "product-v2":
        for module in tree["assembly"]["modules"]:
            visit(module["tree"])
    else:
        visit(tree)
    if not declared:
        return
    # Resolve by immutable ID, not by the currently latest version: a newer
    # catalog does not supersede the authority a saved position declared.
    for node in declared:
        value = node.get("glass_product")
        if value is None:
            # Only historical notations retain the old API contract. New
            # structured SKUs cannot drop their recipe to avoid billing/limits.
            found = rows("SELECT c.id,c.legacy_spec FROM public.glass_purchase_mappings g "
                "LEFT JOIN public.catalog_glass_compositions c ON c.mapping_id=g.id "
                "WHERE g.system_id=%s AND g.technical_sku=%s AND (g.org_id=%s OR g.org_id IS NULL) "
                "ORDER BY g.org_id NULLS LAST,g.version DESC LIMIT 1",
                [system_id, node.get("glass_article_sku"), org_id])
            if found and found[0]["id"] is not None and found[0]["legacy_spec"] is None:
                raise contract_error(422, "glass_authority_required", "Vuelve a seleccionar el producto con su composición del catálogo.")
            continue
        if not isinstance(value, dict) or not value.get("authority_id"):
            raise contract_error(422, "glass_authority_required", "Publica la composición en el catálogo antes de asignarla al vano.")
        try:
            UUID(value["authority_id"])
        except (ValueError, TypeError, AttributeError) as error:
            raise contract_error(400, "glass_authority_invalid", "Vuelve a seleccionar el producto del catálogo.") from error
        found = rows("SELECT g.id AS mapping_id,g.technical_sku,g.glass_spec,c.product::text,c.status,c.legacy_spec,s.is_demo "
            "FROM public.glass_purchase_mappings g JOIN public.profile_systems s ON s.id=g.system_id "
            "LEFT JOIN public.catalog_glass_compositions c ON c.mapping_id=g.id "
            "WHERE g.id=%s AND g.system_id=%s AND (g.org_id=%s OR g.org_id IS NULL)",
            [value["authority_id"], system_id, org_id])
        if not found or found[0]["technical_sku"] != node.get("glass_article_sku"):
            raise contract_error(422, "glass_authority_required", "El vidrio no pertenece al catálogo visible de esta serie.")
        expected = product_for_mapping(found[0])
        try:
            supplied = GlassProduct.model_validate_json(json_text(value))
        except ValueError as error:
            raise contract_error(400, "glass_composition_invalid", "Revisa la composición del vidrio.") from error
        if expected != supplied:
            raise contract_error(409, "glass_authority_changed", "La composición difiere de su versión de catálogo. Vuelve a seleccionar el producto.")


def enforce_design_glass(org_id, tree, result, params):
    """Always check persisted, engine-derived dimensions and complete leaf mass."""
    nodes = {}

    def visit(value, prefix=""):
        if value.get("type") == "BAY":
            nodes[prefix + value["id"]] = value
        for child in value.get("children") or []:
            visit(child, prefix)

    if tree.get("version") == "product-v2":
        for module in tree["assembly"]["modules"]:
            visit(module["tree"], module["id"] + "|")
    else:
        visit(tree)
    rules = load_safety_rules(org_id)
    findings = []
    for piece in result.glasses:
        node = nodes.get(piece.bay_id)
        if not node:
            continue
        door = node.get("opening_type") in ("DOOR_ENTRY", "DOOR_DOUBLE")
        sidelight = node.get("is_sidelight", False)
        sill_mm = Decimal(node["sill_height_mm"]) if node.get("sill_height_mm") is not None else None
        if node.get("glass_product") is None:
            # The old BOM remains unchanged. New writes still satisfy mandatory
            # safety; a legacy trade name does not establish a safety class.
            assessments = assess_glass_safety(safety_class=None, synthetic=False,
                width_mm=piece.width_mm, height_mm=piece.height_mm, rules=rules,
                door=door, sidelight=sidelight, sill_mm=sill_mm)
            findings.extend({**finding.model_dump(mode="json"), "bay_id": piece.bay_id} for finding in assessments)
            continue
        product = GlassProduct.model_validate_json(json_text(node["glass_product"]))
        weight = next((value.total_weight_kg for value in result.leaf_weights if value.bay_id == piece.bay_id), None)
        kit = next((value for value in params.available_hardware_kits if value.sku == node.get("hardware_set_sku")), None)
        assessments = assess_glass(product, width_mm=piece.width_mm, height_mm=piece.height_mm,
            bead_thicknesses=tuple(params.glazing_bead_rules), rules=rules,
            door=door, sidelight=sidelight, sill_mm=sill_mm,
            leaf_weight_kg=weight, hardware_limit_kg=kit.max_leaf_weight_kg if kit else None)
        findings.extend({**finding.model_dump(mode="json"), "bay_id": piece.bay_id} for finding in assessments)
    blocked = next((finding for finding in findings if finding["blocking"]), None)
    if blocked:
        raise contract_error(422, "glass_rule_required", blocked["message"], error_extra={"glass_findings": findings})
    return findings


def rules_snapshot(org_id):
    from catalogs.demo_glass import demo_safety_rules
    found = rows("SELECT payload::text,revision FROM public.glass_safety_rule_sets WHERE org_id=%s", [org_id])
    payload = json.loads(found[0]["payload"]) if found else []
    token = "sha256:" + sha256(json_text(payload).encode()).hexdigest()
    return {"items": payload, "revision": token, "configured": bool(found), "examples": demo_safety_rules()}


def load_safety_rules(org_id):
    return tuple(GlassSafetyRule.model_validate_json(json_text(item)) for item in rules_snapshot(org_id)["items"])


def replace_safety_rules(org_id, actor_id, payload, expected):
    try:
        items = [GlassSafetyRule.model_validate_json(json_text(item)) for item in payload]
    except (ValueError, TypeError) as error:
        raise contract_error(400, "glass_rules_invalid", "Completa cada regla y su fuente. Las reglas oficiales requieren la norma aportada por tu organización.") from error
    if len(items) > 200 or len({item.code for item in items}) != len(items):
        raise contract_error(400, "glass_rules_invalid", "Usa códigos distintos y un máximo de 200 reglas.")
    with transaction.atomic(), catalog_backend():
        # One org lock also serializes the initial empty-set write.
        rows("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", [str(org_id)])
        current = rules_snapshot(org_id)
        if expected != '"' + current["revision"] + '"':
            raise contract_error(409, "glass_rules_stale", "Las reglas cambiaron. Revisa la versión actual antes de aplicar.")
        normalized = json_text([item.model_dump(mode="json") for item in items])
        result = rows("INSERT INTO public.glass_safety_rule_sets(org_id,payload) VALUES(%s,%s::jsonb) "
            "ON CONFLICT(org_id) DO UPDATE SET payload=excluded.payload,revision=glass_safety_rule_sets.revision+1 "
            "RETURNING revision", [org_id, normalized])[0]
        rows("INSERT INTO public.glass_safety_rule_revisions(id,org_id,actor_id,revision,payload) "
             "VALUES(%s,%s,%s,%s,%s::jsonb) RETURNING id", [uuid4(), org_id, actor_id, result["revision"], normalized])
    return rules_snapshot(org_id)
