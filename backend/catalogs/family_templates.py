"""Versioned workshop defaults. They never certify a manufacturer's series."""

from copy import deepcopy
import json
from pathlib import Path

from catalogs.serializers import (
    ArticleWriteSerializer, BeadWriteSerializer, KitWriteSerializer,
    ProfileReinforcementRuleSerializer, SystemWriteSerializer,
)

TEMPLATE_PATH = Path(__file__).with_name("templates") / "families-v1.json"
_KEYS = {"id", "version", "name", "origin", "source_ref", "notes", "system", "profile_defaults",
    "reinforcement_defaults", "hardware_defaults", "glazing_defaults", "prices"}


def _validate(serializer_class, values, *, partial=False):
    serializer = serializer_class(data=values, partial=partial)
    if not serializer.is_valid():
        raise ValueError(f"Invalid catalog template: {serializer.errors}")


def validate_family_templates(payload):
    if set(payload) != {"schema_version", "templates"} or payload["schema_version"] != 1:
        raise ValueError("Unsupported template schema")
    identifiers = set()
    for item in payload["templates"]:
        if set(item) != _KEYS or not isinstance(item["version"], int) or item["version"] < 1:
            raise ValueError("Invalid template shape")
        if item["origin"] != "SUGGESTED" or "revisar con fabricante" not in item["source_ref"].lower():
            raise ValueError("Templates must remain visibly suggested")
        if item["prices"] or item["id"] in identifiers:
            raise ValueError("Templates cannot invent prices or duplicate identities")
        identifiers.add(item["id"])
        _validate(SystemWriteSerializer, {**item["system"], "name": item["name"], "code": item["id"],
            "version": item["version"], "is_active": True})
        for role, values in item["profile_defaults"].items():
            _validate(ArticleWriteSerializer, {**values, "role": role}, partial=True)
        if item["reinforcement_defaults"] is not None:
            _validate(ProfileReinforcementRuleSerializer, {**item["reinforcement_defaults"],
                "reinforcement_sku": "SCHEMA-ONLY", "screw_sku": "SCHEMA-ONLY"})
        for opening, values in item["hardware_defaults"].items():
            _validate(KitWriteSerializer, {**values, "opening_type": opening}, partial=True)
        _validate(BeadWriteSerializer, item["glazing_defaults"], partial=True)
    return deepcopy(payload["templates"])


def family_templates():
    return validate_family_templates(json.loads(TEMPLATE_PATH.read_text(encoding="utf-8")))


def family_template(template_id, version=None):
    for item in family_templates():
        if item["id"] == template_id and (version is None or item["version"] == version):
            return item
    raise ValueError("La plantilla solicitada no está disponible.")
