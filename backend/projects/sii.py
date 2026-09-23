"""SII electronic invoicing — CAF folio pools and the sealed DTE-33 artifact.

A Chilean factura is not legally electronic until it carries a *timbre* — a
folio from a CAF (Código de Autorización de Folios) the SII issued to the
emisor, plus the TED signature stamped with the CAF's private key. This module
keeps the org's CAF pool, allocates folios inside one serialized transaction
(the same folio can never be stamped twice), renders the DTE XML from the
sealed invoice payload, and stores the artifact as immutable evidence.

Scope note: this emits the *timbraje* — the internally signed DTE with TED.
Transport to SII (envío DTE) and the enveloped XML-DSig certificate are the
next slice; the stored XML is already a reviewable, verifiable artifact.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
from decimal import Decimal
from uuid import UUID
from xml.sax.saxutils import escape

import defusedxml.ElementTree as ET
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from django.db import connection, transaction
from django.utils import timezone

from authentication.errors import contract_error
from documents.repository import documentary_backend
from documents.storage import SupabaseDocumentStorage
from pricing.repository import one, rows

SIGNED_URL_TTL_SECONDS = 600

DTE_FACTURA = 33
DTE_CREDIT_NOTE = 61
_RUT_COMPACT = re.compile(r"^(\d{7,8})([\dK])$")


def _rut_normalize(raw) -> str | None:
    """'12.345.678-k' → '12345678-K'; None when the value is not a RUT."""
    compact = re.sub(r"[.\-\s]", "", str(raw or "")).upper()
    match = _RUT_COMPACT.match(compact)
    return f"{match.group(1)}-{match.group(2)}" if match else None


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _tag_text(node, tag: str) -> str:
    value = node.findtext(tag)
    if value is None or not value.strip():
        raise contract_error(422, "sii_caf_invalid", f"El CAF no trae {tag}.")
    return value.strip()


def _parse_caf(xml_text: str) -> dict:
    """Structure-check a SII CAF: defused parse, DA envelope, folio range,
    RSA key material. Returns the canonical CAF fragment (embedded verbatim
    inside the TED's DD) plus the key material needed to stamp FRMT."""
    try:
        root = ET.fromstring(xml_text or "")
    except Exception as error:
        raise contract_error(
            422, "sii_caf_invalid", "El archivo CAF no es un XML válido."
        ) from error
    caf = root if root.tag == "CAF" else root.find("CAF")
    if caf is None or caf.find("DA") is None:
        raise contract_error(
            422, "sii_caf_invalid", "El archivo no es un CAF del SII."
        )
    da = caf.find("DA")
    rng = da.find("RNG")
    rsapk = da.find("RSAPK")
    if rng is None or rsapk is None:
        raise contract_error(
            422, "sii_caf_invalid", "El CAF no trae rango de folios ni clave."
        )
    try:
        tipo_dte = int(_tag_text(da, "TD"))
        folio_desde = int(_tag_text(rng, "D"))
        folio_hasta = int(_tag_text(rng, "H"))
    except ValueError as error:
        raise contract_error(
            422, "sii_caf_invalid", "El rango o tipo de DTE del CAF no es válido."
        ) from error
    if tipo_dte <= 0 or folio_desde > folio_hasta:
        raise contract_error(
            422, "sii_caf_invalid", "El rango o tipo de DTE del CAF no es válido."
        )
    rut = _rut_normalize(_tag_text(da, "RE"))
    if rut is None:
        raise contract_error(
            422, "sii_caf_invalid", "El RUT emisor del CAF no es válido."
        )
    rsask = (root.findtext("RSASK") or "").strip()
    if not rsask:
        raise contract_error(
            422, "sii_caf_invalid", "El CAF no trae la llave privada (RSASK)."
        )
    return {
        "tipo_dte": tipo_dte,
        "folio_desde": folio_desde,
        "folio_hasta": folio_hasta,
        "rut_emisor": rut,
        "razon_social": _tag_text(da, "RS"),
        "rsapk_m": _tag_text(rsapk, "M"),
        "rsapk_e": _tag_text(rsapk, "E"),
        "rsask": rsask,
        "caf_xml": ET.tostring(caf, encoding="unicode"),
    }


def _caf_private_key(rsask: str):
    """SII ships RSASK as base64 DER PKCS#1; PEM/base64 fallbacks tolerated."""
    blob = base64.b64decode(rsask, validate=True)
    loaders = (
        lambda: serialization.load_der_private_key(blob, password=None),
        lambda: serialization.load_pem_private_key(blob, password=None),
    )
    for load in loaders:
        try:
            return load()
        except Exception:
            continue
    raise contract_error(
        422, "sii_caf_key_invalid", "La llave RSASK del CAF no es RSA válida."
    )


def _sign_dd(dd_xml: str, rsask: str) -> str:
    key = _caf_private_key(rsask)
    signature = key.sign(dd_xml.encode("utf-8"), padding.PKCS1v15(), hashes.SHA1())
    return base64.b64encode(signature).decode("ascii")


def _caf_public(row) -> dict:
    hasta, actual = int(row["folio_hasta"]), int(row["folio_actual"])
    return {
        "id": str(row["id"]),
        "tipo_dte": int(row["tipo_dte"]),
        "folio_desde": int(row["folio_desde"]),
        "folio_hasta": hasta,
        "folio_actual": actual,
        "remaining": hasta - actual,
        "rut_emisor": row["rut_emisor"],
        "razon_social": row["razon_social"],
        "created_at": row["created_at"].isoformat()
        if hasattr(row["created_at"], "isoformat")
        else row["created_at"],
    }


def _dte_public(row) -> dict:
    return {
        "id": str(row["id"]),
        "invoice_id": str(row["invoice_id"]),
        "dte_type": int(row["dte_type"]),
        "folio": int(row["folio"]),
        "issued_at": row["issued_at"].isoformat()
        if hasattr(row["issued_at"], "isoformat")
        else row["issued_at"],
    }


def list_cafs(*, org_id: UUID) -> list[dict]:
    with documentary_backend():
        return [
            _caf_public(row)
            for row in rows(
                "SELECT * FROM public.sii_cafs WHERE org_id=%s "
                "ORDER BY tipo_dte, folio_desde",
                [str(org_id)],
            )
        ]


def register_caf(
    *,
    org_id: UUID,
    actor_id: UUID,
    caf_xml: str,
    giro_emis: str | None = None,
    dir_origen: str | None = None,
    cmna_origen: str | None = None,
) -> dict:
    """Register a CAF uploaded by the tenant. The CAF's own RUT/razón social
    are the emisor identity — the org's tax_id only guards a real-RUT
    mismatch, and overlapping folio ranges for the same DTE type are refused
    so allocation can never double-stamp."""
    parsed = _parse_caf(caf_xml)
    file_hash = _sha256((caf_xml or "").encode("utf-8"))
    org_id_s = str(org_id)
    with transaction.atomic(), documentary_backend():
        one(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
            [f"sii_cafs:{org_id_s}"],
        )
        org = one(
            "SELECT id, tax_id, name FROM public.tenancy_organizations WHERE id=%s",
            [org_id_s],
            "org_not_found",
        )
        org_rut = _rut_normalize(org["tax_id"])
        if org_rut is not None and org_rut != parsed["rut_emisor"]:
            raise contract_error(
                409,
                "sii_caf_org_mismatch",
                "El CAF pertenece a otro RUT emisor que esta organización.",
            )
        overlapping = rows(
            "SELECT id FROM public.sii_cafs "
            "WHERE org_id=%s AND tipo_dte=%s AND NOT (folio_hasta < %s OR folio_desde > %s)",
            [org_id_s, parsed["tipo_dte"], parsed["folio_desde"], parsed["folio_hasta"]],
        )
        if overlapping:
            raise contract_error(
                409,
                "sii_caf_overlap",
                "El rango de folios se cruza con un CAF ya cargado.",
            )
        row = one(
            "INSERT INTO public.sii_cafs("
            "org_id,tipo_dte,folio_desde,folio_hasta,folio_actual,rut_emisor,"
            "razon_social,giro_emis,dir_origen,cmna_origen,caf_xml,rsask,"
            "rsapk_m,rsapk_e,file_sha256,uploaded_by) "
            "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *",
            [
                org_id_s,
                parsed["tipo_dte"],
                parsed["folio_desde"],
                parsed["folio_hasta"],
                parsed["folio_desde"] - 1,
                parsed["rut_emisor"],
                parsed["razon_social"],
                (giro_emis or "").strip() or None,
                (dir_origen or "").strip() or None,
                (cmna_origen or "").strip() or None,
                parsed["caf_xml"],
                parsed["rsask"],
                parsed["rsapk_m"],
                parsed["rsapk_e"],
                file_hash,
                str(actor_id),
            ],
        )
    return _caf_public(row)


def _render_dte(
    *,
    tipo: int,
    folio: int,
    receptor: str,
    receptor_name: str,
    deal: dict,
    item: str,
    caf: dict,
    issued_at,
    dir_recep: str = "",
    referencia: str = "",
) -> bytes:
    """Minimal DTE skeleton shared by 33/61: Encabezado + one Detalle + the
    TED (DD + FRMT SHA1withRSA stamped by the CAF key)."""
    total = int(Decimal(str(deal["total_gross"])))
    neto = int(Decimal(str(deal["total_net"])))
    iva = int(Decimal(str(deal["total_tax"])))
    fecha = issued_at.date().isoformat()
    emisor_extra = ""
    for tag, value in (
        ("GiroEmis", caf.get("giro_emis")),
        ("DirOrigen", caf.get("dir_origen")),
        ("CmnaOrigen", caf.get("cmna_origen")),
    ):
        if value:
            emisor_extra += f"<{tag}>{escape(str(value))}</{tag}>"

    # The DD is signed as serialized — build it once, byte-exact.
    dd = (
        f"<DD><RE>{caf['rut_emisor']}</RE><TD>{tipo}</TD><F>{folio}</F>"
        f"<FE>{fecha}</FE><RR>{receptor}</RR><RSR>{escape(receptor_name)}</RSR>"
        f"<MNT>{total}</MNT><IT1>{escape(item)}</IT1>{caf['caf_xml']}"
        f"<TSTED>{issued_at.isoformat()}</TSTED></DD>"
    )
    frmt = _sign_dd(dd, caf["rsask"])
    return (
        f'<DTE version="1.0"><Documento ID="F{tipo}T{folio}">'
        f"<Encabezado><IdDoc><TipoDTE>{tipo}</TipoDTE>"
        f"<Folio>{folio}</Folio><FchEmis>{fecha}</FchEmis></IdDoc>"
        f"<Emisor><RUTEmisor>{caf['rut_emisor']}</RUTEmisor>"
        f"<RznSoc>{escape(caf['razon_social'])}</RznSoc>{emisor_extra}</Emisor>"
        f"<Receptor><RUTRecep>{receptor}</RUTRecep>"
        f"<RznSocRecep>{escape(receptor_name)}</RznSocRecep>{dir_recep}</Receptor>"
        f"<Totales><MntNeto>{neto}</MntNeto><TasaIVA>19</TasaIVA>"
        f"<IVA>{iva}</IVA><MntTotal>{total}</MntTotal></Totales></Encabezado>"
        f"<Detalle><NroLinDet>1</NroLinDet><NmbItem>{escape(item)}</NmbItem>"
        f"<MontoItem>{neto}</MontoItem></Detalle>{referencia}"
        f'<TED version="1.0">{dd}<FRMT algoritmo="SHA1withRSA">{frmt}</FRMT></TED>'
        f"</Documento></DTE>"
    ).encode("utf-8")


def _receptor(payload: dict) -> tuple[str, str]:
    project = payload["project"]
    receptor = _rut_normalize(project.get("client_rut"))
    if receptor is None:
        raise contract_error(
            422,
            "sii_receptor_missing",
            "El documento no tiene un RUT de receptor válido para timbrar.",
        )
    return receptor, str(project.get("client_name") or "Cliente").strip()


def _dte_xml(*, folio: int, invoice: dict, caf: dict, issued_at) -> bytes:
    """DTE-33: one Detalle referencing the sealed quotation."""
    payload = (
        invoice["payload_json"]
        if isinstance(invoice["payload_json"], dict)
        else json.loads(invoice["payload_json"])
    )
    receptor, receptor_name = _receptor(payload)
    project = payload["project"]
    revision = payload.get("revision_code") or "REV-A"
    positions = payload.get("positions") or []
    item = f"Según cotización {revision} — {len(positions)} posición(es)"
    dir_recep = (
        f"<DirRecep>{escape(str(project['delivery_address']))}</DirRecep>"
        if project.get("delivery_address")
        else ""
    )
    return _render_dte(
        tipo=DTE_FACTURA,
        folio=folio,
        receptor=receptor,
        receptor_name=receptor_name,
        deal=payload["deal"],
        item=item,
        caf=caf,
        issued_at=issued_at,
        dir_recep=dir_recep,
    )


def _dte_xml_credit_note(
    *, folio: int, credit_note: dict, parent_dte: dict, caf: dict, issued_at
) -> bytes:
    """DTE-61: annuls a factura — its <Referencia> points at the parent's
    stamped folio (CodRef=1)."""
    payload = (
        credit_note["payload_json"]
        if isinstance(credit_note["payload_json"], dict)
        else json.loads(credit_note["payload_json"])
    )
    receptor, receptor_name = _receptor(payload)
    item = f"Anula factura {payload['invoice']['invoice_code']}"
    if payload.get("reason"):
        item = f"{item} — {payload['reason']}"
    referencia = (
        f"<Referencia><TpoDocRef>{DTE_FACTURA}</TpoDocRef>"
        f"<FolioRef>{int(parent_dte['folio'])}</FolioRef>"
        f"<CodRef>1</CodRef>"
        f"<RazonRef>{escape(payload.get('reason') or 'Anula documento')}</RazonRef>"
        f"</Referencia>"
    )
    return _render_dte(
        tipo=DTE_CREDIT_NOTE,
        folio=folio,
        receptor=receptor,
        receptor_name=receptor_name,
        deal=payload["deal"],
        item=item,
        caf=caf,
        issued_at=issued_at,
        referencia=referencia,
    )


def emit_dte(*, org_id: UUID, project: dict, invoice_id: UUID, actor_id: UUID) -> dict:
    """Timbra a sealed factura: allocate the next folio from the org's CAF
    pool and store the signed DTE XML as immutable evidence. UNIQUE
    (org_id, invoice_id) makes a retried emit replay the sealed artifact."""
    org_id_s, project_id_s, invoice_id_s = str(org_id), str(project["id"]), str(invoice_id)
    object_key: str | None = None
    try:
        with transaction.atomic(), documentary_backend():
            invoice = one(
                "SELECT * FROM public.project_invoices "
                "WHERE id=%s AND org_id=%s AND project_id=%s",
                [invoice_id_s, org_id_s, project_id_s],
                "invoice_not_found",
            )
            # The org folio slot serializes every emit; the existing-row
            # check runs inside it so two concurrent emits on the same
            # invoice can't both pass the replay check.
            one(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                [f"sii_folios:{org_id_s}:{DTE_FACTURA}"],
            )
            existing = rows(
                "SELECT * FROM public.project_dtes "
                "WHERE org_id=%s AND invoice_id=%s",
                [org_id_s, invoice_id_s],
            )
            if existing:
                return _dte_public(existing[0])
            cafs = rows(
                "SELECT * FROM public.sii_cafs "
                "WHERE org_id=%s AND tipo_dte=%s AND folio_actual < folio_hasta "
                "ORDER BY folio_desde LIMIT 1 FOR UPDATE",
                [org_id_s, DTE_FACTURA],
            )
            if not cafs:
                raise contract_error(
                    409,
                    "sii_caf_exhausted",
                    "No hay folios CAF disponibles — cargue un CAF en Configuración.",
                )
            caf = cafs[0]
            folio = int(caf["folio_actual"]) + 1
            if folio > int(caf["folio_hasta"]):
                raise contract_error(
                    409,
                    "sii_caf_exhausted",
                    "No hay folios CAF disponibles — cargue un CAF en Configuración.",
                )
            issued_at = timezone.now()
            # The DD is stamped before the cursor commits: a receptor/XML
            # failure aborts the transaction with the folio still untouched.
            content = _dte_xml(folio=folio, invoice=invoice, caf=caf, issued_at=issued_at)
            moved = rows(
                "UPDATE public.sii_cafs SET folio_actual=%s "
                "WHERE id=%s AND org_id=%s AND folio_actual=%s "
                "RETURNING folio_actual",
                [folio, str(caf["id"]), org_id_s, folio - 1],
            )
            if not moved:
                raise contract_error(
                    409,
                    "sii_caf_exhausted",
                    "No hay folios CAF disponibles — cargue un CAF en Configuración.",
                )
            content_hash = _sha256(content)
            payload = {
                "dte_type": DTE_FACTURA,
                "folio": folio,
                "issued_at": issued_at.isoformat(),
                "invoice_code": invoice["invoice_code"],
                "caf": {
                    "id": str(caf["id"]),
                    "folio_desde": int(caf["folio_desde"]),
                    "folio_hasta": int(caf["folio_hasta"]),
                },
                "emisor": {
                    "rut": caf["rut_emisor"],
                    "razon_social": caf["razon_social"],
                },
            }
            object_key = (
                f"org_{org_id_s}/projects/{project_id_s}/dtes/"
                f"dte{DTE_FACTURA}-{folio}_{content_hash[:16]}.xml"
            )
            storage = SupabaseDocumentStorage()
            try:
                storage.upload_immutable(object_key, content, "application/xml")
                row = one(
                    "INSERT INTO public.project_dtes("
                    "org_id,project_id,invoice_id,caf_id,dte_type,folio,"
                    "payload_json,storage_bucket,storage_object_key,file_sha256,"
                    "media_type,byte_size,issued_by,issued_at) "
                    "VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,'documents',%s,%s,"
                    "'application/xml',%s,%s,%s) RETURNING *",
                    [
                        org_id_s,
                        project_id_s,
                        invoice_id_s,
                        str(caf["id"]),
                        DTE_FACTURA,
                        folio,
                        json.dumps(payload),
                        object_key,
                        content_hash,
                        len(content),
                        str(actor_id),
                        issued_at,
                    ],
                )
            except Exception:
                try:
                    storage.delete_object(object_key)
                    object_key = None
                except Exception:  # noqa: BLE001 — cleanup must not mask the real failure
                    pass
                raise
    except Exception:
        if object_key is not None:
            _purge_unreferenced_dte(
                org_id=org_id, object_key=object_key, tipo=DTE_FACTURA
            )
        raise
    return _dte_public(row)


def dte_access(*, org_id: UUID, project_id: UUID, invoice_id: UUID) -> dict:
    with documentary_backend():
        found = rows(
            "SELECT * FROM public.project_dtes "
            "WHERE org_id=%s AND project_id=%s AND invoice_id=%s",
            [str(org_id), str(project_id), str(invoice_id)],
        )
        if not found:
            raise contract_error(404, "dte_not_found", "La factura no tiene DTE emitido.")
        found = found[0]
        signed_url = SupabaseDocumentStorage().signed_url(
            str(found["storage_object_key"]), expires_in=SIGNED_URL_TTL_SECONDS
        )
    return {
        **_dte_public(found),
        "signed_url": signed_url,
        "expires_in": SIGNED_URL_TTL_SECONDS,
    }


def _purge_unreferenced_dte(
    *, org_id: UUID, object_key: str, tipo: int
) -> None:
    """Compensating delete for a rolled-back DTE: the org folio slot
    serializes against emit — a committed row referencing the key wins,
    an orphan is removed without masking the original failure."""
    import logging

    try:
        with transaction.atomic(), documentary_backend():
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                    [f"sii_folios:{org_id}:{tipo}"],
                )
            referenced = rows(
                "SELECT id FROM public.project_dtes "
                "WHERE org_id=%s AND storage_object_key=%s",
                [str(org_id), object_key],
            )
            if referenced:
                return
            SupabaseDocumentStorage().delete_object(object_key)
    except Exception as cleanup_error:  # noqa: BLE001
        logging.getLogger(__name__).warning(
            "project_dte_cleanup_failed",
            extra={"storage_object_key": object_key, "cleanup_error": str(cleanup_error)},
        )


def dtes_by_invoice(*, org_id: UUID, project_id: UUID) -> dict:
    """invoice_id → light DTE badge for the cobranza invoice listing."""
    return {
        str(row["invoice_id"]): {
            "id": str(row["id"]),
            "dte_type": int(row["dte_type"]),
            "folio": int(row["folio"]),
        }
        for row in rows(
            "SELECT id, invoice_id, dte_type, folio FROM public.project_dtes "
            "WHERE org_id=%s AND project_id=%s",
            [str(org_id), str(project_id)],
        )
    }


def emit_credit_note_dte(
    *, org_id: UUID, project: dict, credit_note_id: UUID, actor_id: UUID
) -> dict:
    """Timbra a nota de crédito as DTE-61. Its <Referencia> points at the
    parent factura's stamped folio, so the parent's DTE-33 must exist —
    a credit note can never invent a folio the SII didn't issue.
    UNIQUE(org_id, credit_note_id) makes a retried emit replay the row."""
    org_id_s, project_id_s, credit_id_s = (
        str(org_id),
        str(project["id"]),
        str(credit_note_id),
    )
    object_key: str | None = None
    try:
        with transaction.atomic(), documentary_backend():
            credit_note = one(
                "SELECT * FROM public.project_credit_notes "
                "WHERE id=%s AND org_id=%s AND project_id=%s",
                [credit_id_s, org_id_s, project_id_s],
                "credit_note_not_found",
            )
            one(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                [f"sii_folios:{org_id_s}:{DTE_CREDIT_NOTE}"],
            )
            existing = rows(
                "SELECT * FROM public.project_dtes "
                "WHERE org_id=%s AND credit_note_id=%s",
                [org_id_s, credit_id_s],
            )
            if existing:
                return _dte_public(existing[0])
            parents = rows(
                "SELECT * FROM public.project_dtes "
                "WHERE org_id=%s AND invoice_id=%s AND credit_note_id IS NULL "
                "AND dte_type=%s",
                [org_id_s, str(credit_note["invoice_id"]), DTE_FACTURA],
            )
            if not parents:
                raise contract_error(
                    409,
                    "sii_reference_missing",
                    "La factura debe timbrarse antes de emitir la nota de crédito electrónica.",
                )
            parent_dte = parents[0]
            cafs = rows(
                "SELECT * FROM public.sii_cafs "
                "WHERE org_id=%s AND tipo_dte=%s AND folio_actual < folio_hasta "
                "ORDER BY folio_desde LIMIT 1 FOR UPDATE",
                [org_id_s, DTE_CREDIT_NOTE],
            )
            if not cafs:
                raise contract_error(
                    409,
                    "sii_caf_exhausted",
                    "No hay folios CAF tipo 61 disponibles — cargue un CAF en Configuración.",
                )
            caf = cafs[0]
            folio = int(caf["folio_actual"]) + 1
            if folio > int(caf["folio_hasta"]):
                raise contract_error(
                    409,
                    "sii_caf_exhausted",
                    "No hay folios CAF tipo 61 disponibles — cargue un CAF en Configuración.",
                )
            issued_at = timezone.now()
            content = _dte_xml_credit_note(
                folio=folio,
                credit_note=credit_note,
                parent_dte=parent_dte,
                caf=caf,
                issued_at=issued_at,
            )
            moved = rows(
                "UPDATE public.sii_cafs SET folio_actual=%s "
                "WHERE id=%s AND org_id=%s AND folio_actual=%s "
                "RETURNING folio_actual",
                [folio, str(caf["id"]), org_id_s, folio - 1],
            )
            if not moved:
                raise contract_error(
                    409,
                    "sii_caf_exhausted",
                    "No hay folios CAF tipo 61 disponibles — cargue un CAF en Configuración.",
                )
            content_hash = _sha256(content)
            payload = {
                "dte_type": DTE_CREDIT_NOTE,
                "folio": folio,
                "issued_at": issued_at.isoformat(),
                "credit_code": credit_note["credit_code"],
                "referenced": {
                    "invoice_code": credit_note["payload_json"]["invoice"]["invoice_code"]
                    if isinstance(credit_note["payload_json"], dict)
                    else json.loads(credit_note["payload_json"])["invoice"]["invoice_code"],
                    "folio": int(parent_dte["folio"]),
                },
                "caf": {
                    "id": str(caf["id"]),
                    "folio_desde": int(caf["folio_desde"]),
                    "folio_hasta": int(caf["folio_hasta"]),
                },
                "emisor": {
                    "rut": caf["rut_emisor"],
                    "razon_social": caf["razon_social"],
                },
            }
            object_key = (
                f"org_{org_id_s}/projects/{project_id_s}/dtes/"
                f"dte{DTE_CREDIT_NOTE}-{folio}_{content_hash[:16]}.xml"
            )
            storage = SupabaseDocumentStorage()
            try:
                storage.upload_immutable(object_key, content, "application/xml")
                row = one(
                    "INSERT INTO public.project_dtes("
                    "org_id,project_id,invoice_id,credit_note_id,caf_id,dte_type,folio,"
                    "payload_json,storage_bucket,storage_object_key,file_sha256,"
                    "media_type,byte_size,issued_by,issued_at) "
                    "VALUES(%s,%s,%s,%s,%s,%s,%s,%s::jsonb,'documents',%s,%s,"
                    "'application/xml',%s,%s,%s) RETURNING *",
                    [
                        org_id_s,
                        project_id_s,
                        str(credit_note["invoice_id"]),
                        credit_id_s,
                        str(caf["id"]),
                        DTE_CREDIT_NOTE,
                        folio,
                        json.dumps(payload),
                        object_key,
                        content_hash,
                        len(content),
                        str(actor_id),
                        issued_at,
                    ],
                )
            except Exception:
                try:
                    storage.delete_object(object_key)
                    object_key = None
                except Exception:  # noqa: BLE001 — cleanup must not mask the real failure
                    pass
                raise
    except Exception:
        if object_key is not None:
            _purge_unreferenced_dte(
                org_id=org_id, object_key=object_key, tipo=DTE_CREDIT_NOTE
            )
        raise
    return _dte_public(row)


def credit_note_dte_access(*, org_id: UUID, project_id: UUID, credit_note_id: UUID) -> dict:
    with documentary_backend():
        found = rows(
            "SELECT * FROM public.project_dtes "
            "WHERE org_id=%s AND project_id=%s AND credit_note_id=%s",
            [str(org_id), str(project_id), str(credit_note_id)],
        )
        if not found:
            raise contract_error(
                404, "dte_not_found", "La nota de crédito no tiene DTE emitido."
            )
        found = found[0]
        signed_url = SupabaseDocumentStorage().signed_url(
            str(found["storage_object_key"]), expires_in=SIGNED_URL_TTL_SECONDS
        )
    return {
        **_dte_public(found),
        "signed_url": signed_url,
        "expires_in": SIGNED_URL_TTL_SECONDS,
    }


def dtes_by_credit_note(*, org_id: UUID, project_id: UUID) -> dict:
    """credit_note_id → light DTE badge for the cobranza listing."""
    return {
        str(row["credit_note_id"]): {
            "id": str(row["id"]),
            "dte_type": int(row["dte_type"]),
            "folio": int(row["folio"]),
        }
        for row in rows(
            "SELECT id, credit_note_id, dte_type, folio FROM public.project_dtes "
            "WHERE org_id=%s AND project_id=%s AND credit_note_id IS NOT NULL",
            [str(org_id), str(project_id)],
        )
    }
