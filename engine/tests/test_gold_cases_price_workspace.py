import json
from pathlib import Path
from decimal import Decimal

import pytest

from dekopen_engine.commercial import CommercialLine, PricingError, finish_lines
from dekopen_engine.price_workspace import cascade, comparison, composition, policy
from dekopen_engine.commercial import direct_cost
from engine.tests.workspace_cases import workspace_cases


def test_workspace_12_100_cascade_and_canonical_delta_golden() -> None:
    assert workspace_cases() == json.loads(Path(__file__).with_name('golden_price_workspace.json').read_text())


def test_quantity_three_rounds_once_at_line_not_display_unit() -> None:
    result = finish_lines([CommercialLine(1,3,Decimal(1),Decimal('10.1666666666'))],'CLP',Decimal('.19'))
    assert result.lines == ((1,Decimal(30)),)
    assert result.project_tax == Decimal(6)
    assert result.project_gross == Decimal(36)


def test_material_bar_fraction_is_preserved_in_exact_cost_cascade() -> None:
    from decimal import localcontext
    with localcontext() as context:
        context.prec = 80
        consumed = Decimal(10)/Decimal(3)
    cost = direct_cost([consumed],Decimal('1.44'),Decimal('.08'),Decimal(15000),Decimal(0))
    parts = composition(materials=[('profile',consumed)],waste=Decimal('.08'),area=Decimal('1.44'),
        labor=Decimal(15000),installation=Decimal(0),extras=[],quantity=1)
    reading = cascade(components=parts,cost=cost,list_net=Decimal(30000),net=Decimal(30000),
        tax=Decimal(5700),gross=Decimal(35700))
    assert parts[0][1] == consumed
    with localcontext() as context:
        context.prec = 256
        assert sum((item['amount'] for item in reading['steps']),Decimal(0)) == Decimal(35700)


def test_missing_composition_cannot_be_balanced_silently() -> None:
    with pytest.raises(PricingError,match='cascade_does_not_close'):
        cascade(components=[('glass',Decimal(1))],cost=Decimal(2),list_net=Decimal(3),
                net=Decimal(3),tax=Decimal(1),gross=Decimal(4))


def test_margin_difference_is_percentage_points_and_unknown_is_not_zero() -> None:
    value = comparison({'margin':Decimal('.35'),'net':None},{'margin':Decimal('.20'),'net':Decimal(100)})
    assert value['margin']['delta_pp'] == Decimal('-15')
    assert value['net']['current'] is None and value['net']['delta'] is None


@pytest.mark.parametrize(('cost','net','expected'),[('75','100',False),('75.01','100',True),('39','100',True),('0','0',True)])
def test_band_boundaries_require_owner_when_outside(cost: str,net: str,expected: bool) -> None:
    assert policy(cost=Decimal(cost),net=Decimal(net),minimum=Decimal('.25'),maximum=Decimal('.60'),
                  discount=Decimal(0),discount_limit=Decimal('.10'))['requires_approval'] is expected
