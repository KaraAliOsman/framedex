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
        # Fabrication authorities the fixed geometry actually consumes — mirror
        # the engine's own role/operation rules so UNKNOWN surfaces here, not
        # mid-calculation, without blocking catalogs whose gaps never reach a
        # calculation:
        # * PVC: every welded-cut member needs weld loss + reinforcement gap —
        #   all effective roles except THRESHOLD (appended unwelded).
        # * non-PVC: profile mass is consumed only by leaf weight, so only the
        #   effective SASH needs a declared density (PVC has a declared system
        #   fallback, so it needs no weight check).
        # * Couplers load outside effective articles; any reinforced coupler
        #   runs reinforcement_cut_length regardless of material.
        if params.material is MaterialType.PVC:
            fabrication_missing = any(
                article.welding_loss_mm is None or article.reinforcement_gap_mm is None
                for role, article in params.effective_profile_articles.items()
                if role is not ProfileRole.THRESHOLD
            )
        else:
            sash = params.effective_profile_articles.get(ProfileRole.SASH)
            fabrication_missing = sash is not None and sash.weight_kg_m is None
        if not fabrication_missing:
            try:
                couplers = SystemParamsRepository().load_coupler_articles(system_id, org_id)
                fabrication_missing = any(
                    article.reinforcement_sku is not None
                    and (article.welding_loss_mm is None or article.reinforcement_gap_mm is None)
                    for article in couplers.values()
                )
            except (ValueError, UnsupportedCatalogContract):
                fabrication_missing = True
        if fabrication_missing:
            reasons.append("fabrication")
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
                glass_skus={row["technical_sku"] for row in glass}, hardware_skus=set(), panel_skus=set())
        except (DocumentaryError, MissingStockAuthority, AmbiguousStockAuthority, ValueError):
            reasons.append("purchase")
    return {"quote_ready": not reasons, "scope": "WHITE_FIXED_CATALOG", "reasons": reasons}
