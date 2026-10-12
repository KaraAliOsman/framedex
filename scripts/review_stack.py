#!/usr/bin/env python3
"""Owned local review stack. Public sources on disk, credentials in memory."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.run' / 'review'
PROJECT = 'framedex-review'
LABEL = 'com.dekopen.review'
OWNER = hashlib.sha256(str(ROOT).lower().encode()).hexdigest()[:16]
NAMES = ['framedex-review-web', 'framedex-review-jobs', 'framedex-review-api']
PUBLIC = 'http://127.0.0.1:5179'
API = 'http://127.0.0.1:8004'
PORTS = [25360, 25361, 25362, 25364, 25365, 25366, 8004, 5179]


def call(args, *, env=None, cwd=ROOT, quiet=False):
    args = [shutil.which(args[0]) or args[0], *args[1:]]
    result = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True,
                            encoding='utf-8', errors='replace')
    if result.returncode:
        # Do not echo arguments or provider/CLI output: either may contain keys.
        raise RuntimeError(f'{Path(args[0]).name}: operación fallida ({result.returncode}).')
    if not quiet and args[0] == 'docker' and args[1:2] == ['build']:
        print('Imagen de revisión construida.', flush=True)
    return result.stdout


def inspect(name):
    result = subprocess.run(['docker', 'container', 'inspect', name], capture_output=True, text=True)
    return json.loads(result.stdout)[0] if result.returncode == 0 else None


def owned(name):
    item = inspect(name)
    if item and item.get('Config', {}).get('Labels', {}).get(LABEL) != OWNER:
        raise RuntimeError(f'El contenedor {name} no pertenece a esta revisión; se conserva.')
    return item


def resources():
    selector = f'label=com.supabase.cli.project={PROJECT}'
    return bool(call(['docker', 'ps', '-aq', '--filter', selector], quiet=True).strip()
                or call(['docker', 'volume', 'ls', '-q', '--filter', selector], quiet=True).strip()
                or inspect(f'supabase_db_{PROJECT}'))


def require_owner():
    manifest = WORK / 'owner.json'
    if manifest.exists():
        if json.loads(manifest.read_text()) != {'owner': OWNER, 'root': str(ROOT)}:
            raise RuntimeError('La carpeta de revisión pertenece a otro checkout.')
    elif resources() or any(inspect(name) for name in NAMES):
        raise RuntimeError('Hay datos de revisión sin manifiesto de propiedad; se conservan.')
    else:
        WORK.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps({'owner': OWNER, 'root': str(ROOT)}), encoding='utf-8')
    for name in NAMES:
        owned(name)


def dotenv():
    env = dict(os.environ)
    path = ROOT / '.env'
    if path.is_file():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            match = re.fullmatch(r'\s*([A-Z][A-Z0-9_]*)\s*=\s*(.*?)\s*', line)
            if not match:
                continue
            key, value = match.groups()
            if len(value) >= 2 and value[0] in {'"', "'"} and value[-1] == value[0]:
                value = value[1:-1]
            env[key] = value
    return env


def prepare():
    config = (ROOT / 'supabase/config.toml').read_text(encoding='utf-8')
    config = config.replace('project_id = "dekopen"', f'project_id = "{PROJECT}"')
    for before, after in zip([25320,25321,25322,25324,25325,25326], PORTS[:6], strict=True):
        config = config.replace(str(before), str(after))
    config = config.replace('5173', '5179')
    target = WORK / 'supabase'
    target.mkdir(exist_ok=True)
    (target / 'config.toml').write_text(config, encoding='utf-8')
    for directory in ['migrations', 'templates']:
        shutil.copytree(ROOT / 'supabase' / directory, target / directory, dirs_exist_ok=True)
    shutil.copy2(ROOT / 'supabase/seed.sql', target / 'seed.sql')


def environment():
    status = json.loads(call(['supabase', 'status', '-o', 'json'], cwd=WORK, quiet=True))
    env = dotenv()
    env.update({
        'SUPABASE_URL': status['API_URL'], 'SUPABASE_ANON_KEY': status['ANON_KEY'],
        'SUPABASE_SERVICE_ROLE_KEY': status['SERVICE_ROLE_KEY'], 'DATABASE_URL': status['DB_URL'],
        'VITE_SUPABASE_URL': status['API_URL'], 'VITE_SUPABASE_ANON_KEY': status['ANON_KEY'],
        'SUPABASE_JWT_VERIFY_MODE': 'auth_server', 'DEBUG': 'true', 'DJANGO_DEBUG': 'true',
        'ALLOWED_HOSTS': 'localhost,127.0.0.1,host.docker.internal', 'DJANGO_URL': API,
        'CORS_ALLOWED_ORIGINS': PUBLIC, 'DEKOPEN_PUBLIC_APP_URL': PUBLIC,
        'BILLING_CALLBACK_ORIGIN': API, 'BILLING_FRONTEND_ORIGIN': PUBLIC,
        'MAIL_PROVIDER': 'sandbox', 'MAIL_SANDBOX_HOST': 'host.docker.internal',
        'MAIL_SANDBOX_PORT': '25365', 'MAILPIT_URL': status['MAILPIT_URL'],
        'AI_GATEWAY_MOCK_ENABLED': '0', 'PORT': '8004', 'PYTHONUTF8': '1',
    })
    # Only loopback endpoints may receive this local fixture.
    if not all('127.0.0.1' in env[key] or 'localhost' in env[key]
               for key in ['SUPABASE_URL', 'DATABASE_URL']):
        raise RuntimeError('La revisión solo admite Supabase local.')
    env['DATABASE_URL'] = env['DATABASE_URL'].replace('127.0.0.1', 'host.docker.internal').replace('localhost', 'host.docker.internal')
    return env


def container(name, image, args, env):
    if owned(name):
        call(['docker', 'rm', '--force', name], quiet=True)
    keys = [key for key in env if key.startswith(('AI_GATEWAY_', 'SUPABASE_', 'MAIL_', 'BILLING_'))
            or key in {'DATABASE_URL', 'SECRET_KEY', 'DEBUG', 'DJANGO_DEBUG', 'PORT',
                       'ALLOWED_HOSTS', 'CORS_ALLOWED_ORIGINS', 'DEKOPEN_PUBLIC_APP_URL',
                       'DJANGO_URL', 'PYTHONUTF8'}]
    command = ['docker', 'run', '--detach', '--name', name, '--label', f'{LABEL}={OWNER}',
               '--mount', f'type=bind,source={ROOT / "scripts"},target=/review-scripts,readonly']
    if name == 'framedex-review-api':
        command += ['--publish', '127.0.0.1:8004:8004']
    for key in keys:
        command += ['--env', key]
    command += [image, *args]
    call(command, env=env, quiet=True)
    call(['docker', 'exec', '--detach', name, 'python', '/review-scripts/review_transport.py'], quiet=True)


def wait(url, seconds=90):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status < 500:
                    return
        except (OSError, urllib.error.URLError):
            time.sleep(.5)
    raise RuntimeError('El servicio de revisión no respondió a tiempo.')


def start():
    require_owner()
    version = call(['supabase', '--version'], quiet=True).strip()
    if version != '2.116.0':
        raise RuntimeError('Instala Supabase CLI 2.116.0 para esta revisión.')
    if not resources():
        for port in PORTS:
            with socket.socket() as sock:
                if sock.connect_ex(('127.0.0.1', port)) == 0:
                    raise RuntimeError(f'El puerto de revisión {port} está ocupado; se conserva su proceso.')
    prepare()
    print('Iniciando Supabase aislado; ninguna base existente se resetea.', flush=True)
    call(['supabase', 'start'], cwd=WORK, quiet=True)
    env = environment()
    print('Construyendo servidor de revisión.', flush=True)
    call(['docker', 'build', '-t', 'framedex-review-api', '.'])
    call(['docker', 'exec', f'supabase_db_{PROJECT}', 'psql', '-U', 'postgres', '-d', 'postgres',
          '-v', 'ON_ERROR_STOP=1', '-c', "INSERT INTO storage.buckets(id,name,public) VALUES('documents','documents',false) ON CONFLICT(id) DO NOTHING"], quiet=True)
    container('framedex-review-api', 'framedex-review-api', [], env)
    wait(API + '/api/schema/')
    container('framedex-review-jobs', 'framedex-review-api',
              ['python', 'backend/manage.py', 'runjobs', '--poll', '1.5'], env)
    print('Preparando proyectos y catálogo DEMO mediante la API.', flush=True)
    call(['docker', 'exec', 'framedex-review-api', 'python', '/review-scripts/dev_fixture.py'], quiet=True)
    print('Cinco cuentas por rol y dos empresas DEMO listas.', flush=True)
    public_env = {key: env[key] for key in ['VITE_SUPABASE_URL', 'VITE_SUPABASE_ANON_KEY']}
    print('Construyendo la aplicación de revisión.', flush=True)
    build = ['docker', 'build', '-f', 'frontend/Dockerfile', '-t', 'framedex-review-web']
    for key in public_env:
        build += ['--build-arg', key]
    call([*build, '.'], env={**os.environ, **public_env})
    if owned('framedex-review-web'):
        call(['docker', 'rm', '--force', 'framedex-review-web'], quiet=True)
    call(['docker', 'run', '--detach', '--name', 'framedex-review-web', '--label', f'{LABEL}={OWNER}',
          '--publish', '127.0.0.1:5179:5179', '--env', 'PORT=5179', '--env', 'BACKEND_ORIGIN=http://host.docker.internal:8004',
          'framedex-review-web'], quiet=True)
    wait(PUBLIC + '/login')
    print(f'Revisión lista: {PUBLIC} · Correo local: http://127.0.0.1:25364', flush=True)


def stop():
    require_owner()
    for name in NAMES:
        if owned(name):
            call(['docker', 'stop', name], quiet=True)
    if resources():
        call(['supabase', 'stop'], cwd=WORK, quiet=True)
    print('Revisión detenida; datos conservados.', flush=True)


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['start', 'stop'])
    args = parser.parse_args()
    try:
        {'start': start, 'stop': stop}[args.action]()
    except (RuntimeError, OSError, ValueError, KeyError) as error:
        print(str(error))
        print('No se borraron datos. Comprueba Docker Desktop y la guía.')
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()
