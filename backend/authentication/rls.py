"""Transaction-local propagation of verified JWT claims into PostgreSQL RLS."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
import json

from django.db import DatabaseError, connection, transaction


@contextmanager
def catalog_backend() -> Iterator[None]:
    """Catalog writes run under the dedicated backend role: member-facing
    `authenticated` holds only column-wise grants over the writable fields, so
    provenance, review stamps and section revisions are exclusively API-written
    under this role. Org/user RLS policies and request.jwt.claims are
    unchanged. No-op where roles do not exist (SQLite unit tests)."""
    if connection.vendor != "postgresql":
        yield
        return
    with connection.cursor() as cursor:
        cursor.execute("SET LOCAL ROLE catalog_backend")
    try:
        yield
    except DatabaseError:
        raise
    except BaseException:
        if not connection.needs_rollback:
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL ROLE authenticated")
        raise
    else:
        if not connection.needs_rollback:
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL ROLE authenticated")


@contextmanager
def authenticated_rls_context(claims: Mapping[str, object]) -> Iterator[None]:
    claims_json = json.dumps(dict(claims), separators=(",", ":"), sort_keys=True)
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT set_config('request.jwt.claims', %s, true)",
                [claims_json],
            )
            cursor.execute("SET LOCAL ROLE authenticated")
        yield
