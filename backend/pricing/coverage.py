"""Cost coverage uses the purchasing identities consumed by the calculator."""

from collections import defaultdict
from datetime import datetime
import json
from zoneinfo import ZoneInfo

from pricing.repository import commercial_backend, demo_cost_rows, rows


def catalog_coverage(org_id, *, system_id=None, effective_date=None, demo_prices=None):
    catalog = {}
    scope = ' AND s.id=%s' if system_id is not None else ''
    scoped = [org_id, system_id] if system_id is not None else [org_id]

    def add(sku, name, kind, unit, *, blocker=None):
        if sku:
            catalog[(kind, sku, unit)] = {'sku': sku, 'name': name, 'kind': kind,
                'required_unit': unit, 'blocker': blocker}

    profiles = rows('SELECT a.id,a.sku,a.name,a.commercial_length_mm,a.reinforcement_rule,s.finish_authority '
        'FROM profile_articles a JOIN profile_systems s ON s.id=a.system_id '
        'WHERE s.is_active AND (a.org_id=%s OR a.org_id IS NULL)' + scope, scoped)
    purchases = defaultdict(list)
    for table, uses_finishes in (('profile_purchase_mappings', False), ('catalog_color_skus', True)):
        profile_ids = [profile['id'] for profile in profiles if (profile['finish_authority'] is not None) == uses_finishes]
        if not profile_ids:
            continue
        physical = ' AND stock_color=finish' if uses_finishes else ''
        mappings = rows(f'SELECT profile_article_id,commercial_sku,org_id,purchase_unit FROM {table} '
            f'WHERE profile_article_id=ANY(%s::uuid[]) AND is_active AND (org_id=%s OR org_id IS NULL){physical}',
            [profile_ids, org_id])
        for mapping in mappings:
            purchases[mapping['profile_article_id']].append(mapping)
    for profile in profiles:
        rule = profile['reinforcement_rule']
        rule = json.loads(rule) if isinstance(rule, str) else rule
        if rule:
            add(rule.get('screw_sku'), 'Tornillo de refuerzo', 'FITTING', 'EA')
        mappings = purchases[profile['id']]
        local = [item for item in mappings if item['org_id'] == org_id]
        mappings = local or mappings
        if not mappings:
            add(profile['sku'], profile['name'], 'PROFILE', 'BAR', blocker='Falta declarar la compra de barra en el catálogo.')
        for mapping in mappings:
            blocker = ('Falta declarar una compra de barra con largo comercial.'
                if mapping['purchase_unit'] != 'BAR' or not profile['commercial_length_mm'] else None)
            add(mapping['commercial_sku'], profile['name'], 'PROFILE', 'BAR', blocker=blocker)
    for item in rows('SELECT a.commercial_sku,a.name,a.stock_length_mm,a.purchase_unit '
        'FROM reinforcement_articles a JOIN profile_systems s ON s.id=a.system_id '
        'WHERE a.is_active AND s.is_active AND (a.org_id=%s OR a.org_id IS NULL)' + scope, scoped):
        add(item['commercial_sku'], item['name'], 'REINFORCEMENT', 'BAR',
            blocker='Falta declarar largo y compra de barra.' if item['purchase_unit'] != 'BAR' or not item['stock_length_mm'] else None)
    for item in rows('SELECT g.technical_sku,g.glass_spec,c.product FROM glass_purchase_mappings g '
        'JOIN profile_systems s ON s.id=g.system_id LEFT JOIN catalog_glass_compositions c ON c.mapping_id=g.id '
        'WHERE s.is_active AND (g.org_id=%s OR g.org_id IS NULL) AND NOT EXISTS '
        '(SELECT 1 FROM catalog_glass_retractions r WHERE r.mapping_id=g.id)' + scope, scoped):
        add(item['technical_sku'], item['glass_spec'] or 'Vidrio', 'GLASS', 'M2')
        product = json.loads(item['product']) if isinstance(item['product'],str) else item['product']
        billing = (product or {}).get('billing') or {}
        for field, unit in {'tempering_sku':'M2','polishing_sku':'M','drilling_sku':'EA',
                            'bars_per_m_sku':'M','bars_per_crossing_sku':'EA'}.items():
            add(billing.get(field), 'Proceso o palillaje de vidrio', 'GLASS', unit)
    for item in rows('SELECT a.sku,a.name FROM infill_articles a JOIN profile_systems s ON s.id=a.system_id '
        'WHERE a.is_active AND s.is_active AND (a.org_id=%s OR a.org_id IS NULL)' + scope, scoped):
        add(item['sku'], item['name'], 'PANEL', 'M2')

    def hardware(value):
        if isinstance(value, list):
            for item in value:
                hardware(item)
        elif isinstance(value, dict):
            if value.get('sku') and value.get('price_unit'):
                add(value['sku'], value.get('name') or 'Componente de herraje', 'HARDWARE', value['price_unit'])
            else:
                for item in value.values():
                    hardware(item)
    for item in rows('SELECT a.sku,a.name,a.class_authority FROM hardware_kits a '
        'JOIN profile_systems s ON s.id=a.system_id WHERE a.is_active AND s.is_active '
        'AND (a.org_id=%s OR a.org_id IS NULL)' + scope, scoped):
        if item['class_authority']:
            authority = json.loads(item['class_authority']) if isinstance(item['class_authority'],str) else item['class_authority']
            hardware(authority)
        else:
            add(item['sku'], item['name'], 'HARDWARE', 'KIT')
    for item in rows('SELECT f.technical_sku FROM fitting_purchase_mappings f '
        'JOIN profile_systems s ON s.id=f.system_id WHERE s.is_active '
        'AND (f.org_id=%s OR f.org_id IS NULL)' + scope, scoped):
        add(item['technical_sku'], 'Fijación sin marco', 'FITTING', 'EA')
    today = effective_date or datetime.now(ZoneInfo('America/Santiago')).date()
    with commercial_backend():
        costs = rows('SELECT i.sku,i.unit,l.valid_from FROM cost_list_items i '
            'JOIN cost_lists l ON l.id=i.cost_list_id AND l.org_id=i.org_id WHERE i.org_id=%s '
            'AND l.is_active AND l.valid_from<=%s AND (l.valid_to IS NULL OR l.valid_to>=%s)', [org_id,today,today])
        demo = demo_cost_rows() if demo_prices is None else demo_prices
    costs_by_sku = defaultdict(list)
    demo_by_sku = defaultdict(list)
    for cost in costs:
        costs_by_sku[cost['sku']].append(cost)
    for cost in demo:
        demo_by_sku[cost['sku']].append(cost)
    for item in catalog.values():
        found = costs_by_sku[item['sku']]
        if found:
            latest = max(row['valid_from'] for row in found)
            found = [row for row in found if row['valid_from'] == latest]
        item['is_demo'] = not found and bool(demo_by_sku[item['sku']])
        if not found:
            found = demo_by_sku[item['sku']]
        units = {'BAR','M'} if item['required_unit'] == 'BAR' else {item['required_unit']}
        item['active_cost_items'] = 1 if len(found) == 1 and found[0]['unit'] in units and not item['blocker'] else 0
        item['blocker'] = item['blocker'] or ('Hay costos vigentes ambiguos.' if len(found)>1
            else 'Falta un costo vigente con la unidad de compra correcta.' if not item['active_cost_items'] else None)
    return sorted(catalog.values(), key=lambda item:(item['active_cost_items'],item['kind'],item['sku']))
