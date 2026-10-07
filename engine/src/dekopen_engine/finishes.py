"""Catalog-defined bicolor, reinforcement, size, clearance, SKU and surcharge."""

from decimal import Decimal, localcontext
from collections.abc import Sequence

from dekopen_engine.catalog_rules import CatalogRuleError
from dekopen_engine.commercial import number
from dekopen_engine.finish_models import ResolvedFinish
from dekopen_engine.models import EffectiveProfileArticle, EngineResult, MaterialType, ProfileRole, SystemParams
from dekopen_engine.weight import MissingFabricationAuthority


def resolve_finish(params: SystemParams, code: str) -> ResolvedFinish | None:
    authority = params.finish_authority
    if authority is None:
        return None
    if authority.material != params.material.value:
        raise CatalogRuleError("finish_material_invalid", "La carta de colores no corresponde al material de la serie. Revisa el catálogo.", {})
    combo = next((item for item in authority.combinations if item.code == code), None)
    if combo is None:
        raise CatalogRuleError("finish_combination_invalid", "La combinación interior/exterior no está permitida. Elige una combinación declarada en la carta de la serie.", {"source": authority.source})
    colors = {color.code: color for color in authority.colors}
    return ResolvedFinish(combination=combo, interior=colors[combo.interior], exterior=colors[combo.exterior],
        base=colors[combo.base] if combo.base else None, profile_skus=params.finish_profile_skus.get(code, {}), handle_colors=authority.handle_colors)


def finish_article(article: EffectiveProfileArticle, selected: ResolvedFinish | None) -> EffectiveProfileArticle:
    if selected is None:
        return article
    combo = selected.combination
    rule = article.reinforcement_rule
    if article.material is MaterialType.PVC and combo.reinforcement_required and article.role.value not in {"GLAZING_BEAD", "THRESHOLD", "RAIL"}:
        if rule is None:
            raise MissingFabricationAuthority(f"Sin dato: {selected.exterior.name} / {selected.interior.name} exige refuerzo; falta la regla de {article.sku}. Completa el catálogo.")
        rule = rule.model_copy(update={"minimum_length_mm": Decimal(0), "required_non_white": False})
    elif rule is not None:
        rule = rule.model_copy(update={"required_non_white": False})
    return article.model_copy(update={"reinforcement_rule": rule})


def prepare_finish(params: SystemParams, code: str) -> SystemParams:
    selected = resolve_finish(params, code)
    if selected is None:
        return params
    combo = selected.combination
    articles: dict[ProfileRole, EffectiveProfileArticle] = {}
    for role, article in params.effective_profile_articles.items():
        articles[role] = finish_article(article, selected)
    beads = {thickness: bead.model_copy(update={"bead_article": finish_article(bead.bead_article, selected)})
             for thickness, bead in params.glazing_bead_rules.items()}
    limits = []
    for rule in params.dimensional_limits:
        update: dict[str, Decimal] = {}
        for field, maximum in (("max_leaf_width_mm", combo.max_leaf_width_mm), ("max_leaf_height_mm", combo.max_leaf_height_mm)):
            if maximum is not None:
                update[field] = min(getattr(rule, field), maximum)
        limits.append(rule.model_copy(update=update))
    return params.model_copy(update={"effective_profile_articles": articles, "glazing_bead_rules": beads,
        "dimensional_limits": tuple(limits), "glass_clearance_white_mm": combo.glass_clearance_mm,
        "glass_clearance_foil_mm": combo.glass_clearance_mm})


def validate_finish_size(params: SystemParams, code: str, width_mm: Decimal, height_mm: Decimal) -> None:
    selected = resolve_finish(params, code)
    if selected is None:
        return
    combo = selected.combination
    for axis, actual, maximum in (("ancho", width_mm, combo.max_position_width_mm), ("alto", height_mm, combo.max_position_height_mm)):
        if maximum is not None and actual > maximum:
            raise CatalogRuleError("finish_size_exceeded",
                f"El {axis} de {actual} mm supera {maximum} mm para {selected.exterior.name} exterior / {selected.interior.name} interior. Reduce la medida o elige otro acabado.",
                {"axis": axis, "actual_mm": str(actual), "maximum_mm": str(maximum), "source": combo.source})


def finish_result(result: EngineResult, params: SystemParams, code: str) -> EngineResult:
    selected = resolve_finish(params, code)
    if selected is None:
        return result
    mapped = {}
    cuts = []
    for cut in result.profile_cuts:
        sku = selected.profile_skus.get(cut.sku)
        if not sku:
            raise MissingFabricationAuthority(f"Sin dato: falta el SKU de {cut.sku} para {selected.exterior.name} exterior / {selected.interior.name} interior. Completa Colores y SKU por color.")
        mapped[cut.sku] = sku
        cuts.append(cut.model_copy(update={"commercial_sku": sku, "stock_color": code}))
    for item in result.hardware_items:
        color = item.resolution.handle_color_code if item.resolution else None
        allowed = selected.combination.allowed_handle_colors
        if color is not None and allowed and color not in allowed:
            raise CatalogRuleError("finish_handle_color_invalid", "El color de manilla no está permitido con este acabado. Elige un color compatible en Herrajes.", {"source": selected.combination.source})
    return result.model_copy(update={"profile_cuts": cuts,
        "finish": selected.model_copy(update={"profile_skus": mapped})})


def finish_surcharge(result: EngineResult, profile_cost: Decimal, currency: str) -> Decimal:
    if result.finish is None:
        return Decimal(0)
    rule = result.finish.combination.surcharge
    if rule.currency != currency:
        raise ValueError("La moneda del recargo no coincide con la cotización; declara una tarifa en esa moneda.")
    if rule.kind == "PER_M":
        length_mm = sum((cut.length_mm * cut.qty for cut in result.profile_cuts), Decimal(0))
        return rule.amount * length_mm / Decimal(1000)
    if rule.kind == "PERCENT":
        return profile_cost * rule.amount / Decimal(100)
    if rule.kind == "FIXED":
        return rule.amount
    return Decimal(0)


def finish_description(result: EngineResult) -> str | None:
    if result.finish is None:
        return None
    selected = result.finish
    if selected.interior.code == selected.exterior.code:
        return f"{selected.interior.name} en ambas caras"
    return f"{selected.exterior.name} exterior / {selected.interior.name} interior"


def finish_selling_delta(baseline: Decimal, proposed: Decimal) -> Decimal:
    """Signed exact difference between engine-priced units; no currency rounding."""
    number(baseline)
    number(proposed)
    with localcontext() as context:
        context.prec = 80
        return proposed - baseline


def finish_rgb_css(channels: Sequence[Decimal | str]) -> str:
    """Linear catalog channels to sRGB for paper/SVG; no engineering numbers."""
    if len(channels) != 3:
        raise ValueError("El color requiere tres canales lineales.")
    rgb = []
    for channel in channels:
        value = Decimal(channel)
        if not value.is_finite() or not Decimal(0) <= value <= Decimal(1):
            raise ValueError("El canal lineal debe estar entre cero y uno.")
        encoded = value * Decimal("12.92") if value <= Decimal("0.0031308") else (
            Decimal("1.055") * value ** (Decimal(1)/Decimal("2.4")) - Decimal("0.055"))
        rgb.append(str((encoded*Decimal(255)).quantize(Decimal(1))))
    return "rgb("+",".join(rgb)+")"
