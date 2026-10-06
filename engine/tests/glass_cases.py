"""D02 golden fixtures: declared PVB, bead, minimum area and processing."""

from decimal import Decimal as D
from typing import Any

from backend.catalogs.demo_glass import demo_glass_product, demo_glass_rates
from dekopen_engine import ParametricNode, NodeType, BayOpeningType, calculate_geometry
from dekopen_engine.glass import build_glass_piece
from dekopen_engine.glass_composition import GlassProcessing, price_glass
from engine.tests.catalog_families import family_params


def glass_cases() -> dict[str, Any]:
    code = "DEMO_60"
    product = demo_glass_product(code, "SAFE")
    processing = GlassProcessing(polished_edges=("TOP", "BOTTOM", "LEFT", "RIGHT"), holes=2,
        bars_vertical=1, bars_horizontal=1)
    pane = build_glass_piece(bay_id="safe", width_mm=D("600"), height_mm=D("300"),
        glass_spec="3+3 PVB 0,38 / 13,62 aire / 4 templado", article_sku=code + "-GLASS-SAFE", product=product, processing=processing)
    price = price_glass(product=product, sku=code + "-GLASS-SAFE", width_mm=pane.width_mm, height_mm=pane.height_mm,
        rates={sku:D(rate) for sku, _, rate in demo_glass_rates(code)}, processing=processing)
    geometry = calculate_geometry(ParametricNode(id="safe", type=NodeType.BAY,
        width_mm=D("600"), height_mm=D("400"), opening_type=BayOpeningType.FIXED,
        glass_thickness_mm=D("24"), glass_spec=pane.glass_spec, glass_product=product,
        glass_processing=processing), family_params(code))
    return {"pane": pane.model_dump(mode="json"), "price": price.model_dump(mode="json"),
            "geometry": geometry.model_dump(mode="json")}
