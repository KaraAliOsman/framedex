from decimal import Decimal as D
import json
from pathlib import Path
import pytest
from dekopen_engine.models import CouplerRule
from dekopen_engine.product import evaluate_product
from dekopen_engine.snapshot import canonical_json, evaluation_payload
from dekopen_engine.commercial import assembly_sale_adjustment
from engine.tests.catalog import demo_60_params
from engine.tests.assembly_cases import assembly_cases, bow_model, joint_article


def test_reviewed_assembly_golden() -> None:
    frozen=json.loads(Path(__file__).with_name('golden_assemblies.json').read_text())
    assert assembly_cases()==frozen
    assert frozen['bow_22_5']['measures']['developed_width_mm']=='2400.00'
    assert frozen['bow_espaciado']['measures']['developed_width_mm']=='2448.00'
    assert frozen['esquina_90']['status']=='VALID'


@pytest.mark.parametrize('angle', ['0','10','15','22.5','30','45','60','-22.5'])
def test_angular_authority_boundary(angle: str) -> None:
    article=joint_article()
    result=evaluate_product(bow_model(angle),demo_60_params(),coupler_articles={article.sku:article})
    assert not any(issue.code=='coupler_angle_incompatible' for issue in result.issues)


def test_angular_error_names_each_joint_and_field() -> None:
    article=joint_article()
    result=evaluate_product(bow_model('89'),demo_60_params(),coupler_articles={article.sku:article})
    errors=[issue for issue in result.issues if issue.code=='coupler_angle_incompatible']
    assert {issue.target for issue in errors}=={'coupling:c1','coupling:c2'}
    assert all(issue.params['field']=='coupler_profile_sku' and issue.params['max_angle_deg']=='60' and issue.params['source'] for issue in errors)
    assert result.status.value=='INVALID'


def test_absent_joint_authority_preserves_historical_bytes() -> None:
    current=joint_article()
    old=current.model_copy(update={'coupling_rule':None})
    value=old.model_dump()
    assert 'coupling_rule' not in value
    old_reloaded=type(old).model_validate(value)
    assert canonical_json(old.model_dump())==canonical_json(old_reloaded.model_dump())
    result=evaluate_product(bow_model(),demo_60_params(),coupler_articles={old.sku:old})
    assert 'measures' not in evaluation_payload(result)


@pytest.mark.parametrize('minimum,maximum,width',[('30','22.5','0'),('0','91','0'),('-1','60','0'),('0','60','-1')])
def test_catalog_rejects_invalid_bounds(minimum: str, maximum: str, width: str) -> None:
    with pytest.raises(ValueError):
        CouplerRule(min_angle_deg=D(minimum),max_angle_deg=D(maximum),development_mm=D(width),source='Ficha técnica')


def test_sale_components_close_without_proportional_distribution() -> None:
    assert assembly_sale_adjustment(D('10001.3'),[D('2500.5'),D('5000.4'),D('1500.2')],'CLP')==D('1000')
    assert assembly_sale_adjustment(D('100.01'),[D('20.02'),D('30.03')],'USD')==D('49.96')


def test_developed_joints_follow_sourced_inline_and_stacked_gaps() -> None:
    from dekopen_engine.assembly_measures import developed_layout
    from dekopen_engine.product import ProductModel
    article = joint_article(width='24')
    product = bow_model()
    result = evaluate_product(product, demo_60_params(), coupler_articles={article.sku: article})
    layout = developed_layout(product.assembly, result.measures)
    assert [joint.x_mm for joint in layout.column_joints] == [D('612'), D('1836')]
    raw = product.model_dump(mode='json')
    raw['assembly']['modules'] = raw['assembly']['modules'][:2]
    raw['assembly']['modules'][1]['width_mm'] = '600'
    raw['assembly']['couplings'] = [{**raw['assembly']['couplings'][0], 'kind': 'STACKED',
                                    'angle_deg': '0', 'edges': ['top', 'bottom']}]
    stacked = ProductModel.model_validate_json(json.dumps(raw))
    evaluation = evaluate_product(stacked, demo_60_params(), coupler_articles={article.sku: article})
    assert evaluation.measures is not None
    assert evaluation.measures.height_mm == D('2424')
    layout = developed_layout(stacked.assembly, evaluation.measures)
    assert layout.members[1].sill_mm == D('1224')
    assert layout.stack_joints[0].y_mm == D('1212')
