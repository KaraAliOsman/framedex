"""Probe the real Linux Gunicorn process against local Supabase and disposable Redis.

No Railway account or production deployment is implied by this local check.
"""

import json
from concurrent.futures import ThreadPoolExecutor
import os
import secrets
import subprocess
import time
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

import httpx

import local_gates


def docker(*arguments, env=None):
    result = subprocess.run(['docker', *arguments], env=env, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError('Docker production probe failed: ' + result.stderr[-1000:])
    return result.stdout.strip()


def main():
    local = local_gates.running_environment()
    network = json.loads(docker('inspect', 'supabase_db_dekopen', '--format', '{{json .NetworkSettings.Networks}}'))
    network_name = next(iter(network))
    identifier = 'dekopen-production-probe-' + uuid4().hex[:10]
    cache_name, app_name = identifier + '-redis', identifier + '-app'
    parsed = urlsplit(local['DATABASE_URL'])
    database = urlunsplit((parsed.scheme, parsed.netloc.rsplit('@', 1)[0] + '@supabase_db_dekopen:5432',
                          parsed.path, 'connect_timeout=3', ''))
    environment = {**os.environ, 'ENVIRONMENT': 'production', 'SECRET_KEY': secrets.token_hex(32),
                   'DATABASE_URL': database, 'REDIS_URL': f'redis://{cache_name}:6379',
                   'SUPABASE_URL': 'https://synthetic.supabase.example', 'SUPABASE_ANON_KEY': 'synthetic',
                   'ALLOWED_HOSTS': '127.0.0.1,healthcheck.railway.app',
                   'CORS_ALLOWED_ORIGINS': 'https://synthetic.example', 'DEBUG': 'False'}
    created = []
    try:
        docker('run', '-d', '--name', cache_name, '--network', network_name, 'redis:8.2-alpine')
        created.append(cache_name)
        flags = [flag for name in ('ENVIRONMENT','SECRET_KEY','DATABASE_URL','REDIS_URL','SUPABASE_URL',
                                  'SUPABASE_ANON_KEY','ALLOWED_HOSTS','CORS_ALLOWED_ORIGINS','DEBUG')
                 for flag in ('-e', name)]
        docker('run', '-d', '--name', app_name, '--network', network_name, '-p', '127.0.0.1::8000',
               *flags, 'dekopen-shot11-app', env=environment)
        created.append(app_name)
        port = json.loads(docker('inspect', app_name, '--format', '{{json .NetworkSettings.Ports}}'))['8000/tcp'][0]['HostPort']
        base = 'http://127.0.0.1:' + port
        deadline = time.monotonic() + 40
        with httpx.Client(timeout=5, trust_env=False) as client:
            while True:
                try:
                    if client.get(base + '/health/ready/').status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                if time.monotonic() >= deadline:
                    raise RuntimeError('Real production process did not become ready')
                time.sleep(0.5)
            assert client.get(base + '/health/live/').status_code == 200
            protected = client.get(base + '/api/v1/billing/wallet/', headers={'X-Forwarded-Proto': 'https'})
            assert protected.status_code == 401
            assert protected.headers['Content-Security-Policy'].startswith("default-src 'none'")
            assert protected.headers['Strict-Transport-Security'].startswith('max-age=31536000')
            assert docker('exec', app_name, 'id', '-u') == '10001'
            # Invalid form callbacks exercise the public DRF boundary without issuing
            # any provider request. Both Gunicorn workers share the Redis counter.
            callback = base + '/api/v1/billing/flow/confirm/' + str(uuid4()) + '/'
            def attempt(_):
                return client.post(callback, content='', headers={
                    'X-Forwarded-Proto': 'https', 'Content-Type': 'application/x-www-form-urlencoded',
                }).status_code
            with ThreadPoolExecutor(max_workers=8) as pool:
                statuses = list(pool.map(attempt, range(105)))
            assert statuses.count(400) == 100 and statuses.count(429) == 5
            docker('stop', cache_name)
            assert client.get(base + '/health/ready/').status_code == 503
            assert client.get(base + '/health/live/').status_code == 200
        print(json.dumps({'gunicorn_nonroot': True, 'production_readiness': 200,
                          'redis_failure_readiness': 503, 'redis_failure_liveness': 200,
                          'unauthenticated_billing': 401, 'security_headers': True,
                          'shared_quota_100_then_429': True,
                          'railway_deployment_proven': False}))
    finally:
        for name in reversed(created):
            docker('rm', '-f', name)


if __name__ == '__main__':
    main()
