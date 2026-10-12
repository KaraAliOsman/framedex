"""Decision analytics. SQL resolves evidence; the pure engine computes values."""

from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from dekopen_engine.analytics import (
    average,
    bar_reading,
    driver_sources,
    margin_bridge,
    ratio,
    total,
)
from documents.repository import rows
from analytics import reports

GROUPS = ("sales", "margin", "production", "field")
PHASES = {
    "DRAFT": "Borrador",
    "QUOTED": "Cotizada",
    "APPROVED": "Aprobada",
    "IN_PRODUCTION": "En fabricación",
    "COMPLETED": "Completada",
    "CANCELLED": "Cancelada",
}
INCIDENTS = {
    "DAMAGE": "Daño",
    "MEASURE": "Medida",
    "MISSING": "Faltante",
    "ADJUSTMENT": "Regulación",
    "WARRANTY": "Garantía",
    "SERVICE": "Servicio",
}
DRIVERS = {
    "materials": "Material útil y valoración",
    "waste": "Merma",
    "labor": "Horas laborales",
    "other": "Servicios y otros costos",
    "remake": "Reposición",
}
TYPOLOGIES = {
    "FIXED": "Fijo",
    "TURN": "Abatible",
    "TILT": "Oscilante",
    "TILT_TURN": "Oscilobatiente",
    "TURN_LEFT": "Abatible izquierda",
    "TURN_RIGHT": "Abatible derecha",
    "TILT_TURN_LEFT": "Oscilobatiente izquierda",
    "TILT_TURN_RIGHT": "Oscilobatiente derecha",
    "SLIDING_2L": "Corredera 2 hojas",
    "SLIDING_3L": "Corredera 3 hojas",
    "SLIDING_4L": "Corredera 4 hojas",
    "SLIDING": "Corredera",
    "AWNING": "Proyectante",
    "DOOR_ENTRY": "Puerta",
    "DOOR_DOUBLE": "Puerta doble",
    "CORNER": "Esquinero",
    "BOW": "Ventana en arco",
    "FRAMELESS": "Vidrio sin marco",
    "COMPOSITE": "Conjunto",
    "LIFT_SLIDE": "Elevable-corredera (HST)",
    "PARALLEL_SLIDE": "Osciloparalela",
    "FOLD": "Plegable",
    "PIVOT_V": "Pivotante vertical",
    "PIVOT_H": "Pivotante horizontal",
    "VERTICAL_SLIDE": "Guillotina",
    "TOP_HUNG": "Proyectante",
    "BOTTOM_HUNG": "Apertura inferior",
    "SLIDE": "Corredera",
}


def typology_label(value):
    return TYPOLOGIES.get(value, "Sin tipología reconocida")


def entity(row, *, value=None, unit="count", currency=None, label=None, href=None, reason=None):
    return {
        "code": row.get("code") or row.get("sku") or row.get("label") or "Fuente sin dirección",
        "label": label or row.get("name") or row.get("label") or "",
        "href": href or f"/projects/{row['project_id']}?section=quote",
        "value": str(value) if value is not None else None,
        "unit": unit,
        "currency": currency,
        "reason": reason,
    }


def metric(
    key,
    label,
    group,
    value,
    unit,
    details,
    formula,
    source,
    *,
    currency=None,
    reason=None,
    missing=0,
):
    return {
        "key": key,
        "label": label,
        "group": group,
        "value": str(value) if value is not None else None,
        "unit": unit,
        "currency": currency,
        "reason": reason if value is None else None,
        "formula": formula,
        "source": source,
        "definition": f"/analytics?definition={key}",
        "details": details,
        "missing": missing,
    }


def _quote(snapshot, cascade=None):
    workspace = snapshot.get("pricing", {}).get("result", {}).get("workspace") or {}
    value = cascade or workspace.get("cascade") or {}
    net = value.get("net", snapshot.get("project", {}).get("total_price_net"))
    cost = value.get("cost", snapshot.get("pricing", {}).get("applied_total_cost_net"))
    if net is None or cost is None:
        return None
    components = defaultdict(list)
    discount = None
    for step in value.get("steps") or []:
        key = step["key"]
        if key == "discount":
            discount = step.get("amount")
        elif key in ("profit_at_list", "project_charges", "tax"):
            continue
        else:
            target = (
                key
                if key in ("waste", "labor")
                else "other"
                if key in ("installation", "services", "extra_services")
                else "materials"
            )
            components[target].append(step["amount"])
    # Absence of a historic composition is preserved, not balanced with a plug.
    return {
        "net": net,
        "cost": cost,
        **{
            key: total(components[key]) if components[key] else "0"
            for key in ("materials", "waste", "labor", "other")
        },
        "discount": discount,
        "composition_known": bool(value.get("steps")),
    }


def _positions(snapshot):
    return snapshot.get("positions") or []


def driver_details(row, orders, data, quote, key, currency):
    detail = []
    if key != "remake":
        detail.append(
            entity(
                row,
                value=quote[key],
                unit="money",
                currency=currency,
                label="Costo cotizado de esta causa en la revisión elegida",
            )
        )
    for order in orders:
        if bool(order["payload_json"].get("remake_of")) != (key == "remake"):
            continue
        materials, steps, _, _ = reports.source_rows(order, data)
        labels = {m["id"]: m["sku"] for m in materials}
        labels.update({s["id"]: s["label"] for s in steps})
        labels.update(other="Servicios y otros costos", credit="Crédito por material recuperado")
        for part in driver_sources(reports.report_cost(order, data), key):
            detail.append(
                entity(
                    order,
                    value=part["amount"],
                    unit="money",
                    currency=currency,
                    label=f"{labels[part['id']]} · {order.get('source') or 'Cierre de costos'}",
                    href=f"/analytics?order={order['id']}&movement={part['id']}",
                )
            )
    return detail


def sales(data, people):
    emissions = data["emissions"]
    count = len(emissions)
    result = []
    for key, label, kind in [
        ("emitted", "Emitidas", None),
        ("approved", "Aprobadas", "APPROVED"),
        ("rejected", "Rechazadas", "DECLINED"),
    ]:
        cohort = [row for row in emissions if kind is None or row["decision"] == kind]
        detail = [
            entity(
                row,
                value=1,
                label=f"{row['name']} · {row['revision_code']} · {row['selected_revision']}",
            )
            for row in cohort
        ]
        result.append(
            metric(
                key,
                label,
                "sales",
                len(cohort) if count else None,
                "count",
                detail,
                "Una revisión emitida cuenta una vez; la respuesta corresponde al ofrecimiento, aunque elija otra revisión.",
                "emissions.sql · project_versions, quote_decisions y customer_approvals; cohorte por emisión.",
                reason="No hay cotizaciones emitidas en el período.",
            )
        )
    approved = [row for row in emissions if row["decision"] == "APPROVED"]
    result.append(
        metric(
            "conversion",
            "¿Cuánto de lo emitido se aprueba?",
            "sales",
            ratio(len(approved), count),
            "fraction",
            [
                entity(
                    row,
                    value=1 if row["decision"] == "APPROVED" else 0,
                    label=f"{row['name']} · {row['revision_code']}",
                )
                for row in emissions
            ],
            "Revisiones aprobadas ÷ revisiones emitidas en la cohorte. Pendientes y cambios solicitados permanecen en el denominador.",
            "emissions.sql · decisión del ofrecimiento; no se cuentan enlaces ni se mezcla una revisión posterior.",
            reason="No hay revisiones emitidas.",
        )
    )
    for dimension, label in [
        ("estimator", "Conversión por estimador"),
        ("typology", "Conversión por tipología"),
    ]:
        groups = defaultdict(list)
        for row in emissions:
            keys = (
                [people.get(str(row["estimator_id"]), "Sin autor declarado")]
                if dimension == "estimator"
                else sorted(
                    {typology_label(p.get("typology")) for p in _positions(row["snapshot_json"])}
                )
                or ["Sin tipología declarada"]
            )
            for key in keys:
                groups[key].append(row)
        for index, (key, cohort) in enumerate(sorted(groups.items())):
            result.append(
                metric(
                    f"conversion_{dimension}:{index}",
                    f"{label} · {key}",
                    "sales",
                    ratio(sum(row["decision"] == "APPROVED" for row in cohort), len(cohort))
                    if not key.startswith("Sin ")
                    else None,
                    "fraction",
                    [
                        entity(row, value=1 if row["decision"] == "APPROVED" else 0)
                        for row in cohort
                    ],
                    "Aprobadas ÷ emitidas del grupo; una cotización mixta pertenece a cada tipología, sin duplicarse dentro de una.",
                    "emissions.sql · pricing.requested_by y positions.typology de la revisión sellada.",
                    reason="Falta declarar el autor o la tipología."
                    if key.startswith("Sin ")
                    else None,
                )
            )
    decisions = [row for row in emissions if row["decision"] in ("APPROVED", "DECLINED")]
    times = []
    detail = []
    for row in decisions:
        hours = None
        if row["decided_at"] is not None and row["decided_at"] >= row["emitted_at"]:
            difference = row["decided_at"] - row["emitted_at"]
            hours = ratio(
                difference.days * 86400000000
                + difference.seconds * 1000000
                + difference.microseconds,
                3600000000,
            )
        times.append(hours)
        detail.append(
            entity(
                row,
                value=hours,
                unit="hours",
                reason="Falta un timestamp de decisión válido." if hours is None else None,
            )
        )
    result.append(
        metric(
            "decision_time",
            "¿Cuánto tarda el cliente en decidir?",
            "sales",
            average(times),
            "hours",
            detail,
            "Promedio de (decisión − emisión) en horas transcurridas; aprobadas y rechazadas. No son horas laborales.",
            "emissions.sql · project_versions.emitted_at y quote_decisions.decided_at; fallback histórico customer_approvals.decided_at.",
            reason="No hay decisiones o faltan timestamps válidos; no se promedian solo las filas completas.",
            missing=sum(value is None for value in times),
        )
    )
    rejected = [row for row in emissions if row["decision"] == "DECLINED"]
    reasons = defaultdict(list)
    for row in rejected:
        reasons[row["rejection_note"] or "Sin motivo declarado"].append(row)
    for index, (reason, cohort) in enumerate(sorted(reasons.items())):
        result.append(
            metric(
                f"rejection_reason:{index}",
                reason,
                "sales",
                len(cohort),
                "count",
                [entity(row, value=1) for row in cohort],
                "Conteo de rechazos con el mismo motivo literal; la IA no clasifica ni completa motivos.",
                "emissions.sql · evidence.note o decided_note del rechazo.",
            )
        )
    # One current revision per project: older issued revisions are not pipeline.
    current = {}
    for row in emissions:
        if row["revision_code"] != row["current_revision"]:
            continue
        if (
            str(row["project_id"]) not in current
            or row["emitted_at"] > current[str(row["project_id"])]["emitted_at"]
        ):
            current[str(row["project_id"])] = row
    pipeline = defaultdict(list)
    for row in current.values():
        pipeline[(row["phase"], row["snapshot_json"].get("project", {}).get("currency"))].append(
            row
        )
    for index, ((phase, currency), cohort) in enumerate(sorted(pipeline.items(), key=str)):
        values = [
            row["snapshot_json"].get("project", {}).get("total_price_gross") for row in cohort
        ]
        result.append(
            metric(
                f"pipeline:{index}",
                f"¿Cuánto hay en {PHASES.get(phase, 'fase sin declarar').lower()}?",
                "sales",
                total(values) if currency else None,
                "money",
                [
                    entity(row, value=value, unit="money", currency=currency)
                    for row, value in zip(cohort, values, strict=True)
                ],
                "Suma bruta de la revisión vigente de cada obra emitida en la cohorte, por fase actual y moneda. No son ingresos cobrados.",
                "emissions.sql · project.total_price_gross sellado; projects.status actual.",
                currency=currency,
                reason="Falta moneda o total sellado en al menos una obra; no se suma un subconjunto.",
                missing=sum(value is None for value in values),
            )
        )
    return result


def margins(data):
    selected = {}
    for row in data["emissions"]:
        if row["decision"] == "APPROVED":
            selected[str(row["project_id"])] = row
    result, works, typologies = [], [], defaultdict(list)
    for row in selected.values():
        snapshot = row["snapshot_json"]
        quote = _quote(snapshot)
        orders = [
            o
            for o in data["orders"]
            if str(o["project_version_id"]) == str(row["selected_version_id"])
        ]
        base = [o for o in orders if not o["payload_json"].get("remake_of")]
        remakes = [o for o in orders if o["payload_json"].get("remake_of")]
        known_positions = {str(p["id"]) for p in _positions(snapshot)}
        covered_positions = {str(o["payload_json"].get("position_id")) for o in base}
        bridge = None
        if quote is not None:
            bridge = margin_bridge(
                quote=quote,
                base=[reports.report_cost(o, data) for o in base],
                remakes=[reports.report_cost(o, data) for o in remakes],
            )
            if not known_positions or known_positions != covered_positions:
                bridge.update(
                    real_cost=None,
                    real_profit=None,
                    real_margin=None,
                    delta_profit=None,
                    delta_margin=None,
                    drivers=[],
                    causes=[
                        "Falta la OT de una posición de la revisión elegida; no se calcula un margen parcial."
                    ],
                )
            if snapshot.get("project", {}).get("currency") not in ("CLP", "USD", "UF"):
                bridge.update(
                    real_cost=None,
                    real_profit=None,
                    real_margin=None,
                    delta_profit=None,
                    delta_margin=None,
                    drivers=[],
                    causes=[
                        "Falta declarar la moneda de la revisión sellada; no se mezclan costos de distintas monedas."
                    ],
                )
        cause = (
            " ".join(bridge["causes"])
            if bridge
            else "La revisión histórica no conserva neto y costo del motor."
        )
        work = {
            "id": str(row["project_id"]),
            "code": row["code"],
            "name": row["name"],
            "revision": row["selected_revision"],
            "currency": snapshot.get("project", {}).get("currency"),
            "quoted_margin": bridge["quoted_margin"] if bridge else None,
            "real_margin": bridge["real_margin"] if bridge else None,
            "quoted_cost": bridge["quoted_cost"] if bridge else None,
            "real_cost": bridge["real_cost"] if bridge else None,
            "delta_profit": bridge["delta_profit"] if bridge else None,
            "delta_margin": bridge["delta_margin"] if bridge else None,
            "net": quote["net"] if quote else None,
            "reason": cause or None,
            "drivers": bridge["drivers"] if bridge else [],
            "discount": bridge.get("discount") if bridge else None,
            "orders": [
                {
                    "id": str(o["id"]),
                    "code": o["code"],
                    "remake": bool(o["payload_json"].get("remake_of")),
                    "result": reports.report_cost(o, data),
                    "source": o.get("source") or "Falta fuente de costos.",
                    "href": f"/production?order={o['id']}",
                }
                for o in orders
            ],
            "demo": any(p.get("is_demo") for p in _positions(snapshot)),
        }
        works.append(work)
        for key, label, unit in [
            ("quoted_margin", "Margen cotizado", "fraction"),
            ("real_margin", "Margen real", "fraction"),
            ("delta_profit", "Desvío de utilidad", "money"),
        ]:
            result.append(
                metric(
                    f"{key}:{row['id']}",
                    f"{label} · {row['code']}",
                    "margin",
                    work[key],
                    unit,
                    [entity(row, value=work[key], unit=unit, currency=work["currency"])],
                    "(Neto de la revisión elegida − costo) ÷ neto; desvío de utilidad = costo cotizado − costo real.",
                    "emissions.sql, orders.sql, materials.sql, steps.sql, remnants.sql · revisión aprobada y cierre de todas sus OT y remakes.",
                    currency=work["currency"],
                    reason=cause or "El neto es cero: el margen no está definido.",
                )
            )
        if bridge and bridge["drivers"]:
            for driver in bridge["drivers"]:
                result.append(
                    metric(
                        f"driver_{driver['key']}:{row['id']}",
                        f"{DRIVERS[driver['key']]} · {row['code']}",
                        "margin",
                        driver["amount"],
                        "money",
                        driver_details(row, orders, data, quote, driver["key"], work["currency"]),
                        "Costo cotizado de la causa − costo real original; reposiciones = −costo real de todas las OT de reposición.",
                        "Cascada sellada del motor y revisión inmutable de costos por OT. El descuento ya está incluido en el neto.",
                        currency=work["currency"],
                    )
                )
            result.append(
                metric(
                    f"driver_discount:{row['id']}",
                    f"Descuento de la revisión elegida · {row['code']}",
                    "margin",
                    bridge.get("discount"),
                    "money",
                    [
                        entity(
                            row,
                            value=bridge.get("discount"),
                            unit="money",
                            currency=work["currency"],
                            label="Descuento sellado en la cascada de la revisión elegida",
                        )
                    ],
                    "Descuento sellado, ya incluido en el neto y la utilidad cotizados; no se resta de nuevo en el desvío.",
                    "emissions.sql · pricing.result.workspace.cascade.steps.discount.amount.",
                    currency=work["currency"],
                    reason="La revisión histórica no conserva el descuento en su cascada.",
                )
            )
        # No arbitrary allocation of project-level charges to typologies.
        line_quotes = (
            snapshot.get("pricing", {}).get("result", {}).get("workspace", {}).get("positions")
            or []
        )
        for position in _positions(snapshot):
            line = next(
                (q for q in line_quotes if q["position_index"] == position["position_index"]), None
            )
            line_orders = [
                o
                for o in orders
                if str(o["payload_json"].get("position_id")) == str(position["id"])
            ]
            line_quote = _quote(snapshot, line.get("cascade")) if line else None
            line_bridge = (
                margin_bridge(
                    quote=line_quote,
                    base=[
                        reports.report_cost(o, data)
                        for o in line_orders
                        if not o["payload_json"].get("remake_of")
                    ],
                    remakes=[
                        reports.report_cost(o, data)
                        for o in line_orders
                        if o["payload_json"].get("remake_of")
                    ],
                )
                if line_quote
                else None
            )
            typologies[(typology_label(position.get("typology")), work["currency"])].append(
                (row, line_bridge)
            )
    for index, ((typology, currency), entries) in enumerate(sorted(typologies.items(), key=str)):
        values = [bridge["delta_profit"] if bridge else None for _, bridge in entries]
        result.append(
            metric(
                f"deviation_typology:{index}",
                f"Desvío de utilidad por tipología · {typology}",
                "margin",
                total(values),
                "money",
                [
                    entity(row, value=value, unit="money", currency=currency)
                    for (row, _), value in zip(entries, values, strict=True)
                ],
                "Suma de (costo cotizado de la posición − costo real de sus OT originales y reposiciones). Cargos globales no se reparten sin autoridad.",
                "emissions.sql · workspace.positions.cascade; orders/materials/steps/remnants.sql ligados a position_id.",
                currency=currency,
                reason="Falta la cascada por posición o un cierre de costos; no se omiten las posiciones incompletas.",
                missing=sum(value is None for value in values),
            )
        )
    return result, works


def production(data, start, end):
    cohort = [
        o for o in data["orders"] if start <= o["created_on"] <= end and o["status"] != "CANCELLED"
    ]
    result = []
    for key, label, field in [
        ("planned_waste", "Merma prevista", "planned_waste"),
        ("actual_waste", "Merma real", "waste_ratio"),
        ("utilization", "¿Cuánto material queda en piezas?", "utilization"),
    ]:
        numerator, denominator, detail = [], [], []
        for o in cohort:
            actual = o.get("evidence_json") or {}
            if field == "planned_waste":
                metrics = (
                    o["payload_json"].get("optimization", {}).get("bars", {}).get("metrics") or {}
                )
                bars = (
                    o["payload_json"]
                    .get("optimization", {})
                    .get("bars", {})
                    .get("workshop_cut_plan")
                )
                stock = total([bar.get("stock_length_mm") for bar in bars]) if bars else None
                loss = metrics.get("process_waste_mm")
                if metrics.get("unplaced", 0):
                    stock = loss = None
            else:
                measurements = actual.get("bars") or {}
                _, _, _, fingerprint = reports.source_rows(o, data)
                if fingerprint != o.get("source_fingerprint"):
                    measurements = {}
                stock = measurements.get("input_mm")
                loss = measurements.get("waste_mm" if field == "waste_ratio" else "productive_mm")
                try:
                    reading = bar_reading(
                        **{
                            k: measurements.get(k)
                            for k in ("input_mm", "productive_mm", "waste_mm", "reusable_mm")
                        },
                        complete=measurements.get("complete", False),
                    )
                    if reading["cause"]:
                        stock = loss = None
                except ValueError:
                    stock = loss = None
            numerator.append(loss)
            denominator.append(stock)
            detail.append(
                entity(
                    o,
                    value=ratio(loss, stock) if stock is not None and loss is not None else None,
                    unit="fraction",
                    href=f"/production?order={o['id']}",
                    label=o.get("source") or "Plan de corte y medición real",
                    reason="Falta plan completo o medición vigente de barras."
                    if stock is None or loss is None
                    else None,
                )
            )
        top, bottom = total(numerator), total(denominator)
        value = ratio(top, bottom) if top is not None and bottom is not None else None
        result.append(
            metric(
                key,
                label,
                "production",
                value,
                "fraction",
                detail,
                "Suma de largo perdido (o productivo) ÷ suma de largo de entrada. Pérdida incluye sierra, despuntes y sobrante descartado; retazo reutilizable no es merma.",
                "orders.sql · optimization.bars.metrics.process_waste_mm y workshop_cut_plan.stock_length_mm; production_actual_reports.evidence_json.bars para el hecho real.",
                reason="No hay OT o falta evidencia de barras en alguna; no se compara solo el subconjunto medido.",
                missing=sum(v is None for v in numerator),
            )
        )
    ids = {str(o["id"]) for o in cohort}
    consumed = [
        r
        for r in data["remnants"]
        if str(r["consumed_order_id"]) in ids and r["status"] == "CONSUMED"
    ]
    result.append(
        metric(
            "remnant_use",
            "Retazos realmente consumidos",
            "production",
            len(consumed) if cohort else None,
            "count",
            [
                entity(
                    {"code": r["code"] or "Retazo histórico"},
                    value=1,
                    href=f"/inventory?remnant={r['id']}",
                    label="Consumo material confirmado al cortar",
                )
                for r in consumed
            ],
            "Instancias de retazo en estado consumido por OT de la cohorte. Reservar o planificar un retazo no cuenta como uso.",
            "remnants.sql · inventory_remnants.status y consumed_order_id.",
            reason="No hay OT en el período.",
        )
    )
    stations = defaultdict(list)
    for s in data["steps"]:
        if str(s["order_id"]) in ids and s["status"] == "DONE":
            stations[s["label"]].append(s)
    for index, (label, steps) in enumerate(sorted(stations.items())):
        result.append(
            metric(
                f"station_time:{index}",
                f"Tiempo transcurrido · {label}",
                "production",
                average([s["elapsed_hours"] for s in steps]),
                "hours",
                [
                    entity(
                        {
                            "code": next(
                                o["code"] for o in cohort if str(o["id"]) == str(s["order_id"])
                            )
                        },
                        value=s["elapsed_hours"],
                        unit="hours",
                        href=f"/production?order={s['order_id']}",
                    )
                    for s in steps
                ],
                "Promedio de (finished_at − started_at) de pasos terminados. Incluye esperas; no se usa como costo de mano de obra.",
                "steps.sql · production_steps.started_at, finished_at y status.",
                reason="Falta un timestamp válido en una estación terminada.",
                missing=sum(s["elapsed_hours"] is None for s in steps),
            )
        )
    punctual = []
    detail = []
    for o in cohort:
        value = None
        if o["expected_at"] is not None and o["completed_at"] is not None:
            value = int(
                o["completed_at"].astimezone(ZoneInfo(o["timezone"])).date() <= o["expected_at"]
            )
        punctual.append(value)
        detail.append(
            entity(
                o,
                value=value,
                href=f"/production?order={o['id']}",
                reason="Falta promesa de término o evento de finalización."
                if value is None
                else None,
            )
        )
    result.append(
        metric(
            "orders_on_time",
            "¿Se terminan las OT a tiempo?",
            "production",
            ratio(total(punctual), len(punctual)) if total(punctual) is not None else None,
            "fraction",
            detail,
            "OT finalizadas hasta expected_at ÷ OT de la cohorte de liberación; una promesa o finalización ausente impide afirmar la puntualidad completa.",
            "orders.sql · orders.expected_at y primer evento WO_COMPLETED; día local de la organización.",
            reason="Falta una promesa o finalización; no se excluyen OT pendientes.",
            missing=sum(v is None for v in punctual),
        )
    )
    causes = defaultdict(list)
    for o in cohort:
        if o["payload_json"].get("remake_of"):
            reason = o["payload_json"].get("remake_reason") or {}
            causes[reason.get("note") or "Sin causa declarada"].append(o)
    for index, (label, orders) in enumerate(sorted(causes.items())):
        result.append(
            metric(
                f"remake_cause:{index}",
                label,
                "production",
                len(orders),
                "count",
                [entity(o, value=1, href=f"/production?order={o['id']}") for o in orders],
                "Órdenes de reposición liberadas en la cohorte, agrupadas por causa literal.",
                "orders.sql · payload_json.remake_of y remake_reason.note.",
            )
        )
    return result


def field(data):
    result = []
    visits = [v for v in data["visits"] if v["status"] != "CANCELLED"]
    values = []
    detail = []
    for v in visits:
        value = (
            int(v["received_at"].astimezone(ZoneInfo(v["timezone"])).date() <= v["planned_on"])
            if v["received_at"] is not None
            else None
        )
        values.append(value)
        detail.append(
            entity(
                v,
                value=value,
                href=f"/dispatch?visit={v['id']}",
                label="Instalación con recepción firmada",
                reason="Falta el acta firmada de instalación." if value is None else None,
            )
        )
    result.append(
        metric(
            "installations_on_time",
            "¿Se instalan a tiempo?",
            "field",
            ratio(total(values), len(values)) if total(values) is not None else None,
            "fraction",
            detail,
            "Visitas de instalación recibidas hasta planned_on ÷ visitas agendadas en el período; servicios y visitas canceladas se excluyen.",
            "visits.sql · field_visits.planned_on, kind, status y primer field_events.RECEIVE.",
            reason="No hay instalaciones o falta recepción firmada; no se omiten las pendientes.",
            missing=sum(v is None for v in values),
        )
    )
    for dimension in ("kind", "typology"):
        groups = defaultdict(list)
        for i in data["incidents"]:
            context = i["context_json"] or {}
            unit = next(
                (
                    u
                    for u in context.get("units", [])
                    if str(u.get("position_id")) == str(i["position_id"])
                    and u.get("unit_index") == i["unit_index"]
                ),
                {},
            )
            label = (
                INCIDENTS[i["kind"]]
                if dimension == "kind"
                else typology_label(i.get("frozen_typology") or unit.get("typology"))
            )
            groups[label].append(i)
        for index, (label, incidents) in enumerate(sorted(groups.items())):
            result.append(
                metric(
                    f"incidents_{dimension}:{index}",
                    f"Incidencias · {label}",
                    "field",
                    len(incidents),
                    "count",
                    [
                        entity(
                            i,
                            value=1,
                            href=f"/dispatch?view=cases&visit={i['visit_id']}",
                            label=i["description"],
                        )
                        for i in incidents
                    ],
                    "Incidencias registradas en el período, por tipo o tipología sellada de la unidad; una incidencia cuenta una vez.",
                    "incidents.sql · field_incidents.kind, position_id, unit_index; field_visits.context_json.units.",
                )
            )
    warranties = [
        i for i in data["incidents"] if i["kind"] == "WARRANTY" and i["status"] != "CLOSED"
    ]
    result.append(
        metric(
            "open_warranties",
            "Garantías del período todavía abiertas",
            "field",
            len(warranties) if data["incidents"] else None,
            "count",
            [
                entity(
                    i,
                    value=1,
                    href=f"/dispatch?view=cases&visit={i['visit_id']}",
                    label=i["description"],
                )
                for i in warranties
            ],
            "Casos de garantía creados en el período cuyo estado actual no es cerrado. Es una lectura actual, no un saldo histórico al final del período.",
            "incidents.sql · field_incidents.kind, created_at y status.",
            reason="No hay incidencias registradas en el período.",
        )
    )
    return result


def workspace(org, start=None, end=None):
    start, end = reports.period(org, start, end)
    data = reports.load(org, start, end)
    people = {
        str(p["user_id"]): p["display_name"]
        for p in rows("SELECT * FROM private.field_people(%s)", [org])
    }
    commercial = sales(data, people)
    margin, works = margins(data)
    items = [*commercial, *margin, *production(data, start, end), *field(data)]
    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "as_of": datetime.now(timezone.utc).isoformat(),
        "metrics": items,
        "works": works,
        "source": "analytics-v1 · evidencia por organización, revisión elegida y motor Decimal.",
        "empty": not (
            data["emissions"]
            or data["visits"]
            or data["incidents"]
            or any(start <= o["created_on"] <= end for o in data["orders"])
        ),
    }
