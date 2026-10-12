"""Internal-document adapter and separate, immutable SII simulator evidence.

The real signer/submitter remains projects.sii + projects.sii_envio. This
adapter never generates a CAF, electronic stamp, signature or tax XML.
"""

import hashlib
import json

from django.db import transaction

from authentication.errors import contract_error
from documents.repository import documentary_backend, decoded
from pricing.repository import one, rows
from projects.collection_settings import preferences
from projects.service import project_row
from documents.legal import INTERNAL_LEGEND

RESPONSES = {
    "ACCEPTED": "El simulador aceptó el documento. No se envió a SII.",
    "WARNINGS": "El simulador aceptó con reparos. Revise los datos del receptor antes de la activación real.",
    "REJECTED": "El simulador rechazó el documento. Corrija los antecedentes y prepare una nueva revisión.",
}


def public(row):
    return {"id": str(row["id"]), "invoice_id": str(row["invoice_id"]),
            "credit_note_id": str(row["credit_note_id"]) if row.get("credit_note_id") else None,
            "folio": row["folio"], "dte_type": row["dte_type"], "status": row["status"],
            "detail": decoded(row["response"])["detail"], "simulated": True,
            "actor_label": row.get("actor_label"), "created_at": row["created_at"].isoformat()}


def list_simulations(*, org_id, project_id):
    project_row(org_id, project_id)
    with documentary_backend():
        found = rows("SELECT * FROM public.project_fiscal_simulations WHERE org_id=%s AND project_id=%s "
                     "ORDER BY created_at,id", [str(org_id), str(project_id)])
    return {"items": [public(row) for row in found]}


def simulate(*, org_id, project_id, actor_id, actor_label, data):
    if not preferences(org_id)["simulation_enabled"]:
        raise contract_error(422, "collection_simulation_disabled", "El dueño desactivó los simuladores en Ajustes › Cobranza e integraciones.")
    project_row(org_id, project_id)
    binding = {key: str(value) for key, value in data.items() if key != "operation_key"}
    digest = hashlib.sha256(json.dumps(binding, sort_keys=True).encode()).hexdigest()
    with transaction.atomic(), documentary_backend():
        one("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", [f"fiscal_simulation:{org_id}"])
        existing = rows("SELECT * FROM public.project_fiscal_simulations WHERE org_id=%s AND operation_key=%s",
                        [str(org_id), data["operation_key"]])
        if existing:
            if str(existing[0]["project_id"]) != str(project_id) or existing[0]["request_hash"] != digest:
                raise contract_error(409, "fiscal_operation_conflict", "La operación ya identifica otra prueba tributaria.")
            return public(existing[0])
        invoice = one("SELECT payload_json FROM public.project_invoices WHERE org_id=%s AND project_id=%s AND id=%s",
                      [str(org_id), str(project_id), str(data["invoice_id"])], "invoice_not_found")
        dte_type = 39 if decoded(invoice["payload_json"]).get("document_kind") == "BOLETA" else 33
        credit_id = data.get("credit_note_id")
        if credit_id:
            one("SELECT id FROM public.project_credit_notes WHERE org_id=%s AND invoice_id=%s AND id=%s",
                [str(org_id), str(data["invoice_id"]), str(credit_id)], "credit_note_not_found")
            dte_type = 61
        count = one("SELECT count(*) AS n FROM public.project_fiscal_simulations WHERE org_id=%s", [str(org_id)])["n"]
        result = {"detail": RESPONSES[data["scenario"]], "legend": INTERNAL_LEGEND, "provider": "SIMULATED"}
        row = one("INSERT INTO public.project_fiscal_simulations(org_id,project_id,invoice_id,credit_note_id,"
                  "operation_key,request_hash,folio,dte_type,status,response,actor_id,actor_label) "
                  "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s) RETURNING *",
                  [str(org_id), str(project_id), str(data["invoice_id"]), str(credit_id) if credit_id else None,
                   data["operation_key"], digest, f"SIM-{count + 1:06d}", dte_type, data["scenario"],
                   json.dumps(result), str(actor_id), actor_label])
    return public(row)
