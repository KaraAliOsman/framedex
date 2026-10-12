"""Safe integration/readiness projection. Provider secrets stay in their adapters."""

import os
from django.utils import timezone

from authentication.errors import contract_error
from documents.repository import documentary_backend
from pricing.repository import rows

DEFAULTS = {"simulation_enabled": True, "payment_link_days": 7,
            "sii_active": False, "sii_certified": False}


def preferences(org_id):
    with documentary_backend():
        found = rows("SELECT simulation_enabled,payment_link_days,sii_active,sii_certified "
                     "FROM public.collection_preferences WHERE org_id=%s", [str(org_id)])
    return {**DEFAULTS, **(found[0] if found else {})}


def status(org_id):
    pref = preferences(org_id)
    with documentary_backend():
        flow = rows("SELECT enabled,api_url FROM public.org_payment_integrations "
                    "WHERE org_id=%s AND provider='FLOW'", [str(org_id)])
        certificates = rows("SELECT id FROM public.sii_certificates WHERE org_id=%s "
                            "AND active AND valid_to>%s", [str(org_id), timezone.now()])
    connected = bool(flow and flow[0]["enabled"])
    sii = (pref["sii_active"] and pref["sii_certified"] and bool(certificates)
           and os.environ.get("SII_WS_ENVIO_URL", "").startswith("https://palena.sii.cl/")
           and bool(os.environ.get("SII_WS_TOKEN")))
    return {**pref, "flow_connected": connected, "sii_connected": sii,
            "flow_environment": ("production" if connected and flow[0]["api_url"] == "https://www.flow.cl/api"
                                 else "sandbox" if connected else None),
            "flow_instructions": "Configura credenciales, retorno y webhook en Ajustes › Flow. Verifica sandbox antes de activar producción.",
            "sii_instructions": "Configura CAF, certificado vigente y endpoint productivo del adaptador existente. Declara la certificación de la organización después de verificarla con SII."}


def save(*, org_id, actor_id, data):
    if data.get("sii_active") and not data.get("sii_certified"):
        raise contract_error(422, "sii_certification_required", "Declara la certificación de la organización antes de activar SII.")
    with documentary_backend():
        rows("INSERT INTO public.collection_preferences(org_id,simulation_enabled,payment_link_days,"
             "sii_active,sii_certified,updated_by) VALUES(%s,%s,%s,%s,%s,%s) "
             "ON CONFLICT(org_id) DO UPDATE SET simulation_enabled=EXCLUDED.simulation_enabled,"
             "payment_link_days=EXCLUDED.payment_link_days,sii_active=EXCLUDED.sii_active,"
             "sii_certified=EXCLUDED.sii_certified,updated_by=EXCLUDED.updated_by,updated_at=now() RETURNING org_id",
             [str(org_id), data["simulation_enabled"], data["payment_link_days"], data["sii_active"],
              data["sii_certified"], str(actor_id)])
    return status(org_id)
