"""Active-organization resolution backed exclusively by RLS-visible memberships."""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast
from uuid import UUID

from django.db import connection
from rest_framework import status

from authentication.errors import contract_error
from authentication.types import Membership, OrganizationRole, TenantContext


class MembershipRepository:
    def list_active_for_user(self, user_id: UUID) -> tuple[Membership, ...]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT membership.org_id, organization.name, membership.role::text
                FROM public.tenancy_memberships AS membership
                JOIN public.tenancy_organizations AS organization
                  ON organization.id = membership.org_id
                WHERE membership.user_id = %s
                  AND membership.is_active = TRUE
                ORDER BY organization.name, membership.org_id
                """,
                [user_id],
            )
            rows: Sequence[tuple[object, object, object]] = cursor.fetchall()
        return tuple(
            Membership(
                organization_id=_as_uuid(row[0]),
                organization_name=str(row[1]),
                role=cast(OrganizationRole, str(row[2])),
            )
            for row in rows
        )


def _as_uuid(value: object) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))


def resolve_tenant_context(
    memberships: tuple[Membership, ...],
    organization_header: str | None,
) -> TenantContext:
    if not memberships:
        raise contract_error(
            status.HTTP_403_FORBIDDEN,
            "no_active_membership",
            "User has no active membership",
        )

    requested_id: UUID | None = None
    if organization_header is not None:
        try:
            requested_id = UUID(organization_header)
        except ValueError as error:
            raise contract_error(
                status.HTTP_400_BAD_REQUEST,
                "invalid_organization_id",
                "X-Organization-ID must be a UUID",
            ) from error

    if requested_id is not None:
        selected = next(
            (
                membership
                for membership in memberships
                if membership.organization_id == requested_id
            ),
            None,
        )
        if selected is None:
            raise contract_error(
                status.HTTP_403_FORBIDDEN,
                "organization_access_denied",
                "User does not have an active membership in this organization",
            )
        return TenantContext(active_organization=selected, memberships=memberships)

    if len(memberships) > 1:
        raise contract_error(
            status.HTTP_409_CONFLICT,
            "organization_selection_required",
            "Select an active organization",
            extra={"memberships": [item.public_dict() for item in memberships]},
        )
    return TenantContext(active_organization=memberships[0], memberships=memberships)


def enforce_owner_mfa(context: TenantContext, aal: str) -> None:
    if context.active_organization.role == "OWNER" and aal != "aal2":
        raise contract_error(
            status.HTTP_403_FORBIDDEN,
            "mfa_required",
            "OWNER requires aal2",
            error_extra={"required_aal": "aal2"},
        )
