"""Transport normalization and deterministic call into the pure engine."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Literal, cast

from dekopen_engine import (
    BayOpeningType,
    CoupledAssembly,
    CouplingDef,
    EffectiveProfileArticle,
    EngineResult,
    NodeType,
    ParametricNode,
    ProductEvaluation,
    ProductModel,
    ProductModule,
    SystemParams,
    calculate_geometry,
    evaluate_product,
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
    "panel_article_sku",
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
        "panel_article_sku",
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


def normalized_root_from_api(
    *,
    parametric_tree: object,
    nominal_width_mm: Decimal,
    nominal_height_mm: Decimal,
    color: str,
    params: SystemParams,
) -> ParametricNode:
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
    return root


def calculate_from_api(
    *, parametric_tree: object, nominal_width_mm: Decimal, nominal_height_mm: Decimal,
    color: str, params: SystemParams,
) -> EngineResult:
    root = normalized_root_from_api(
        parametric_tree=parametric_tree, nominal_width_mm=nominal_width_mm,
        nominal_height_mm=nominal_height_mm, color=color, params=params,
    )
    try:
        return calculate_geometry(root, params, is_foiled=False)
    except NotImplementedError as error:
        raise UnsupportedEngineContract(str(error)) from error
    except ValueError as error:
        raise InvalidEngineRequest(str(error)) from error


_PRODUCT_FIELDS = {"version", "assembly"}
_ASSEMBLY_FIELDS = {"modules", "couplings"}
_MODULE_FIELDS = {"id", "width_mm", "height_mm", "tree"}
_COUPLING_FIELDS = {"id", "angle_deg", "coupler_profile_sku"}


def _require_dict(payload: object, field_name: str) -> dict[str, object]:
    if not isinstance(payload, dict) or not all(
        isinstance(key, str) for key in payload
    ):
        raise InvalidEngineRequest(f"{field_name} must be an object")
    return cast(dict[str, object], payload)


def _require_str(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise InvalidEngineRequest(f"{field_name} must be a string")
    return value


def parse_product_model(payload: object) -> ProductModel:
    raw = _require_dict(payload, "product")
    unexpected = set(raw) - _PRODUCT_FIELDS
    if unexpected:
        raise InvalidEngineRequest(
            f"product contains unsupported fields: {sorted(unexpected)}"
        )
    if raw.get("version") != "product-v2":
        raise InvalidEngineRequest("product.version must be 'product-v2'")

    assembly = _require_dict(raw.get("assembly"), "product.assembly")
    unexpected = set(assembly) - _ASSEMBLY_FIELDS
    if unexpected:
        raise InvalidEngineRequest(
            f"product.assembly contains unsupported fields: {sorted(unexpected)}"
        )
    raw_modules = assembly.get("modules")
    raw_couplers = assembly.get("couplings", [])
    if not isinstance(raw_modules, list) or not raw_modules:
        raise InvalidEngineRequest("product.assembly.modules must be a non-empty array")
    if not isinstance(raw_couplers, list):
        raise InvalidEngineRequest("product.assembly.couplings must be an array")

    modules: list[ProductModule] = []
    seen_ids: set[str] = set()
    for item in raw_modules:
        module = _require_dict(item, "module")
        unexpected = set(module) - _MODULE_FIELDS
        if unexpected:
            raise InvalidEngineRequest(
                f"module contains unsupported fields: {sorted(unexpected)}"
            )
        module_id = _require_str(module.get("id"), "module.id")
        if module_id in seen_ids:
            raise InvalidEngineRequest("module ids must be unique")
        seen_ids.add(module_id)
        modules.append(
            ProductModule(
                id=module_id,
                width_mm=_decimal_string(module.get("width_mm"), "module.width_mm"),
                height_mm=_decimal_string(
                    module.get("height_mm"), "module.height_mm"
                ),
                tree=parse_parametric_node(module.get("tree")),
            )
        )

    couplings: list[CouplingDef] = []
    for item in raw_couplers:
        coupling = _require_dict(item, "coupling")
        unexpected = set(coupling) - _COUPLING_FIELDS
        if unexpected:
            raise InvalidEngineRequest(
                f"coupling contains unsupported fields: {sorted(unexpected)}"
            )
        sku = coupling.get("coupler_profile_sku")
        if sku is not None and not isinstance(sku, str):
            raise InvalidEngineRequest("coupler_profile_sku must be a string")
        couplings.append(
            CouplingDef(
                id=_require_str(coupling.get("id"), "coupling.id"),
                angle_deg=_decimal_string(
                    coupling.get("angle_deg"), "coupling.angle_deg"
                ),
                coupler_profile_sku=cast(str | None, sku),
            )
        )

    try:
        return ProductModel(
            version=cast(Literal["product-v2"], "product-v2"),
            assembly=CoupledAssembly(modules=modules, couplings=couplings),
        )
    except ValueError as error:
        raise InvalidEngineRequest("Invalid product model") from error


def evaluate_assembly_from_api(
    *,
    product: object,
    color: str,
    params: SystemParams,
    coupler_articles: dict[str, EffectiveProfileArticle] | None = None,
) -> ProductEvaluation:
    if color != "WHITE":
        raise UnsupportedEngineContract(
            "Only WHITE has a canonical color mapping"
        )
    model = (
        product
        if isinstance(product, ProductModel)
        else parse_product_model(product)
    )
    return evaluate_product(
        model, params, coupler_articles=coupler_articles, is_foiled=False
    )
