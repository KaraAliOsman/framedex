"""Server-authoritative BOM costing, reproducible previews and approvals."""

from dataclasses import asdict
from decimal import Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json

from django.db import connection

from authentication.errors import contract_error
from authentication.rls import tx_aborted
from dekopen_engine.commercial import (
    CommercialLine, PricingError, PricingMode, direct_cost, discount_state,
    finish_lines, target_project, unit_price, validate_segment,
)
from dekopen_engine.glass import exact_glass_area_m2
from dekopen_engine.snapshot import result_payload
from dekopen_engine.glass_composition import price_glass, glass_rate_requirements, glass_polygon_perimeter_m
from engine_api.adapter import parse_parametric_node
from engine_api.adapter import engine_result_from_api
from pricing.repository import PricingRepository, audit_reason, json_text, one, rows

D = Decimal

# Human es-CL detail per pricing failure code — the HTTP layer renders
# these so an estimator sees what to fix, never a raw engine code. Codes
# raised while iterating positions get prefixed with the position label
# ("Vano 3 · Dormitorio: …") so the blocker names where it lives.
PRICING_ERROR_DETAILS = {
    'invalid_margin_band': 'revisa mínimo, objetivo y máximo de la banda de margen',
    'cascade_does_not_close': 'la composición no coincide con su costo; revisa sus autoridades antes de aplicar',
    'incomplete_repricing_evidence': 'falta una autoridad técnica o comercial congelada; revisa el catálogo y sus costos',
    'installation_rule_duplicate': 'la instalación está seleccionada por posición y por proyecto; elige una sola regla',
    'ambiguous_authority': 'hay más de una autoridad de costos vigente para la fecha; revisa las listas de costos',
    'ambiguous_cost_list': 'hay más de una lista de costos vigente; revisa las vigencias en Configuración',
    'ambiguous_selected_glass': 'usa más de un vidrio distinto y el precio por m² exige un solo vidrio por vano',
    'audit_reason_required': 'indica el motivo del cambio para dejar trazabilidad',
    'authority_not_found': 'no se encontró la autoridad comercial requerida; revisa la configuración de precios',
    'commercial_revision_required': 'requiere una nueva revisión antes de cotizar; crea la revisión siguiente desde el proyecto',
    'cost_list_not_found': 'no existe la lista de costos indicada',
    'fx_snapshot_immutable': 'la cotización de moneda ya está cerrada',
    'glass_bay_not_found': 'no se encontró su paño de vidrio; revisa el diseño',
    'glass_processing_cost_missing': 'falta una tarifa declarada para el vidrio, su área mínima o sus procesos; completa la lista de costos',
    'incompatible_cost_unit': 'la unidad de costo de un material no es compatible con su uso; revisa la lista de costos',
    'invalid_admin_fields': 'revisa los campos de configuración',
    'invalid_column_mapping': 'revisa el mapeo de columnas del archivo',
    'invalid_xlsx_file': 'el archivo Excel no es válido o está dañado',
    'missing_fx_authority': 'falta la cotización de moneda para la fecha; regístrala antes de cotizar en otra moneda',
    'missing_glass_authority': 'no hay precio registrado para el vidrio seleccionado; agrégalo a la lista de costos o cambia el vidrio',
    'missing_selected_glass_sku': 'no declara el vidrio seleccionado; revisa el diseño',
    'negative_margin': 'la operación dejaría margen negativo; ajusta el precio o el costo',
    'operation_already_final': 'la operación de precios ya está cerrada',
    'operation_not_withdrawable': 'la operación ya no se puede anular',
    'owner_approval_required': 'el descuento requiere aprobación del dueño',
    'owner_confirmation_required': 'esta operación requiere la confirmación del dueño',
    'pricing_operation_not_found': 'no se encontró la operación comercial indicada; recarga el listado',
    'pricing_configuration_not_found': 'falta la tarifa del modo de precio para esta tipología; complétala en Precios',
    'unsupported_currency': 'esta moneda no admite cotización; usa CLP o USD en Ajustes',
    'pricing_permission_denied': 'tu rol no permite esta operación comercial',
    'pricing_rules_not_found': 'no hay reglas de precio configuradas para tu taller; registra margen e impuesto en Ajustes → Costos y precios → Reglas comerciales antes de cotizar',
    'project_has_no_positions': 'el proyecto no tiene vanos para cotizar',
    'project_not_found': 'no se encontró el proyecto; recarga y vuelve a intentar',
    'stale_pricing_operation': 'los precios cambiaron desde que preparaste la operación; recarga y vuelve a aplicar',
    'target_margin_already_defines_final_price': 'el margen objetivo ya define el precio final y no admite descuento adicional',
    'unknown_pricing_resource': 'la configuración no está disponible',
    'xlsx_expanded_limit': 'el archivo supera el límite de filas permitido',
    'xlsx_header_missing_or_duplicate': 'el Excel no tiene los encabezados esperados o los repite',
    'xlsx_no_rows': 'el archivo no contiene filas de datos',
    'xlsx_sheet_limit': 'el archivo supera el tamaño permitido',
}


def _position_label(position):
    tag = (position.get('location_tag') or '').strip()
    return f"Vano {position['position_index']}" + (f" · {tag}" if tag else "")


def pricing_public_detail(code):
    """Failure code → standalone human sentence, for surfaces that show the
    detail without a position prefix (view mapping, batch item errors)."""
    detail = PRICING_ERROR_DETAILS.get(
        code,'la operación comercial requiere revisar sus permisos, datos o configuración')
    return detail[0].upper() + detail[1:] + '.'


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


def design_glass_sku(tree, bay_id):
    # Assembly BOM items carry 'module_id|bay_id' — resolve inside the module tree.
    if isinstance(tree, dict) and tree.get('version') == 'product-v2':
        module_id, separator, inner_id = bay_id.partition('|')
        if not separator:
            raise PricingError('glass_bay_not_found')
        for module in tree.get('assembly', {}).get('modules', []):
            if module.get('id') == module_id:
                return glass_sku(module.get('tree', {}), inner_id)
        raise PricingError('glass_bay_not_found')
    return glass_sku(tree, bay_id)


def design_glass_node(tree, bay_id):
    if tree.get('version') == 'product-v2':
        module_id, _, bay_id = bay_id.partition('|')
        tree = next((module['tree'] for module in tree['assembly']['modules'] if module['id'] == module_id), {})
    def visit(node):
        if node.get('id') == bay_id:
            return node
        return next((found for child in node.get('children', []) if (found := visit(child)) is not None), None)
    found = visit(tree)
    if found is None:
        raise PricingError('glass_bay_not_found')
    return parse_parametric_node(found)


def decoded(value):
    return json.loads(value, parse_float=Decimal) if isinstance(value,str) else value


def source_revision(project, positions):
    # Full technical input plus stored commercial values detects edits and applies.
    return sha256(json_text({'project':project,'positions':positions}).encode()).hexdigest()


def linear_cost(repo, sku, length, stock_length, *, with_trace=False):
    from dekopen_engine.price_workspace import linear_purchase
    try:
        result = linear_purchase(repo.cost(sku,'BAR'),'BAR',length,stock_length,repo.currency)
    except PricingError as error:
        if error.code != 'incompatible_cost_unit':
            raise
        result = linear_purchase(repo.cost(sku,'M'),'M',length,stock_length,repo.currency)
    return result if with_trace else result['amount']


def position_cost(repo, position, rules):
    from dekopen_engine.price_workspace import money_trace
    from pricing.resolved import safe_technical
    from projects.finishes import position_finish_code
    params, couplers, stocks, steels = safe_technical(repo,position['system_id'])
    tree = decoded(position['parametric_tree'])
    color = position_finish_code(position)
    result = engine_result_from_api(tree=tree,color=color,params=params,
        nominal_width_mm=position['width_mm'],nominal_height_mm=position['height_mm'],
        coupler_articles=couplers)
    if not getattr(repo,'frozen',False):
        from catalogs.glass import validate_design_products, enforce_design_glass
        with connection.cursor() as cursor:
            cursor.execute('SET LOCAL ROLE authenticated')
        try:
            validate_design_products(repo.org_id,position['system_id'],tree)
            enforce_design_glass(repo.org_id,tree,result,params)
        finally:
            if not tx_aborted():
                with connection.cursor() as cursor:
                    cursor.execute('SET LOCAL ROLE pricing_backend')
    try:
        profile_stocks = {cut.sku:stocks[f'{color}|{cut.sku}'] for cut in result.profile_cuts if cut.extra_code is None}
        steel_stocks = {(steel.parent_profile_sku,steel.reinforcement_sku):
            steels[f'{color}|{steel.parent_profile_sku}|{steel.reinforcement_sku}']
            for steel in result.reinforcements if steel.extra_code is None}
    except KeyError as error:
        if not getattr(repo,'frozen',False):
            from dekopen_engine.cutting import MissingStockAuthority
            raise MissingStockAuthority('No existe una compra de barra utilizable para este artículo.') from error
        raise PricingError('incomplete_repricing_evidence') from error
    materials = []
    composition = []
    glass_extras = []
    for cut in result.profile_cuts:
        if cut.extra_code is not None:
            continue  # Extra's sourced supply cost includes its physical BOM.
        stock = profile_stocks[cut.sku]
        buying = linear_cost(repo,stock.commercial_sku,cut.length_mm*cut.qty,stock.stock_length_mm,with_trace=True)
        cost = buying['amount']
        materials.append(cost)
        composition.append({'kind':'PROFILE','sku':stock.commercial_sku,
                            'quantity':str((cut.length_mm*cut.qty/D('1000')).quantize(D('0.001'))),
                            'unit':'M','cost':str(cost),'trace':buying['trace']})
    from dekopen_engine.finishes import finish_surcharge
    if result.finish is not None:
        surcharge_rule = result.finish.combination.surcharge
        priced_result = result.model_copy(update={"finish": result.finish.model_copy(update={
            "combination": result.finish.combination.model_copy(update={"surcharge": surcharge_rule.model_copy(update={
                "amount": (repo.convert(surcharge_rule.amount, surcharge_rule.currency)
                           if surcharge_rule.kind in {"FIXED", "PER_M"} else surcharge_rule.amount),
                "currency": repo.currency})})})})
        priced_result = priced_result.model_copy(update={"profile_cuts":[cut for cut in priced_result.profile_cuts if cut.extra_code is None]})
        profile_base = sum(materials,D(0))
        surcharge = finish_surcharge(priced_result, profile_base, repo.currency)
        resolved_surcharge = priced_result.finish.combination.surcharge
        surcharge_inputs = [('Tarifa declarada',resolved_surcharge.amount,
            '%' if resolved_surcharge.kind == 'PERCENT' else repo.currency)]
        if resolved_surcharge.kind == 'PERCENT':
            surcharge_inputs.append(('Costo de perfiles',profile_base,repo.currency))
        elif resolved_surcharge.kind == 'PER_M':
            surcharge_inputs.append(('Largo de perfiles',sum((cut.length_mm*cut.qty for cut in priced_result.profile_cuts),D(0)),'mm'))
        materials.append(surcharge)
        composition.append({'kind':'FINISH','sku':color,'quantity':'1','unit':'EA',
            'cost':str(surcharge), 'source':surcharge_rule.source,
            'trace':money_trace({'PERCENT':'Costo de perfiles × porcentaje ÷ 100',
                'PER_M':'Tarifa por metro × largo en mm ÷ 1 000','FIXED':'Recargo fijo declarado',
                'NONE':'Sin recargo declarado'}[resolved_surcharge.kind],surcharge,surcharge_inputs),
            'rule':surcharge_rule.model_dump(mode='json')})
    for steel in result.reinforcements:
        if steel.extra_code is not None:
            continue
        stock = steel_stocks[(steel.parent_profile_sku,steel.reinforcement_sku)]
        buying = linear_cost(repo,stock.commercial_sku,steel.length_mm*steel.qty,stock.stock_length_mm,with_trace=True)
        cost = buying['amount']
        materials.append(cost)
        composition.append({'kind':'REINFORCEMENT','sku':stock.commercial_sku,
                            'quantity':str((steel.length_mm*steel.qty/D('1000')).quantize(D('0.001'))),
                            'unit':'M','cost':str(cost),'trace':buying['trace']})
    for glass in result.glasses:
        # The selected commercial glass SKU is explicit in the persisted tree.
        sku = design_glass_sku(tree,glass.bay_id)
        # Rect panes keep exact w*h pricing; shaped pieces use the engine's
        # polygon area (bbox would overcharge a sloped or arched outline).
        glass_area = (
            glass.area_m2
            if getattr(glass, "shape", None)
            else exact_glass_area_m2(glass.width_mm, glass.height_mm)
        )
        node = design_glass_node(tree, glass.bay_id)
        rates = {sku: repo.cost(sku, 'M2')}
        for charge_sku, unit in glass_rate_requirements(node.glass_product, node.glass_processing):
            rates[charge_sku] = repo.cost(charge_sku, unit)
        try:
            priced = price_glass(product=node.glass_product, sku=sku,
                width_mm=glass.width_mm, height_mm=glass.height_mm, rates=rates,
                processing=node.glass_processing, shape_area_m2=glass_area if glass.shape else None,
                shape_perimeter_m=glass_polygon_perimeter_m(glass.shape) if glass.shape else None)
        except ValueError as error:
            raise PricingError('glass_processing_cost_missing') from error
        from dekopen_engine.extras import glass_bar_lines
        if priced.bars_length_m:
            glass_extras.extend(glass_bar_lines(priced,node.glass_product,bay_id=glass.bay_id,currency=repo.currency,
                waste=rules['waste_factor_pct'],margin=rules['default_margin_pct']))
        cost = priced.total_cost-sum((charge.total_cost for charge in priced.charges if charge.kind in {'Palillaje por metro','Cruce de palillaje'}),D(0))
        materials.append(cost)
        composition.append({'kind':'GLASS','sku':sku,
                            'quantity':str(priced.billable_area_m2.quantize(D('0.0001'))),
                            'unit':'M2','cost':str(cost),
                            'trace':money_trace('Suma de cantidades facturables × tarifas por vidrio y tratamiento; palillaje en extras',cost,
                                [(label,value,unit) for charge in priced.charges if charge.kind not in {'Palillaje por metro','Cruce de palillaje'}
                                 for label,value,unit in [(charge.kind+' · cantidad',charge.quantity,{'M2':'m²','M':'m','EA':'unidad'}[charge.unit]),
                                     (charge.kind+' · tarifa',charge.unit_cost,repo.currency),
                                     (charge.kind+' · aporte',charge.total_cost,repo.currency)]]),
                            'glass_charges':[charge.model_dump(mode='json') for charge in priced.charges]})
    for panel in result.panels:
        panel_area = exact_glass_area_m2(panel.width_mm,panel.height_mm)
        rate = repo.cost(panel.sku,'M2')
        cost = rate * panel_area
        materials.append(cost)
        composition.append({'kind':'PANEL','sku':panel.sku,
                            'quantity':str(panel_area.quantize(D('0.0001'))),
                            'unit':'M2','cost':str(cost),'trace':money_trace('Área × tarifa por m²',cost,
                                [('Área del panel',panel_area,'m²'),('Tarifa por m²',rate,repo.currency)])})
    from dekopen_engine.hardware_classes import hardware_component_cost
    for kit in result.hardware_items:
        if kit.resolution is not None:
            for component in kit.contents:
                rate = repo.cost(component.sku,component.price_unit)
                cost = hardware_component_cost(component,rate) * kit.qty
                materials.append(cost)
                composition.append({'kind':'HARDWARE','sku':component.sku,
                    'quantity':str(component.price_quantity * kit.qty), 'unit':component.price_unit,
                    'cost':str(cost),
                    'trace':money_trace('Cantidad facturable por conjunto × conjuntos × tarifa de compra',cost,
                        [('Cantidad por conjunto',component.price_quantity,{'M':'m','EA':'unidad','KIT':'kit'}.get(component.price_unit,'unidad')),
                         ('Conjuntos',D(kit.qty),'unidad'),('Tarifa de compra',rate,repo.currency)]),
                    'hardware_class':kit.resolution.class_name,
                    'cut_length_mm':None if component.cut_length_mm is None else str(component.cut_length_mm),
                    'source':component.source})
            continue
        rate = repo.cost(kit.kit_sku,'KIT')
        cost = rate * kit.qty
        materials.append(cost)
        composition.append({'kind':'HARDWARE','sku':kit.kit_sku,
                            'quantity':str(kit.qty),'unit':'KIT',
                            'cost':str(cost),'trace':money_trace('Conjuntos × tarifa de compra',cost,
                                [('Conjuntos',D(kit.qty),'kit'),('Tarifa de compra',rate,repo.currency)])})
    # Frameless supports/fittings are counted pieces: a declared SKU must
    # resolve a unit price or the quote fails — never silently priced at zero.
    for fitting in result.fittings:
        if fitting.extra_code is not None:
            continue
        rate = repo.cost(fitting.sku,'EA')
        cost = rate * fitting.qty
        materials.append(cost)
        composition.append({'kind':'FITTING','sku':fitting.sku,
                            'quantity':str(fitting.qty),'unit':'EA',
                            'cost':str(cost),'trace':money_trace('Unidades × tarifa de compra',cost,
                                [('Unidades',D(fitting.qty),'unidad'),('Tarifa de compra',rate,repo.currency)])})
    area = exact_glass_area_m2(position['width_mm'],position['height_mm'])
    from projects.extras import converted_lines
    from dekopen_engine.extras import price_facts
    extra_lines = converted_lines(repo,price_facts(params.extra_authority,result.extras)) if result.extras else []
    extra_lines.extend(glass_extras)
    installation = D('0') if rules.get('explicit_project_installation') or any(item.installation for item in extra_lines) else rules['installation_rate_per_m2']
    total = direct_cost(materials,area,rules['waste_factor_pct'],rules['labor_rate_per_m2'],
                        installation) + sum((item.total_cost for item in extra_lines),D('0'))
    composition.extend({'kind':'EXTRA','sku':item.code,'quantity':str(item.quantity),'unit':item.unit,
                        'cost':str(item.total_cost),'source':item.source,
                        'trace':money_trace('Cantidad derivada del extra × tarifa de compra',item.total_cost,
                            [('Cantidad derivada',item.quantity,item.unit),('Tarifa de compra',item.cost_rate,repo.currency)])} for item in extra_lines)
    formation = {'composition':composition,'unit_cost_exact':str(total),
                 'extra_authority':params.extra_authority.model_dump(mode='json') if params.extra_authority else None,
                 'extra_lines':[item.model_dump(mode='json') for item in extra_lines],
                 'materials_cost':str(sum(materials,D('0'))),
                 'waste_pct':str(rules['waste_factor_pct']),
                 'labor_rate_per_m2':str(rules['labor_rate_per_m2']),
                 'installation_rate_per_m2':str(installation),
                 'area_m2':str(area)}
    return total, area, result, formation


def configured_unit_price(repo, mode, position, *, cost, area, result, margin, context_code, extras=(), with_trace=False):
    """One selling-price authority for project pricing and indicative finish deltas."""
    if mode == PricingMode.TARGET_GROSS_MARGIN_PROJECT:
        raise PricingError('project_mode_requires_project')
    extra = {}
    if mode != PricingMode.COST_PLUS_MARGIN:
        config = repo.configuration(mode.value, context_code, position['typology'])
        if mode == PricingMode.PRICE_PER_M2_BY_TYPOLOGY:
            if not config['base_glass_sku'] or not result.glasses:
                raise PricingError('missing_glass_authority')
            selected = {design_glass_sku(decoded(position['parametric_tree']), glass.bay_id)
                        for glass in result.glasses}
            if len(selected) != 1:
                raise PricingError('ambiguous_selected_glass')
            extra = {'rate': repo.convert(config['rate_per_m2'], config['currency']),
                     'selected_glass': repo.cost(next(iter(selected)), 'M2'),
                     'base_glass': repo.cost(config['base_glass_sku'], 'M2')}
        elif mode == PricingMode.FIXED_PRICE_MATRIX_DIMENSIONAL:
            extra = {'cells': repo.matrix(config)}
        else:
            extra = {'catalog_price': repo.convert(config['catalog_price'], config['currency'])}
    from dekopen_engine.extras import position_price
    base_price = unit_price(mode, cost=cost-sum((item.total_cost for item in extras),D('0')), margin=margin, area=area,
                      width=position['width_mm'], height=position['height_mm'],
                      foil=position['color_interior'] != 'WHITE' or position['color_exterior'] != 'WHITE', **extra)
    price = position_price(base_price,extras)
    if not with_trace:
        return price
    from dekopen_engine.price_workspace import unit_price_trace
    return {'amount':price,'trace':unit_price_trace(mode.value,price,currency=repo.currency,
        cost=cost-sum((item.total_cost for item in extras),D(0)),margin=margin,area=area,
        width=position['width_mm'],height=position['height_mm'],
        foil=position['color_interior'] != 'WHITE' or position['color_exterior'] != 'WHITE',rates=extra,
        extras=[(item.name,item.total_price) for item in extras])}


def preview(org_id, actor, request, *, simulate=False, proposed_positions=None, workspace=False):
    project = one('SELECT * FROM public.projects WHERE id=%s AND org_id=%s FOR UPDATE',
                  [request['project_id'],org_id],'project_not_found')
    if not simulate and project['status'] != 'DRAFT':
        raise PricingError('commercial_revision_required')
    if not simulate and rows(
        "SELECT operation.id FROM public.pricing_operations operation "
        "JOIN public.projects project ON project.id=operation.project_id AND project.org_id=operation.org_id "
        "WHERE operation.org_id=%s AND operation.project_id=%s AND operation.state='APPLIED' "
        "AND COALESCE(operation.revision_code,'REV-A')=project.current_revision "
        "AND (project.pricing_reset_at IS NULL OR operation.approved_at>project.pricing_reset_at) LIMIT 1",
        [org_id, project['id']],
    ):
        raise PricingError('commercial_revision_required')
    positions = rows('SELECT * FROM public.project_positions WHERE project_id=%s AND org_id=%s '
                     'ORDER BY position_index FOR UPDATE',[project['id'],org_id])
    if proposed_positions is not None:
        positions = proposed_positions
    if not positions:
        raise PricingError('project_has_no_positions')
    rules = one('SELECT * FROM public.pricing_rules WHERE org_id=%s',[org_id],'pricing_rules_not_found')
    request = {**request,'target_margin':request.get('target_margin',rules['default_margin_pct'])}
    repo = PricingRepository(org_id,request['effective_date'],request['currency'],request.get('fx_snapshot_id'))
    repo.technical = {}
    mode = PricingMode(request['pricing_mode'])
    if mode == PricingMode.TARGET_GROSS_MARGIN_PROJECT and actor.active_organization.role != 'OWNER':
        raise PricingError('pricing_permission_denied')
    organization = one('SELECT currency FROM public.tenancy_organizations WHERE id=%s',[org_id])
    repo.authorities.append({'organization_currency':organization['currency']})
    calculation_rules = {**rules,
        'labor_rate_per_m2':repo.convert(rules['labor_rate_per_m2'],organization['currency']),
        'installation_rate_per_m2':repo.convert(rules['installation_rate_per_m2'],organization['currency'])}
    from projects.extras import service_lines, policy_record, lock_policy
    from dekopen_engine.extra_models import ExtraLine
    from dekopen_engine.extras import partition_price, service_price, target_services
    lock_policy(org_id)
    policy_evidence = policy_record(org_id)
    project_services = service_lines(org_id,project,positions,repo)
    calculation_rules['explicit_project_installation'] = any(item.installation for item in project_services)
    discount = request['discount_pct']
    state = (discount_state('OWNER',discount,request['confirmed'])
        if actor.active_organization.role == 'OWNER' else 'APPLIED')
    if mode == PricingMode.COMMERCIAL_LIST_WITH_DISCOUNTS:
        # Segment bands only bound the list-with-discounts catalogue: RETAIL
        # requires 0% and ARCHITECT 8–12%, so applying them to the manual
        # discount decision would make the estimator approval path
        # unreachable for any negotiated discount.
        validate_segment(request['segment'],discount,sum(p['quantity'] for p in positions))
    if mode == PricingMode.TARGET_GROSS_MARGIN_PROJECT and discount:
        raise PricingError('target_margin_already_defines_final_price')
    cost_lines, priced_lines, technical, extras_by_index, price_weights = [], [], [], {}, {}
    with localcontext() as context:
        context.prec = 256
        for position in positions:
            try:
                cost, area, result, formation = position_cost(repo,position,calculation_rules)
                index = position['position_index']
                position_extras = [ExtraLine.model_validate_json(json_text(item)) for item in formation.get('extra_lines',[])]
                if calculation_rules['explicit_project_installation'] and any(item.installation for item in position_extras):
                    raise PricingError('installation_rule_duplicate')
                extras_by_index[index] = position_extras
                cost_lines.append((index,cost*position['quantity']))
                technical.append({'position_id':position['id'],
                                  'position_index':index,
                                  'unit_cost':str(cost),
                                  'bom':result_payload(result),**formation})
                if mode == PricingMode.TARGET_GROSS_MARGIN_PROJECT:
                    price_weights[index] = cost-sum((item.total_cost for item in position_extras),D('0'))
                    continue
                selling = configured_unit_price(repo, mode, position, cost=cost, area=area,
                    result=result, margin=request.get('target_margin',rules['default_margin_pct']), context_code=request['context_code'],extras=position_extras,with_trace=True)
                exact_price = selling['amount']
                formation['price_trace'] = selling['trace']
                technical[-1]['price_trace'] = selling['trace']
                price_weights[index] = exact_price-sum((item.total_price for item in position_extras),D('0'))
                priced_lines.append(CommercialLine(index,position['quantity'],cost,exact_price,discount))
            except PricingError as error:
                # The estimator fixing this has to know WHICH vano fails —
                # name the position, then the human reason for the code.
                detail = PRICING_ERROR_DETAILS.get(
                    error.code,'la operación comercial requiere revisar sus permisos, datos o configuración')
                raise contract_error(422,error.code,f'{_position_label(position)}: {detail}.') from error
        extra_amounts = [D(str(item['amount'])) for item in request.get('extras') or []]
        service_rows = [service_price(item,request['currency']) for item in project_services]
        extra_amounts.extend(D(row['amount']) for row in service_rows)
        if mode == PricingMode.TARGET_GROSS_MARGIN_PROJECT and project_services:
            output, service_rows = target_services(cost_lines,project_services,request['target_margin'],request['currency'],rules['tax_rate_pct'],
                [D(str(item['amount'])) for item in request.get('extras') or []])
        else:
            output = (target_project(cost_lines,request['target_margin'],request['currency'],rules['tax_rate_pct'],extra_amounts)
                      if mode == PricingMode.TARGET_GROSS_MARGIN_PROJECT
                      else finish_lines(priced_lines,request['currency'],rules['tax_rate_pct'],extra_amounts))
    # Per-line selling detail so the decision screen can show unit price,
    # quantity and discount next to the line total — a line net is a per-
    # position TOTAL (unit × qty × (1−discount)), never a unit price. The
    # authority stays in the engine: exact_unit_price is the pre-discount
    # computed unit; the target-margin mode has no per-line discount, so
    # its unit readout is the allocated line net over quantity.
    quantities = {position['position_index']: int(position['quantity']) for position in positions}
    if mode == PricingMode.TARGET_GROSS_MARGIN_PROJECT:
        line_detail = [
            {'position_index': index, 'quantity': quantities[index],
             'unit_price': str((D(str(net)) / quantities[index]).quantize(D('0.0001'),rounding=ROUND_HALF_UP)),
             'discount_pct': '0'}
            for index, net in output.lines]
    else:
        line_detail = [
            {'position_index': line.position_index, 'quantity': quantities[line.position_index],
             'unit_price': str(line.exact_unit_price.quantize(D('0.0001'),rounding=ROUND_HALF_UP)),
             'discount_pct': str(line.discount)}
            for line in priced_lines]
    for detail,(index,net) in zip(line_detail,output.lines,strict=True):
        if extras_by_index[index]:
            detail.update(partition_price(net,price_weights[index],[(item,item.total_cost if mode == PricingMode.TARGET_GROSS_MARGIN_PROJECT else item.total_price)
                for item in extras_by_index[index]],quantity=quantities[index],currency=request['currency']))
    evidence = None
    if not simulate or workspace:
        from pricing.workspace import workspace_evidence
        evidence = workspace_evidence(repo,project,positions,request,rules,technical,cost_lines,
            priced_lines,output,line_detail,project_services,policy_evidence)
        if evidence['policy']['requires_approval'] and actor.active_organization.role != 'OWNER':
            state = 'PENDING'
    if simulate and not workspace:
        return {**asdict(output), 'currency': request['currency'], 'line_detail': line_detail}
    if workspace:
        return {'id':None,'state':'PENDING' if state == 'PENDING' else 'PREVIEW',
            'project_id':str(project['id']),'project_code':project.get('code') or '',
            'project_name':project.get('name') or '','client_name':project.get('client_name') or '',
            'revision_code':project['current_revision'],'discount_pct':str(discount),
            'pricing_mode':request['pricing_mode'],'segment':request['segment'],
            'currency':request['currency'],**asdict(output),'line_detail':line_detail,
            'services':service_rows,'workspace':evidence['workspace'],
            'reason':request['reason'],'requested_by':str(request['_actor_id']),
            'requested_by_email':request.get('_actor_email'),'approved_by':None,'approved_at':None,
            'created_at':None,'cost_lines':[],'positions_breakdown':[],
            'authorities':repo.authorities,'rules':{},'total_cost':str(evidence['workspace']['cascade']['cost'])}
    audit_reason(request['reason'])
    record = one(
        'INSERT INTO public.pricing_operations(org_id,project_id,requested_by,requested_by_email,'
        'request,input_snapshot,result,source_revision,revision_code,state,reason) '
        'VALUES(%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s,%s,%s,%s) RETURNING id,created_at',
        [org_id,project['id'],request['_actor_id'],request.get('_actor_email'),
         json_text({key:value for key,value in request.items() if not key.startswith('_')}),
         json_text({'rules':rules,'authorities':repo.authorities,'positions':technical,'cost_lines':cost_lines,'extra_policy':policy_evidence,'replay':evidence['replay'],'approval_policy':evidence['policy']}),
         json_text({**asdict(output),'line_detail':line_detail,'services':service_rows,'services_cost':str(sum((item.total_cost for item in project_services),D('0'))),'document_extra_prices':policy_evidence['policy']['document_prices'],'workspace':evidence['workspace']}),source_revision(project,positions),project['current_revision'],
         'PENDING' if state=='PENDING' else 'PREVIEW',request['reason']])
    costs = [(index, D(str(cost))) for index, cost in cost_lines]
    breakdown = [{
        'position_id':str(p['position_id']),
        'position_index':p.get('position_index'),
        'unit_cost':str(p.get('unit_cost') or ''),
        'area_m2':str(p.get('area_m2') or ''),
        'materials_cost':str(p.get('materials_cost') or ''),
        'waste_pct':str(p.get('waste_pct') or ''),
        'labor_rate_per_m2':str(p.get('labor_rate_per_m2') or ''),
        'installation_rate_per_m2':str(p.get('installation_rate_per_m2') or ''),
        'composition':p.get('composition') or [],
    } for p in technical]
    return {'id':str(record['id']),'state':'PENDING' if state=='PENDING' else 'PREVIEW',
            'project_id':str(project['id']),
            'project_code':project.get('code') or '',
            'project_name':project.get('name') or '',
            'client_name':project.get('client_name') or '',
            'revision_code':project['current_revision'],
            'discount_pct':str(discount),
            'pricing_mode':request.get('pricing_mode') or '',
            'segment':request.get('segment') or '',
            'currency':request['currency'],**asdict(output),
            'line_detail':line_detail,
            'workspace':evidence['workspace'],
            'services':service_rows,
            'document_extra_prices':policy_evidence['policy']['document_prices'],
            'extras':[{'label':item['label'],'kind':item['kind'],
                       'amount':str(item['amount'])}
                      for item in request.get('extras') or []],
            'cost_lines':[{'position_index':index,'line_cost':str(cost)} for index,cost in costs],
            'total_cost':str(sum((cost for _, cost in costs), D('0'))+sum((item.total_cost for item in project_services),D('0'))),
            'positions_breakdown':breakdown,
            'authorities':repo.authorities,
            'rules':{key:str(rules[key]) for key in
                     ('default_margin_pct','tax_rate_pct','waste_factor_pct','labor_rate_per_m2',
                      'installation_rate_per_m2') if key in rules},
            'reason':request['reason'],'requested_by':str(request['_actor_id']),
            'requested_by_email':request.get('_actor_email'),
            'approved_by':None,'approved_at':None,
            'created_at':record['created_at'].isoformat()}


def design_batch_preview(org_id, _actor, request):
    """§08-WC — honest money diff for a proposed batch design edit. Each
    item's proposed design passes the same engine gate a save would
    (calculate_design), then position_cost prices the stored position and
    the proposed product under the same rules — the count + Δ the human
    confirms is the real unit cost, never a model estimate."""
    from authentication.errors import ContractAPIException
    from projects.service import calculate_design

    project = one('SELECT * FROM public.projects WHERE id=%s AND org_id=%s',
                  [request['project_id'],org_id],'project_not_found')
    if project['status'] != 'DRAFT':
        raise PricingError('commercial_revision_required')
    # Mirror editable(): a version row on the current revision means it is
    # sealed — positions can no longer change, so a batch preview is moot.
    # project_versions is role-denied to `authenticated` (rbac_repair), so the
    # check must run as documentary_backend like every other reader does.
    from documents.repository import documentary_backend

    with documentary_backend():
        sealed = rows(
            "SELECT id FROM public.project_versions WHERE org_id=%s AND project_id=%s "
            "AND revision_code=%s LIMIT 1",
            [org_id, project['id'], project['current_revision']],
        )
    if sealed:
        raise PricingError('commercial_revision_required')
    rules = one('SELECT * FROM public.pricing_rules WHERE org_id=%s',[org_id],'pricing_rules_not_found')
    organization = one('SELECT currency FROM public.tenancy_organizations WHERE id=%s',[org_id])
    repo = PricingRepository(org_id,request['effective_date'],organization['currency'],None)
    repo.authorities.append({'organization_currency':organization['currency']})
    calculation_rules = {**rules,
        'labor_rate_per_m2':repo.convert(rules['labor_rate_per_m2'],organization['currency']),
        'installation_rate_per_m2':repo.convert(rules['installation_rate_per_m2'],organization['currency'])}
    items = []
    with localcontext() as context:
        context.prec = 80
        for entry in request['items']:
            position_id = entry['position_id']
            design = entry['design']
            found = rows(
                'SELECT * FROM public.project_positions WHERE id=%s AND org_id=%s AND project_id=%s',
                [position_id,org_id,project['id']],
            )
            if not found:
                items.append({'position_id':position_id,'ok':False,
                              'error_code':'position_not_found','error':'La posición no existe en este proyecto.'})
                continue
            position = found[0]
            try:
                # Engine validity under the member-facing role, exactly like
                # a save; cost reads swap roles internally as position_cost
                # already does.
                with connection.cursor() as cursor:
                    cursor.execute('SET LOCAL ROLE authenticated')
                try:
                    calculate_design(org_id,{**design,'system_id':str(design['system_id'])})
                finally:
                    with connection.cursor() as cursor:
                        cursor.execute('SET LOCAL ROLE pricing_backend')
                before, *_ = position_cost(repo,position,calculation_rules)
                pseudo = {
                    'system_id':design['system_id'],
                    'parametric_tree':design['parametric_tree'],
                    'width_mm':D(str(design['nominal_width_mm'])),
                    'height_mm':D(str(design['nominal_height_mm'])),
                    'color_interior':design['color'],
                    'color_exterior':design['color'],
                }
                after, *_ = position_cost(repo,pseudo,calculation_rules)
            except ContractAPIException as error:
                items.append({'position_id':position_id,'ok':False,
                              'error_code':error.contract_code,'error':error.public_detail})
                continue
            except PricingError as error:
                items.append({'position_id':position_id,'ok':False,
                              'error_code':error.code,
                              'error':pricing_public_detail(error.code)})
                continue
            quantity = position['quantity']
            items.append({
                'position_id':position_id,
                'index':position['position_index'],
                'ok':True,
                'quantity':quantity,
                'unit_cost_before':str(before),
                'unit_cost_after':str(after),
                'line_cost_before':str(before*quantity),
                'line_cost_after':str(after*quantity),
            })
    return {'currency':organization['currency'],'items':items}


def operation_public(operation):
    # Internal frozen authority for decision/sealing. HTTP callers must apply
    # price_visibility for the active member before returning buying costs.
    snapshot = decoded(operation['input_snapshot'])
    costs = snapshot.get('cost_lines') or []
    snapshot_rules = snapshot.get('rules') or {}
    breakdown = [{
        'position_id':str(p['position_id']),
        'position_index':p.get('position_index'),
        'unit_cost':str(p.get('unit_cost') or ''),
        'area_m2':str(p.get('area_m2') or ''),
        'materials_cost':str(p.get('materials_cost') or ''),
        'waste_pct':str(p.get('waste_pct') or ''),
        'labor_rate_per_m2':str(p.get('labor_rate_per_m2') or ''),
        'installation_rate_per_m2':str(p.get('installation_rate_per_m2') or ''),
        'composition':p.get('composition') or [],
    } for p in snapshot.get('positions') or []]
    return {'id':str(operation['id']),'state':operation['state'],
            'project_id':str(operation['project_id']),
            'project_code':operation.get('project_code') or '',
            'project_name':operation.get('project_name') or '',
            'client_name':operation.get('client_name') or '',
            'revision_code':operation.get('revision_code') or 'REV-A',
            'discount_pct':str(decoded(operation['request'])['discount_pct']),
            'pricing_mode':decoded(operation['request']).get('pricing_mode') or '',
            'segment':decoded(operation['request']).get('segment') or '',
            'currency':decoded(operation['request'])['currency'],**decoded(operation['result']),
            'extras':[{'label':item['label'],'kind':item.get('kind') or 'OTHER',
                       'amount':str(item['amount'])}
                      for item in decoded(operation['request']).get('extras') or []],
            'cost_lines':[{'position_index':index,'line_cost':str(cost)} for index,cost in costs],
            'total_cost':str(sum((D(str(cost)) for _, cost in costs), D('0'))+D(str(decoded(operation['result']).get('services_cost','0')))),
            'positions_breakdown':breakdown,
            'authorities':snapshot.get('authorities') or [],
            'rules':{key:str(snapshot_rules[key]) for key in
                     ('default_margin_pct','tax_rate_pct','waste_factor_pct','labor_rate_per_m2',
                      'installation_rate_per_m2') if key in snapshot_rules},
            'reason':str(operation['reason']),
            'requested_by':str(operation['requested_by']),
            'requested_by_email':operation.get('requested_by_email'),
            'approved_by':str(operation['approved_by']) if operation['approved_by'] else None,
            'approved_at':operation['approved_at'].isoformat() if operation['approved_at'] else None,
            'created_at':operation['created_at'].isoformat()}


def apply_operation(org_id, actor_id, role, operation_id, reason, confirmed, reject=False):
    operation = one('SELECT * FROM public.pricing_operations WHERE id=%s AND org_id=%s FOR UPDATE',
                    [operation_id,org_id],'pricing_operation_not_found')
    if role not in ('OWNER','ESTIMATOR') or (role != 'OWNER' and operation['requested_by'] != actor_id):
        raise PricingError('pricing_permission_denied')
    if operation['state'] not in ('PREVIEW','PENDING'):
        raise PricingError('operation_already_final')
    request = decoded(operation['request'])
    snapshot = decoded(operation['input_snapshot'])
    state = ('APPLIED' if role == 'ESTIMATOR' and snapshot.get('approval_policy') is not None
        else discount_state(role,D(str(request['discount_pct'])),confirmed))
    approval_required = snapshot.get('approval_policy',{}).get('requires_approval',False)
    if state == 'PENDING' or (role != 'OWNER' and approval_required) or (reject and role != 'OWNER'):
        raise PricingError('owner_approval_required')
    audit_reason(reason)
    if reject:
        one("UPDATE public.pricing_operations SET state='REJECTED',approved_by=%s,approved_at=now(),reason=%s "
            'WHERE id=%s AND org_id=%s RETURNING id',[actor_id,reason,operation_id,org_id])
        return operation_public(one('SELECT * FROM public.pricing_operations WHERE id=%s AND org_id=%s',
                                    [operation_id,org_id]))
    project = one('SELECT * FROM public.projects WHERE id=%s AND org_id=%s FOR UPDATE',
                  [operation['project_id'],org_id])
    positions = rows('SELECT * FROM public.project_positions WHERE project_id=%s AND org_id=%s '
                     'ORDER BY position_index FOR UPDATE',[project['id'],org_id])
    if (project['status'] != 'DRAFT'
            or (operation.get('revision_code') or 'REV-A') != project['current_revision']
            or source_revision(project,positions) != operation['source_revision']):
        raise PricingError('stale_pricing_operation')
    output = decoded(operation['result'])
    snapshot = decoded(operation['input_snapshot'])
    if role != 'OWNER' and snapshot.get('approval_policy'):
        from dekopen_engine.price_workspace import policy
        rows("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",[str(org_id)+':pricing_rules'])
        live_rules = one('SELECT * FROM public.pricing_rules WHERE org_id=%s',[org_id])
        live_decision = policy(cost=D(str(output['workspace']['cascade']['cost'])),net=D(str(output['project_net'])),
            minimum=live_rules['minimum_margin_pct'],maximum=live_rules['maximum_margin_pct'],
            discount=D(str(request['discount_pct'])),discount_limit=live_rules['discount_approval_pct'])
        if live_decision['requires_approval']:
            raise PricingError('owner_approval_required')
    if 'extra_policy' in snapshot:
        from projects.extras import policy_record, lock_policy
        lock_policy(org_id)
        if policy_record(org_id) != snapshot['extra_policy']:
            raise PricingError('stale_pricing_operation')
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
                       [sum(costs.values(),D('0'))+D(str(output.get('services_cost','0'))),output['project_net'],output['project_tax'],
                        output['project_gross'],project['id'],org_id])
        cursor.execute("UPDATE public.pricing_operations SET state='APPLIED',approved_by=%s,approved_at=clock_timestamp(),reason=%s "
                       'WHERE id=%s AND org_id=%s',[actor_id,reason,operation_id,org_id])
    return operation_public(one('SELECT * FROM public.pricing_operations WHERE id=%s AND org_id=%s',
                                [operation_id,org_id]))


def withdraw_operation(org_id, actor_id, role, operation_id, reason):
    """A PENDING request the requester no longer wants reviewed — or the owner
    clearing the queue — must not stay actionable forever."""
    operation = one('SELECT * FROM public.pricing_operations WHERE id=%s AND org_id=%s FOR UPDATE',
                    [operation_id,org_id],'pricing_operation_not_found')
    if role not in ('OWNER','ESTIMATOR') or (role != 'OWNER' and operation['requested_by'] != actor_id):
        raise PricingError('pricing_permission_denied')
    if operation['state'] != 'PENDING':
        raise PricingError('operation_not_withdrawable')
    audit_reason(reason)
    one("UPDATE public.pricing_operations SET state='WITHDRAWN',approved_by=%s,approved_at=clock_timestamp(),"
        'reason=%s WHERE id=%s AND org_id=%s RETURNING id',
        [actor_id,reason,operation_id,org_id])
    return operation_public(one('SELECT * FROM public.pricing_operations WHERE id=%s AND org_id=%s',
                                [operation_id,org_id]))
