"""Real Postgres proofs for sealed mail, dispatch concurrency and tenant scope."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.db import close_old_connections, connection, DatabaseError, transaction
import pytest

from backend.tests.integration.test_shot08_pricing import (
    committed_commercial_rows as committed_commercial_rows,
    as_user,
)
from documents.repository import DocumentaryError, documentary_backend, one, rows, write
from notifications import adapters, service
from projects import org_branding

pytestmark = pytest.mark.rls_integration
real_branding_for_snapshot = org_branding.branding_for_snapshot


def queued(org, actor, key="event"):
    return service.seal_mail(
        org_id=org,
        actor_id=actor,
        event_key=key,
        kind="APPROVAL",
        recipient="internal@example.invalid",
        message={
            "subject": "Aprobación recibida",
            "html": "<p>Obra</p>",
            "text": "Obra",
            "images": [],
            "from_name": "DEKOPEN",
        },
    )


def test_seal_is_transactional_idempotent_and_private(committed_commercial_rows):
    org, other, users = committed_commercial_rows
    with transaction.atomic():
        queued(org, users["ESTIMATOR"], "rollback")
        transaction.set_rollback(True)
    assert rows("SELECT id FROM public.mail_outbox WHERE org_id=%s", [org]) == []
    first = queued(org, users["ESTIMATOR"])
    assert queued(org, users["ESTIMATOR"])["id"] == first["id"]
    assert (
        one(
            "SELECT count(*) AS n FROM public.job_runs WHERE org_id=%s AND type='mail.deliver'",
            [org],
        )["n"]
        == 1
    )
    assert "content_ciphertext" not in first
    for role in users:
        with as_user(users[role]), documentary_backend():
            visible = rows("SELECT id FROM public.mail_outbox WHERE org_id=%s", [org])
            assert len(visible) == (0 if role == "INSTALLER" else 1)
            assert rows("SELECT id FROM public.mail_outbox WHERE org_id=%s", [other]) == []
            with pytest.raises(DatabaseError), transaction.atomic():
                rows("SELECT content_ciphertext FROM public.mail_outbox WHERE org_id=%s", [org])
            with pytest.raises(DatabaseError), transaction.atomic():
                write("UPDATE public.mail_outbox SET state='SENT' WHERE id=%s", [first["id"]])
    with as_user(users["ESTIMATOR"]):
        with pytest.raises(DatabaseError), transaction.atomic():
            rows("SELECT * FROM public.mail_outbox")
    with pytest.raises(DatabaseError, match="sealed_mail_immutable"), transaction.atomic():
        write(
            "UPDATE public.mail_outbox SET recipient='changed@example.invalid' WHERE id=%s",
            [first["id"]],
        )


def test_concurrent_workers_commit_before_smtp_and_deliver_once(
    committed_commercial_rows, monkeypatch
):
    org, _, users = committed_commercial_rows
    mail = queued(org, users["ESTIMATOR"])
    barrier = Barrier(2)
    deliveries = []

    def deliver(payload, *, mail_id, recipient):
        assert not connection.in_atomic_block
        # A second connection sees DISPATCHING before any provider work.
        from django.db import connections

        fresh = connections["default"].copy()
        try:
            with fresh.cursor() as cursor:
                cursor.execute("SELECT state FROM public.mail_outbox WHERE id=%s", [str(mail_id)])
                assert cursor.fetchone()[0] == "DISPATCHING"
        finally:
            fresh.close()
        deliveries.append(mail_id)

    monkeypatch.setattr(adapters, "deliver", deliver)

    def dispatch(_):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            return service.dispatch(org_id=org, mail_id=mail["id"])
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(dispatch, [1, 2]))
    assert len(deliveries) == 1
    assert one("SELECT state,attempt FROM public.mail_outbox WHERE id=%s", [mail["id"]]) == {
        "state": "SENT",
        "attempt": 1,
    }
    assert [
        row["event"]
        for row in rows(
            "SELECT event FROM public.mail_attempts WHERE mail_id=%s ORDER BY created_at,id",
            [mail["id"]],
        )
    ] == ["DISPATCHING", "SENT"]
    service.dispatch(org_id=org, mail_id=mail["id"])
    assert len(deliveries) == 1
    with pytest.raises(DatabaseError, match="mail_attempt_immutable"), transaction.atomic():
        write("DELETE FROM public.mail_attempts WHERE mail_id=%s", [mail["id"]])


def test_lost_provider_response_never_auto_resends(committed_commercial_rows, monkeypatch):
    org, other, users = committed_commercial_rows
    mail = queued(org, users["ESTIMATOR"])
    delivered = []

    def lose_response(*args, **kwargs):
        delivered.append(kwargs["mail_id"])
        raise TimeoutError("response lost")

    monkeypatch.setattr(adapters, "deliver", lose_response)
    assert service.dispatch(org_id=org, mail_id=mail["id"])["state"] == "UNCERTAIN"
    assert service.dispatch(org_id=org, mail_id=mail["id"])["state"] == "UNCERTAIN"
    assert len(delivered) == 1
    with as_user(users["ESTIMATOR"]):
        from documents.repository import DocumentaryError

        with pytest.raises(DocumentaryError, match="mail_not_found"):
            service.recover(
                org_id=other, mail_id=mail["id"], actor_id=users["ESTIMATOR"], expected_attempt=1
            )
        recovered = service.recover(
            org_id=org, mail_id=mail["id"], actor_id=users["ESTIMATOR"], expected_attempt=1
        )
        assert recovered["state"] == "QUEUED"
        with pytest.raises(DocumentaryError, match="mail_recovery_conflict"):
            service.recover(
                org_id=org, mail_id=mail["id"], actor_id=users["ESTIMATOR"], expected_attempt=1
            )
    monkeypatch.setattr(
        adapters, "deliver", lambda *args, **kwargs: delivered.append(kwargs["mail_id"])
    )
    service.dispatch(org_id=org, mail_id=mail["id"])
    assert len(delivered) == 2
    assert one("SELECT state,attempt FROM public.mail_outbox WHERE id=%s", [mail["id"]]) == {
        "state": "SENT",
        "attempt": 2,
    }


def test_crashed_worker_and_attempt_scope_are_explicit(committed_commercial_rows):
    org, other, users = committed_commercial_rows
    mail = queued(org, users["ESTIMATOR"])
    write(
        "UPDATE public.mail_outbox SET state='DISPATCHING',attempt=1,dispatch_started_at=now()-interval '3 minutes' WHERE id=%s",
        [mail["id"]],
    )
    service.reconcile_stale(org_id=org)
    assert (
        one("SELECT state FROM public.mail_outbox WHERE id=%s", [mail["id"]])["state"]
        == "UNCERTAIN"
    )
    with pytest.raises(DatabaseError, match="mail_attempt_scope_mismatch"), transaction.atomic():
        write(
            "INSERT INTO public.mail_attempts(org_id,mail_id,attempt,event) VALUES(%s,%s,1,'SENT')",
            [other, mail["id"]],
        )


def test_branding_rls_preferences_and_contrast_are_tenant_owned(
    committed_commercial_rows, monkeypatch
):
    # The shared unit fixture replaces this I/O boundary. This proof uses it live.
    monkeypatch.setattr(org_branding, "branding_for_snapshot", real_branding_for_snapshot)
    org, other, users = committed_commercial_rows
    with as_user(users["ESTIMATOR"]):
        saved = org_branding.save_branding(
            org_id=org, data={"commercial_name": "Sur", "brand_primary_color": "#FFFFFF"}
        )
        assert saved["brand_color_fallback"] and saved["brand_effective_color"] == "#075F5A"
        with documentary_backend():
            snapshot = org_branding.branding_for_snapshot(org_id=org)
        assert snapshot["brand_schema"] == 1 and snapshot["document_attribution"] is False
        assert "notification_email" not in snapshot
        with pytest.raises((DatabaseError, DocumentaryError)), transaction.atomic():
            org_branding.save_branding(org_id=other, data={"commercial_name": "Bad"})
    with as_user(users["INSTALLER"]):
        with pytest.raises((DatabaseError, DocumentaryError)), transaction.atomic():
            org_branding.save_branding(org_id=org, data={"commercial_name": "Bad"})
