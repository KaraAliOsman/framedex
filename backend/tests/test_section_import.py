"""Section drawing ingestion — parser + service contract tests."""
import pytest

from catalogs import section_import, service


SQUARE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="60mm" height="70mm">'
    '<polygon points="0,0 60,0 60,70 0,70"/></svg>'
).encode()


def test_svg_polygon_mm_units():
    result = section_import.import_section("frame.svg", SQUARE_SVG)
    assert result.format == "svg"
    assert result.mm_per_unit is not None and str(result.mm_per_unit) == "1"
    assert len(result.candidates) == 1
    assert result.candidates[0]["area"] == "4200.00"
    assert result.warnings == []


def test_svg_polyline_must_be_closed():
    content = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="100mm">'
        '<polyline points="0,0 60,0 60,70"/>'
        '<polygon points="0,0 60,0 60,70 0,70"/></svg>'
    ).encode()
    result = section_import.import_section("profile.svg", content)
    assert len(result.candidates) == 1
    assert any("open outline" in w for w in result.warnings)


def test_svg_path_and_transforms_apply():
    content = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="80mm">'
        '<g transform="translate(10,5) scale(2)">'
        '<path d="M0,0 L30,0 L30,35 L0,35 Z"/></g></svg>'
    ).encode()
    result = section_import.import_section("sash.svg", content)
    pts = result.candidates[0]["points"]
    assert [p[0] for p in pts] == ["10.0", "70.0", "70.0", "10.0", "10.0"]
    assert result.candidates[0]["area"] == "4200.00"


def test_svg_curved_path_samples_to_polygon():
    content = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="100mm">'
        '<path d="M0,0 L60,0 C60,10 60,20 60,30 L0,30 Z"/></svg>'
    ).encode()
    result = section_import.import_section("bead.svg", content)
    assert len(result.candidates) == 1
    # Curve sampled: more vertices than the 4 corners.
    assert len(result.candidates[0]["points"]) > 8


def test_svg_px_flagged_for_review():
    content = b'<svg xmlns="http://www.w3.org/2000/svg" width="60px"><polygon points="0,0 60,0 60,70 0,70"/></svg>'
    result = section_import.import_section("web.svg", content)
    assert any("96 dpi" in w for w in result.warnings)


LWPOLY_DXF = """  0
SECTION
  2
HEADER
  9
$INSUNITS
 70
     4
  0
ENDSEC
  0
SECTION
  2
ENTITIES
  0
LWPOLYLINE
  5
100
 70
     1
 90
        4
 10
0.0
 20
0.0
 10
60.0
 20
0.0
 10
60.0
 20
70.0
 10
0.0
 20
70.0
  0
ENDSEC
  0
EOF
""".encode()


def test_dxf_closed_lwpolyline_insunits_mm():
    result = section_import.import_section("frame.dxf", LWPOLY_DXF)
    assert result.format == "dxf"
    assert result.mm_per_unit is not None and str(result.mm_per_unit) == "1"
    assert result.candidates[0]["area"] == "4200.00"
    assert len(result.candidates[0]["points"]) == 4


def test_dxf_without_insunits_warns():
    content = LWPOLY_DXF.replace(b"  9\n$INSUNITS\n 70\n     4\n", b"")
    result = section_import.import_section("drawing.dxf", content)
    assert result.mm_per_unit is None
    assert any("$INSUNITS" in w for w in result.warnings)


def test_dxf_bulge_expands_arc():
    content = LWPOLY_DXF.replace(
        b" 10\n60.0\n 20\n70.0\n", b" 10\n60.0\n 20\n70.0\n 42\n1.0\n"
    )
    result = section_import.import_section("arched.dxf", content)
    # The bulged closing edge samples into additional points.
    assert len(result.candidates[0]["points"]) > 4


def test_dxf_open_polyline_skipped():
    content = LWPOLY_DXF.replace(b" 70\n     1\n", b" 70\n     0\n")
    with pytest.raises(section_import.SectionImportError):
        section_import.import_section("open.dxf", content)


def test_empty_file_rejected():
    with pytest.raises(section_import.SectionImportError):
        section_import.import_section("blank.dxf", b"")


class _Storage:
    def __init__(self):
        self.writes = []

    def upload_immutable(self, object_key, content, content_type):
        self.writes.append((object_key, content_type))


def test_service_parses_and_stores(monkeypatch):
    storage = _Storage()
    monkeypatch.setattr(
        "documents.storage.SupabaseDocumentStorage", lambda: storage
    )
    # The service imports the storage class lazily inside the function.
    import documents.storage as storage_mod

    monkeypatch.setattr(storage_mod, "SupabaseDocumentStorage", lambda: storage)
    out = service.import_section_drawing(
        org_id="org-1",
        file_name="frame.dxf",
        content=LWPOLY_DXF,
        content_type="application/dxf",
    )
    assert out["document_path"].startswith("section-imports/org-1/")
    assert out["document_path"].endswith("/frame.dxf")
    assert out["format"] == "dxf"
    assert out["mm_per_unit"] is not None
    assert storage.writes and storage.writes[0][1] == "application/dxf"


def test_service_rejects_bad_name(monkeypatch):
    with pytest.raises(Exception) as exc:
        service.import_section_drawing(
            org_id="org-1", file_name="../escape.dxf", content=LWPOLY_DXF, content_type=""
        )
    assert "section_file_name" in str(exc.value)


def test_service_rejects_unparseable(monkeypatch):
    with pytest.raises(Exception) as exc:
        service.import_section_drawing(
            org_id="org-1", file_name="notes.txt", content=b"hello world", content_type=""
        )
    assert "section" in str(exc.value)
