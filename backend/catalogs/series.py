"""A series sheet over the existing catalog, never a parallel numeric model."""

from copy import deepcopy
from decimal import Decimal

from django.db import connection, transaction

from authentication.errors import ContractAPIException, contract_error
from authentication.rls import catalog_backend
from catalogs import service
from catalogs.reference_protection import protect_changes
from catalogs.evidence import list_evidence
from catalogs.family_templates import family_template
from catalogs.value_origins import (
    RULE_FIELDS, annotated_cells, cell_history, cells, latest_versions,
    record_origin, resolve_origin, index_versions, index_evidence,
)
from pricing.repository import admin_write, commercial_backend, json_text, one, rows
from documents.repository import documentary_backend

RESOURCES = {"systems": service.SYSTEMS, "articles": service.ARTICLES,
    "glazing": service.BEADS, "hardware-kits": service.KITS}


def _validate(serializer_class, values):
    validator = serializer_class(data=values)
    if not validator.is_valid():
        raise contract_error(400, "catalog_validation_error", "Revisa las celdas indicadas.",
            error_extra={"fields": validator.errors})
    return validator.validated_data


def _merge(base, overrides):
    result = deepcopy(base)
    for key, value in overrides.items():
        result[key] = _merge(result[key], value) if isinstance(value, dict) and isinstance(result.get(key), dict) else value
    return result


def _annotations(defaults, overrides, source):
    supplied = set(dict(cells(overrides)))
    return {field: {"origin": "SUGGESTED", "source_ref": source}
        for field, _ in cells(defaults) if field not in supplied}


def _template_create(resource, org_id, actor_id, defaults, overrides, source):
    values = _validate(resource.serializer, _merge(defaults, overrides))
    with annotated_cells(_annotations(defaults, overrides, source)):
        return service.create(resource, org_id, values, actor_id=actor_id)


def create_from_template(org_id, actor_id, data, *, can_view_prices=False):
    try:
        template = family_template(data["template_id"], data["template_version"])
    except ValueError as error:
        raise contract_error(400, "catalog_template_missing", str(error)) from error
    with transaction.atomic():
        system = _template_create(service.SYSTEMS, org_id, actor_id, template["system"], {
            **data.get("rules", {}), "name": data["name"], "code": data["code"],
            "version": 1, "is_active": True,
            **({"manufacturer": data["manufacturer"]} if data.get("manufacturer") else {}),
        }, template["source_ref"])
        with catalog_backend():
            one("INSERT INTO public.catalog_series_setup(system_id,org_id,template_id,template_version) "
                "VALUES(%s,%s,%s,%s) RETURNING system_id", [system["id"], org_id, template["id"], template["version"]])
        profiles = {}
        for raw in data.get("profiles", []):
            supplied = {key: value for key, value in raw.items() if key != "screw_sku"}
            defaults = {"material": system["material"], **template["profile_defaults"].get(raw["role"], {})}
            if raw.get("reinforcement_sku") and raw.get("screw_sku") and template["reinforcement_defaults"]:
                defaults["reinforcement_rule"] = template["reinforcement_defaults"]
                supplied["reinforcement_rule"] = {"reinforcement_sku": raw["reinforcement_sku"],
                    "screw_sku": raw["screw_sku"], **supplied.get("reinforcement_rule", {})}
            article = _template_create(service.ARTICLES, org_id, actor_id, defaults,
                {**supplied, "system_id": system["id"]}, template["source_ref"])
            if article["sku"] in profiles:
                raise contract_error(400, "catalog_duplicate_sku", "Hay códigos de perfil repetidos.")
            profiles[article["sku"]] = article
        for raw in data.get("glazing", []):
            bead = profiles.get(raw["bead_sku"])
            if not bead or bead["role"] != "GLAZING_BEAD":
                raise contract_error(400, "catalog_bead_missing", "Elige un junquillo de esta serie.")
            supplied = {key: value for key, value in raw.items() if key != "bead_sku"}
            _template_create(service.BEADS, org_id, actor_id, {"is_active": True, **template["glazing_defaults"]},
                {**supplied, "bead_article_id": bead["id"], "system_id": system["id"]}, template["source_ref"])
        for raw in data.get("hardware", []):
            _template_create(service.KITS, org_id, actor_id,
                {"is_active": True, **template["hardware_defaults"].get(raw["opening_type"], {})},
                {**raw, "system_id": system["id"]}, template["source_ref"])
        return series_sheet(org_id, system["id"], can_view_prices=can_view_prices)


def value_text(value):
    if value is None:
        return None
    return str(value) if isinstance(value, (str, Decimal, int)) and not isinstance(value, bool) else json_text(value)


def _setup(org_id, system_id):
    from catalogs.use_levels import series_verification
    found = rows("SELECT template_id,template_version,verified_at,verified_by,verified_hash "
        "FROM public.catalog_series_setup WHERE org_id=%s AND system_id=%s", [org_id, system_id])
    setup = found[0] if found else dict.fromkeys(("template_id", "template_version", "verified_at", "verified_by", "verified_hash"))
    verified = series_verification(org_id, system_id)
    return {**setup, **{key: verified.get(key) for key in ("verified_at", "verified_by", "verified_hash")}}


def _sheet_rows(workspace):
    return {"systems": [workspace["system"]], "articles": workspace["articles"],
        "glazing": workspace["beads"], "hardware-kits": workspace["kits"]}


def _cell_projections(org_id, system_id, grouped, versions):
    evidence = index_evidence(list_evidence(org_id=org_id, system_id=system_id))
    versions = index_versions(versions)
    people = _actor_names(org_id)
    output = []
    for name, records in grouped.items():
        resource = RESOURCES[name]
        for row in records:
            values = dict(cells(row))
            for key in set(resource.fields) & RULE_FIELDS:
                if row.get(key) is None:
                    values[key] = None
            for field, value in sorted(values.items()):
                origin = resolve_origin(resource.table, row, field, value, versions, evidence) if value is not None else {
                    "origin": None, "source_ref": None, "set_by": None, "set_at": None, "version_id": None}
                output.append({"resource": name, "row_id": row["id"], "field": field,
                    "value": value_text(value), **origin,
                    "actor_name": people.get(str(origin["set_by"]))})
    return output


def _actor_names(org_id):
    # The existing tenant-checked function exposes active workshop names only.
    # It never makes auth.users or another tenant's people available to callers.
    with documentary_backend():
        people = rows("SELECT user_id,display_name FROM private.field_people(%s)", [org_id])
    return {str(person["user_id"]): person["display_name"] for person in people}


def price_items(org_id, system_id):
    # This projection is called only for OWNER and retains the existing
    # commercial role + tenant RLS. Other roles receive no purchase costs.
    from pricing.coverage import catalog_coverage

    # Coverage follows the calculator's actual cost identities, including
    # kit components, reinforcement screws and glass processes. Supplier
    # mapping codes alone are not necessarily the keys used by the engine.
    skus = sorted({item["sku"] for item in catalog_coverage(org_id, system_id=system_id)})
    if not skus:
        return []
    with commercial_backend():
        return rows("SELECT c.id,c.cost_list_id,c.sku,c.description,c.unit,c.unit_cost::text,l.currency,l.valid_from,l.valid_to "
            "FROM public.cost_list_items c JOIN public.cost_lists l ON l.id=c.cost_list_id AND l.org_id=c.org_id "
            "WHERE c.org_id=%s AND l.is_active AND c.sku=ANY(%s) "
            "ORDER BY c.sku,l.valid_from DESC,c.id", [org_id, skus])


def series_sheet(org_id, system_id, *, can_view_prices=False):
    workspace = service.system_workspace(org_id, system_id)
    grouped = _sheet_rows(workspace)
    versions = latest_versions(org_id, system_id)
    setup = _setup(org_id, system_id)
    system = workspace["system"]
    revision = service.catalog_revision({"rows": {name: [(str(row["id"]), row["revision"]) for row in records]
        for name, records in grouped.items()}, "versions": sorted(str(item["id"]) for item in versions), "setup": setup})
    return {"id": system_id, "revision": revision, "setup": setup,
        "usage": system["readiness"]["usage"],
        "cells": _cell_projections(org_id, system_id, grouped, versions),
        "tabs": {"profiles": workspace["articles"], "rules": system, "hardware": workspace["kits"],
            "glazing_colors": {"beads": workspace["beads"], "glasses": workspace["glasses"],
                "finishes": system.get("finishes") or ["WHITE"], "finish_rules": system.get("finish_authority")},
            "typologies": {"dimensional_limits": system.get("dimensional_limits") or [],
                "opening_capabilities": system.get("opening_capabilities")},
            "prices": {"can_view": can_view_prices, "items": price_items(org_id, system_id) if can_view_prices else [],
                "purchase_mappings": workspace["purchase_mappings"], "reinforcements": workspace["reinforcements"]}}}


def _lock_sheet(org_id, system_id, expected):
    service._lock_singleton_role(system_id)
    current = service.retrieve(service.SYSTEMS, org_id, system_id, lock=True)
    service._require_owned(current, org_id)
    for resource in (service.ARTICLES, service.BEADS, service.KITS):
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT id FROM public.{resource.table} WHERE system_id=%s AND org_id=%s ORDER BY id FOR UPDATE",
                [system_id, org_id])
            cursor.fetchall()
    sheet = series_sheet(org_id, system_id)
    if sheet["revision"] != expected:
        raise contract_error(409, "catalog_stale_edit", "La serie cambió. Recarga antes de guardar el lote.")
    return sheet


def _target(org_id, system_id, item, *, writable=True):
    resource = RESOURCES[item["resource"]]
    row = service.retrieve(resource, org_id, item["row_id"])
    parent = row["id"] if resource is service.SYSTEMS else row["system_id"]
    if str(parent) != str(system_id):
        raise contract_error(404, "catalog_cell_missing", "La celda no pertenece a esta serie.")
    if writable:
        service._require_owned(row, org_id)
    return resource, row


def _unique_addresses(items):
    addresses = [(item["resource"], str(item["row_id"]), item["field"]) for item in items]
    if len(addresses) != len(set(addresses)):
        raise contract_error(400, "catalog_duplicate_cell", "Una celda aparece más de una vez en el lote.")
    ordered = sorted(addresses)
    for previous, current in zip(ordered, ordered[1:]):
        if previous[:2] == current[:2] and current[2].startswith(previous[2] + "."):
            raise contract_error(400, "catalog_overlapping_cells", "Edita la regla completa o sus celdas por separado.")


def edit_cells(org_id, system_id, actor_id, data, *, can_view_prices=False):
    _unique_addresses(data["changes"])
    with transaction.atomic(), protect_changes(org_id):
        _lock_sheet(org_id, system_id, data["revision"])
        grouped = {}
        for item in data["changes"]:
            resource, row = _target(org_id, system_id, item)
            path = item["field"].split(".")
            if path[0] not in resource.fields or path[0] in {"system_id", "version"} or any(not token for token in path):
                raise contract_error(400, "catalog_cell_invalid", "La celda indicada no se puede editar.")
            group = grouped.setdefault((item["resource"], row["id"]), {"resource": resource, "row": row, "values": {}})
            values = group["values"]
            if len(path) == 1:
                if path[0] in values:
                    raise contract_error(400, "catalog_overlapping_cells", "Edita la regla completa o sus celdas por separado.")
                values[path[0]] = item["value"]
            else:
                target = values.setdefault(path[0], deepcopy(row.get(path[0])))
                for key in path[1:-1]:
                    if not isinstance(target, dict) or key not in target:
                        raise contract_error(400, "catalog_cell_invalid", "La regla indicada no contiene esta celda.")
                    target = target[key]
                if not isinstance(target, dict) or path[-1] not in target or path[-1] == "source":
                    raise contract_error(400, "catalog_cell_invalid", "La regla indicada no contiene esta celda.")
                target[path[-1]] = item["value"]
        for group in grouped.values():
            try:
                service.update(group["resource"], org_id, group["row"]["id"], group["values"],
                    expected_revision='"' + group["row"]["revision"] + '"', actor_id=actor_id)
            except ContractAPIException as error:
                if error.status_code == 400 and error.contract_code == "catalog_validation_error":
                    error.error_extra.update(resource=next(name for name, value in RESOURCES.items()
                        if value is group["resource"]), row_id=str(group["row"]["id"]))
                raise
        return series_sheet(org_id, system_id, can_view_prices=can_view_prices)


def confirm_cells(org_id, system_id, actor_id, data, *, can_view_prices=False):
    _unique_addresses(data["cells"])
    with transaction.atomic():
        sheet = _lock_sheet(org_id, system_id, data["revision"])
        indexed = {(item["resource"], str(item["row_id"]), item["field"]): item for item in sheet["cells"]}
        for item in data["cells"]:
            resource, row = _target(org_id, system_id, item)
            address = (item["resource"], str(item["row_id"]), item["field"])
            if indexed.get(address, {}).get("origin") != "SUGGESTED":
                raise contract_error(409, "catalog_cell_not_suggested", "Esta celda ya no contiene un valor sugerido.")
            record_origin(org_id=org_id, system_id=system_id, table=resource.table, row=row,
                field_name=item["field"], origin="WORKSHOP", source_ref="Confirmado por el taller", actor_id=actor_id)
        return series_sheet(org_id, system_id, can_view_prices=can_view_prices)


def edit_prices(org_id, system_id, data):
    """One audited batch, guarded against both catalog and cost changes."""
    ids = [str(item["id"]) for item in data["changes"]]
    if len(ids) != len(set(ids)):
        raise contract_error(400, "catalog_duplicate_price", "Un precio aparece más de una vez en el lote.")
    with transaction.atomic():
        _lock_sheet(org_id, system_id, data["revision"])
        allowed = {str(item["id"]) for item in price_items(org_id, system_id)}
        if not set(ids) <= allowed:
            raise contract_error(404, "catalog_price_missing", "El precio no pertenece a esta serie.")
        # Writes use the owner's existing authenticated RLS and audit trigger.
        # pricing_backend deliberately has read-only access to purchase costs.
        locked = rows("SELECT id,unit_cost FROM public.cost_list_items WHERE org_id=%s "
            "AND id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE", [org_id, ids])
        current = {str(item["id"]): item["unit_cost"] for item in locked}
        if any(current.get(str(item["id"])) != item["previous_unit_cost"] for item in data["changes"]):
            raise contract_error(409, "catalog_stale_price", "Un precio cambió. Recarga antes de guardar el lote.")
        for item in data["changes"]:
            admin_write("cost-items", org_id, {"unit_cost": item["unit_cost"]}, data["reason"], item["id"])
        return series_sheet(org_id, system_id, can_view_prices=True)


def price_history(org_id, system_id, price_id):
    service.retrieve(service.SYSTEMS, org_id, system_id)
    if str(price_id) not in {str(item["id"]) for item in price_items(org_id, system_id)}:
        raise contract_error(404, "catalog_price_missing", "El precio no pertenece a esta serie.")
    people = _actor_names(org_id)
    entries = rows("SELECT id,old_value::text AS previous_value,new_value::text AS value,"
        "actor_user_id AS set_by,created_at AS set_at,reason FROM public.price_audit_logs "
        "WHERE org_id=%s AND entity='cost_list_items' AND entity_id=%s ORDER BY created_at DESC,event_order DESC",
        [org_id, price_id])
    return {"items": [{**entry, "actor_name": people.get(str(entry["set_by"]))} for entry in entries]}


def history(org_id, system_id, item):
    service.retrieve(service.SYSTEMS, org_id, system_id)
    resource = RESOURCES[item["resource"]]
    entries = cell_history(org_id, system_id, resource.table, item["row_id"], item["field"])
    if not entries:
        _target(org_id, system_id, item, writable=False)
    people = _actor_names(org_id)
    return {"items": [{**entry, "value": value_text(entry["value"]), "previous_value": value_text(entry["previous_value"]),
        "actor_name": people.get(str(entry["set_by"]))}
        for entry in entries]}
