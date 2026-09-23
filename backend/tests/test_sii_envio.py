"""SII envío — certificate upload/wrapping, envelope signing, send + replay."""

import base64
import hashlib
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone as utc_timezone
from uuid import uuid4

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID
from lxml import etree

from authentication.errors import ContractAPIException
from projects import sii, sii_envio


class _Storage:
    def __init__(self):
        self.uploads = []
        self.deleted = []
        self.objects = {}

    def upload_immutable(self, object_key, content, content_type):
        self.uploads.append((object_key, content, content_type))
        self.objects[object_key] = content

    def download(self, object_key):
        return self.objects[object_key]

    def delete_object(self, object_key):
        self.deleted.append(object_key)

    def signed_url(self, object_key, expires_in=None):
        return f"https://storage.test/{object_key}?exp={expires_in}"


@contextmanager
def _noop(*args, **kwargs):
    yield


def _rsa_key():
    return rsa.generate_private_key(3, 2048)


def _self_signed(key, rut="13037614-2", expired=False):
    name = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, "Firmante Prueba"),
            x509.NameAttribute(NameOID.SERIAL_NUMBER, rut),
        ]
    )
    now = datetime.now(utc_timezone.utc)
    builder = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=400 if expired else 1))
        .not_valid_after(now - timedelta(days=1) if expired else now + timedelta(days=365))
    )
    return builder.sign(key, hashes.SHA256())


def _pfx(password=b"secret", rut="13037614-2", key=None, expired=False):
    key = key or _rsa_key()
    cert = _self_signed(key, rut=rut, expired=expired)
    encryption = (
        serialization.BestAvailableEncryption(password)
        if password
        else serialization.NoEncryption()
    )
    return pkcs12.serialize_key_and_certificates(
        name=b"cert", key=key, cert=cert, cas=None, encryption_algorithm=encryption
    ), key, cert


def _cert_row(org_id, pfx, password="secret", over=None):
    file_hash = sii_envio._sha256(pfx)
    aad = sii_envio._cert_aad(str(org_id), file_hash)
    now = datetime.now(utc_timezone.utc)
    row = {
        "id": uuid4(),
        "org_id": org_id,
        "subject": "CN=Firmante Prueba",
        "rut_firma": "13037614-2",
        "serial_number": "123",
        "valid_from": now - timedelta(days=1),
        "valid_to": now + timedelta(days=365),
        "pfx_wrapped": sii._wrap_rsask(base64.b64encode(pfx).decode("ascii"), aad),
        "password_wrapped": sii._wrap_rsask(password, aad) if password else None,
        "file_sha256": file_hash,
        "nro_resol": 0,
        "fch_resol": "2026-10-01",
        "active": True,
        "uploaded_by": uuid4(),
        "created_at": now,
    }
    row.update(over or {})
    return row


def _dte_xml(folio=7):
    return (
        '<?xml version="1.0" encoding="ISO-8859-1"?>'
        '<DTE xmlns="http://www.sii.cl/SiiDte" version="1.0">'
        f'<Documento ID="F33T{folio}">'
        "<Encabezado><IdDoc><TipoDTE>33</TipoDTE>"
        f"<Folio>{folio}</Folio><FchEmis>2026-10-02</FchEmis></IdDoc>"
        "<Emisor><RUTEmisor>76123456-0</RUTEmisor></Emisor>"
        "<Receptor><RUTRecep>76543210-3</RUTRecep></Receptor>"
        "<Totales><MntTotal>1190</MntTotal></Totales></Encabezado>"
        "<Detalle><NroLinDet>1</NroLinDet><NmbItem>VENTANA</NmbItem>"
        "<QtyItem>1</QtyItem><MontoItem>1000</MontoItem></Detalle>"
        '<TED version="1.0"><DD><RE>76123456-0</RE><TD>33</TD>'
        f"<F>{folio}</F><ND>0</ND><RR>76543210-3</RR><RSR>C</RSR>"
        "<MNT>1190</MNT><IT1>VENTANA</IT1><CAF/>"
        "<TSTED>2026-10-02T10:00:00</TSTED></DD>"
        '<FRMT algoritmo="SHA1withRSA">eA==</FRMT></TED>'
        "<TmstFirma>2026-10-02T10:00:00</TmstFirma>"
        "</Documento></DTE>"
    ).encode("iso-8859-1")


def _dte_row(org_id, invoice_id, caf_id, folio=7, over=None):
    row = {
        "id": uuid4(),
        "org_id": org_id,
        "project_id": uuid4(),
        "invoice_id": invoice_id,
        "credit_note_id": None,
        "dte_type": 33,
        "folio": folio,
        "caf_id": caf_id,
        "storage_object_key": f"org_{org_id}/dtes/dte33-{folio}.xml",
        "issued_at": "2026-10-02T10:00:00+00:00",
    }
    row.update(over or {})
    return row


def _patch_envio(
    monkeypatch,
    storage,
    *,
    dte=None,
    existing_envio=None,
    certs=None,
    caf=None,
    client=None,
    insert_row=None,
):
    state = {"inserted": None}

    def fake_one(sql, params=None, *args, **kw):
        text = str(sql)
        if "INSERT INTO public.sii_envios" in text:
            row = insert_row or {
                "id": uuid4(),
                "dte_id": (dte[0]["id"] if dte else uuid4()),
                "status": "PENDING",
                "track_id": None,
                "glosa": None,
                "sent_at": "2026-10-03T10:00:00+00:00",
            }
            state["inserted"] = row
            return row
        if "UPDATE public.sii_envios" in text:
            row = dict(state["inserted"] or {})
            row.update(
                {"status": params[0], "track_id": params[1], "glosa": params[2]}
            )
            return row
        if "INSERT INTO public.sii_certificates" in text:
            return {
                "id": uuid4(),
                "org_id": uuid4(),
                "subject": params[1],
                "rut_firma": params[2],
                "serial_number": params[3],
                "valid_from": params[4],
                "valid_to": params[5],
                "pfx_wrapped": params[6],
                "password_wrapped": params[7],
                "file_sha256": params[8],
                "nro_resol": params[9],
                "fch_resol": params[10],
                "active": True,
                "created_at": "2026-10-03T10:00:00+00:00",
            }
        if "FROM public.sii_cafs" in text:
            if caf is None:
                raise ContractAPIException(404, "sii_caf_missing", "x")
            return caf
        if "pg_advisory_xact_lock" in text:
            return {}
        return {}

    def fake_rows(sql, params=None):
        if "FROM public.project_dtes" in sql:
            return list(dte or [])
        if "FROM public.sii_envios" in sql:
            return list(existing_envio or [])
        if "FROM public.sii_certificates" in sql and "SET active=false" in sql:
            return []
        if "FROM public.sii_certificates" in sql:
            return list(certs or [])
        return []

    monkeypatch.setattr(sii_envio, "one", fake_one)
    monkeypatch.setattr(sii_envio, "rows", fake_rows)
    monkeypatch.setattr(sii, "_kek", lambda: b"\x01" * 32)
    monkeypatch.setattr(sii_envio, "SupabaseDocumentStorage", lambda: storage)
    monkeypatch.setattr(sii_envio.transaction, "atomic", _noop)
    monkeypatch.setattr(sii_envio, "documentary_backend", _noop)
    if client is not None:
        monkeypatch.setattr(sii_envio, "_sii_client", lambda: client)
    return state


def _caf(org_id):
    return {
        "id": uuid4(),
        "org_id": org_id,
        "rut_emisor": "76123456-0",
        "razon_social": "Ventanas Prueba SpA",
    }


def test_upload_certificate_wraps_and_stores():
    storage = _Storage()
    org_id = uuid4()
    pfx, _key, cert = _pfx()
    with pytest.MonkeyPatch.context() as mp:
        _patch_envio(mp, storage)
        result = sii_envio.upload_certificate(
            org_id=org_id,
            actor_id=uuid4(),
            pfx_b64=base64.b64encode(pfx).decode("ascii"),
            password="secret",
            nro_resol=0,
            fch_resol="2026-10-01",
        )
    assert result["rut_firma"] == "13037614-2"
    assert result["active"] is True


def test_upload_certificate_rejects_bad_base64():
    with pytest.MonkeyPatch.context() as mp:
        _patch_envio(mp, _Storage())
        with pytest.raises(ContractAPIException) as error:
            sii_envio.upload_certificate(
                org_id=uuid4(),
                actor_id=uuid4(),
                pfx_b64="%%%",
                password=None,
                nro_resol=0,
                fch_resol="2026-10-01",
            )
    assert error.value.contract_code == "sii_cert_invalid"


def test_upload_certificate_rejects_no_rut_cert():
    # name without any RUT: a cert whose subject carries no RUT at all
    key = _rsa_key()
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Sin Rut")])
    now = datetime.now(utc_timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=365))
        .sign(key, hashes.SHA256())
    )
    pfx = pkcs12.serialize_key_and_certificates(
        name=b"c",
        key=key,
        cert=cert,
        cas=None,
        encryption_algorithm=serialization.NoEncryption(),
    )
    with pytest.MonkeyPatch.context() as mp:
        _patch_envio(mp, _Storage())
        with pytest.raises(ContractAPIException) as error:
            sii_envio.upload_certificate(
                org_id=uuid4(),
                actor_id=uuid4(),
                pfx_b64=base64.b64encode(pfx).decode("ascii"),
                password=None,
                nro_resol=0,
                fch_resol="2026-10-01",
            )
    assert error.value.contract_code == "sii_cert_rut_missing"


def test_upload_certificate_rejects_expired():
    pfx, _key, _cert = _pfx(expired=True)
    with pytest.MonkeyPatch.context() as mp:
        _patch_envio(mp, _Storage())
        with pytest.raises(ContractAPIException) as error:
            sii_envio.upload_certificate(
                org_id=uuid4(),
                actor_id=uuid4(),
                pfx_b64=base64.b64encode(pfx).decode("ascii"),
                password="secret",
                nro_resol=0,
                fch_resol="2026-10-01",
            )
    assert error.value.contract_code == "sii_cert_expired"


def test_upload_certificate_rejects_non_rsa():
    key = ec.generate_private_key(ec.SECP256R1())
    cert = _self_signed(key)
    pfx = pkcs12.serialize_key_and_certificates(
        name=b"c",
        key=key,
        cert=cert,
        cas=None,
        encryption_algorithm=serialization.NoEncryption(),
    )
    with pytest.MonkeyPatch.context() as mp:
        _patch_envio(mp, _Storage())
        with pytest.raises(ContractAPIException) as error:
            sii_envio.upload_certificate(
                org_id=uuid4(),
                actor_id=uuid4(),
                pfx_b64=base64.b64encode(pfx).decode("ascii"),
                password=None,
                nro_resol=0,
                fch_resol="2026-10-01",
            )
    assert error.value.contract_code == "sii_cert_not_rsa"


def _verify_signature(target, cert):
    """Verify one enveloped RSA-SHA1 signature on ``target``: DigestValue must
    match sha1(c14n(target minus its Signature)) and SignatureValue must
    verify over c14n(SignedInfo) with the cert's public key. The signed
    Signature is always the target's last child — a descendant find would hit
    the Documento's own signature inside a SetDTE. The digest runs in place:
    detaching the node would drop in-scope ancestor namespaces that c14n
    includes."""
    sig = target[-1]
    assert sig.tag == f"{{{sii_envio._DS}}}Signature"
    signed_info = sig.find(f"{{{sii_envio._DS}}}SignedInfo")
    digest_value = signed_info.find(
        f"{{{sii_envio._DS}}}Reference/{{{sii_envio._DS}}}DigestValue"
    ).text
    signature_b64 = sig.find(f"{{{sii_envio._DS}}}SignatureValue").text
    cert.public_key().verify(
        base64.b64decode(signature_b64),
        sii_envio._c14n(signed_info),
        padding.PKCS1v15(),
        hashes.SHA1(),
    )
    target.remove(sig)
    try:
        computed = base64.b64encode(
            hashlib.sha1(sii_envio._c14n(target)).digest()
        ).decode("ascii")
        assert computed == digest_value
    finally:
        target.append(sig)


def test_send_envio_seals_signed_envelope_and_records_track():
    storage = _Storage()
    org_id, invoice_id, project_id = uuid4(), uuid4(), uuid4()
    caf = _caf(org_id)
    dte = _dte_row(org_id, invoice_id, caf["id"], folio=7)
    pfx, _key, cert = _pfx()
    storage.objects[dte["storage_object_key"]] = _dte_xml(folio=7)
    with pytest.MonkeyPatch.context() as mp:
        mp.delenv("SII_WS_ENVIO_URL", raising=False)
        _patch_envio(mp, storage, dte=[dte], certs=[], caf=caf)
        cert_row = _cert_row(org_id, pfx)
        _patch_envio(mp, storage, dte=[dte], certs=[cert_row], caf=caf)
        result = sii_envio.send_invoice_envio(
            org_id=org_id, project_id=project_id, invoice_id=invoice_id, actor_id=uuid4()
        )
    assert result["status"] == "ACCEPTED"
    assert result["track_id"].startswith("MOCK-")
    envelope_key, envelope, media = storage.uploads[0]
    assert envelope_key.endswith(".xml") and media == "application/xml"
    root = etree.fromstring(envelope)
    assert root.tag == "{http://www.sii.cl/SiiDte}EnvioDTE"
    caratula = root.find("{http://www.sii.cl/SiiDte}SetDTE/{http://www.sii.cl/SiiDte}Caratula")
    assert caratula.findtext("{http://www.sii.cl/SiiDte}RutReceptor") == "60803000-K"
    assert caratula.findtext("{http://www.sii.cl/SiiDte}RutEnvia") == "13037614-2"
    documento = sii_envio._find_id(root, "F33T7")
    _verify_signature(documento, cert)
    set_dte = sii_envio._find_id(root, "SetDoc")
    _verify_signature(set_dte, cert)


def test_send_envio_escapes_non_latin1_characters_in_envelope():
    storage = _Storage()
    org_id, invoice_id, project_id = uuid4(), uuid4(), uuid4()
    caf = _caf(org_id)
    dte = _dte_row(org_id, invoice_id, caf["id"], folio=8)
    pfx, _key, _cert = _pfx()
    dte_bytes = _dte_xml(folio=8).replace(
        b"VENTANA", "VENTANA &#8212; \xda\xd1O".encode("latin-1"))
    storage.objects[dte["storage_object_key"]] = dte_bytes
    with pytest.MonkeyPatch.context() as mp:
        mp.delenv("SII_WS_ENVIO_URL", raising=False)
        _patch_envio(mp, storage, dte=[dte], certs=[], caf=caf)
        cert_row = _cert_row(org_id, pfx)
        _patch_envio(mp, storage, dte=[dte], certs=[cert_row], caf=caf)
        sii_envio.send_invoice_envio(
            org_id=org_id, project_id=project_id, invoice_id=invoice_id, actor_id=uuid4()
        )
    _key, envelope, _media = storage.uploads[0]
    assert b"&#8212;" in envelope
    assert b"\xe2\x80\x94" not in envelope
    assert b"\xda\xd1" in envelope
    root = etree.fromstring(envelope)
    item = root.findtext(".//{http://www.sii.cl/SiiDte}NmbItem")
    assert item == "VENTANA — ÚÑO"


def test_send_envio_requires_dte():
    with pytest.MonkeyPatch.context() as mp:
        _patch_envio(mp, _Storage(), dte=[])
        with pytest.raises(ContractAPIException) as error:
            sii_envio.send_invoice_envio(
                org_id=uuid4(), project_id=uuid4(), invoice_id=uuid4(), actor_id=uuid4()
            )
    assert error.value.contract_code == "sii_dte_missing"


def test_send_envio_requires_certificate():
    storage = _Storage()
    org_id, invoice_id = uuid4(), uuid4()
    caf = _caf(org_id)
    dte = _dte_row(org_id, invoice_id, caf["id"])
    with pytest.MonkeyPatch.context() as mp:
        _patch_envio(mp, storage, dte=[dte], certs=[], caf=caf)
        with pytest.raises(ContractAPIException) as error:
            sii_envio.send_invoice_envio(
                org_id=org_id, project_id=uuid4(), invoice_id=invoice_id, actor_id=uuid4()
            )
    assert error.value.contract_code == "sii_certificate_missing"


def test_send_envio_rejects_expired_certificate():
    storage = _Storage()
    org_id, invoice_id = uuid4(), uuid4()
    caf = _caf(org_id)
    dte = _dte_row(org_id, invoice_id, caf["id"])
    pfx, _key, _cert = _pfx()
    with pytest.MonkeyPatch.context() as mp:
        _patch_envio(mp, storage, dte=[dte], certs=[], caf=caf)
        cert_row = _cert_row(
            org_id,
            pfx,
            over={"valid_to": datetime.now(utc_timezone.utc) - timedelta(days=1)},
        )
        _patch_envio(mp, storage, dte=[dte], certs=[cert_row], caf=caf)
        with pytest.raises(ContractAPIException) as error:
            sii_envio.send_invoice_envio(
                org_id=org_id, project_id=uuid4(), invoice_id=invoice_id, actor_id=uuid4()
            )
    assert error.value.contract_code == "sii_cert_expired"


def test_send_envio_replays_existing_row():
    storage = _Storage()
    org_id, invoice_id = uuid4(), uuid4()
    caf = _caf(org_id)
    dte = _dte_row(org_id, invoice_id, caf["id"])
    envio = {
        "id": uuid4(),
        "dte_id": dte["id"],
        "status": "ACCEPTED",
        "track_id": "MOCK-1",
        "glosa": None,
        "sent_at": "2026-10-03T10:00:00+00:00",
    }
    with pytest.MonkeyPatch.context() as mp:
        _patch_envio(mp, storage, dte=[dte], existing_envio=[envio], caf=caf)
        result = sii_envio.send_invoice_envio(
            org_id=org_id, project_id=uuid4(), invoice_id=invoice_id, actor_id=uuid4()
        )
    assert result["id"] == str(envio["id"])
    assert storage.uploads == []


def test_envio_access_returns_signed_url():
    storage = _Storage()
    org_id, invoice_id = uuid4(), uuid4()
    dte = _dte_row(org_id, invoice_id, uuid4())
    envio = {
        "id": uuid4(),
        "dte_id": dte["id"],
        "status": "ACCEPTED",
        "track_id": "MOCK-1",
        "glosa": "ok",
        "sent_at": "2026-10-03T10:00:00+00:00",
        "storage_object_key": "org_x/envios/e.xml",
    }

    def fake_rows(sql, params=None):
        if "FROM public.sii_envios" in str(sql):
            return [envio]
        return []

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(sii_envio, "rows", fake_rows)
        mp.setattr(sii_envio, "SupabaseDocumentStorage", lambda: storage)
        mp.setattr(sii_envio, "documentary_backend", _noop)
        result = sii_envio.invoice_envio_access(org_id=org_id, invoice_id=invoice_id)
    assert result["signed_url"].startswith("https://storage.test/")
    assert result["track_id"] == "MOCK-1"


def test_envio_access_missing_returns_404():
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(sii_envio, "rows", lambda *a, **k: [])
        mp.setattr(sii_envio, "documentary_backend", _noop)
        with pytest.raises(ContractAPIException) as error:
            sii_envio.invoice_envio_access(org_id=uuid4(), invoice_id=uuid4())
    assert error.value.contract_code == "sii_envio_missing"
