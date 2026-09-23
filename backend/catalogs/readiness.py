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
        # Fabrication authorities the fixed geometry actually consumes:
        # every welded PVC cut member needs declared weld loss + reinforcement
        # gap; every non-PVC member needs a real mass (PVC has a declared
        # system fallback). UNKNOWN must surface here — not mid-calculation.
        fabrication_missing = (
            any(
                article.welding_loss_mm is None or article.reinforcement_gap_mm is None
                for article in params.effective_profile_articles.values()
            )
            if params.material is MaterialType.PVC
            else any(
                article.weight_kg_m is None
                for article in params.effective_profile_articles.values()
            )
        )
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
