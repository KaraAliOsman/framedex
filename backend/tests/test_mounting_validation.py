"""Reject extra survey work before parsing individual entries."""
from unittest.mock import patch

import pytest
from rest_framework import serializers

from projects.serializers import validate_measurement_input


@pytest.mark.parametrize('tree', [
    {'type':'BAY','id':'one'},
    {'version':'product-v2','assembly':{'modules':[{'id':'one'},{'id':'two'}]}},
])
def test_oversized_measurements_are_rejected_before_model_validation(tree):
    with patch('pydantic.TypeAdapter', side_effect=AssertionError('Must reject before parsing')):
        with pytest.raises(serializers.ValidationError, match='por marco'):
            validate_measurement_input([None]*10000, {'parametric_tree':tree})
