"""Tenant workshop policy and read-only example using the existing BOM resolver."""

from dataclasses import asdict
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.db import connection
from django.utils import timezone

from authentication.errors import contract_error
from dekopen_engine.simple_pricing import SimplePricingPolicy, simple_price
from dekopen_engine.commercial import CommercialLine, finish_lines
from dekopen_engine.extra_models import ExtraLine
from pricing.repository import PricingRepository, audit_reason, commercial_backend, one, rows, json_text

D = Decimal
POLICY_FIELDS = ('currency', 'labor_rate', 'labor_basis', 'installation_rate',
    'installation_basis', 'margin', 'rounding_step', 'waste', 'tax_rate', 'use_advanced')


def engine_policy(values):
    return SimplePricingPolicy(**{key: values[key] for key in POLICY_FIELDS
        if key not in ('tax_rate', 'use_advanced')})


def lock_policy(org_id):
    # Also serializes the first insert; a row lock alone cannot lock absence.
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
            [str(org_id) + ':workshop_pricing_policy'])


def read_policy(org_id, *, for_update=False):
    found = rows('SELECT * FROM public.workshop_pricing_policies WHERE org_id=%s' +
        (' FOR UPDATE' if for_update else ''), [org_id])
    if found:
        return {key: found[0][key] for key in (*POLICY_FIELDS, 'revision', 'updated_at')} | {
            'saved': True, 'suggested_fields': []}
    organization = one('SELECT currency FROM public.tenancy_organizations WHERE id=%s', [org_id])
    currency = organization['currency']
    historical = rows('SELECT * FROM public.pricing_rules WHERE org_id=%s', [org_id])
    rules = historical[0] if historical else {}
    # Editable suggestions for services, never manufacturer facts or BOM costs.
    return {'currency': currency,
        'labor_rate': rules.get('labor_rate_per_m2', D('15000') if currency == 'CLP' else D('0')),
        'labor_basis': 'M2',
        'installation_rate': rules.get('installation_rate_per_m2', D('10000') if currency == 'CLP' else D('0')),
        'installation_basis': 'M2', 'margin': rules.get('default_margin_pct', D('.35')),
        'rounding_step': D('1000') if currency == 'CLP' else D('.01'),
        'waste': rules.get('waste_factor_pct', D('0')), 'tax_rate': rules.get('tax_rate_pct', D('.19')),
        'use_advanced': False, 'revision': 0, 'updated_at': None, 'saved': False,
        'suggested_fields': list(POLICY_FIELDS)}


def save_policy(org_id, values, expected_revision, reason):
    engine_policy(values)
    lock_policy(org_id)
    current = read_policy(org_id, for_update=True)
    if current['revision'] != expected_revision:
        raise contract_error(409, 'stale_workshop_policy',
            'Los precios de tu empresa cambiaron. Recarga antes de guardar; conserva tus cambios para compararlos.')
    audit_reason(reason)
    parameters = [values[key] for key in POLICY_FIELDS]
    if current['saved']:
        one('UPDATE public.workshop_pricing_policies SET ' +
            ','.join(f'{key}=%s' for key in POLICY_FIELDS) + ' WHERE org_id=%s RETURNING id',
            [*parameters, org_id])
    else:
        one('INSERT INTO public.workshop_pricing_policies(org_id,' + ','.join(POLICY_FIELDS) +
            ') VALUES(' + ','.join(['%s'] * (len(POLICY_FIELDS) + 1)) + ') RETURNING id',
            [org_id, *parameters])
    return read_policy(org_id)


def policy_example(org_id, values, position_id=None):
    """No preview operation or prices are persisted by this endpoint."""
    from pricing.service import position_cost

    policy = engine_policy(values)
    with commercial_backend():
        condition = ' AND p.id=%s' if position_id else ''
        positions = rows('SELECT p.* FROM public.project_positions p JOIN public.projects work '
            'ON work.id=p.project_id AND work.org_id=p.org_id WHERE p.org_id=%s' + condition +
            " AND work.status='DRAFT' ORDER BY work.updated_at DESC,p.position_index LIMIT 1",
            [org_id, position_id] if position_id else [org_id])
        if not positions:
            if position_id:
                raise contract_error(404, 'pricing_example_not_found', 'Elige una ventana de una obra en borrador.')
            return {'position_id': None, 'position_index': None, 'currency': policy.currency,
                'breakdown': None, 'project_net': None, 'project_tax': None, 'project_gross': None,
                'assumptions': {}, 'detail': 'Crea una ventana para ver el precio con tus materiales.'}
        position = positions[0]
        repo = PricingRepository(org_id, timezone.localdate(timezone=ZoneInfo('America/Santiago')),
            policy.currency, request_cache=True)
        # Resolve all materials once through the established backend authority.
        # Zero services/waste here leave those additions to the simple engine.
        _, area, _, formation = position_cost(repo, position, {'waste_factor_pct': D('0'),
            'labor_rate_per_m2': D('0'), 'installation_rate_per_m2': D('0'),
            'default_margin_pct': values['margin']})
        extras = [ExtraLine.model_validate_json(json_text(item)) for item in formation['extra_lines']]
        price = simple_price([D(row['cost']) for row in formation['composition'] if row['kind'] != 'EXTRA'],
            area, policy, extras=extras)
        total = finish_lines([CommercialLine(position['position_index'], 1, price.direct_cost, price.unit_net)],
            policy.currency, values['tax_rate'])
    return {'position_id': position['id'], 'position_index': position['position_index'],
        'currency': policy.currency, 'breakdown': asdict(price), 'project_net': total.project_net,
        'project_tax': total.project_tax, 'project_gross': total.project_gross,
        'assumptions': formation.get('catalog_use', {}),
        'detail': 'Ejemplo de una unidad con materiales y medidas de tu obra; no modifica sus precios.'}


def example_preview(org_id, actor, request):
    return policy_example(org_id, request['values'], request.get('position_id'))
