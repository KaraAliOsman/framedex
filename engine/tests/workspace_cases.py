"""P07 resolved DEMO authorities: 12/100 positions, quantity three and replay."""

from decimal import Decimal, localcontext
from collections.abc import Mapping
from typing import Any

from dekopen_engine.commercial import CommercialLine, direct_cost, finish_lines, unit_price, PricingMode
from dekopen_engine.price_workspace import (DRIVERS, cascade, composition, explain,
    policy, undiscounted_lines)

D = Decimal


def project_case(count: int, currency: str) -> dict[str,Any]:
    with localcontext() as ctx:
        ctx.prec = 256
        components: list[tuple[str,Decimal]] = []
        lines: list[CommercialLine] = []
        for index in range(1,count+1):
            # Declared synthetic cost rates, not production authorities.
            with localcontext() as fraction_context:
                fraction_context.prec = 80
                profile = D(12345)*D(4500+index)/D(6000)
            materials = [('profile',profile),
                         ('glass',D('8450.2500')*D('1.4400')),('hardware',D('2500.0000'))]
            area, waste, labor = D('1.44'), D('.08'), D('15000')
            cost = direct_cost([amount for _,amount in materials],area,waste,labor,D(0))
            quantity = 3 if index == 1 else 1
            components.extend(composition(materials=materials,waste=waste,area=area,labor=labor,
                installation=D(0),extras=[],quantity=quantity))
            price = unit_price(PricingMode.COST_PLUS_MARGIN,cost=cost,margin=D('.35'),area=area,width=D(1200),height=D(1200))
            lines.append(CommercialLine(index,quantity,cost,price,D('.05')))
        output = finish_lines(lines,currency,D('.19'))
        reading = cascade(components=components,cost=sum((line.unit_cost*line.quantity for line in lines),D(0)),
            list_net=undiscounted_lines([(line.exact_unit_price,line.quantity) for line in lines],currency),
            net=output.project_net,tax=output.project_tax,gross=output.project_gross,currency=currency,tax_rate=D('.19'))
        assert sum((step['amount'] for step in reading['steps']),D(0)) == output.project_gross
        return {'count':count,'currency':currency,'line_one_quantity':lines[0].quantity,
                'line_one_net':str(output.lines[0][1]),
                'cascade':{key:str(value) for key,value in reading.items() if key not in {'steps','traces'}},
                'steps':[{key:str(value) for key,value in step.items()} for step in reading['steps']]}


def replay_case() -> dict[str,Any]:
    before = {key:D(0) for key in DRIVERS}
    before.update(quantity=D(3),dimensions=D('1.44'),glass=D(8000),hardware=D(2500),
                  cost_list=D(12000),fx=D(1),margin=D('.35'),discount=D(0),tax=D('.19'))
    after = {**before,'quantity':D(4),'dimensions':D('1.65'),'glass':D(8500),
             'hardware':D(3200),'cost_list':D(12500),'fx':D('1.05'),'margin':D('.32'),'discount':D('.05')}
    def reprice(state: Mapping[str,Any]) -> dict[str,Decimal]:
        with localcontext() as ctx:
            ctx.prec = 80
            cost = (state['cost_list']+state['glass']*state['dimensions']+state['hardware'])*state['fx']
            price = unit_price(PricingMode.COST_PLUS_MARGIN,cost=cost,margin=state['margin'],
                area=state['dimensions'],width=D(1200),height=D(1200))
            result = finish_lines([CommercialLine(1,int(state['quantity']),cost,price,state['discount'])],'CLP',state['tax'])
            return {'net':result.project_net,'tax':result.project_tax,'total':result.project_gross,'position_1':result.lines[0][1]}
    result = explain(before,after,reprice)
    return {'order':result['order'],'delta':{key:str(value) for key,value in result['delta'].items()},
            'contributions':[{'driver':item['driver'],'delta':{key:str(value) for key,value in item['delta'].items()}}
                             for item in result['contributions']]}


def workspace_cases() -> dict[str,Any]:
    return {'projects':[project_case(count,currency) for count in (12,100) for currency in ('CLP','USD')],
            'replay':replay_case(),
            'approval':policy(cost=D(80),net=D(100),minimum=D('.25'),maximum=D('.60'),discount=D(0),discount_limit=D('.10')) | {'margin':'0.2'}}
