from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from dekopen_engine import (
    EffectiveProfileArticle,
    GlazingBeadRule,
    MaterialType,
    ProfileRole,
    RailType,
    SystemParams,
)

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


def _article(
    sku: str,
    role: ProfileRole,
    face: str,
    welding: str,
    gap: str,
) -> EffectiveProfileArticle:
    return EffectiveProfileArticle(
        sku=sku,
        role=role,
        face_width_mm=Decimal(face),
        welding_loss_mm=Decimal(welding),
        reinforcement_gap_mm=Decimal(gap),
        weight_kg_m=Decimal("1.2000"),
        steel_weight_kg_m=Decimal("1.7000"),
    )


def demo_60_params() -> SystemParams:
    frame = _article("MARCO", ProfileRole.FRAME, "60.00", "6.00", "15.00")
    sash = _article("HOJA", ProfileRole.SASH, "75.00", "6.00", "15.00")
    mullion_v = _article("POSTE-V", ProfileRole.MULLION_V, "80.00", "0.00", "5.00")
    mullion_h = _article("POSTE-H", ProfileRole.MULLION_H, "80.00", "0.00", "5.00")
    bead_24 = _article("JQ-24", ProfileRole.GLAZING_BEAD, "24.00", "0.00", "15.00")
    bead_14 = _article("JQ-14", ProfileRole.GLAZING_BEAD, "14.00", "0.00", "15.00")
    bead_10 = _article("JQ-10", ProfileRole.GLAZING_BEAD, "10.00", "0.00", "15.00")
    beads = {
        Decimal("4.00"): (bead_24, "24.00", "3.00"),
        Decimal("5.00"): (bead_24, "24.00", "2.50"),
        Decimal("6.00"): (bead_24, "24.00", "2.00"),
        Decimal("20.00"): (bead_14, "14.00", "3.00"),
        Decimal("24.00"): (bead_10, "10.00", "3.00"),
    }
    return SystemParams(
        system_code="DEMO_60",
        depth_mm=Decimal("60.00"),
        material=MaterialType.PVC,
        effective_profile_articles={
            ProfileRole.FRAME: frame,
            ProfileRole.SASH: sash,
            ProfileRole.MULLION_V: mullion_v,
            ProfileRole.MULLION_H: mullion_h,
        },
        glazing_bead_rules={
            thickness: GlazingBeadRule(
                glass_thickness_mm=thickness,
                bead_article=values[0],
                bead_width_mm=Decimal(values[1]),
                gasket_interior_mm=Decimal(values[2]),
                gasket_exterior_mm=Decimal(values[2]),
                cut_add_mm=Decimal("9.00"),
            )
            for thickness, values in beads.items()
        },
        rebate_depth_mm=Decimal("20.00"),
        sash_overlap_mm=Decimal("8.00"),
        glass_clearance_white_mm=Decimal("5.00"),
        glass_clearance_foil_mm=Decimal("5.00"),
        central_overlap_mm=Decimal("40.00"),
        rail_type=RailType.DUAL,
    )
