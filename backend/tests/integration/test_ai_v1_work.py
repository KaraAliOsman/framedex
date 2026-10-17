"""V1 delegated work: reversible presentation and calculation without writes."""

from uuid import uuid4
from decimal import Decimal

from django.db import DatabaseError, transaction
import pytest

from ai_gateway import presentation, quotation
from authentication.errors import ContractAPIException
from backend.tests.integration.test_shot08_pricing import owner_client
from backend.tests.integration.test_shot09_documentary import (
    documentary_tenant as documentary_tenant, as_user, _seed_project,
)
from pricing.repository import rows
from projects import org_branding

pytestmark = pytest.mark.rls_integration


def test_presentation_is_previewed_replayed_and_reversed_once(documentary_tenant):
    org, other, users, outsider = documentary_tenant
    key = str(uuid4())
    with as_user(users["OWNER"]):
        original = org_branding.get_branding(org_id=org)["document_preferences"]
        sample = presentation.preview(org_id=org, user_id=users["OWNER"], patch={
            "quotation_layout": "COMPACT", "presentation_title": "Su próxima obra",
            "portal_intro": "Revise sus ventanas y converse con nuestro equipo.",
        })
        assert org_branding.get_branding(org_id=org)["document_preferences"] == original
        request = dict(org_id=org, user_id=users["OWNER"], patch=sample["patch"],
                       before_sig=sample["before_sig"], operation_key=key)
        applied = presentation.apply(**request)
        assert presentation.apply(**request) == {**applied, "replayed": True}
        assert presentation.operation_state(org_id=org, user_id=users["OWNER"], operation_key=key)["state"] == "APPLIED"
        assert org_branding.get_branding(org_id=org)["document_preferences"]["quotation_layout"] == "COMPACT"
        reversed_change = presentation.undo(org_id=org, user_id=users["OWNER"], operation_id=applied["operation_id"])
        assert org_branding.get_branding(org_id=org)["document_preferences"] == original
        assert presentation.undo(org_id=org, user_id=users["OWNER"], operation_id=applied["operation_id"]) == {**reversed_change, "replayed": True}
        assert presentation.operation_state(org_id=org, user_id=users["OWNER"], operation_key=key)["state"] == "UNDONE"
        assert len(rows("SELECT id FROM public.presentation_changes WHERE org_id=%s", [org])) == 2
        with pytest.raises(DatabaseError), transaction.atomic():
            rows("UPDATE public.presentation_changes SET operation_key='rewritten' WHERE org_id=%s RETURNING id", [org])
    with as_user(outsider):
        assert rows("SELECT id FROM public.presentation_changes WHERE org_id=%s", [org]) == []
        assert presentation.operation_state(org_id=other, user_id=outsider, operation_key=key)["operation_id"] is None


def test_presentation_rejects_changed_samples_and_preserves_later_manual_edits(documentary_tenant):
    org, _, users, _ = documentary_tenant
    with as_user(users["OWNER"]):
        sample = presentation.preview(org_id=org, user_id=users["OWNER"], patch={"presentation_title": "Primera propuesta"})
        applied = presentation.apply(org_id=org, user_id=users["OWNER"], patch=sample["patch"], before_sig=sample["before_sig"], operation_key=str(uuid4()))
        org_branding.save_branding(org_id=org, data={"document_preferences": {"presentation_intro": "Edición manual posterior"}})
        with pytest.raises(ContractAPIException) as stale:
            presentation.undo(org_id=org, user_id=users["OWNER"], operation_id=applied["operation_id"])
        assert stale.value.contract_code == "presentation_stale"
        with pytest.raises(ContractAPIException) as stale:
            presentation.apply(org_id=org, user_id=users["OWNER"], patch=sample["patch"], before_sig=sample["before_sig"], operation_key=str(uuid4()))
        assert stale.value.contract_code == "presentation_stale"
        assert org_branding.get_branding(org_id=org)["document_preferences"]["presentation_intro"] == "Edición manual posterior"


def test_presentation_http_is_owner_only_and_refuses_arbitrary_configuration(documentary_tenant):
    org, _, users, _ = documentary_tenant
    path = "/api/v1/ai/presentation/preview/"
    for role in ("ESTIMATOR", "WORKSHOP_MANAGER", "INSTALLER"):
        response = owner_client(users[role]).post(path, {"patch": {"accent": "GRAPHITE"}}, format="json", HTTP_X_ORGANIZATION_ID=str(org))
        assert response.status_code == 403
    response = owner_client(users["OWNER"]).post(path, {"patch": {"role": "OWNER", "javascript": "alert(1)"}}, format="json", HTTP_X_ORGANIZATION_ID=str(org))
    assert response.status_code == 400


def test_quotation_prepares_exact_sale_without_applying_or_exposing_cost(documentary_tenant):
    org, _, users, _ = documentary_tenant
    project, _, _ = _seed_project(org, users["OWNER"], apply_pricing=False)
    with as_user(users["OWNER"]):
        operations_before = rows("SELECT id FROM public.pricing_operations WHERE org_id=%s", [org])
    with as_user(users["ESTIMATOR"]):
        before = rows("SELECT updated_at,total_price_gross FROM public.projects WHERE id=%s", [project])
        result = quotation.prepare(org_id=org, user_id=users["ESTIMATOR"], project_id=project)
        assert result["valid"] and not result["price_applied"]
        assert result["totals"]["gross"] is not None and result["lines"]
        assert result["request"]["target_margin"] == Decimal("0.3500")
        assert not any("cost" in key for key in result)
        assert not any("cost" in key for line in result["lines"] for key in line)
        assert rows("SELECT updated_at,total_price_gross FROM public.projects WHERE id=%s", [project]) == before
    with as_user(users["OWNER"]):
        assert rows("SELECT id FROM public.pricing_operations WHERE org_id=%s", [org]) == operations_before
    with as_user(users["WORKSHOP_MANAGER"]), pytest.raises(ContractAPIException) as forbidden:
        quotation.prepare(org_id=org, user_id=users["WORKSHOP_MANAGER"], project_id=project)
    assert forbidden.value.status_code == 403
