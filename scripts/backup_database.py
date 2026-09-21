"""Encrypted, snapshot-consistent PostgreSQL backups and fail-closed clean restores.

Requires pg_dump/pg_restore matching the server major, psycopg and cryptography.
Credentials use libpq environment variables; never print commands or connection strings.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import time

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import httpx
import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict

MAGIC = b"DEKOPEN-BACKUP-v1\x00"
CHUNK = 1024 * 1024


def encryption_key() -> bytes:
    try:
        key = bytes.fromhex(os.environ["BACKUP_ENCRYPTION_KEY"])
    except (KeyError, ValueError):
        raise ValueError("BACKUP_ENCRYPTION_KEY must contain 64 hexadecimal characters") from None
    if len(key) != 32:
        raise ValueError("BACKUP_ENCRYPTION_KEY must encode exactly 32 bytes")
    return key


def encrypt(source: Path, destination: Path, key: bytes) -> None:
    nonce = os.urandom(12)
    context = Cipher(algorithms.AES(key), modes.GCM(nonce)).encryptor()
    context.authenticate_additional_data(MAGIC)
    # Exclusive creation prevents replacing a previous backup.
    with source.open("rb") as reader, destination.open("xb") as writer:
        writer.write(MAGIC + nonce)
        while data := reader.read(CHUNK):
            writer.write(context.update(data))
        writer.write(context.finalize())
        writer.write(context.tag)


def decrypt(source: Path, destination: Path, key: bytes) -> None:
    with source.open("rb") as reader:
        if reader.read(len(MAGIC)) != MAGIC:
            raise ValueError("Unsupported backup format")
        nonce = reader.read(12)
        reader.seek(-16, 2)
        tag = reader.read(16)
        remaining = reader.tell() - len(MAGIC) - 12 - 16
        if remaining <= 0:
            raise ValueError("Truncated backup")
        reader.seek(len(MAGIC) + 12)
        context = Cipher(algorithms.AES(key), modes.GCM(nonce, tag)).decryptor()
        context.authenticate_additional_data(MAGIC)
        # Acquire exclusive ownership before cleanup may remove this path.
        writer = destination.open("xb")
        try:
            with writer:
                while remaining:
                    data = reader.read(min(CHUNK, remaining))
                    if not data:
                        raise ValueError("Truncated backup")
                    remaining -= len(data)
                    writer.write(context.update(data))
                writer.write(context.finalize())
        except BaseException:
            destination.unlink(missing_ok=True)
            raise


@contextmanager
def private_directory():
    with tempfile.TemporaryDirectory(prefix="dekopen-backup-") as name:
        path = Path(name)
        path.chmod(0o700)
        yield path


def pg_command(program: str, arguments: list[str], database_url: str) -> None:
    parameters = conninfo_to_dict(database_url)
    names = {'dbname': 'PGDATABASE', 'user': 'PGUSER', 'password': 'PGPASSWORD',
             'host': 'PGHOST', 'port': 'PGPORT', 'sslmode': 'PGSSLMODE',
             'sslrootcert': 'PGSSLROOTCERT', 'connect_timeout': 'PGCONNECT_TIMEOUT',
             'options': 'PGOPTIONS', 'application_name': 'PGAPPNAME', 'hostaddr': 'PGHOSTADDR'}
    if set(parameters) - names.keys():
        raise ValueError('Unsupported backup libpq connection option')
    environment = {name: value for name, value in os.environ.items() if not name.startswith('PG')}
    environment.update({names[name]: value for name, value in parameters.items()})
    result = subprocess.run([program, *arguments], env=environment, capture_output=True)
    if result.returncode:
        # pg errors can contain DSNs, SQL values and credentials.
        raise RuntimeError(f"{program} failed with exit code {result.returncode}; no restore proof")


def fingerprints(connection) -> dict:
    connection.execute("SET LOCAL TIME ZONE 'UTC'")
    tables = connection.execute("""
        SELECT schemaname, tablename FROM pg_tables
        WHERE schemaname IN ('public','auth','storage','supabase_migrations')
        ORDER BY schemaname, tablename
    """).fetchall()
    result = {}
    for schema, table in tables:
        digest, count = hashlib.sha256(), 0
        query = sql.SQL("SELECT row_to_json(t)::text FROM {}.{} t ORDER BY row_to_json(t)::text")
        with connection.cursor(name="backup_integrity") as cursor:
            cursor.execute(query.format(sql.Identifier(schema), sql.Identifier(table)))
            for (row,) in cursor:
                digest.update(row.encode() + b"\n")
                count += 1
        result[f"{schema}.{table}"] = {"rows": count, "sha256": digest.hexdigest()}
    return result


def role_manifest(connection) -> dict:
    # Capture authorization roles, never password hashes. Restored logins remain disabled
    # until the platform operator rotates credentials and provisions the trusted boundary.
    roles = connection.execute("""
        SELECT rolname, rolinherit, rolbypassrls FROM pg_roles
        WHERE rolname NOT LIKE 'pg_%' AND rolname <> current_user ORDER BY rolname
    """).fetchall()
    memberships = connection.execute("""
        SELECT parent.rolname, member.rolname FROM pg_auth_members m
        JOIN pg_roles parent ON parent.oid=m.roleid JOIN pg_roles member ON member.oid=m.member
        WHERE parent.rolname NOT LIKE 'pg_%' AND member.rolname NOT LIKE 'pg_%'
        ORDER BY 1,2
    """).fetchall()
    return {"roles": roles, "memberships": memberships}


def backup(destination: Path) -> dict:
    key = encryption_key()
    database_url = os.environ["BACKUP_DATABASE_URL"]
    started = datetime.now(timezone.utc)
    with private_directory() as temporary, psycopg.connect(database_url) as connection:
        connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        snapshot = connection.execute("SELECT pg_export_snapshot()").fetchone()[0]
        manifest = {
            "format": 1, "started_at": started.isoformat(),
            "server_version": connection.info.server_version,
            "roles": role_manifest(connection), "tables": fingerprints(connection),
        }
        dump = temporary / "database.dump"
        pg_command("pg_dump", ["--format=custom", "--compress=9", "--no-owner",
                               "--snapshot=" + snapshot, "--file=" + str(dump)], database_url)
        manifest["dump_sha256"] = file_hash(dump)
        (temporary / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        bundle = temporary / "bundle.tar"
        with tarfile.open(bundle, "w") as archive:
            for name in ("database.dump", "manifest.json"):
                archive.add(temporary / name, arcname=name)
        encrypt(bundle, destination, key)
    return {"backup_sha256": file_hash(destination), "started_at": started.isoformat(),
            "table_count": len(manifest["tables"])}


def file_hash(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def restore(source: Path) -> dict:
    started = time.monotonic()
    target = os.environ["RESTORE_DATABASE_URL"]
    if target == os.environ.get("BACKUP_DATABASE_URL"):
        raise ValueError("Restore target must differ from backup source")
    with private_directory() as temporary:
        bundle = temporary / "bundle.tar"
        decrypt(source, bundle, encryption_key())
        # Extract only the two expected regular members, after GCM authentication.
        with tarfile.open(bundle) as archive:
            if sorted(archive.getnames()) != ["database.dump", "manifest.json"]:
                raise ValueError("Unexpected backup members")
            for member in archive.getmembers():
                if not member.isfile():
                    raise ValueError("Invalid backup member")
                with archive.extractfile(member) as reader, (temporary / member.name).open('xb') as writer:
                    shutil.copyfileobj(reader, writer, CHUNK)
        manifest = json.loads((temporary / "manifest.json").read_text(encoding="utf-8"))
        dump = temporary / "database.dump"
        if manifest["format"] != 1 or file_hash(dump) != manifest["dump_sha256"]:
            raise ValueError("Backup manifest mismatch")
        with psycopg.connect(target) as connection:
            if connection.info.server_version // 10000 != manifest["server_version"] // 10000:
                raise ValueError("Restore requires the backed-up PostgreSQL major version")
            objects = connection.execute("""
                SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                WHERE n.nspname NOT LIKE 'pg_%' AND n.nspname <> 'information_schema'
                  AND c.relkind IN ('r','p','v','m','S','f')
            """).fetchone()[0]
            schemas = connection.execute("""
                SELECT count(*) FROM pg_namespace WHERE nspname NOT LIKE 'pg_%'
                  AND nspname NOT IN ('public','information_schema')
            """).fetchone()[0]
            if objects or schemas:
                raise ValueError("Restore requires a clean database; existing data is never overwritten")
            existing = {r[0] for r in connection.execute("SELECT rolname FROM pg_roles")}
            for name, inherit, bypass in manifest["roles"]["roles"]:
                if name in existing:
                    raise ValueError("Restore requires a clean role boundary")
                connection.execute(sql.SQL("CREATE ROLE {} NOLOGIN NOSUPERUSER {} {}").format(
                    sql.Identifier(name), sql.SQL("INHERIT" if inherit else "NOINHERIT"),
                    sql.SQL("BYPASSRLS" if bypass else "NOBYPASSRLS")))
            for parent, member in manifest["roles"]["memberships"]:
                connection.execute(sql.SQL("GRANT {} TO {}").format(
                    sql.Identifier(parent), sql.Identifier(member)))
        pg_command("pg_restore", ["--exit-on-error", "--single-transaction", "--no-owner",
                                  "--dbname=", str(dump)], target)
        with psycopg.connect(target) as connection:
            if fingerprints(connection) != manifest["tables"]:
                raise ValueError("Restored table contents differ from the exported snapshot")
            # Historical migrations may deliberately leave a NOT VALID FK. A drill
            # actually validates its restored rows rather than trusting the flag.
            pending = connection.execute("""
                SELECT n.nspname,c.relname,k.conname FROM pg_constraint k
                JOIN pg_class c ON c.oid=k.conrelid JOIN pg_namespace n ON n.oid=c.relnamespace
                WHERE NOT k.convalidated
            """).fetchall()
            for schema, table, constraint in pending:
                connection.execute(sql.SQL('ALTER TABLE {}.{} VALIDATE CONSTRAINT {}').format(
                    sql.Identifier(schema), sql.Identifier(table), sql.Identifier(constraint)))
            ledger_errors = connection.execute("""
                SELECT count(*) FROM public.tenancy_organizations o
                WHERE o.credits_balance <> (SELECT coalesce(sum(amount),0) FROM public.credit_ledger l WHERE l.org_id=o.id)
                   OR o.credits_balance <> (SELECT coalesce(sum(remaining),0) FROM public.credit_lots l WHERE l.org_id=o.id)
            """).fetchone()[0]
            if ledger_errors:
                raise ValueError("Restored ledger balances are inconsistent")
            unprotected = connection.execute("""
                SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                WHERE n.nspname='public' AND c.relkind='r' AND NOT c.relrowsecurity
                  AND EXISTS(SELECT 1 FROM pg_attribute a WHERE a.attrelid=c.oid AND a.attname='org_id')
            """).fetchone()[0]
            if unprotected:
                raise ValueError("Restored business tables lack RLS")
    elapsed = time.monotonic() - started
    if elapsed > 7200:
        raise ValueError("Restore exceeded the two-hour RTO")
    return {"backup_sha256": file_hash(source), "restore_seconds": round(elapsed, 3),
            "table_count": len(manifest["tables"]), "content_hashes_match": True,
            "constraints_valid": True, "ledger_consistent": True, "tenant_rls_enabled": True,
            "production_rpo_proven": False}


def upload(path: Path) -> None:
    base = os.environ["SUPABASE_URL"].rstrip("/")
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    if not base.startswith("https://"):
        raise ValueError("Backup Storage requires HTTPS")
    with path.open("rb") as stream, httpx.Client(timeout=300, follow_redirects=False) as client:
        response = client.post(f"{base}/storage/v1/object/dekopen-backups/{path.name}",
                               headers={"apikey": key, "Authorization": "Bearer " + key,
                                        "Content-Type": "application/octet-stream",
                                        "x-upsert": "false"}, content=stream)
        if response.status_code not in (200, 201):
            raise RuntimeError("Encrypted Storage upload failed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("backup", "restore", "scheduled"))
    parser.add_argument("path", type=Path, nargs='?')
    parser.add_argument("--upload", action="store_true")
    arguments = parser.parse_args()
    if arguments.operation == 'scheduled':
        if arguments.path is not None or arguments.upload:
            parser.error('scheduled owns its temporary path and always uploads')
        from uuid import uuid4
        with private_directory() as temporary:
            name = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid4().hex + '.aes'
            path = temporary / name
            result = backup(path)
            upload(path)
            result.update(storage_uploaded=True, object_name=name)
        print(json.dumps(result, sort_keys=True))
        return
    if arguments.path is None:
        parser.error('backup and restore require a path')
    result = backup(arguments.path) if arguments.operation == "backup" else restore(arguments.path)
    if arguments.upload:
        if arguments.operation != "backup":
            raise ValueError("Upload is only supported after backup")
        upload(arguments.path)
        result["storage_uploaded"] = True
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
