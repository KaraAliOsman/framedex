"""Human-reviewed catalog changes with an optimistic diff and atomic publication."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import hmac
import json
from uuid import UUID, uuid5

from django.db import transaction
from rest_framework import serializers

from authentication.errors import contract_error
from authentication.rls import catalog_backend
from catalogs import evidence, service
from catalogs.serializers import (
    ArticleWriteSerializer, BeadWriteSerializer, KitWriteSerializer, ProfileCutRuleSerializer,
    ProfileReinforcementRuleSerializer, SystemDimensionalLimitSerializer,
    SystemWriteSerializer,
)
from dekopen_engine.hardware import normalize_opening_type
from dekopen_engine.models import BayOpeningType
from dekopen_engine.documentary_canonical import documentary_canonical_json_v1
from documents.repository import documentary_backend
from ingest.catalog_template import SCHEMAS, candidate
from pricing.repository import admin_write, rows, json_text
from pricing.serializers import CostItemSerializer, CostListSerializer, StrictSerializer


class ColorSkuSerializer(StrictSerializer):
    system_id = serializers.UUIDField()
    profile_article_id = serializers.UUIDField()
    finish = serializers.CharField(max_length=50)
    commercial_sku = serializers.CharField(max_length=150)
    physical_stock_identity = serializers.CharField(max_length=200)
    source = serializers.CharField(max_length=500)


class GlassMappingSerializer(StrictSerializer):
    system_id = serializers.UUIDField()
    technical_sku = serializers.CharField(max_length=100)
    purchasing_sku = serializers.CharField(max_length=100)
    manufacturer_name = serializers.CharField(max_length=255)
    glass_spec = serializers.CharField(max_length=200)
    purchase_unit = serializers.ChoiceField(choices=["EA"])
    version = serializers.IntegerField(min_value=1)
    provenance = serializers.DictField()


COLORS = service.Resource("catalog_color_skus", ColorSkuSerializer, backend_lock=True)
GLASS = service.Resource("glass_purchase_mappings", GlassMappingSerializer, backend_lock=True)
RESOURCES = {resource.table: resource for resource in
             (service.SYSTEMS, service.ARTICLES, service.BEADS, service.KITS, COLORS, GLASS)}


@dataclass
class Change:
    key: str
    sheet: str
    table: str
    row_id: str
    data: dict
    before: dict | None
    action: str


def _error(key, field, message):
    return {"key": key, "field": field, "message": message}


def _validated(serializer, data, key, errors, *, partial=False, instance=None):
    validator = serializer(data=data, partial=partial, instance=instance)
    if validator.is_valid():
        return validator.validated_data
    def describe(field, reasons):
        if isinstance(reasons, dict):
            for child, details in reasons.items():
                describe(f"{field}.{child}", details)
            return
        for reason in reasons if isinstance(reasons, list) else [reasons]:
            code = getattr(reason, "code", "invalid")
            message = {"required": "completa este campo con su fuente", "null": "falta este dato de la fuente",
                "invalid_choice": "elige una de las opciones del catálogo", "max_decimal_places": "reduce los decimales a la precisión de esta columna",
                "max_digits": "el número supera la capacidad de esta columna", "min_value": "el valor es menor que el mínimo permitido",
                "max_value": "el valor supera el máximo permitido"}.get(code)
            if message is None:
                original = str(reason)
                message = original if original.startswith(("El ", "La ", "Los ", "Las ", "Falta", "Hay ", "Este ", "Esta ", "Sin dato", "No ")) else "revisa el valor y la compatibilidad de este campo"
            label = next((column.label for columns in SCHEMAS.values() for column in columns if column.key == field), field)
            errors.append(_error(key, field, f"Columna ‘{label}’: {message}."))
    for field, reasons in validator.errors.items():
        describe(field, reasons)
    return None


def _system_payload(values):
    data = {key: value for key, value in values.items()
            if key in SystemWriteSerializer().fields and key != "source"}
    data["code"] = values["system_code"]
    sliding = {key.removeprefix("sliding."): value for key, value in values.items()
               if key.startswith("sliding.") and value is not None}
    data["sliding_parameters"] = sliding or None
    return data


def _entries(import_row, items):
    saved = import_row["candidates"]
    if isinstance(saved, str):
        saved = json.loads(saved)
    by_key = {entry["key"]: entry for entry in saved}
    output = []
    if not items or len(items) > 2000 or len({item["key"] for item in items}) != len(items):
        raise contract_error(422, "catalog_review_items_invalid", "Selecciona filas distintas para revisar.")
    for item in items:
        original = by_key.get(item["key"])
        if original is None or original.get("sheet") not in SCHEMAS:
            raise contract_error(422, "catalog_review_item_unknown", "La fila no pertenece a esta importación.")
        allowed = {column.key for column in SCHEMAS[original["sheet"]]}
        if set(item["values"]) - allowed:
            raise contract_error(422, "catalog_review_fields_invalid", "La fila contiene columnas no reconocidas.")
        reviewed = candidate(original["sheet"], item["values"], key=item["key"],
            row=original["row"], method="MANUAL", refs=original.get("fields"))
        reviewed["method"] = original["method"]
        for field, value in reviewed["values"].items():
            if value != original["values"].get(field):
                reviewed["fields"][field] = {**reviewed["fields"][field],
                    "method": "HUMAN_CORRECTION", "original": original["values"].get(field),
                    "confidence": "HUMAN_REVIEWED"}
        output.append(reviewed)
    return output


def _plan(org_id, import_row, entries, *, lock=False):
    errors = [_error(entry["key"], error["field"], error["message"])
              for entry in entries for error in entry["errors"]]
    changes: list[Change] = []
    current: dict[tuple[str, str], dict] = {}
    systems: dict[str, str] = {}
    codes = sorted({entry["values"].get("system_code") for entry in entries
                    if entry["values"].get("system_code")})
    for code in codes:
        found = rows("SELECT id FROM public.profile_systems WHERE org_id=%s AND code=%s"
                     + (" FOR UPDATE" if lock else ""), [org_id, code])
        if found:
            system = service.retrieve(service.SYSTEMS, org_id, found[0]["id"])
            current[("system", code)] = system
            systems[code] = str(system["id"])
    order = {name: index for index, name in enumerate(SCHEMAS)}
    entries.sort(key=lambda entry: order[entry["sheet"]])
    seen = set()
    list_definitions = {}
    for entry in entries:
        if entry["errors"]:
            continue
        key, sheet, values = entry["key"], entry["sheet"], entry["values"]
        code = values["system_code"]
        identity = (sheet, code, values.get("sku"), values.get("opening_type"),
                    values.get("finish"), values.get("version"), values.get("list_code"))
        if identity in seen:
            errors.append(_error(key, "system_code", "Hay dos filas para la misma autoridad. Excluye la duplicada antes de publicar."))
            continue
        seen.add(identity)
        before = None
        resource = None
        data = None
        if sheet == "Sistemas":
            before = current.get(("system", code))
            data = _validated(SystemWriteSerializer, _system_payload(values), key, errors)
            resource = service.SYSTEMS
            systems[code] = str(before["id"]) if before else str(uuid5(UUID(str(import_row["id"])), "system:" + code))
        elif code not in systems:
            errors.append(_error(key, "system_code", "No existe este sistema en tu catálogo. Incluye su fila en Sistemas."))
            continue
        elif sheet in ("Perfiles", "Roles y reglas de corte", "Refuerzos", "Colores y SKU por color"):
            sku = values["sku"]
            profile = current.get((code, sku))
            if profile is None and ("system", code) in current:
                found = rows("SELECT id FROM public.profile_articles WHERE system_id=%s AND org_id=%s AND sku=%s",
                             [systems[code], org_id, sku])
                if found:
                    profile = service.retrieve(service.ARTICLES, org_id, found[0]["id"])
                    current[(code, sku)] = profile
            if sheet == "Perfiles":
                before, resource = profile, service.ARTICLES
                raw = {name: value for name, value in values.items() if name in ArticleWriteSerializer().fields}
                raw["system_id"] = systems[code]
                data = _validated(ArticleWriteSerializer, raw, key, errors)
            elif profile is None:
                errors.append(_error(key, "sku", "No existe este perfil. Incluye primero su fila en Perfiles."))
                continue
            elif sheet in ("Roles y reglas de corte", "Refuerzos"):
                rule_serializer = ProfileCutRuleSerializer if sheet == "Roles y reglas de corte" else ProfileReinforcementRuleSerializer
                field = "cut_rule" if sheet == "Roles y reglas de corte" else "reinforcement_rule"
                rule = _validated(rule_serializer, {name: values.get(name) for name in rule_serializer().fields}, key, errors)
                if rule is not None:
                    data = {field: rule}
                    if sheet == "Roles y reglas de corte":
                        data["role"] = values["role"]
                before, resource = profile, service.ARTICLES
            else:
                if values["finish"] not in (current.get(("system", code)) or {}).get("finishes", []):
                    errors.append(_error(key, "finish", "Declara este color en la hoja Sistemas antes de asignar su SKU."))
                    continue
                found = rows("SELECT id FROM public.catalog_color_skus WHERE org_id=%s AND profile_article_id=%s AND finish=%s",
                             [org_id, profile["id"], values["finish"]]) if profile.get("revision") else []
                before = service.retrieve(COLORS, org_id, found[0]["id"]) if found else None
                resource = COLORS
                data = _validated(ColorSkuSerializer, {"system_id": systems[code], "profile_article_id": profile["id"],
                    **{name: values[name] for name in ("finish", "commercial_sku", "physical_stock_identity", "source")}}, key, errors)
        elif sheet == "Límites":
            before = current.get(("system", code))
            rule = _validated(SystemDimensionalLimitSerializer,
                {name: values.get(name) for name in SystemDimensionalLimitSerializer().fields}, key, errors)
            if rule is not None and before:
                limits = [item for item in before.get("dimensional_limits", []) if item["opening_type"] != rule["opening_type"]] + [rule]
                data = _validated(SystemWriteSerializer, {"dimensional_limits": limits}, key, errors,
                                  partial=True, instance=before)
            resource = service.SYSTEMS
        elif sheet == "Herrajes":
            resource = service.KITS
            found = rows("SELECT id FROM public.hardware_kits WHERE org_id=%s AND system_id=%s AND sku=%s",
                         [org_id, systems[code], values["sku"]]) if ("system", code) in current and current[("system", code)].get("revision") else []
            before = service.retrieve(resource, org_id, found[0]["id"]) if found else None
            raw = {name: values.get(name) for name in KitWriteSerializer().fields if name != "system_id"}
            raw["system_id"] = systems[code]
            if values["opening_type"] not in ("TURN", "TILT_TURN", "SLIDING", "DOOR", "AWNING"):
                raw["opening_type"] = normalize_opening_type(BayOpeningType(values["opening_type"]))
            data = _validated(KitWriteSerializer, raw, key, errors)
        elif sheet == "Vidrios":
            bead_fields=("glass_thickness_mm","bead_sku","bead_width_mm","gasket_interior_mm","gasket_exterior_mm","cut_add_mm")
            if any(values.get(field) is not None for field in bead_fields):
                bead=current.get((code,values.get("bead_sku")))
                if bead is None and current.get(("system",code),{}).get("revision"):
                    found=rows("SELECT id FROM public.profile_articles WHERE org_id=%s AND system_id=%s AND sku=%s",
                               [org_id,systems[code],values.get("bead_sku")])
                    bead=service.retrieve(service.ARTICLES,org_id,found[0]["id"]) if found else None
                if not bead or bead.get("role")!="GLAZING_BEAD":
                    errors.append(_error(key,"bead_sku","Incluye un perfil de rol Junquillo con este SKU en la hoja Perfiles."))
                else:
                    bead_data=_validated(BeadWriteSerializer,{
                        "system_id":systems[code],"bead_article_id":bead["id"],"is_active":True,
                        **{field:values.get(field) for field in bead_fields if field!="bead_sku"}},key,errors)
                    if bead_data is not None:
                        bead_identity=("bead",code,values["glass_thickness_mm"])
                        previous=current.get(bead_identity)
                        if previous is None and current.get(("system",code),{}).get("revision"):
                            found=rows("SELECT id FROM public.glazing_bead_matrix WHERE org_id=%s AND system_id=%s AND glass_thickness_mm=%s",
                                       [org_id,systems[code],values["glass_thickness_mm"]])
                            previous=service.retrieve(service.BEADS,org_id,found[0]["id"]) if found else None
                        bead_id=str(previous["id"]) if previous else str(uuid5(UUID(str(import_row["id"])),json_text(bead_identity)))
                        action="update" if previous else "create"
                        if previous and all(service._json_value(previous.get(field))==service._json_value(value) for field,value in bead_data.items()):
                            action="none"
                        changes.append(Change(key,sheet,service.BEADS.table,bead_id,bead_data,previous,action))
                        current[bead_identity]={**(previous or {}),**bead_data,"id":bead_id}
            resource = GLASS
            with catalog_backend():
                found = rows("SELECT g.id,EXISTS(SELECT 1 FROM public.catalog_glass_retractions r WHERE r.mapping_id=g.id) AS retracted "
                    "FROM public.glass_purchase_mappings g WHERE g.org_id=%s AND g.system_id=%s AND g.technical_sku=%s AND g.version=%s",
                    [org_id, systems[code], values["sku"], values["version"]]) if ("system", code) in current and current[("system", code)].get("revision") else []
            if found and found[0]["retracted"]:
                errors.append(_error(key, "version", "Esta versión del vidrio fue retirada. Aumenta su versión para volver a publicarlo."))
                continue
            before = service.retrieve(GLASS, org_id, found[0]["id"]) if found else None
            data = _validated(GlassMappingSerializer, {"system_id": systems[code], "technical_sku": values["sku"],
                **{name: values[name] for name in ("purchasing_sku", "manufacturer_name", "glass_spec", "version")},
                "purchase_unit": "EA", "provenance": {"source": values["source"], "method": entry["method"],
                    "catalog_import": str(import_row["id"])}}, key, errors)
        elif sheet == "Precios de costo":
            if not rows("SELECT private.pricing_role(%s,ARRAY['OWNER']) AS allowed", [org_id])[0]["allowed"]:
                errors.append(_error(key, "unit_cost", "Solo el dueño puede publicar precios de costo. Excluye esta fila para publicar el resto."))
                continue
            cost_list = _validated(CostListSerializer, {name: values[name] for name in
                ("supplier_name", "currency", "valid_from", "valid_to")}, key, errors)
            previous_list = list_definitions.setdefault(values["list_code"], cost_list)
            if previous_list != cost_list:
                errors.append(_error(key, "list_code", "Las filas de esta lista declaran proveedores, monedas o vigencias distintos."))
                continue
            cost = _validated(CostItemSerializer, {"cost_list_id": uuid5(UUID(str(import_row["id"])), values["list_code"]),
                **{name: values[name] for name in ("sku", "item_type", "unit", "unit_cost")}, "description": values["source"]}, key, errors)
            if cost is not None and cost_list is not None:
                changes.append(Change(key, sheet, "cost_list_items", "", {"list": cost_list, "item": cost,
                    "list_code": values["list_code"]}, None, "create"))
            continue
        if data is None or resource is None:
            continue
        row_id = str(before["id"]) if before else systems[code] if resource is service.SYSTEMS else str(uuid5(UUID(str(import_row["id"])), json_text(identity)))
        action = "update" if before else "create"
        if before and all(service._json_value(before.get(field)) == service._json_value(value) for field, value in data.items()):
            action = "none"
        if before and before.get("read_only"):
            errors.append(_error(key, "system_code", "Este catálogo es de lectura. Usa un código nuevo para tu copia."))
            continue
        if resource is GLASS and before and action != "none":
            errors.append(_error(key, "version", "La versión del vidrio es inmutable. Aumenta su versión para registrar la corrección."))
            continue
        changes.append(Change(key, sheet, resource.table, row_id, data, before, action))
        simulated = {**(before or {}), **data, "id": row_id}
        if resource is service.SYSTEMS:
            current[("system", code)] = simulated
        elif resource is service.ARTICLES:
            current[(code, values["sku"])] = simulated
    token = "sha256:" + sha256(documentary_canonical_json_v1({
        "import_id": str(import_row["id"]), "entries": entries,
        "changes": [change.__dict__ for change in changes], "errors": errors})).hexdigest()
    return changes, errors, token


def _get(org_id, import_id, *, lock=False):
    from ingest.catalog_service import _get as get_import
    if not lock:
        return get_import(org_id, import_id)
    with documentary_backend():
        found = rows("SELECT * FROM public.catalog_imports WHERE org_id=%s AND id=%s FOR UPDATE", [org_id, import_id])
    if not found:
        raise contract_error(404, "catalog_import_not_found", "La importación no existe.")
    return found[0]


def preview(*, org_id, import_id, items):
    row = _get(org_id, import_id)
    if row["status"] != "REVIEW_READY":
        raise contract_error(409, "catalog_review_not_ready", "Espera a que termine la extracción o abre una importación pendiente.")
    changes, errors, token = _plan(org_id, row, _entries(row, items))
    return {"review_token": token, "errors": errors, "changes": [{
        "key": change.key, "sheet": change.sheet, "action": change.action,
        "before": {field: change.before.get(field) for field in change.data} if change.before else None,
        "after": change.data} for change in changes]}


def publish(*, org_id, actor_id, import_id, items, review_token):
    from ingest.catalog_service import _public
    with transaction.atomic():
        row = _get(org_id, import_id, lock=True)
        if row["status"] == "CONFIRMED":
            return {"import": _public(row), "created": _public(row)["result"], "errors": []}
        if row["status"] != "REVIEW_READY":
            raise contract_error(409, "catalog_review_not_ready", "La importación no está lista para publicar.")
        entries = _entries(row, items)
        changes, errors, token = _plan(org_id, row, entries, lock=True)
        if errors:
            return {"import": _public(row), "created": [], "errors": errors}
        if not hmac.compare_digest(token, review_token):
            raise contract_error(409, "catalog_review_stale", "El catálogo o las filas cambiaron. Revisa el diff actualizado antes de publicar.")
        replacements, result, undo = {}, [], []
        undo_by_authority = {}
        cost_lists = {}
        by_key = {entry["key"]: entry for entry in entries}
        for change in changes:
            if change.action == "none":
                continue
            data = {name: replacements.get(str(value), value) if isinstance(value, (str, UUID)) else value
                    for name, value in change.data.items()}
            if change.table == "cost_list_items":
                code = data["list_code"]
                if code not in cost_lists:
                    cost_lists[code] = admin_write("cost-lists", org_id, {**data["list"],
                        "description": f"{code} · {row['file_name']}"}, "Publicación revisada de catálogo")
                    undo.append({"table": "cost_lists", "id": str(cost_lists[code]["id"]), "action": "deactivate"})
                item = admin_write("cost-items", org_id, {**data["item"], "cost_list_id": cost_lists[code]["id"]},
                                   "Publicación revisada de catálogo")
            else:
                resource = RESOURCES[change.table]
                if change.action == "create":
                    item = service.create(resource, org_id, data, actor_id=actor_id)
                    replacements[change.row_id] = str(item["id"])
                else:
                    target_id = replacements.get(change.row_id, change.row_id)
                    item = service.retrieve(resource, org_id, target_id, lock=True)
                    item = service.update(resource, org_id, target_id, data,
                        expected_revision='"' + item["revision"] + '"', actor_id=actor_id)
                if resource in (service.SYSTEMS, service.ARTICLES, service.BEADS, service.KITS):
                    with catalog_backend():
                        rows(f"UPDATE public.{resource.table} SET data_provenance='IMPORT',review_pending=TRUE WHERE id=%s AND org_id=%s RETURNING id",
                             [item["id"], org_id])
                    item = service.retrieve(resource, org_id, item["id"])
                    item = service.review(resource, org_id, item["id"], actor_id,
                                          expected_revision='"' + item["revision"] + '"')
                identity = (change.table, str(item["id"]))
                if identity not in undo_by_authority:
                    saved = {"table": change.table, "id": str(item["id"]), "action": change.action,
                             "before": change.before, "after_revision": item["revision"]}
                    undo_by_authority[identity] = saved
                    undo.append(saved)
                else:
                    undo_by_authority[identity]["after_revision"] = item["revision"]
                entry = by_key[change.key]
                for field, value in entry["values"].items():
                    if value is None:
                        continue
                    source = entry["fields"][field]
                    attestation = evidence.declare_evidence(org_id=org_id, actor_id=actor_id, values={
                        "authority_table": change.table, "row_id": item["id"], "field_name": field,
                        "value_text": json_text(value)[:120],
                        "source_document": f"{row['file_name']} · {source.get('ref','')}"[:300],
                        "applicability": f"{source.get('ref','')} · {source.get('method',entry['method'])} · {entry['values']['source']}"[:300]})
                    evidence.review_evidence(org_id=org_id, evidence_id=UUID(attestation["id"]), actor_id=actor_id, state="REVIEWED")
            result.append({"key": change.key, "table": change.table, "row_id": str(item["id"]), "action": change.action})
        with catalog_backend():
            rows("INSERT INTO public.catalog_import_publications(org_id,import_id,actor_id,action,review_token,candidates,changes) "
                 "VALUES(%s,%s,%s,'PUBLISH',%s,%s::jsonb,%s::jsonb) RETURNING id",
                 [org_id, import_id, actor_id, token, json_text(entries), json_text(undo)])
        with documentary_backend():
            updated = rows("UPDATE public.catalog_imports SET status='CONFIRMED',result=%s::jsonb,"
                "approved_by=%s,approved_at=now(),updated_at=now() WHERE id=%s AND org_id=%s RETURNING *",
                [json_text(result), actor_id, import_id, org_id])[0]
    return {"import": _public(updated), "created": result, "errors": []}


def undo_publication(*, org_id, actor_id, import_id):
    from ingest.catalog_service import _public
    with transaction.atomic():
        row = _get(org_id, import_id, lock=True)
        if row["status"] == "UNDONE":
            return {"import": _public(row)}
        if row["status"] != "CONFIRMED":
            raise contract_error(409, "catalog_undo_unavailable", "Esta importación no tiene una publicación que deshacer.")
        found = rows("SELECT * FROM public.catalog_import_publications WHERE org_id=%s AND import_id=%s AND action='PUBLISH' ORDER BY created_at DESC LIMIT 1",
                     [org_id, import_id])
        if not found:
            raise contract_error(409, "catalog_undo_unavailable", "La importación histórica no tiene un diff reversible.")
        publication = found[0]
        changes = publication["changes"]
        if isinstance(changes, str):
            changes = json.loads(changes)
        for change in reversed(changes):
            if change["table"] == "cost_lists":
                admin_write("cost-lists", org_id, {"is_active": False}, "Deshacer importación de catálogo", row_id=change["id"])
                continue
            resource = RESOURCES[change["table"]]
            current = service.retrieve(resource, org_id, change["id"], lock=True)
            if current["revision"] != change["after_revision"]:
                raise contract_error(409, "catalog_undo_stale", "El catálogo cambió después de publicar. Revisa su nueva versión antes de deshacer.")
            if change["action"] == "create":
                if resource is GLASS:
                    with catalog_backend():
                        rows("INSERT INTO public.catalog_glass_retractions(mapping_id,org_id,import_id,actor_id) VALUES(%s,%s,%s,%s) RETURNING mapping_id",
                             [change["id"], org_id, import_id, actor_id])
                elif resource in (COLORS, service.ARTICLES, service.BEADS):
                    service.delete(resource, org_id, change["id"], expected_revision='"' + current["revision"] + '"')
                else:
                    # Retain the authored rows and their provenance. Inactive
                    # authorities cannot feed a new calculation; sealed history
                    # and immutable glass references remain intact.
                    service.update(resource, org_id, change["id"], {"is_active": False},
                        expected_revision='"' + current["revision"] + '"', actor_id=actor_id)
            else:
                restore = {field: value for field, value in change["before"].items() if field in resource.fields}
                service.update(resource, org_id, change["id"], restore,
                    expected_revision='"' + current["revision"] + '"', actor_id=actor_id)
        with catalog_backend():
            rows("INSERT INTO public.catalog_import_publications(org_id,import_id,actor_id,action,review_token,candidates,changes) "
                 "VALUES(%s,%s,%s,'UNDO',%s,'[]'::jsonb,%s::jsonb) RETURNING id",
                 [org_id, import_id, actor_id, publication["review_token"], json_text(changes)])
        with documentary_backend():
            updated = rows("UPDATE public.catalog_imports SET status='UNDONE',updated_at=now() WHERE id=%s AND org_id=%s RETURNING *",
                           [import_id, org_id])[0]
    return {"import": _public(updated)}
