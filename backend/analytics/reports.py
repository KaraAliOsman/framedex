"""Append-only closure of an OT against its current stock/station evidence."""

from datetime import date, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

from authentication.errors import contract_error
from dekopen_engine.analytics import actual_cost, bar_reading, remnant_quantity, decimal_text
from documents.repository import decoded, documentary_backend, json_text, one, rows
from analytics.today import local_today

SQL = Path(__file__).with_name("sql")


def load(org, start, end, *, order_id=None):
    parameters = {
        "org": str(org),
        "start": start,
        "end": end,
        "order_id": str(order_id) if order_id else None,
    }
    with documentary_backend():
        values = {
            key: rows((SQL / f"{key}.sql").read_text(encoding="utf-8"), parameters)
            if order_id is None or key not in ("emissions", "visits", "incidents")
            else []
            for key in (
                "emissions",
                "orders",
                "materials",
                "steps",
                "remnants",
                "visits",
                "incidents",
            )
        }
        for source in values.values():
            for row in source:
                for key in (
                    "snapshot_json",
                    "payload_json",
                    "evidence_json",
                    "result_json",
                    "context_json",
                ):
                    if key in row and row[key] is not None:
                        row[key] = decoded(row[key])
        return values


def preferences(org):
    found = rows("SELECT period_days FROM public.analytics_preferences WHERE org_id=%s", [org])
    return {"period_days": int(found[0]["period_days"]) if found else 30}


def period(org, start=None, end=None):
    last = end or local_today(org)
    first = start or last - timedelta(days=preferences(org)["period_days"] - 1)
    if first > last:
        raise contract_error(
            422,
            "analytics_period_invalid",
            "La fecha inicial debe ser anterior al cierre del período.",
        )
    return first, last


def update_preferences(org, actor, days):
    rows(
        "INSERT INTO public.analytics_preferences(org_id,period_days,updated_by) VALUES(%s,%s,%s) "
        "ON CONFLICT(org_id) DO UPDATE SET period_days=EXCLUDED.period_days,updated_by=EXCLUDED.updated_by,updated_at=now() RETURNING org_id",
        [org, days, actor],
    )
    return preferences(org)


def source_rows(order, sources):
    order_id = str(order["id"])
    materials = [dict(row) for row in sources["materials"] if str(row["order_id"]) == order_id]
    for row in materials:
        row["id"] = str(row["id"])
        row["quantity"] = str(row["quantity"])
    for row in sources["remnants"]:
        if str(row["consumed_order_id"]) != order_id or row["status"] != "CONSUMED":
            continue
        quantity = remnant_quantity(
            **{key: row[key] for key in ("kind", "length_mm", "width_mm", "height_mm")}
        )
        materials.append(
            {
                "id": str(row["id"]),
                "kind": "REMNANT",
                "quantity": str(quantity),
                "unit": "M" if row["kind"] == "BAR" else "M2",
                "sku": row["code"] or "Retazo sin dirección histórica",
                "name": "Retazo consumido",
                "note": "Inventario físico de retazos",
            }
        )
    steps = [
        {**row, "id": str(row["id"])}
        for row in sources["steps"]
        if str(row["order_id"]) == order_id
    ]
    produced = [
        row
        for row in sources["remnants"]
        if str(row["origin_order_id"]) == order_id and row["status"] != "SCRAPPED"
    ]
    state = {
        "order": order_id,
        "version": str(order["project_version_id"]),
        "materials": [
            {key: row[key] for key in ("id", "kind", "quantity", "unit")} for row in materials
        ],
        "steps": [
            {key: row[key] for key in ("id", "status", "started_at", "finished_at")}
            for row in steps
        ],
        "produced": [
            {key: row[key] for key in ("id", "kind", "length_mm", "width_mm", "height_mm")}
            for row in produced
        ],
    }
    fingerprint = sha256(json_text(state).encode()).hexdigest()
    return materials, steps, produced, fingerprint


def report_cost(order, sources):
    materials, steps, produced, fingerprint = source_rows(order, sources)
    evidence = order.get("evidence_json") or {}
    stale = bool(evidence and fingerprint != order["source_fingerprint"])
    material_rates = {str(row["id"]): row for row in evidence.get("materials", [])}
    station_rates = {str(row["id"]): row for row in evidence.get("labor", [])}
    result = actual_cost(
        materials=[
            {
                **row,
                **{
                    key: decimal_text(material_rates.get(row["id"], {}).get(key))
                    for key in ("unit_cost", "waste_quantity")
                },
            }
            for row in materials
        ],
        labor=[
            {
                **row,
                **{
                    key: decimal_text(station_rates.get(row["id"], {}).get(key))
                    for key in ("hours", "hourly_rate")
                },
            }
            for row in steps
        ],
        other=evidence.get("other_cost"),
        credit=evidence.get("reusable_credit"),
        closed=bool(evidence.get("closed")) and not stale,
    )
    if stale:
        result["causes"].insert(
            0,
            "El inventario o las estaciones cambiaron después del cierre. Registra una revisión de costos.",
        )
    return result


def order_read(org, order_id, sources=None):
    data = sources or load(org, date(1900, 1, 1), date(9999, 12, 31), order_id=order_id)
    candidates = [row for row in data["orders"] if str(row["id"]) == str(order_id)]
    if not candidates:
        raise contract_error(
            404, "analytics_order_not_found", "La OT no está disponible para tu organización."
        )
    order = candidates[0]
    materials, steps, produced, fingerprint = source_rows(order, data)
    version = one(
        "SELECT snapshot_json->'project'->>'currency' AS currency FROM public.project_versions WHERE id=%s AND org_id=%s",
        [order["project_version_id"], org],
    )
    currency = version["currency"]
    rates = order.get("evidence_json") or {}
    material_rates = {str(row["id"]): row for row in rates.get("materials", [])}
    station_rates = {str(row["id"]): row for row in rates.get("labor", [])}
    return {
        "id": str(order["id"]),
        "code": order["code"],
        "project_id": str(order["project_id"]),
        "status": order["status"],
        "currency": currency,
        "revision": order.get("report_revision") or 0,
        "source_fingerprint": fingerprint,
        "source": order.get("source") or "",
        "reason": order.get("reason") or "",
        "materials": [
            {
                **{key: row.get(key) for key in ("id", "kind", "quantity", "unit", "sku", "name")},
                **{
                    key: decimal_text(material_rates.get(row["id"], {}).get(key))
                    for key in ("unit_cost", "waste_quantity")
                },
            }
            for row in materials
        ],
        "labor": [
            {
                **{key: row[key] for key in ("id", "label", "status")},
                **{
                    key: decimal_text(station_rates.get(row["id"], {}).get(key))
                    for key in ("hours", "hourly_rate")
                },
            }
            for row in steps
        ],
        "produced": [
            {"id": str(row["id"]), "code": row["code"] or "Retazo sin dirección histórica"}
            for row in produced
        ],
        "other_cost": decimal_text(rates.get("other_cost")),
        "reusable_credit": decimal_text(rates.get("reusable_credit")),
        "closed": bool(rates.get("closed")),
        "bars": {
            key: value if isinstance(value, bool) else decimal_text(value)
            for key, value in (rates.get("bars") or {}).items()
        },
        "result": report_cost(order, data),
    }


def save_report(org, actor, order_id, data, *, preview=False):
    one(
        "SELECT id FROM public.orders WHERE org_id=%s AND id=%s AND order_type='WORKSHOP_OT' FOR UPDATE",
        [org, order_id],
    )
    request_hash = sha256(json_text(data).encode()).hexdigest()
    prior = rows(
        "SELECT request_hash,order_id,response_json FROM public.production_actual_reports WHERE org_id=%s AND request_key=%s",
        [org, data["request_key"]],
    )
    if prior:
        if prior[0]["request_hash"] != request_hash or str(prior[0]["order_id"]) != str(order_id):
            raise contract_error(
                409,
                "analytics_replay_conflict",
                "Ese registro ya se usó con otros datos. Actualiza la OT y vuelve a revisar.",
            )
        return decoded(prior[0]["response_json"])
    sources = load(org, date(1900, 1, 1), date(9999, 12, 31), order_id=order_id)
    current = order_read(org, order_id, sources)
    if (
        data["expected_revision"] != current["revision"]
        or data["source_fingerprint"] != current["source_fingerprint"]
    ):
        raise contract_error(
            409,
            "analytics_report_stale",
            "La OT cambió mientras revisabas. Actualiza consumos y estaciones antes de registrar.",
        )
    if data["currency"] != current["currency"]:
        raise contract_error(
            422,
            "analytics_currency",
            "Registra los costos en la moneda de la revisión emitida; convierte con un tipo de cambio con referencia explícita antes de ingresarlos.",
        )
    for key in ("materials", "labor"):
        ids = [str(row["id"]) for row in data[key]]
        if len(ids) != len(set(ids)) or set(ids) != {row["id"] for row in current[key]}:
            raise contract_error(
                422,
                "analytics_source_scope",
                "Cada consumo y estación de esta OT debe figurar una sola vez. Actualiza y revisa la lista completa.",
            )
    if (
        not current["produced"]
        and data["reusable_credit"] is not None
        and Decimal(str(data["reusable_credit"])) != 0
    ):
        raise contract_error(
            422,
            "analytics_credit_source",
            "La OT no tiene retazos producidos que respalden ese crédito de inventario.",
        )
    if data["closed"] and current["status"] not in (
        "COMPLETED",
        "DISPATCHED",
        "INSTALLED",
        "CANCELLED",
    ):
        raise contract_error(
            422,
            "analytics_order_unfinished",
            "Termina o cancela la OT antes de confirmar el cierre de costos.",
        )
    evidence = {
        key: data[key]
        for key in ("materials", "labor", "other_cost", "reusable_credit", "closed", "bars")
    }
    virtual = next(row for row in sources["orders"] if str(row["id"]) == str(order_id))
    virtual.update(evidence_json=evidence, source_fingerprint=current["source_fingerprint"])
    try:
        result = report_cost(virtual, sources)
        bar_reading(**evidence["bars"])
    except (ValueError, ArithmeticError) as error:
        raise contract_error(
            422,
            "analytics_evidence_invalid",
            "Revisa la merma, las tarifas y el balance de corte: no pueden duplicar material ni dejar un saldo negativo.",
        ) from error
    if data["closed"] and result["causes"]:
        raise contract_error(422, "analytics_cost_incomplete", " ".join(result["causes"]))
    if preview:
        return {
            **current,
            **evidence,
            "source": data["source"],
            "reason": data["reason"],
            "result": result,
            "previous_result": current["result"],
        }
    if not data.get("confirmed"):
        raise contract_error(
            422,
            "analytics_confirmation",
            "Revisa el cierre de costos y confirma antes de registrar una revisión.",
        )
    virtual.update(
        report_revision=current["revision"] + 1, source=data["source"], reason=data["reason"]
    )
    response = order_read(org, order_id, sources)
    rows(
        "INSERT INTO public.production_actual_reports(org_id,order_id,revision,request_key,request_hash,source_fingerprint,currency,evidence_json,result_json,response_json,source,reason,created_by) "
        "VALUES(%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s,%s,%s) RETURNING id",
        [
            org,
            order_id,
            current["revision"] + 1,
            data["request_key"],
            request_hash,
            current["source_fingerprint"],
            data["currency"],
            json_text(evidence),
            json_text(result),
            json_text(response),
            data["source"],
            data["reason"],
            actor,
        ],
    )
    return response
