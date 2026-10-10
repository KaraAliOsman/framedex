"""Real tenant/RLS and transactional proofs for the exact reviewed quotation."""

import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID

from django.db import close_old_connections, connection, DatabaseError, transaction
import pytest

from backend.tests.integration.test_shot09_documentary import (
    documentary_tenant as documentary_tenant,
    documentary_committed_tenant as documentary_committed_tenant,
    as_user,
    _seed_project,
    _freeze_token,
    FakeStorage,
)
from documents import issuance, issuance_views
from documents.preferences import document_preferences
from documents.repository import DocumentaryError, documentary_backend, one, rows, write
from notifications import crypto, service as mail
from portal import service as portal, link_controls

pytestmark = pytest.mark.rls_integration


class ReviewStorage(FakeStorage):
    def signed_url(self, object_key, expires_in=None):
        return super().signed_url(object_key)

    def download(self, object_key):
        return self.uploads[object_key]

    def download_bounded(self, object_key, max_bytes):
        content = self.download(object_key)
        assert len(content) <= max_bytes
        return content


@pytest.fixture(autouse=True)
def private_storage(monkeypatch, settings):
    FakeStorage.uploads = {}
    FakeStorage.deleted = []
    monkeypatch.setattr(issuance, "SupabaseDocumentStorage", ReviewStorage)
    monkeypatch.setattr(mail, "SupabaseDocumentStorage", ReviewStorage)
    settings.DEKOPEN_PUBLIC_APP_URL = "https://quotation.example.test"


def ready_case(org, actor):
    project, position, operation = _seed_project(org, actor)
    terms = {
        **document_preferences({})["commercial_terms"],
        "delivery_text": "20 días hábiles",
        "installation_text": "Instalación incluida",
        "exclusions": "Pintura",
        "warranty": "12 meses",
    }
    import json

    with as_user(actor):
        current = one("SELECT updated_at FROM projects WHERE id=%s", [project])["updated_at"]
        issuance.save_customer(
            org_id=org,
            project_id=project,
            data={
                "client_name": "Cliente de obra",
                "client_rut": "12345678-5",
                "client_email": "cliente@example.test",
                "delivery_address": "Obra Norte",
                "expected_updated_at": current,
            },
        )
        with documentary_backend():
            write(
                "UPDATE project_documentary_inputs SET commercial_terms=%s::jsonb,quotation_valid_until='2999-01-01' WHERE project_id=%s",
                [json.dumps(terms), project],
            )
    return project, position, operation


def review(org, actor, project, operation):
    with issuance.provisional_uploads(), as_user(actor):
        return issuance.prepare_preview(
            org_id=org, actor_id=actor, project_id=project, pricing_operation_id=operation
        )


def intent(preview):
    return {
        "preview_id": preview["id"],
        "expected_document_sha256": preview["file_sha256"],
        "expected_snapshot_sha256": preview["snapshot_sha256"],
        "expected_recipient": preview["recipient"],
        "confirmed": True,
    }


def issue(org, actor, project, preview):
    with issuance.provisional_uploads(), as_user(actor):
        return issuance.issue_preview(
            org_id=org, actor_id=actor, project_id=project, role="OWNER", data=intent(preview)
        )


def test_private_review_creates_no_capability_and_is_bound_to_actor_tenant(documentary_tenant):
    org, other, users, other_user = documentary_tenant
    owner = users["OWNER"]
    project, _, operation = ready_case(org, owner)
    preview = review(org, owner, project, operation)
    assert len(FakeStorage.uploads) == 1
    assert next(iter(FakeStorage.uploads.values())).startswith(b"%PDF-")
    assert rows("SELECT id FROM project_versions WHERE project_id=%s", [project]) == []
    assert rows("SELECT id FROM customer_approvals WHERE project_id=%s", [project]) == []
    assert rows("SELECT id FROM mail_outbox WHERE project_id=%s", [project]) == []
    with as_user(owner), documentary_backend():
        row = one("SELECT * FROM quotation_previews WHERE id=%s", [preview["id"]])
        token = crypto.open_message(row["token_ciphertext"], org_id=org, mail_id=row["id"])["token"]
        assert token not in row["token_ciphertext"]
    with (
        transaction.atomic(),
        portal.portal_backend(),
        pytest.raises(DocumentaryError, match="quote_not_found"),
    ):
        portal._approval_for_token(token)
    for actor, tenant in [
        (users["ESTIMATOR"], org),
        (other_user, other),
        (users["INSTALLER"], org),
    ]:
        with as_user(actor), pytest.raises(DocumentaryError, match="quotation_preview_not_found"):
            issuance.preview_access(
                org_id=tenant, actor_id=actor, project_id=project, preview_id=preview["id"]
            )
    with pytest.raises(DatabaseError, match="quotation_review_immutable"), transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL ROLE postgres")
        write(
            "UPDATE quotation_previews SET expires_at=expires_at+interval '1 minute' WHERE id=%s",
            [preview["id"]],
        )


def test_one_review_seals_exact_bytes_and_one_mail_then_recovers_receipt(documentary_tenant):
    org, _, users, _ = documentary_tenant
    owner = users["OWNER"]
    project, _, operation = ready_case(org, owner)
    preview = review(org, owner, project, operation)
    content = next(iter(FakeStorage.uploads.values()))
    result = issue(org, owner, project, preview)
    repeated = issue(org, owner, project, preview)
    assert result["created"] and not repeated["created"] and result["id"] == repeated["id"]
    assert result["mail"]["id"] == repeated["mail"]["id"]
    assert result["production_allowed"] == preview["production_allowed"]
    assert result["documentary_complete"] == preview["documentary_complete"]
    artifact = one("SELECT * FROM document_artifacts WHERE id=%s", [result["artifact_id"]])
    assert artifact["file_sha256"] == preview["file_sha256"]
    assert FakeStorage.uploads[artifact["storage_object_key"]] == content
    version = one("SELECT * FROM project_versions WHERE id=%s", [result["id"]])
    assert version["snapshot_sha256"] == preview["snapshot_sha256"]
    assert version["emitted_at"] == preview["document_date"]
    saved = one("SELECT * FROM mail_outbox WHERE id=%s", [result["mail"]["id"]])
    message = crypto.open_message(saved["content_ciphertext"], org_id=org, mail_id=saved["id"])
    assert base64.b64decode(message["attachments"][0]["data"]) == content
    assert len(rows("SELECT id FROM quotation_issues WHERE project_id=%s", [project])) == 1
    assert len(rows("SELECT id FROM customer_approvals WHERE project_id=%s", [project])) == 1
    assert len(rows("SELECT id FROM mail_outbox WHERE project_id=%s", [project])) == 1
    assert len(rows("SELECT id FROM job_runs WHERE org_id=%s AND type='mail.deliver'", [org])) == 1
    with pytest.raises(DatabaseError, match="quotation_issue_immutable"), transaction.atomic():
        write("DELETE FROM quotation_issues WHERE project_id=%s", [project])


@pytest.mark.parametrize("mutation", ["confirmation", "customer", "terms", "bytes", "expiration"])
def test_stale_or_corrupt_review_cannot_seal_or_queue_mail(
    documentary_tenant, mutation, monkeypatch
):
    org, _, users, _ = documentary_tenant
    owner = users["OWNER"]
    project, _, operation = ready_case(org, owner)
    preview = review(org, owner, project, operation)
    data = intent(preview)
    expected = "quotation_preview_stale"
    if mutation == "confirmation":
        data["expected_recipient"] = "otro@example.test"
    elif mutation == "customer":
        with as_user(owner):
            current = one("SELECT updated_at FROM projects WHERE id=%s", [project])["updated_at"]
            issuance.save_customer(
                org_id=org,
                project_id=project,
                data={
                    "client_name": "Otro cliente",
                    "client_rut": "12345678-5",
                    "client_email": "otro@example.test",
                    "delivery_address": "Obra Norte",
                    "expected_updated_at": current,
                },
            )
    elif mutation == "terms":
        with as_user(owner), documentary_backend():
            write(
                "UPDATE project_documentary_inputs SET payment_terms='Pago corregido' WHERE project_id=%s",
                [project],
            )
    elif mutation == "bytes":
        FakeStorage.uploads[next(iter(FakeStorage.uploads))] = b"tampered"
        expected = "quotation_preview_integrity_failed"
    else:
        old = issuance._preview_row
        monkeypatch.setattr(
            issuance,
            "_preview_row",
            lambda **kw: {
                **old(**kw),
                "expires_at": datetime.now(timezone.utc) - timedelta(seconds=1),
            },
        )
        expected = "quotation_preview_expired"
    with (
        pytest.raises(DocumentaryError, match=expected),
        issuance.provisional_uploads(),
        as_user(owner),
    ):
        issuance.issue_preview(
            org_id=org, actor_id=owner, project_id=project, role="OWNER", data=data
        )
    assert rows("SELECT id FROM project_versions WHERE project_id=%s", [project]) == []
    assert rows("SELECT id FROM mail_outbox WHERE project_id=%s", [project]) == []
    assert rows("SELECT id FROM customer_approvals WHERE project_id=%s", [project]) == []


def test_mail_failure_rolls_back_seal_and_removes_only_attempt_owned_upload(
    documentary_tenant, monkeypatch
):
    org, _, users, _ = documentary_tenant
    owner = users["OWNER"]
    project, _, operation = ready_case(org, owner)
    preview = review(org, owner, project, operation)
    before = dict(FakeStorage.uploads)

    def fail(**kwargs):
        raise RuntimeError("mail boundary failure")

    monkeypatch.setattr(issuance, "send_quote", fail)
    with pytest.raises(RuntimeError, match="mail boundary"), transaction.atomic():
        issue(org, owner, project, preview)
    assert FakeStorage.uploads == before
    assert rows("SELECT id FROM project_versions WHERE project_id=%s", [project]) == []
    assert rows("SELECT id FROM customer_approvals WHERE project_id=%s", [project]) == []
    assert one("SELECT status FROM projects WHERE id=%s", [project])["status"] == "DRAFT"


def test_deadline_is_shared_by_portal_and_mail_and_regeneration_is_idempotent(
    documentary_tenant, monkeypatch
):
    org, _, users, _ = documentary_tenant
    owner = users["OWNER"]
    project, _, operation = ready_case(org, owner)
    preview = review(org, owner, project, operation)
    result = issue(org, owner, project, preview)
    token = result["path"].rsplit("/", 1)[-1]
    approval_id = UUID(str(result["approval_id"]))
    original = one("SELECT expires_at FROM customer_approvals WHERE id=%s", [approval_id])[
        "expires_at"
    ]
    deadline = datetime.now(timezone.utc) + timedelta(hours=1)
    with as_user(owner):
        record = link_controls.change_deadline(
            org_id=org,
            project_id=project,
            approval_id=approval_id,
            actor_id=owner,
            data={"confirmed": True, "expected_expires_at": original, "expires_at": deadline},
        )
        assert record[0]["expires_at"] == deadline.isoformat()
        assert record[0]["original_expires_at"] == original.isoformat()
    with transaction.atomic(), portal.portal_backend():
        assert portal._approval_for_token(token)["expires_at"] == deadline
    with (
        pytest.raises(DatabaseError, match="document_approval_identity_immutable"),
        transaction.atomic(),
    ):
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL ROLE postgres")
        write("UPDATE customer_approvals SET expires_at=%s WHERE id=%s", [deadline, approval_id])
    # The access projection alone expires. The original DOCUMENT identity stays intact.
    with as_user(owner), documentary_backend():
        write(
            "INSERT INTO quote_link_deadlines(org_id,project_id,approval_id,expires_at,created_by) VALUES(%s,%s,%s,now()-interval '1 second',%s)",
            [org, project, approval_id, owner],
        )
    from analytics.today import quotation_rows, quote_public
    with as_user(owner):
        follow_up = quotation_rows(org)
        assert follow_up[0]["expires_at"] < datetime.now(timezone.utc)
        assert quote_public(follow_up[0], datetime.now(timezone.utc).date())["state"] == "link_expired"
        assert follow_up[0]["id"] == project
    with (
        pytest.raises(DocumentaryError, match="quote_expired"),
        transaction.atomic(),
        portal.portal_backend(),
    ):
        portal._approval_for_token(token)
    with mail.mail_backend():
        row = one("SELECT * FROM mail_outbox WHERE id=%s", [result["mail"]["id"]])
    message = crypto.open_message(row["content_ciphertext"], org_id=org, mail_id=row["id"])
    with mail.mail_backend(), pytest.raises(ValueError, match="mail_quote_link_inactive"):
        mail._check_live(row, message)
    monkeypatch.setattr(portal, "generate_artifact", lambda **kw: ({}, False))
    with as_user(owner):
        regenerated = link_controls.regenerate(
            org_id=org,
            project_id=project,
            approval_id=approval_id,
            actor_id=owner,
            role="OWNER",
            confirmed=True,
        )
        replay = link_controls.regenerate(
            org_id=org,
            project_id=project,
            approval_id=approval_id,
            actor_id=owner,
            role="OWNER",
            confirmed=True,
        )
        assert regenerated["path"] == replay["path"]
    with transaction.atomic(), portal.portal_backend():
        assert portal._approval_for_token(regenerated["token"])["status"] == "PENDING"
    assert len(rows("SELECT id FROM customer_approvals WHERE project_id=%s", [project])) == 2
    assert len(FakeStorage.uploads) == 2


def test_two_concurrent_clicks_and_lost_response_produce_one_receipt(
    documentary_committed_tenant, monkeypatch
):
    org, _, users, _ = documentary_committed_tenant
    owner = users["OWNER"]
    project, _, operation = ready_case(org, owner)
    token = _freeze_token(owner)
    monkeypatch.setattr(issuance_views, "verified_request_token", lambda request: token)
    request = SimpleNamespace(headers={"X-Organization-ID": str(org)})
    preview = issuance_views.guided_with_retry(
        request=request, project_id=project, data={"pricing_operation_id": operation}, issuing=False
    )

    def click(_):
        close_old_connections()
        try:
            return issuance_views.guided_with_retry(
                request=request, project_id=project, data=intent(preview), issuing=True
            )
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(click, range(2)))
    assert sorted(result["created"] for result in results) == [False, True]
    assert results[0]["id"] == results[1]["id"]
    assert results[0]["mail"]["id"] == results[1]["mail"]["id"]
    assert len(rows("SELECT id FROM quotation_issues WHERE project_id=%s", [project])) == 1
    assert len(rows("SELECT id FROM mail_outbox WHERE project_id=%s", [project])) == 1
