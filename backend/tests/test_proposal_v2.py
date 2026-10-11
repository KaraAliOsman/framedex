"""Consent contract and public projection: sealed tax, extras and currency."""
from decimal import Decimal as D
from uuid import uuid4

import pytest

from portal.proposal import commercial_projection
from portal.serializers import DecideRequestSerializer, PortalPayRequestSerializer


def decision(**changes):
    return {'decision':'APPROVED','decided_by':'Ana Pérez','decided_rut':'12.345.678-5',
        'selected_revision':'REV-B','expected_offering_sha256':'a'*64,'expected_selected_sha256':'b'*64,
        'confirmed':True,'consent_text':'Acepto la propuesta sellada',**changes}


@pytest.mark.parametrize('changes,field',[
    ({'decided_by':''},'decided_by'),({'decided_rut':'12.345.678-0'},'decided_rut'),
    ({'decided_rut':''},'decided_rut'),({'confirmed':False},'confirmed'),
    ({'consent_text':''},'confirmed'),({'expected_selected_sha256':'partial'},'expected_selected_sha256'),
    ({'selected_revision':'REV-1'},'selected_revision'),({'extra':'tenant'},'non_field_errors')])
def test_acceptance_needs_identity_explicit_consent_and_exact_fingerprint(changes,field):
    serializer=DecideRequestSerializer(data=decision(**changes))
    assert not serializer.is_valid() and field in serializer.errors


def test_changes_require_comment_and_decline_can_omit_identity_and_reason():
    serializer=DecideRequestSerializer(data=decision(decision='CHANGES_REQUESTED',note=''))
    assert not serializer.is_valid() and 'note' in serializer.errors
    serializer=DecideRequestSerializer(data=decision(decision='CHANGES_REQUESTED',note='Cambiar posición 4',position_id=str(uuid4()),decided_by='',decided_rut='',confirmed=False))
    assert serializer.is_valid(),serializer.errors
    serializer=DecideRequestSerializer(data=decision(decision='DECLINED',decided_by='',decided_rut='',confirmed=False))
    assert serializer.is_valid(),serializer.errors


@pytest.mark.parametrize('amount',['0','-1','1.01','NaN','Infinity'])
def test_payer_amount_is_integer_positive_clp(amount):
    serializer=PortalPayRequestSerializer(data={'operation_key':str(uuid4()),'amount':amount,'payer_email':'ana@example.test'})
    assert not serializer.is_valid()


def test_missing_commercial_authority_is_unknown_and_never_zero():
    result=commercial_projection({'revision_code':'REV-A','snapshot_json':{'project':{'code':'P-000001'}}},
        [{'id':str(uuid4()),'quantity':1,'price_net':None}])
    assert result['display_total_gross'] is None and result['price_cause']
    assert result['positions'][0]['unit_price_gross'] is None and result['consent_text'] is None


def test_projection_does_not_leak_costs_or_assume_tax_rate():
    source={'project':{'code':'P-000001','currency':'USD','total_price_net':'100','total_price_tax':'7','total_price_gross':'107'},
            'pricing':{'request':{'extras':[{'label':'Despacho','amount':'10'}]},
                       'result':{'services':[{'label':'Instalación','amount':'20','cost':'secret'}],'project_cost':'secret'}}}
    result=commercial_projection({'revision_code':'REV-B','snapshot_json':source},[{'id':'p','quantity':2,'price_net':'70'}])
    assert result['positions'][0]['unit_price_gross']=='37.45'
    assert D(result['positions'][0]['line_price_gross'])+sum(D(item['line_price_gross']) for item in result['extras'])==D('107')
    assert 'secret' not in str(result) and 'US$ 107,00' in result['consent_text']
