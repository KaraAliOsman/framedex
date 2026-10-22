"""Recalculate and seal human-confirmed reference windows, never client output."""

from decimal import Decimal
from copy import deepcopy
import hashlib
import json

from django.core import signing
from django.db import transaction

from authentication.errors import contract_error
from authentication.rls import catalog_backend
from catalogs import series, service
from catalogs.use_levels import technical_fingerprint
from dekopen_engine.calibration import measurement_comparison, physical_reference, propose_calibration
from dekopen_engine.snapshot import canonical_json, result_payload
from engine_api.adapter import calculate_from_api, normalized_root_from_api
from engine_api.repository import SystemParamsRepository
from pricing.repository import json_text, rows

SALT = "catalog-reference-window-v1"


def _digest(value):
    return hashlib.sha256(canonical_json(value)).hexdigest()


def _request(data):
    return {"parametric_tree": data["parametric_tree"], "nominal_width_mm": str(data["nominal_width_mm"]),
        "nominal_height_mm": str(data["nominal_height_mm"]), "color": data["color"]}


def calculate(org_id, system_id, data):
    params = SystemParamsRepository().load_visible(system_id, org_id)
    try:
        result = calculate_from_api(params=params, **{**_request(data),
            "nominal_width_mm": Decimal(data["nominal_width_mm"]), "nominal_height_mm": Decimal(data["nominal_height_mm"])})
    except (ValueError, NotImplementedError) as error:
        raise contract_error(422, "catalog_trial_invalid", str(error)) from error
    return params, result


def _identity(org_id, system_id, data, result):
    return {"org_id": str(org_id), "system_id": str(system_id), "input": _digest(_request(data)),
        "technical_hash": technical_fingerprint(org_id, system_id), "output": _digest(physical_reference(result))}


def trial(org_id, system_id, data):
    _, result = calculate(org_id, system_id, data)
    try:
        compared = measurement_comparison(result, data.get("manual_values", {}))
    except ValueError as error:
        raise contract_error(422, "catalog_trial_measurement", str(error)) from error
    return {"measurements": compared, "result": result_payload(result),
        "calculation_token": signing.dumps(_identity(org_id, system_id, data, result), salt=SALT, compress=True)}


def proposals(org_id, system_id, data):
    params, _ = calculate(org_id, system_id, data)
    root = normalized_root_from_api(params=params, **{**_request(data),
        "nominal_width_mm": data["nominal_width_mm"], "nominal_height_mm": data["nominal_height_mm"]})
    try:
        choices = propose_calibration(root, params, finish=data["color"], measurement_key=data["measurement_key"],
            target_mm=data["target_mm"])
    except ValueError as error:
        raise contract_error(422, "catalog_trial_measurement", str(error)) from error
    sheet = series.series_sheet(org_id, system_id)
    output = []
    for proposal in choices:
        parameter = proposal.parameter
        resource = series.RESOURCES[parameter.resource]
        records = [sheet["tabs"]["rules"]] if resource is service.SYSTEMS else (
            sheet["tabs"]["profiles"] if resource is service.ARTICLES else sheet["tabs"]["glazing_colors"]["beads"])
        row = next((row for row in records if resource is service.SYSTEMS or (
            row.get("sku") == parameter.sku if resource is service.ARTICLES else
            Decimal(row["glass_thickness_mm"]) == parameter.glass_thickness_mm)), None)
        if row is None:
            continue
        path = parameter.field.split(".")
        values = {path[0]: deepcopy(row.get(path[0]))} if len(path) > 1 else {path[0]: str(proposal.value)}
        if len(path) > 1:
            target = values[path[0]]
            for part in path[1:-1]:
                target = target[part]
            target[path[-1]] = str(proposal.value)
        validator = resource.serializer(instance=row, data=values, partial=True)
        if not validator.is_valid():
            continue  # The pure engine may support a wider range than storage.
        output.append({"label": parameter.label, "previous": str(parameter.previous), "value": str(proposal.value),
            "change": {"resource": parameter.resource, "row_id": str(row["id"]), "field": parameter.field,
                "value": str(proposal.value)}, "measurements": measurement_comparison(proposal.result, {}),
            "result": result_payload(proposal.result)})
    return {"revision": sheet["revision"], "items": output}


def verify(org_id, system_id, actor_id, data):
    if data.get("confirmed") is not True:
        raise contract_error(422, "catalog_trial_confirmation", "Confirma el despiece completo antes de guardar la prueba.")
    with transaction.atomic():
        sheet = series._lock_sheet(org_id, system_id, data["revision"])
        _, result = calculate(org_id, system_id, data)
        try:
            accepted = signing.loads(data["calculation_token"], salt=SALT, max_age=1800)
        except signing.BadSignature as error:
            raise contract_error(409, "catalog_trial_stale", "Vuelve a calcular la ventana antes de confirmarla.") from error
        if accepted != _identity(org_id, system_id, data, result):
            raise contract_error(409, "catalog_trial_stale", "La serie o las medidas cambiaron. Vuelve a comparar la ventana.")
        try:
            compared = measurement_comparison(result, data.get("manual_values", {}))
        except ValueError as error:
            raise contract_error(422, "catalog_trial_measurement", str(error)) from error
        if any(item["matches"] is False for item in compared):
            raise contract_error(422, "catalog_trial_difference", "Ajusta las diferencias antes de confirmar la ventana.")
        if data.get("confirm_suggested"):
            suggested = [{key: item[key] for key in ("resource", "row_id", "field")}
                for item in sheet["cells"] if item["origin"] == "SUGGESTED"]
            if suggested:
                series.confirm_cells(org_id, system_id, actor_id, {"revision": sheet["revision"], "cells": suggested})
        fingerprint = technical_fingerprint(org_id, system_id)
        with catalog_backend():
            saved = rows("INSERT INTO public.catalog_reference_windows(org_id,system_id,input,expected_output,technical_hash,verified_by) "
                "VALUES(%s,%s,%s::jsonb,%s::jsonb,%s,%s) RETURNING id,verified_at,verified_by",
                [org_id, system_id, json_text({**_request(data), "manual_values": {
                    key: str(value) for key, value in data.get("manual_values", {}).items()}}),
                    json_text(physical_reference(result)), fingerprint, actor_id])[0]
            rows("INSERT INTO public.catalog_series_setup(system_id,org_id,verified_at,verified_by,verified_hash,wizard_step,progress_revision) "
                "VALUES(%s,%s,now(),%s,%s,5,2) ON CONFLICT(system_id) DO UPDATE SET "
                "verified_at=now(),verified_by=EXCLUDED.verified_by,verified_hash=EXCLUDED.verified_hash,wizard_step=5,"
                "progress_revision=catalog_series_setup.progress_revision+1 RETURNING system_id",
                [system_id, org_id, actor_id, fingerprint])
        return {**saved, "system_id": system_id, "technical_hash": fingerprint}


def references(org_id, system_id):
    service.retrieve(service.SYSTEMS, org_id, system_id)
    with catalog_backend():
        found = rows("SELECT id,input::text,expected_output::text,technical_hash,verified_by,verified_at "
            "FROM public.catalog_reference_windows WHERE org_id=%s AND system_id=%s ORDER BY verified_at,id", [org_id, system_id])
    return [{**row, "input": json.loads(row["input"]), "expected_output": json.loads(row["expected_output"])} for row in found]


def progress(org_id, system_id, data=None):
    system = service.retrieve(service.SYSTEMS, org_id, system_id)
    if data is not None:
        service._require_owned(system, org_id)
    with catalog_backend():
        if data is not None:
            rows("INSERT INTO public.catalog_series_setup(system_id,org_id) VALUES(%s,%s) ON CONFLICT DO NOTHING RETURNING system_id",
                [system_id, org_id])
            updated = rows("UPDATE public.catalog_series_setup SET wizard_step=%s,wizard_state=%s::jsonb,progress_revision=progress_revision+1 "
                "WHERE system_id=%s AND org_id=%s AND progress_revision=%s RETURNING system_id",
                [data["step"], json_text(data["state"]), system_id, org_id, data["revision"]])
            if not updated:
                raise contract_error(409, "catalog_progress_stale", "El alta cambió en otra pantalla. Recupera su progreso antes de continuar.")
        found = rows("SELECT wizard_step AS step,wizard_state::text AS state,progress_revision AS revision "
            "FROM public.catalog_series_setup WHERE system_id=%s AND org_id=%s", [system_id, org_id])
    return {**found[0], "state": json.loads(found[0]["state"])} if found else {"step": 1, "state": {}, "revision": 1}
