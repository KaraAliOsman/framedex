"""Reviewable accessory quantities and prices, all exact DEMO authorities."""

from decimal import Decimal as D
import json
from typing import Any

from backend.catalogs.demo_extras import extra_manifest
from dekopen_engine.extra_models import ExtraAuthority, ExtraDefinition, ExtraSelection
from dekopen_engine.extras import partition_price, price_facts, project_lines
from dekopen_engine.geometry import compute_geometry
from dekopen_engine.models import ParametricNode, SystemParams


def extra_context(code: str = "DEMO_60", opening: str = "FIXED") -> tuple[SystemParams, ParametricNode]:
    record = next(row for row in extra_manifest() if row["code"] == code)
    params = SystemParams.model_validate_json(json.dumps(record["params"]))
    node = ParametricNode.model_validate_json(json.dumps({"id":"vano","type":"BAY","width_mm":"1500","height_mm":"1400",
        "opening_type":opening,"glass_thickness_mm":"24","glass_spec":"4-16-4","glass_article_sku":code+"-GLASS"}))
    if opening != "FIXED":
        from dekopen_engine.openings import opening_from_legacy
        from dekopen_engine.models import BayOpeningType, OpeningUse
        node = node.model_copy(update={"opening_type":None,"opening":opening_from_legacy(BayOpeningType(opening)),"opening_use":OpeningUse.WINDOW})
    return params,node


def installation(scope: str = "PROJECT", basis: str = "PERIMETER") -> ExtraDefinition:
    return ExtraDefinition.model_validate_json(json.dumps({"code":"INSTALL","name":"Instalación estándar","scope":scope,
        "kind":"SERVICE","basis":basis,"unit":"M" if basis == "PERIMETER" else "M2" if basis == "AREA" else "EA",
        "cost_rate":"1000","selling_rate":"1500","currency":"CLP","source":"Tarifa de ensayo declarada","synthetic":True,"installation":True}))


def extra_cases() -> dict[str, Any]:
    params,node = extra_context()
    node = node.model_copy(update={"extras":[ExtraSelection(code="SILL",overhang_left_mm=D(30),overhang_right_mm=D(30)),
        ExtraSelection(code="FRAME_EXTENSION",sides=["LEFT","RIGHT"]),ExtraSelection(code="SCREEN_FIXED")]})
    computation = compute_geometry(node,params,finish="WHITE")
    assert computation.result and computation.manufacturing_trace and params.extra_authority
    prices = price_facts(params.extra_authority,computation.result.extras)
    authority = ExtraAuthority(schema_version=1,definitions=[installation()],source="Ensayo")
    services = project_lines(authority,[ExtraSelection(code="INSTALL")],[(D(1500),D(1400),2)])
    return {"geometric-bom":computation.result.model_dump(mode="json"),
        "extra-members":[member.model_dump(mode="json") for member in computation.manufacturing_trace.members if member.assembly == "EXTRA"],
        "sublines":[item.model_dump(mode="json") for item in prices],
        "project-perimeter":[item.model_dump(mode="json") for item in services],
        "exact-partition":partition_price(D(210001),D(100000),[(item,item.total_price) for item in prices],quantity=2,currency="CLP")}
