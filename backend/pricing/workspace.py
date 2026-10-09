"""Project price projection, frozen replay and requester attention."""

from copy import deepcopy
from decimal import Decimal, localcontext

from pydantic import TypeAdapter

from dekopen_engine.commercial import (CommercialLine, PricingError, PricingMode,
    finish_lines, target_project, quantize_currency)
from dekopen_engine.price_workspace import (DRIVERS, cascade, comparison, composition,
    explain, gross_margin, money_trace, policy, undiscounted_lines)
from dekopen_engine.extra_models import ExtraAuthority, ExtraPolicy, ExtraSelection, ExtraLine
from dekopen_engine.extras import project_lines, service_price, target_services
from pricing.repository import rows, json_text
from pricing.resolved import financial_bundle, FrozenPricingRepository, frozen_copy

D = Decimal
ZERO = D(0)
CAUSES = {
    'below_minimum':'El margen queda bajo el mínimo de la organización.',
    'above_maximum':'El margen supera el máximo de la organización.',
    'undefined_margin':'El neto no permite determinar el margen.',
    'discount_limit':'El descuento supera el umbral de aprobación.',
}
GLASS_KEYS = {'glass_article_sku','glass_product','glass_processing','glass_thickness_mm','glass_spec'}
HARDWARE_KEYS = {'opening','opening_type','hardware_set_sku','hardware_selection','handle_height_mm','door_handedness','hinge_side'}
DIMENSION_KEYS = {'width_mm','height_mm','nominal_width_mm','nominal_height_mm',
    'offset_mm','position_mm','arc_rise_mm','top_left_offset_mm','top_right_offset_mm',
    'rise_mm','split_mm','split_offset_mm','sill_height_mm','fixed_mm','x_mm','y_mm','bulges'}


def _split_tree(value, selected):
    if isinstance(value,list):
        return [_split_tree(item,selected) for item in value]
    if not isinstance(value,dict):
        return None
    return {key:deepcopy(item) if key in selected else _split_tree(item,selected)
            for key,item in value.items() if key in selected or isinstance(item,(dict,list))}


def _without_tree(value):
    if isinstance(value,list):
        return [_without_tree(item) for item in value]
    if not isinstance(value,dict):
        return deepcopy(value)
    return {key:_without_tree(item) for key,item in value.items() if key not in GLASS_KEYS | HARDWARE_KEYS | DIMENSION_KEYS}


def _overlay(base, overlay):
    if isinstance(base,list) and isinstance(overlay,list):
        return [_overlay(item,overlay[index] if index < len(overlay) else None) for index,item in enumerate(base)]
    if not isinstance(base,dict) or not isinstance(overlay,dict):
        return deepcopy(base)
    result = deepcopy(base)
    for key,item in overlay.items():
        if key in GLASS_KEYS | HARDWARE_KEYS | DIMENSION_KEYS:
            result[key] = deepcopy(item)
        elif key in base:
            result[key] = _overlay(base[key],item)
    return result


def replay_state(replay):
    positions = replay['positions']
    return {
        'quantity':{str(p['position_index']):p['quantity'] for p in positions},
        'dimensions':{str(p['position_index']):{**{key:p[key] for key in ('width_mm','height_mm')},
            'tree':_split_tree(p['parametric_tree'],DIMENSION_KEYS)} for p in positions},
        'glass':{str(p['position_index']):_split_tree(p['parametric_tree'],GLASS_KEYS) for p in positions},
        'hardware':{str(p['position_index']):_split_tree(p['parametric_tree'],HARDWARE_KEYS) for p in positions},
        'design':{'positions':{str(p['position_index']):{**p,'parametric_tree':_without_tree(p['parametric_tree'])} for p in positions},
                  'technical':replay['technical']},
        'cost_list':{'costs':replay['financial']['costs'],'demo':replay['financial']['demo'],
                     'rules':replay['rules'],'organization_currency':replay['organization_currency']},
        'fx':{'rows':replay['financial']['fx'],'id':replay['request'].get('fx_snapshot_id'),'currency':replay['request']['currency']},
        'commercial_list':{'configurations':replay['financial']['configurations'],'matrix':replay['financial']['matrix'],
                           'mode':replay['request']['pricing_mode'],'context':replay['request']['context_code']},
        'margin':replay['request']['target_margin'],
        'discount':replay['request']['discount_pct'],
        'segment':replay['request']['segment'],
        'services':{'policy':replay['extra_policy'],'selections':replay['selections'],'extras':replay['request'].get('extras',[])},
        'tax':replay['rules']['tax_rate_pct'],
    }


def _reprice(org_id, state, before, after):
    """All resolvers below read frozen objects; this callback has no I/O."""
    from pricing.service import position_cost, configured_unit_price
    from projects.extras import converted_lines
    rules = {key:D(str(value)) if key.endswith('_pct') or key.endswith('_m2') else value
             for key,value in state['cost_list']['rules'].items()}
    repo = FrozenPricingRepository(org_id,state['fx']['currency'],
        {**state['cost_list'],'fx':state['fx']['rows'],**state['commercial_list']},
        state['design']['technical'],state['fx']['id'])
    rules.update({key:repo.convert(rules[key],state['cost_list']['organization_currency'])
                  for key in ('labor_rate_per_m2','installation_rate_per_m2')})
    positions = []
    for index,quantity in state['quantity'].items():
        source = (state['design']['positions'].get(index) or after['design']['positions'].get(index)
                  or before['design']['positions'].get(index))
        if source is None:
            raise PricingError('incomplete_repricing_evidence')
        position = deepcopy(source)
        dimensions = state['dimensions'].get(index) or after['dimensions'].get(index) or before['dimensions'][index]
        position.update({key:value for key,value in dimensions.items() if key != 'tree'})
        position['parametric_tree'] = _overlay(position['parametric_tree'],dimensions.get('tree'))
        position['width_mm'],position['height_mm'] = D(str(position['width_mm'])),D(str(position['height_mm']))
        position['quantity'] = int(quantity)
        for key in ('glass','hardware'):
            overlay = state[key].get(index) or after[key].get(index) or before[key].get(index)
            position['parametric_tree'] = _overlay(position['parametric_tree'],overlay)
        positions.append(position)
    extra_policy = ExtraPolicy.model_validate_json(json_text(state['services']['policy']['policy']))
    authority = ExtraAuthority(schema_version=1,definitions=[item for item in extra_policy.services if item.scope == 'PROJECT'],source='Organización')
    selections = TypeAdapter(list[ExtraSelection]).validate_json(json_text(state['services']['selections']))
    services = converted_lines(repo,project_lines(authority,selections,
        [(p['width_mm'],p['height_mm'],p['quantity']) for p in positions])) if selections else []
    rules['explicit_project_installation'] = any(item.installation for item in services)
    mode = PricingMode(state['commercial_list']['mode'])
    costs, lines = [], []
    with localcontext() as context:
        context.prec = 256
        for p in positions:
            cost,area,result,formation = position_cost(repo,p,rules)
            costs.append((p['position_index'],cost*p['quantity']))
            if mode != PricingMode.TARGET_GROSS_MARGIN_PROJECT:
                price = configured_unit_price(repo,mode,p,cost=cost,area=area,result=result,
                    margin=D(str(state['margin'])),context_code=state['commercial_list']['context'],
                    extras=[ExtraLine.model_validate_json(json_text(item)) for item in formation['extra_lines']])
                lines.append(CommercialLine(p['position_index'],p['quantity'],cost,price,D(str(state['discount']))))
        extras = [D(str(item['amount'])) for item in state['services']['extras']]
        if mode == PricingMode.TARGET_GROSS_MARGIN_PROJECT and services:
            output,_ = target_services(costs,services,D(str(state['margin'])),repo.currency,D(str(state['tax'])),extras)
        elif mode == PricingMode.TARGET_GROSS_MARGIN_PROJECT:
            output = target_project(costs,D(str(state['margin'])),repo.currency,D(str(state['tax'])),extras)
        else:
            output = finish_lines(lines,repo.currency,D(str(state['tax'])),
                extras+[D(service_price(item,repo.currency)['amount']) for item in services])
    return {'net':output.project_net,'tax':output.project_tax,'total':output.project_gross,
            **{f'position_{index}':net for index,net in output.lines}}


def workspace_evidence(repo,project,positions,request,rules,technical,cost_lines,
                       priced_lines,output,line_detail,services,extra_policy):
    from projects.extras import selections_for
    from pricing.service import decoded
    financial = financial_bundle(repo)
    organization_currency = next(a['organization_currency'] for a in repo.authorities if 'organization_currency' in a)
    replay_positions = [{**{key:p[key] for key in ('id','position_index','quantity','system_id','typology',
        'width_mm','height_mm','color_interior','color_exterior','location_tag')},
        'parametric_tree':decoded(p['parametric_tree'])} for p in positions]
    replay = frozen_copy({'positions':replay_positions,'technical':repo.technical,'financial':financial,
        'rules':rules,'request':{key:value for key,value in request.items() if not key.startswith('_')},
        'extra_policy':extra_policy,'organization_currency':organization_currency,
        'selections':[item.model_dump(mode='json') for item in selections_for(repo.org_id,project['id'],project['current_revision'])]})
    previous = rows("SELECT * FROM public.pricing_operations WHERE org_id=%s AND project_id=%s AND state='APPLIED' "
                    'ORDER BY approved_at DESC,id DESC LIMIT 1',[repo.org_id,project['id']])
    current = previous[0] if previous else None
    current_output = decoded(current['result']) if current else {}
    current_snapshot = decoded(current['input_snapshot']) if current else {}
    comparable = bool(current and decoded(current['request'])['currency'] == request['currency'])
    with localcontext() as context:
        context.prec = 256
        service_cost = sum((item.total_cost for item in services),ZERO)
        total_cost = sum((cost for _,cost in cost_lines),ZERO)+service_cost
        min_margin = rules.get('minimum_margin_pct',D('.25'))
        max_margin = rules.get('maximum_margin_pct',D('.60'))
        limit = rules.get('discount_approval_pct',D('.10'))
        decision = policy(cost=total_cost,net=output.project_net,minimum=min_margin,maximum=max_margin,
                          discount=request['discount_pct'],discount_limit=limit)
        decision['cause_text'] = [CAUSES[cause] for cause in decision['causes']]
        service_net = sum((D(service_price(item,request['currency'])['amount']) for item in services),ZERO)
        manual_extras = sum((D(str(item['amount'])) for item in request.get('extras') or []),ZERO)
        list_net = (output.project_net-manual_extras if request['pricing_mode'] == PricingMode.TARGET_GROSS_MARGIN_PROJECT.value
                    else undiscounted_lines([(line.exact_unit_price,line.quantity) for line in priced_lines],request['currency'])+service_net)
        cost_map = dict(cost_lines)
        details = {item['position_index']:item for item in line_detail}
        old_lines = {int(index):D(str(net)) for index,net in current_output.get('lines',[])} if comparable else {}
        all_components, line_readings = [], []
        for p,tech in zip(positions,technical,strict=True):
            index,quantity = p['position_index'],p['quantity']
            components = composition(materials=[(item['kind'].lower(),D(item['cost'])) for item in tech['composition'] if item['kind'] != 'EXTRA'],
                waste=D(tech['waste_pct']),area=D(tech['area_m2']),labor=D(tech['labor_rate_per_m2']),
                installation=D(tech['installation_rate_per_m2']),
                extras=[('extra',D(item['cost'])) for item in tech['composition'] if item['kind'] == 'EXTRA'],quantity=quantity)
            net = dict(output.lines)[index]
            unit_price = D(details[index]['unit_price'])
            undiscounted = net if request['pricing_mode'] == PricingMode.TARGET_GROSS_MARGIN_PROJECT.value else quantize_currency(next(line.exact_unit_price for line in priced_lines if line.position_index == index)*quantity,request['currency'])
            reading = cascade(components=components,cost=cost_map[index],list_net=undiscounted,net=net,tax=ZERO,gross=net,currency=request['currency'])
            currency = request['currency']
            for key,formula,inputs in (
                ('waste','Costo material × merma × cantidad',
                    [('Costo material por unidad',D(tech['materials_cost']),currency),('Merma',D(tech['waste_pct']),'fracción')]),
                ('labor','Área por unidad × tarifa de proceso × cantidad',
                    [('Área por unidad',D(tech['area_m2']),'m²'),('Tarifa por m²',D(tech['labor_rate_per_m2']),currency)]),
                ('installation','Área por unidad × tarifa de instalación × cantidad',
                    [('Área por unidad',D(tech['area_m2']),'m²'),('Tarifa por m²',D(tech['installation_rate_per_m2']),currency)]),
            ):
                amount = next(step['amount'] for step in reading['steps'] if step['key'] == key)
                reading['traces'][key] = money_trace(formula,amount,inputs+[('Cantidad',D(quantity),'unidad')])
            exact_price = (net / D(quantity) if request['pricing_mode'] == PricingMode.TARGET_GROSS_MARGIN_PROJECT.value
                else next(line.exact_unit_price for line in priced_lines if line.position_index == index))
            line_traces = {
                'unit_cost':money_trace('Costo de la posición ÷ cantidad',D(tech['unit_cost_exact']),
                    [('Costo de la posición',cost_map[index],currency),('Cantidad',D(quantity),'unidad')]),
                'unit_price':money_trace('Precio unitario calculado; lectura a cuatro decimales con mitades alejándose de cero',unit_price,
                    [('Precio unitario exacto',exact_price,currency)]),
                'line_net':money_trace('Precio unitario exacto × cantidad × (1 − descuento); mitades alejándose de cero por línea',net,
                    [('Precio unitario exacto',exact_price,currency),('Cantidad',D(quantity),'unidad'),
                     ('Descuento',ZERO if request['pricing_mode'] == PricingMode.TARGET_GROSS_MARGIN_PROJECT.value else request['discount_pct'],'fracción')]),
                'list_net':money_trace('Precio unitario exacto × cantidad; mitades alejándose de cero por línea',undiscounted,
                    [('Precio unitario exacto',exact_price,currency),('Cantidad',D(quantity),'unidad')]),
            }
            line_traces['unit_price_sale'] = deepcopy(line_traces['unit_price'])
            if tech.get('price_trace'):
                line_traces['unit_price'] = deepcopy(tech['price_trace'])
            if reading['traces'].get('margin'):
                line_traces['margin'] = deepcopy(reading['traces']['margin'])
            reading['traces']['list_net'] = line_traces['list_net']
            if index in old_lines:
                line_traces['delta'] = money_trace('Neto propuesto de la posición − neto aplicado',net-old_lines[index],
                    [('Neto propuesto',net,currency),('Neto aplicado',old_lines[index],currency)])
            all_components.extend(components)
            line_readings.append({'position_index':index,'location':p.get('location_tag') or '',
                'typology':p['typology'],'width_mm':str(p['width_mm']),'height_mm':str(p['height_mm']),
                'quantity':quantity,'unit_cost':D(tech['unit_cost_exact']),'unit_price':unit_price,
                'line_net':net,'margin':reading['margin'],'delta':net-old_lines[index] if index in old_lines else None,
                'cascade':reading,'traces':line_traces,'discount_pct':request['discount_pct'],
                'composition':tech['composition'],'warnings':[]})
        all_components.append(('services',service_cost))
        reading = cascade(components=all_components,cost=total_cost,list_net=list_net,net=output.project_net,
                          tax=output.project_tax,gross=output.project_gross,extras_net=manual_extras,currency=request['currency'],tax_rate=rules['tax_rate_pct'])
        reading['traces']['list_net'] = money_trace('Suma de precios de lista redondeados por posición y servicios',list_net,
            [(f"Posición {item['position_index']}",D(item['cascade']['list_net']),request['currency']) for item in line_readings]
            + [('Servicios del proyecto',service_net,request['currency'])])
        old_cost = current_output.get('workspace',{}).get('cascade',{}).get('cost')
        before = {key:D(str(current_output[field])) if comparable and field in current_output else None
                  for key,field in (('net','project_net'),('tax','project_tax'),('total','project_gross'))}
        before['cost'] = D(str(old_cost)) if comparable and old_cost is not None else None
        before['margin'] = gross_margin(before['cost'],before['net']) if before['cost'] is not None and before['net'] is not None else None
        compare = comparison(before,{'net':output.project_net,'tax':output.project_tax,'total':output.project_gross,
                                     'cost':total_cost,'margin':reading['margin']},request['currency'])
        for key,row in compare.items():
            trace_key = 'gross' if key == 'total' else key
            proposed_trace = reading['traces'].get(trace_key)
            if proposed_trace:
                row['traces']['proposed'] = deepcopy(proposed_trace)
            current_trace = current_output.get('workspace',{}).get('cascade',{}).get('traces',{}).get(trace_key)
            if comparable and current_trace:
                row['traces']['current'] = deepcopy(current_trace)
    attribution = {'available':False,'reason':'Sin dato: la operación anterior no conserva todas las autoridades de reprecio.','order':list(DRIVERS)}
    if not current:
        attribution['reason'] = 'Sin dato: todavía no se ha aplicado un precio al proyecto.'
    elif not comparable:
        attribution['reason'] = 'Sin dato: las operaciones usan monedas distintas; no se comparan sin conversión declarada.'
    elif current_snapshot.get('replay'):
        before_state,after_state = replay_state(current_snapshot['replay']),replay_state(replay)
        try:
            attribution = explain(before_state,after_state,lambda state:_reprice(repo.org_id,state,before_state,after_state))
            if attribution['current']['net'] != D(str(current_output['project_net'])) or attribution['proposed']['net'] != output.project_net:
                raise PricingError('repricing_does_not_close')
        except (PricingError,ValueError,KeyError) as error:
            attribution = {'available':False,'reason':'Sin dato: las autoridades congeladas no admiten este escenario intermedio.','order':list(DRIVERS),
                           'technical_code':getattr(error,'code','incompatible_counterfactual')}
    sources = []
    def human_date(value):
        text = str(value)
        return '-'.join(reversed(text.split('-'))) if len(text) == 10 else text
    for authority in repo.authorities:
        if 'cost' in authority:
            item = authority['cost']
            label = 'Catálogo DEMO' if item.get('is_demo') else f"Lista de costos vigente desde {human_date(item.get('valid_from','Sin dato'))}"
        elif 'fx' in authority:
            item = authority['fx']
            label = f"FX {item['base_currency']} → {item['quote_currency']} · {human_date(item['observed_date'])} · {str(item['observed_rate']).replace('.',',')}"
        elif 'configuration' in authority:
            code = authority['configuration']['context_code']
            label = f"Lista comercial {'principal' if code == 'DEFAULT' else code} · revisión {authority['configuration']['revision']}"
        else:
            continue
        if label not in sources:
            sources.append(label)
    locked = project['status'] != 'DRAFT' or bool(rows(
        "SELECT id FROM public.pricing_operations WHERE org_id=%s AND project_id=%s AND state='APPLIED' "
        "AND revision_code=%s AND (%s IS NULL OR approved_at>%s) LIMIT 1",
        [repo.org_id,project['id'],project['current_revision'],project.get('pricing_reset_at'),project.get('pricing_reset_at')]))
    workspace = {'comparison':compare,'cascade':reading,'positions':line_readings,'explanation':attribution,
        'editable':not locked,'blocked_reason':'Esta revisión ya está cerrada para precios. Prepara una nueva revisión o deshaz el precio desde el proyecto.' if locked else None,
        'band':{'minimum':min_margin,'target':rules['default_margin_pct'],'maximum':max_margin},
        'requested_margin':request['target_margin'],'policy':{key:value for key,value in decision.items() if key != 'margin'},
        'sources':sources,'demo':any(a.get('cost',{}).get('is_demo') for a in repo.authorities)
            or any(bundle.get('demo',False) for bundle in repo.technical.values()),
        'rounding':'El costo consumido conserva su precisión exacta. Precio unitario indicativo a cuatro decimales; el neto de cada línea usa el precio exacto y se redondea una vez con mitades alejándose de cero. El IVA se redondea por proyecto.',
        'current_revision':current['revision_code'] if current else None}
    controls = {key:str(request[key]) if request.get(key) is not None else '' for key in ('pricing_mode','currency','effective_date',
        'context_code','fx_snapshot_id','discount_pct','target_margin','segment')}
    workspace['controls'] = controls
    previous_controls = decoded(current['request']) if current else {}
    def visible_control(key,value):
        if value is None:
            return None
        if key == 'fx_snapshot_id':
            selected = next((item for item in financial['fx'] if str(item['id']) == str(value)),None)
            return f"{selected['observed_date']} · {selected['observed_rate']}" if selected else 'Sin conversión'
        if key in {'target_margin','discount_pct'}:
            from dekopen_engine.price_workspace import percent_points
            return percent_points(D(str(value)))
        return str(value)
    workspace['changes'] = [{'field':key,'before':visible_control(key,previous_controls.get(key)),
        'after':visible_control(key,value)} for key,value in controls.items()
        if key != 'target_margin' or value != '']
    workspace['changes'] = [item for item in workspace['changes'] if item['before'] != item['after']]
    for value in [workspace['cascade'],*workspace['positions'],*(item['cascade'] for item in workspace['positions'])]:
        for trace in value.get('traces',{}).values():
            trace['authority'] = ' · '.join(sources) or 'Autoridad declarada de la operación'
    for position in workspace['positions']:
        for item in position.get('composition',[]):
            if 'trace' in item:
                item['trace']['authority'] = ' · '.join(sources) or 'Autoridad declarada de compra'
    for item in attribution.get('contributions',[]):
        for trace in item.get('traces',{}).values():
            trace['authority'] = 'Autoridades congeladas de las operaciones actual y propuesta'
    for row in compare.values():
        for stage,trace in row.get('traces',{}).items():
            if stage == 'proposed':
                trace['authority'] = ' · '.join(sources) or 'Autoridad declarada de la propuesta'
            elif stage != 'current':
                trace['authority'] = 'Operación aplicada y autoridades congeladas de la propuesta'
    return frozen_copy({'workspace':workspace,'replay':replay,'policy':decision})


def project_price_attention(org_id,user_id,role):
    counts = {'pricing_pending':0,'pricing_decisions':0}
    if role == 'OWNER':
        counts['pricing_pending'] = len(rows("SELECT id FROM public.pricing_operations WHERE org_id=%s AND state='PENDING'",[org_id]))
    if role in ('OWNER','ESTIMATOR'):
        counts['pricing_decisions'] = len(rows("SELECT o.id FROM public.pricing_operations o WHERE o.org_id=%s AND o.requested_by=%s "
            "AND o.approved_by IS DISTINCT FROM o.requested_by AND o.state IN ('APPLIED','REJECTED') "
            'AND NOT EXISTS(SELECT 1 FROM public.pricing_attention_receipts r WHERE r.org_id=o.org_id AND r.operation_id=o.id AND r.user_id=%s)',
            [org_id,user_id,user_id]))
    return counts
