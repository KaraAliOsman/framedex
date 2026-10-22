"""Reversible draft prices. Formal commercial operations belong to issuance."""

from dataclasses import asdict
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.db import transaction
from django.utils import timezone

from authentication.errors import ContractAPIException
from dekopen_engine.commercial import CommercialLine, PricingError
from dekopen_engine.extra_models import ExtraLine
from dekopen_engine.extras import service_price, partition_price
from dekopen_engine.snapshot import result_payload
from dekopen_engine.cutting import InvalidCutContract
from engine_api.adapter import UnsupportedEngineContract
from engine_api.repository import UnsupportedCatalogContract, SystemNotFound
from pricing.repository import PricingRepository, commercial_backend, one, rows, json_text
from pricing.service import position_cost, preview, source_revision, pricing_public_detail, decoded
from pricing.simple_policy import engine_policy, read_policy
from dekopen_engine.simple_pricing import simple_price, simple_project

D = Decimal


def working_request(project_id, policy, effective_date):
    return {'project_id': project_id, 'pricing_mode': 'COST_PLUS_MARGIN', 'currency': policy['currency'],
        'effective_date': effective_date, 'context_code': 'DEFAULT', 'discount_pct': D('0'),
        'target_margin': policy['margin'], 'segment': 'RETAIL', 'confirmed': False,
        'reason': 'Precio vigente del borrador', 'simple_policy_revision': policy['revision']}


def calculate_simple(org_id, project, positions, values, request):
    from projects.extras import service_lines, policy_record, lock_policy
    from pricing.resolved import financial_bundle
    policy = engine_policy(values)
    repo = PricingRepository(org_id, request['effective_date'], policy.currency, request_cache=True)
    repo.preload_costs(financial_bundle(repo))
    lock_policy(org_id)
    extra_policy = policy_record(org_id)
    services = service_lines(org_id, project, positions, repo)
    explicit_installation = any(item.installation for item in services)
    # These rules resolve material/extra facts. Only simple_price adds the
    # declared service units and material waste to the base window.
    rules = {'waste_factor_pct': policy.waste, 'labor_rate_per_m2': D('0'),
        'installation_rate_per_m2': D('0'), 'default_margin_pct': policy.margin}
    technical, lines, details, extras_by_index = [], [], [], {}
    for position in positions:
        _, area, bom, formation = position_cost(repo, position, rules)
        extras = [ExtraLine.model_validate_json(json_text(item)) for item in formation['extra_lines']]
        if explicit_installation and any(item.installation for item in extras):
            raise PricingError('installation_rule_duplicate')
        priced = simple_price([D(item['cost']) for item in formation['composition'] if item['kind'] != 'EXTRA'],
            area, policy, installation_included=explicit_installation, extras=extras)
        index = position['position_index']
        extras_by_index[index] = extras
        lines.append(CommercialLine(index, position['quantity'], priced.direct_cost, priced.unit_net))
        technical.append({**formation, 'position_id': str(position['id']), 'position_index': index,
            'bom': result_payload(bom), 'unit_cost': str(priced.direct_cost),
            'unit_cost_exact': str(priced.direct_cost), 'simple_price': asdict(priced)})
        details.append({'position_index': index, 'quantity': position['quantity'], 'unit_price': str(priced.unit_net),
            'discount_pct': '0', 'breakdown': asdict(priced), 'catalog_use': formation.get('catalog_use', {})})
    priced_project = simple_project(lines, policy.currency, values['tax_rate'], services)
    # Extras retain the existing exact allocation contract for documentary sublines.
    for detail, line, (_, net) in zip(details, lines, priced_project.totals.lines, strict=True):
        extras = extras_by_index[line.position_index]
        if extras:
            from dekopen_engine.extras import base_price_weight
            detail.update(partition_price(net, base_price_weight(line.exact_unit_price, extras),
                [(item, item.total_price) for item in extras], quantity=line.quantity, currency=policy.currency))
    return {'request': request,
        'input_snapshot': {'rules': rules, 'workshop_policy': values, 'authorities': repo.authorities,
            'positions': technical, 'cost_lines': priced_project.cost_lines, 'extra_policy': extra_policy},
        'result': {**asdict(priced_project.totals), 'currency': policy.currency, 'line_detail': details,
            'services': [service_price(item, policy.currency) for item in services],
            'services_cost': priced_project.services_cost, 'total_cost': priced_project.total_cost,
            'document_extra_prices': extra_policy['policy']['document_prices']}}


@transaction.atomic
def refresh_working(org_id, actor, project_id):
    """Lock the draft and calculate its current costs without applying a price.

    Recalculates current costs rather than claiming a stale cache is authoritative.
    Hooks and public projection are activated by the subsequent P04 integration.
    """
    if actor.active_organization.role not in ('OWNER', 'ESTIMATOR') or actor.active_organization.organization_id != org_id:
        raise PricingError('pricing_permission_denied')
    with commercial_backend():
        project = one('SELECT * FROM public.projects WHERE id=%s AND org_id=%s FOR UPDATE', [project_id, org_id])
        if project['status'] != 'DRAFT' or rows('SELECT id FROM public.pricing_operations '
            "WHERE org_id=%s AND project_id=%s AND state='APPLIED' AND coalesce(revision_code,'REV-A')=%s "
            'AND (%s::timestamptz IS NULL OR approved_at>%s::timestamptz)',
            [org_id, project_id, project['current_revision'], project['pricing_reset_at'], project['pricing_reset_at']]):
            return None
        positions = rows('SELECT * FROM public.project_positions WHERE project_id=%s AND org_id=%s '
            'ORDER BY position_index FOR UPDATE', [project_id, org_id])
        values = read_policy(org_id)
        effective_date = timezone.localdate(timezone=ZoneInfo('America/Santiago'))
        request = working_request(project_id, values, effective_date)
        request['_actor_id'] = one("SELECT (nullif(current_setting('request.jwt.claims',true),'')::jsonb->>'sub')::uuid AS id")['id']
        state = 'READY'
        try:
            with transaction.atomic():
                if not positions:
                    raise PricingError('project_has_no_positions')
                if values['use_advanced']:
                    rules = one('SELECT * FROM public.pricing_rules WHERE org_id=%s', [org_id], 'pricing_rules_not_found')
                    advanced_request = {**request, 'pricing_mode': rules['pricing_mode'],
                        'target_margin': rules['default_margin_pct']}
                    # Workspace simulation keeps discount bands/approval and creates no operation.
                    projected = preview(org_id, actor, advanced_request, simulate=True, workspace=True)
                    state = 'PENDING' if projected['state'] == 'PENDING' else 'READY'
                    output = {'request': advanced_request, 'input_snapshot': {}, 'result': projected}
                else:
                    output = calculate_simple(org_id, project, positions, values, request)
        except (PricingError, ContractAPIException) as error:
            if isinstance(error, ContractAPIException) and error.status_code != 422:
                raise
            code = error.code if isinstance(error, PricingError) else error.contract_code
            detail = pricing_public_detail(code) if isinstance(error, PricingError) else error.public_detail
            state = 'BLOCKED'
            output = {'request': request, 'input_snapshot': {}, 'result': {'error': {'code': code, 'detail': detail}}}
        except (InvalidCutContract, UnsupportedEngineContract, UnsupportedCatalogContract, SystemNotFound):
            state = 'BLOCKED'
            output = {'request': request, 'input_snapshot': {}, 'result': {'error': {
                'code': 'technical_authority_required', 'detail': 'Revisa el diseño y los datos de su serie antes de cotizar.'}}}
        # A nested commercial resolver restores authenticated; re-enter only
        # after its savepoint has completed and before the private cache write.
    with commercial_backend():
        return one('INSERT INTO public.project_working_prices(org_id,project_id,revision_code,policy_revision,'
            'source_revision,effective_date,currency,state,request,input_snapshot,result) '
            'VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb) '
            'ON CONFLICT(project_id,revision_code) DO UPDATE SET policy_revision=excluded.policy_revision,'
            'source_revision=excluded.source_revision,effective_date=excluded.effective_date,currency=excluded.currency,'
            'state=excluded.state,request=excluded.request,input_snapshot=excluded.input_snapshot,result=excluded.result '
            'RETURNING *', [org_id, project_id, project['current_revision'], values['revision'],
                source_revision(project, positions), effective_date, request['currency'], state,
                json_text(output['request']), json_text(output['input_snapshot']), json_text(output['result'])])


def working_public(record, role):
    """Sale allowlist for estimators; private BOM/cost authority stays in the cache."""
    result = decoded(record['result'])
    public = {key: record[key] for key in ('state', 'currency', 'policy_revision', 'computed_at')}
    public['error'] = result.get('error')
    for key in ('project_net', 'project_tax', 'project_gross'):
        public[key] = str(result[key]) if key in result else None
    public['lines'] = [{key: item[key] for key in ('position_index', 'quantity', 'unit_price', 'discount_pct')}
        | {'line_net': str(dict(result.get('lines', []))[item['position_index']])}
        | ({'breakdown': item.get('breakdown'), 'catalog_use': item.get('catalog_use')} if role == 'OWNER' else {})
        for item in result.get('line_detail', [])]
    return public
