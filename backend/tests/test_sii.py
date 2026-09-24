"""SII DTE — CAF parsing/registration, timbraje, folio allocation, replay."""

import base64
import re
from contextlib import contextmanager
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from authentication.errors import ContractAPIException
from projects import credit_notes as credit_notes_module
from projects import sii


class _Storage:
    def __init__(self):
        self.uploads = []
        self.deleted = []

    def upload_immutable(self, object_key, content, content_type):
        self.uploads.append((object_key, content, content_type))

    def delete_object(self, object_key):
        self.deleted.append(object_key)

    def signed_url(self, object_key, expires_in=None):
        return f"https://storage.test/{object_key}?exp={expires_in}"


@contextmanager
def _noop(*args, **kwargs):
    yield


def _caf_xml(desde=1, hasta=10, rut="76123456-0", tipo=33):
    key = rsa.generate_private_key(3, 1024)
    numbers = key.private_numbers()
    modulus = numbers.public_numbers.n.to_bytes(
        (numbers.public_numbers.n.bit_length() + 7) // 8, "big"
    )
    exponent = numbers.public_numbers.e.to_bytes(
        (numbers.public_numbers.e.bit_length() + 7) // 8, "big"
    )
    rsask = base64.b64encode(
        key.private_bytes(
            serialization.Encoding.DER,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    ).decode()
    caf = (
        '<CAF version="1.0"><DA>'
        f"<RE>{rut}</RE><RS>Ventanas Prueba SpA</RS><TD>{tipo}</TD>"
        f"<RNG><D>{desde}</D><H>{hasta}</H></RNG>"
        "<FA>2026-10-01</FA>"
        f"<RSAPK><M>{base64.b64encode(modulus).decode()}</M>"
        f"<E>{base64.b64encode(exponent).decode()}</E></RSAPK>"
        "<IDK>300</IDK></DA>"
        '<FRMA algoritmo="SHA1withRSA"></FRMA>'
        f"</CAF><RSASK>{rsask}</RSASK>"
        "<RSAPUBK></RSAPUBK>"
    )
    return f'<AUTORIZACION version="1.0">{caf}</AUTORIZACION>', key


def _invoice_row(over=None):
    row = {
        "id": uuid4(),
        "org_id": uuid4(),
        "project_id": uuid4(),
        "invoice_code": "FAC-0001",
        "payload_json": {
            "invoice_code": "FAC-0001",
            "issued_at": "2026-10-01T10:00:00+00:00",
            "revision_code": "REV-A",
            "project": {
                "code": "PRY-001",
                "name": "Edificio Norte",
                "client_name": "Constructora Andina",
                "client_rut": "76.543.210-3",
                "client_giro": "Construcción",
                "client_comuna": "Providencia",
                "client_address": "Av. Los Leones 456",
                "delivery_address": "Av. Providencia 1234",
                "currency": "CLP",
            },
            "deal": {
                "total_net": "1000000",
                "total_tax": "190000",
                "total_gross": "1190000",
            },
            "positions": [
                {"position_index": 1, "typology": "SLIDING_2L", "quantity": 2}
            ],
        },
        "created_at": "2026-10-01T10:00:00+00:00",
    }
    row.update(over or {})
    return row


def _caf_row(parsed, org_id, actual=None, over=None):
    row = {
        "id": uuid4(),
        "org_id": org_id,
        "tipo_dte": parsed["tipo_dte"],
        "folio_desde": parsed["folio_desde"],
        "folio_hasta": parsed["folio_hasta"],
        "folio_actual": actual if actual is not None else parsed["folio_desde"] - 1,
        "rut_emisor": parsed["rut_emisor"],
        "razon_social": parsed["razon_social"],
        "giro_emis": "Ventas de ventanas",
        "dir_origen": "Los Aromos 100",
        "cmna_origen": "Santiago",
        "acteco": 466001,
        "caf_xml": parsed["caf_xml"],
        "rsask": parsed["rsask"],
        "rsapk_m": parsed["rsapk_m"],
        "rsapk_e": parsed["rsapk_e"],
        "file_sha256": "a" * 64,
        "uploaded_by": uuid4(),
        "created_at": "2026-10-01T10:00:00+00:00",
    }
    row.update(over or {})
    return row


def _dte_row(invoice_id, folio=1, over=None):
    row = {
        "id": uuid4(),
        "org_id": uuid4(),
        "project_id": uuid4(),
        "invoice_id": invoice_id,
        "dte_type": 33,
        "folio": folio,
        "storage_object_key": f"org_x/dtes/dte33-{folio}.xml",
        "issued_at": "2026-10-02T10:00:00+00:00",
    }
    row.update(over or {})
    return row


def _credit_note_row(invoice, over=None):
    row = {
        "id": uuid4(),
        "org_id": invoice["org_id"],
        "project_id": invoice["project_id"],
        "invoice_id": invoice["id"],
        "credit_code": "NC-0001",
        "payload_json": {
            "credit_code": "NC-0001",
            "reason": "Anula por error en folio",
            "invoice": {
                "id": str(invoice["id"]),
                "invoice_code": invoice["invoice_code"],
            },
            "revision_code": "REV-A",
            "project": invoice["payload_json"]["project"],
            "deal": invoice["payload_json"]["deal"],
            "positions": invoice["payload_json"]["positions"],
        },
        "created_at": "2026-10-03T10:00:00+00:00",
    }
    row.update(over or {})
    return row


def _dispatch_note_row(order, over=None):
    row = {
        "id": uuid4(),
        "org_id": order["org_id"],
        "project_id": order["project_id"],
        "work_order_id": order["id"],
        "note_code": "GD-0001",
        "payload_json": {
            "note_code": "GD-0001",
            "issued_at": "2026-10-04T10:00:00+00:00",
            "order": {"code": order["order_code"], "id": str(order["id"]), "quantity": 2},
            "project": {
                "code": "PRJ-0001",
                "name": "Proyecto",
                "client_name": "Cliente Uno",
                "client_rut": "76123456-0",
                "delivery_address": "Av. Los Robles 123, Concepción",
            },
            "units": [],
            "totals": {"units": 2},
            "dispatch": {"dispatched_by": str(uuid4()), "note": None},
        },
        "created_at": "2026-10-04T10:00:00+00:00",
    }
    row.update(over or {})
    return row


def _order_row(over=None):
    row = {
        "id": uuid4(),
        "org_id": uuid4(),
        "project_id": uuid4(),
        "order_code": "OT-0042",
    }
    row.update(over or {})
    return row


def _patch_env(
    monkeypatch,
    storage,
    *,
    org=None,
    cafs=None,
    invoice=None,
    existing=None,
    insert_row=None,
    credit_note=None,
    parents=None,
    existing_nc=None,
    annulled=None,
    order=None,
    note=None,
    existing_dte52=None,
):
    def fake_one(sql, params=None, *args, **kw):
        text = str(sql)
        if "INSERT INTO public.project_dtes" in text:
            return insert_row or _dte_row(
                invoice["id"] if invoice else None, folio=1
            )
        if "INSERT INTO public.sii_cafs" in text:
            return _caf_row(_parse(), org_id=uuid4())
        if "INSERT INTO public.project_credit_notes" in text:
            return credit_note or _credit_note_row(invoice)
        if "COUNT(*) AS n" in text and "FROM public.project_credit_notes" in text:
            return {"n": len(annulled or [])}
        if "FROM public.orders" in text:
            if order is None:
                raise ContractAPIException(404, "work_order_not_found", "x")
            return order
        if "FROM public.tenancy_organizations" in text:
            if org is None:
                raise ContractAPIException(404, "org_not_found", "x")
            return org
        if "FROM public.project_credit_notes" in text:
            if credit_note is None:
                raise ContractAPIException(404, "credit_note_not_found", "x")
            return credit_note
        if "FROM public.project_invoices" in text:
            if invoice is None:
                raise ContractAPIException(404, "invoice_not_found", "x")
            return invoice
        if "pg_advisory_xact_lock" in text:
            return {"pg_advisory_xact_lock": None}
        return {}

    def fake_rows(sql, params=None):
        if "FROM public.sii_cafs" in sql and "folio_actual < folio_hasta" in sql:
            return [
                row
                for row in (cafs or [])
                if int(row["folio_actual"]) < int(row["folio_hasta"])
            ]
        if "FROM public.sii_cafs" in sql:
            return list(cafs or [])
        if "FROM public.project_dtes" in sql and "JOIN public.dispatch_notes" in sql:
            return list(existing_dte52 or [])
        if "FROM public.project_dtes" in sql and "dispatch_note_id=%s" in sql:
            return list(existing_dte52 or [])
        if "FROM public.project_dtes" in sql and "credit_note_id IS NULL" in sql:
            return list(parents) if parents is not None else list(existing or [])
        if "FROM public.project_dtes" in sql and "credit_note_id=%s" in sql:
            return list(existing_nc or [])
        if "FROM public.project_dtes" in sql:
            return list(existing or [])
        if "FROM public.project_credit_notes" in sql:
            return list(annulled or [])
        if "FROM public.dispatch_notes" in sql:
            return [note] if note is not None else []
        if "UPDATE public.sii_cafs" in sql:
            return [{"folio_actual": 1}]
        return []

    monkeypatch.setattr(sii, "one", fake_one)
    monkeypatch.setattr(sii, "rows", fake_rows)
    monkeypatch.setattr(sii, "_kek", lambda: b"\x01" * 32)
    monkeypatch.setattr(sii, "SupabaseDocumentStorage", lambda: storage)
    monkeypatch.setattr(sii.transaction, "atomic", _noop)
    monkeypatch.setattr(sii, "documentary_backend", _noop)
    # emit_credit_note_dte seals the NC document through
    # projects.credit_notes — stub its own module-level deps too.
    monkeypatch.setattr(credit_notes_module, "one", fake_one)
    monkeypatch.setattr(credit_notes_module, "SupabaseDocumentStorage", lambda: storage)
    monkeypatch.setattr(
        credit_notes_module,
        "render_credit_note",
        lambda payload, pdf_identifier=None: (b"%PDF-fake-cn", "application/pdf"),
    )
    monkeypatch.setattr(
        credit_notes_module, "_purge_unreferenced_credit_note", lambda **kw: None
    )


def _parse(desde=1, hasta=10):
    xml, _ = _caf_xml(desde=desde, hasta=hasta)
    return sii._parse_caf(xml)


def test_parse_caf_extracts_range_and_keys():
    parsed = _parse(desde=50, hasta=99)
    assert parsed["tipo_dte"] == 33
    assert parsed["folio_desde"] == 50
    assert parsed["folio_hasta"] == 99
    assert parsed["rut_emisor"] == "76123456-0"
    assert parsed["razon_social"] == "Ventanas Prueba SpA"
    assert "<CAF" in parsed["caf_xml"] and "<DA>" in parsed["caf_xml"]


def test_parse_caf_rejects_non_xml_and_missing_rsask():
    with pytest.raises(ContractAPIException) as excinfo:
        sii._parse_caf("not xml at all")
    assert excinfo.value.contract_code == "sii_caf_invalid"
    xml, _ = _caf_xml()
    broken = xml.split("<RSASK>")[0] + "</AUTORIZACION>"
    with pytest.raises(ContractAPIException) as excinfo:
        sii._parse_caf(broken)
    assert excinfo.value.contract_code == "sii_caf_invalid"


def test_parse_caf_rejects_inverted_range():
    xml, _ = _caf_xml(desde=10, hasta=5)
    with pytest.raises(ContractAPIException) as excinfo:
        sii._parse_caf(xml)
    assert excinfo.value.contract_code == "sii_caf_invalid"


def test_register_caf_rejects_overlapping_range(monkeypatch):
    storage = _Storage()
    org = {"id": uuid4(), "tax_id": "76123456-0", "name": "Org"}
    existing = _caf_row(_parse(), org_id=org["id"])
    _patch_env(monkeypatch, storage, org=org, cafs=[existing])
    xml, _ = _caf_xml(desde=5, hasta=20)
    with pytest.raises(ContractAPIException) as excinfo:
        sii.register_caf(
            org_id=org["id"], actor_id=uuid4(), caf_xml=xml
        )
    assert excinfo.value.contract_code == "sii_caf_overlap"


def test_register_caf_rejects_rut_mismatch(monkeypatch):
    storage = _Storage()
    org = {"id": uuid4(), "tax_id": "11111111-1", "name": "Org"}
    _patch_env(monkeypatch, storage, org=org)
    xml, _ = _caf_xml()
    with pytest.raises(ContractAPIException) as excinfo:
        sii.register_caf(org_id=org["id"], actor_id=uuid4(), caf_xml=xml)
    assert excinfo.value.contract_code == "sii_caf_org_mismatch"


def test_emit_dte_allocates_folio_and_stamps_ted(monkeypatch):
    storage = _Storage()
    invoice = _invoice_row()
    caf = _caf_row(_parse(), org_id=invoice["org_id"], actual=0)
    dte_row = _dte_row(invoice["id"], folio=1)
    _patch_env(
        monkeypatch,
        storage,
        cafs=[caf],
        invoice=invoice,
        insert_row=dte_row,
    )
    out = sii.emit_dte(
        org_id=invoice["org_id"],
        project={"id": invoice["project_id"]},
        invoice_id=invoice["id"],
        actor_id=uuid4(),
    )
    assert out["folio"] == 1
    assert out["dte_type"] == 33
    assert len(storage.uploads) == 1
    object_key, content, media = storage.uploads[0]
    assert object_key.endswith(".xml") and "dte33-1_" in object_key
    assert media == "application/xml"
    text = content.decode("iso-8859-1")
    assert '<?xml version="1.0" encoding="ISO-8859-1"?>' in text
    assert '<DTE version="1.0" xmlns="http://www.sii.cl/SiiDte">' in text
    assert "<TipoDTE>33</TipoDTE>" in text
    assert "<Folio>1</Folio>" in text
    assert "<RUTEmisor>76123456-0</RUTEmisor>" in text
    assert "<RUTRecep>76543210-3</RUTRecep>" in text
    # SII-schema required sections, always present.
    assert "<GiroEmis>Ventas de ventanas</GiroEmis>" in text
    assert "<Acteco>466001</Acteco>" in text
    assert "<DirOrigen>Los Aromos 100</DirOrigen>" in text
    assert "<CmnaOrigen>Santiago</CmnaOrigen>" in text
    assert "<GiroRecep>Construcción</GiroRecep>" in text
    assert "<DirRecep>Av. Los Leones 456</DirRecep>" in text
    assert "<CmnaRecep>Providencia</CmnaRecep>" in text
    # TSTED is Chilean wall time at second precision — no offset, no µs.
    tsted = re.search(r"<TSTED>([^<]+)</TSTED>", text).group(1)
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", tsted)
    tmst = re.search(r"<TmstFirma>([^<]+)</TmstFirma>", text).group(1)
    assert tmst == tsted
    assert "<MntNeto>1000000</MntNeto>" in text
    assert "<MntTotal>1190000</MntTotal>" in text
    assert 'FRMT algoritmo="SHA1withRSA"' in text
    # Round-trip: the FRMT verifies against the CAF public key (M/E).
    import defusedxml.ElementTree as ET

    root = ET.fromstring(text)
    dd = text[text.index("<DD>") : text.index("</DD>") + len("</DD>")]
    frmt = base64.b64decode(
        root.findtext(
            ".//{http://www.sii.cl/SiiDte}TED/{http://www.sii.cl/SiiDte}FRMT"
        )
    )
    m = base64.b64decode(caf["rsapk_m"])
    e = base64.b64decode(caf["rsapk_e"])
    public = rsa.RSAPublicNumbers(
        int.from_bytes(e, "big"), int.from_bytes(m, "big")
    ).public_key()
    public.verify(
        frmt, dd.encode("iso-8859-1"), padding.PKCS1v15(), hashes.SHA1()
    )


def test_emit_dte_replay_returns_existing(monkeypatch):
    storage = _Storage()
    invoice = _invoice_row()
    existing = _dte_row(invoice["id"], folio=7)
    _patch_env(monkeypatch, storage, invoice=invoice, existing=[existing])
    out = sii.emit_dte(
        org_id=invoice["org_id"],
        project={"id": invoice["project_id"]},
        invoice_id=invoice["id"],
        actor_id=uuid4(),
    )
    assert out["folio"] == 7
    assert out["id"] == str(existing["id"])
    assert storage.uploads == []


def test_emit_dte_requires_available_folio(monkeypatch):
    storage = _Storage()
    invoice = _invoice_row()
    exhausted = _caf_row(_parse(desde=1, hasta=5), org_id=invoice["org_id"], actual=5)
    _patch_env(monkeypatch, storage, cafs=[exhausted], invoice=invoice)
    with pytest.raises(ContractAPIException) as excinfo:
        sii.emit_dte(
            org_id=invoice["org_id"],
            project={"id": invoice["project_id"]},
            invoice_id=invoice["id"],
            actor_id=uuid4(),
        )
    assert excinfo.value.contract_code == "sii_caf_exhausted"
    assert storage.uploads == []


def test_emit_dte_requires_receptor_rut(monkeypatch):
    storage = _Storage()
    invoice = _invoice_row(
        over={
            "payload_json": {
                **_invoice_row()["payload_json"],
                "project": {
                    **_invoice_row()["payload_json"]["project"],
                    "client_rut": "sin rut",
                },
            }
        }
    )
    caf = _caf_row(_parse(), org_id=invoice["org_id"], actual=0)
    _patch_env(monkeypatch, storage, cafs=[caf], invoice=invoice)
    with pytest.raises(ContractAPIException) as excinfo:
        sii.emit_dte(
            org_id=invoice["org_id"],
            project={"id": invoice["project_id"]},
            invoice_id=invoice["id"],
            actor_id=uuid4(),
        )
    assert excinfo.value.contract_code == "sii_receptor_missing"


def test_dte_access_signs_the_stored_object(monkeypatch):
    storage = _Storage()
    invoice = _invoice_row()
    dte = _dte_row(invoice["id"], folio=3)
    _patch_env(monkeypatch, storage, existing=[dte])
    out = sii.dte_access(
        org_id=uuid4(), project_id=dte["project_id"], invoice_id=dte["invoice_id"]
    )
    assert out["signed_url"].startswith("https://storage.test/")
    assert out["expires_in"] == 600
    assert out["folio"] == 3


def test_dte_access_missing_raises_404(monkeypatch):
    _patch_env(monkeypatch, _Storage())
    with pytest.raises(ContractAPIException) as excinfo:
        sii.dte_access(org_id=uuid4(), project_id=uuid4(), invoice_id=uuid4())
    assert excinfo.value.contract_code == "dte_not_found"


def test_emit_credit_note_dte_references_parent_folio(monkeypatch):
    storage = _Storage()
    invoice = _invoice_row()
    credit_note = _credit_note_row(invoice)
    caf61 = _caf_row(
        sii._parse_caf(_caf_xml(tipo=61, desde=1, hasta=10)[0]),
        org_id=invoice["org_id"],
        actual=0,
    )
    parent = _dte_row(invoice["id"], folio=4)
    insert_row = _dte_row(
        invoice["id"], folio=1, over={"dte_type": 61, "credit_note_id": credit_note["id"]}
    )
    _patch_env(
        monkeypatch,
        storage,
        cafs=[caf61],
        invoice=invoice,
        credit_note=credit_note,
        annulled=[credit_note],
        parents=[parent],
        insert_row=insert_row,
    )
    out = sii.emit_credit_note_dte(
        org_id=invoice["org_id"],
        project={"id": invoice["project_id"]},
        invoice_id=invoice["id"],
        actor_id=uuid4(),
    )
    assert out["dte_type"] == 61 and out["folio"] == 1
    object_key, content, media = storage.uploads[0]
    assert "dte61-1_" in object_key and media == "application/xml"
    text = content.decode("iso-8859-1")
    assert "<TipoDTE>61</TipoDTE>" in text
    assert (
        "<NroLinRef>1</NroLinRef><TpoDocRef>33</TpoDocRef>"
        "<FolioRef>4</FolioRef><FchRef>2026-10-02</FchRef>"
        "<CodRef>1</CodRef>" in text
    )
    assert "Anula factura FAC-0001" in text
    import defusedxml.ElementTree as ET

    root = ET.fromstring(text)
    dd = text[text.index("<DD>") : text.index("</DD>") + len("</DD>")]
    frmt = base64.b64decode(
        root.findtext(
            ".//{http://www.sii.cl/SiiDte}TED/{http://www.sii.cl/SiiDte}FRMT"
        )
    )
    public = rsa.RSAPublicNumbers(
        int.from_bytes(base64.b64decode(caf61["rsapk_e"]), "big"),
        int.from_bytes(base64.b64decode(caf61["rsapk_m"]), "big"),
    ).public_key()
    public.verify(
        frmt, dd.encode("iso-8859-1"), padding.PKCS1v15(), hashes.SHA1()
    )


def test_emit_credit_note_dte_seals_credit_note_document(monkeypatch):
    storage = _Storage()
    invoice = _invoice_row()
    caf61 = _caf_row(
        sii._parse_caf(_caf_xml(tipo=61, desde=1, hasta=10)[0]),
        org_id=invoice["org_id"],
        actual=0,
    )
    insert_row = _dte_row(
        invoice["id"],
        folio=1,
        over={"dte_type": 61, "credit_note_id": str(uuid4())},
    )
    _patch_env(
        monkeypatch,
        storage,
        invoice=invoice,
        cafs=[caf61],
        parents=[_dte_row(invoice["id"], folio=4)],
        insert_row=insert_row,
    )
    out = sii.emit_credit_note_dte(
        org_id=invoice["org_id"],
        project={"id": invoice["project_id"]},
        invoice_id=invoice["id"],
        actor_id=uuid4(),
        reason="Anula por error en folio",
    )
    assert out["dte_type"] == 61 and out["folio"] == 1
    assert len(storage.uploads) == 2
    pdf_key, pdf_content, pdf_media = storage.uploads[0]
    assert "credit-notes/nc-0001_" in pdf_key
    assert pdf_media == "application/pdf"
    xml_key, _, _ = storage.uploads[1]
    assert "dte61-1_" in xml_key


def test_emit_credit_note_dte_bounds_sii_field_lengths(monkeypatch):
    storage = _Storage()
    invoice = _invoice_row()
    credit_note = _credit_note_row(invoice)
    credit_note["payload_json"]["reason"] = "x" * 300
    caf61 = _caf_row(
        sii._parse_caf(_caf_xml(tipo=61, desde=1, hasta=10)[0]),
        org_id=invoice["org_id"],
        actual=0,
    )
    _patch_env(
        monkeypatch,
        storage,
        invoice=invoice,
        credit_note=credit_note,
        annulled=[credit_note],
        parents=[_dte_row(invoice["id"], folio=4)],
        cafs=[caf61],
    )
    sii.emit_credit_note_dte(
        org_id=invoice["org_id"],
        project={"id": invoice["project_id"]},
        invoice_id=invoice["id"],
        actor_id=uuid4(),
    )
    text = storage.uploads[0][1].decode("iso-8859-1")
    razon = text[text.index("<RazonRef>") + len("<RazonRef>") : text.index("</RazonRef>")]
    assert razon == "x" * 90
    nmb = text[text.index("<NmbItem>") + len("<NmbItem>") : text.index("</NmbItem>")]
    assert nmb == "Anula factura FAC-0001"


def test_emit_credit_note_dte_requires_timbred_parent(monkeypatch):
    storage = _Storage()
    invoice = _invoice_row()
    _patch_env(monkeypatch, storage, invoice=invoice, parents=[])
    with pytest.raises(ContractAPIException) as excinfo:
        sii.emit_credit_note_dte(
            org_id=invoice["org_id"],
            project={"id": invoice["project_id"]},
            invoice_id=invoice["id"],
            actor_id=uuid4(),
        )
    assert excinfo.value.contract_code == "sii_reference_missing"
    assert storage.uploads == []


def test_emit_credit_note_dte_replay_and_exhaustion(monkeypatch):
    storage = _Storage()
    invoice = _invoice_row()
    credit_note = _credit_note_row(invoice)
    existing = _dte_row(
        invoice["id"], folio=9, over={"dte_type": 61, "credit_note_id": credit_note["id"]}
    )
    _patch_env(
        monkeypatch,
        storage,
        invoice=invoice,
        credit_note=credit_note,
        annulled=[credit_note],
        existing_nc=[existing],
        parents=[_dte_row(invoice["id"], folio=4)],
    )
    out = sii.emit_credit_note_dte(
        org_id=invoice["org_id"],
        project={"id": invoice["project_id"]},
        invoice_id=invoice["id"],
        actor_id=uuid4(),
    )
    assert out["folio"] == 9 and storage.uploads == []

    exhausted = _caf_row(
        sii._parse_caf(_caf_xml(tipo=61, desde=1, hasta=3)[0]),
        org_id=invoice["org_id"],
        actual=3,
    )
    _patch_env(
        monkeypatch,
        _Storage(),
        invoice=invoice,
        credit_note=credit_note,
        annulled=[credit_note],
        parents=[_dte_row(invoice["id"], folio=4)],
        cafs=[exhausted],
    )
    with pytest.raises(ContractAPIException) as excinfo:
        sii.emit_credit_note_dte(
            org_id=invoice["org_id"],
            project={"id": invoice["project_id"]},
            invoice_id=invoice["id"],
            actor_id=uuid4(),
        )
    assert excinfo.value.contract_code == "sii_caf_exhausted"


def test_emit_dte_refuses_annulled_invoice(monkeypatch):
    storage = _Storage()
    invoice = _invoice_row()
    caf = _caf_row(_parse(), org_id=invoice["org_id"], actual=0)
    _patch_env(
        monkeypatch,
        storage,
        cafs=[caf],
        invoice=invoice,
        annulled=[{"id": uuid4()}],
    )
    with pytest.raises(ContractAPIException) as excinfo:
        sii.emit_dte(
            org_id=invoice["org_id"],
            project={"id": invoice["project_id"]},
            invoice_id=invoice["id"],
            actor_id=uuid4(),
        )
    assert excinfo.value.contract_code == "invoice_already_annulled"
    assert storage.uploads == []


def test_register_caf_rejects_mismatched_key_pair(monkeypatch):
    storage = _Storage()
    org = {"id": uuid4(), "tax_id": "76123456-0", "name": "Org"}
    _patch_env(monkeypatch, storage, org=org)
    xml, _ = _caf_xml()
    # A CAF whose RSASK belongs to a different key than its declared RSAPK.
    foreign_rsask = sii._parse_caf(_caf_xml()[0])["rsask"]
    mismatched = xml.replace(
        f"<RSASK>{sii._parse_caf(xml)['rsask']}</RSASK>",
        f"<RSASK>{foreign_rsask}</RSASK>",
    )
    assert mismatched != xml
    with pytest.raises(ContractAPIException) as excinfo:
        sii.register_caf(org_id=org["id"], actor_id=uuid4(), caf_xml=mismatched)
    assert excinfo.value.contract_code == "sii_caf_key_mismatch"


def test_register_caf_fails_closed_without_kek(monkeypatch):
    storage = _Storage()
    org = {"id": uuid4(), "tax_id": "76123456-0", "name": "Org"}
    _patch_env(monkeypatch, storage, org=org)
    monkeypatch.setattr(sii, "_kek", lambda: None)
    xml, _ = _caf_xml()
    with pytest.raises(ContractAPIException) as excinfo:
        sii.register_caf(org_id=org["id"], actor_id=uuid4(), caf_xml=xml)
    assert excinfo.value.contract_code == "sii_kek_unconfigured"


def test_rsask_roundtrip_wrap_unwrap(monkeypatch):
    monkeypatch.setattr(sii, "_kek", lambda: b"\x02" * 32)
    aad = sii._caf_aad(str(uuid4()), 33, 1, 10)
    wrapped = sii._wrap_rsask("aGFzc2R1aWFzZA==", aad)
    assert wrapped.startswith("enc:v2:")
    assert sii._unwrap_rsask(wrapped, aad) == "aGFzc2R1aWFzZA=="
    # Ciphertext moved onto a different pool row fails decryption.
    other = sii._caf_aad(str(uuid4()), 33, 50, 60)
    with pytest.raises(ContractAPIException) as excinfo:
        sii._unwrap_rsask(wrapped, other)
    assert excinfo.value.contract_code == "sii_caf_key_invalid"
    # Legacy plaintext rows stay readable without a KEK.
    assert sii._unwrap_rsask("b3RoZXJwbGFpbg==") == "b3RoZXJwbGFpbg=="


def test_parse_caf_rejects_zero_based_range():
    xml, _ = _caf_xml(desde=0, hasta=50)
    with pytest.raises(ContractAPIException) as excinfo:
        sii._parse_caf(xml)
    assert excinfo.value.contract_code == "sii_caf_invalid"


def test_emit_dte_rejects_non_latin1_characters(monkeypatch):
    storage = _Storage()
    invoice = _invoice_row()
    invoice["payload_json"]["project"]["client_name"] = "Ventanas \U0001fa9f SpA"
    caf = _caf_row(_parse(), org_id=invoice["org_id"], actual=0)
    _patch_env(monkeypatch, storage, cafs=[caf], invoice=invoice)
    with pytest.raises(ContractAPIException) as excinfo:
        sii.emit_dte(
            org_id=invoice["org_id"],
            project={"id": invoice["project_id"]},
            invoice_id=invoice["id"],
            actor_id=uuid4(),
        )
    assert excinfo.value.contract_code == "sii_dte_unrepresentable"
    # The folio is only committed after the XML is stamped, so a rejected
    # render never consumes one.
    assert storage.uploads == []


def test_emit_dte_refuses_non_clp_invoice(monkeypatch):
    storage = _Storage()
    invoice = _invoice_row()
    invoice["payload_json"]["deal"]["currency"] = "USD"
    caf = _caf_row(_parse(), org_id=invoice["org_id"], actual=0)
    _patch_env(monkeypatch, storage, cafs=[caf], invoice=invoice)
    with pytest.raises(ContractAPIException) as excinfo:
        sii.emit_dte(
            org_id=invoice["org_id"],
            project={"id": invoice["project_id"]},
            invoice_id=invoice["id"],
            actor_id=uuid4(),
        )
    assert excinfo.value.contract_code == "sii_currency_unsupported"
    # The folio cursor must be untouched — the DD is validated before UPDATE.
    assert storage.uploads == []


def test_emit_dte_refuses_fractional_clp_totals(monkeypatch):
    storage = _Storage()
    invoice = _invoice_row()
    invoice["payload_json"]["deal"]["total_net"] = "1000.50"
    caf = _caf_row(_parse(), org_id=invoice["org_id"], actual=0)
    _patch_env(monkeypatch, storage, cafs=[caf], invoice=invoice)
    with pytest.raises(ContractAPIException) as excinfo:
        sii.emit_dte(
            org_id=invoice["org_id"],
            project={"id": invoice["project_id"]},
            invoice_id=invoice["id"],
            actor_id=uuid4(),
        )
    assert excinfo.value.contract_code == "sii_amount_fractional"


def test_rut_normalize_rejects_bad_verifier(monkeypatch):
    assert sii._rut_normalize("76.543.210-1") is None
    assert sii._rut_normalize("76.543.210-3") == "76543210-3"
    assert sii._rut_normalize("76123456-0") == "76123456-0"
    assert sii._rut_normalize("60803000-k") == "60803000-K"
    assert sii._rut_normalize("60803000-9") is None
    assert sii._rut_normalize("sin rut") is None


def test_emit_dte_refuses_incomplete_emisor(monkeypatch):
    storage = _Storage()
    invoice = _invoice_row()
    caf = _caf_row(_parse(), org_id=invoice["org_id"], actual=0)
    caf["acteco"] = None
    _patch_env(monkeypatch, storage, cafs=[caf], invoice=invoice)
    with pytest.raises(ContractAPIException) as excinfo:
        sii.emit_dte(
            org_id=invoice["org_id"],
            project={"id": invoice["project_id"]},
            invoice_id=invoice["id"],
            actor_id=uuid4(),
        )
    assert excinfo.value.contract_code == "sii_emisor_incomplete"
    assert storage.uploads == []


def test_emit_dte_refuses_incomplete_receptor(monkeypatch):
    storage = _Storage()
    invoice = _invoice_row()
    invoice["payload_json"]["project"]["client_giro"] = ""
    caf = _caf_row(_parse(), org_id=invoice["org_id"], actual=0)
    _patch_env(monkeypatch, storage, cafs=[caf], invoice=invoice)
    with pytest.raises(ContractAPIException) as excinfo:
        sii.emit_dte(
            org_id=invoice["org_id"],
            project={"id": invoice["project_id"]},
            invoice_id=invoice["id"],
            actor_id=uuid4(),
        )
    assert excinfo.value.contract_code == "sii_receptor_incomplete"
    assert storage.uploads == []


def test_register_caf_rejects_malformed_rsask_base64(monkeypatch):
    storage = _Storage()
    org = {"id": uuid4(), "tax_id": "76123456-0", "name": "Org"}
    _patch_env(monkeypatch, storage, org=org)
    xml, _ = _caf_xml()
    broken = re.sub(r"<RSASK>.*?</RSASK>", "<RSASK>%%%</RSASK>", xml)
    with pytest.raises(ContractAPIException) as excinfo:
        sii.register_caf(org_id=org["id"], actor_id=uuid4(), caf_xml=broken)
    assert excinfo.value.contract_code == "sii_caf_key_invalid"


def test_dtes_by_invoice_returns_public_shape(monkeypatch):
    invoice_id = uuid4()
    row = _dte_row(invoice_id, folio=9)
    monkeypatch.setattr(sii, "rows", lambda sql, params=None: [row])
    out = sii.dtes_by_invoice(org_id=row["org_id"], project_id=row["project_id"])
    badge = out[str(invoice_id)]
    assert badge["invoice_id"] == str(invoice_id)
    assert badge["issued_at"] == row["issued_at"]
    assert badge["folio"] == 9


def test_register_caf_rejects_org_without_rut(monkeypatch):
    storage = _Storage()
    org = {"id": uuid4(), "tax_id": "BOW-TEST-1", "name": "Org"}
    _patch_env(monkeypatch, storage, org=org)
    xml, _ = _caf_xml()
    with pytest.raises(ContractAPIException) as excinfo:
        sii.register_caf(org_id=org["id"], actor_id=uuid4(), caf_xml=xml)
    assert excinfo.value.contract_code == "sii_org_rut_missing"


def test_emit_dte_upgrades_plaintext_rsask(monkeypatch):
    storage = _Storage()
    org = {"id": uuid4(), "tax_id": "76123456-0", "name": "Org"}
    invoice = _invoice_row()
    caf = _caf_row(_parse(), org_id=invoice["org_id"])
    _patch_env(monkeypatch, storage, org=org, cafs=[caf], invoice=invoice)
    updates = []
    original_rows = sii.rows
    monkeypatch.setattr(
        sii,
        "rows",
        lambda sql, params=None: updates.append(sql) or original_rows(sql, params),
    )
    sii.emit_dte(
        org_id=invoice["org_id"],
        project={"id": invoice["project_id"]},
        invoice_id=invoice["id"],
        actor_id=uuid4(),
    )
    assert any("SET rsask" in sql for sql in updates)


def test_emit_dte_rejects_nonstandard_tax_rate(monkeypatch):
    storage = _Storage()
    org = {"id": uuid4(), "tax_id": "76123456-0", "name": "Org"}
    invoice = _invoice_row(
        {
            "payload_json": {
                "deal": {
                    "currency": "CLP",
                    "total_net": "1000000",
                    "total_tax": "100000",
                    "total_gross": "1100000",
                },
                "project": _invoice_row()["payload_json"]["project"],
                "positions": [],
                "revision_code": "REV-A",
            }
        }
    )
    caf = _caf_row(_parse(), org_id=invoice["org_id"])
    _patch_env(monkeypatch, storage, org=org, cafs=[caf], invoice=invoice)
    with pytest.raises(ContractAPIException) as excinfo:
        sii.emit_dte(
            org_id=invoice["org_id"],
            project={"id": invoice["project_id"]},
            invoice_id=invoice["id"],
            actor_id=uuid4(),
        )
    assert excinfo.value.contract_code == "sii_tax_rate_unsupported"
    assert storage.uploads == []


def test_emit_dispatch_note_dte_stamps_and_replays(monkeypatch):
    storage = _Storage()
    order = _order_row()
    note = _dispatch_note_row(order)
    caf52 = _caf_row(
        sii._parse_caf(_caf_xml(tipo=52, desde=1, hasta=10)[0]),
        org_id=order["org_id"],
        actual=0,
    )
    insert_row = _dte_row(
        None,
        folio=1,
        over={"dte_type": 52, "dispatch_note_id": str(note["id"]), "invoice_id": None},
    )
    existing52 = []
    _patch_env(
        monkeypatch,
        storage,
        order=order,
        note=note,
        cafs=[caf52],
        insert_row=insert_row,
        existing_dte52=existing52,
    )
    out = sii.emit_dispatch_note_dte(
        org_id=order["org_id"], order_id=order["id"], actor_id=uuid4()
    )
    assert out["dte_type"] == 52 and out["folio"] == 1
    assert len(storage.uploads) == 1
    object_key, content, media = storage.uploads[0]
    assert "dte52-1_" in object_key and media == "application/xml"
    text = content.decode("iso-8859-1")
    assert "<TipoDTE>52</TipoDTE>" in text
    assert "<IndTraslado>1</IndTraslado>" in text
    # Amount-less guía: the schema still requires Totales/MontoItem —
    # they stamp as 0 while QtyItem carries the moved units.
    assert "<Totales><MntTotal>0</MntTotal></Totales>" in text
    assert "<MontoItem>0</MontoItem>" in text
    assert "<MntNeto>" not in text
    assert "<QtyItem>2</QtyItem>" in text
    assert (
        "<NroLinRef>1</NroLinRef><TpoDocRef>OT</TpoDocRef>"
        "<FolioRef>OT-0042</FolioRef><FchRef>2026-10-04</FchRef>" in text
    )
    assert "<DirRecep>Av. Los Robles 123, Concepción</DirRecep>" in text
    assert "<GiroRecep>" not in text

    # Replay: same guía returns the stored DTE without new folio or upload.
    existing52.append(insert_row)
    replay = sii.emit_dispatch_note_dte(
        org_id=order["org_id"], order_id=order["id"], actor_id=uuid4()
    )
    assert replay["folio"] == 1 and len(storage.uploads) == 1


def test_emit_dispatch_note_dte_ind_traslado_5(monkeypatch):
    storage = _Storage()
    order = _order_row()
    caf52 = _caf_row(
        sii._parse_caf(_caf_xml(tipo=52, desde=1, hasta=10)[0]),
        org_id=order["org_id"],
        actual=0,
    )
    _patch_env(
        monkeypatch,
        storage,
        order=order,
        note=_dispatch_note_row(order),
        cafs=[caf52],
    )
    sii.emit_dispatch_note_dte(
        org_id=order["org_id"],
        order_id=order["id"],
        actor_id=uuid4(),
        ind_traslado=5,
    )
    text = storage.uploads[0][1].decode("iso-8859-1")
    assert "<IndTraslado>5</IndTraslado>" in text
    # Internal transfer: the receptor is the issuer itself, not the
    # customer on the sealed guía.
    assert "<RUTRecep>76123456-0</RUTRecep>" in text
    assert "<RznSocRecep>Ventanas Prueba SpA</RznSocRecep>" in text
    assert "<DirRecep>Av. Los Robles 123, Concepción</DirRecep>" in text


def test_emit_dispatch_note_dte_ind_traslado_5_skips_client_rut(monkeypatch):
    storage = _Storage()
    order = _order_row()
    note = _dispatch_note_row(order)
    # A traslado interno never names the customer: a guía sealed with a
    # blank client RUT still stamps, because the issuer is the receptor.
    note["payload_json"]["project"]["client_rut"] = ""
    caf52 = _caf_row(
        sii._parse_caf(_caf_xml(tipo=52, desde=1, hasta=10)[0]),
        org_id=order["org_id"],
        actual=0,
    )
    _patch_env(
        monkeypatch,
        storage,
        order=order,
        note=note,
        cafs=[caf52],
    )
    sii.emit_dispatch_note_dte(
        org_id=order["org_id"],
        order_id=order["id"],
        actor_id=uuid4(),
        ind_traslado=5,
    )
    text = storage.uploads[0][1].decode("iso-8859-1")
    assert "<RUTRecep>76123456-0</RUTRecep>" in text


def test_emit_dispatch_note_dte_ind_traslado_5_needs_destination(monkeypatch):
    storage = _Storage()
    order = _order_row()
    note = _dispatch_note_row(order)
    note["payload_json"]["project"]["delivery_address"] = ""
    caf52 = _caf_row(
        sii._parse_caf(_caf_xml(tipo=52, desde=1, hasta=10)[0]),
        org_id=order["org_id"],
        actual=0,
    )
    _patch_env(
        monkeypatch,
        storage,
        order=order,
        note=note,
        cafs=[caf52],
    )
    with pytest.raises(ContractAPIException) as excinfo:
        sii.emit_dispatch_note_dte(
            org_id=order["org_id"],
            order_id=order["id"],
            actor_id=uuid4(),
            ind_traslado=5,
        )
    assert excinfo.value.contract_code == "sii_receptor_incomplete"
    assert storage.uploads == []


def test_emit_dispatch_note_dte_requires_sealed_note(monkeypatch):
    storage = _Storage()
    order = _order_row()
    _patch_env(monkeypatch, storage, order=order, note=None)
    with pytest.raises(ContractAPIException) as excinfo:
        sii.emit_dispatch_note_dte(
            org_id=order["org_id"], order_id=order["id"], actor_id=uuid4()
        )
    assert excinfo.value.contract_code == "dispatch_note_missing"
    assert storage.uploads == []


def test_emit_dispatch_note_dte_requires_caf_52(monkeypatch):
    storage = _Storage()
    order = _order_row()
    _patch_env(
        monkeypatch, storage, order=order, note=_dispatch_note_row(order), cafs=[]
    )
    with pytest.raises(ContractAPIException) as excinfo:
        sii.emit_dispatch_note_dte(
            org_id=order["org_id"], order_id=order["id"], actor_id=uuid4()
        )
    assert excinfo.value.contract_code == "sii_caf_exhausted"
    assert storage.uploads == []


def test_emit_dispatch_note_dte_requires_receptor_rut(monkeypatch):
    storage = _Storage()
    order = _order_row()
    note = _dispatch_note_row(order)
    note["payload_json"]["project"]["client_rut"] = ""
    caf52 = _caf_row(
        sii._parse_caf(_caf_xml(tipo=52, desde=1, hasta=10)[0]),
        org_id=order["org_id"],
        actual=0,
    )
    _patch_env(
        monkeypatch, storage, order=order, note=note, cafs=[caf52]
    )
    with pytest.raises(ContractAPIException) as excinfo:
        sii.emit_dispatch_note_dte(
            org_id=order["org_id"], order_id=order["id"], actor_id=uuid4()
        )
    assert excinfo.value.contract_code == "sii_receptor_missing"
    assert storage.uploads == []


def test_dispatch_note_dte_access_signs_the_stored_object(monkeypatch):
    storage = _Storage()
    order = _order_row()
    note = _dispatch_note_row(order)
    dte = _dte_row(
        None,
        folio=3,
        over={"dte_type": 52, "dispatch_note_id": str(note["id"]), "invoice_id": None},
    )
    _patch_env(monkeypatch, storage, order=order, existing_dte52=[dte])
    out = sii.dispatch_note_dte_access(org_id=order["org_id"], order_id=order["id"])
    assert out["folio"] == 3 and out["dte_type"] == 52
    assert dte["storage_object_key"] in out["signed_url"]
