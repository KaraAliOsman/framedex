import pytest

from engine.tests.thermal_cases import reports
from projects.thermal_views import ThermalAuthoritySerializer


@pytest.mark.parametrize("url", ["ftp://example.test/informe", "file:///informe", "javascript:alert(1)"])
def test_source_url_rejects_non_http_before_database_write(url):
    fields = set(ThermalAuthoritySerializer().fields)
    data = reports()[0].model_dump(mode="json", include=fields)
    data["source_url"] = url
    serializer = ThermalAuthoritySerializer(data=data)
    assert not serializer.is_valid() and "source_url" in serializer.errors


def test_source_url_accepts_original_https_document():
    fields = set(ThermalAuthoritySerializer().fields)
    data = reports()[0].model_dump(mode="json", include=fields)
    assert ThermalAuthoritySerializer(data=data).is_valid()
