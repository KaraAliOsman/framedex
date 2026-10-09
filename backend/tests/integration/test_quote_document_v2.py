"""Real Postgres: transactional QR, independent sharing, immutable settings."""
from copy import deepcopy
from decimal import Decimal
from uuid import UUID, uuid4

from django.db import DatabaseError, transaction
import pytest

from backend.tests.integration.test_shot09_documentary import (
    documentary_tenant as documentary_tenant, as_user, _seed_project, _freeze, FakeStorage,
)
from documents import artifacts
from documents.preferences import document_preferences
from documents.repository import DocumentaryError, documentary_backend, one, rows, write
from documents.service import revision_snapshot, _sealed_alternatives, prepare_documentary_inputs, save_documentary_inputs
from portal import service as portal
from portal.document_links import document_portal_url
from projects.org_branding import save_branding
from projects import service as projects
from backend.tests.integration.test_shot10_revision_lifecycle import price_current

pytestmark = pytest.mark.rls_integration


def frozen_case(org, owner):
    project, position, operation = _seed_project(org, owner)
    version = _freeze(org, owner, project, operation)
    return project, position, UUID(version["id"])


def test_pdf_link_rollback_encryption_scope_and_immutable_identity(documentary_tenant, settings):
    org, other, users, _ = documentary_tenant
    project, _, version_id = frozen_case(org, users["OWNER"])
    settings.DEKOPEN_PUBLIC_APP_URL = "https://quote.example.test"
    with as_user(users["ESTIMATOR"]), documentary_backend():
        version, _ = revision_snapshot(version_id, org)
        with transaction.atomic():
            document_portal_url(org_id=org, version=version, actor_id=users["ESTIMATOR"])
            transaction.set_rollback(True)
        assert rows("SELECT id FROM document_portal_links WHERE org_id=%s", [org]) == []
        assert rows("SELECT id FROM customer_approvals WHERE org_id=%s", [org]) == []
        url = document_portal_url(org_id=org, version=version, actor_id=users["ESTIMATOR"])
        assert document_portal_url(org_id=org, version=version, actor_id=users["ESTIMATOR"]) == url
        link = one("SELECT * FROM document_portal_links WHERE project_version_id=%s", [version_id])
        assert url.rsplit("/", 1)[-1] not in link["token_ciphertext"]
        for field, value in [("token_ciphertext", "tampered"), ("org_id", str(other))]:
            with pytest.raises(DatabaseError, match="permission denied"), transaction.atomic():
                write(f"UPDATE document_portal_links SET {field}=%s WHERE id=%s", [value, link["id"]])
        with pytest.raises(DatabaseError, match="document_approval_identity_immutable"), transaction.atomic():
            write("UPDATE customer_approvals SET link_source='SHARE' WHERE id=%s", [link["approval_id"]])
        with pytest.raises(DatabaseError, match="document_portal_link_scope_mismatch"), transaction.atomic():
            write("INSERT INTO document_portal_links(org_id,project_version_id,approval_id,token_ciphertext) VALUES(%s,%s,%s,'fake')", [other, version_id, uuid4()])
    with as_user(users["ESTIMATOR"]), documentary_backend():
        assert rows("SELECT id FROM document_portal_links WHERE org_id=%s", [other]) == []
    with as_user(users["INSTALLER"]), documentary_backend():
        with pytest.raises(DatabaseError), transaction.atomic():
            document_portal_url(org_id=org, version=version, actor_id=users["INSTALLER"])


def test_share_preserves_printed_qr_and_revoke_does_not_change_pdf(documentary_tenant, monkeypatch):
    org, _, users, _ = documentary_tenant
    project, _, version_id = frozen_case(org, users["OWNER"])
    FakeStorage.uploads = {}
    monkeypatch.setattr(artifacts, "SupabaseDocumentStorage", FakeStorage)
    with as_user(users["OWNER"]):
        artifact, created = artifacts.generate_artifact(org_id=org, actor_id=users["OWNER"], role="OWNER",
            project_version_id=version_id, order_id=None, document_type="DOC-01", file_format="PDF")
        assert created
        with documentary_backend():
            version, _ = revision_snapshot(version_id, org)
            url = document_portal_url(org_id=org, version=version, actor_id=users["OWNER"])
        token = url.rsplit("/", 1)[-1]
        portal.share_quote(org_id=org, project_id=project, actor_id=users["OWNER"], role="OWNER")
        portal.share_quote(org_id=org, project_id=project, actor_id=users["OWNER"], role="OWNER")
        approvals = portal.list_approvals(org_id=org, project_id=project)
        printed = next(row for row in approvals if row["link_source"] == "DOCUMENT")
        assert printed["status"] == "PENDING"
        with transaction.atomic(), portal.portal_backend():
            approval = portal._approval_for_token(token)
            assert str(approval["project_version_id"]) == str(version_id)
        saved_bytes = deepcopy(FakeStorage.uploads)
        portal.revoke_link(org_id=org, project_id=project, approval_id=UUID(printed["id"]), actor_id=users["OWNER"])
        with pytest.raises(DocumentaryError, match="quote_revoked"), transaction.atomic(), portal.portal_backend():
            portal._approval_for_token(token)
        reused, created = artifacts.generate_artifact(org_id=org, actor_id=users["OWNER"], role="OWNER",
            project_version_id=version_id, order_id=None, document_type="DOC-01", file_format="PDF")
        assert not created and reused["id"] == artifact["id"]
        assert FakeStorage.uploads == saved_bytes


def test_saved_terms_and_preferences_survive_updates_and_seal(documentary_tenant):
    org, _, users, _ = documentary_tenant
    project, _, operation = _seed_project(org, users["OWNER"])
    prefs = document_preferences({"paper": "A4", "accent": "GRAPHITE", "legal_footer": "Empresa del sur"})
    with as_user(users["OWNER"]):
        save_branding(org_id=org, data={"commercial_name": "Marca propia", "document_preferences": prefs})
        result = save_branding(org_id=org, data={"document_preferences": prefs})
        assert result["commercial_name"] == "Marca propia"
        with documentary_backend():
            write("UPDATE project_documentary_inputs SET commercial_terms=%s::jsonb WHERE project_id=%s", ['{"payment_schedule":[{"label":"Al aprobar","share":"0.5"},{"label":"Entrega","share":"0.5"}]}', project])
        frozen = _freeze(org, users["OWNER"], project, operation)
        _, snapshot = revision_snapshot(UUID(frozen["id"]), org)
        assert snapshot["organization"]["document_preferences"] == prefs
        assert snapshot["project"]["commercial_terms"]["payment_schedule"][0]["share"] == "0.5"
        save_branding(org_id=org, data={"document_preferences": document_preferences({"paper": "OFICIO"})})
        _, after = revision_snapshot(UUID(frozen["id"]), org)
        assert after == snapshot
        with documentary_backend(), pytest.raises(DatabaseError), transaction.atomic():
            write("UPDATE project_documentary_inputs SET commercial_terms='{}' WHERE project_id=%s", [project])


def test_alternative_scope_and_hash_are_verified_and_defaults_are_not_backfilled(documentary_tenant):
    org, other, users, _ = documentary_tenant
    project, _, version_id = frozen_case(org, users["OWNER"])
    different, _, _ = _seed_project(org, users["OWNER"])
    with as_user(users["OWNER"]), documentary_backend():
        assert prepare_documentary_inputs(org_id=org, project_id=different)["commercial_terms"] == {}
    with as_user(users["OWNER"]), documentary_backend():
        selected = _sealed_alternatives([version_id], project, org)
        assert selected[0]["project"]["code"] and "alternatives" not in selected[0]
        with pytest.raises(DocumentaryError, match="scope_mismatch"):
            _sealed_alternatives([version_id], different, org)
        with pytest.raises(DocumentaryError):
            _sealed_alternatives([version_id], project, other)
        with pytest.raises(DatabaseError, match="quote_alternative_scope_mismatch"), transaction.atomic():
            write("UPDATE project_documentary_inputs SET alternative_version_ids=%s::uuid[] WHERE project_id=%s", [[str(version_id)], different])


@pytest.mark.parametrize("failure", ["render", "upload"])
def test_failed_pdf_generation_leaves_no_approval_or_capability(documentary_tenant, monkeypatch, failure):
    org, _, users, _ = documentary_tenant
    _, _, version_id = frozen_case(org, users["OWNER"])
    FakeStorage.uploads = {}
    FakeStorage.deleted = []
    monkeypatch.setattr(artifacts, "SupabaseDocumentStorage", FakeStorage)
    def fail(*args, **kwargs):
        raise RuntimeError("simulated documentary boundary failure")
    if failure == "render":
        monkeypatch.setattr(artifacts, "render_pdf_document", fail)
    else:
        original = FakeStorage.upload_immutable
        def interrupted_upload(self, *args):
            original(self, *args)
            fail()
        monkeypatch.setattr(FakeStorage, "upload_immutable", interrupted_upload)
    with as_user(users["OWNER"]):
        with pytest.raises(RuntimeError, match="boundary failure"):
            artifacts.generate_artifact(org_id=org, actor_id=users["OWNER"], role="OWNER",
                project_version_id=version_id, order_id=None, document_type="DOC-01", file_format="PDF")
        with documentary_backend():
            assert rows("SELECT id FROM document_portal_links WHERE org_id=%s", [org]) == []
            assert rows("SELECT id FROM customer_approvals WHERE org_id=%s", [org]) == []
            assert rows("SELECT id FROM document_artifacts WHERE org_id=%s", [org]) == []
    assert FakeStorage.uploads == {}


def test_successor_seals_selected_alternative_without_adding_its_price(documentary_tenant):
    org, _, users, _ = documentary_tenant
    owner = users["OWNER"]
    project, _, version_a = frozen_case(org, owner)
    with as_user(owner), documentary_backend():
        _, before = revision_snapshot(version_a, org)
    with as_user(owner):
        projects.start_successor(org, project)
        with documentary_backend():
            prepared = prepare_documentary_inputs(org_id=org, project_id=project)
        fields = ("position_id", "calculation_hash", "location_tag", "manufacturing_placement_policy_id",
            "handle_requirement_policy_id", "reinforcement_cut_policy_id", "workshop_annotations",
            "structural_inputs", "glass_polishing", "handle_intents", "accessory_schedule", "legacy_handle_migration_confirmed")
        from documents.serializers import DocumentaryInputsSerializer
        data = {"payment_terms": prepared["payment_terms"], "quotation_valid_until": prepared["quotation_valid_until"],
            "commercial_terms": prepared["commercial_terms"], "alternative_version_ids": [str(version_a)],
            "positions": [{key: item[key] for key in fields} for item in prepared["positions"]]}
        serializer = DocumentaryInputsSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        save_documentary_inputs(org_id=org, actor_id=owner, project_id=project, data=serializer.validated_data)
        with documentary_backend():
            assert prepare_documentary_inputs(org_id=org, project_id=project)["alternative_version_ids"] == [version_a]
        operation = price_current(org, owner, "OWNER", project)
        issued = _freeze(org, owner, project, operation)
        with documentary_backend():
            _, after = revision_snapshot(UUID(issued["id"]), org)
            _, unchanged = revision_snapshot(version_a, org)
    assert issued["revision_code"] == "REV-B" and unchanged == before
    assert after["alternatives"][0]["project"] == before["project"]
    assert after["alternatives"][0]["positions"] == before["positions"]
    assert Decimal(after["project"]["total_price_gross"]) == Decimal(after["pricing"]["result"]["project_gross"])
    from documents.renderers import _doc01
    assert "No incluida en el total de esta propuesta" in _doc01(after)
