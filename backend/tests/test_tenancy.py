from __future__ import annotations

from uuid import UUID

import pytest

from authentication.errors import ContractAPIException
from authentication.tenancy import enforce_owner_mfa, resolve_tenant_context
from backend.tests.factories import ORG_A_ID, ORG_B_ID, membership


def assert_contract_error(error: pytest.ExceptionInfo[ContractAPIException], code: str) -> None:
    assert error.value.contract_code == code


def test_zero_memberships_is_forbidden() -> None:
    with pytest.raises(ContractAPIException) as error:
        resolve_tenant_context((), None)
    assert_contract_error(error, "no_active_membership")


def test_single_membership_auto_selects() -> None:
    selected = resolve_tenant_context((membership(),), None)
    assert selected.active_organization.organization_id == ORG_A_ID


def test_multiple_memberships_require_header() -> None:
    memberships = (
        membership(),
        membership(ORG_B_ID, name="Taller B"),
    )
    with pytest.raises(ContractAPIException) as error:
        resolve_tenant_context(memberships, None)
    assert_contract_error(error, "organization_selection_required")
    assert len(error.value.extra["memberships"]) == 2


def test_malformed_and_foreign_headers_fail_closed() -> None:
    with pytest.raises(ContractAPIException) as malformed:
        resolve_tenant_context((membership(),), "not-a-uuid")
    assert_contract_error(malformed, "invalid_organization_id")

    with pytest.raises(ContractAPIException) as foreign:
        resolve_tenant_context((membership(),), str(UUID(int=999)))
    assert_contract_error(foreign, "organization_access_denied")


def test_owner_requires_aal2_only_in_selected_owner_organization() -> None:
    owner = membership(role="OWNER")
    estimator = membership(ORG_B_ID, role="ESTIMATOR", name="Taller B")
    with pytest.raises(ContractAPIException) as error:
        enforce_owner_mfa(resolve_tenant_context((owner, estimator), str(ORG_A_ID)), "aal1")
    assert_contract_error(error, "mfa_required")

    enforce_owner_mfa(
        resolve_tenant_context((owner, estimator), str(ORG_A_ID)), "aal2"
    )
    enforce_owner_mfa(
        resolve_tenant_context((owner, estimator), str(ORG_B_ID)), "aal1"
    )
