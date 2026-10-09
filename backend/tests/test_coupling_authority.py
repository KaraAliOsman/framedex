from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from backend.tests.test_engine_assembly import COUPLER_ARTICLE, bow_product, bow_request, configure_assembly_api
from catalogs.serializers import ArticleWriteSerializer
from dekopen_engine.models import CouplerRule


@pytest.mark.parametrize('angle,valid', [('0',True),('22.5',True),('-22.5',True),('60',True),('89',False)])
def test_api_angular_limits_are_sourced_and_errors_address_each_joint(monkeypatch, angle, valid):
    rule = CouplerRule(min_angle_deg=Decimal('0'),max_angle_deg=Decimal('60'),
                       development_mm=Decimal('24'),source='Ficha fixture, página 2')
    article = COUPLER_ARTICLE.model_copy(update={'coupling_rule':rule})
    client = APIClient()
    configure_assembly_api(client,monkeypatch,{article.sku:article})
    response = client.post('/api/v1/engine/assembly/calculate/',
                           bow_request(bow_product(angle,article.sku)),format='json')
    assert response.status_code == 200, response.content
    value = response.json()
    if valid:
        assert value['status'] == 'VALID'
        assert value['measures']['developed_width_mm'] == '2148.00'
        assert value['elevation']['width_mm'] == '2148.00'
    else:
        errors = [issue for issue in value['issues'] if issue['code']=='coupler_angle_incompatible']
        assert {issue['target'] for issue in errors} == {'coupling:c1','coupling:c2'}
        assert all(issue['params']['field']=='coupler_profile_sku' for issue in errors)
        assert value.get('measures') is None


@pytest.mark.parametrize('rule', [
    {'min_angle_deg':'30','max_angle_deg':'15','development_mm':'0','source':'Fuente'},
    {'min_angle_deg':'0','max_angle_deg':'60','development_mm':'-1','source':'Fuente'},
    {'min_angle_deg':'0','max_angle_deg':'60','development_mm':'0','source':' '},
])
def test_article_write_rejects_invalid_angular_authority(rule):
    data = ArticleWriteSerializer(data={'system_id':'00000000-0000-4000-8000-000000000001',
        'sku':'SOURCED','name':'Acoplador','role':'COUPLER','material':'PVC','face_width_mm':'40',
        'coupling_rule':rule})
    assert not data.is_valid()
    assert 'coupling_rule' in data.errors


def test_reviewed_catalog_interchange_keeps_coupling_authority():
    from ingest.catalog_template import candidate, export_csv, parse_structured
    from backend.tests.catalog_interchange_fixture import catalog_rows
    import json
    row = next(item for item in catalog_rows() if item['sheet'] == 'Perfiles')
    rule = {'min_angle_deg': '0.00', 'max_angle_deg': '60.00',
            'development_mm': '24.00', 'source': 'Ficha proveedor página 2'}
    values = {**row['values'], 'role': 'COUPLER', 'coupling_rule': json.dumps(rule)}
    authority = candidate('Perfiles', values, key='coupling', row=5, method='MANUAL')
    assert not authority['errors']
    restored = parse_structured('CSV', export_csv('Perfiles', [authority]))[0]
    assert restored['values']['coupling_rule'] == rule
