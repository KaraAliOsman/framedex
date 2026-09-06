from __future__ import annotations

from uuid import UUID

from engine.tests.catalog import demo_60_params as demo_60_params

from authentication.types import Membership, SupabaseUser, VerifiedSupabaseToken

USER_ID = UUID("10000000-0000-0000-0000-000000000001")
ORG_A_ID = UUID("20000000-0000-0000-0000-000000000001")
ORG_B_ID = UUID("20000000-0000-0000-0000-000000000002")
SYSTEM_ID = UUID("d0000000-0000-0000-0000-000000000001")


def authenticated_identity(
    *, aal: str = "aal1"
) -> tuple[SupabaseUser, VerifiedSupabaseToken]:
    user = SupabaseUser(id=USER_ID, email="user@example.com")
    token = VerifiedSupabaseToken(
        access_token="verified-token",
        claims={
            "sub": str(USER_ID),
            "exp": 4_102_444_800,
            "iss": "http://127.0.0.1:54321/auth/v1",
            "aud": "authenticated",
            "role": "authenticated",
            "aal": aal,
            "email": user.email,
        },
        user_id=USER_ID,
        email=user.email,
        aal="aal2" if aal == "aal2" else "aal1",
    )
    return user, token


def membership(
    organization_id: UUID = ORG_A_ID,
    *,
    role: str = "ESTIMATOR",
    name: str = "Taller A",
) -> Membership:
    valid_role = {
        "OWNER": "OWNER",
        "ESTIMATOR": "ESTIMATOR",
        "WORKSHOP_MANAGER": "WORKSHOP_MANAGER",
        "INSTALLER": "INSTALLER",
    }[role]
    return Membership(
        organization_id=organization_id,
        organization_name=name,
        role=valid_role,
    )
