"""Synthetic PRO6004 workshop fixture; no manufacturer or production-price claims."""

from dataclasses import asdict
from decimal import Decimal as D, localcontext
from typing import Any

from dekopen_engine import (
    BayOpeningType, EffectiveProfileArticle, GlazingBeadRule, HardwareKitRule,
    MaterialType, NodeType, ParametricNode, ProfileRole, SystemFamily, SystemParams,
    calculate_geometry,
)
from dekopen_engine.glass import exact_glass_area_m2
from dekopen_engine.models import ProfileCutRule, ProfileReinforcementRule, SystemDimensionalLimit
from dekopen_engine.price_workspace import linear_purchase
from dekopen_engine.simple_pricing import SimplePricingPolicy, simple_price

SOURCE = 'Synthetic workshop fixture; not manufacturer data'
RATES = {'PRO-F': D('12000'), 'PRO-S': D('15000'), 'PRO-B': D('5000'),
    'STEEL-F': D('8000'), 'STEEL-S': D('8000'), 'GLASS-24': D('20000'),
    'PRO-TURN': D('12000'), 'SCREW-F': D('20'), 'SCREW-S': D('20')}


def pro6004_params() -> SystemParams:
    def article(sku: str, role: ProfileRole, face: str,
                steel: str | None = None, screw: str | None = None) -> EffectiveProfileArticle:
        bead = role is ProfileRole.GLAZING_BEAD
        return EffectiveProfileArticle(sku=sku, role=role, material=MaterialType.PVC,
            face_width_mm=D(face), commercial_length_mm=D('6500'),
            welding_loss_mm=D('0') if bead else D('6'), reinforcement_gap_mm=D('15'),
            weight_kg_m=D('1.2'), steel_weight_kg_m=D('1.7'), reinforcement_sku=steel,
            cut_rule=ProfileCutRule(angle_degrees=90 if bead else 45,
                welding_loss_per_end_mm=D('0') if bead else D('3'),
                joint_deduction_per_end_mm=D('0'), meeting_deduction_mm=D('0'),
                cut_step_mm=D('0.01'), rounding='UP', source=SOURCE),
            reinforcement_rule=ProfileReinforcementRule(reinforcement_sku=steel,
                reinforcement_type='STEEL', minimum_length_mm=D('0'),
                required_finishes=('WHITE',), required_non_white=True,
                cut_deduction_mm=D('30'), screws_per_m=D('4'), screw_sku=screw,
                screw_weight_kg=D('0.001'), source=SOURCE) if steel and screw else None)

    frame = article('PRO-F', ProfileRole.FRAME, '60', 'STEEL-F', 'SCREW-F')
    sash = article('PRO-S', ProfileRole.SASH, '60', 'STEEL-S', 'SCREW-S')
    bead = article('PRO-B', ProfileRole.GLAZING_BEAD, '20')
    return SystemParams(system_code='PRO6004-SYNTHETIC', system_family=SystemFamily.CASEMENT,
        material=MaterialType.PVC, depth_mm=D('60'),
        effective_profile_articles={ProfileRole.FRAME: frame, ProfileRole.SASH: sash},
        glazing_bead_rules={D('24'): GlazingBeadRule(glass_thickness_mm=D('24'),
            bead_article=bead, bead_width_mm=D('20'), gasket_interior_mm=D('3'),
            gasket_exterior_mm=D('3'), cut_add_mm=D('0'))},
        rebate_depth_mm=D('15'), end_milling_overlap_mm=D('4'), sash_overlap_mm=D('8'),
        glass_clearance_white_mm=D('5'), glass_clearance_foil_mm=D('5'),
        door_leaf_side_clearance_mm=D('0'), finishes=('WHITE',),
        dimensional_limits=tuple(SystemDimensionalLimit(opening_type=opening,
            min_leaf_width_mm=D('200'), max_leaf_width_mm=D('3000'),
            min_leaf_height_mm=D('200'), max_leaf_height_mm=D('3000'),
            min_aspect_ratio=D('.25'), max_aspect_ratio=D('5'), max_leaf_weight_kg=D('100'),
            source=SOURCE) for opening in (BayOpeningType.FIXED, BayOpeningType.TURN_LEFT)),
        available_hardware_kits=[HardwareKitRule(sku='PRO-TURN', name='Synthetic turn kit',
            opening_type='TURN', min_leaf_width_mm=D('200'), max_leaf_width_mm=D('1500'),
            min_leaf_height_mm=D('200'), max_leaf_height_mm=D('2400'), max_leaf_weight_kg=D('100'),
            weight_kg=D('1'))])


def window_case(opening: BayOpeningType, policy: SimplePricingPolicy) -> dict[str, Any]:
    root = ParametricNode(id='trial', type=NodeType.BAY, width_mm=D('1200'), height_mm=D('1100'),
        opening_type=opening, glass_spec='4-16-4', glass_article_sku='GLASS-24',
        glass_thickness_mm=D('24'))
    bom = calculate_geometry(root, pro6004_params(), finish='WHITE')
    materials: list[dict[str, Any]] = []
    with localcontext() as context:
        context.prec = 256
        for cut in bom.profile_cuts:
            length = cut.length_mm * cut.qty
            amount = linear_purchase(RATES[cut.sku], 'BAR', length, D('6500'), 'CLP')['amount']
            materials.append({'kind': 'PROFILE', 'sku': cut.sku, 'length_mm': str(cut.length_mm),
                'quantity': cut.qty, 'stock_length_mm': '6500', 'rate': str(RATES[cut.sku]),
                'unit': 'BAR', 'amount': str(amount)})
        for steel in bom.reinforcements:
            assert steel.reinforcement_sku
            sku = steel.reinforcement_sku
            amount = linear_purchase(RATES[sku], 'BAR', steel.length_mm * steel.qty, D('6000'), 'CLP')['amount']
            materials.append({'kind': 'REINFORCEMENT', 'sku': sku, 'length_mm': str(steel.length_mm),
                'quantity': steel.qty, 'stock_length_mm': '6000', 'rate': str(RATES[sku]),
                'unit': 'BAR', 'amount': str(amount)})
        for glass in bom.glasses:
            area = exact_glass_area_m2(glass.width_mm, glass.height_mm)
            materials.append({'kind': 'GLASS', 'sku': 'GLASS-24', 'width_mm': str(glass.width_mm),
                'height_mm': str(glass.height_mm), 'quantity': str(area), 'unit': 'M2',
                'rate': str(RATES['GLASS-24']), 'amount': str(area * RATES['GLASS-24'])})
        for kit in bom.hardware_items:
            materials.append({'kind': 'HARDWARE', 'sku': kit.kit_sku, 'quantity': kit.qty,
                'unit': 'KIT', 'rate': str(RATES[kit.kit_sku]), 'amount': str(RATES[kit.kit_sku] * kit.qty)})
        for fitting in bom.fittings:
            materials.append({'kind': 'FITTING', 'sku': fitting.sku, 'quantity': fitting.qty,
                'unit': 'EA', 'rate': str(RATES[fitting.sku]), 'amount': str(RATES[fitting.sku] * fitting.qty)})
    priced = simple_price([D(item['amount']) for item in materials], D('1.32'), policy)
    return {'source': SOURCE, 'system_code': 'PRO6004-SYNTHETIC',
        'input': root.model_dump(mode='json'), 'materials': materials,
        'policy': {key: str(value) for key, value in asdict(policy).items()},
        'price': {key: str(value) for key, value in asdict(priced).items()}}


def simple_pricing_cases() -> dict[str, Any]:
    return {
        'PRO6004-fija': window_case(BayOpeningType.FIXED, SimplePricingPolicy(currency='CLP',
            labor_rate=D('15000'), labor_basis='M2', installation_rate=D('10000'),
            installation_basis='WINDOW', margin=D('0.35'), rounding_step=D('1000'))),
        'PRO6004-abatible': window_case(BayOpeningType.TURN_LEFT, SimplePricingPolicy(currency='CLP',
            labor_rate=D('20000'), labor_basis='WINDOW', installation_rate=D('5000'),
            installation_basis='M2', margin=D('0.35'), rounding_step=D('1000'))),
    }
