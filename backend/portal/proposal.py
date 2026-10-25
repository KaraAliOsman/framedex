"""Public commercial projection. No cost, live design or repricing authority."""

from documents.human import human_code
from decimal import Decimal

from dekopen_engine.commercial import PricingError
from dekopen_engine.quotation import GrossQuotationInput, gross_quotation, payment_amounts
from documents.renderers import _money
from documents.repository import decoded


def commercial_projection(version, positions):
    snapshot = decoded(version["snapshot_json"])
    sealed = snapshot.get("project") or {}
    pricing = snapshot.get("pricing") or {}
    services = (pricing.get("result") or {}).get("services") or []
    charges = (pricing.get("request") or {}).get("extras") or []
    extras = [{"key": f"service-{i}", "label": str(item.get("name") or item.get("label") or "Servicio"),
               "synthetic": bool(item.get("synthetic")), "source": item.get("source"),
               "amount": str(item["amount"]) if item.get("amount") is not None else None}
              for i, item in enumerate(services)]
    extras += [{"key": f"charge-{i}", "label": str(item.get("label") or "Cargo declarado"),
                "amount": str(item["amount"]) if item.get("amount") is not None else None}
               for i, item in enumerate(charges)]
    currency = sealed.get("currency") or "CLP"
    cause = None
    result = None
    try:
        entries = [GrossQuotationInput(str(p["id"]), p["quantity"], Decimal(p["price_net"])) for p in positions]
        entries += [GrossQuotationInput(e["key"], 1, Decimal(e["amount"])) for e in extras]
        result = gross_quotation(entries, currency=currency,
            sealed_net=Decimal(str(sealed["total_price_net"])),
            sealed_tax=Decimal(str(sealed["total_price_tax"])),
            sealed_gross=Decimal(str(sealed["total_price_gross"])))
    except (KeyError, TypeError, ValueError, ArithmeticError, PricingError):
        cause = "Falta una proyección comercial completa en esta revisión. Solicite una cotización nueva al fabricante."
    lines = {item.key: item for item in result.lines} if result else {}
    for item in [*positions, *extras]:
        line = lines.get(str(item.get("id") or item.get("key")))
        item.update(unit_price_gross=str(line.unit_gross) if line else None,
                    line_price_gross=str(line.gross) if line else None,
                    unit_rounding_adjustment=str(line.unit_adjustment) if line else None)
    terms = sealed.get("commercial_terms") or {}
    declared = terms.get("payment_schedule") or []
    schedule = []
    if declared and result:
        try:
            amounts = payment_amounts(result.sealed_gross, [Decimal(str(item["share"])) for item in declared], currency)
            schedule = [{"label": item["label"], "amount": str(amount),
                         "due_on": item.get("due_on"), "due_event": item.get("due_event")}
                        for item, amount in zip(declared, amounts, strict=True)]
        except (KeyError, TypeError, ValueError, ArithmeticError, PricingError):
            cause = "El calendario de esta revisión necesita revisión del fabricante. Solicite una cotización nueva."
    total = str(result.display_gross) if result else None
    reference = f"{human_code(sealed.get('code'))} · rev. {str(version['revision_code']).removeprefix('REV-')}"
    consent = f"Acepto la propuesta {reference} por {_money(total, currency)} IVA incluido y sus condiciones" if total else None
    return {"positions": positions, "extras": extras, "commercial_terms": terms,
            "payment_schedule": schedule, "display_total_gross": total,
            "rounding_adjustment": str(result.rounding_adjustment) if result else None,
            "price_cause": cause, "consent_text": consent,
            "price_source": "Motor comercial: venta e impuesto de esta revisión emitida; reparto exacto y ajuste de moneda explícito."}
