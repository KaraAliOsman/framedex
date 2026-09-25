"""§C storage-key trust — the canonical sanitizer serves upload and read."""

from __future__ import annotations

import pytest

from documents.repository import DocumentaryError
from documents.storage import sanitize_storage_key


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
