"""Customer history follows aliases without rewriting sealed project records."""

import json
from dataclasses import asdict
from decimal import Decimal

from dekopen_engine.collections import CollectionPayment, collection_summary
from dekopen_engine.customer_accounts import customer_accounts
from django.utils import timezone
from documents.repository import documentary_backend
from pricing.repository import rows
from projects import clients, payments


def aliases(org_id, client_id):
    return [
        str(row["id"])
        for row in rows(
            "WITH RECURSIVE family AS (SELECT id FROM public.clients WHERE org_id=%s AND id=%s "
            "UNION ALL SELECT c.id FROM public.clients c JOIN family f ON c.merged_into_id=f.id WHERE c.org_id=%s) "
            "SELECT id FROM family",
            [org_id, client_id, org_id],
        )
    ]


def account_history(org_id, client_id):
    family = aliases(org_id, client_id)
    projects = rows(
        "SELECT id,code,name,status,updated_at,total_price_gross FROM public.projects "
        "WHERE org_id=%s AND client_id=ANY(%s::uuid[]) ORDER BY updated_at DESC,id",
        [org_id, family],
    )
    project_history, payment_history, quote_history, documents, accounts = [], [], [], [], []
    for project in projects:
        identity = project["id"]
        deal = payments._deal(org_id, identity, project)
        with documentary_backend():
            ledger = rows(
                "SELECT p.*,r.receipt_code,r.payload_json->'project'->>'currency' AS receipt_currency FROM public.project_payments p LEFT JOIN public.payment_receipts r "
                "ON r.org_id=p.org_id AND r.payment_id=p.id WHERE p.org_id=%s AND p.project_id=%s "
                "ORDER BY p.recorded_at DESC,p.id",
                [org_id, identity],
            )
            versions = rows(
                "SELECT v.id,v.revision_code,v.snapshot_json,v.emitted_at,c.kind AS agreement_status,"
                "c.selected_version_id FROM public.project_versions v LEFT JOIN LATERAL "
                "private.quotation_choice(v.org_id,v.id) c ON true WHERE v.org_id=%s AND v.project_id=%s "
                "ORDER BY v.emitted_at DESC,v.id",
                [org_id, identity],
            )
            for table, kind, code in (
                ("project_invoices", "INVOICE", "invoice_code"),
                ("payment_receipts", "RECEIPT", "receipt_code"),
                ("project_credit_notes", "CREDIT_NOTE", "credit_code"),
            ):
                for doc in rows(
                    f"SELECT id,{code} AS label,created_at FROM public.{table} WHERE org_id=%s AND project_id=%s ORDER BY created_at DESC,id",
                    [org_id, identity],
                ):
                    documents.append(
                        {
                            **doc,
                            "kind": kind,
                            "project_id": identity,
                            "project_code": project["code"],
                            "revision_code": None,
                        }
                    )
        summary = payments.collection_projection(
            org_id=org_id, project_id=identity, deal=deal, payments=ledger
        )
        currency = deal["currency"] if deal else None
        accounts.append(
            (
                currency or "",
                summary,
                [
                    CollectionPayment(
                        str(p["id"]),
                        Decimal(str(p["amount"])),
                        p["voided_at"] is None,
                        bool(p.get("simulated")),
                    )
                    for p in ledger
                ],
            )
        )
        project_history.append(
            {
                **{key: project[key] for key in ("id", "code", "name", "status", "updated_at")},
                "currency": currency,
                "revision_code": deal.get("sealed_revision") if deal else None,
                "total": str(summary.total) if summary.total is not None else None,
                "collected": str(summary.collected) if deal else None,
                "balance": str(summary.balance) if summary.balance is not None else None,
                "money_cause": None if deal else "Falta calcular y aplicar el precio de la obra.",
                "simulated": summary.includes_simulation,
            }
        )
        for payment in ledger:
            payment_history.append(
                {
                    **{
                        key: payment[key]
                        for key in (
                            "id",
                            "receipt_code",
                            "amount",
                            "kind",
                            "method",
                            "recorded_at",
                            "voided_at",
                        )
                    },
                    "project_id": identity,
                    "project_code": project["code"],
                    "currency": payment["receipt_currency"] or currency,
                    "simulated": bool(payment.get("simulated")),
                }
            )
        for version in versions:
            snapshot = version["snapshot_json"]
            if isinstance(snapshot, str):
                snapshot = json.loads(snapshot)
            sealed = snapshot.get("project", {})
            quote_history.append(
                {
                    "project_id": identity,
                    "project_code": project["code"],
                    "project_name": project["name"],
                    "version_id": version["id"],
                    "revision_code": version["revision_code"],
                    "emitted_at": version["emitted_at"],
                    "currency": sealed.get("currency"),
                    "total": sealed.get("total_price_gross"),
                    "agreement_status": version["agreement_status"],
                    "selected": bool(deal and deal.get("version_id") == str(version["id"])),
                }
            )
            documents.append(
                {
                    "id": version["id"],
                    "kind": "QUOTE",
                    "project_id": identity,
                    "project_code": project["code"],
                    "label": f"Cotización · {version['revision_code']}",
                    "revision_code": version["revision_code"],
                    "created_at": version["emitted_at"],
                }
            )
    return {
        "projects": project_history,
        "payments": payment_history,
        "quotations": quote_history,
        "documents": documents,
        "balances": [
            {
                **asdict(a),
                **{
                    key: str(getattr(a, key))
                    for key in ("total", "collected", "balance", "simulated_collected")
                },
            }
            for a in customer_accounts(accounts)
        ],
        "unknown_projects": sum(item["total"] is None for item in project_history),
    }


def dossier(org_id, client_id):
    client = clients.client_public(org_id, client_id)
    family = aliases(org_id, client_id)
    notes = rows(
        "SELECT id,body,author_label,created_at,is_legacy,source_updated_at FROM public.client_notes "
        "WHERE org_id=%s AND client_id=ANY(%s::uuid[]) ORDER BY created_at DESC,id",
        [org_id, family],
    )
    merges = rows(
        "SELECT m.id,s.name AS source_name,t.name AS target_name,m.reason,m.actor_label,m.created_at "
        "FROM public.client_merges m JOIN public.clients s ON s.id=m.source_id AND s.org_id=m.org_id "
        "JOIN public.clients t ON t.id=m.target_id AND t.org_id=m.org_id WHERE m.org_id=%s "
        "AND (m.source_id=ANY(%s::uuid[]) OR m.target_id=ANY(%s::uuid[])) ORDER BY m.created_at DESC,m.id",
        [org_id, family, family],
    )
    history = account_history(org_id, client_id)
    return {
        "client": client,
        "requested_id": client_id,
        "financial_access": True,
        "active_projects": sum(
            p["status"] not in ("COMPLETED", "CANCELLED") for p in history["projects"]
        ),
        "notes": notes,
        "merges": merges,
        **history,
    }


def _balance_clients(org_id, identities):
    """Two batch reads, then the same engine account projection as the dossier.

    The directory needs balances only: due dates, documents and full dossier
    histories cannot affect that predicate and need not be fetched. Unknown
    totals never become zero; currencies remain separate, including aliases.
    """
    if not identities:
        return []
    with documentary_backend():
        projects = rows(
            "WITH RECURSIVE family(root_id,id) AS ("
            "SELECT id,id FROM public.clients WHERE org_id=%s AND id=ANY(%s::uuid[]) "
            "UNION ALL SELECT f.root_id,c.id FROM public.clients c JOIN family f "
            "ON c.merged_into_id=f.id WHERE c.org_id=%s) "
            "SELECT f.root_id,p.id,p.total_price_gross,sealed.total AS sealed_total,"
            "sealed.currency AS sealed_currency,applied.currency AS applied_currency,"
            "applied.present AS has_applied,org.currency AS org_currency "
            "FROM family f JOIN public.projects p ON p.client_id=f.id AND p.org_id=%s "
            "LEFT JOIN public.tenancy_organizations org ON org.id=p.org_id "
            "LEFT JOIN LATERAL (SELECT v.snapshot_json#>>'{project,total_price_gross}' AS total,"
            "v.snapshot_json#>>'{project,currency}' AS currency FROM ("
            "SELECT id,org_id FROM public.project_versions WHERE org_id=p.org_id AND project_id=p.id "
            "ORDER BY emitted_at DESC,id DESC LIMIT 1) offered "
            "LEFT JOIN LATERAL private.quotation_choice(offered.org_id,offered.id) choice "
            "ON choice.kind='APPROVED' JOIN public.project_versions v "
            "ON v.id=COALESCE(choice.selected_version_id,offered.id) AND v.org_id=offered.org_id) sealed ON true "
            "LEFT JOIN LATERAL (SELECT currency,true AS present "
            "FROM private.applied_pricing_currency(p.org_id,p.id)) applied ON sealed.total IS NULL",
            [org_id, identities, org_id, org_id],
        )
        ledger = rows(
            "SELECT id,project_id,amount,voided_at,simulated FROM public.project_payments "
            "WHERE org_id=%s AND project_id=ANY(%s::uuid[])",
            [org_id, list({str(p["id"]) for p in projects})],
        ) if projects else []
    by_project = {}
    for payment in ledger:
        by_project.setdefault(str(payment["project_id"]), []).append(CollectionPayment(
            str(payment["id"]), Decimal(str(payment["amount"])),
            payment["voided_at"] is None, bool(payment["simulated"]),
        ))
    accounts = {}
    today = timezone.localdate()
    for project in projects:
        if project["sealed_total"] is not None:
            total, currency = project["sealed_total"], project["sealed_currency"] or "CLP"
        elif project["has_applied"]:
            total = project["total_price_gross"]
            currency = project["applied_currency"] or project["org_currency"] or "CLP"
        else:
            continue
        ledger = by_project.get(str(project["id"]), [])
        summary = collection_summary(total=Decimal(str(total)), currency=currency,
                                     milestones=(), payments=ledger, today=today)
        accounts.setdefault(str(project["root_id"]), []).append((currency, summary, ledger))
    return [identity for identity, entries in accounts.items()
            if any(account.balance > 0 for account in customer_accounts(entries))]


def directory(org_id, data, *, commercial):
    needle = data.get("q", "").strip()

    def pattern(text):
        return "%" + text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"

    # Search and active-project filtering happen before LIMIT. Alias ancestry
    # is one set-based query; contacts/addresses are loaded only for the page.
    prefix = (
        "WITH RECURSIVE family(root_id,id) AS (SELECT id,id FROM public.clients WHERE org_id=%s "
        "UNION ALL SELECT f.root_id,c.id FROM public.clients c JOIN family f "
        "ON c.merged_into_id=f.id WHERE c.org_id=%s), matches AS ("
        "SELECT c.*,EXISTS(SELECT 1 FROM public.projects p JOIN family f ON p.client_id=f.id "
        "WHERE p.org_id=%s AND f.root_id=c.id AND p.status NOT IN('COMPLETED','CANCELLED')) "
        "AS has_active_projects FROM public.clients c WHERE c.org_id=%s "
        "AND (c.name ILIKE %s OR private.client_rut_key(c.rut) LIKE %s) "
        "AND (%s OR c.merged_into_id IS NULL)) "
    )
    parameters = [org_id, org_id, org_id, org_id, pattern(needle), pattern(clients.rut_key(needle)),
                  bool(data.get("include_merged"))]
    condition = "WHERE (%s=false OR has_active_projects)"
    parameters.append(bool(data.get("with_active_projects")))
    if data.get("with_balance"):
        candidates = rows(prefix + "SELECT id FROM matches " + condition, parameters)
        identities = _balance_clients(org_id, [str(p["id"]) for p in candidates]) if commercial else []
        condition += " AND id=ANY(%s::uuid[])"
        parameters.append(identities)
    total = rows(prefix + "SELECT count(*) AS total FROM matches " + condition, parameters)[0]["total"]
    offset, limit = data.get("offset", 0), data.get("limit", 50)
    page = rows(prefix + "SELECT * FROM matches " + condition + " ORDER BY is_active DESC,name,id LIMIT %s OFFSET %s",
                [*parameters, limit, offset])
    children = clients.child_lists(org_id, [item["id"] for item in page])
    return {
        "items": [{**clients._public(item), **children[str(item["id"])],
                   "has_active_projects": item["has_active_projects"]} for item in page],
        "total": total,
        "next_offset": offset + limit if offset + limit < total else None,
    }
