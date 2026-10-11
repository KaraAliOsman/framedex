"""Advanced inspector authorities and precision at the HTTP boundary."""
from contextlib import nullcontext
from decimal import Decimal as D
from uuid import uuid4

import pytest

from catalogs.glass_views import GlassPreviewInputSerializer
from engine.tests.advanced_cases import advanced_node, advanced_params, advanced_typologies
from projects import hardware


def test_glass_preview_preserves_fractional_engine_output_exactly():
    value = "635.166666666666666666666666590000"
    serializer = GlassPreviewInputSerializer(data={
        "system_id": str(uuid4()), "product": {}, "width_mm": value,
        "height_mm": "1985", "leaf_weight_kg": "40.000000000000000000000000009",
        "previous_infill_kg": "25.22",
    })
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["width_mm"] == D(value)
    assert serializer.validated_data["leaf_weight_kg"] == D("40.000000000000000000000000009")


@pytest.mark.parametrize("value", [635.1666, True, "NaN", "Infinity", "-Infinity", "-1", "0"])
def test_glass_preview_rejects_float_nonfinite_and_nonpositive_measures(value):
    serializer = GlassPreviewInputSerializer(data={"system_id": str(uuid4()), "product": {}, "width_mm": value})
    assert not serializer.is_valid()
    assert "width_mm" in serializer.errors


@pytest.mark.parametrize("code,recipe_code", advanced_typologies())
def test_inspector_uses_mobile_recipe_kits_without_fixed_or_passage_overrides(monkeypatch, code, recipe_code):
    node, params = advanced_node(code, recipe_code), advanced_params(code)
    monkeypatch.setattr(hardware.SystemParamsRepository, "load_visible", lambda *args: params)
    monkeypatch.setattr(hardware, "commercial_backend", nullcontext)
    monkeypatch.setattr(hardware, "rows", lambda *args: [{"default_margin_pct": D("0.35"), "waste_factor_pct": D("0.05")}])
    monkeypatch.setattr(hardware.PricingRepository, "cost", lambda *args: D("100"))
    preview = hardware.preview_hardware(uuid4(), {"system_id": uuid4(), "parametric_tree": node.model_dump(mode="json"),
        "width_mm": node.width_mm, "height_mm": node.height_mm, "bay_id": node.id, "color": "WHITE"})
    recipe = next(recipe for cap in params.opening_capabilities for recipe in cap.advanced_recipes if recipe.code == recipe_code)
    moving = [panel for panel in recipe.panels if panel.kind == "MOVING"]
    assert [leaf["leaf_id"] for leaf in preview["leaves"]] == [panel.slot for panel in moving]
    for leaf, panel in zip(preview["leaves"], moving, strict=True):
        selected = next(candidate for candidate in leaf["candidates"] if candidate["selected"])
        assert selected["compatible"] and selected["resolution"]
        allowed = recipe.pass_through_hardware_kit_skus if panel.pass_through else recipe.hardware_kit_skus
        assert selected["sku"] in allowed
        if any(panel.pass_through for panel in recipe.panels):
            assert not leaf["editable"]
