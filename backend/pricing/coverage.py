"""Cost coverage uses the purchasing identities consumed by the calculator."""

from datetime import datetime
import json
from zoneinfo import ZoneInfo

from pricing.repository import rows


def catalog_coverage(org_id):
    catalog = {}

    def add(sku, name, kind, unit, *, blocker=None):
        if sku:
            catalog[(kind, sku, unit)] = {'sku': sku, 'name': name, 'kind': kind,
                'required_unit': unit, 'blocker': blocker}

    profiles = rows('SELECT a.id,a.sku,a.name,a.commercial_length_mm,s.finish_authority '
        'FROM profile_articles a JOIN profile_systems s ON s.id=a.system_id '
        'WHERE s.is_active AND (a.org_id=%s OR a.org_id IS NULL)', [org_id])
    for profile in profiles:
        table = 'catalog_color_skus' if profile['finish_authority'] is not None else 'profile_purchase_mappings'
        physical = ' AND stock_color=finish' if table == 'catalog_color_skus' else ''
        mappings = rows(f'SELECT commercial_sku,org_id,purchase_unit FROM {table} '
            f'WHERE profile_article_id=%s AND is_active AND (org_id=%s OR org_id IS NULL){physical}',
            [profile['id'], org_id])
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
        'WHERE a.is_active AND s.is_active AND (a.org_id=%s OR a.org_id IS NULL)', [org_id]):
        add(item['commercial_sku'], item['name'], 'REINFORCEMENT', 'BAR',
            blocker='Falta declarar largo y compra de barra.' if item['purchase_unit'] != 'BAR' or not item['stock_length_mm'] else None)
    for item in rows('SELECT g.technical_sku,g.glass_spec,c.product FROM glass_purchase_mappings g '
        'JOIN profile_systems s ON s.id=g.system_id LEFT JOIN catalog_glass_compositions c ON c.mapping_id=g.id '
        'WHERE s.is_active AND (g.org_id=%s OR g.org_id IS NULL) AND NOT EXISTS '
        '(SELECT 1 FROM catalog_glass_retractions r WHERE r.mapping_id=g.id)', [org_id]):
        add(item['technical_sku'], item['glass_spec'] or 'Vidrio', 'GLASS', 'M2')
        product = json.loads(item['product']) if isinstance(item['product'],str) else item['product']
        billing = (product or {}).get('billing') or {}
        for field, unit in {'tempering_sku':'M2','polishing_sku':'M','drilling_sku':'EA',
                            'bars_per_m_sku':'M','bars_per_crossing_sku':'EA'}.items():
            add(billing.get(field), 'Proceso o palillaje de vidrio', 'GLASS', unit)
    for item in rows('SELECT a.sku,a.name FROM infill_articles a JOIN profile_systems s ON s.id=a.system_id '
        'WHERE a.is_active AND s.is_active AND (a.org_id=%s OR a.org_id IS NULL)', [org_id]):
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
        'AND (a.org_id=%s OR a.org_id IS NULL)', [org_id]):
        if item['class_authority']:
            authority = json.loads(item['class_authority']) if isinstance(item['class_authority'],str) else item['class_authority']
            hardware(authority)
        else:
            add(item['sku'], item['name'], 'HARDWARE', 'KIT')
    for item in rows('SELECT f.technical_sku FROM fitting_purchase_mappings f '
        'JOIN profile_systems s ON s.id=f.system_id WHERE s.is_active '
        'AND (f.org_id=%s OR f.org_id IS NULL)', [org_id]):
        add(item['technical_sku'], 'Fijación sin marco', 'FITTING', 'EA')
    today = datetime.now(ZoneInfo('America/Santiago')).date()
    costs = rows('SELECT i.sku,i.unit,l.valid_from FROM cost_list_items i '
        'JOIN cost_lists l ON l.id=i.cost_list_id AND l.org_id=i.org_id WHERE i.org_id=%s '
        'AND l.is_active AND l.valid_from<=%s AND (l.valid_to IS NULL OR l.valid_to>=%s)', [org_id,today,today])
    demo = rows('SELECT p.sku,p.unit FROM catalog_demo_prices p JOIN profile_systems s ON s.id=p.system_id '
        'WHERE p.org_id IS NULL AND p.is_demo AND s.is_demo AND s.is_global AND s.is_active')
    for item in catalog.values():
        found = [row for row in costs if row['sku'] == item['sku']]
        if found:
            latest = max(row['valid_from'] for row in found)
            found = [row for row in found if row['valid_from'] == latest]
        item['is_demo'] = not found and any(row['sku'] == item['sku'] for row in demo)
        if not found:
            found = [row for row in demo if row['sku'] == item['sku']]
        units = {'BAR','M'} if item['required_unit'] == 'BAR' else {item['required_unit']}
        item['active_cost_items'] = 1 if len(found) == 1 and found[0]['unit'] in units and not item['blocker'] else 0
        item['blocker'] = item['blocker'] or ('Hay costos vigentes ambiguos.' if len(found)>1
            else 'Falta un costo vigente con la unidad de compra correcta.' if not item['active_cost_items'] else None)
    return sorted(catalog.values(), key=lambda item:(item['active_cost_items'],item['kind'],item['sku']))
