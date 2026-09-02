"""Deterministic assembly helpers for the SHOT-03 base bill of materials."""

from __future__ import annotations

from collections.abc import Sequence

from dekopen_engine.models import (
    EngineResult,
    GlassPiece,
    ProfileCut,
    ProfileRole,
    ReinforcementPiece,
)

_PROFILE_ROLE_ORDER = {
    ProfileRole.FRAME: 0,
    ProfileRole.MULLION_V: 1,
    ProfileRole.MULLION_H: 2,
    ProfileRole.SASH: 3,
    ProfileRole.GLAZING_BEAD: 4,
    ProfileRole.INVERSOR: 5,
    ProfileRole.COUPLER: 6,
    ProfileRole.ADDITIONAL: 7,
}


def build_engine_result(
    *,
    profile_cuts: Sequence[ProfileCut],
    reinforcements: Sequence[ReinforcementPiece],
    glasses: Sequence[GlassPiece],
) -> EngineResult:
    """Copy and stably order BOM categories without recalculating geometry."""

    ordered_profile_cuts = sorted(
        profile_cuts,
        key=lambda cut: _PROFILE_ROLE_ORDER[cut.role],
    )
    ordered_reinforcements = sorted(
        reinforcements,
        key=lambda piece: _PROFILE_ROLE_ORDER[piece.role],
    )
    return EngineResult(
        profile_cuts=ordered_profile_cuts,
        reinforcements=ordered_reinforcements,
        glasses=list(glasses),
        hardware_items=[],
    )
