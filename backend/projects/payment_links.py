"""Flow payment links for cobranza — the provider-verified collection path.

A link is the durable claim for one Flow charge: the org's own Flow credentials
(org_payment_integrations) sign a `payment/create` whose commerceOrder is the
link's operation_key. The public webhook only carries a token — authority comes
from `payment/getStatus` re-queried server-side, never from callback data.
Settlement inserts a project_payments row keyed by the same operation_key, so
the ledger's UNIQUE (org_id, operation_key) dedupes webhook retries, manual
records, and lost-callback recovery identically. Mirrors billing/settlement.py:
no provider mutation is retried after an uncertain outcome — recovery is a GET.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from uuid import UUID

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from authentication.errors import contract_error
from billing import wallet
from billing.flow import FlowClient, FlowError
from documents.repository import documentary_backend
from pricing.repository import rows
from projects import payments
from projects.service import project_row

_LINK_KINDS = ("ANTICIPO", "PARCIAL", "SALDO")


def _public_link(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "operation_key": row["operation_key"],
        "kind": row["kind"],
        "amount": str(row["amount"]),
        "payer_email": row["payer_email"],
        "subject": row["subject"],
        "status": row["status"],
        "environment": row["environment"],
        "url": row["url"],
        "project_payment_id": str(row["project_payment_id"]) if row["project_payment_id"] else None,
        "created_at": row["created_at"].isoformat()
        if hasattr(row["created_at"], "isoformat")
        else row["created_at"],
        "updated_at": row["updated_at"].isoformat()
        if hasattr(row["updated_at"], "isoformat")
        else row["updated_at"],
    }


def _environment(api_url: str) -> str:
    return "sandbox" if api_url == "https://sandbox.flow.cl/api" else "production"


def _client(integration: dict) -> FlowClient:
    return FlowClient(
        api_url=integration["api_url"],
        api_key=integration["api_key"],
        secret_key=integration["secret_key"],
    )


def _client_for_link(link: dict) -> FlowClient:
    """Credentials that signed the dispatch while the charge is in flight;
    once the link is terminal the snapshot is deleted and the org's current
    integration answers recovery reads instead."""
    if link.get("flow_api_url") and link.get("flow_api_key") and link.get("flow_secret_key"):
        return FlowClient(
            api_url=link["flow_api_url"],
            api_key=link["flow_api_key"],
            secret_key=link["flow_secret_key"],
        )
    with documentary_backend():
        integration = rows(
            "SELECT api_url, api_key, secret_key FROM public.org_payment_integrations "
            "WHERE org_id=%s AND provider='FLOW' AND enabled",
            [str(link["org_id"])],
        )
    if not integration:
        raise FlowError("flow_not_configured")
    return _client(integration[0])


def get_integration(*, org_id: UUID) -> dict:
    """Config status for the settings surface — never leaks the secret."""
    with documentary_backend():
        found = rows(
            "SELECT api_url, api_key, payer_return_url, enabled, updated_at "
            "FROM public.org_payment_integrations WHERE org_id=%s AND provider='FLOW'",
            [str(org_id)],
        )
    if not found:
        return {"configured": False}
    row = found[0]
    return {
        "configured": True,
        "api_url": row["api_url"],
        "api_key_preview": row["api_key"][:4] + "…" + row["api_key"][-2:],
        "payer_return_url": row["payer_return_url"],
        "enabled": row["enabled"],
        "updated_at": row["updated_at"].isoformat()
        if hasattr(row["updated_at"], "isoformat")
        else row["updated_at"],
    }


def save_integration(*, org_id: UUID, data: dict) -> dict:
    """Upsert the org's Flow credentials. Secret is write-only: omitted on
    update keeps the stored one; it is never returned in any response."""
    api_url = str(data.get("api_url") or "https://sandbox.flow.cl/api")
    with transaction.atomic(), documentary_backend():
        existing = rows(
            "SELECT api_key, secret_key FROM public.org_payment_integrations "
            "WHERE org_id=%s AND provider='FLOW'",
            [str(org_id)],
        )
        api_key = data.get("api_key") or (existing[0]["api_key"] if existing else None)
        secret = data.get("secret_key") or (existing[0]["secret_key"] if existing else None)
        if not api_key:
            raise contract_error(
                422, "flow_api_key_required", "La clave de API de Flow es obligatoria."
            )
        if not secret:
            raise contract_error(
                422, "flow_secret_required", "La clave secreta de Flow es obligatoria."
            )
        rows(
            """
            INSERT INTO public.org_payment_integrations(
                org_id, provider, api_url, api_key, secret_key, payer_return_url, enabled)
            VALUES (%s, 'FLOW', %s, %s, %s, %s, %s)
            ON CONFLICT (org_id) DO UPDATE SET
                api_url = EXCLUDED.api_url,
                api_key = EXCLUDED.api_key,
                secret_key = EXCLUDED.secret_key,
                payer_return_url = EXCLUDED.payer_return_url,
                enabled = EXCLUDED.enabled,
                updated_at = now()
            RETURNING org_id
            """,
            [
                str(org_id),
                api_url,
                api_key.strip(),
                secret.strip(),
                (data.get("payer_return_url") or "").strip() or None,
                bool(data.get("enabled", True)),
            ],
        )
    return get_integration(org_id=org_id)


def list_links(*, org_id: UUID, project_id: UUID) -> dict:
    project_row(org_id, project_id)
    with documentary_backend():
        found = rows(
            "SELECT * FROM public.project_payment_links "
            "WHERE org_id=%s AND project_id=%s ORDER BY created_at,id",
            [str(org_id), str(project_id)],
        )
    return {"links": [_public_link(row) for row in found]}


def create_link(*, org_id: UUID, project_id: UUID, actor_id: UUID, data: dict) -> dict:
    """One durable dispatch claim per operation_key — a replay returns the
    existing link instead of minting a second charge."""
    project = project_row(org_id, project_id)
    amount = Decimal(str(data["amount"]))
    if not amount.is_finite() or amount <= 0 or amount != amount.to_integral_value():
        raise contract_error(422, "amount_invalid", "El monto debe ser un entero CLP positivo.")
    kind = str(data["kind"]).upper()
    if kind not in _LINK_KINDS:
        raise contract_error(422, "payment_kind_invalid", "Tipo de cobro no válido.")
    deal = payments._deal(org_id, project_id, project)
    if deal is None:
        raise contract_error(
            422, "payment_requires_deal", "El proyecto necesita un precio aplicado para cobrar."
        )
    if deal["currency"] != "CLP":
        raise contract_error(
            422,
            "payment_link_currency_unsupported",
            "Los links Flow solo cobran en CLP — el trato del proyecto usa otra moneda.",
        )
    subject = (data.get("subject") or "").strip() or f"{project['name']} — pago {kind.lower()}"
    with transaction.atomic():
        # Serialize against reset_draft_pricing, which holds the same project
        # lock while clearing pricing — a reset that commits first must not let
        # this claim outlive the deal it was priced against. Locking as the
        # request role: documentary_backend cannot take FOR UPDATE on projects.
        project_row(org_id, project_id, lock=True)
        if payments._deal(org_id, project_id, project) is None:
            raise contract_error(
                422, "payment_requires_deal", "El proyecto necesita un precio aplicado para cobrar."
            )
        with documentary_backend():
            integration = rows(
                "SELECT * FROM public.org_payment_integrations "
                "WHERE org_id=%s AND provider='FLOW' AND enabled",
                [str(org_id)],
            )
            if not integration:
                raise contract_error(
                    422,
                    "flow_not_configured",
                    "Configura la integración Flow en Ajustes primero.",
                )
            # Conflict-tolerant claim: concurrent replays converge on the one row the
            # unique key allows; the loser reads and validates the winner instead of
            # erroring out of the idempotency contract.
            inserted = rows(
                """
                INSERT INTO public.project_payment_links(
                    org_id, project_id, operation_key, kind, amount, payer_email,
                    subject, status, environment, created_by)
                VALUES (%s,%s,%s,%s,%s,%s,%s,'DISPATCHING',%s,%s)
                ON CONFLICT (org_id, operation_key) DO NOTHING
                RETURNING *
                """,
                [
                    str(org_id),
                    str(project_id),
                    data["operation_key"],
                    kind,
                    str(amount),
                    data["payer_email"].strip(),
                    subject[:200],
                    _environment(integration[0]["api_url"]),
                    str(actor_id),
                ],
            )
            if inserted:
                link = inserted[0]
            else:
                existing = rows(
                    "SELECT * FROM public.project_payment_links WHERE org_id=%s AND operation_key=%s",
                    [str(org_id), data["operation_key"]],
                )
                link = existing[0]
                if str(link["project_id"]) != str(project_id):
                    raise contract_error(
                        409, "payment_operation_conflict", "La operación ya existe en otro proyecto."
                    )
                return {"link": _public_link(link)}
            integration = integration[0]
            # The credential version that signs this dispatch travels in a
            # backend-only row — never on the tenant-readable links table.
            rows(
                "INSERT INTO public.project_payment_link_credentials("
                "link_id, org_id, flow_api_url, flow_api_key, flow_secret_key) "
                "VALUES (%s,%s,%s,%s,%s)",
                [
                    str(link["id"]),
                    str(org_id),
                    integration["api_url"],
                    integration["api_key"],
                    integration["secret_key"],
                ],
            )
    # The claim is committed — now the provider mutation. An uncertain outcome
    # marks the link UNCERTAIN; recovery is a GET, never a second POST.
    client = _client(integration)
    callback_origin = settings.BILLING_CALLBACK_ORIGIN.rstrip("/")
    return_url = integration["payer_return_url"] or (
        settings.BILLING_FRONTEND_ORIGIN.rstrip("/") + "/pago/retorno"
    )
    try:
        created = client.create_payment(
            order=str(data["operation_key"]),
            subject=subject[:200],
            amount=amount,
            email=data["payer_email"].strip(),
            confirmation_url=f"{callback_origin}/api/v1/projects/flow/confirm/{link['id']}/",
            return_url=return_url,
        )
        redirect = client.redirect_url(created)
        if type(created.get("flowOrder")) is not int or created["flowOrder"] <= 0:
            raise FlowError("flow_invalid_payment", uncertain=True)
    except FlowError as error:
        with transaction.atomic(), documentary_backend():
            rows(
                "UPDATE public.project_payment_links SET status='UNCERTAIN', updated_at=now() "
                "WHERE org_id=%s AND id=%s AND status='DISPATCHING' RETURNING id",
                [str(org_id), str(link["id"])],
            )
        raise contract_error(
            503, "payment_link_dispatch_failed", "Flow no confirmó el link — reintenta verificar."
        ) from error
    with transaction.atomic(), documentary_backend():
        link = rows(
            "UPDATE public.project_payment_links SET status='PENDING', flow_order=%s, "
            "flow_token=%s, url=%s, updated_at=now() "
            "WHERE org_id=%s AND id=%s RETURNING *",
            [str(created["flowOrder"]), str(created.get("token") or ""), redirect,
             str(org_id), str(link["id"])],
        )[0]
    return {"link": _public_link(link)}


def _payment(value: dict) -> dict:
    """Reduce provider data to required authority; mirrors billing's shape check."""
    try:
        if type(value["flowOrder"]) is not int or value["flowOrder"] <= 0:
            raise ValueError()
        if type(value["status"]) is not int or value["status"] not in (1, 2, 3, 4):
            raise ValueError()
        if not isinstance(value["commerceOrder"], str) or not value["commerceOrder"]:
            raise ValueError()
        amount = Decimal(value["amount"])
        if value["currency"] != "CLP" or not amount.is_finite() or amount <= 0:
            raise ValueError()
        return {
            "flowOrder": str(value["flowOrder"]),
            "commerceOrder": value["commerceOrder"],
            "status": value["status"],
            "amount": amount,
        }
    except (KeyError, TypeError, ValueError, InvalidOperation):
        raise FlowError("flow_invalid_payment") from None


def _settle(*, org_id: UUID, link_id: UUID, verified: dict, client: FlowClient) -> dict:
    """Fold a verified provider observation into link + ledger, idempotently."""
    with wallet.financial_transaction(org_id):
        found = rows(
            "SELECT * FROM public.project_payment_links "
            "WHERE org_id=%s AND id=%s FOR UPDATE",
            [str(org_id), str(link_id)],
        )
        if not found:
            raise contract_error(404, "payment_link_not_found", "El link de pago no existe.")
        link = found[0]
        if (
            link["operation_key"] != verified["commerceOrder"]
            or Decimal(str(link["amount"])) != verified["amount"]
            or link["flow_order"] not in (None, verified["flowOrder"])
            or link["environment"] != _environment(client.api_url)
        ):
            raise FlowError("flow_payment_binding_mismatch")
        if str(link["status"]) == "PAID":
            return {"link": _public_link(link)}
        if verified["status"] == 1:
            updated = rows(
                "UPDATE public.project_payment_links SET status='PENDING', flow_order=%s, "
                "updated_at=now() WHERE org_id=%s AND id=%s "
                "AND status IN ('DISPATCHING','UNCERTAIN','FAILED','PENDING') RETURNING *",
                [verified["flowOrder"], str(org_id), str(link_id)],
            )
            if updated:
                link = updated[0]
            return {"link": _public_link(link)}
        if verified["status"] in (3, 4):
            link = rows(
                "UPDATE public.project_payment_links SET status='FAILED', "
                "flow_order=%s, updated_at=now() "
                "WHERE org_id=%s AND id=%s AND status<>'PAID' RETURNING *",
                [verified["flowOrder"], str(org_id), str(link_id)],
            )[0]
            rows(
                "DELETE FROM public.project_payment_link_credentials WHERE link_id=%s",
                [str(link_id)],
            )
            return {"link": _public_link(link)}
        # status 2 — settled. The ledger's UNIQUE (org_id, operation_key) is the
        # dedup boundary: webhook retries and recoveries converge on one row.
        payment = rows(
            """
            INSERT INTO public.project_payments(
                org_id, project_id, operation_key, kind, amount, method,
                reference, note, recorded_by, recorded_at)
            VALUES (%s,%s,%s,%s,%s,'OTHER',%s,%s,%s,%s)
            ON CONFLICT (org_id, operation_key) DO NOTHING
            RETURNING *
            """,
            [
                str(org_id),
                str(link["project_id"]),
                str(link["operation_key"]),
                str(link["kind"]),
                str(Decimal(str(link["amount"]))),
                f"FLOW {verified['flowOrder']}",
                f"Cobro en línea — link {link['id']}",
                None,
                timezone.now(),
            ],
        )
        if not payment:
            # The operation key was claimed manually first — only a payment that
            # matches this link's own claim may stand in for the settlement.
            conflicting = rows(
                "SELECT * FROM public.project_payments WHERE org_id=%s AND operation_key=%s "
                "FOR UPDATE",
                [str(org_id), str(link["operation_key"])],
            )
            payment = conflicting
            if (
                str(payment[0]["project_id"]) != str(link["project_id"])
                or Decimal(str(payment[0]["amount"])) != Decimal(str(link["amount"]))
                or str(payment[0]["kind"]) != str(link["kind"])
                or payment[0]["voided_at"] is not None
            ):
                raise contract_error(
                    409,
                    "payment_operation_conflict",
                    "La operación pertenece a un cobro distinto — revisa el libro de cobranza.",
                )
        link = rows(
            "UPDATE public.project_payment_links SET status='PAID', flow_order=%s, "
            "project_payment_id=%s, updated_at=now() "
            "WHERE org_id=%s AND id=%s RETURNING *",
            [verified["flowOrder"], str(payment[0]["id"]), str(org_id), str(link_id)],
        )[0]
    # The credential version only needs to outlive an in-flight charge —
    # terminal links drop the snapshot so plaintext creds never accumulate.
    rows(
        "DELETE FROM public.project_payment_link_credentials WHERE link_id=%s",
        [str(link_id)],
    )
    return {"link": _public_link(link)}


def confirm_link(*, link_id: UUID, token: str) -> dict:
    """Public webhook: resolve the org through the opaque link id, then verify
    server-side with the link's own dispatch credentials — callback fields are
    untrusted and rotated org credentials never strand an outstanding charge."""
    with documentary_backend():
        found = rows(
            "SELECT l.*, c.flow_api_url, c.flow_api_key, c.flow_secret_key "
            "FROM public.project_payment_links l "
            "LEFT JOIN public.project_payment_link_credentials c ON c.link_id = l.id "
            "WHERE l.id=%s",
            [str(link_id)],
        )
    if not found:
        raise FlowError("payment_link_not_found")
    link = found[0]
    client = _client_for_link(link)
    verified = _payment(client.payment_status(token))
    return _settle(org_id=link["org_id"], link_id=link_id, verified=verified, client=client)


def recover_link(*, org_id: UUID, project_id: UUID, link_id: UUID) -> dict:
    """Recheck a pending/uncertain link via GET by commerceOrder — recovers a
    lost webhook or ambiguous create without issuing another charge."""
    with documentary_backend():
        found = rows(
            "SELECT l.*, c.flow_api_url, c.flow_api_key, c.flow_secret_key "
            "FROM public.project_payment_links l "
            "LEFT JOIN public.project_payment_link_credentials c ON c.link_id = l.id "
            "WHERE l.org_id=%s AND l.project_id=%s AND l.id=%s",
            [str(org_id), str(project_id), str(link_id)],
        )
        if not found:
            raise contract_error(404, "payment_link_not_found", "El link de pago no existe.")
        link = found[0]
    if str(link["status"]) == "PAID":
        return {"link": _public_link(link)}
    client = _client_for_link(link)
    verified = _payment(client.payment_by_order(str(link["operation_key"])))
    return _settle(org_id=org_id, link_id=link_id, verified=verified, client=client)
