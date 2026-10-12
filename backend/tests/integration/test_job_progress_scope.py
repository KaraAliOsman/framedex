"""Worker progress survives domain projections without leaking authority."""

from decimal import Decimal
import json
from uuid import uuid4

from django.db import connection, DatabaseError, transaction
import pytest

from jobs.repository import LockLostError, report_progress
from jobs.service import job_owner

pytestmark = pytest.mark.rls_integration


@pytest.mark.parametrize("role", ["none", "authenticated"])
def test_progress_restores_role_claims_and_keeps_user_queue_private(django_db_blocker, role):
    if connection.vendor != "postgresql":
        pytest.fail("Worker role regression requires real PostgreSQL; never skipped")
    with django_db_blocker.unblock(), transaction.atomic():
        org, job, actor = uuid4(), uuid4(), uuid4()
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO public.tenancy_organizations(id,name,tax_id) VALUES(%s,'Progress regression',%s)", [org, str(org)])
            cursor.execute("INSERT INTO public.job_runs(id,org_id,type,state,locked_by,locked_at) VALUES(%s,%s,'ai.agent.run','RUNNING','scope-regression',NOW())", [job, org])
            cursor.execute("SELECT set_config('request.jwt.claims',%s,true)", [json.dumps({"sub": str(actor), "role": "authenticated"})])
            if role == "authenticated":
                cursor.execute("SET LOCAL ROLE authenticated")
            cursor.execute("SELECT current_setting('role'),current_setting('request.jwt.claims')")
            before = cursor.fetchone()
        report_progress(job_id=job, worker_id="scope-regression", progress=55)
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_setting('role'),current_setting('request.jwt.claims')")
            assert cursor.fetchone() == before
        with pytest.raises(LockLostError):
            report_progress(job_id=job, worker_id="different-worker", progress=95)
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_setting('role'),current_setting('request.jwt.claims')")
            assert cursor.fetchone() == before
        with job_owner(), connection.cursor() as cursor:
            cursor.execute("SELECT progress,locked_by FROM public.job_runs WHERE id=%s", [job])
            assert cursor.fetchone() == (Decimal("55.00"), "scope-regression")
        if role == "authenticated":
            with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cursor:
                cursor.execute("SELECT id FROM public.job_runs WHERE id=%s", [job])
        transaction.set_rollback(True)
