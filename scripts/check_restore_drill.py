"""Real clean-instance PostgreSQL 17 restore proof using disposable Docker resources.

Synthetic data only. Never connects to or modifies an existing database. Does not prove
production PITR, Storage delivery, production-sized RTO, or authentication service recovery.
"""

import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]


def run(arguments, *, env=None, input_text=None):
    result = subprocess.run(arguments, env=env, input=input_text, text=True,
                            encoding='utf-8', capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-4000:] or result.stdout[-4000:])
    return result.stdout.strip()


def main():
    sha = run(['git', 'rev-parse', 'HEAD'])
    if run(['git', 'status', '--porcelain']):
        raise RuntimeError('SHA-bound recovery proof requires a clean worktree')
    run(['docker', 'build', '-f', 'scripts/Dockerfile.backup', '--label',
         'org.opencontainers.image.revision=' + sha, '-t', 'dekopen-shot11-backup', '.'])
    identity = 'dekopen-drill-' + uuid4().hex[:12]
    containers = []
    environment = {**os.environ, 'POSTGRES_PASSWORD': secrets.token_hex(24),
                   'BACKUP_ENCRYPTION_KEY': secrets.token_hex(32)}
    run(['docker', 'network', 'create', identity])
    try:
        for suffix in ('source', 'restore'):
            name = identity + '-' + suffix
            run(['docker', 'run', '-d', '--name', name, '--network', identity,
                 '--network-alias', suffix, '-e', 'POSTGRES_PASSWORD', 'postgres:17-bookworm'],
                env=environment)
            containers.append(name)
            deadline = time.monotonic() + 60
            while True:
                status = subprocess.run(['docker', 'exec', name, 'pg_isready', '-U', 'postgres'],
                                        capture_output=True)
                process = run(['docker', 'exec', name, 'cat', '/proc/1/comm'])
                if status.returncode == 0 and process == 'postgres':
                    break
                if time.monotonic() > deadline:
                    raise RuntimeError('Disposable PostgreSQL did not become ready')
                time.sleep(0.5)
        source, target = containers
        paths = [ROOT / 'supabase/compat/postgres16_bootstrap.sql',
                 *sorted((ROOT / 'supabase/migrations').glob('*.sql')), ROOT / 'supabase/seed.sql']
        for path in paths:
            run(['docker', 'exec', '-i', source, 'psql', '-U', 'postgres', '-v', 'ON_ERROR_STOP=1'],
                input_text=path.read_text(encoding='utf-8'))
        run(['docker', 'exec', '-i', source, 'psql', '-U', 'postgres', '-v', 'ON_ERROR_STOP=1'],
            input_text="""
            INSERT INTO public.tenancy_organizations(id,name,tax_id) VALUES
              ('11111111-1111-4111-8111-111111111111','SYNTHETIC DR wallet','DR-FIXTURE');
            INSERT INTO public.tenancy_memberships(org_id,user_id,role) VALUES
              ('11111111-1111-4111-8111-111111111111','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','OWNER');
            INSERT INTO public.payments(org_id,provider,provider_payment_id,amount,currency,status)
              VALUES('11111111-1111-4111-8111-111111111111','flow','SYNTHETIC-DR-payment',43857,'CLP','succeeded');
            INSERT INTO public.payment_events(org_id,provider,event_id,payload,processed_at)
              VALUES('11111111-1111-4111-8111-111111111111','flow','SYNTHETIC-DR-event','{}',now());
            """)
        password = environment['POSTGRES_PASSWORD']
        environment.update(BACKUP_DATABASE_URL=f'postgresql://postgres:{password}@source:5432/postgres',
                           RESTORE_DATABASE_URL=f'postgresql://postgres:{password}@restore:5432/postgres')
        with tempfile.TemporaryDirectory(prefix='dekopen-drill-') as temporary:
            mount = ['--mount', f'type=bind,source={temporary},target=/backup']
            # Linux bind mounts preserve the host's mode-0700 ownership. Run the
            # disposable probe as its owning non-root user instead of opening the
            # private directory to other users or running the image as root.
            identity_flags = ['--user', f'{os.getuid()}:{os.getgid()}'] if os.name == 'posix' else []
            if os.name == 'posix' and os.getuid() == 0:
                raise RuntimeError('Run the synthetic restore probe as a non-root host user')
            common = ['docker', 'run', '--rm', *identity_flags, '--network', identity, *mount,
                      '-e', 'BACKUP_DATABASE_URL', '-e', 'RESTORE_DATABASE_URL', '-e', 'BACKUP_ENCRYPTION_KEY',
                      'dekopen-shot11-backup']
            backup = json.loads(run([*common, 'backup', '/backup/drill.aes'], env=environment))
            restored = json.loads(run([*common, 'restore', '/backup/drill.aes'], env=environment))
            if backup['backup_sha256'] != restored['backup_sha256']:
                raise RuntimeError('Restore used a different encrypted artifact')
            # The same encrypted backup must refuse to overwrite the restored database.
            repeated = subprocess.run([*common, 'restore', '/backup/drill.aes'], env=environment,
                                      capture_output=True)
            if repeated.returncode == 0 or b'clean database' not in repeated.stderr:
                raise RuntimeError('Restore did not refuse a populated target')
            restored['refuses_populated_target'] = True
            restored['source'] = 'synthetic isolated PostgreSQL 17; all repository migrations and seed'
            restored['sha'] = sha
            print(json.dumps(restored, indent=2))
    finally:
        for container in reversed(containers):
            run(['docker', 'rm', '-f', container])
        run(['docker', 'network', 'rm', identity])


if __name__ == '__main__':
    main()
