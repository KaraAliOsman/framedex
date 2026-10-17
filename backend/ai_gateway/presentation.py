"""Typed, reversible presentation edits. No executable markup or domain math."""

from __future__ import annotations

import hashlib
import json
from uuid import uuid4

from django.db import transaction
from rest_framework import serializers

from authentication.errors import contract_error
from documents.repository import documentary_backend
from pricing.repository import rows, json_text
from pricing.serializers import StrictSerializer
from projects import org_branding


class PresentationPatchSerializer(StrictSerializer):
    quotation_layout = serializers.ChoiceField(choices=("EDITORIAL", "COMPACT"), required=False)
    presentation_title = serializers.CharField(max_length=120, allow_blank=True, required=False)
    presentation_intro = serializers.CharField(max_length=1200, allow_blank=True, required=False)
    portal_heading = serializers.CharField(max_length=120, allow_blank=True, required=False)
    portal_intro = serializers.CharField(max_length=1200, allow_blank=True, required=False)
    accent = serializers.ChoiceField(choices=("TEAL", "TEAL_DARK", "GRAPHITE"), required=False)
    paper = serializers.ChoiceField(choices=("LETTER", "A4", "OFICIO"), required=False)


FIELDS = tuple(PresentationPatchSerializer().fields)
LABELS = dict(zip(FIELDS, ("Composición del PDF", "Título de la propuesta", "Presentación del PDF",
    "Título de la página del cliente", "Presentación de la página", "Tinta", "Papel"), strict=True))


def _owner(org_id, user_id):
    membership = rows("SELECT role FROM public.tenancy_memberships WHERE org_id=%s AND user_id=%s AND is_active",
                      [str(org_id), str(user_id)])
    if not membership or membership[0]["role"] != "OWNER":
        raise contract_error(403, "presentation_owner_required", "Solo el dueño puede cambiar la presentación de la empresa.")


def _state(org_id):
    current = org_branding.get_branding(org_id=org_id)
    preferences = current["document_preferences"]
    return {"preferences": {key: preferences.get(key, "") for key in FIELDS},
            "updated_at": str(current.get("updated_at") or "")}


def signature(state):
    return hashlib.sha256(json.dumps(state, sort_keys=True, default=str).encode()).hexdigest()


def operation_state(*, org_id, user_id, operation_key):
    _owner(org_id, user_id)
    result = rows("SELECT p.id, EXISTS(SELECT 1 FROM public.presentation_changes r WHERE r.reverses_id=p.id AND r.org_id=p.org_id) AS undone "
                  "FROM public.presentation_changes p WHERE p.org_id=%s AND p.actor_id=%s AND p.operation_key=%s",
                  [str(org_id), str(user_id), operation_key])
    if not result:
        return {"operation_id": None, "state": "PROPOSED"}
    return {"operation_id": str(result[0]["id"]), "state": "UNDONE" if result[0]["undone"] else "APPLIED"}


def preview(*, org_id, user_id, patch):
    _owner(org_id, user_id)
    validated = PresentationPatchSerializer(data=patch)
    validated.is_valid(raise_exception=True)
    patch = dict(validated.validated_data)
    if not patch:
        raise contract_error(400, "presentation_empty", "Indica qué parte de la presentación quieres cambiar.")
    before = _state(org_id)
    after = {**before["preferences"], **patch}
    return {"valid": True, "before_sig": signature(before), "patch": patch,
            "before": before["preferences"], "after": after,
            "changes": [{"field": key, "label": LABELS[key], "before": before["preferences"].get(key), "after": value}
                        for key, value in patch.items() if before["preferences"].get(key) != value],
            "scope": "Próximas cotizaciones y páginas de cliente. Las revisiones emitidas conservan su presentación."}


def apply(*, org_id, user_id, patch, before_sig, operation_key, reverses_id=None):
    _owner(org_id, user_id)
    request_hash = signature({"patch": patch, "before_sig": before_sig, "reverses_id": str(reverses_id or "")})
    with transaction.atomic(), documentary_backend():
        rows("SELECT id FROM public.tenancy_organizations WHERE id=%s FOR UPDATE", [str(org_id)])
        existing = rows("SELECT * FROM public.presentation_changes WHERE org_id=%s AND actor_id=%s AND operation_key=%s",
                        [str(org_id), str(user_id), operation_key])
        if existing:
            if existing[0]["request_hash"] != request_hash:
                raise contract_error(409, "presentation_key_conflict", "Esta acción ya se usó para otro cambio.")
            return {"operation_id": str(existing[0]["id"]), "applied": True, "replayed": True}
        simulation = preview(org_id=org_id, user_id=user_id, patch=patch)
        if simulation["before_sig"] != before_sig:
            raise contract_error(409, "presentation_stale", "La presentación cambió. Prepara una muestra nueva antes de aplicar.")
        before = _state(org_id)
        org_branding._save_branding(org_id=org_id, data={"document_preferences": simulation["patch"]})
        after = _state(org_id)
        identity = uuid4()
        rows("INSERT INTO public.presentation_changes(id,org_id,actor_id,operation_key,request_hash,before_state,after_state,reverses_id) "
             "VALUES(%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s) RETURNING id",
             [str(identity), str(org_id), str(user_id), operation_key, request_hash, json_text(before), json_text(after), reverses_id])
        return {"operation_id": str(identity), "applied": True, "replayed": False}


def undo(*, org_id, user_id, operation_id):
    _owner(org_id, user_id)
    with transaction.atomic(), documentary_backend():
        events = rows("SELECT * FROM public.presentation_changes WHERE id=%s AND org_id=%s AND actor_id=%s",
                      [str(operation_id), str(org_id), str(user_id)])
        if not events:
            raise contract_error(404, "presentation_change_missing", "No se encontró este cambio de presentación.")
        event = events[0]
        before = event["before_state"]
        after = event["after_state"]
        if isinstance(before, str):
            before, after = json.loads(before), json.loads(after)
        return apply(org_id=org_id, user_id=user_id, patch=before["preferences"],
                     before_sig=signature(after), operation_key=f"undo:{operation_id}", reverses_id=str(operation_id))
