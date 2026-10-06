"""Declared synthetic glass fixture. No certification or supplier performance."""

from decimal import Decimal
from typing import Any

from dekopen_engine.glass_composition import (
    GlassProduct, GlassBilling, GlassProperties, GlassLimits, SupplierSafety,
    GlassPane, GlassInterlayer, parse_glass_notation,
)

SOURCE = "DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"


def demo_glass_product(code: str, kind: str) -> GlassProduct:
    safe = kind == "SAFE"
    composition = parse_glass_notation("3+3 PVB 0,38 / 13,62 aire aluminio / 4 templado" if safe
        else "4 / 16 Ar borde cálido / 4 Low-E (c3)")
    if safe:
        pane = composition.layers[0]
        assert isinstance(pane, GlassPane)
        composition = composition.model_copy(update={"layers": (
            pane.model_copy(update={"interlayers": (GlassInterlayer(thickness_mm=Decimal("0.38"), density_kg_m3=Decimal("1070"), source=SOURCE),)}),
            *composition.layers[1:])})
    return GlassProduct(name="DEMO · Termopanel laminado de seguridad" if safe else "DEMO · Termopanel Low-E",
        composition=composition, source=SOURCE, synthetic=True,
        properties=GlassProperties(safety_class=SupplierSafety(value="B", source=SOURCE) if safe else None),
        limits=GlassLimits(min_width_mm=Decimal("100"), max_width_mm=Decimal("3000"),
            min_height_mm=Decimal("100"), max_height_mm=Decimal("3000"), max_aspect_ratio=Decimal("8"), source=SOURCE),
        billing=GlassBilling(minimum_area_m2=Decimal("0.35"), tempering_sku=f"{code}-GLASS-TEMPER",
            polishing_sku=f"{code}-GLASS-POLISH", drilling_sku=f"{code}-GLASS-DRILL",
            bars_per_m_sku=f"{code}-GLASS-BAR", bars_per_crossing_sku=f"{code}-GLASS-CROSS", source=SOURCE))


def demo_safety_rules() -> list[dict[str, Any]]:
    return [{"code": "DEMO-" + zone, "name": name, "zone": zone, "source": SOURCE,
             "synthetic": True, "mandatory": False, **extra} for zone, name, extra in (
        ("DOOR", "Puerta vidriada · ejemplo sintético", {}),
        ("SIDELIGHT", "Panel lateral · ejemplo sintético", {}),
        ("LOW_PANE", "Paño bajo · ejemplo sintético", {"maximum_sill_mm": "800"}),
        ("LARGE_PANE", "Gran ventanal · ejemplo sintético", {"minimum_area_m2": "3"}),
    )]


def demo_glass_rates(code: str) -> list[tuple[str, str, str]]:
    return [(f"{code}-GLASS-{suffix}", unit, rate) for suffix, unit, rate in (
        ("SAFE", "M2", "45000"), ("LOWE", "M2", "32000"), ("TEMPER", "M2", "6000"),
        ("POLISH", "M", "2500"), ("DRILL", "EA", "1800"), ("BAR", "M", "3500"), ("CROSS", "EA", "900"),
    )]
