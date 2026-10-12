from decimal import Decimal as D
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.catalogs.demo_glass import demo_glass_product, demo_safety_rules
from dekopen_engine.glass import migrate_glass_spec
from dekopen_engine.glass_composition import (
    GlassProduct, GlassProperties, GlassSafetyRule, GlassLimits, GlassProcessing,
    GlassInterlayer, parse_glass_notation, format_glass_notation, glass_mass_per_m2,
    total_glass_thickness, net_glass_thickness, assess_glass, SupplierValue, price_glass,
)
from dekopen_engine.glass_orders import supplier_glass_rows
from dekopen_engine import GlassPiece
from engine.tests.glass_cases import glass_cases


NOTATIONS = (
    "4 / 12 aire / 4", "5 / 12 Ar / 4 Low-E (c3)", "3+3 PVB 0,38", "4+4 / 16 / 6 templado",
    "DVH 5-12-5", "dvh 4-16-4", "4-12-3+3", "4-16-4-16-4", "6", "8 templado",
    "6 termoendurecido", "4 bronce", "5 gris", "6 verde", "4 control solar", "4 reflectivo",
    "6 espejo", "4 satinado", "6 arenado", "4 impreso", "6 FLOAT INCOLORO", "  4 / 16 ARGÓN / 4  ",
    "4 / 14 aire aluminio / 4", "4 / 14 Ar borde cálido / 4 Low-E (c3)",
    "4+4 PVB 0.76", "3+3+3 PVB 0,38", "3+3 PVB acústico 0,76", "10 templado {SKU-10}",
    "4 Low-E (c2) / 16 aire / 4", "TVH 4 / 12 aire / 4 / 12 Ar / 4 Low-E (c5)",
)


@pytest.mark.parametrize("notation", NOTATIONS)
def test_30_notations_roundtrip_without_guessing(notation: str) -> None:
    parsed = parse_glass_notation(notation)
    assert parse_glass_notation(format_glass_notation(parsed)) == parsed


def test_golden_pvb_bead_minimum_and_processing_are_exact() -> None:
    frozen = json.loads(Path(__file__).with_name("golden_glass_products.json").read_text(encoding="utf-8"))
    assert glass_cases() == frozen
    assert frozen["pane"]["weight_kg"] == "4.57"
    assert frozen["pane"]["thickness_total_mm"] == "24.00"
    assert frozen["price"]["area_m2"] == "0.18"
    assert frozen["price"]["billable_area_m2"] == "0.35"
    assert frozen["price"]["total_cost"] == "30000.00"
    assert {cut["sku"] for cut in frozen["geometry"]["profile_cuts"] if cut["role"] == "GLAZING_BEAD"} == {"DEMO_60-JQ-10"}


def test_unknown_interlayer_and_properties_are_never_zero_or_certified() -> None:
    composition = parse_glass_notation("3+3 / 16 / 4")
    product = GlassProduct(name="Producto por revisar", source="Ficha aportada", composition=composition)
    assert net_glass_thickness(composition) == D("10")
    assert total_glass_thickness(composition) is None
    assert glass_mass_per_m2(product) is None
    assert product.properties.ug is None and product.properties.safety_class is None
    with pytest.raises(ValidationError):
        GlassInterlayer(thickness_mm=D("0.38"), density_kg_m3=D("1070"))
    with pytest.raises(ValidationError):
        GlassProperties(solar_factor=SupplierValue(value=D("1.01"), source="Ficha"))
    with pytest.raises(ValidationError):
        GlassLimits(max_width_mm=D("3000"))


def test_door_safety_is_a_sourced_advisory_unless_org_requires_it() -> None:
    product = GlassProduct(name="Float común", source="Ficha", composition=parse_glass_notation("6"))
    rule = GlassSafetyRule.model_validate_json(json.dumps(demo_safety_rules()[0]))
    checks = assess_glass(product, width_mm=D("700"), height_mm=D("1800"), bead_thicknesses=(D("6"),), rules=(rule,), door=True)
    assert checks[0].source == rule.source and checks[0].synthetic and not checks[0].blocking
    required = rule.model_copy(update={"mandatory": True})
    assert assess_glass(product, width_mm=D("700"), height_mm=D("1800"), bead_thicknesses=(D("6"),), rules=(required,), door=True)[0].blocking
    assert not assess_glass(product, width_mm=D("700"), height_mm=D("1800"), bead_thicknesses=(D("6"),), rules=(required,))


def test_low_sidelight_large_pane_limits_and_hardware_are_distinct() -> None:
    product = demo_glass_product("DEMO_60", "LOWE")
    rules = tuple(GlassSafetyRule.model_validate_json(json.dumps(rule)) for rule in demo_safety_rules())
    checks = assess_glass(product, width_mm=D("2000"), height_mm=D("2000"), bead_thicknesses=(D("24"),), rules=rules,
        sidelight=True, sill_mm=D("799.99"), leaf_weight_kg=D("100.01"), hardware_limit_kg=D("100"))
    assert {check.code for check in checks} == {"DEMO-SIDELIGHT", "DEMO-LOW_PANE", "DEMO-LARGE_PANE", "hardware_mass_limit"}
    assert assess_glass(product, width_mm=D("3000.01"), height_mm=D("1000"), bead_thicknesses=(D("24"),))[0].blocking


def test_legacy_migration_preserves_unknown_cause() -> None:
    assert migrate_glass_spec("4-16-4 Float Incoloro")["composition"]["layers"][1]["width_mm"] == "16"
    assert migrate_glass_spec("3+3")["review_required"]
    assert migrate_glass_spec("producto especial sin ficha")["status"] == "UNKNOWN"
    assert migrate_glass_spec("producto especial sin ficha")["composition"] is None


def test_heterogeneous_pvb_and_case_sensitive_supplier_codes_roundtrip() -> None:
    for notation in ("3 + 3 + 4 [PVB 0,38; PVB acústico 0,76]", "4 / 16 aire sellante {THIOKOL-A} / 4"):
        composition = parse_glass_notation(notation)
        assert parse_glass_notation(format_glass_notation(composition)) == composition


def test_synthetic_class_does_not_satisfy_an_official_mandatory_rule() -> None:
    product = demo_glass_product("DEMO_60", "SAFE")
    rule = GlassSafetyRule(code="REAL", name="Puerta", zone="DOOR", source="Norma aportada", mandatory=True)
    checks = assess_glass(product, width_mm=D("700"), height_mm=D("1800"), bead_thicknesses=(D("24"),), rules=(rule,), door=True)
    assert any(check.code == "REAL" and check.blocking for check in checks)


def test_unknown_sill_does_not_bypass_mandatory_risk_review() -> None:
    product = demo_glass_product("DEMO_60", "LOWE")
    rule = GlassSafetyRule(code="BAJO", name="Paño bajo", zone="LOW_PANE", maximum_sill_mm=D("800"), source="Regla aportada", mandatory=True)
    checks = assess_glass(product, width_mm=D("700"), height_mm=D("1800"), bead_thicknesses=(D("24"),), rules=(rule,))
    assert checks[0].code == "BAJO_height_unknown" and checks[0].blocking


def test_supplier_weight_and_ug_cannot_be_zero() -> None:
    for field in ("weight_kg_m2", "ug"):
        with pytest.raises(ValidationError):
            GlassProperties.model_validate({field: SupplierValue(value=D("0"), source="Ficha")})


def test_missing_processing_tariff_is_an_error_and_costs_use_exact_area() -> None:
    product = demo_glass_product("DEMO_60", "LOWE")
    with pytest.raises(ValueError, match="Perforación"):
        price_glass(product=product, sku="BASE", width_mm=D("600"), height_mm=D("300"),
            rates={"BASE": D("1000")}, processing=GlassProcessing(holes=1))


@pytest.mark.parametrize("kind", ["SAFE", "LOWE"])
def test_response_preserves_the_exact_recipe_and_detects_real_changes(kind: str) -> None:
    from dekopen_engine.snapshot import result_payload, calculation_hash
    from dekopen_engine.models import EngineResult
    from dekopen_engine.glass import build_glass_piece
    original = EngineResult.model_validate_json(json.dumps(glass_cases()["geometry"]))
    original = original.model_copy(update={"glasses": [build_glass_piece(bay_id="B1", width_mm=D("600.00"), height_mm=D("300.00"),
        glass_spec="", product=demo_glass_product("DEMO_60", kind))]})
    response = result_payload(original)
    assert response["glasses"] == original.model_dump(mode="json")["glasses"]
    before = calculation_hash({}, response)
    changed = json.loads(json.dumps(response))
    changed["glasses"][0]["composition"]["layers"][0]["plies"][0]["thickness_mm"] = "3.01"
    assert calculation_hash({}, changed) != before


def test_supplier_batch_of_twelve_positions_matches_each_engine_piece() -> None:
    frozen = glass_cases()["geometry"]["glasses"][0]
    piece = GlassPiece.model_validate_json(json.dumps(frozen))
    batch = tuple(row for position in range(1, 13) for row in supplier_glass_rows(
        order_code=f"OT-{position:03d}", position_index=position, location=f"Dormitorio {position}", quantity=2, pieces=[piece]))
    assert len(batch) == 12
    for row in batch:
        assert row.width_mm == piece.width_mm and row.height_mm == piece.height_mm
        assert row.quantity == 2 and len(row.label_codes) == 2
        assert row.integer_dimensions
        assert "no se recorta" in row.instructions[0].lower()
