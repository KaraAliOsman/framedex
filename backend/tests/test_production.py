import os

from cryptography.exceptions import InvalidTag
from django.test import Client, override_settings
import pytest

from config.production import validate_production
from scripts.backup_database import encrypt, decrypt


def test_liveness_is_independent_and_readiness_rejects_missing_dependencies(django_db_blocker):
    client = Client()
    assert client.get('/health/live/').json() == {'status': 'alive'}
    assert client.post('/health/live/').status_code == 405
    with django_db_blocker.unblock(), override_settings(REDIS_URL=''):
        assert client.get('/health/ready/').status_code == 503


def test_production_configuration_rejects_development_defaults():
    with pytest.raises(ValueError):
        validate_production({'ENVIRONMENT': 'production'})
    environment = {
        'ENVIRONMENT': 'production', 'SECRET_KEY': 'a' * 64,
        'DATABASE_URL': 'postgresql://fixture/fixture', 'SUPABASE_URL': 'https://fixture.supabase.co',
        'SUPABASE_ANON_KEY': 'public-fixture', 'ALLOWED_HOSTS': 'api.example.com',
        'CORS_ALLOWED_ORIGINS': 'https://app.example.com', 'REDIS_URL': 'redis://fixture:6379',
    }
    validate_production(environment)
    for field, value in [('DEBUG', 'true'), ('SECRET_KEY', 'change-this'),
                         ('CORS_ALLOWED_ORIGINS', '*'), ('ALLOWED_HOSTS', '*'),
                         ('SUPABASE_URL', 'http://fixture')]:
        with pytest.raises(ValueError):
            validate_production({**environment, field: value})


def test_encrypted_backup_round_trip_and_authentication_failure(tmp_path):
    key = os.urandom(32)
    source, encrypted, restored = [tmp_path / name for name in ('source', 'encrypted', 'restored')]
    source.write_bytes(os.urandom(2 * 1024 * 1024 + 37))
    encrypt(source, encrypted, key)
    decrypt(encrypted, restored, key)
    assert restored.read_bytes() == source.read_bytes()
    with pytest.raises(FileExistsError):
        decrypt(encrypted, restored, key)
    assert restored.read_bytes() == source.read_bytes()
    with pytest.raises(FileExistsError):
        encrypt(source, encrypted, key)
    failed = tmp_path / 'failed'
    with pytest.raises(InvalidTag):
        decrypt(encrypted, failed, os.urandom(32))
    assert not failed.exists()
    corrupt = bytearray(encrypted.read_bytes())
    corrupt[-50] ^= 1
    encrypted.write_bytes(corrupt)
    with pytest.raises(InvalidTag):
        decrypt(encrypted, failed, key)
    assert not failed.exists()
