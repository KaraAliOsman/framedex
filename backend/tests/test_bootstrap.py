from django.conf import settings


def test_django_bootstrap_contract() -> None:
    assert settings.ROOT_URLCONF == "config.urls"
    assert "rest_framework" in settings.INSTALLED_APPS
    assert "drf_spectacular" in settings.INSTALLED_APPS
    assert settings.CORS_ALLOW_CREDENTIALS is False
    assert "x-organization-id" in settings.CORS_ALLOW_HEADERS
