"""Current catalog prerequisites for a WHITE fixed quotation, never production approval."""

from dekopen_engine.models import MaterialType, ProfileRole
from documents.repository import (
    DocumentaryError, load_manufacturing_policies, load_purchase_authorities,
)
from engine_api.cutting_repository import CuttingRepository, MissingStockAuthority, AmbiguousStockAuthority
from engine_api.inspection_repository import InspectorRepository
from engine_api.repository import SystemParamsRepository, SystemNotFound, UnsupportedCatalogContract
from pricing.repository import rows


def catalog_readiness(system_id, org_id):
    reasons = []
    params = None
    try:
        params = SystemParamsRepository().load_visible(system_id, org_id)
        if (
            params.material not in (MaterialType.PVC, MaterialType.ALUMINIUM)
            or not params.glazing_bead_rules
        ):
            reasons.append("technical_catalog")
    except (SystemNotFound, UnsupportedCatalogContract, ValueError):
        reasons.append("technical_catalog")
    try:
        InspectorRepository().load(system_id, org_id)
    except (ValueError, UnsupportedCatalogContract):
        reasons.append("inspection")
    policies = []
    for table in ("manufacturing_placement_policies", "handle_requirement_policies",
                  "reinforcement_cut_policies"):
        values = rows(f"SELECT id FROM public.{table} WHERE system_id=%s "
                      "AND (org_id IS NULL OR org_id=%s) ORDER BY version DESC,id",
                      [system_id, org_id])
        policies.append(values[0]["id"] if values else None)
    if None in policies:
        reasons.append("manufacturing")
    else:
        try:
            load_manufacturing_policies(system_id=system_id, org_id=org_id,
                placement_id=policies[0], handle_id=policies[1], reinforcement_id=policies[2])
        except (DocumentaryError, ValueError):
            reasons.append("manufacturing")
    if params is not None:
        # Fabrication authorities the geometry actually consumes — mirror
        # the engine's own role/operation rules so UNKNOWN surfaces here, not
        # mid-calculation, without blocking catalogs whose gaps never reach a
        # calculation:
        # * rebate_depth_mm / end_milling_overlap_mm are consumed by every
        #   glazed bay and every mullion — NULL means the system cannot prove
        #   its fabrication geometry (the engine raises instead of inventing).
        # * PVC: every welded-cut member needs weld loss + reinforcement gap —
        #   all effective roles except THRESHOLD (appended unwelded).
        # * Profile and steel mass feed leaf weight — there is no fallback
        #   anymore, so the effective SASH needs both when it is reinforced.
        # * A hardware kit with no declared mass makes weight-based
        #   certification undecidable.
        # * Couplers load outside effective articles; any reinforced coupler
        #   runs reinforcement_cut_length regardless of material.
        fabrication_missing = (
            params.rebate_depth_mm is None or params.end_milling_overlap_mm is None
        )
        if params.material is MaterialType.PVC:
            fabrication_missing = fabrication_missing or any(
                article.welding_loss_mm is None or article.reinforcement_gap_mm is None
                for role, article in params.effective_profile_articles.items()
                if role is not ProfileRole.THRESHOLD
            )
        sash = params.effective_profile_articles.get(ProfileRole.SASH)
        if sash is not None:
            fabrication_missing = fabrication_missing or (
                sash.weight_kg_m is None
                or (bool(sash.reinforcement_sku) and sash.steel_weight_kg_m is None)
            )
        fabrication_missing = fabrication_missing or any(
            kit.weight_kg is None for kit in params.available_hardware_kits
        )
        if not fabrication_missing:
            try:
                couplers = SystemParamsRepository().load_coupler_articles(system_id, org_id)
                fabrication_missing = any(
                    bool(article.reinforcement_sku)
                    and (article.welding_loss_mm is None or article.reinforcement_gap_mm is None)
                    for article in couplers.values()
                )
            except (ValueError, UnsupportedCatalogContract):
                fabrication_missing = True
        if fabrication_missing:
            reasons.append("fabrication")
        # Production authority must not ride on values nobody ever verified:
        # LEGACY_UNVERIFIED rows and rows whose technical values changed after
        # their last review (review_pending) need a human review first —
        # review() clears both gates.
        if rows(
            "SELECT 1 FROM public.profile_systems WHERE id=%s"
            " AND (is_global = TRUE OR org_id=%s)"
            " AND (data_provenance='LEGACY_UNVERIFIED' OR review_pending)"
            " UNION ALL"
            " SELECT 1 FROM public.profile_articles WHERE system_id=%s"
            " AND (org_id IS NULL OR org_id=%s)"
            " AND (data_provenance='LEGACY_UNVERIFIED' OR review_pending)"
            " UNION ALL"
            " SELECT 1 FROM public.infill_articles WHERE system_id=%s"
            " AND (org_id IS NULL OR org_id=%s)"
            " AND (data_provenance='LEGACY_UNVERIFIED' OR review_pending)"
            " UNION ALL"
            " SELECT 1 FROM public.hardware_kits WHERE"
            " (system_id=%s OR system_id IS NULL)"
            " AND (org_id IS NULL OR org_id=%s)"
            " AND (data_provenance='LEGACY_UNVERIFIED' OR review_pending)"
            " LIMIT 1",
            [system_id, org_id, system_id, org_id,
             system_id, org_id, system_id, org_id],
        ):
            reasons.append("catalog_review")
        try:
            frame = params.effective_profile_articles[ProfileRole.FRAME]
            profiles = [frame,
                        *(rule.bead_article for rule in params.glazing_bead_rules.values())]
            steels: set[str] = set()
            if params.material is MaterialType.PVC:
                # A welded PVC frame always has reinforcement, including
                # default SKU resolution. Mechanically jointed systems do not.
                stock, _ = CuttingRepository().reinforcement_stock(
                    system_id, org_id, frame.sku, frame.reinforcement_sku, "WHITE")
                steels = {stock.workshop_sku}
            glass = rows("SELECT technical_sku FROM public.glass_purchase_mappings "
                         "WHERE system_id=%s AND (org_id IS NULL OR org_id=%s)", [system_id, org_id])
            if not glass:
                raise DocumentaryError("glass_purchase_mapping_required")
            load_purchase_authorities(system_id=system_id, org_id=org_id, color="WHITE",
                profile_skus={article.sku for article in profiles}, reinforcement_skus=steels,
                glass_skus={row["technical_sku"] for row in glass}, hardware_skus=set(),
                panel_skus=set(), fitting_skus=set())
        except (DocumentaryError, MissingStockAuthority, AmbiguousStockAuthority, ValueError):
            reasons.append("purchase")
    return {"quote_ready": not reasons, "scope": "WHITE_FIXED_CATALOG", "reasons": reasons}
