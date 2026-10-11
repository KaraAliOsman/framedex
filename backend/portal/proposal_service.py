"""Capability-scoped proposal choices and immutable human consent."""

from datetime import date, datetime, timezone
from decimal import Decimal
import base64
import json
from uuid import uuid4
from zoneinfo import ZoneInfo

from django.db import transaction

from dekopen_engine.collections import CollectionPayment, collection_summary
from documents.agreements import choice, resolve_option, lock_quote
from documents.repository import DocumentaryError, decoded, one, rows, write
from projects.rut import valid_rut
from portal.proposal import commercial_projection


def option(version, *, allow_pdf=True):
    from portal.service import _sealed_positions, _sealed_project
    sealed = _sealed_project(version)
    artifacts = rows("SELECT storage_object_key FROM public.document_artifacts WHERE org_id=%s AND project_version_id=%s "
                     "AND document_type='DOC-01' AND format='PDF' ORDER BY created_at DESC LIMIT 1",
                     [version['org_id'], version['id']]) if allow_pdf else []
    from documents.artifacts import SupabaseDocumentStorage
    pdf = SupabaseDocumentStorage().signed_url(str(artifacts[0]['storage_object_key'])) if artifacts else None
    return {"revision_code": version["revision_code"],
            "snapshot_sha256": str(version.get("snapshot_sha256") or ""),
            "currency": sealed.get("currency") or "CLP",
            "total_price_gross": str(sealed["total_price_gross"]) if sealed.get("total_price_gross") is not None else None,
            "quote_pdf_url": pdf, "payment_terms": sealed.get('payment_terms'),
            "notes_commercial": sealed.get('notes_commercial'),
            **commercial_projection(version, _sealed_positions(version))}


def successor_path(approval, version, project):
    snapshot = decoded(version["snapshot_json"])
    if not (snapshot.get("organization") or {}).get("document_preferences", {}).get("portal_successor_link", False):
        return None
    from portal.document_links import _cipher
    found = rows("SELECT * FROM private.quote_successor_link(%s,%s)",
                 [approval["org_id"], version["id"]])
    if not found:
        return None
    row = found[0]
    raw = base64.b64decode(row["token_ciphertext"], validate=True)
    aad = f"document-link:v1:{row['org_id']}:{row['project_version_id']}:{row['id']}".encode()
    return "/cotizacion/" + _cipher().decrypt(raw[:12], raw[12:], aad).decode()


def read(token, *, track=True):
    from portal import service

    with transaction.atomic(), service.portal_backend():
        approval = service._approval_for_token(token)
        offering = service._bound_version(approval)
        project = service._live_project(approval)
        if track:
            write("UPDATE public.customer_approvals SET view_count=view_count+1,"
                  "first_viewed_at=COALESCE(first_viewed_at,clock_timestamp()),last_viewed_at=clock_timestamp() "
                  "WHERE id=%s AND org_id=%s", [approval["id"], approval["org_id"]])
        decided = choice(approval["org_id"], offering["id"])
        state = decided["kind"] if decided else approval["status"]
        legacy_approval = None
        if not decided and state == 'PENDING' and project['status'] in ('APPROVED','IN_PRODUCTION','COMPLETED'):
            legacy = rows("SELECT decided_at FROM public.customer_approvals WHERE org_id=%s AND project_version_id=%s AND status='APPROVED' ORDER BY decided_at LIMIT 1",
                          [approval['org_id'], offering['id']])
            if legacy:
                state = 'APPROVED'
                legacy_approval = legacy[0]['decided_at']
        selected, _ = resolve_option(approval["org_id"], offering, offering["revision_code"])
        if decided:
            record = one("SELECT revision_code FROM public.project_versions WHERE id=%s AND org_id=%s",
                         [decided["selected_version_id"], approval["org_id"]])
            selected, _ = resolve_option(approval["org_id"], offering, record["revision_code"])
        sealed = service._sealed_project(selected)
        offered_project = service._sealed_project(offering)
        superseded = project["current_revision"] != offering["revision_code"]
        expired = service._validity_expired(offered_project.get("quotation_valid_until"))
        selected_option = option(selected, allow_pdf=not superseded and not expired)
        options = [selected_option if str(selected['id']) == str(offering['id']) else option(offering, allow_pdf=not superseded and not expired)]
        if not superseded and not expired:
            for alternative in (decoded(offering["snapshot_json"]).get("alternatives") or []):
                revision = alternative["revision"]
                version, _ = resolve_option(approval["org_id"], offering, revision)
                options.append(selected_option if str(selected['id']) == str(version['id']) else option(version))
        now = datetime.now(ZoneInfo("America/Santiago")).date()
        valid_until = offered_project.get("quotation_valid_until")
        days = (date.fromisoformat(str(valid_until)) - now).days if valid_until else None
        payment = None
        provider = None
        if not superseded and not expired and selected_option["total_price_gross"] is not None:
            ledger = rows("SELECT id,amount,voided_at,simulated FROM public.project_payments WHERE org_id=%s AND project_id=%s",
                          [approval["org_id"], approval["project_id"]])
            balance = collection_summary(total=Decimal(selected_option["total_price_gross"]), currency=selected_option["currency"],
                milestones=[], payments=[CollectionPayment(str(p["id"]), Decimal(str(p["amount"])),
                    p["voided_at"] is None, bool(p.get("simulated"))) for p in ledger], today=now)
            payment = {"status": balance.status, "collected": str(balance.collected),
                       "balance": str(balance.balance), "simulated": balance.includes_simulation}
            if (state == "APPROVED" and project["status"] in ("APPROVED", "IN_PRODUCTION", "COMPLETED")
                and balance.balance > 0 and selected_option["currency"] == "CLP"):
                enabled = rows("SELECT enabled FROM public.org_payment_integrations WHERE org_id=%s AND provider='FLOW'",
                               [approval["org_id"]])
                pref = rows("SELECT simulation_enabled FROM public.collection_preferences WHERE org_id=%s", [approval["org_id"]])
                provider = "FLOW" if enabled and enabled[0]["enabled"] else "SIMULATED" if not pref or pref[0]["simulation_enabled"] else None
        payment_url = None
        if provider and payment:
            from portal.payments import pending_path
            payment_url = pending_path(token=token, approval=approval, revision=selected['revision_code'],
                                       balance=Decimal(payment['balance']), provider=provider)
        return {"schema": "portal_quote_v2", "organization": service._sealed_organization(offering),
            "project_code": offered_project.get("code") or "", "project_name": offered_project.get("name") or "",
            "client_name": offered_project.get("client_name") or "", "revision_code": offering["revision_code"],
            "offering_sha256": str(offering.get("snapshot_sha256") or ""), "selected_revision": selected["revision_code"],
            "emitted_at": offering["emitted_at"].isoformat(), "currency": selected_option["currency"],
            "payment_terms": sealed.get("payment_terms"), "notes_commercial": sealed.get("notes_commercial"),
            "total_price_net": str(sealed["total_price_net"]) if sealed.get("total_price_net") is not None else None,
            "total_price_tax": str(sealed["total_price_tax"]) if sealed.get("total_price_tax") is not None else None,
            "total_price_gross": selected_option["total_price_gross"],
            **{key: value for key, value in selected_option.items() if key not in ("currency", "revision_code", "snapshot_sha256", "total_price_gross")},
            "options": options, "valid_until": valid_until, "validity_days": days,
            "validity_expired": expired, "superseded": superseded,
            "successor_path": successor_path(approval, offering, project) if superseded else None,
            "expires_at": approval["expires_at"].isoformat(), "approval_status": state,
            "decided_by": None, "decided_note": None,
            "decided_at": ((decided or {}).get('decided_at') or approval['decided_at'] or legacy_approval).isoformat()
                if (decided or {}).get("decided_at") or approval["decided_at"] or legacy_approval else None,
            "payment": payment, "payment_provider": provider, "payment_url": payment_url,
            "quote_pdf_url": selected_option['quote_pdf_url']}


def decide(*, token, decision, decided_by, note=None, decided_rut=None, selected_revision=None,
           confirmed=False, consent_text=None, expected_offering_sha256=None, expected_selected_sha256=None,
           position_id=None, ip_address=None, user_agent=""):
    from portal import service
    with transaction.atomic(), service.portal_backend():
        approval = service._approval_for_token(token)
        lock_quote(approval['org_id'], approval['project_id'])
        project = service._live_project(approval, for_update=True)
        offering = service._bound_version(approval)
        previous = choice(approval["org_id"], offering["id"])
        if previous or approval["status"] != "PENDING":
            # The first human decision wins, including across different links.
            return read(token, track=False)
        if project["current_revision"] != offering["revision_code"]:
            raise DocumentaryError("quote_link_stale")
        if project["status"] != "QUOTED":
            raise DocumentaryError("quote_already_decided")
        if service._validity_expired(service._sealed_project(offering).get("quotation_valid_until")):
            raise DocumentaryError("quote_validity_expired")
        selected, _ = resolve_option(approval["org_id"], offering, selected_revision or offering["revision_code"])
        projected = option(selected, allow_pdf=False)
        if (expected_offering_sha256 != str(offering["snapshot_sha256"])
            or expected_selected_sha256 != str(selected["snapshot_sha256"])):
            raise DocumentaryError("quote_consent_stale", detail="La propuesta que está aceptando cambió. Consulte nuevamente el enlace y revise sus condiciones.")
        if decision == "APPROVED":
            if not decided_by.strip() or not valid_rut(decided_rut or "") or confirmed is not True:
                raise DocumentaryError("quote_consent_required", detail="Indique su nombre, un RUT válido y marque la aceptación de la propuesta y sus condiciones.")
            if projected["price_cause"] or not projected["consent_text"] or consent_text != projected["consent_text"]:
                raise DocumentaryError("quote_consent_stale", detail="Revise el importe y las condiciones de la opción elegida antes de aceptar.")
            if str(selected["id"]) != str(offering["id"]):
                conflicts = rows("SELECT 1 AS conflict WHERE EXISTS(SELECT 1 FROM public.project_payments "
                    "WHERE org_id=%s AND project_id=%s AND voided_at IS NULL) OR EXISTS(SELECT 1 FROM public.project_payment_links "
                    "WHERE org_id=%s AND project_id=%s AND status IN('DISPATCHING','PENDING','UNCERTAIN'))",
                    [approval["org_id"], approval["project_id"], approval["org_id"], approval["project_id"]])
                # Orders are checked through a nonpersonal scoped projection below.
                orders = one("SELECT private.quote_has_production(%s,%s) OR private.quote_has_conflicting_purchase(%s,%s,%s) "
                    "OR private.quote_has_conflicting_invoice(%s,%s,%s) AS present",
                    [approval["org_id"], approval["project_id"], approval["org_id"], approval["project_id"], selected['id'],
                     approval["org_id"], approval["project_id"], selected['id']])
                if conflicts or orders["present"]:
                    raise DocumentaryError("quote_option_committed", detail="El fabricante debe conciliar los cobros, documentos de cobro o la fabricación existentes antes de aceptar otra solución. Contáctelo para emitir una revisión nueva.")
        elif decision == "CHANGES_REQUESTED":
            if not (note or "").strip():
                raise DocumentaryError("quote_change_note_required", detail="Describa el cambio que necesita; puede indicar su posición exacta.")
        elif decision != "DECLINED":
            raise DocumentaryError("quote_decision_invalid")
        if position_id and str(position_id) not in {str(p["id"]) for p in projected["positions"]}:
            raise DocumentaryError("quote_position_not_offered")
        now = datetime.now(timezone.utc)
        evidence = {"name": decided_by.strip(), "rut": (decided_rut or "").strip(),
            "note": (note or "").strip(), "confirmed": confirmed is True,
            "consent": projected["consent_text"] if decision == "APPROVED" else None,
            "ip_address": ip_address, "user_agent": user_agent[:1024],
            "offering_revision": offering["revision_code"], "selected_revision": selected["revision_code"],
            "offering_sha256": str(offering["snapshot_sha256"]), "selected_sha256": str(selected["snapshot_sha256"])}
        one("INSERT INTO public.quote_decisions(id,org_id,project_id,offering_version_id,selected_version_id,approval_id,kind,"
            "decided_at,offering_sha256,selected_sha256,position_id,evidence) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb) RETURNING id",
            [uuid4(), approval["org_id"], approval["project_id"], offering["id"], selected["id"], approval["id"], decision,
             now, offering["snapshot_sha256"], selected["snapshot_sha256"], position_id,
             json.dumps(evidence, ensure_ascii=False)])
        write("UPDATE public.customer_approvals SET status=%s,decided_at=%s WHERE id=%s AND org_id=%s AND status='PENDING'",
              [decision, now, approval["id"], approval["org_id"]])
        if decision == "APPROVED":
            service._transition_project_approved(approval=approval, version_id=str(selected["id"]), now=now)
    return read(token, track=False)
