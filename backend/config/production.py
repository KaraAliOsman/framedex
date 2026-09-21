"""Fail-closed production configuration and a real WSGI process boundary."""

import os
from urllib.parse import urlsplit


def validate_production(environment):
    if environment.get('ENVIRONMENT', 'development') != 'production':
        return
    required = ('SECRET_KEY', 'DATABASE_URL', 'SUPABASE_URL', 'SUPABASE_ANON_KEY',
                'ALLOWED_HOSTS', 'CORS_ALLOWED_ORIGINS', 'REDIS_URL')
    if any(not environment.get(name, '').strip() for name in required):
        raise ValueError('Production requires explicit secrets, hosts, database, Redis and origins')
    if (environment.get('DEBUG', '').lower() in ('1', 'true', 'yes')
            or len(environment['SECRET_KEY']) < 50
            or any(part in environment['SECRET_KEY'].lower() for part in ('change', 'insecure', 'local-only'))):
        raise ValueError('Unsafe production Django settings')
    if urlsplit(environment['DATABASE_URL']).scheme not in ('postgres', 'postgresql'):
        raise ValueError('Production requires PostgreSQL')
    if urlsplit(environment['SUPABASE_URL']).scheme != 'https':
        raise ValueError('Production Supabase must use HTTPS')
    origins = [value.strip() for value in environment['CORS_ALLOWED_ORIGINS'].split(',')]
    if any(urlsplit(value).scheme != 'https' or '*' in value for value in origins):
        raise ValueError('Production CORS requires explicit HTTPS origins')
    if '*' in environment['ALLOWED_HOSTS']:
        raise ValueError('Production hosts cannot use a wildcard')


def is_production():
    return os.environ.get('ENVIRONMENT') == 'production'
