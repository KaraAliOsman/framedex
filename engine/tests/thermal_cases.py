"""Isolated arithmetic fixtures. These do not certify the DEMO catalog."""
from datetime import date
from decimal import Decimal as D
import json
from typing import Any

from dekopen_engine.geometry import compute_geometry
from dekopen_engine.glass_composition import GlassProduct, parse_glass_notation
from dekopen_engine.models import ParametricNode, NodeType, BayOpeningType
from dekopen_engine.thermal import ThermalAuthority, ThermalGeometry, calculate_uw, thermal_geometry
from dekopen_engine.technical_facts import GeometryComputation
from engine.tests.catalog import demo_60_params

AS_OF = date(2026, 10, 11)


def geometry(opening: BayOpeningType = BayOpeningType.FIXED, *, split: bool = False) -> tuple[ThermalGeometry, GeometryComputation]:
    composition = parse_glass_notation("4-16-4")
    composition = composition.model_copy(update={"layers": (composition.layers[0],
        composition.layers[1].model_copy(update={"spacer":"WARM_EDGE"}), composition.layers[2])})
    product = GlassProduct(name="Caso de cálculo manual, no certificado", source="Prueba unitaria aislada",
        composition=composition)
    root = ParametricNode(id="fixed", type=NodeType.BAY, width_mm=D("1000"), height_mm=D("1000"),
        opening_type=opening, glass_thickness_mm=D("24"), glass_spec="4-16-4",
        glass_article_sku="TEST-GLASS", glass_product=product)
    if split:
        root = ParametricNode(id="split",type=NodeType.SPLIT_V,width_mm=D("1000"),height_mm=D("1000"),
            split_offset_mm=D("500"),mullion_profile_sku="POSTE-V",
            children=[root.model_copy(update={"id":identity,"width_mm":None,"height_mm":None}) for identity in ("left","right")])
    computation = compute_geometry(root, demo_60_params())
    thermal = thermal_geometry(computation)
    assert thermal is not None
    return thermal, computation


def reports(geo: ThermalGeometry | None = None) -> tuple[ThermalAuthority, ...]:
    geo = geo or geometry()[0]
    pane = geo.panes[0]
    common = {"catalog_fingerprint": "unit-test-geometry", "profile_skus": list(geo.profile_skus),
        "min_width_mm": "1000", "max_width_mm": "1000", "min_height_mm": "1000", "max_height_mm": "1000",
        "opening_types": list(geo.opening_types), "source_document": "Prueba matemática aislada; sin certificación",
        "source_url": "https://example.test/caso-manual", "source_page": "Caso1",
        "laboratory": "Fixture de prueba unitaria", "report_date": "2026-01-01", "valid_until": "2027-01-01",
        "standard": "ISO 10077-1: ecuación de áreas", "applicability": "Solo fixture; no usar en obra.",
        "review_state": "REVIEWED", "reviewed_by": "reviewer-test", "reviewed_at": "2026-01-02"}
    glass = {"glass_sku": pane.glass_sku, "glass_fingerprint": pane.glass_fingerprint}
    values = [{**common, "id":"frame", "kind":"FRAME", "uf":"1.5"},
              {**common, **glass, "id":"glass", "kind":"GLASS", "ug":"1.1", "solar_factor":"0.55"},
              {**common, **glass, "id":"spacer", "kind":"SPACER", "spacer_code":pane.spacer_code, "psi_g":"0.05"},
              {**common, "id":"air", "kind":"PERFORMANCE", "construction_fingerprint":geo.construction_fingerprint, "air_class":3, "air_pressure_pa":"100", "water_class":"7A", "wind_class":"C3",
               "standard":"NCh3296 y NCh3297 · solo fixture", "laboratory_registration":"Registro de prueba aislado, sin acreditación real"}]
    return tuple(ThermalAuthority.model_validate_json(json.dumps(v)) for v in values)


def thermal_cases() -> dict[str, Any]:
    geo, _ = geometry()
    result = calculate_uw(geo, reports(geo), catalog_fingerprint="unit-test-geometry", as_of=AS_OF)
    # Frame face60 each side: 1000−120=880mm daylight. Cut=910mm
    # because rebate20−clearance5 hides15mm at EACH edge.
    # Ag=.88*.88=.7744; Af=1−.7744=.2256; lg=2(.88+.88)=3.52.
    # .7744*1.1 + .2256*1.5 + 3.52*.05 = .85184+.3384+.176
    # =1.36624 W/K. Divide by 1m² =>Uw=1.36624 W/m²K, exactly.
    additional = {}
    for name, opening, split in (("casement",BayOpeningType.TURN_LEFT,False),("split",BayOpeningType.FIXED,True)):
        other, _ = geometry(opening,split=split)
        metric = calculate_uw(other,reports(other),catalog_fingerprint="unit-test-geometry",as_of=AS_OF)
        additional[name] = {"daylight_mm":[[str(p.visible_width_mm),str(p.visible_height_mm)] for p in other.panes],
            **{key:str(metric["trace"][key]) for key in ("ag_m2","af_m2","lg_m","numerator_w_k")},"uw":str(metric["uw"])}
    return {"method":"ISO 10077-1 · áreas visibles", "daylight_mm":["880","880"], "cut_mm":["910","910"],
        **{key:str(result["trace"][key]) for key in ("ag_m2","af_m2","lg_m","area_m2","numerator_w_k")},
        "uw":str(result["uw"]), "air_class":result["air_class"],"additional":additional}
