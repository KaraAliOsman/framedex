"""How the interface looks for one person in one workshop.

Presentation only — density, text size, motion, the tab a work opens on,
the side rail. The assistant may change it for the person (a reversible
step with a receipt); nothing here reaches a work, a price, a document or
another person. Unknown keys and values are refused, never stored.
"""

from __future__ import annotations

import json
from uuid import UUID

from rest_framework import serializers

from authentication.errors import contract_error
from pricing.repository import rows

DEFAULTS = {
    "density": "office",
    "text_size": "normal",
    "reduce_motion": False,
    "project_tab": "positions",
    "rail_collapsed": False,
}


class InterfacePreferencesSerializer(serializers.Serializer):
    density = serializers.ChoiceField(choices=["office", "workshop"], required=False)
    text_size = serializers.ChoiceField(choices=["normal", "large"], required=False)
    reduce_motion = serializers.BooleanField(required=False)
    project_tab = serializers.ChoiceField(choices=["positions", "quote", "production", "activity"],
                                          required=False)
    rail_collapsed = serializers.BooleanField(required=False)

    def validate(self, attrs):
        unknown = set(self.initial_data or {}) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({key: "Preferencia desconocida." for key in sorted(unknown)})
        return attrs


def clean(values: object) -> dict:
    serializer = InterfacePreferencesSerializer(data=values if isinstance(values, dict) else {})
    if not isinstance(values, dict) or not serializer.is_valid():
        raise contract_error(400, "interface_preferences_invalid", "Revisa las preferencias de la interfaz.",
                             error_extra={"fields": serializer.errors if isinstance(values, dict) else {}})
    return dict(serializer.validated_data)


def get_preferences(org_id: UUID, user_id: UUID) -> dict:
    found = rows("SELECT preferences::text AS preferences FROM public.member_interface_preferences "
                 "WHERE org_id=%s AND user_id=%s", [org_id, user_id])
    stored = json.loads(found[0]["preferences"]) if found else {}
    return {**DEFAULTS, **{key: value for key, value in stored.items() if key in DEFAULTS}}


def save_preferences(org_id: UUID, user_id: UUID, changes: dict) -> dict:
    """Merges validated changes over the person's current preferences."""
    merged = {**get_preferences(org_id, user_id), **clean(changes)}
    rows("INSERT INTO public.member_interface_preferences(org_id,user_id,preferences,updated_at) "
         "VALUES(%s,%s,%s::jsonb,now()) ON CONFLICT (org_id,user_id) DO UPDATE SET "
         "preferences=EXCLUDED.preferences,updated_at=now() RETURNING org_id",
         [org_id, user_id, json.dumps(merged)])
    return merged
