"""The policy boundary accepts exact rates, never browser-provided material costs."""

from decimal import Decimal as D

import pytest

from pricing.simple_serializers import SimplePolicyValuesSerializer, SimplePolicyExampleRequestSerializer


def values(**changes):
    return {'currency': 'CLP', 'labor_rate': '15000.1234', 'labor_basis': 'M2',
        'installation_rate': '10000', 'installation_basis': 'WINDOW', 'margin': '.35',
        'rounding_step': '1000', 'waste': '0', 'tax_rate': '.19', 'use_advanced': False, **changes}


def test_policy_preserves_four_decimal_rates_and_explicit_zero():
    serializer = SimplePolicyValuesSerializer(data=values(installation_rate='0'))
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data['labor_rate'] == D('15000.1234')
    assert serializer.validated_data['installation_rate'] == D('0')


@pytest.mark.parametrize('changes', [
    {'margin': '1'}, {'margin': '-.0001'}, {'margin': 'NaN'}, {'labor_rate': '-1'},
    {'labor_rate': '1.00001'}, {'installation_rate': 'Infinity'}, {'labor_basis': 'BAR'},
    {'currency': 'EUR'}, {'rounding_step': '.5'}, {'rounding_step': '0'},
    {'currency': 'USD', 'rounding_step': '.015'}, {'tax_rate': '1.01'}, {'waste': '-.01'},
    {'org_id': 'other'}, {'revision': 5}, {'materials': ['1']},
])
def test_policy_rejects_inexact_invalid_or_server_owned_fields(changes):
    assert not SimplePolicyValuesSerializer(data=values(**changes)).is_valid()


def test_example_cannot_supply_cost_or_impersonate_an_actor():
    assert SimplePolicyExampleRequestSerializer(data={'values': values()}).is_valid()
    for extra in ({'cost': '1'}, {'actor_id': 'other'}, {'project_net': '1'}):
        assert not SimplePolicyExampleRequestSerializer(data={'values': values(), **extra}).is_valid()
