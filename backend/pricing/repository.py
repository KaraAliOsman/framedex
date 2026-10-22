"""Resolved commercial authorities inside verified, transaction-local RLS."""

from collections import defaultdict
from contextlib import contextmanager
from datetime import date
from decimal import Decimal
import json
from uuid import UUID

from django.db import connection, DatabaseError

from authentication.rls import authenticated_read, tx_aborted
from psycopg import sql

from dekopen_engine.commercial import PricingError, convert_cost


def encode(value):
    if isinstance(value, (Decimal, UUID, date)):
        return str(value)
    raise TypeError(f'Unsupported persisted type: {type(value).__name__}')


def json_text(value):
    return json.dumps(value, default=encode, sort_keys=True, separators=(',', ':'), allow_nan=False)


def rows(query, parameters=()):
    with connection.cursor() as cursor:
        cursor.execute(query, parameters)
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


def write(query, parameters=()):
    """Statement without a row result — returns rowcount.
    `rows()` is SELECT-only: `cursor.description` is None on writes."""
    with connection.cursor() as cursor:
        cursor.execute(query, parameters)
        return cursor.rowcount


def one(query, parameters=(), code='authority_not_found'):
    result = rows(query, parameters)
    if len(result) != 1:
        raise PricingError('ambiguous_authority' if result else code)
    return result[0]


def demo_cost_rows():
    """Synthetic prices also resolve the demo's declared purchase identities.

    Copy the existing exact price; never derive a rate from a code prefix or
    extend a workshop mapping into the platform's example price list.
    """
    prices = rows('SELECT p.* FROM public.catalog_demo_prices p JOIN public.profile_systems s ON s.id=p.system_id '
        'WHERE p.org_id IS NULL AND p.is_demo AND s.is_demo AND s.is_global AND s.is_active')
    with authenticated_read():
        aliases = rows('SELECT a.system_id,a.sku,m.commercial_sku FROM public.profile_articles a '
            'JOIN public.profile_systems s ON s.id=a.system_id JOIN public.profile_purchase_mappings m ON m.profile_article_id=a.id '
            'WHERE s.org_id IS NULL AND s.is_global AND s.is_demo AND s.is_active AND a.org_id IS NULL AND m.org_id IS NULL AND m.is_active '
            'UNION SELECT r.system_id,r.sku,r.commercial_sku FROM public.reinforcement_articles r JOIN public.profile_systems s ON s.id=r.system_id '
            'WHERE s.org_id IS NULL AND s.is_global AND s.is_demo AND s.is_active AND r.org_id IS NULL AND r.is_active')
    direct = {item['sku'] for item in prices}
    output = {(item['sku'], str(item['id'])): item for item in prices}
    by_series_sku = defaultdict(list)
    for price in prices:
        by_series_sku[(price['system_id'], price['sku'])].append(price)
    for alias in aliases:
        if alias['commercial_sku'] in direct:
            continue
        for price in by_series_sku[(alias['system_id'], alias['sku'])]:
            copied = {**price, 'sku': alias['commercial_sku']}
            output[(copied['sku'], str(copied['id']))] = copied
    return list(output.values())


def audit_reason(reason: str):
    if not reason.strip():
        raise PricingError('audit_reason_required')
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config('app.pricing_reason',%s,true)", [reason])


@contextmanager
def commercial_backend():
    # Session user is trusted; clients never receive membership in this role.
    # Its own tenant RLS policies remain active and JWT claims remain unchanged.
    with connection.cursor() as cursor:
        cursor.execute('SET LOCAL ROLE pricing_backend')
    try:
        yield
    except DatabaseError:
        # A PostgreSQL statement error aborts the transaction even when Django
        # has not marked needs_rollback yet. Do not mask it with SET ROLE.
        raise
    except BaseException:
        if not tx_aborted():
            with connection.cursor() as cursor:
                cursor.execute('SET LOCAL ROLE authenticated')
        raise
    else:
        if not tx_aborted():
            with connection.cursor() as cursor:
                cursor.execute('SET LOCAL ROLE authenticated')


class PricingRepository:
    def __init__(self, org_id, effective_date: date, currency: str, fx_id=None, *, request_cache=False):
        self.org_id = org_id
        self.effective_date = effective_date
        self.currency = currency
        self.fx_id = fx_id
        self.authorities = []
        self.technical = {}
        self.technical_values = {}
        # Opt-in only for one repeatable-read proposal. An ordinary repository
        # continues to observe edits between transactions.
        self._query_cache = {} if request_cache else None
        self.financial = None

    def preload_costs(self, bundle):
        if self._query_cache is None:
            raise ValueError('Cost prefetch requires a request-scoped repository')
        self.financial = bundle
        self._cost_candidates = {}
        self._demo_candidates = {}
        for kind, target in [('costs', self._cost_candidates), ('demo', self._demo_candidates)]:
            for item in bundle[kind]:
                target.setdefault(item['sku'], []).append(item)

    def _rows(self, query, parameters):
        if self._query_cache is None:
            return rows(query, parameters)
        key = (query, tuple(parameters))
        if key not in self._query_cache:
            self._query_cache[key] = rows(query, parameters)
        return self._query_cache[key]

    def _one(self, query, parameters, code):
        result = self._rows(query, parameters)
        if len(result) != 1:
            raise PricingError('ambiguous_authority' if result else code)
        return result[0]

    def convert(self, value, currency):
        snapshot = None
        if currency != self.currency:
            if self.fx_id is None:
                raise PricingError('missing_fx_authority')
            snapshot = self._one(
                'SELECT * FROM public.pricing_fx_snapshots WHERE id=%s AND org_id=%s '
                'AND effective_date=%s AND base_currency=%s AND quote_currency=%s',
                [self.fx_id,self.org_id,self.effective_date,'USD','CLP'],
                'missing_fx_authority')
            self.authorities.append({'fx': snapshot})
        return convert_cost(value,currency,self.currency,
                            None if snapshot is None else snapshot['observed_rate'])

    def cost(self, sku: str, required_unit: str):
        candidates = self._cost_candidates.get(sku, []) if self.financial is not None else self._rows(
            'SELECT i.id,i.sku,i.unit,i.unit_cost,l.id AS cost_list_id,l.currency,l.valid_from,l.valid_to '
            'FROM public.cost_list_items i JOIN public.cost_lists l '
            'ON l.id=i.cost_list_id AND l.org_id=i.org_id '
            'WHERE i.org_id=%s AND i.sku=%s AND l.is_active AND l.valid_from<=%s '
            'AND (l.valid_to IS NULL OR l.valid_to>=%s) ORDER BY l.valid_from DESC',
            [self.org_id,sku,self.effective_date,self.effective_date])
        if not candidates:
            demo = self._demo_candidates.get(sku, []) if self.financial is not None else [
                item for item in demo_cost_rows() if item['sku'] == sku]
            if not demo:
                raise PricingError('cost_list_not_found')
            if len(demo) != 1:
                raise PricingError('ambiguous_cost_list')
            value = {key: demo[0][key] for key in
                     ('id','sku','unit','unit_cost','currency','system_id','is_demo','seed','source')}
            if value['unit'].upper() != required_unit.upper():
                raise PricingError('incompatible_cost_unit')
            self.authorities.append({'cost': value})
            return self.convert(value['unit_cost'],value['currency'])
        latest = [item for item in candidates if item['valid_from'] == candidates[0]['valid_from']]
        if len(latest) != 1:
            raise PricingError('ambiguous_cost_list')
        value = latest[0]
        if value['unit'].upper() != required_unit.upper():
            raise PricingError('incompatible_cost_unit')
        self.authorities.append({'cost': value})
        return self.convert(value['unit_cost'],value['currency'])

    def configuration(self, mode, context, typology):
        config = self._one(
            'SELECT * FROM public.pricing_configurations WHERE org_id=%s AND pricing_mode=%s '
            'AND context_code=%s AND typology=%s AND is_active',
            [self.org_id,mode,context,typology], 'pricing_configuration_not_found')
        self.authorities.append({'configuration': config})
        return config

    def matrix(self, configuration):
        cells = self._rows('SELECT width_mm,height_mm,price FROM public.pricing_matrix_cells '
                     'WHERE org_id=%s AND configuration_id=%s',
                     [self.org_id,configuration['id']])
        self.authorities.append({'cells': cells})
        return {(cell['width_mm'],cell['height_mm']): self.convert(cell['price'],configuration['currency'])
                for cell in cells}


ADMIN_TABLES = {
    'cost-lists': ('cost_lists', ('supplier_name','description','currency','valid_from','valid_to','is_active')),
    'cost-items': ('cost_list_items', ('cost_list_id','sku','description','item_type','unit','unit_cost')),
    'rules': ('pricing_rules', ('pricing_mode','default_margin_pct','tax_rate_pct','waste_factor_pct',
                              'labor_rate_per_m2','installation_rate_per_m2','minimum_margin_pct',
                              'maximum_margin_pct','discount_approval_pct')),
    'configurations': ('pricing_configurations', ('context_code','typology','pricing_mode','currency',
                                                'rate_per_m2','base_glass_sku','catalog_price','is_active')),
    'matrix-cells': ('pricing_matrix_cells', ('configuration_id','width_mm','height_mm','price')),
    'fx': ('pricing_fx_snapshots', ('base_currency','quote_currency','observed_rate',
                                 'observed_date','effective_date','source')),
}


def admin_list(resource, org_id):
    if resource == 'demo-costs':
        return rows('SELECT p.*,s.name AS system_name,s.code AS system_code '
                    'FROM public.catalog_demo_prices p JOIN public.profile_systems s ON s.id=p.system_id '
                    'WHERE p.is_demo AND s.is_demo AND s.is_global AND s.is_active ORDER BY s.code,p.sku')
    if resource == 'audits':
        return rows('SELECT l.*, p.code AS project_code, p.name AS project_name '
                    'FROM public.price_audit_logs l '
                    'LEFT JOIN public.projects p ON p.id=l.project_id AND p.org_id=l.org_id '
                    'WHERE l.org_id=%s ORDER BY l.created_at DESC,l.id LIMIT 200', [org_id])
    if resource == 'coverage':
        from pricing.coverage import catalog_coverage
        return catalog_coverage(org_id)
    if resource not in ADMIN_TABLES:
        raise PricingError('unknown_pricing_resource')
    table, _ = ADMIN_TABLES[resource]
    return rows(sql.SQL('SELECT * FROM public.{} WHERE org_id=%s ORDER BY id').format(sql.Identifier(table)), [org_id])


def admin_write(resource, org_id, values, reason, row_id=None):
    if resource not in ADMIN_TABLES:
        raise PricingError('unknown_pricing_resource')
    if resource == 'fx' and row_id is not None:
        raise PricingError('fx_snapshot_immutable')
    table, fields = ADMIN_TABLES[resource]
    data = {key: value for key,value in values.items() if key in fields}
    if not data or set(values)-set(fields):
        raise PricingError('invalid_admin_fields')
    audit_reason(reason)
    if row_id is None:
        data['org_id'] = org_id
        statement = sql.SQL('INSERT INTO public.{} ({}) VALUES ({}) RETURNING *').format(
            sql.Identifier(table),sql.SQL(',').join(map(sql.Identifier,data)),
            sql.SQL(',').join(sql.Placeholder() for _ in data))
        return one(statement,list(data.values()))
    statement = sql.SQL('UPDATE public.{} SET {} WHERE id=%s AND org_id=%s RETURNING *').format(
        sql.Identifier(table),sql.SQL(',').join(sql.SQL('{}=%s').format(sql.Identifier(key)) for key in data))
    return one(statement,[*data.values(),row_id,org_id])
