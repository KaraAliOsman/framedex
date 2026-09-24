from decimal import Decimal

import pytest

from catalogs.serializers import (
    KIT_OPENING_TYPES,
    KitWriteSerializer,
    ArticleWriteSerializer,
    CatalogHardwareComponentSerializer,
    ProfileSectionSerializer,
    SystemWriteSerializer,
)
from catalogs.service import _contents_json, _jsonb, catalog_revision, require_revision
from authentication.errors import ContractAPIException
from engine_api.repository import (
    UnsupportedCatalogContract,
    _hardware_contents,
    _section,
)


def test_component_round_trip_remains_engine_decimal():
    serializer = CatalogHardwareComponentSerializer(
        data={
            "sku": "COMPONENT",
            "name": 'Component "quoted"',
            "qty": "1.00000000000000000001",
            "unit": "unit",
        }
    )
    assert serializer.is_valid(), serializer.errors
    persisted = _contents_json([serializer.validated_data])
    loaded = _hardware_contents(persisted)
    assert loaded[0].qty == Decimal("1.00000000000000000001")
    assert loaded[0].name == 'Component "quoted"'


def test_catalog_revision_rejects_stale_or_missing_copy_without_rounding():
    original = {"contents": [{"qty": Decimal("1.00000000000000000001")}], "name": "Kit"}
    changed = {"contents": [{"qty": Decimal("1.00000000000000000002")}], "name": "Kit"}
    revision = catalog_revision(original)
    assert revision != catalog_revision(changed)
    assert revision == catalog_revision(dict(reversed(list(original.items()))))
    require_revision({"revision": revision}, f'"{revision}"')
    for token in (None, revision, f'"{catalog_revision(changed)}"'):
        with pytest.raises(ContractAPIException) as error:
            require_revision({"revision": revision}, token)
        assert error.value.status_code == 409


@pytest.mark.parametrize("quantity", [True, "NaN", "Infinity", "0", "-1", {}])
def test_invalid_component_quantity(quantity):
    serializer = CatalogHardwareComponentSerializer(
        data={
            "sku": "C",
            "name": "Component",
            "qty": quantity,
            "unit": "unit",
        }
    )
    assert not serializer.is_valid()


def test_kit_opening_choices_match_current_operable_engine():
    assert set(KIT_OPENING_TYPES) == {
        "TURN",
        "TILT_TURN",
        "SLIDING",
        "AWNING",
        "DOOR",
    }


@pytest.mark.parametrize("opening", ["TURN_LEFT", "SLIDING_2L", "FIXED", "OTHER"])
def test_kit_rejects_noncanonical_opening(opening):
    serializer = KitWriteSerializer(
        data={"opening_type": opening},
        partial=True,
    )
    assert not serializer.is_valid()


@pytest.mark.parametrize("value", ["0", "-1", "100000000.00", "6000.001"])
def test_stock_length_rejects_invalid_engine_or_storage_range(value):
    serializer = ArticleWriteSerializer(
        data={"commercial_length_mm": value},
        partial=True,
    )
    assert not serializer.is_valid()


def test_stock_length_accepts_exact_storage_boundary():
    serializer = ArticleWriteSerializer(
        data={"commercial_length_mm": "99999999.99"},
        partial=True,
    )
    assert serializer.is_valid(), serializer.errors


def test_patch_checks_interval_against_existing_other_endpoint():
    serializer = KitWriteSerializer(
        instance={
            "min_leaf_width_mm": Decimal("400"),
            "max_leaf_width_mm": Decimal("1200"),
        },
        data={"max_leaf_width_mm": "399.99"},
        partial=True,
    )
    assert not serializer.is_valid()


def test_equal_interval_endpoints_are_valid():
    serializer = KitWriteSerializer(
        instance={"min_leaf_width_mm": Decimal("400")},
        data={"max_leaf_width_mm": "400.00"},
        partial=True,
    )
    assert serializer.is_valid(), serializer.errors


@pytest.mark.parametrize("field", ["org_id", "is_global", "is_demo", "id"])
def test_system_rejects_authority_injection(field):
    serializer = SystemWriteSerializer(data={field: "injected"}, partial=True)
    assert not serializer.is_valid()


def test_dimensions_never_round_excess_precision():
    serializer = ArticleWriteSerializer(
        data={"face_width_mm": "60.001"},
        partial=True,
    )
    assert not serializer.is_valid()


def test_new_system_requires_explicit_added_geometry():
    serializer = SystemWriteSerializer(data={})
    assert not serializer.is_valid()
    assert {
        "sliding_glazing_deduction_width_mm",
        "sliding_glazing_deduction_height_mm",
        "door_leaf_side_clearance_mm",
    } <= set(serializer.errors)


def test_component_rejects_untyped_extra_content():
    serializer = CatalogHardwareComponentSerializer(
        data={
            "sku": "C",
            "name": "Component",
            "qty": "1",
            "unit": "unit",
            "price": "1000",
        }
    )
    assert not serializer.is_valid()


SECTION_POLYGON = {
    "source": "POLYGON",
    "polygon": [
        {"x_mm": "0", "y_mm": "0"},
        {"x_mm": "60", "y_mm": "0"},
        {"x_mm": "60", "y_mm": "60"},
        {"x_mm": "0", "y_mm": "60"},
    ],
    "depth_mm": "60.00",
    "axes": [{"name": "GLAZING", "y_mm": "24.00"}],
}


def test_article_section_round_trip_preserves_engine_decimal():
    serializer = ArticleWriteSerializer(data={"section": SECTION_POLYGON}, partial=True)
    assert serializer.is_valid(), serializer.errors
    section = _section(_jsonb(serializer.validated_data["section"]))
    assert section is not None
    assert section.source == "POLYGON"
    assert section.depth_mm == Decimal("60.00")
    assert section.polygon[0].x_mm == Decimal("0")
    assert section.axes[0].y_mm == Decimal("24.00")


@pytest.mark.parametrize(
    "mutated",
    [
        {**SECTION_POLYGON, "polygon": SECTION_POLYGON["polygon"][:2]},
        {**SECTION_POLYGON, "depth_mm": "0"},
        {**SECTION_POLYGON, "source": "TRACING"},
        {k: v for k, v in SECTION_POLYGON.items() if k != "polygon"},
    ],
)
def test_article_section_rejects_noncanonical_shapes(mutated):
    serializer = ProfileSectionSerializer(data=mutated)
    assert not serializer.is_valid()


def test_section_decoder_passes_absent_and_rejects_decoded_json():
    assert _section(None) is None
    with pytest.raises(UnsupportedCatalogContract):
        _section({"source": "POLYGON"})
