from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from dekopen_engine import (
    FLOAT_GLASS_DENSITY_KG_M3,
    GLASS_WEIGHT_FACTOR_KG_M2_PER_MM,
    build_glass_piece,
    derive_net_glass_thickness,
    exact_glass_area_m2,
)


def test_canonical_glass_density_constants() -> None:
    assert FLOAT_GLASS_DENSITY_KG_M3 == Decimal("2500")
    assert GLASS_WEIGHT_FACTOR_KG_M2_PER_MM == Decimal("2.50")


def test_net_thickness_sums_glass_panes_only() -> None:
    cases = {
        "4-16-4": Decimal("8.00"),
        "4-12-4": Decimal("8.00"),
        "6-12-6": Decimal("12.00"),
        "4-12-3+3": Decimal("10.00"),
        "4-16-4-16-4": Decimal("12.00"),
        "6": Decimal("6.00"),
    }
    for glass_spec, expected_mm in cases.items():
        actual_mm = derive_net_glass_thickness(glass_spec)
        assert actual_mm == expected_mm


def test_unreadable_composition_is_unknown_not_package_thickness() -> None:
    # A spec whose composition cannot be established must not borrow the
    # glazing package thickness — the whole IGU treated as monolithic glass
    # was a fabricated mass several times the real one.
    for glass_spec in ("", "DVH", "x-16-4", "hermetico doble", "4-16-4-16"):
        assert derive_net_glass_thickness(glass_spec) is None
    glass = build_glass_piece(
        bay_id="unknown_composition",
        width_mm=Decimal("680.00"),
        height_mm=Decimal("1310.00"),
        glass_spec="DVH hermetico",
    )
    assert glass.weight_kg is None
    assert glass.thickness_net_mm is None
    assert glass.area_m2 == Decimal("0.8908")


def test_glass_piece_fixture_a() -> None:
    glass = build_glass_piece(
        bay_id="fixture_a",
        width_mm=Decimal("680.00"),
        height_mm=Decimal("1310.00"),
        glass_spec="4-16-4",
    )

    assert exact_glass_area_m2(glass.width_mm, glass.height_mm) == Decimal("0.8908")
    assert glass.area_m2 == Decimal("0.8908")
    assert glass.thickness_net_mm == Decimal("8.00")
    assert glass.weight_kg == Decimal("17.82")


def test_glass_piece_fixture_b() -> None:
    glass = build_glass_piece(
        bay_id="fixture_b",
        width_mm=Decimal("546.00"),
        height_mm=Decimal("1176.00"),
        glass_spec="4-12-4",
    )

    exact_area = exact_glass_area_m2(glass.width_mm, glass.height_mm)
    assert exact_area == Decimal("0.642096")
    assert glass.area_m2 == Decimal("0.6421")
    assert glass.thickness_net_mm == Decimal("8.00")
    assert glass.weight_kg == Decimal("12.84")


def test_weight_uses_exact_area_instead_of_published_area() -> None:
    glass = build_glass_piece(
        bay_id="anti_double_rounding",
        width_mm=Decimal("100.00"),
        height_mm=Decimal("61.90"),
        glass_spec="4-12-3+3",
    )

    assert glass.thickness_net_mm is not None
    incorrectly_double_rounded = (
        glass.area_m2
        * glass.thickness_net_mm
        * GLASS_WEIGHT_FACTOR_KG_M2_PER_MM
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    assert exact_glass_area_m2(glass.width_mm, glass.height_mm) == Decimal("0.00619")
    assert glass.area_m2 == Decimal("0.0062")
    assert glass.weight_kg == Decimal("0.15")
    assert incorrectly_double_rounded == Decimal("0.16")
    assert glass.weight_kg != incorrectly_double_rounded
