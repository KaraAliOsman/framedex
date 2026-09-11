"""Server-authoritative BOM costing, reproducible previews and approvals."""

from dataclasses import asdict
from decimal import Decimal, localcontext
from hashlib import sha256
import json

from django.db import connection

from dekopen_engine.commercial import (
    CommercialLine, PricingError, PricingMode, direct_cost, discount_state,
    finish_lines, target_project, unit_price, validate_segment,
)
from dekopen_engine.glass import exact_glass_area_m2
from engine_api.adapter import calculate_from_api
from engine_api.cutting_repository import CuttingRepository
from engine_api.repository import SystemParamsRepository
from pricing.repository import PricingRepository, audit_reason, json_text, one, rows

D = Decimal


def glass_sku(tree, bay_id):
    if tree.get('id') == bay_id:
        sku = tree.get('glass_article_sku')
        if not sku:
            raise PricingError('missing_selected_glass_sku')
        return sku
    for child in tree.get('children', []):
        try:
            return glass_sku(child,bay_id)
        except PricingError as error:
            if error.code != 'glass_bay_not_found':
                raise
    raise PricingError('glass_bay_not_found')


def decoded(value):
    return json.loads(value, parse_float=Decimal) if isinstance(value,str) else value


def source_revision(project, positions):
    # Full technical input plus stored commercial values detects edits and applies.
    return sha256(json_text({'project':project,'positions':positions}).encode()).hexdigest()


def linear_cost(repo, sku, length, stock_length):
    try:
        return repo.cost(sku,'BAR') * length / stock_length
    except PricingError as error:
        if error.code != 'incompatible_cost_unit':
            raise
        return repo.cost(sku,'M') * length / D('1000')


def position_cost(repo, position, rules):
    # Technical catalog has its existing authenticated policies; commercial raw
    # costs are read only after returning to the backend calculator role.
    with connection.cursor() as cursor:
        cursor.execute('SET LOCAL ROLE authenticated')
    try:
        params = SystemParamsRepository().load_visible(position['system_id'],repo.org_id)
        stock_repo = CuttingRepository()
        profile_stocks = {}
        steel_stocks = {}
        tree = decoded(position['parametric_tree'])
        color = 'WHITE' if position['color_interior']=='WHITE' and position['color_exterior']=='WHITE' else 'FOILED'
        result = calculate_from_api(parametric_tree=tree, nominal_width_mm=position['width_mm'],
                                    nominal_height_mm=position['height_mm'],color=color,params=params)
        for cut in result.profile_cuts:
            profile_stocks[cut.sku] = stock_repo.profile_stock(position['system_id'],repo.org_id,cut.sku,color)
        for steel in result.reinforcements:
            steel_stocks[(steel.parent_profile_sku,steel.reinforcement_sku)] = stock_repo.reinforcement_stock(
                position['system_id'],repo.org_id,steel.parent_profile_sku,steel.reinforcement_sku,color)[0]
    finally:
        if not connection.needs_rollback:
            with connection.cursor() as cursor:
                cursor.execute('SET LOCAL ROLE pricing_backend')
    tree = decoded(position['parametric_tree'])
    color = 'WHITE' if position['color_interior']=='WHITE' and position['color_exterior']=='WHITE' else 'FOILED'
    materials = []
    for cut in result.profile_cuts:
        stock = profile_stocks[cut.sku]
        materials.append(linear_cost(repo,stock.commercial_sku,cut.length_mm*cut.qty,stock.stock_length_mm))
    for steel in result.reinforcements:
        stock = steel_stocks[(steel.parent_profile_sku,steel.reinforcement_sku)]
        materials.append(linear_cost(repo,stock.commercial_sku,steel.length_mm*steel.qty,stock.stock_length_mm))
    for glass in result.glasses:
        # The selected commercial glass SKU is explicit in the persisted tree.
        sku = glass_sku(tree,glass.bay_id)
        materials.append(repo.cost(sku,'M2') * exact_glass_area_m2(glass.width_mm,glass.height_mm))
    for panel in result.panels:
        materials.append(repo.cost(panel.sku,'M2') * exact_glass_area_m2(panel.width_mm,panel.height_mm))
    for kit in result.hardware_items:
        materials.append(repo.cost(kit.kit_sku,'KIT') * kit.qty)
    area = exact_glass_area_m2(position['width_mm'],position['height_mm'])
    return (direct_cost(materials,area,rules['waste_factor_pct'],rules['labor_rate_per_m2'],
                        rules['installation_rate_per_m2']), area, result)


def preview(org_id, actor, request):
    project = one('SELECT * FROM public.projects WHERE id=%s AND org_id=%s FOR UPDATE',
                  [request['project_id'],org_id],'project_not_found')
    if project['status'] != 'DRAFT':
        raise PricingError('commercial_revision_required')
    positions = rows('SELECT * FROM public.project_positions WHERE project_id=%s AND org_id=%s '
                     'ORDER BY position_index FOR UPDATE',[project['id'],org_id])
    if not positions:
        raise PricingError('project_has_no_positions')
    rules = one('SELECT * FROM public.pricing_rules WHERE org_id=%s',[org_id],'pricing_rules_not_found')
    repo = PricingRepository(org_id,request['effective_date'],request['currency'],request.get('fx_snapshot_id'))
    mode = PricingMode(request['pricing_mode'])
    if mode == PricingMode.TARGET_GROSS_MARGIN_PROJECT and actor.active_organization.role != 'OWNER':
        raise PricingError('pricing_permission_denied')
    organization = one('SELECT currency FROM public.tenancy_organizations WHERE id=%s',[org_id])
    repo.authorities.append({'organization_currency':organization['currency']})
    calculation_rules = {**rules,
        'labor_rate_per_m2':repo.convert(rules['labor_rate_per_m2'],organization['currency']),
        'installation_rate_per_m2':repo.convert(rules['installation_rate_per_m2'],organization['currency'])}
    discount = request['discount_pct']
    state = discount_state(actor.active_organization.role,discount,request['confirmed'])
    if mode == PricingMode.COMMERCIAL_LIST_WITH_DISCOUNTS:
        validate_segment(request['segment'],discount,sum(p['quantity'] for p in positions))
    if mode == PricingMode.TARGET_GROSS_MARGIN_PROJECT and discount:
        raise PricingError('target_margin_already_defines_final_price')
    cost_lines, priced_lines, technical = [], [], []
    with localcontext() as context:
        context.prec = 80
        for position in positions:
            cost, area, result = position_cost(repo,position,calculation_rules)
            index = position['position_index']
            cost_lines.append((index,cost*position['quantity']))
            technical.append({'position_id':position['id'],'unit_cost':cost,
                              'bom':result.model_dump(mode='json')})
            if mode == PricingMode.TARGET_GROSS_MARGIN_PROJECT:
                continue
            extra = {}
            if mode != PricingMode.COST_PLUS_MARGIN:
                config = repo.configuration(mode.value,request['context_code'],position['typology'])
                if mode == PricingMode.PRICE_PER_M2_BY_TYPOLOGY:
                    if not config['base_glass_sku'] or not result.glasses:
                        raise PricingError('missing_glass_authority')
                    selected = {glass_sku(decoded(position['parametric_tree']),glass.bay_id)
                                for glass in result.glasses}
                    if len(selected) != 1:
                        raise PricingError('ambiguous_selected_glass')
                    extra = {'rate':repo.convert(config['rate_per_m2'],config['currency']),
                             'selected_glass':repo.cost(next(iter(selected)),'M2'),
                             'base_glass':repo.cost(config['base_glass_sku'],'M2')}
                elif mode == PricingMode.FIXED_PRICE_MATRIX_DIMENSIONAL:
                    extra = {'cells':repo.matrix(config)}
                else:
                    extra = {'catalog_price':repo.convert(config['catalog_price'],config['currency'])}
            exact_price = unit_price(mode,cost=cost,margin=rules['default_margin_pct'],area=area,
                                     width=position['width_mm'],height=position['height_mm'],
                                     foil=position['color_interior']!='WHITE' or position['color_exterior']!='WHITE',**extra)
            priced_lines.append(CommercialLine(index,position['quantity'],cost,exact_price,discount))
        output = (target_project(cost_lines,request['target_margin'],request['currency'],rules['tax_rate_pct'])
                  if mode == PricingMode.TARGET_GROSS_MARGIN_PROJECT
                  else finish_lines(priced_lines,request['currency'],rules['tax_rate_pct']))
    audit_reason(request['reason'])
    record = one(
        'INSERT INTO public.pricing_operations(org_id,project_id,requested_by,request,input_snapshot,'
        'result,source_revision,state,reason) VALUES(%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s,%s,%s) RETURNING id',
        [org_id,project['id'],request['_actor_id'],
         json_text({key:value for key,value in request.items() if not key.startswith('_')}),
         json_text({'rules':rules,'authorities':repo.authorities,'positions':technical,'cost_lines':cost_lines}),
         json_text(asdict(output)),source_revision(project,positions),'PENDING' if state=='PENDING' else 'PREVIEW',request['reason']])
    return {'id':str(record['id']),'state':'PENDING' if state=='PENDING' else 'PREVIEW',
            'project_id':str(project['id']),'discount_pct':str(discount),
            'currency':request['currency'],**asdict(output)}


def operation_public(operation):
    return {'id':str(operation['id']),'state':operation['state'],
            'project_id':str(operation['project_id']),
            'discount_pct':str(decoded(operation['request'])['discount_pct']),
            'currency':decoded(operation['request'])['currency'],**decoded(operation['result'])}


def apply_operation(org_id, actor_id, role, operation_id, reason, confirmed, reject=False):
    operation = one('SELECT * FROM public.pricing_operations WHERE id=%s AND org_id=%s FOR UPDATE',
                    [operation_id,org_id],'pricing_operation_not_found')
    if role not in ('OWNER','ESTIMATOR') or (role != 'OWNER' and operation['requested_by'] != actor_id):
        raise PricingError('pricing_permission_denied')
    if operation['state'] not in ('PREVIEW','PENDING'):
        raise PricingError('operation_already_final')
    request = decoded(operation['request'])
    state = discount_state(role,D(str(request['discount_pct'])),confirmed)
    if state == 'PENDING' or (reject and role != 'OWNER'):
        raise PricingError('owner_approval_required')
    audit_reason(reason)
    if reject:
        one("UPDATE public.pricing_operations SET state='REJECTED',approved_by=%s,approved_at=now(),reason=%s "
            'WHERE id=%s AND org_id=%s RETURNING id',[actor_id,reason,operation_id,org_id])
        operation['state'] = 'REJECTED'
        return operation_public(operation)
    project = one('SELECT * FROM public.projects WHERE id=%s AND org_id=%s FOR UPDATE',
                  [operation['project_id'],org_id])
    positions = rows('SELECT * FROM public.project_positions WHERE project_id=%s AND org_id=%s '
                     'ORDER BY position_index FOR UPDATE',[project['id'],org_id])
    if project['status'] != 'DRAFT' or source_revision(project,positions) != operation['source_revision']:
        raise PricingError('stale_pricing_operation')
    output = decoded(operation['result'])
    snapshot = decoded(operation['input_snapshot'])
    costs = {int(index):D(str(cost)) for index,cost in snapshot['cost_lines']}
    prices = {int(index):D(str(price)) for index,price in output['lines']}
    with connection.cursor() as cursor:
        for position in positions:
            index = position['position_index']
            if prices[index] < costs[index]:
                raise PricingError('negative_margin')
            cursor.execute('UPDATE public.project_positions SET cost_net=%s,price_net=%s,discount_pct=%s,'
                           'updated_at=now() WHERE id=%s AND org_id=%s',
                           [costs[index],prices[index],request['discount_pct'],position['id'],org_id])
        cursor.execute('UPDATE public.projects SET total_cost_net=%s,total_price_net=%s,total_price_tax=%s,'
                       'total_price_gross=%s,updated_at=now() WHERE id=%s AND org_id=%s',
                       [sum(costs.values(),D('0')),output['project_net'],output['project_tax'],
                        output['project_gross'],project['id'],org_id])
        cursor.execute("UPDATE public.pricing_operations SET state='APPLIED',approved_by=%s,approved_at=now(),reason=%s "
                       'WHERE id=%s AND org_id=%s',[actor_id,reason,operation_id,org_id])
    operation['state'] = 'APPLIED'
    return operation_public(operation)
