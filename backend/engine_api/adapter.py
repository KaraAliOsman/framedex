"""Transport normalization and deterministic call into the pure engine."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import cast

from dekopen_engine import (
    BayOpeningType,
    EngineResult,
    NodeType,
    ParametricNode,
    SystemParams,
    calculate_geometry,
)


class InvalidEngineRequest(ValueError):
    pass


class UnsupportedEngineContract(ValueError):
    pass


_NODE_FIELDS = {
    "id",
    "type",
    "width_mm",
    "height_mm",
    "split_offset_mm",
    "mullion_profile_sku",
    "children",
    "opening_type",
    "glass_thickness_mm",
    "glass_spec",
    "glass_article_sku",
    "hardware_set_sku",
    "handle_height_mm",
}
_DECIMAL_NODE_FIELDS = {
    "width_mm",
    "height_mm",
    "split_offset_mm",
    "glass_thickness_mm",
    "handle_height_mm",
}


def _decimal_string(value: object, field_name: str) -> Decimal:
    if not isinstance(value, str):
        raise InvalidEngineRequest(f"{field_name} must be a decimal string")
    try:
        number = Decimal(value)
    except InvalidOperation as error:
        raise InvalidEngineRequest(f"{field_name} must be a decimal string") from error
    if not number.is_finite():
        raise InvalidEngineRequest(f"{field_name} must be finite")
    return number


def parse_parametric_node(payload: object) -> ParametricNode:
    if not isinstance(payload, dict) or not all(isinstance(key, str) for key in payload):
        raise InvalidEngineRequest("parametric_tree must be an object")
    raw = cast(dict[str, object], payload)
    unexpected = set(raw) - _NODE_FIELDS
    if unexpected:
        raise InvalidEngineRequest("parametric_tree contains unsupported fields")
    if not isinstance(raw.get("id"), str) or not isinstance(raw.get("type"), str):
        raise InvalidEngineRequest("Every node requires string id and type")

    values: dict[str, object] = {"id": raw["id"]}
    try:
        values["type"] = NodeType(cast(str, raw["type"]))
        if "opening_type" in raw and raw["opening_type"] is not None:
            if not isinstance(raw["opening_type"], str):
                raise InvalidEngineRequest("opening_type must be a string")
            values["opening_type"] = BayOpeningType(cast(str, raw["opening_type"]))
    except ValueError as error:
        raise InvalidEngineRequest("Unsupported node or opening type") from error

    for field_name in _DECIMAL_NODE_FIELDS:
        if field_name in raw and raw[field_name] is not None:
            values[field_name] = _decimal_string(raw[field_name], field_name)
    for field_name in (
        "mullion_profile_sku",
        "glass_spec",
        "glass_article_sku",
        "hardware_set_sku",
    ):
        if field_name in raw and raw[field_name] is not None:
            if not isinstance(raw[field_name], str):
                raise InvalidEngineRequest(f"{field_name} must be a string")
            values[field_name] = raw[field_name]

    children = raw.get("children", [])
    if not isinstance(children, list):
        raise InvalidEngineRequest("children must be an array")
    values["children"] = [parse_parametric_node(child) for child in children]
    try:
        return ParametricNode(**values)
    except ValueError as error:
        raise InvalidEngineRequest("Invalid parametric_tree") from error


def calculate_from_api(
    *,
    parametric_tree: object,
    nominal_width_mm: Decimal,
    nominal_height_mm: Decimal,
    color: str,
    params: SystemParams,
) -> EngineResult:
    if color != "WHITE":
        raise UnsupportedEngineContract("Only WHITE has a canonical SHOT-04 color mapping")

    root = parse_parametric_node(parametric_tree)
    if root.width_mm is not None and root.width_mm != nominal_width_mm:
        raise InvalidEngineRequest("nominal_width_mm conflicts with parametric_tree")
    if root.height_mm is not None and root.height_mm != nominal_height_mm:
        raise InvalidEngineRequest("nominal_height_mm conflicts with parametric_tree")
    root = root.model_copy(
        update={"width_mm": nominal_width_mm, "height_mm": nominal_height_mm}
    )
    try:
        return calculate_geometry(root, params, is_foiled=False)
    except NotImplementedError as error:
        raise UnsupportedEngineContract(str(error)) from error
    except ValueError as error:
        raise InvalidEngineRequest(str(error)) from error
