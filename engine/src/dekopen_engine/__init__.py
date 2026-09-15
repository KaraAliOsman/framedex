"""Public interface for Dekopen's pure deterministic calculation engine."""

from dekopen_engine.documentary_canonical import (
    DOCUMENTARY_CANONICAL_VERSION,
    bom_hash_v1,
    documentary_canonical_json_v1,
    documentary_sha256_v1,
    file_sha256,
    snapshot_sha256_v1,
)
from dekopen_engine.geometry import (
    SUPPORTED_OPENING_TYPES,
    calculate_geometry,
    welding_loss_per_end,
)
from dekopen_engine.glass import (
    FLOAT_GLASS_DENSITY_KG_M3,
    GLASS_WEIGHT_FACTOR_KG_M2_PER_MM,
    build_glass_piece,
    derive_net_glass_thickness,
    exact_glass_area_m2,
)
from dekopen_engine.models import (
    BayOpeningType,
    EffectiveProfileArticle,
    EngineResult,
    GlassPiece,
    GlazingBeadRule,
    HardwareComponent,
    HardwareItem,
    PanelRule,
    PanelPiece,
    LeafWeight,
    HardwareKitRule,
    MaterialType,
    NodeType,
    ParametricNode,
    ProfileCut,
    ProfileRole,
    RailType,
    ReinforcementPiece,
    SystemParams,
)

PACKAGE_NAME = "dekopen-engine"
__version__ = "0.1.0"

__all__ = [
    "DOCUMENTARY_CANONICAL_VERSION",
    "FLOAT_GLASS_DENSITY_KG_M3",
    "GLASS_WEIGHT_FACTOR_KG_M2_PER_MM",
    "PACKAGE_NAME",
    "SUPPORTED_OPENING_TYPES",
    "BayOpeningType",
    "EffectiveProfileArticle",
    "EngineResult",
    "GlassPiece",
    "GlazingBeadRule",
    "HardwareComponent",
    "HardwareItem",
    "PanelRule",
    "PanelPiece",
    "LeafWeight",
    "HardwareKitRule",
    "MaterialType",
    "NodeType",
    "ParametricNode",
    "ProfileCut",
    "ProfileRole",
    "RailType",
    "ReinforcementPiece",
    "SystemParams",
    "__version__",
    "bom_hash_v1",
    "build_glass_piece",
    "calculate_geometry",
    "derive_net_glass_thickness",
    "documentary_canonical_json_v1",
    "documentary_sha256_v1",
    "exact_glass_area_m2",
    "file_sha256",
    "snapshot_sha256_v1",
    "welding_loss_per_end",
]
