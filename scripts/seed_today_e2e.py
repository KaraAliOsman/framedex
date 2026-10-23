"""Synthetic Hoy evidence, restricted to a local tenant created by this E2E."""

import json
import os
from pathlib import Path
import sys
from urllib.parse import urlsplit
from uuid import UUID

if urlsplit(os.environ.get("DATABASE_URL", "")).hostname not in {"127.0.0.1", "localhost", "::1"}:
    raise SystemExit("Hoy E2E seeding requires local PostgreSQL")
root = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(root), str(root / "backend")]
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django  # noqa: E402

django.setup()

from django.db import connection, transaction  # noqa: E402
from backend.tests.integration.test_shot09_documentary import _seed_project, _freeze, as_user  # noqa: E402
from pricing.repository import one, json_text, commercial_backend  # noqa: E402
from ai_gateway.jobs import _ai_backend  # noqa: E402

org, actor = UUID(sys.argv[1]), UUID(sys.argv[2])
with transaction.atomic():
    with connection.cursor() as cursor:
        cursor.execute("SELECT o.name FROM public.tenancy_organizations o "
            "JOIN public.tenancy_memberships m ON m.org_id=o.id "
            "WHERE o.id=%s AND m.user_id=%s AND m.role='OWNER' AND m.is_active", [org, actor])
        tenant = cursor.fetchone()
        if not tenant or not tenant[0].startswith("DK2 E2E SYNTHETIC "):
            raise SystemExit("Refusing to seed a tenant not owned by this Hoy test")
    issued, _, operation = _seed_project(org, actor)
    with as_user(actor), commercial_backend():
        one("UPDATE public.projects SET name='Casa Pérez · ensayo sintético' WHERE id=%s RETURNING id", [issued])
    _freeze(org, actor, issued, operation)
    draft, _, _ = _seed_project(org, actor, apply_pricing=False)
    with as_user(actor):
        one("UPDATE public.projects SET name='Ventanas de la terraza · ensayo sintético' WHERE id=%s RETURNING id", [draft])
    # A synthetic verified receipt exercises the read projection. This is no
    # claim of a live provider run and invokes no AI or external action.
    with as_user(actor), _ai_backend():
        one("INSERT INTO public.ai_jobs(org_id,user_id,surface,goal,state,result,receipt) "
            "VALUES(%s,%s,'projects','Fixture sintética de Hoy','SUCCEEDED',%s::jsonb,%s::jsonb) RETURNING id",
            [org, actor, json_text({'created_project': {'project_id': str(draft)}}),
             json_text({'objects': [{'kind': 'project', 'id': str(draft), 'status': 'applied'}]})])
print(json.dumps({'issued': str(issued), 'draft': str(draft)}))
