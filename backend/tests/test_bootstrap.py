from django.conf import settings


def test_django_bootstrap_contract() -> None:
    assert settings.ROOT_URLCONF == "config.urls"
    assert settings.INSTALLED_APPS == []
