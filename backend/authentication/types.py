"""Typed authentication and tenancy values shared by DRF views."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

AssuranceLevel = Literal["aal1", "aal2"]
OrganizationRole = Literal["OWNER", "ESTIMATOR", "WORKSHOP_MANAGER", "INSTALLER"]


@dataclass(frozen=True, slots=True)
class SupabaseUser:
    id: UUID
    email: str

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_anonymous(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class VerifiedSupabaseToken:
    access_token: str
    claims: dict[str, object]
    user_id: UUID
    email: str
    aal: AssuranceLevel


@dataclass(frozen=True, slots=True)
class Membership:
    organization_id: UUID
    organization_name: str
    role: OrganizationRole

    def public_dict(self) -> dict[str, str]:
        return {
            "organization_id": str(self.organization_id),
            "organization_name": self.organization_name,
            "role": self.role,
        }


@dataclass(frozen=True, slots=True)
class TenantContext:
    active_organization: Membership
    memberships: tuple[Membership, ...]
