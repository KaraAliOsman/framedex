"""Pure canonical response serialization and calculation identity; no file I/O."""

from collections.abc import Mapping
from decimal import Decimal
import hashlib
import json
from typing import TypeAlias

from dekopen_engine.models import EngineResult

JsonValue: TypeAlias = None | bool | int | str | list["JsonValue"] | dict[str, "JsonValue"]


def _json_value(value: object, field: str = "") -> JsonValue:
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Canonical numbers must be finite")
        quantum = (
            Decimal("0.01") if field.endswith("_mm") or field.endswith("_kg")
            else Decimal("0.0001") if field == "area_m2"
            else Decimal("0.1") if field in ("angle_left", "angle_right") else None
        )
        if quantum is not None:
            scaled = value.quantize(quantum)
            if scaled != value:
                raise ValueError(f"Canonical output would lose precision: {field}")
            return format(scaled, "f")
        return format(value, "f")
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            raise ValueError("Canonical object keys must be strings")
        return {key: _json_value(item, key) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    raise ValueError("Unsupported canonical value; technical numbers require Decimal")


def canonical_json(value: object) -> bytes:
    return json.dumps(
        _json_value(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def calculation_hash(request: Mapping[str, object], response: Mapping[str, object]) -> str:
    without_hash = {key: value for key, value in response.items() if key != "calculation_hash"}
    preimage = {"request": request, "response_without_calculation_hash": without_hash}
    return "sha256:" + hashlib.sha256(canonical_json(preimage)).hexdigest()


def result_payload(result: EngineResult) -> dict[str, JsonValue]:
    value = _json_value(result.model_dump())
    assert isinstance(value, dict)
    return value


def calculation_response(request: Mapping[str, object], result: EngineResult) -> dict[str, JsonValue]:
    response = result_payload(result)
    response["calculation_hash"] = calculation_hash(request, response)
    return response
