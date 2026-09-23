"""SII envío — the transport layer that turns a stamped DTE into a real tax
document.

A timbrado (the sealed DTE artifact emitted by ``projects.sii``) only reaches
the SII inside a signed ``<EnvioDTE>`` envelope: a ``<SetDTE>`` carries a
``<Caratula>`` identifying the sender plus the DTE itself, and both the DTE's
``<Documento>`` and the envelope are signed XML-DSig with the organization's
digital certificate — a different credential from the CAF's RSASK, owned by a
person the SII authorized to send documents for the company.

The envío row seals the envelope XML as immutable evidence; ``status`` /
``track_id`` / ``glosa`` are the SII-side lifecycle and mutate backend-only
(PENDING → ACCEPTED/REJECTED), the same discipline as the CAF folio cursor.
Submission goes through a small adapter: the real SII webservice when
``SII_WS_ENVIO_URL`` is configured, an explicit deterministic mock otherwise —
the sealed payload always records which adapter answered.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone as utc_timezone
from uuid import UUID

import httpx
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from django.db import transaction
from django.utils import timezone
from lxml import etree

from authentication.errors import contract_error
from documents.repository import documentary_backend
from documents.storage import SupabaseDocumentStorage
from pricing.repository import one, rows
from projects.sii import (
    SIGNED_URL_TTL_SECONDS,
    _rut_normalize,
    _sha256,
    _unwrap_rsask,
    _wrap_rsask,
)

# The SII is the fixed receptor of every envío envelope.
SII_RECEPTOR_RUT = "60803000-K"
_DS = "http://www.w3.org/2000/09/xmldsig#"
_C14N = "http://www.w3.org/TR/2001/REC-xml-c14n-20010315"
_ENVIO_STATUSES = ("PENDING", "ACCEPTED", "REJECTED")
_MAX_PFX_BYTES = 65536
_RUT_IN_TEXT = re.compile(r"\b\d{7,8}-[\dkK]\b")

try:
    # SII timestamps are continental-Chile wall time.
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

    _SII_TZ = ZoneInfo("America/Santiago")
except ZoneInfoNotFoundError:  # pragma: no cover - container without tzdata
    _SII_TZ = utc_timezone(timedelta(hours=-3))


def _cert_aad(org_id: str, file_sha256: str) -> bytes:
    """AES-GCM associated data binding the wrapped pfx to its org + content —
    ciphertext copied onto another row can never be decrypted."""
    return f"sii_certificates:{org_id}:{file_sha256}".encode("utf-8")


def _cert_rut(cert: x509.Certificate) -> str | None:
    """The signing person's RUT inside a SII personal certificate lives in the
    subject — usually serialNumber, sometimes folded into the CN."""
    for attribute in cert.subject:
        for match in _RUT_IN_TEXT.findall(str(attribute.value or "")):
            normalized = _rut_normalize(match)
            if normalized is not None:
                return normalized
    return None


def _load_pfx(pfx: bytes, password: str | None) -> tuple:
    try:
        key, cert, _extra = pkcs12.load_key_and_certificates(
            pfx, password.encode("utf-8") if password else None
        )
    except Exception as error:
        raise contract_error(
            422, "sii_cert_invalid", "El certificado no se pudo abrir."
        ) from error
    if key is None or cert is None:
        raise contract_error(
            422, "sii_cert_invalid", "El archivo no trae llave privada y certificado."
        )
    if not isinstance(key, rsa.RSAPrivateKey):
        raise contract_error(
            422, "sii_cert_not_rsa", "El certificado debe tener una llave RSA."
        )
    return key, cert


def _cert_public(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "subject": row["subject"],
        "rut_firma": row["rut_firma"],
        "serial_number": row.get("serial_number"),
        "valid_from": str(row["valid_from"]),
        "valid_to": str(row["valid_to"]),
        "nro_resol": int(row["nro_resol"]),
        "fch_resol": str(row["fch_resol"]),
        "active": bool(row["active"]),
        "created_at": str(row["created_at"]),
    }


def certificate_status(*, org_id: UUID) -> dict | None:
    """Public metadata of the org's active certificate — never key material."""
    found = rows(
        "SELECT * FROM public.sii_certificates WHERE org_id=%s AND active",
        [str(org_id)],
    )
    return _cert_public(found[0]) if found else None


def upload_certificate(
    *,
    org_id: UUID,
    actor_id: UUID,
    pfx_b64: str,
    password: str | None,
    nro_resol: int,
    fch_resol: str,
) -> dict:
    """Install the org's digital certificate: validate the .pfx is a real RSA
    credential carrying a RUT, not expired, then store the blob wrapped with
    the deployment KEK. Uploading a new certificate retires the previous one —
    envíos always sign with the single active row."""
    try:
        pfx = base64.b64decode(pfx_b64 or "", validate=True)
    except Exception as error:
        raise contract_error(
            422, "sii_cert_invalid", "El certificado no es base64 válido."
        ) from error
    if not pfx or len(pfx) > _MAX_PFX_BYTES:
        raise contract_error(
            422, "sii_cert_invalid", "El tamaño del certificado no es válido."
        )
    _key, cert = _load_pfx(pfx, password)
    if _cert_rut(cert) is None:
        raise contract_error(
            422, "sii_cert_rut_missing", "El certificado no identifica un RUT de firmante."
        )
    now = timezone.now()
    try:
        valid_to = cert.not_valid_after_utc
        valid_from = cert.not_valid_before_utc
    except AttributeError:  # pragma: no cover - cryptography < 42
        valid_to = cert.not_valid_after.replace(tzinfo=utc_timezone.utc)
        valid_from = cert.not_valid_before.replace(tzinfo=utc_timezone.utc)
    if valid_to <= now:
        raise contract_error(
            422, "sii_cert_expired", "El certificado está vencido."
        )
    try:
        resol_date = datetime.strptime(str(fch_resol or "")[:10], "%Y-%m-%d").date()
    except ValueError as error:
        raise contract_error(
            422, "sii_resolucion_invalid", "La fecha de resolución no es válida."
        ) from error
    file_hash = _sha256(pfx)
    aad = _cert_aad(str(org_id), file_hash)
    org_id_s = str(org_id)
    with transaction.atomic(), documentary_backend():
        one(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
            [f"sii_certs:{org_id_s}"],
        )
        rows(
            "UPDATE public.sii_certificates SET active=false "
            "WHERE org_id=%s AND active RETURNING id",
            [org_id_s],
        )
        row = one(
            "INSERT INTO public.sii_certificates("
            "org_id,subject,rut_firma,serial_number,valid_from,valid_to,"
            "pfx_wrapped,password_wrapped,file_sha256,nro_resol,fch_resol,"
            "active,uploaded_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,true,%s) "
            "RETURNING *",
            [
                org_id_s,
                cert.subject.rfc4514_string()[:256],
                _cert_rut(cert),
                format(cert.serial_number, "d")[:40] or None,
                valid_from,
                valid_to,
                _wrap_rsask(base64.b64encode(pfx).decode("ascii"), aad),
                _wrap_rsask(password, aad) if password else None,
                file_hash,
                int(nro_resol),
                resol_date,
                str(actor_id),
            ],
        )
    return _cert_public(row)


def _cert_material(cert_row: dict) -> tuple:
    """Unwrap the stored pfx and return (private_key, certificate)."""
    aad = _cert_aad(str(cert_row["org_id"]), str(cert_row["file_sha256"]))
    pfx = base64.b64decode(_unwrap_rsask(str(cert_row["pfx_wrapped"]), aad))
    password = (
        _unwrap_rsask(str(cert_row["password_wrapped"]), aad)
        if cert_row.get("password_wrapped")
        else None
    )
    return _load_pfx(pfx, password)


def _c14n(element) -> bytes:
    """Canonical XML (REC-xml-c14n-20010315, inclusive, no comments) — the
    byte form both signatures digest."""
    return etree.tostring(element, method="c14n", with_comments=False)


def _rsa_key_value(privkey) -> tuple[str, str]:
    numbers = privkey.public_key().public_numbers()
    modulus = numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, "big")
    exponent = numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, "big")
    return (
        base64.b64encode(modulus).decode("ascii"),
        base64.b64encode(exponent).decode("ascii"),
    )


def _find_id(root, element_id: str):
    for element in root.iter():
        if element.get("ID") == element_id:
            return element
    raise ValueError(f"element {element_id} not found")


def _build_signature(target_id: str, digest_b64: str, privkey,
                     cert_der_b64: str) -> str:
    """The <Signature> element over an element already digested. Enveloped
    transform — the signature itself never enters the digest — RSA-SHA1."""
    modulus, exponent = _rsa_key_value(privkey)
    return (
        f'<Signature xmlns="{_DS}">'
        f"<SignedInfo>"
        f'<CanonicalizationMethod Algorithm="{_C14N}"/>'
        f'<SignatureMethod Algorithm="{_DS}rsa-sha1"/>'
        f'<Reference URI="#{target_id}">'
        f'<Transforms><Transform Algorithm="{_DS}enveloped-signature"/></Transforms>'
        f'<DigestMethod Algorithm="{_DS}sha1"/>'
        f"<DigestValue>{digest_b64}</DigestValue>"
        f"</Reference></SignedInfo>"
        f"<SignatureValue></SignatureValue>"
        f"<KeyInfo><KeyValue><RSAKeyValue>"
        f"<Modulus>{modulus}</Modulus><Exponent>{exponent}</Exponent>"
        f"</RSAKeyValue></KeyValue>"
        f"<X509Data><X509Certificate>{cert_der_b64}</X509Certificate></X509Data>"
        f"</KeyInfo></Signature>"
    )


def _envelope_sign(root, target_id: str, privkey, cert_der_b64: str) -> None:
    """Append an enveloped xmldsig Signature over the element carrying
    ID=target_id: digest the target before the Signature exists (enveloped
    transform removes it from the digest anyway), then sign the SignedInfo
    in final context so ancestor namespaces digest identically on verify."""
    target = _find_id(root, target_id)
    digest = base64.b64encode(hashlib.sha1(_c14n(target)).digest()).decode("ascii")
    skeleton = _build_signature(target_id, digest, privkey, cert_der_b64)
    signature_el = etree.fromstring(skeleton.encode("utf-8"))
    target.append(signature_el)
    signed_info = signature_el.find(f"{{{_DS}}}SignedInfo")
    signature_el.find(f"{{{_DS}}}SignatureValue").text = base64.b64encode(
        privkey.sign(_c14n(signed_info), padding.PKCS1v15(), hashes.SHA1())
    ).decode("ascii")


def _render_envio_envelope(
    dte_xml: bytes,
    dte: dict,
    privkey,
    cert: x509.Certificate,
    caf: dict,
    cert_row: dict,
    sent_at,
) -> bytes:
    """Build the full <EnvioDTE>: embed the stored DTE unsigned, then sign
    Documento *inside the envelope* and finally SetDoc. c14n pulls in-scope
    ancestor namespaces into the digest — signing before embedding would
    produce a SignedInfo that no longer canonicalizes identically once
    EnvioDTE's xmlns:xsi is in scope, so both signatures are created in the
    tree's final shape. The stored timbraje file is never touched."""
    dte_root = etree.fromstring(dte_xml)
    cert_der_b64 = base64.b64encode(
        cert.public_bytes(serialization.Encoding.DER)
    ).decode("ascii")
    local = sent_at.astimezone(_SII_TZ)
    tmst = local.strftime("%Y-%m-%dT%H:%M:%S")
    caratula = (
        f'<Caratula version="1.0"><RutEmisor>{caf["rut_emisor"]}</RutEmisor>'
        f"<RutEnvia>{cert_row['rut_firma']}</RutEnvia>"
        f"<RutReceptor>{SII_RECEPTOR_RUT}</RutReceptor>"
        f"<FchResol>{cert_row['fch_resol']}</FchResol>"
        f"<NroResol>{int(cert_row['nro_resol'])}</NroResol>"
        f"<TmstFirmaEnv>{tmst}</TmstFirmaEnv></Caratula>"
    )
    dte_inner = etree.tostring(dte_root, encoding="unicode")
    envelope_xml = (
        '<EnvioDTE xmlns="http://www.sii.cl/SiiDte" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:schemaLocation="http://www.sii.cl/SiiDte EnvioDTE_v10.xsd" '
        'version="1.0"><SetDTE ID="SetDoc">'
        f"{caratula}{dte_inner}</SetDTE></EnvioDTE>"
    )
    env_root = etree.fromstring(envelope_xml.encode("utf-8"))
    documento_id = f"F{int(dte['dte_type'])}T{int(dte['folio'])}"
    _envelope_sign(env_root, documento_id, privkey, cert_der_b64)
    _envelope_sign(env_root, "SetDoc", privkey, cert_der_b64)
    return etree.tostring(env_root, encoding="iso-8859-1", xml_declaration=True)


class _MockSiiClient:
    """Deterministic local stand-in for the SII webservice — every response
    is stamped ``adapter=mock`` in the sealed payload so a simulated envío
    is never mistaken for a real submission."""

    adapter = "mock"

    def submit(self, content: bytes, *, rut_emisor: str, rut_envia: str) -> dict:
        return {
            "track_id": f"MOCK-{hashlib.sha256(content).hexdigest()[:12].upper()}",
            "status": "ACCEPTED",
            "glosa": "Envío simulado localmente",
        }


class _HttpSiiClient:
    """Real submission seam: posts the EnvioDTE envelope to the configured
    SII endpoint and parses the TRACKID out of the response."""

    adapter = "sii-ws"

    def __init__(self, url: str) -> None:
        self._url = url

    def submit(self, content: bytes, *, rut_emisor: str, rut_envia: str) -> dict:
        response = httpx.post(
            self._url,
            content=content,
            headers={"Content-Type": "application/xml"},
            timeout=30,
        )
        if response.status_code != 200:
            raise contract_error(
                503,
                "sii_envio_unreachable",
                f"El SII respondió {response.status_code} — el envío no quedó registrado.",
            )
        match = re.search(r"<TRACKID>(\d+)</TRACKID>", response.text or "")
        if match is None:
            raise contract_error(
                502,
                "sii_envio_bad_response",
                "La respuesta del SII no trae TRACKID.",
            )
        return {"track_id": match.group(1), "status": "ACCEPTED", "glosa": None}


def _sii_client():
    url = os.environ.get("SII_WS_ENVIO_URL", "").strip()
    if url:
        return _HttpSiiClient(url)
    return _MockSiiClient()


def _envio_public(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "dte_id": str(row["dte_id"]),
        "status": row["status"],
        "track_id": row.get("track_id"),
        "glosa": row.get("glosa"),
        "sent_at": str(row["sent_at"]),
    }


def _purge_unreferenced_envio(*, org_id: UUID, object_key: str) -> None:
    """Compensating delete for a rolled-back envío: an orphan object is
    removed without masking the original failure."""
    try:
        SupabaseDocumentStorage().delete_object(object_key)
    except Exception as cleanup_error:  # noqa: BLE001
        logging.getLogger(__name__).warning(
            "envio_cleanup_failed",
            extra={"storage_object_key": object_key, "cleanup_error": str(cleanup_error)},
        )


def send_invoice_envio(
    *, org_id: UUID, project_id: UUID, invoice_id: UUID, actor_id: UUID
) -> dict:
    """Submit a stamped factura's DTE to the SII: seal the EnvioDTE envelope
    (document signature + set signature, both with the org certificate) and
    dispatch it through the configured adapter. UNIQUE (org_id, dte_id)
    makes a retried send replay the stored envío."""
    org_id_s, invoice_id_s = str(org_id), str(invoice_id)
    project_id_s = str(project_id)
    object_key: str | None = None
    try:
        with transaction.atomic(), documentary_backend():
            dte = rows(
                "SELECT * FROM public.project_dtes "
                "WHERE org_id=%s AND invoice_id=%s AND credit_note_id IS NULL",
                [org_id_s, invoice_id_s],
            )
            if not dte:
                raise contract_error(
                    409,
                    "sii_dte_missing",
                    "La factura aún no está timbrada — emita el DTE primero.",
                )
            dte = dte[0]
            one(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                [f"sii_envios:{org_id_s}:{dte['id']}"],
            )
            existing = rows(
                "SELECT * FROM public.sii_envios WHERE org_id=%s AND dte_id=%s",
                [org_id_s, str(dte["id"])],
            )
            if existing:
                return _envio_public(existing[0])
            cert_rows = rows(
                "SELECT * FROM public.sii_certificates WHERE org_id=%s AND active",
                [org_id_s],
            )
            if not cert_rows:
                raise contract_error(
                    409,
                    "sii_certificate_missing",
                    "Suba el certificado digital de la empresa antes de enviar al SII.",
                )
            cert_row = cert_rows[0]
            valid_to = cert_row["valid_to"]
            if valid_to.tzinfo is None:
                valid_to = valid_to.replace(tzinfo=utc_timezone.utc)
            if valid_to <= timezone.now():
                raise contract_error(
                    409, "sii_cert_expired", "El certificado digital está vencido."
                )
            caf = one(
                "SELECT * FROM public.sii_cafs WHERE id=%s",
                [str(dte["caf_id"])],
                "sii_caf_missing",
            )
            storage = SupabaseDocumentStorage()
            dte_xml = storage.download(str(dte["storage_object_key"]))
            privkey, cert = _cert_material(cert_row)
            sent_at = timezone.now()
            envelope = _render_envio_envelope(
                dte_xml, dte, privkey, cert, caf, cert_row, sent_at
            )
            envelope_hash = _sha256(envelope)
            object_key = (
                f"org_{org_id_s}/projects/{project_id_s}/envios/"
                f"envio-dte{dte['dte_type']}-{dte['folio']}_{envelope_hash[:16]}.xml"
            )
            storage.upload_immutable(object_key, envelope, "application/xml")
            try:
                row = one(
                    "INSERT INTO public.sii_envios("
                    "org_id,project_id,dte_id,status,payload_json,storage_bucket,"
                    "storage_object_key,file_sha256,media_type,byte_size,sent_by,"
                    "sent_at) VALUES(%s,%s,%s,'PENDING',%s,'documents',%s,%s,"
                    "'application/xml',%s,%s,%s) RETURNING *",
                    [
                        org_id_s,
                        project_id_s,
                        str(dte["id"]),
                        json.dumps(
                            {
                                "dte_type": int(dte["dte_type"]),
                                "folio": int(dte["folio"]),
                                "dte_id": str(dte["id"]),
                                "caf_id": str(caf["id"]),
                                "emisor": {
                                    "rut": caf["rut_emisor"],
                                    "razon_social": caf["razon_social"],
                                },
                                "envia": cert_row["rut_firma"],
                                "caratula": {
                                    "nro_resol": int(cert_row["nro_resol"]),
                                    "fch_resol": str(cert_row["fch_resol"]),
                                    "rut_receptor": SII_RECEPTOR_RUT,
                                },
                            }
                        ),
                        object_key,
                        envelope_hash,
                        len(envelope),
                        str(actor_id),
                        sent_at,
                    ],
                )
            except Exception:
                storage.delete_object(object_key)
                object_key = None
                raise
            client = _sii_client()
            result = client.submit(
                envelope,
                rut_emisor=str(caf["rut_emisor"]),
                rut_envia=str(cert_row["rut_firma"]),
            )
            status = result["status"] if result["status"] in _ENVIO_STATUSES else "PENDING"
            row = one(
                "UPDATE public.sii_envios SET status=%s, track_id=%s, glosa=%s,"
                "payload_json = payload_json || %s::jsonb WHERE id=%s RETURNING *",
                [
                    status,
                    result.get("track_id"),
                    result.get("glosa"),
                    json.dumps(
                        {
                            "adapter": client.adapter,
                            "track_id": result.get("track_id"),
                        }
                    ),
                    str(row["id"]),
                ],
            )
            return _envio_public(row)
    except Exception:
        if object_key is not None:
            _purge_unreferenced_envio(org_id=org_id, object_key=object_key)
        raise


def envios_by_invoice(*, org_id: UUID, project_id: UUID) -> dict:
    """invoice_id → light envío badge for the cobranza invoice listing —
    only the parent factura's envío."""
    return {
        str(row["invoice_id"]): {
            "id": str(row["id"]),
            "status": row["status"],
            "track_id": row["track_id"],
        }
        for row in rows(
            "SELECT e.id, e.status, e.track_id, d.invoice_id "
            "FROM public.sii_envios e "
            "JOIN public.project_dtes d ON d.id = e.dte_id "
            "WHERE e.org_id=%s AND e.project_id=%s AND d.credit_note_id IS NULL",
            [str(org_id), str(project_id)],
        )
    }


def invoice_envio_access(*, org_id: UUID, invoice_id: UUID) -> dict:
    """Read the envío of an invoice's DTE — public row plus a short-lived
    signed URL to the sealed envelope."""
    with documentary_backend():
        found = rows(
            "SELECT e.* FROM public.sii_envios e "
            "JOIN public.project_dtes d ON d.id = e.dte_id "
            "WHERE e.org_id=%s AND d.invoice_id=%s AND d.credit_note_id IS NULL",
            [str(org_id), str(invoice_id)],
        )
        if not found:
            raise contract_error(
                404, "sii_envio_missing", "El DTE de la factura no fue enviado."
            )
        row = found[0]
    storage = SupabaseDocumentStorage()
    out = _envio_public(row)
    out["signed_url"] = storage.signed_url(
        str(row["storage_object_key"]), expires_in=SIGNED_URL_TTL_SECONDS
    )
    return out
