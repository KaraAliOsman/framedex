"""Extras carry quantities, cuts, sourced prices and historical compatibility."""

from decimal import Decimal as D
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from dekopen_engine.extra_models import ExtraAuthority, ExtraContext, ExtraSelection
from dekopen_engine.extras import partition_price, position_lines, project_lines, suggestions, target_services, glass_bar_lines
from dekopen_engine.geometry import calculate_geometry
from dekopen_engine.cutting import pieces_from_result
from engine.tests.extra_cases import extra_cases, extra_context, installation
from engine.tests.finish_cases import finish_context


def test_reviewed_accessory_goldens() -> None:
    frozen = json.loads(Path(__file__).with_name("golden_extras.json").read_text(encoding="utf-8"))
    assert extra_cases() == frozen
    cuts = [row for row in frozen["geometric-bom"]["profile_cuts"] if row.get("extra_code") == "SILL"]
    assert [D(row["length_mm"]) for row in cuts] == [D(1560)]
    assert D(frozen["project-perimeter"][0]["quantity"]) == D("11.6")
    assert D(frozen["project-perimeter"][0]["total_price"]) == D(17400)
    detail = frozen["exact-partition"]
    assert D(detail["base_net"])+sum((D(row["net"]) for row in detail["sublines"]),D(0)) == D(210001)
    assert len(frozen["extra-members"]) == 3


def test_extension_is_a_real_cut_piece_and_synthetic_trace() -> None:
    params,node = extra_context()
    result = calculate_geometry(node.model_copy(update={"extras":[ExtraSelection(code="FRAME_EXTENSION",sides=["LEFT","TOP"])]}),params,finish="WHITE")
    pieces = pieces_from_result(result,color="WHITE",reinforcement_skus={})
    assert sorted(piece.length_mm for piece in pieces if "EXTRA-FRAME_EXTENSION" in piece.workshop_sku) == [D(1400),D(1500)]
    assert all(fact.synthetic for fact in result.extras)
    assert "total_cost" not in result.model_dump_json() and "cost_rate" not in result.model_dump_json()


def test_saved_extras_roundtrip_preserves_exact_quantities_and_money() -> None:
    from dekopen_engine.extra_models import ExtraLine
    from dekopen_engine.models import EngineResult
    from dekopen_engine.extras import price_facts

    params, node = extra_context()
    result = calculate_geometry(node.model_copy(update={"extras": [ExtraSelection(code="SILL", overhang_left_mm=D(30), overhang_right_mm=D(30))]}), params, finish="WHITE")
    restored = EngineResult.model_validate_json(result.model_dump_json())
    assert restored == result and restored.extras[0].quantity == D("1.56")
    line = price_facts(params.extra_authority, result.extras)[0]
    assert ExtraLine.model_validate_json(line.model_dump_json()) == line
    raw = line.model_dump(mode="json")
    raw["quantity"] = 1.56
    with pytest.raises(ValidationError, match="exactos"):
        ExtraLine.model_validate_json(json.dumps(raw))


def test_suggestions_have_a_cause_and_discard_is_durable() -> None:
    params,node = extra_context()
    assert params.extra_authority
    result = calculate_geometry(node,params,finish="WHITE")
    proposal = next(item for item in result.extra_suggestions if item.selection.code == "SILL")
    assert proposal.cause and proposal.source and proposal.selection.overhang_left_mm == D(30)
    discarded = calculate_geometry(node.model_copy(update={"extras":[proposal.selection.model_copy(update={"decision":"DISMISS"})]}),params,finish="WHITE")
    assert discarded.extras == []
    assert "SILL" not in {item.selection.code for item in discarded.extra_suggestions}
    gap = suggestions(params.extra_authority,[],width=D(1500),height=D(1400),leaves=result.opening_leaves,
        context=ExtraContext(opening_width_mm=D(1560),opening_height_mm=D(1400)))
    assert "60 mm" in next(item.cause for item in gap if item.selection.code == "FRAME_EXTENSION")


def test_no_guessed_extra_missing_authority_or_incompatible_screen() -> None:
    params,node = extra_context()
    with pytest.raises(ValueError,match="Sin dato"):
        calculate_geometry(node.model_copy(update={"extras":[ExtraSelection(code="UNKNOWN")]}),params,finish="WHITE")
    with pytest.raises(ValueError,match="compatible"):
        calculate_geometry(node.model_copy(update={"extras":[ExtraSelection(code="SCREEN_SLIDE")]}),params,finish="WHITE")


def test_screen_dimensions_and_special_handle_replace_base_once() -> None:
    params,node = extra_context(opening="TURN_LEFT")
    node = node.model_copy(update={"width_mm":D(900),"height_mm":D(850)})
    base = calculate_geometry(node,params,finish="WHITE")
    result = calculate_geometry(node.model_copy(update={"extras":[ExtraSelection(code="SCREEN_ROLL"),ExtraSelection(code="SPECIAL_HANDLE")]}),params,finish="WHITE")
    leaf = base.opening_leaves[0]
    screen = next(fact for fact in result.extras if fact.code == "SCREEN_ROLL")
    assert (screen.width_mm,screen.height_mm) == (leaf.width_mm,leaf.height_mm)
    assert all(component.category != "HANDLE" for kit in result.hardware_items for component in kit.contents)
    assert sum(fitting.qty for fitting in result.fittings if fitting.extra_code == "SPECIAL_HANDLE") == 1


@pytest.mark.parametrize("basis,expected",[("AREA","4.2"),("PERIMETER","11.6"),("PER_POSITION","2"),("FIXED","1")])
def test_project_rules_use_real_position_quantity(basis: str,expected: str) -> None:
    authority = ExtraAuthority(schema_version=1,definitions=[installation(basis=basis)],source="Ensayo")
    assert project_lines(authority,[ExtraSelection(code="INSTALL")],[(D(1500),D(1400),2)])[0].quantity == D(expected)


@pytest.mark.parametrize("currency,total",[("CLP","1"),("USD","1.01"),("CLP","9007199254740993")])
def test_currency_remainders_keep_exact_total(currency: str,total: str) -> None:
    definition = installation(scope="POSITION")
    rows = position_lines(ExtraAuthority(schema_version=1,definitions=[definition],source="Ensayo"),[ExtraSelection(code="INSTALL")],
        width=D(1),height=D(1),leaves=[])
    detail = partition_price(D(total),D(1),[(rows[0],D("0.123456789123456789123456789"))],quantity=3,currency=currency)
    assert D(detail["base_net"])+sum((D(str(row["net"])) for row in detail["sublines"]),D(0)) == D(total)


def test_duplicate_installation_and_float_authority_are_refused() -> None:
    first = installation()
    second = first.model_copy(update={"code":"OTHER"})
    with pytest.raises(ValueError,match="una sola"):
        project_lines(ExtraAuthority(schema_version=1,definitions=[first,second],source="Ensayo"),
            [ExtraSelection(code="INSTALL"),ExtraSelection(code="OTHER")],[(D(1500),D(1400),1)])
    raw = first.model_dump(mode="json")
    raw["cost_rate"] = 0.1
    with pytest.raises(ValidationError,match="exactos"):
        type(first).model_validate_json(json.dumps(raw))


def test_legacy_result_and_tree_keep_field_presence() -> None:
    params,node = finish_context()
    result = calculate_geometry(node,params,finish="WHITE")
    assert "extras" not in result.model_dump() and "extra_suggestions" not in result.model_dump()
    assert "extras" not in node.model_dump() and "extra_context" not in node.model_dump()


def test_explicit_empty_sides_cannot_restore_hidden_defaults() -> None:
    params,node = extra_context()
    with pytest.raises(ValueError,match='al menos un lado'):
        calculate_geometry(node.model_copy(update={'extras':[ExtraSelection(code='FRAME_EXTENSION',sides=[])]}),params,finish='WHITE')
    defaults = calculate_geometry(node.model_copy(update={'extras':[ExtraSelection(code='FRAME_EXTENSION')]}),params,finish='WHITE')
    assert defaults.extras[0].quantity == D('2.8')


@pytest.mark.parametrize('currency',['CLP','USD'])
def test_project_target_margin_includes_service_cost_and_rounding(currency: str) -> None:
    definition = installation().model_copy(update={'currency':currency})
    authority = ExtraAuthority(schema_version=1,definitions=[definition],source='Ensayo')
    services = project_lines(authority,[ExtraSelection(code='INSTALL')],[(D(1500),D(1400),2)])
    result,rows = target_services([(1,D(100000)),(2,D(200000))],services,D('0.25'),currency,D('0.19'),[])
    assert result.project_net == D('415467' if currency == 'CLP' else '415466.67')
    assert result.extras_net == sum((D(str(row['amount'])) for row in rows),D(0))
    assert sum((price for _,price in result.lines),D(0))+result.extras_net == result.project_net
    for row in rows:
        assert D(str(row['quantity']))*D(str(row['unit_price']))+D(str(row['rounding'])) == D(str(row['amount']))


def test_glass_grid_keeps_d02_authority_and_costs_once() -> None:
    from dekopen_engine.glass_composition import GlassBilling, GlassProcessing, parse_glass_notation, GlassProduct, price_glass
    product = GlassProduct(name='Termopanel con palillaje',composition=parse_glass_notation('4-16-4'),source='Proveedor · ensayo',
        synthetic=True,billing=GlassBilling(bars_per_m_sku='BARS',bars_per_crossing_sku='CROSS',source='Lista de ensayos'))
    priced = price_glass(product=product,sku='IGU',width_mm=D(900),height_mm=D(800),rates={'IGU':D(10000),'BARS':D(1000),'CROSS':D(500)},
        processing=GlassProcessing(bars_vertical=2,bars_horizontal=1))
    lines = glass_bar_lines(priced,product,bay_id='vidrio',currency='CLP',waste=D('0.08'),margin=D('0.25'))
    assert [item.quantity for item in lines] == [D('2.5'),D(2)]
    assert sum((item.total_cost for item in lines),D(0)) == D(3500)*D('1.08')
    assert all(item.synthetic and item.source == 'Lista de ensayos' for item in lines)


@pytest.mark.parametrize('shape', ['CONTOUR', 'FRAMELESS'])
def test_shape_without_extra_authority_cannot_silently_drop_selection(shape: str) -> None:
    from dekopen_engine.contour import Contour
    from dekopen_engine.models import PlanPoint
    from dekopen_engine.product import CoupledAssembly, FramelessSpec, ProductModel, ProductModule, ProductStatus, evaluate_product

    params, node = extra_context()
    module = ProductModule(id='m1', width_mm=D(1500), height_mm=D(1400),
                           tree=node.model_copy(update={'extras': [ExtraSelection(code='SILL')]}))
    if shape == 'CONTOUR':
        module = module.model_copy(update={'contour': Contour(vertices=[
            PlanPoint(x_mm=D(0),y_mm=D(0)), PlanPoint(x_mm=D(1500),y_mm=D(0)),
            PlanPoint(x_mm=D(1500),y_mm=D(1400)), PlanPoint(x_mm=D(0),y_mm=D(1400))], bulges=[D(0)]*4)})
    else:
        module = module.model_copy(update={'frameless': FramelessSpec()})
    product = ProductModel(version='product-v2',assembly=CoupledAssembly(modules=[module]))
    result = evaluate_product(product,params,coupler_articles={},finish='WHITE')
    assert result.status is ProductStatus.MANUFACTURING_INCOMPLETE
    assert any('autoridad de accesorios' in str(issue.params) for issue in result.issues)
    assert result.bom is None
