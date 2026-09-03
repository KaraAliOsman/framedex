"""RLS-bound DB-to-engine parameter loader; it contains no geometry formulas."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
import json
from typing import cast
from uuid import UUID

from django.db import connection

from dekopen_engine import (
    EffectiveProfileArticle,
    GlazingBeadRule,
    HardwareKitRule,
    MaterialType,
    ProfileRole,
    RailType,
    SystemParams,
)


class SystemNotFound(LookupError):
    pass


class UnsupportedCatalogContract(ValueError):
    pass


def _decimal(value: object) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _article_from_row(row: Sequence[object], *, offset: int = 0) -> EffectiveProfileArticle:
    return EffectiveProfileArticle(
        sku=str(row[offset]),
        role=ProfileRole(str(row[offset + 1])),
        face_width_mm=_decimal(row[offset + 2]),
        welding_loss_mm=_decimal(row[offset + 3]),
        reinforcement_gap_mm=_decimal(row[offset + 4]),
        weight_kg_m=_decimal(row[offset + 5]),
        steel_weight_kg_m=_decimal(row[offset + 6]),
        reinforcement_sku=(
            str(row[offset + 7]) if row[offset + 7] is not None else None
        ),
    )


class SystemParamsRepository:
    def load_visible(self, system_id: UUID, active_org_id: UUID) -> SystemParams:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT code, depth_mm, material::text, sash_overlap_mm,
                       glass_clearance_white_mm, glass_clearance_foil_mm,
                       pulley_height_mm, central_overlap_mm,
                       sliding_lateral_clearance_mm, sliding_end_add_mm,
                       corner_bracket_loss_mm, hook_depth_mm,
                       door_threshold_mm, door_bottom_clearance_mm, rail_type
                FROM public.profile_systems
                WHERE id = %s AND is_active = TRUE
                  AND (is_global = TRUE OR org_id = %s)
                """,
                [system_id, active_org_id],
            )
            system = cursor.fetchone()
        if system is None:
            raise SystemNotFound

        articles = self._load_articles(system_id, active_org_id)
        rules = self._load_glazing_rules(system_id, active_org_id)
        kits = self._load_hardware_kits(system_id, active_org_id)
        frame = articles.get(ProfileRole.FRAME)
        if frame is None:
            raise UnsupportedCatalogContract("FRAME effective article is required")

        return SystemParams(
            system_code=str(system[0]),
            depth_mm=_decimal(system[1]),
            material=MaterialType(str(system[2])),
            effective_profile_articles=articles,
            glazing_bead_rules=rules,
            sash_overlap_mm=_decimal(system[3]),
            glass_clearance_white_mm=_decimal(system[4]),
            glass_clearance_foil_mm=_decimal(system[5]),
            pulley_height_mm=_decimal(system[6]),
            central_overlap_mm=_decimal(system[7]),
            sliding_lateral_clearance_mm=_decimal(system[8]),
            sliding_end_add_mm=_decimal(system[9]),
            corner_bracket_loss_mm=_decimal(system[10]),
            hook_depth_mm=_decimal(system[11]),
            door_threshold_mm=_decimal(system[12]),
            door_bottom_clearance_mm=_decimal(system[13]),
            rail_type=RailType(str(system[14])),
            pvc_weight_kg_m=frame.weight_kg_m,
            steel_weight_kg_m=frame.steel_weight_kg_m,
            available_hardware_kits=kits,
        )

    def _load_articles(
        self, system_id: UUID, active_org_id: UUID
    ) -> dict[ProfileRole, EffectiveProfileArticle]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT sku, role::text, face_width_mm, welding_loss_mm,
                       reinforcement_gap_mm, weight_kg_m, steel_weight_kg_m,
                       reinforcement_sku
                FROM public.profile_articles
                WHERE system_id = %s AND (org_id IS NULL OR org_id = %s)
                ORDER BY sku
                """,
                [system_id, active_org_id],
            )
            rows = cursor.fetchall()
        result: dict[ProfileRole, EffectiveProfileArticle] = {}
        for row in rows:
            article = _article_from_row(row)
            if article.role is ProfileRole.GLAZING_BEAD:
                continue
            if article.role in result:
                raise UnsupportedCatalogContract(
                    f"Multiple effective articles for role {article.role.value}"
                )
            result[article.role] = article
        return result

    def _load_glazing_rules(
        self, system_id: UUID, active_org_id: UUID
    ) -> dict[Decimal, GlazingBeadRule]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT matrix.glass_thickness_mm, matrix.bead_width_mm,
                       matrix.gasket_interior_mm, matrix.gasket_exterior_mm,
                       matrix.cut_add_mm,
                       article.sku, article.role::text, article.face_width_mm,
                       article.welding_loss_mm, article.reinforcement_gap_mm,
                       article.weight_kg_m, article.steel_weight_kg_m,
                       article.reinforcement_sku
                FROM public.glazing_bead_matrix AS matrix
                JOIN public.profile_articles AS article
                  ON article.id = matrix.bead_article_id
                WHERE matrix.system_id = %s AND matrix.is_active = TRUE
                  AND (matrix.org_id IS NULL OR matrix.org_id = %s)
                  AND article.system_id = matrix.system_id
                  AND (article.org_id IS NULL OR article.org_id = %s)
                ORDER BY matrix.glass_thickness_mm
                """,
                [system_id, active_org_id, active_org_id],
            )
            rows = cursor.fetchall()
        return {
            _decimal(row[0]): GlazingBeadRule(
                glass_thickness_mm=_decimal(row[0]),
                bead_article=_article_from_row(row, offset=5),
                bead_width_mm=_decimal(row[1]),
                gasket_interior_mm=_decimal(row[2]),
                gasket_exterior_mm=_decimal(row[3]),
                cut_add_mm=_decimal(row[4]),
            )
            for row in rows
        }

    def _load_hardware_kits(
        self, system_id: UUID, active_org_id: UUID
    ) -> list[HardwareKitRule]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT sku, name, opening_type, min_leaf_width_mm,
                       max_leaf_width_mm, min_leaf_height_mm, max_leaf_height_mm,
                       max_leaf_weight_kg, rail_type, carriages_qty,
                       stay_arms_qty, contents
                FROM public.hardware_kits
                WHERE system_id = %s AND is_active = TRUE
                  AND (org_id IS NULL OR org_id = %s)
                ORDER BY sku
                """,
                [system_id, active_org_id],
            )
            rows = cursor.fetchall()
        return [
            HardwareKitRule(
                sku=str(row[0]),
                name=str(row[1]),
                opening_type=str(row[2]),
                min_leaf_width_mm=_decimal(row[3]),
                max_leaf_width_mm=_decimal(row[4]),
                min_leaf_height_mm=_decimal(row[5]),
                max_leaf_height_mm=_decimal(row[6]),
                max_leaf_weight_kg=_decimal(row[7]),
                rail_type=RailType(str(row[8])),
                carriages_qty=int(cast(int, row[9])),
                stay_arms_qty=int(cast(int, row[10])),
                contents=(
                    json.loads(row[11])
                    if isinstance(row[11], str)
                    else cast(list[dict[str, str]], row[11])
                ),
            )
            for row in rows
        ]
