"""A private PDF reviews working money; only the human issue applies it."""

from decimal import Decimal as D
from uuid import UUID

from django.db import transaction
import pytest

from authentication.errors import ContractAPIException
from backend.tests.integration.test_guided_quotation import (
    documentary_tenant as documentary_tenant, private_storage as private_storage,
    ready_case, intent, issue, as_user, ReviewStorage,
)
from backend.tests.integration.test_simple_pricing_policy import policy_values
from documents import issuance
from documents.repository import documentary_backend
from documents.service import revision_snapshot
from pricing.repository import commercial_backend, one, rows
from pricing.simple_policy import save_policy
from projects import service

pytestmark = pytest.mark.rls_integration


@pytest.mark.parametrize('advanced', [False, True])
@pytest.mark.parametrize('role', ['OWNER', 'ESTIMATOR'])
def test_review_without_apply_then_exact_issue_and_idempotent_replay(documentary_tenant, advanced, role):
    org, _, users, _ = documentary_tenant
    actor = users[role]
    project, _, _ = ready_case(org, users['OWNER'], apply_pricing=False)
    with as_user(users['OWNER']):
        save_policy(org, policy_values(use_advanced=advanced), 0, 'Mis precios')
    with as_user(actor):
        with issuance.provisional_uploads():
            preview = issuance.prepare_preview(org_id=org, actor_id=actor, project_id=project)
        assert service.editable(org, project)['id'] == project
        with commercial_backend():
            assert rows("SELECT id FROM pricing_operations WHERE project_id=%s AND state='APPLIED'", [project]) == []
        with documentary_backend():
            reviewed = one('SELECT snapshot_json,storage_object_key FROM quotation_previews WHERE id=%s', [preview['id']])
        reviewed_bytes = ReviewStorage().download(reviewed['storage_object_key'])
    with as_user(actor), issuance.provisional_uploads():
        emitted = issuance.issue_preview(org_id=org, actor_id=actor, project_id=project, role=role, data=intent(preview))
    assert emitted['created']
    with as_user(actor):
        _, frozen = revision_snapshot(UUID(str(emitted['id'])), org)
        assert frozen == service.decoded(reviewed['snapshot_json'])
        assert frozen['pricing']['request']['application_method'] == 'AT_ISSUE'
        with commercial_backend():
            applied = one("SELECT * FROM pricing_operations WHERE project_id=%s AND state='APPLIED'", [project])
            assert applied['approved_by'] == actor and applied['approved_at'] is not None
        with documentary_backend():
            artifact = one('SELECT storage_object_key FROM document_artifacts WHERE id=%s', [emitted['artifact_id']])
        assert ReviewStorage().download(artifact['storage_object_key']) == reviewed_bytes
    with as_user(users['OWNER']):
        save_policy(org, policy_values(margin='.50', use_advanced=advanced), 1, 'Solo nuevos borradores')
        assert revision_snapshot(UUID(str(emitted['id'])), org)[1] == frozen
    assert issue(org, actor, project, preview)['created'] is False


@pytest.mark.parametrize('change', ['policy', 'cost', 'quantity'])
@pytest.mark.parametrize('advanced', [False, True])
def test_changed_price_or_design_requires_a_new_pdf_and_never_applies(documentary_tenant, change, advanced):
    org, _, users, _ = documentary_tenant
    actor = users['OWNER']
    project, position, _ = ready_case(org, actor, apply_pricing=False)
    with as_user(actor), issuance.provisional_uploads():
        save_policy(org, policy_values(use_advanced=advanced), 0, 'Mis precios')
        preview = issuance.prepare_preview(org_id=org, actor_id=actor, project_id=project)
        if change == 'policy':
            save_policy(org, policy_values(margin='.50', use_advanced=advanced), 1, 'Nuevo margen')
        elif change == 'cost':
            rows('UPDATE cost_list_items SET unit_cost=unit_cost+1 WHERE org_id=%s RETURNING id', [org])
        else:
            current = service.position_row(org, position)
            public = service.position_public(current)
            service.save_position_metadata(org, project, {**public, 'quantity': 3})
        with pytest.raises(ContractAPIException) as rejected:
            issuance.issue_preview(org_id=org, actor_id=actor, project_id=project, role='OWNER', data=intent(preview))
        assert rejected.value.contract_code == 'quotation_preview_stale'
        with commercial_backend():
            assert rows("SELECT id FROM pricing_operations WHERE project_id=%s AND state='APPLIED'", [project]) == []
        assert service.editable(org, project)['id'] == project
        with documentary_backend():
            assert rows('SELECT id FROM quotation_issues WHERE project_id=%s', [project]) == []
        assert D(preview['total_price_gross']) > 0


def test_failure_after_application_rolls_back_price_and_keeps_review(documentary_tenant, monkeypatch):
    org, _, users, _ = documentary_tenant
    actor = users['OWNER']
    project, _, _ = ready_case(org, actor, apply_pricing=False)
    with as_user(actor), issuance.provisional_uploads():
        preview = issuance.prepare_preview(org_id=org, actor_id=actor, project_id=project)
    before = dict(ReviewStorage.uploads)

    def fail(**kwargs):
        raise RuntimeError('mail boundary failure')

    monkeypatch.setattr(issuance, 'send_quote', fail)
    with pytest.raises(RuntimeError, match='mail boundary'), transaction.atomic():
        issue(org, actor, project, preview)
    assert ReviewStorage.uploads == before
    with as_user(actor):
        assert service.editable(org, project)['id'] == project
        with commercial_backend():
            assert rows("SELECT id FROM pricing_operations WHERE project_id=%s AND state='APPLIED'", [project]) == []
        assert rows('SELECT id FROM project_versions WHERE project_id=%s', [project]) == []


def test_early_draft_renders_from_working_price_without_applying(documentary_tenant):
    org, _, users, _ = documentary_tenant
    actor = users['OWNER']
    project, _, _ = ready_case(org, actor, apply_pricing=False)
    with as_user(actor):
        content = issuance.draft_preview(org_id=org, actor_id=actor, project_id=project)
        assert content.startswith(b'%PDF-')
        assert service.editable(org, project)['id'] == project
        with commercial_backend():
            assert rows("SELECT id FROM pricing_operations WHERE project_id=%s AND state='APPLIED'", [project]) == []
