"""Versioned canonical bytes and SHA-256 identities for documentary evidence."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from hashlib import sha256
import json
import numbers
from typing import TypeAlias, cast
from uuid import UUID

from pydantic import BaseModel

DOCUMENTARY_CANONICAL_VERSION = "DOCUMENTARY_CANONICAL_V1"
MAX_SAFE_INTEGER = 9_007_199_254_740_991
DocumentaryValue: TypeAlias = (
    None | bool | int | str | list["DocumentaryValue"] | dict[str, "DocumentaryValue"]
)


def _datetime_text(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Documentary datetimes must include a timezone")
    utc = value.astimezone(timezone.utc)
    rendered = utc.isoformat(timespec="microseconds" if utc.microsecond else "seconds")
    return rendered.removesuffix("+00:00") + "Z"


def _documentary_value(value: object) -> DocumentaryValue:
    # Decoded sealed snapshots overwhelmingly contain exact JSON builtins.
    # Resolve those without traversing model/number ABCs at every leaf; typed
    # subclasses still go through the original authority conversion below.
    kind = type(value)
    if value is None or kind in (str, bool):
        return cast(DocumentaryValue, value)
    if kind is int:
        integer = cast(int, value)
        if abs(integer) > MAX_SAFE_INTEGER:
            raise ValueError("Documentary integers must be JSON-safe")
        return integer
    if kind is dict:
        mapping = cast(dict[object, object], value)
        if not all(isinstance(key, str) for key in mapping):
            raise ValueError("Documentary object keys must be strings")
        return {cast(str, key): _documentary_value(item) for key, item in mapping.items()}
    if kind is list:
        return [_documentary_value(item) for item in cast(list[object], value)]
    if isinstance(value, BaseModel):
        return _documentary_value(value.model_dump(mode="python", by_alias=True))
    if isinstance(value, Enum):
        return _documentary_value(value.value)
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Documentary decimals must be finite")
        return format(value, "f")
    if isinstance(value, datetime):
        return _datetime_text(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, int):
        if abs(value) > MAX_SAFE_INTEGER:
            raise ValueError("Documentary integers must be JSON-safe")
        return value
    if isinstance(value, numbers.Number):
        raise ValueError("Documentary numbers require Decimal, never float")
    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            raise ValueError("Documentary object keys must be strings")
        return {key: _documentary_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_documentary_value(item) for item in value]
    raise ValueError(f"Unsupported documentary value: {type(value).__name__}")


def documentary_canonical_json_v1(value: object) -> bytes:
    return json.dumps(
        _documentary_value(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def documentary_sha256_v1(value: object) -> str:
    return sha256(documentary_canonical_json_v1(value)).hexdigest()


def bom_hash_v1(
    *, project_id: UUID | str, revision: str, positions: object, bom: object
) -> str:
    if not revision or revision != revision.strip():
        raise ValueError("Documentary revision must be canonical")
    canonical_project_id = project_id if isinstance(project_id, UUID) else UUID(project_id)
    return documentary_sha256_v1(
        {
            "project_id": canonical_project_id,
            "revision": revision,
            "positions": positions,
            "bom": bom,
        }
    )


def snapshot_sha256_v1(snapshot: Mapping[str, object]) -> str:
    if "snapshot_sha256" in snapshot:
        raise ValueError("Snapshot hash cannot include itself")
    return documentary_sha256_v1(snapshot)


def file_sha256(content: bytes) -> str:
    return sha256(content).hexdigest()
