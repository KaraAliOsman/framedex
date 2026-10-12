"""Independent Uw arithmetic and regulatory adversaries; never DEMO certification."""
from datetime import date
from decimal import Decimal as D, localcontext
import json
from pathlib import Path
from typing import Any

import pytest

from dekopen_engine.thermal import ThermalProjectInput, assess_project, calculate_uw
from dekopen_engine.thermal_rules import PERCENTAGES, U_BOUNDS, AIR_MINIMUM, EQUIPMENT_U_MAX, maximum_percentage, orientation_from_azimuth
from engine.tests.thermal_cases import AS_OF, geometry, reports, thermal_cases
from dekopen_engine.models import BayOpeningType


def test_manual_fixed_golden_uses_visible_not_cut_area() -> None:
    assert thermal_cases() == json.loads(Path(__file__).with_name("golden_thermal.json").read_text())
    geo, computation = geometry()
    assert computation.infills[0].width_mm == D("910")
    assert geo.panes[0].visible_width_mm == D("880")
    result = calculate_uw(geo, reports(geo), catalog_fingerprint="unit-test-geometry", as_of=AS_OF)
    assert result["uw"] == D("1.36624")
    assert result["trace"]["ag_m2"] == D("0.7744")
    with localcontext() as context:
        context.prec = 3
        assert calculate_uw(geo, reports(geo), catalog_fingerprint="unit-test-geometry", as_of=AS_OF)["uw"] == D("1.36624")


def test_leaf_and_divider_manual_area_arithmetic() -> None:
    # Sash overlap8: visible1000−2(60+75−8)=746mm.
    # Ag=.746²=.556516; Af=.443484; lg=2.984m.
    # .556516*1.1+.443484*1.5+2.984*.05=1.4265936.
    case=thermal_cases()["additional"]
    assert case["casement"]["uw"] == "1.4265936"
    assert case["casement"]["daylight_mm"] == [["746.00","746.00"]]
    # Half opening500−outer frame60−mullion half40=400mm;
    # height1000−120=880. Ag=2*.4*.88=.704;Af=.296;lg=5.12.
    # .704*1.1+.296*1.5+5.12*.05=1.4744.
    assert D(case["split"]["uw"]) == D("1.4744")
    assert case["split"]["daylight_mm"] == [["400.00","880.00"],["400.00","880.00"]]


@pytest.mark.parametrize("binding", [None,"different-glazing-or-layout"])
def test_performance_never_transfers_to_an_unbound_construction(binding: str | None) -> None:
    geo,_=geometry()
    sources=reports(geo)
    metric=calculate_uw(geo,(*sources[:-1],sources[-1].model_copy(update={"construction_fingerprint":binding})),
        catalog_fingerprint="unit-test-geometry",as_of=AS_OF)
    assert metric["uw"] is not None and metric["air_class"] is None


def test_dividing_or_opening_changes_the_tested_construction() -> None:
    original,_=geometry()
    split,_=geometry(split=True)
    leaf,_=geometry(BayOpeningType.TURN_LEFT)
    assert len({original.construction_fingerprint,split.construction_fingerprint,leaf.construction_fingerprint}) == 3


def test_overlapping_sliding_panes_never_use_the_rectangular_area_method() -> None:
    geo,_=geometry(BayOpeningType.SLIDING_2L)
    metric=calculate_uw(geo,(),catalog_fingerprint="unit-test-geometry",as_of=AS_OF)
    assert metric["uw"] is None and metric["air_class"] is None
    assert any("solapes" in cause for cause in metric["missing"])


@pytest.mark.parametrize("omitted", ["FRAME","GLASS","SPACER"])
def test_each_missing_authority_emits_unknown_without_number(omitted: str) -> None:
    geo, _ = geometry()
    result = calculate_uw(geo, tuple(r for r in reports() if r.kind != omitted), catalog_fingerprint="unit-test-geometry", as_of=AS_OF)
    assert result["state"] == "UNKNOWN" and result["uw"] is None and result["missing"]


@pytest.mark.parametrize("change", [{"synthetic":True}, {"review_state":"PENDING"}, {"review_state":"REVOKED"},
    {"reviewed_by":None}, {"reviewed_at":None}, {"catalog_fingerprint":"old"},
    {"profile_skus":("DIFFERENT",)}, {"max_width_mm":D("999")},
    {"opening_types":("TURN_LEFT",)}, {"valid_until":date(2026,10,10)}, {"report_date":date(2026,10,12)}])
def test_a_review_stamp_cannot_promote_wrong_stale_or_demo_authority(change: dict[str, Any]) -> None:
    geo, _ = geometry()
    source = reports()
    result = calculate_uw(geo, (source[0].model_copy(update=change), *source[1:]), catalog_fingerprint="unit-test-geometry", as_of=AS_OF)
    assert result["uw"] is None


def test_conflicting_reports_never_choose_the_better_value() -> None:
    geo, _=geometry()
    source=reports()
    result=calculate_uw(geo, (*source,source[0].model_copy(update={"id":"another","uf":D("0.5")})), catalog_fingerprint="unit-test-geometry",as_of=AS_OF)
    assert result["uw"] is None


@pytest.mark.parametrize("kwargs", [{"synthetic":True},{"geometry_authoritative":False}])
def test_credible_values_never_certify_a_synthetic_or_unsourced_geometry(kwargs: dict[str, Any]) -> None:
    geo,_=geometry()
    result=calculate_uw(geo,reports(),catalog_fingerprint="unit-test-geometry",as_of=AS_OF,**kwargs)
    assert result["uw"] is None and result["air_class"] is None


def project_input(**changes: Any) -> ThermalProjectInput:
    contexts = changes.pop("positions", [{"position_id":"one","orientation":"E"},{"position_id":"two","orientation":"W"}])
    return ThermalProjectInput.model_validate_json(json.dumps({"zone":"F","zone_source":"Plano oficial revisado por responsable",
        "use":"RESIDENTIAL","walls_m2":{"E":"10","W":"10"},"exposed_wall_area_m2":"20",
        "wall_source":"Plano de la unidad térmica", "envelope_complete":True,"regulatory_scope_confirmed":True,
        "regulatory_method_confirmed":True, "regulatory_calculation_source":"Memoria de prueba; no usar en obra",
        "positions":[{"surface":"WALL", **context} for context in contexts],**changes}))


def position(identity: str, uw: str | None = "2.5", area: str = "2", air: int | None = 3, quantity: int = 1) -> dict[str, Any]:
    return {"position_id":identity,"quantity":quantity,"window_area_m2":D(area),"thermal":{
        "uw":D(uw) if uw else None,"air_class":air,"missing":[]}}


def test_east_and_west_are_distinct_groups_with_worst_u_not_average() -> None:
    inputs=project_input(positions=[{"position_id":"one","orientation":"E"},{"position_id":"two","orientation":"E"},{"position_id":"three","orientation":"W"}])
    report=assess_project(inputs,[position("one",uw="0.6"),position("two",uw="4.0"),position("three",uw="0.6")])
    east,west=report["groups"]
    assert east["largest_uw"] == D("4.0") and east["maximum_percentage"] == D("32")
    assert east["actual_percentage"] == D("40")
    assert west["maximum_percentage"] == D("54") and west["actual_percentage"] == D("20")
    assert report["positions"][0]["verdict"] == "FAIL"
    assert report["positions"][2]["verdict"] == "PASS"


def test_missing_other_window_never_removes_it_from_group() -> None:
    inputs=project_input(positions=[{"position_id":"one","orientation":"E"},{"position_id":"two","orientation":"E"}])
    report=assess_project(inputs,[position("one"),position("two",uw=None)])
    assert report["verdict"] == "UNKNOWN" and report["groups"][0]["largest_uw"] is None


def test_unlocated_window_blocks_a_favourable_facade_verdict() -> None:
    report = assess_project(project_input(positions=[{"position_id":"one","orientation":"E"}]),
                            [position("one"), position("two")])
    assert all(p["verdict"] == "UNKNOWN" for p in report["positions"])


def test_orientation_does_not_silently_declare_a_facade() -> None:
    report = assess_project(project_input(positions=[{"position_id":"one","orientation":"E","surface":None}]), [position("one")])
    assert report["verdict"] == "UNKNOWN" and not report["groups"]


@pytest.mark.parametrize("changes", [{"walls_m2":{},"exposed_wall_area_m2":None,"wall_source":""},
    {"envelope_complete":False},{"regulatory_scope_confirmed":False},{"regulatory_method_confirmed":False},
    {"regulatory_calculation_source":""},{"zone":None}, {"use":None}, {"positions":[]}])
def test_incomplete_envelope_never_passes(changes: dict[str, Any]) -> None:
    report=assess_project(project_input(**changes),[position("one"),position("two")])
    assert report["verdict"] == "UNKNOWN"


def test_ogt_is_derived_below_sixty_percent_and_uses_all_walls() -> None:
    report=assess_project(project_input(exposed_wall_area_m2="11.99"),[position("one"),position("two")])
    assert report["ogt"] is True and report["groups"][0]["orientation"] == "OGT"
    assert report["groups"][0]["actual_percentage"] == D("20")
    assert assess_project(project_input(exposed_wall_area_m2="12"),[position("one")])["ogt"] is False


def test_quantities_air_roof_and_equipment_have_separate_requirements() -> None:
    inputs=project_input(use="HEALTH",zone="H",positions=[{"position_id":"one","surface":"ROOF"}])
    report=assess_project(inputs,[position("one",uw="3.7",air=2)])
    assert report["verdict"] == "FAIL" and len(report["positions"][0]["causes"]) == 2
    assert report["positions"][0]["maximum_uw"] == D("2.4")
    assert assess_project(inputs,[position("one",uw="3.0",air=3)])["verdict"] == "FAIL"
    facade=assess_project(inputs.model_copy(update={"positions":project_input().positions}),[position("one",uw="2.5")])
    assert facade["positions"][0]["maximum_uw"] == D("2.4") and facade["verdict"] == "FAIL"
    report=assess_project(project_input(),[position("one",quantity=3)])
    assert report["groups"][0]["actual_percentage"] == D("60") and report["verdict"] == "FAIL"


def test_every_transcribed_table_cell_and_exact_upper_boundary_matches_fixture() -> None:
    root=Path(__file__).parents[2]/"docs/engineering/thermal"
    fixture=json.loads((root/"oguc-ds15-transcripcion.json").read_text())
    assert fixture["citation"]["pages"] == [6,7,12,15,18]
    assert fixture["u_bounds"] == [str(value) for value in U_BOUNDS]
    for zone, rows in fixture["table3"].items():
        assert tuple(map(tuple,rows)) == PERCENTAGES[zone]
        for row, orientation in zip(rows,("N","E","S","OGT"),strict=True):
            for index,bound in enumerate(U_BOUNDS):
                assert maximum_percentage(zone,orientation,bound) == D(row[index])
                if index < len(U_BOUNDS)-1:
                    assert maximum_percentage(zone,orientation,bound+D("0.00001")) == D(row[index+1])
    assert fixture["air_minimum"] == AIR_MINIMUM
    assert fixture["equipment_u_max"] == {zone:str(value) for zone,value in EQUIPMENT_U_MAX.items()}
    assert maximum_percentage("A","N",D("5.80001")) is None


@pytest.mark.parametrize("angle,expected", [("0","N"),("44.99","N"),("45","E"),("134.99","E"),("135","S"),("225","W"),("315","N"),("359.99","N")])
def test_azimuth_boundaries(angle: str, expected: str) -> None:
    assert orientation_from_azimuth(D(angle)) == expected
