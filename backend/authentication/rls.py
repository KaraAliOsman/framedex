"""Transaction-local propagation of verified JWT claims into PostgreSQL RLS."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
import json

from django.db import connection, transaction


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
