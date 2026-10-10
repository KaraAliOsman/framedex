"""Trusted server provider callback scope; callers first verify a capability.

This SQL role is never selected from request/JWT fields. Every callback query
is still explicitly bound to the resolved tenant and its exact provider claim.
"""

from contextlib import contextmanager

from django.db import connection, transaction


@contextmanager
def provider_scope():
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_setting('role',true)")
            previous = str(cursor.fetchone()[0] or "none")
            cursor.execute("SELECT current_setting('request.jwt.claims',true),current_setting('request.jwt.claim.sub',true)")
            previous_claims, previous_sub = cursor.fetchone()
            cursor.execute("SET LOCAL ROLE service_role")
            cursor.execute("SELECT set_config('request.jwt.claims',%s,true),set_config('request.jwt.claim.sub','',true)",
                           ['{"role":"service_role"}'])
        try:
            yield
        finally:
            if not connection.needs_rollback:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT set_config('role',%s,true)", [previous])
                    cursor.execute("SELECT set_config('request.jwt.claims',%s,true),set_config('request.jwt.claim.sub',%s,true)",
                                   [previous_claims or "{}", previous_sub or ""])
