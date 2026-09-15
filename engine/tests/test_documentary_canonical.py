from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from hashlib import sha256
from uuid import UUID

import pytest
from pydantic import BaseModel

from dekopen_engine.documentary_canonical import (
    DOCUMENTARY_CANONICAL_VERSION,
    bom_hash_v1,
    documentary_canonical_json_v1,
    documentary_sha256_v1,
    file_sha256,
    snapshot_sha256_v1,
)


class Kind(str, Enum):
    VALUE = "VÁLIDO"


class Evidence(BaseModel):
    amount: Decimal
    kind: Kind


def test_documentary_canonical_vector_is_byte_exact() -> None:
    value = {
        "z": Decimal("1.2000"),
        "a": [True, None, 7, UUID("01234567-89ab-cdef-0123-456789abcdef")],
        "á": Evidence(amount=Decimal("0.00"), kind=Kind.VALUE),
        "date": date(2026, 9, 14),
        "time": datetime(2026, 9, 14, 8, 5, 4, 321000, tzinfo=timezone(timedelta(hours=-3))),
    }
    expected = (
        '{"a":[true,null,7,"01234567-89ab-cdef-0123-456789abcdef"],'
        '"date":"2026-09-14","time":"2026-09-14T11:05:04.321000Z",'
        '"z":"1.2000","á":{"amount":"0.00","kind":"VÁLIDO"}}'
    ).encode("utf-8")
    assert DOCUMENTARY_CANONICAL_VERSION == "DOCUMENTARY_CANONICAL_V1"
    assert documentary_canonical_json_v1(value) == expected
    assert documentary_sha256_v1(value) == sha256(expected).hexdigest()
    assert documentary_canonical_json_v1(dict(reversed(list(value.items())))) == expected


def test_bom_hash_has_exactly_four_semantic_components() -> None:
    project_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    positions = [{"id": "P-1", "width_mm": Decimal("1000.00")}]
    bom = [{"position_id": "P-1", "profile_cuts": []}]
    preimage = (
        '{"bom":[{"position_id":"P-1","profile_cuts":[]}],'
        '"positions":[{"id":"P-1","width_mm":"1000.00"}],'
        '"project_id":"aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa","revision":"REV-A"}'
    ).encode()
    actual = bom_hash_v1(project_id=project_id, revision="REV-A", positions=positions, bom=bom)
    assert actual == sha256(preimage).hexdigest()
    assert len(actual) == 64
    assert actual != documentary_sha256_v1({"canonical_version": DOCUMENTARY_CANONICAL_VERSION,
                                            "project_id": project_id, "revision": "REV-A",
                                            "positions": positions, "bom": bom})
    with pytest.raises(ValueError, match="canonical"):
        bom_hash_v1(project_id=project_id, revision=" REV-A", positions=positions, bom=bom)
    with pytest.raises(ValueError):
        bom_hash_v1(project_id="not-a-uuid", revision="REV-A", positions=positions, bom=bom)


def test_snapshot_and_file_hash_namespaces_are_distinct() -> None:
    snapshot = {"bom_hash": "0" * 64, "payload": {"amount": Decimal("10.00")}}
    snapshot_hash = snapshot_sha256_v1(snapshot)
    encoded = documentary_canonical_json_v1(snapshot)
    assert snapshot_hash == sha256(encoded).hexdigest()
    assert file_sha256(encoded + b"\n") != snapshot_hash
    with pytest.raises(ValueError, match="include itself"):
        snapshot_sha256_v1({**snapshot, "snapshot_sha256": snapshot_hash})


@pytest.mark.parametrize(
    "value",
    [
        0.1,
        {"nested": [Decimal("NaN")]},
        {1: "not-a-string-key"},
        9_007_199_254_740_992,
        datetime(2026, 9, 14),
        b"bytes-are-file-authority-only",
    ],
)
def test_documentary_canonical_rejects_ambiguous_values(value: object) -> None:
    with pytest.raises(ValueError):
        documentary_canonical_json_v1(value)
