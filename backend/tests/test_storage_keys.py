"""§C storage-key trust — the canonical sanitizer serves upload and read."""

from __future__ import annotations

import pytest

from documents.repository import DocumentaryError
from documents.storage import readable_storage_key, sanitize_storage_key
from ingest.extract import safe_file_name


def test_sanitize_storage_key_accepts_canonical_keys() -> None:
    assert (
        sanitize_storage_key("imports/org/proj/imp/lista de precios (v2).pdf")
        == "imports/org/proj/imp/lista de precios (v2).pdf"
    )
    assert sanitize_storage_key("artifacts/o/v/doc-01.pdf") == "artifacts/o/v/doc-01.pdf"


@pytest.mark.parametrize(
    "key",
    [
        "",
        "imports//org/file.pdf",
        "imports/./org/file.pdf",
        "imports/../secret",
        "../escape.pdf",
        "./file.pdf",
        "imports/org/..",
        "imports/org/a\\b.pdf",
        "imports/org/a%2Fb.pdf",
        "imports/org/100%.pdf",
        "imports/org/lead name.pdf".replace("imports", " imports"),
        "imports/org/trail .pdf".replace("org", "org "),
        "imports/org/a\tb.pdf",
        "imports/org/a\nb.pdf",
    ],
)
def test_sanitize_storage_key_rejects_noncanonical_keys(key: str) -> None:
    with pytest.raises(DocumentaryError) as caught:
        sanitize_storage_key(key)
    assert caught.value.code == "storage_key_invalid"


def test_sanitize_storage_key_rejects_non_strings() -> None:
    with pytest.raises(DocumentaryError):
        sanitize_storage_key(None)  # type: ignore[arg-type]


def test_readable_storage_key_tolerates_literal_percent() -> None:
    """A '%' the upload path stored stays readable later — the read rule
    only refuses what could escape the bucket."""
    assert (
        readable_storage_key("imports/org/proj/imp/iva 19%.pdf")
        == "imports/org/proj/imp/iva 19%.pdf"
    )


@pytest.mark.parametrize(
    "key",
    [
        "imports//org/file.pdf",
        "imports/../secret",
        "imports/org/a\\b.pdf",
        " imports/org/lead.pdf",
        "imports/org/trail.pdf ",
        "imports/org/a\tb.pdf",
    ],
)
def test_readable_storage_key_still_rejects_noncanonical(key: str) -> None:
    with pytest.raises(DocumentaryError) as caught:
        readable_storage_key(key)
    assert caught.value.code == "storage_key_invalid"


def test_safe_file_name_rejects_edge_whitespace() -> None:
    """A leading/trailing space must fail validation BEFORE upload — the
    canonical key check would otherwise refuse the object it minted."""
    assert not safe_file_name(" lista.pdf")
    assert not safe_file_name("lista.pdf ")
    assert not safe_file_name(" lista.pdf ")
    assert safe_file_name("lista de precios.pdf")
    assert not safe_file_name("")
