"""Frozen authority resolver for pure commercial counterfactual replay."""

from copy import deepcopy
from decimal import Decimal

from django.db import connection

from dekopen_engine.commercial import PricingError, convert_cost
from dekopen_engine.cutting import StockRule, MissingStockAuthority, AmbiguousStockAuthority
from dekopen_engine.models import SystemParams, EffectiveProfileArticle
from engine_api.cutting_repository import CuttingRepository
from engine_api.repository import SystemParamsRepository
from pricing.repository import rows, json_text


def financial_bundle(repo):
    return {
        'costs': rows('SELECT i.id,i.sku,i.unit,i.unit_cost,l.id AS cost_list_id,l.currency,l.valid_from,l.valid_to '
            'FROM public.cost_list_items i JOIN public.cost_lists l ON l.id=i.cost_list_id AND l.org_id=i.org_id '
            'WHERE i.org_id=%s AND l.is_active AND l.valid_from<=%s '
            'AND (l.valid_to IS NULL OR l.valid_to>=%s) ORDER BY l.valid_from DESC',
            [repo.org_id,repo.effective_date,repo.effective_date]),
        'demo': rows('SELECT p.* FROM public.catalog_demo_prices p JOIN public.profile_systems s ON s.id=p.system_id '
            'WHERE p.org_id IS NULL AND p.is_demo AND s.is_demo AND s.is_global AND s.is_active'),
        'configurations': rows('SELECT * FROM public.pricing_configurations WHERE org_id=%s AND is_active',[repo.org_id]),
        'matrix': rows('SELECT * FROM public.pricing_matrix_cells WHERE org_id=%s',[repo.org_id]),
        'fx': rows('SELECT * FROM public.pricing_fx_snapshots WHERE org_id=%s',[repo.org_id]),
    }


def technical_bundle(repo, system_id):
    key = str(system_id)
    if key in repo.technical:
        return repo.technical[key]
    params = SystemParamsRepository().load_visible(system_id,repo.org_id)
    system_identity = rows('SELECT is_demo FROM public.profile_systems WHERE id=%s',[system_id])
    couplers = SystemParamsRepository().load_coupler_articles(system_id,repo.org_id)
    profiles = rows('SELECT sku FROM public.profile_articles WHERE system_id=%s '
                    'AND (org_id=%s OR org_id IS NULL)',[system_id,repo.org_id])
    steel = rows('SELECT r.sku,p.sku AS parent FROM public.reinforcement_articles r '
        'JOIN public.profile_articles p ON p.id=r.parent_profile_article_id '
        'WHERE r.system_id=%s AND r.is_active AND (r.org_id=%s OR r.org_id IS NULL)',[system_id,repo.org_id])
    stocks, reinforcements = {}, {}
    source = CuttingRepository()
    for color in params.finishes:
        for article in profiles:
            try:
                stock = source.profile_stock(system_id,repo.org_id,article['sku'],color)
            except (MissingStockAuthority,AmbiguousStockAuthority):
                continue  # An unusable mapping remains absent; replay must reject its use.
            stocks[f"{color}|{article['sku']}"] = stock.model_dump(mode='json')
        for article in steel:
            try:
                stock, _ = source.reinforcement_stock(system_id,repo.org_id,article['parent'],article['sku'],color)
            except (MissingStockAuthority,AmbiguousStockAuthority):
                continue
            reinforcements[f"{color}|{article['parent']}|{article['sku']}"] = stock.model_dump(mode='json')
        for parent in {article['parent'] for article in steel}:
            try:
                stock,_ = source.reinforcement_stock(system_id,repo.org_id,parent,None,color)
            except (MissingStockAuthority,AmbiguousStockAuthority):
                continue
            reinforcements[f'{color}|{parent}|None'] = stock.model_dump(mode='json')
    result = {'params':params.model_dump(mode='json'),'demo':bool(system_identity and system_identity[0]['is_demo']),
              'couplers':{sku:value.model_dump(mode='json') for sku,value in couplers.items()},
              'stocks':stocks,'reinforcements':reinforcements}
    repo.technical[key] = result
    return result


def technical_values(bundle):
    return (SystemParams.model_validate_json(json_text(bundle['params'])),
            {sku:EffectiveProfileArticle.model_validate_json(json_text(value)) for sku,value in bundle['couplers'].items()},
            {key:StockRule.model_validate_json(json_text(value)) for key,value in bundle['stocks'].items()},
            {key:StockRule.model_validate_json(json_text(value)) for key,value in bundle['reinforcements'].items()})


class FrozenPricingRepository:
    """No connection access. Missing historical facts are a refusal, never today's rate."""

    frozen = True

    def __init__(self, org_id, currency, bundle, technical, fx_id=None):
        self.org_id, self.currency = org_id, currency
        self.bundle, self.technical, self.fx_id = bundle, technical, str(fx_id) if fx_id else None
        self.authorities = []

    def convert(self, value, currency):
        rate = None
        if currency != self.currency:
            found = [row for row in self.bundle['fx'] if str(row['id']) == self.fx_id
                     and row['base_currency'] == currency and row['quote_currency'] == self.currency]
            if len(found) != 1:
                raise PricingError('incomplete_repricing_evidence')
            rate = Decimal(str(found[0]['observed_rate']))
        return convert_cost(Decimal(str(value)),currency,self.currency,rate)

    def cost(self, sku, required_unit):
        found = [row for row in self.bundle['costs'] if row['sku'] == sku]
        if found:
            found = [row for row in found if row['valid_from'] == found[0]['valid_from']]
        else:
            found = [row for row in self.bundle['demo'] if row['sku'] == sku]
        if len(found) != 1:
            raise PricingError('incomplete_repricing_evidence')
        item = found[0]
        if item['unit'].upper() != required_unit.upper():
            raise PricingError('incompatible_cost_unit')
        return self.convert(item['unit_cost'],item['currency'])

    def configuration(self, mode, context, typology):
        found = [item for item in self.bundle['configurations'] if item['pricing_mode'] == mode
                 and item['context_code'] == context and item['typology'] == typology]
        if len(found) != 1:
            raise PricingError('incomplete_repricing_evidence')
        return found[0]

    def matrix(self, configuration):
        return {(item['width_mm'],item['height_mm']):self.convert(item['price'],configuration['currency'])
                for item in self.bundle['matrix'] if str(item['configuration_id']) == str(configuration['id'])}


def safe_technical(repo, system_id):
    if getattr(repo,'frozen',False):
        if str(system_id) not in repo.technical:
            raise PricingError('incomplete_repricing_evidence')
        return technical_values(repo.technical[str(system_id)])
    with connection.cursor() as cursor:
        cursor.execute('SET LOCAL ROLE authenticated')
    try:
        return technical_values(technical_bundle(repo,system_id))
    finally:
        from authentication.rls import tx_aborted
        if not tx_aborted():
            with connection.cursor() as cursor:
                cursor.execute('SET LOCAL ROLE pricing_backend')


def frozen_copy(value):
    # Numeric strings and date/UUID strings are portable; Decimal(float) is forbidden.
    import json
    return deepcopy(json.loads(json_text(value),parse_float=Decimal))
