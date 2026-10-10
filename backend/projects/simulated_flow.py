"""Explicit Flow simulator: capability, expiry, callback and one ledger receipt.

No HTTP request goes to Flow. The simulated provenance follows the payment
into its immutable PDF and every balance projection.
"""

from datetime import timedelta
from decimal import Decimal
import hashlib
import hmac
import json
import secrets
from uuid import UUID, uuid4

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from authentication.errors import contract_error
from documents.repository import documentary_backend
from pricing.repository import one, rows
from projects.collection_settings import preferences
from projects.payment_links import _public_link
from projects.payments import _deal, collection_projection
from projects.receipts import issue_receipt
from projects.provider_scope import provider_scope
from projects.service import project_row


def create_link(*, org_id, project_id, actor_id, data):
    pref = preferences(org_id)
    if not pref["simulation_enabled"]:
        raise contract_error(422, "collection_simulation_disabled", "El dueño desactivó los simuladores en Ajustes › Cobranza e integraciones.")
    amount = Decimal(str(data["amount"]))
    if not amount.is_finite() or amount <= 0 or amount != amount.to_integral_value():
        raise contract_error(422, "amount_invalid", "El monto debe ser un entero CLP positivo.")
    expiry = data.get("expires_at")
    request = {k: str(v) if hasattr(v, "isoformat") or isinstance(v, Decimal) else v
               for k, v in data.items()}
    digest = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
    with transaction.atomic():
        project = project_row(org_id, project_id, lock=True)
        with documentary_backend():
            existing = rows("SELECT * FROM public.project_payment_links WHERE org_id=%s AND operation_key=%s",
                            [str(org_id), data["operation_key"]])
            if existing:
                link = existing[0]
                if str(link["project_id"]) != str(project_id) or link.get("request_hash") != digest:
                    raise contract_error(409, "payment_operation_conflict", "La operación ya identifica otro cobro. Revisa el enlace registrado.")
                return {"link": _public_link(link)}
            deal = _deal(org_id, project_id, project)
            if not deal or not deal["sealed_revision"]:
                raise contract_error(422, "payment_requires_sealed_deal", "Emite una revisión antes de crear un cobro.")
            if deal["currency"] != "CLP":
                raise contract_error(422, "payment_currency_unsupported", "El simulador Flow cobra solo en CLP. Registra otras monedas manualmente.")
            ledger = rows("SELECT id,amount,voided_at,simulated FROM public.project_payments "
                          "WHERE org_id=%s AND project_id=%s", [str(org_id), str(project_id)])
            balance = collection_projection(org_id=org_id, project_id=project_id, deal=deal, payments=ledger).balance
            if amount > balance:
                raise contract_error(422, "payment_exceeds_balance", "El cobro supera el saldo pendiente. Revisa los movimientos.")
            expiry = expiry or timezone.now() + timedelta(days=pref["payment_link_days"])
            if expiry <= timezone.now() or expiry > timezone.now() + timedelta(days=90):
                raise contract_error(422, "payment_link_expiry_invalid", "El vencimiento debe ser futuro y estar dentro de 90 días.")
            rows("UPDATE public.project_payment_links SET status='CANCELLED',updated_at=now() "
                 "WHERE org_id=%s AND project_id=%s AND environment='simulated' "
                 "AND status='PENDING' AND expires_at<=now() RETURNING id", [str(org_id), str(project_id)])
            live = rows("SELECT id FROM public.project_payment_links WHERE org_id=%s AND project_id=%s "
                        "AND status IN ('DISPATCHING','PENDING','UNCERTAIN') "
                        "AND (environment<>'simulated' OR expires_at IS NULL OR expires_at>now())",
                        [str(org_id), str(project_id)])
            if live:
                raise contract_error(409, "payment_link_pending_exists", "Ya hay un cobro vigente. Usa su enlace o verifica su resultado.")
            identifier, token = uuid4(), secrets.token_urlsafe(32)
            origin = (settings.BILLING_FRONTEND_ORIGIN or getattr(settings, "DEKOPEN_PUBLIC_APP_URL", "")).rstrip("/")
            if not origin:
                raise contract_error(422, "payer_return_not_configured", "Configura el origen público de la aplicación antes de preparar cobros.")
            link = one("INSERT INTO public.project_payment_links(id,org_id,project_id,operation_key,kind,amount,"
                       "payer_email,subject,status,environment,flow_token,url,created_by,deal_total,deal_currency,"
                       "expires_at,deal_revision,request_hash) "
                       "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'PENDING','simulated',%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *",
                       [str(identifier), str(org_id), str(project_id), data["operation_key"], data["kind"], amount,
                        data["payer_email"], data.get("subject") or f"{project['code']} · pago simulado",
                        token, f"{origin}/pago/simulado/{identifier}?token={token}", str(actor_id),
                        deal["total"], deal["currency"], expiry, deal["sealed_revision"], digest])
    return {"link": _public_link(link)}


def _capability(link_id, token):
    # The initial privileged lookup is bounded to the claimed link; its opaque
    # token is checked before any project, issuer or ledger data is read.
    with provider_scope():
        found = rows("SELECT * FROM public.project_payment_links WHERE id=%s AND environment='simulated'", [str(link_id)])
    if not found or not token or not hmac.compare_digest(str(found[0]["flow_token"] or ""), token):
        raise contract_error(404, "payment_link_not_found", "El acceso de prueba no está disponible. Pida un enlace vigente.")
    return found[0]


def payer_status(*, link_id, token):
    link = _capability(link_id, token)
    public = _public_link(link)
    return {k: public[k] for k in ("amount", "status", "expires_at", "deal_revision", "environment")}


def confirm(*, link_id, token, outcome):
    resolved = _capability(link_id, token)
    with provider_scope():
        project = project_row(resolved["org_id"], resolved["project_id"], lock=True)
        with documentary_backend():
            link = one("SELECT * FROM public.project_payment_links WHERE org_id=%s AND id=%s FOR UPDATE",
                       [str(resolved["org_id"]), str(link_id)])
            if link["status"] in ("PAID", "FAILED"):
                return payer_status(link_id=link_id, token=token)
            if link["status"] != "PENDING" or link["expires_at"] <= timezone.now():
                raise contract_error(409, "payment_link_expired", "El enlace de prueba venció. Pida un nuevo acceso.")
            if outcome == "FAILED":
                rows("UPDATE public.project_payment_links SET status='FAILED',updated_at=now() WHERE id=%s RETURNING id", [str(link_id)])
                return payer_status(link_id=link_id, token=token)
            if outcome != "PAID":
                raise contract_error(400, "payment_simulation_outcome_invalid", "Elija pago aprobado o rechazado para la prueba.")
            org_id, project_id = link["org_id"], link["project_id"]
            deal = _deal(org_id, project_id, project)
            if not deal or deal["sealed_revision"] != link["deal_revision"]:
                raise contract_error(409, "payment_link_stale", "La cotización fue reemplazada. Pida un cobro de la revisión vigente.")
            ledger = rows("SELECT id,amount,voided_at,simulated FROM public.project_payments "
                          "WHERE org_id=%s AND project_id=%s", [str(org_id), str(project_id)])
            balance = collection_projection(org_id=org_id, project_id=project_id, deal=deal, payments=ledger).balance
            if Decimal(str(link["amount"])) > balance:
                raise contract_error(422, "payment_exceeds_balance", "El saldo cambió. Revise los movimientos antes de repetir la prueba.")
            payment = one("INSERT INTO public.project_payments(org_id,project_id,operation_key,kind,amount,method,"
                          "reference,note,recorded_by,recorded_at,actor_label,simulated) "
                          "VALUES(%s,%s,%s,%s,%s,'OTHER',%s,%s,%s,%s,'Simulador Flow',true) RETURNING *",
                          [str(org_id), str(project_id), link["operation_key"], link["kind"], link["amount"],
                           "Flow simulado", "Prueba de pago — no se movió dinero", str(link["created_by"]), timezone.now()])
            issue_receipt(org_id=org_id, project=project, payment=payment,
                          actor_id=UUID(str(link["created_by"])), deal=deal)
            rows("UPDATE public.project_payment_links SET status='PAID',project_payment_id=%s,updated_at=now() "
                 "WHERE id=%s RETURNING id", [str(payment["id"]), str(link_id)])
    return payer_status(link_id=link_id, token=token)
