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
import os
import re
from datetime import timedelta, timezone as utc_timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import defusedxml.ElementTree as ET
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.db import connection, transaction
from django.utils import timezone

from authentication.errors import contract_error
from documents.repository import documentary_backend
from documents.storage import SupabaseDocumentStorage
from pricing.repository import one, rows
from projects import credit_notes

SIGNED_URL_TTL_SECONDS = 600

DTE_FACTURA = 33
DTE_CREDIT_NOTE = 61
_RUT_COMPACT = re.compile(r"^(\d{7,8})([\dK])$")


try:
    # SII timestamps are continental-Chile wall time.
    _SII_TZ = ZoneInfo("America/Santiago")
except ZoneInfoNotFoundError:  # pragma: no cover - container without tzdata
    _SII_TZ = utc_timezone(timedelta(hours=-3))


def _rut_dv(body: str) -> str:
    """Modulo-11 verifier digit of a RUT body ('76123456' → '0')."""
    total = sum(int(digit) * (2 + index % 6) for index, digit in enumerate(reversed(body)))
    dv = 11 - total % 11
    return "0" if dv == 11 else "K" if dv == 10 else str(dv)


def _rut_normalize(raw) -> str | None:
    """'12.345.678-k' → '12345678-K'; None when the shape or the verifier
    digit is wrong — a shape-valid bad RUT must never enter a sealed DTE."""
    compact = re.sub(r"[.\-\s]", "", str(raw or "")).upper()
    match = _RUT_COMPACT.match(compact)
    if match is None or _rut_dv(match.group(1)) != match.group(2):
        return None
    return f"{match.group(1)}-{match.group(2)}"


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
    if tipo_dte <= 0 or folio_desde < 1 or folio_desde > folio_hasta:
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
    try:
        blob = base64.b64decode(rsask, validate=True)
    except Exception as error:
        raise contract_error(
            422, "sii_caf_key_invalid", "La llave RSASK del CAF no es RSA válida."
        ) from error
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


def _latin1(xml: str) -> bytes:
    """DTE files are ISO-8859-1 per the SII convention — anything outside
    latin-1 can't be stamped and is refused rather than silently mangled."""
    try:
        return xml.encode("iso-8859-1")
    except UnicodeEncodeError as error:
        raise contract_error(
            422,
            "sii_dte_unrepresentable",
            "El DTE contiene caracteres no representables en ISO-8859-1.",
        ) from error


def _sign_dd(dd_xml: str, rsask: str, aad: bytes | None = None) -> str:
    key = _caf_private_key(_unwrap_rsask(rsask, aad))
    # The SII signs the DD as ISO-8859-1 bytes — UTF-8 would verify locally
    # and fail the SII verifier on every accented character.
    signature = key.sign(_latin1(dd_xml), padding.PKCS1v15(), hashes.SHA1())
    return base64.b64encode(signature).decode("ascii")


def _kek() -> bytes | None:
    """Key-encryption key for stored RSASK material: 32 bytes hex in
    ``SII_CAF_KEK`` — the fiscal signing key never persists as plaintext."""
    raw = os.environ.get("SII_CAF_KEK", "").strip()
    if not raw:
        return None
    try:
        key = bytes.fromhex(raw)
    except ValueError:
        return None
    return key if len(key) == 32 else None


def _caf_aad(org_id: str, tipo_dte: int, desde: int, hasta: int) -> bytes:
    """AES-GCM associated data binding a wrapped key to its exact CAF pool —
    ciphertext moved onto another row (or org) can never be decrypted."""
    return f"sii_cafs:{org_id}:{tipo_dte}:{desde}:{hasta}".encode("utf-8")


def _row_aad(org_id: str, caf: dict) -> bytes:
    return _caf_aad(
        org_id,
        int(caf["tipo_dte"]),
        int(caf["folio_desde"]),
        int(caf["folio_hasta"]),
    )


def _wrap_rsask(rsask: str, aad: bytes | None = None) -> str:
    """Envelope-encrypt the CAF private key (AES-256-GCM, fresh nonce) for
    storage. Refuses to persist plaintext — an unconfigured KEK fails closed."""
    kek = _kek()
    if kek is None:
        raise contract_error(
            503,
            "sii_kek_unconfigured",
            "SII_CAF_KEK no está configurado — las claves CAF no se almacenan en claro.",
        )
    nonce = os.urandom(12)
    blob = AESGCM(kek).encrypt(nonce, rsask.encode("utf-8"), aad)
    return (
        f"enc:v2:{base64.b64encode(nonce).decode()}"
        f":{base64.b64encode(blob).decode()}"
    )


def _unwrap_rsask(stored: str, aad: bytes | None = None) -> str:
    """Inverse of ``_wrap_rsask``; rows stored before envelope versions existed
    are still readable so a KEK rollout never strands an older pool."""
    if stored.startswith("enc:v2:"):
        versioned_aad: bytes | None = aad
    elif stored.startswith("enc:v1:"):
        versioned_aad = None
    else:
        return stored
    kek = _kek()
    if kek is None:
        raise contract_error(
            503,
            "sii_kek_unconfigured",
            "SII_CAF_KEK no está configurado — no se puede descifrar la clave CAF.",
        )
    _, _, nonce_b64, blob_b64 = stored.split(":", 3)
    try:
        return AESGCM(kek).decrypt(
            base64.b64decode(nonce_b64), base64.b64decode(blob_b64), versioned_aad
        ).decode("utf-8")
    except Exception as error:
        raise contract_error(
            422,
            "sii_caf_key_invalid",
            "La clave CAF almacenada no se pudo descifrar.",
        ) from error


def _ensure_rsask_wrapped(caf: dict, org_id: str) -> dict:
    """A plaintext RSASK row predates envelope encryption: re-wrap it now,
    inside the folio transaction, so no fiscal key is ever *used* from
    cleartext storage. Without a KEK it fails closed — plaintext never
    signs."""
    if caf["rsask"].startswith(("enc:v1:", "enc:v2:")):
        return caf
    wrapped = _wrap_rsask(caf["rsask"], _row_aad(org_id, caf))
    rows(
        "UPDATE public.sii_cafs SET rsask=%s "
        "WHERE id=%s AND org_id=%s RETURNING id",
        [wrapped, str(caf["id"]), org_id],
    )
    return {**caf, "rsask": wrapped}


def _assert_key_pair(parsed: dict) -> None:
    """The uploaded RSASK must be a valid RSA key matching the declared
    RSAPK modulus/exponent — a malformed or mismatched pool must never
    reach the folio registry."""
    key = _caf_private_key(parsed["rsask"])
    public = key.public_key().public_numbers()
    try:
        declared_n = int.from_bytes(base64.b64decode(parsed["rsapk_m"]), "big")
        declared_e = int.from_bytes(base64.b64decode(parsed["rsapk_e"]), "big")
    except Exception as error:
        raise contract_error(
            422, "sii_caf_invalid", "La clave pública RSAPK del CAF no es válida."
        ) from error
    if declared_n != public.n or declared_e != public.e:
        raise contract_error(
            422,
            "sii_caf_key_mismatch",
            "La llave privada del CAF no corresponde a la clave pública declarada.",
        )


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
        "acteco": row["acteco"],
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
    acteco: int | None = None,
) -> dict:
    """Register a CAF uploaded by the tenant. The CAF's own RUT/razón social
    are the emisor identity — the org's tax_id only guards a real-RUT
    mismatch, and overlapping folio ranges for the same DTE type are refused
    so allocation can never double-stamp."""
    if len((caf_xml or "").encode("utf-8")) > 131072:
        raise contract_error(
            422, "sii_caf_invalid", "El archivo CAF es demasiado grande."
        )
    parsed = _parse_caf(caf_xml)
    _assert_key_pair(parsed)
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
        if org_rut is None:
            raise contract_error(
                422,
                "sii_org_rut_missing",
                "Configure el RUT de la organización antes de registrar un CAF.",
            )
        if org_rut != parsed["rut_emisor"]:
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
            "razon_social,giro_emis,dir_origen,cmna_origen,acteco,caf_xml,rsask,"
            "rsapk_m,rsapk_e,file_sha256,uploaded_by) "
            "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *",
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
                acteco,
                parsed["caf_xml"],
                _wrap_rsask(
                    parsed["rsask"],
                    _caf_aad(
                        org_id_s,
                        parsed["tipo_dte"],
                        parsed["folio_desde"],
                        parsed["folio_hasta"],
                    ),
                ),
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
    receptor_extra: str,
    deal: dict,
    item: str,
    caf: dict,
    issued_at,
    referencia: str = "",
) -> str:
    """Minimal DTE skeleton shared by 33/61: Encabezado + one Detalle + the
    TED (DD + FRMT SHA1withRSA stamped by the CAF key)."""
    # A DTE is a peso document: a foreign-currency deal would lose its
    # currency entirely, so it refuses here rather than emitting wrong numbers.
    if str(deal.get("currency") or "CLP").upper() != "CLP":
        raise contract_error(
            422,
            "sii_currency_unsupported",
            "El DTE sólo timbra documentos en CLP — este está en "
            f"{deal.get('currency')}.",
        )
    amounts = [
        Decimal(str(deal[key]))
        for key in ("total_gross", "total_net", "total_tax")
    ]
    if any(amount != amount.to_integral_value() for amount in amounts):
        raise contract_error(
            422,
            "sii_amount_fractional",
            "Los totales del documento no son enteros — el DTE no puede "
            "truncarlos.",
        )
    total, neto, iva = (int(amount) for amount in amounts)
    # This renderer only supports the standard 19% IVA: a document priced
    # under a different rate would emit contradictory fiscal fields, so it
    # is refused rather than stamped with a wrong TasaIVA.
    if iva != int(
        (neto * Decimal("0.19")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    ) or total != neto + iva:
        raise contract_error(
            422,
            "sii_tax_rate_unsupported",
            "El documento no lleva IVA 19% — el DTE no puede timbrarlo.",
        )
    # A DTE is rejected by the SII schema without the emisor's activity code
    # and business address — refuse before a folio is ever allocated.
    if not all(
        caf.get(key)
        for key in ("giro_emis", "dir_origen", "cmna_origen", "acteco")
    ):
        raise contract_error(
            422,
            "sii_emisor_incomplete",
            "El CAF no trae giro, dirección, comuna ni acteco del emisor.",
        )
    local = issued_at.astimezone(_SII_TZ)
    fecha = local.date().isoformat()
    tsted = local.strftime("%Y-%m-%dT%H:%M:%S")
    emisor_extra = "".join(
        f"<{tag}>{escape(str(caf[key]))}</{tag}>"
        for tag, key in (
            ("GiroEmis", "giro_emis"),
            ("Acteco", "acteco"),
            ("DirOrigen", "dir_origen"),
            ("CmnaOrigen", "cmna_origen"),
        )
    )
    # The DD is signed as serialized — build it once, byte-exact.
    dd = (
        f"<DD><RE>{caf['rut_emisor']}</RE><TD>{tipo}</TD><F>{folio}</F>"
        f"<FE>{fecha}</FE><RR>{receptor}</RR><RSR>{escape(receptor_name[:40])}</RSR>"
        f"<MNT>{total}</MNT><IT1>{escape(item)}</IT1>{caf['caf_xml']}"
        f"<TSTED>{tsted}</TSTED></DD>"
    )
    frmt = _sign_dd(dd, caf["rsask"], _row_aad(str(caf["org_id"]), caf))
    return (
        '<?xml version="1.0" encoding="ISO-8859-1"?>'
        f'<DTE version="1.0" xmlns="http://www.sii.cl/SiiDte">'
        f'<Documento ID="F{tipo}T{folio}">'
        f"<Encabezado><IdDoc><TipoDTE>{tipo}</TipoDTE>"
        f"<Folio>{folio}</Folio><FchEmis>{fecha}</FchEmis></IdDoc>"
        f"<Emisor><RUTEmisor>{caf['rut_emisor']}</RUTEmisor>"
        f"<RznSoc>{escape(caf['razon_social'])}</RznSoc>{emisor_extra}</Emisor>"
        f"<Receptor><RUTRecep>{receptor}</RUTRecep>"
        f"<RznSocRecep>{escape(receptor_name)}</RznSocRecep>{receptor_extra}</Receptor>"
        f"<Totales><MntNeto>{neto}</MntNeto><TasaIVA>19</TasaIVA>"
        f"<IVA>{iva}</IVA><MntTotal>{total}</MntTotal></Totales></Encabezado>"
        f"<Detalle><NroLinDet>1</NroLinDet><NmbItem>{escape(item)}</NmbItem>"
        f"<MontoItem>{neto}</MontoItem></Detalle>{referencia}"
        f'<TED version="1.0">{dd}<FRMT algoritmo="SHA1withRSA">{frmt}</FRMT></TED>'
        f"<TmstFirma>{tsted}</TmstFirma></Documento></DTE>"
    )


def _encode_dte(xml: str) -> bytes:
    """Serialize the DTE as the SII's ISO-8859-1 bytes."""
    return _latin1(xml)


def _receptor(payload: dict) -> tuple[str, str, str]:
    project = payload["project"]
    receptor = _rut_normalize(project.get("client_rut"))
    if receptor is None:
        raise contract_error(
            422,
            "sii_receptor_missing",
            "El documento no tiene un RUT de receptor válido para timbrar.",
        )
    receptor_fields = ("client_giro", "client_comuna", "client_address")
    if not all(str(project.get(key) or "").strip() for key in receptor_fields):
        raise contract_error(
            422,
            "sii_receptor_incomplete",
            "Faltan giro, comuna y dirección del receptor para timbrar.",
        )
    receptor_extra = "".join(
        f"<{tag}>{escape(str(project[key]).strip())}</{tag}>"
        for tag, key in (
            ("GiroRecep", "client_giro"),
            ("DirRecep", "client_address"),
            ("CmnaRecep", "client_comuna"),
        )
    )
    return receptor, str(project.get("client_name") or "Cliente").strip(), receptor_extra


def _dte_xml(*, folio: int, invoice: dict, caf: dict, issued_at) -> str:
    """DTE-33: one Detalle referencing the sealed quotation."""
    payload = (
        invoice["payload_json"]
        if isinstance(invoice["payload_json"], dict)
        else json.loads(invoice["payload_json"])
    )
    receptor, receptor_name, receptor_extra = _receptor(payload)
    revision = payload.get("revision_code") or "REV-A"
    positions = payload.get("positions") or []
    item = f"Según cotización {revision} - {len(positions)} posición(es)"
    return _render_dte(
        tipo=DTE_FACTURA,
        folio=folio,
        receptor=receptor,
        receptor_name=receptor_name,
        receptor_extra=receptor_extra,
        deal=payload["deal"],
        item=item,
        caf=caf,
        issued_at=issued_at,
    )


def _dte_xml_credit_note(
    *, folio: int, credit_note: dict, parent_dte: dict, caf: dict, issued_at
) -> str:
    """DTE-61: annuls a factura — its <Referencia> points at the parent's
    stamped folio (CodRef=1)."""
    payload = (
        credit_note["payload_json"]
        if isinstance(credit_note["payload_json"], dict)
        else json.loads(credit_note["payload_json"])
    )
    receptor, receptor_name, receptor_extra = _receptor(payload)
    item = f"Anula factura {payload['invoice']['invoice_code']}"
    if payload.get("reason"):
        item = f"{item} - {payload['reason']}"
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
        receptor_extra=receptor_extra,
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
            annulled = rows(
                "SELECT id FROM public.project_credit_notes "
                "WHERE org_id=%s AND invoice_id=%s LIMIT 1",
                [org_id_s, invoice_id_s],
            )
            if annulled:
                raise contract_error(
                    409,
                    "invoice_already_annulled",
                    "La factura está anulada por una nota de crédito — timbre el DTE-61 sobre la nota.",
                )
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
            caf = _ensure_rsask_wrapped(cafs[0], org_id_s)
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
            content = _encode_dte(
                _dte_xml(folio=folio, invoice=invoice, caf=caf, issued_at=issued_at)
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
        str(row["invoice_id"]): _dte_public(row)
        for row in rows(
            "SELECT * FROM public.project_dtes "
            "WHERE org_id=%s AND project_id=%s",
            [str(org_id), str(project_id)],
        )
    }


def emit_credit_note_dte(
    *,
    org_id: UUID,
    project: dict,
    invoice_id: UUID,
    actor_id: UUID,
    reason: str | None = None,
) -> dict:
    """Timbra the electronic annulment of a stamped factura: seals the nota
    de crédito document AND its DTE-61 in one transaction — a factura the
    SII stamped is annulled electronically, never by a paper-only note.
    The NC's <Referencia> points at the parent's stamped folio (CodRef=1),
    so the parent's DTE-33 must exist first. UNIQUE(invoice_id) on the
    credit note and UNIQUE(org_id, credit_note_id) on the DTE make a
    retried emit replay the same artifacts."""
    org_id_s, project_id_s, invoice_id_s = str(org_id), str(project["id"]), str(invoice_id)
    object_key: str | None = None
    credit_object_key: str | None = None
    try:
        with transaction.atomic(), documentary_backend():
            invoice = one(
                "SELECT * FROM public.project_invoices "
                "WHERE id=%s AND org_id=%s AND project_id=%s",
                [invoice_id_s, org_id_s, project_id_s],
                "invoice_not_found",
            )
            # Org slots serialize NC creation and folio allocation: the
            # replay checks below can never race a second click on the
            # same invoice.
            one(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                [f"project_credit_notes:{org_id_s}"],
            )
            one(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                [f"sii_folios:{org_id_s}:{DTE_CREDIT_NOTE}"],
            )
            parents = rows(
                "SELECT * FROM public.project_dtes "
                "WHERE org_id=%s AND invoice_id=%s AND credit_note_id IS NULL "
                "AND dte_type=%s",
                [org_id_s, invoice_id_s, DTE_FACTURA],
            )
            if not parents:
                raise contract_error(
                    409,
                    "sii_reference_missing",
                    "La factura debe timbrarse antes de emitir la nota de crédito electrónica.",
                )
            parent_dte = parents[0]
            notes = rows(
                "SELECT * FROM public.project_credit_notes "
                "WHERE invoice_id=%s AND org_id=%s",
                [invoice_id_s, org_id_s],
            )
            if notes:
                credit_note = notes[0]
                existing = rows(
                    "SELECT * FROM public.project_dtes "
                    "WHERE org_id=%s AND credit_note_id=%s",
                    [org_id_s, str(credit_note["id"])],
                )
                if existing:
                    return _dte_public(existing[0])
            else:
                # The electronic annulment seals its own counter-document:
                # NC PDF + DTE-61 commit or roll back together.
                credit_note, credit_object_key = credit_notes.seal_credit_note(
                    invoice=invoice,
                    org_id_s=org_id_s,
                    project_id_s=project_id_s,
                    project=project,
                    reason=reason,
                    actor_id=actor_id,
                )
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
            caf = _ensure_rsask_wrapped(cafs[0], org_id_s)
            folio = int(caf["folio_actual"]) + 1
            if folio > int(caf["folio_hasta"]):
                raise contract_error(
                    409,
                    "sii_caf_exhausted",
                    "No hay folios CAF tipo 61 disponibles — cargue un CAF en Configuración.",
                )
            issued_at = timezone.now()
            content = _encode_dte(
                _dte_xml_credit_note(
                    folio=folio,
                    credit_note=credit_note,
                    parent_dte=parent_dte,
                    caf=caf,
                    issued_at=issued_at,
                )
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
                        str(credit_note["id"]),
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
        if credit_object_key is not None:
            credit_notes._purge_unreferenced_credit_note(
                org_id=org_id, object_key=credit_object_key
            )
        raise
    return _dte_public(row)


def credit_note_dte_access(*, org_id: UUID, project_id: UUID, invoice_id: UUID) -> dict:
    with documentary_backend():
        found = rows(
            "SELECT * FROM public.project_dtes "
            "WHERE org_id=%s AND project_id=%s AND invoice_id=%s "
            "AND credit_note_id IS NOT NULL",
            [str(org_id), str(project_id), str(invoice_id)],
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
    """credit_note_id → DTE badge for the cobranza listing."""
    return {
        str(row["credit_note_id"]): _dte_public(row)
        for row in rows(
            "SELECT * FROM public.project_dtes "
            "WHERE org_id=%s AND project_id=%s AND credit_note_id IS NOT NULL",
            [str(org_id), str(project_id)],
        )
    }
