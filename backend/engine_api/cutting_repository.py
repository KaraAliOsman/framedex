"""Visible catalog authorities for cutting; no geometry or packing formulas."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from django.db import connection

from dekopen_engine.cutting import (
    AmbiguousCuttingProfile,
    AmbiguousStockAuthority,
    CutMaterial,
    CuttingProfile,
    MissingCuttingProfile,
    MissingStockAuthority,
    StockRule,
)
from dekopen_engine.models import EngineResult
from engine_api.repository import SystemParamsRepository, _decimal


@dataclass(frozen=True)
class CuttingAuthorities:
    stocks: list[StockRule]
    reinforcement_skus: dict[str, str]
    reinforcement_ix: dict[str, Decimal | None]


def _positive_stock_length(value) -> Decimal:
    # NULL is UNKNOWN — the catalog never stated a commercial length, so the
    # optimizer has no bar to nest against. Refuse rather than invent one.
    if value is None:
        raise MissingStockAuthority(
            "Stock length unknown — declare commercial_length_mm on the article"
        )
    length = _decimal(value)
    if length <= Decimal("0"):
        raise MissingStockAuthority("Stock length must be positive")
    return length


def effective_scope(
    rows: list[tuple[object, ...]], org_id: UUID, scope_index: int
) -> list[tuple[object, ...]]:
    tenant = [row for row in rows if str(row[scope_index]) == str(org_id)]
    return tenant if tenant else [row for row in rows if row[scope_index] is None]


class CuttingRepository:
    def __init__(self, *, request_cache: bool = False):
        # Only an explicitly bounded read proposal can reuse authority. The
        # ordinary repository must see catalog changes between transactions.
        self._request_cache = request_cache
        self._visible_systems=set()
        self._profile_stocks={}
        self._reinforcement_stocks={}
        self._stock_catalogs = {}
        self._finish_authorities = {}

    def prefetch_stocks(self, system_id: UUID, org_id: UUID) -> None:
        """Read the same stock rows once inside a bounded authority snapshot.

        Scope, ambiguity, units and unknown lengths are still checked when a
        stock is requested. RLS applies to every SELECT, including mappings.
        """
        if not self._request_cache:
            raise ValueError("Stock prefetch requires a request-scoped repository")
        scope = (system_id, org_id)
        if scope in self._stock_catalogs:
            return
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT a.id, a.commercial_length_mm, a.material::text,
                          s.finish_authority IS NOT NULL, a.sku, s.finish_authority::text
                   FROM public.profile_articles a JOIN public.profile_systems s ON s.id=a.system_id
                   WHERE a.system_id=%s AND (a.org_id IS NULL OR a.org_id=%s) ORDER BY a.id""",
                [system_id, org_id],
            )
            articles = cursor.fetchall()
            ids = [article[0] for article in articles]
            mappings = {}
            for table in ("profile_purchase_mappings", "catalog_color_skus"):
                finish = "finish" if table == "catalog_color_skus" else "NULL"
                color_clause = " AND stock_color=finish" if table == "catalog_color_skus" else ""
                cursor.execute(
                    f"""SELECT id, commercial_sku, manufacturer_name, supplier_name,
                               purchase_unit, org_id, profile_article_id, {finish}
                        FROM public.{table}
                        WHERE profile_article_id=ANY(%s) AND is_active
                          AND (org_id IS NULL OR org_id=%s){color_clause} ORDER BY id""",
                    [ids, org_id],
                )
                mappings[table] = cursor.fetchall()
            cursor.execute(
                """SELECT id, sku, commercial_sku, manufacturer_name, supplier_name,
                          stock_length_mm, purchase_unit, ix_cm4, org_id,
                          parent_profile_article_id, is_default
                   FROM public.reinforcement_articles
                   WHERE system_id=%s AND is_active
                     AND (org_id IS NULL OR org_id=%s) ORDER BY id""",
                [system_id, org_id],
            )
            steel = cursor.fetchall()
        self._stock_catalogs[scope] = (articles, mappings, steel)

    def _stock_rows(self, query, parameters, prefetched=None):
        if prefetched is not None:
            return prefetched
        with connection.cursor() as cursor:
            cursor.execute(query, parameters)
            return cursor.fetchall()

    def cutting_profile(self, org_id: UUID, code: str | None = None) -> CuttingProfile:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT id, code, kerf_mm, head_trim_mm, tail_trim_mm, org_id
                   FROM public.cutting_profiles
                   WHERE is_active AND (org_id IS NULL OR org_id=%s)
                     AND ((%s IS NULL AND is_default) OR code=%s)
                   ORDER BY id""",
                [org_id, code, code],
            )
            rows = cursor.fetchall()
        if code is None:
            rows = effective_scope(rows, org_id, 5)
        if not rows:
            raise MissingCuttingProfile
        if len(rows) != 1:
            raise AmbiguousCuttingProfile
        row = rows[0]
        return CuttingProfile(
            id=str(row[0]),
            code=str(row[1]),
            kerf_mm=_decimal(row[2]),
            head_trim_mm=_decimal(row[3]),
            tail_trim_mm=_decimal(row[4]),
        )

    def profile_stock(self, system_id: UUID, org_id: UUID, sku: str, color: str) -> StockRule:
        if not self._request_cache:
            return self._profile_stock(system_id, org_id, sku, color)
        key=(system_id,org_id,sku,color)
        if key not in self._profile_stocks:
            self._profile_stocks[key]=self._profile_stock(system_id,org_id,sku,color)
        return self._profile_stocks[key]

    def _profile_stock(self, system_id: UUID, org_id: UUID, sku: str, color: str) -> StockRule:
        catalog = self._stock_catalogs.get((system_id, org_id))
        articles = self._stock_rows(
                """SELECT a.id, a.commercial_length_mm, a.material::text,
                          s.finish_authority IS NOT NULL
                   FROM public.profile_articles a JOIN public.profile_systems s ON s.id=a.system_id
                   WHERE a.system_id=%s AND a.sku=%s
                     AND (a.org_id IS NULL OR a.org_id=%s) ORDER BY a.id""",
                [system_id, sku, org_id],
                None if catalog is None else [row[:4] for row in catalog[0] if row[4] == sku],
        )
        if not articles:
            raise MissingStockAuthority
        if len(articles) != 1:
            raise AmbiguousStockAuthority
        article = articles[0]
        has_finish_authority = len(article) > 3 and bool(article[3])
        table = "catalog_color_skus" if has_finish_authority else "profile_purchase_mappings"
        color_clause = " AND finish=%s AND stock_color=finish" if has_finish_authority else ""
        candidates = self._stock_rows(
                f"""SELECT id, commercial_sku, manufacturer_name, supplier_name,
                          purchase_unit, org_id
                   FROM public.{table}
                   WHERE profile_article_id=%s AND is_active
                     AND (org_id IS NULL OR org_id=%s){color_clause} ORDER BY id""",
                [article[0], org_id, *([color] if has_finish_authority else [])],
                None if catalog is None else [row[:6] for row in catalog[1][table]
                    if row[6] == article[0] and (not has_finish_authority or row[7] == color)],
        )
        rows = effective_scope(candidates, org_id, 5)
        if not rows:
            raise MissingStockAuthority
        if len(rows) != 1:
            raise AmbiguousStockAuthority
        row = rows[0]
        if row[4] != "BAR":
            raise MissingStockAuthority("Stock is not supplied as bars")
        return StockRule(
            stock_authority_id=str(row[0]),
            workshop_sku=sku,
            commercial_sku=str(row[1]),
            manufacturer_name=str(row[2]),
            supplier_name=None if row[3] is None else str(row[3]),
            purchase_unit="BAR",
            material=CutMaterial(str(article[2])),
            color=color,
            stock_length_mm=_positive_stock_length(article[1]),
        )

    def reinforcement_stock(
        self, system_id: UUID, org_id: UUID, parent_sku: str,
        requested_sku: str | None, color: str,
    ) -> tuple[StockRule, Decimal | None]:
        if not self._request_cache:
            return self._reinforcement_stock(system_id, org_id, parent_sku, requested_sku, color)
        key = (system_id, org_id, parent_sku, requested_sku, color)
        if key not in self._reinforcement_stocks:
            self._reinforcement_stocks[key] = self._reinforcement_stock(
                system_id, org_id, parent_sku, requested_sku, color)
        return self._reinforcement_stocks[key]

    def _reinforcement_stock(
        self,
        system_id: UUID,
        org_id: UUID,
        parent_sku: str,
        requested_sku: str | None,
        color: str,
    ) -> tuple[StockRule, Decimal | None]:
        catalog = self._stock_catalogs.get((system_id, org_id))
        parents = self._stock_rows(
                """SELECT a.id,s.finish_authority::text FROM public.profile_articles a
                   JOIN public.profile_systems s ON s.id=a.system_id WHERE a.system_id=%s AND a.sku=%s
                     AND (a.org_id IS NULL OR a.org_id=%s) ORDER BY a.id""",
                [system_id, parent_sku, org_id],
                None if catalog is None else [(row[0], row[5]) for row in catalog[0]
                    if row[4] == parent_sku],
        )
        if not parents:
            raise MissingStockAuthority
        if len(parents) != 1:
            raise AmbiguousStockAuthority
        if len(parents[0]) > 1 and parents[0][1] is not None:
            from dekopen_engine.finish_models import FinishAuthority
            raw_authority = parents[0][1]
            if self._request_cache:
                if raw_authority not in self._finish_authorities:
                    self._finish_authorities[raw_authority] = FinishAuthority.model_validate_json(raw_authority)
                authority = self._finish_authorities[raw_authority]
            else:
                authority = FinishAuthority.model_validate_json(raw_authority)
            selected = next((combo for combo in authority.combinations if combo.code == color), None)
            if selected is None:
                raise MissingStockAuthority("La combinación de color no está declarada.")
            color = selected.reinforcement_stock_code
        candidates = self._stock_rows(
                """SELECT id, sku, commercial_sku, manufacturer_name, supplier_name,
                          stock_length_mm, purchase_unit, ix_cm4, org_id
                   FROM public.reinforcement_articles
                   WHERE system_id=%s AND parent_profile_article_id=%s AND is_active
                     AND (org_id IS NULL OR org_id=%s)
                     AND ((%s IS NULL AND is_default) OR sku=%s) ORDER BY id""",
                [system_id, parents[0][0], org_id, requested_sku, requested_sku],
                None if catalog is None else [row[:9] for row in catalog[2]
                    if row[9] == parents[0][0]
                    and ((requested_sku is None and row[10]) or row[1] == requested_sku)],
        )
        rows = effective_scope(candidates, org_id, 8)
        if not rows:
            raise MissingStockAuthority
        if len(rows) != 1:
            raise AmbiguousStockAuthority
        row = rows[0]
        if row[6] != "BAR":
            raise MissingStockAuthority
        return StockRule(
            stock_authority_id=str(row[0]),
            workshop_sku=str(row[1]),
            commercial_sku=str(row[2]),
            manufacturer_name="" if row[3] is None else str(row[3]),
            supplier_name=None if row[4] is None else str(row[4]),
            purchase_unit="BAR",
            material=CutMaterial.STEEL,
            color=color,
            stock_length_mm=_positive_stock_length(row[5]),
        ), None if row[7] is None else _decimal(row[7])

    def for_result(
        self,
        result: EngineResult,
        system_id: UUID,
        org_id: UUID,
        color: str,
    ) -> CuttingAuthorities:
        # Also verifies that the requested system is visible and active through the original loader.
        scope=(system_id,org_id)
        if not self._request_cache or scope not in self._visible_systems:
            SystemParamsRepository().load_visible(system_id, org_id)
            self._visible_systems.add(scope)
        stocks: dict[str, StockRule] = {}
        defaults: dict[str, str] = {}
        inertias: dict[str, Decimal | None] = {}
        for sku in sorted({cut.sku for cut in result.profile_cuts}):
            stock = self.profile_stock(system_id, org_id, sku, color)
            stocks[stock.stock_authority_id] = stock
        identities = {
            (cut.parent_profile_sku, cut.reinforcement_sku) for cut in result.reinforcements
        }
        for parent, requested in sorted(identities, key=lambda x: (x[0], x[1] or "")):
            stock, ix = self.reinforcement_stock(system_id, org_id, parent, requested, color)
            stocks[stock.stock_authority_id] = stock
            if requested is None:
                defaults[parent] = stock.workshop_sku
            inertias[parent] = ix
        return CuttingAuthorities([stocks[key] for key in sorted(stocks)], defaults, inertias)
