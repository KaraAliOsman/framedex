# PRD-01: MOTOR TÉCNICO DE CÁLCULO Y OPTIMIZACIÓN (`/engine`) (v1.1.2)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.1.2 (Congelada y Bloqueada tras Micro-Parche Final)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Fase:** 1 (Núcleo)  
**Bloquea a:** PRD-04, PRD-05, PRD-06, PRD-07, PRD-08, PRD-16

---

## 1. Misión y Principios del Motor

El paquete `/engine` es el núcleo matemático puro de Dekopen. Sus responsabilidades exclusivas son:
1. Parsear y validar el árbol paramétrico de cualquier tipología de ventana/puerta de PVC o aluminio.
2. Calcular las longitudes exactas de corte de perfiles de PVC, refuerzos de acero galvanizado, junquillos, empaquetaduras y dimensiones de vidrios simples y termopaneles (DVH), derivando el espesor neto del vidrio desde `glass_spec`.
3. Resolver los kits de herrajes adecuados desde `hardware_kits` mediante la función de normalización `normalize_opening_type()`, matching dimensional, rail_type y peso de hoja.
4. Generar la lista exhaustiva de materiales (Bill of Materials - BOM), desglosada por metros lineales, piezas unitarias, kits de herrajes y fijaciones.
5. Optimizar el patrón de corte lineal 1D sobre barras comerciales mediante el algoritmo **Best-Fit Decreasing (BFD)** con descuento de kerf (ancho de disco), despuntes de punta y cola, y cálculo exacto de mermas.
6. Ejecutar la validación técnica previa contra el catálogo maestro de Casos de Oro (**Gold Cases G1–G12 + G-Pro1**; G10 en Fase 1.5) con tolerancia estricta de `0.00 mm`.

### Principio de Aislamiento Puro y Convención de Soldadura
- **Sin I/O:** Prohibido importar módulos de red, sockets, base de datos o frameworks web.
- **Tipado Decimal:** Prohibido `float`. Todas las dimensiones y coeficientes se expresan como `Decimal`.
- **Convención de Soldadura:** `SystemParams.welding_loss_per_corner` (e.g. $3.00\text{ mm}$ por cabezal/esquina en inglete) vs `profile_articles.welding_loss_mm` ($6.00\text{ mm}$ total por pieza de corte con 2 extremos soldados). La fórmula $L_{cut} = W_{nominal} + (2 \times \text{welding\_loss\_per\_corner})$ equivale exactamente a $W_{nominal} + \text{welding\_loss\_mm}$.

---

## 2. Modelo de Objetos y Parámetros del Sistema (`engine/models.py`)

```python
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import List, Dict, Optional
import re
from pydantic import BaseModel, Field

class MaterialType(str, Enum):
    PVC = "PVC"
    ALUMINIUM = "ALUMINIUM"

class RailType(str, Enum):
    DUAL = "dual"
    MONO = "mono"

class BayOpeningType(str, Enum):
    FIXED = "FIXED"
    TURN_LEFT = "TURN_LEFT"
    TURN_RIGHT = "TURN_RIGHT"
    TILT_TURN_LEFT = "TILT_TURN_LEFT"
    TILT_TURN_RIGHT = "TILT_TURN_RIGHT"
    SLIDING_2L = "SLIDING_2L"
    SLIDING_3L = "SLIDING_3L"
    SLIDING_4L = "SLIDING_4L"
    AWNING = "AWNING"
    DOOR_ENTRY = "DOOR_ENTRY"
    DOOR_DOUBLE = "DOOR_DOUBLE"

class GlassPiece(BaseModel):
    bay_id: str
    width_mm: Decimal
    height_mm: Decimal
    area_m2: Decimal
    weight_kg: Decimal
    thickness_net_mm: Decimal

class HardwareKitRule(BaseModel):
    sku: str
    name: str
    opening_type: str  # 'TURN', 'TILT_TURN', 'SLIDING', 'AWNING', 'DOOR'
    min_leaf_width_mm: Decimal
    max_leaf_width_mm: Decimal
    min_leaf_height_mm: Decimal
    max_leaf_height_mm: Decimal
    max_leaf_weight_kg: Decimal
    rail_type: RailType = RailType.DUAL
    carriages_qty: int = 2
    stay_arms_qty: int = 1
    contents: List[Dict[str, str]] = []

class SystemParams(BaseModel):
    system_code: str
    depth_mm: Decimal
    material: MaterialType = MaterialType.PVC
    welding_loss_per_corner: Decimal = Decimal('3.00')
    frame_face_width_mm: Decimal = Decimal('60.00')
    sash_face_width_mm: Decimal = Decimal('75.00')
    mullion_face_width_mm: Decimal = Decimal('80.00')
    rebate_depth_mm: Decimal = Decimal('20.00')
    steel_gap_corner_mm: Decimal = Decimal('15.00')
    steel_gap_mullion_mm: Decimal = Decimal('5.00')
    end_milling_overlap_mm: Decimal = Decimal('0.00')
    
    # Parámetros avanzados
    sash_overlap_mm: Decimal = Decimal('8.00')
    glass_clearance_white_mm: Decimal = Decimal('3.00')  # Demo 60 congela 5.00 mm
    glass_clearance_foil_mm: Decimal = Decimal('5.00')
    pulley_height_mm: Decimal = Decimal('12.00')
    central_overlap_mm: Decimal = Decimal('35.00')       # Demo 60 = 40.00 mm
    sliding_lateral_clearance_mm: Decimal = Decimal('0.00')
    sliding_end_add_mm: Decimal = Decimal('6.00')
    corner_bracket_loss_mm: Decimal = Decimal('0.00')
    hook_depth_mm: Decimal = Decimal('0.00')
    door_threshold_mm: Decimal = Decimal('30.00')
    door_bottom_clearance_mm: Decimal = Decimal('20.00')
    rail_type: RailType = RailType.DUAL
    
    # Pesos de perfiles y aceros seed (Demo 60 mm)
    pvc_weight_kg_m: Decimal = Decimal('1.2000')
    steel_weight_kg_m: Decimal = Decimal('1.7000')  # Refuerzo estándar 1.5mm
    hardware_kit_weight_kg: Decimal = Decimal('2.50') # Peso estándar kit herraje
    
    available_hardware_kits: List[HardwareKitRule] = []

# Precedencia de pesos: profile_articles.weight_kg_m prevalece sobre SystemParams.pvc_weight_kg_m (fallback de sistema).
WEIGHT_FALLBACK_FACTOR = Decimal('1.1')
```

---

## 3. Derivación de Espesor Neto y Resolución de Herrajes

### 3.1. Derivación del Espesor Neto de Vidrio (`engine/glass.py`)
```python
def derive_net_glass_thickness(glass_spec: str, fallback_thickness: Decimal) -> Decimal:
    """
    Deriva el espesor neto sumando exclusivamente los paños de cristal.
    Ejemplos:
      - '4-16-4' o '4-12-4' -> 4 + 4 = 8.00 mm
      - '6-12-6'            -> 6 + 6 = 12.00 mm
      - '4-12-3+3'          -> 4 + 6 = 10.00 mm (laminado 3+3 = 6)
      - '6 Float' o '6'     -> 6.00 mm
    """
    parts = glass_spec.strip().split('-')
    if len(parts) >= 3:  # DVH estándar (vidrio - cámara - vidrio)
        pane1_str = parts[0].split()[0]
        pane2_str = parts[2].split()[0]
        t1 = sum(Decimal(x) for x in pane1_str.split('+') if x.replace('.', '', 1).isdigit())
        t2 = sum(Decimal(x) for x in pane2_str.split('+') if x.replace('.', '', 1).isdigit())
        return t1 + t2
    elif len(parts) == 1: # Monolítico
        m = re.search(r'^\d+(\.\d+)?', glass_spec.strip())
        if m:
            return Decimal(m.group(0))
    return fallback_thickness
```

### 3.2. Resolución y Normalización de Herrajes (`engine/hardware.py`)
```python
def normalize_opening_type(opening_type: str) -> str:
    if opening_type in ("TURN_LEFT", "TURN_RIGHT"):
        return "TURN"
    elif opening_type in ("TILT_TURN_LEFT", "TILT_TURN_RIGHT"):
        return "TILT_TURN"
    elif opening_type in ("SLIDING_2L", "SLIDING_3L", "SLIDING_4L"):
        return "SLIDING"
    elif opening_type == "AWNING":
        return "AWNING"
    elif opening_type in ("DOOR_ENTRY", "DOOR_DOUBLE"):
        return "DOOR"
    return opening_type

def resolve_hardware_kit(opening_type: str, sash_w: Decimal, sash_h: Decimal, sash_weight: Decimal, params: SystemParams) -> Optional[HardwareKitRule]:
    normalized_type = normalize_opening_type(opening_type)
    for kit in params.available_hardware_kits:
        if kit.opening_type == normalized_type and \
           kit.rail_type == params.rail_type and \
           kit.min_leaf_width_mm <= sash_w <= kit.max_leaf_width_mm and \
           kit.min_leaf_height_mm <= sash_h <= kit.max_leaf_height_mm and \
           sash_weight <= kit.max_leaf_weight_kg:
            return kit
    return None
```

---

## 4. Fórmulas Canónicas por Tipología (`engine/geometry.py`)

```python
def calculate_geometry(node, params: SystemParams, is_foiled: bool = False):
    clearance = params.glass_clearance_foil_mm if is_foiled else params.glass_clearance_white_mm
    
    # 1. MARCO PRINCIPAL
    if params.material == MaterialType.ALUMINIUM:
        l_frame_cut_h = node.width_mm - (Decimal('2.0') * params.corner_bracket_loss_mm)
        l_frame_cut_v = node.height_mm - (Decimal('2.0') * params.corner_bracket_loss_mm)
    else:
        l_frame_cut_h = node.width_mm + (Decimal('2.0') * params.welding_loss_per_corner)
        l_frame_cut_v = node.height_mm + (Decimal('2.0') * params.welding_loss_per_corner)
        
    w_inner = node.width_mm - (Decimal('2.0') * params.frame_face_width_mm)
    h_inner = node.height_mm - (Decimal('2.0') * params.frame_face_width_mm)
    
    # REFUERZOS DE ACERO DE MARCO
    l_steel_frame_h = l_frame_cut_h - (Decimal('2.0') * (params.welding_loss_per_corner + params.steel_gap_corner_mm))
    l_steel_frame_v = l_frame_cut_v - (Decimal('2.0') * (params.welding_loss_per_corner + params.steel_gap_corner_mm))
    
    # 2. RESOLUCIÓN DE VANOS (DISPATCHER POR TIPOLOGÍA)
    match node.opening_type:
        case "FIXED":
            w_glass = node.bay_width_inner + (Decimal('2.0') * params.rebate_depth_mm) - (Decimal('2.0') * clearance)
            h_glass = node.bay_height_inner + (Decimal('2.0') * params.rebate_depth_mm) - (Decimal('2.0') * clearance)
            
        case "TURN_LEFT" | "TURN_RIGHT" | "TILT_TURN_LEFT" | "TILT_TURN_RIGHT":
            w_sash_outer = node.bay_width_inner + (Decimal('2.0') * params.sash_overlap_mm)
            h_sash_outer = node.bay_height_inner + (Decimal('2.0') * params.sash_overlap_mm)
            l_sash_cut_h = w_sash_outer + (Decimal('2.0') * params.welding_loss_per_corner)
            l_sash_cut_v = h_sash_outer + (Decimal('2.0') * params.welding_loss_per_corner)
            l_steel_sash_h = l_sash_cut_h - (Decimal('2.0') * (params.welding_loss_per_corner + params.steel_gap_corner_mm))
            l_steel_sash_v = l_sash_cut_v - (Decimal('2.0') * (params.welding_loss_per_corner + params.steel_gap_corner_mm))
            w_glass = w_sash_outer - (Decimal('2.0') * params.sash_face_width_mm) + (Decimal('2.0') * params.rebate_depth_mm) - (Decimal('2.0') * clearance)
            h_glass = h_sash_outer - (Decimal('2.0') * params.sash_face_width_mm) + (Decimal('2.0') * params.rebate_depth_mm) - (Decimal('2.0') * clearance)

        case "SLIDING_2L":
            w_sash = ((node.width_mm - (Decimal('2.0') * params.frame_face_width_mm) + params.central_overlap_mm) / Decimal('2.0')) + params.sliding_end_add_mm
            h_sash = node.height_mm - (Decimal('2.0') * params.frame_face_width_mm) - (Decimal('2.0') * params.pulley_height_mm)
            
        case "SLIDING_3L":
            w_sash = (w_inner - (Decimal('2.0') * params.sliding_lateral_clearance_mm) + (Decimal('2.0') * params.central_overlap_mm)) / Decimal('3.0')
            h_sash = h_inner - (Decimal('2.0') * params.pulley_height_mm)

        case "SLIDING_4L":
            w_sash = (w_inner + (Decimal('3.0') * params.central_overlap_mm)) / Decimal('4.0')
            h_sash = h_inner - (Decimal('2.0') * params.pulley_height_mm)

        case "DOOR_DOUBLE":
            w_sash = (w_inner + (Decimal('2.0') * params.sash_overlap_mm) - Decimal('5.00')) / Decimal('2.0')
            h_sash = node.height_mm - params.door_threshold_mm - params.door_bottom_clearance_mm

        case "AWNING":
            w_sash = node.bay_width_inner + (Decimal('2.0') * params.sash_overlap_mm)
            h_sash = node.bay_height_inner + (Decimal('2.0') * params.sash_overlap_mm)

        case "BAY_WINDOW" | "CORNER_COUPLER":
            # Descuento de poste esquinero / acople angular (90°, 135° o variable)
            # w_frame_nominal = rough_opening - coupler_deduction_mm
            w_frame_nominal = node.width_mm - node.coupler_deduction_mm
            l_frame_cut_h = w_frame_nominal + (Decimal('2.0') * params.welding_loss_per_corner)
            l_frame_cut_v = node.height_mm + (Decimal('2.0') * params.welding_loss_per_corner)
            w_inner = w_frame_nominal - (Decimal('2.0') * params.frame_face_width_mm)
            h_inner = node.height_mm - (Decimal('2.0') * params.frame_face_width_mm)
            # Despiece del sub-vano interior según su tipo de apertura (fijo, corredera u oscilobatiente)
```

---

## 5. Catálogo Maestro de Casos de Oro (G1 – G12 + G-Pro1)

| Caso ID | Tipología y Medidas Nominales | Especificación y Despiece Crítico | Estado de Aprobación |
|---|---|---|---|
| **G1** | **Paño Fijo Simple** $1000 \times 1000\text{ mm}$ blanco | Marco: $1006.00\text{ mm}$ (H/V) · Acero: $970.00\text{ mm}$ · Vidrio: $910.00 \times 910.00\text{ mm}$ · Junquillo: $919.00\text{ mm}$. | 🔒 **CONGELADO** |
| **G2** | **Practicable 1 Hoja** $800 \times 1200\text{ mm}$ | Hoja: $702.00 / 1102.00\text{ mm}$ · Acero Hoja: $666.00 / 1066.00\text{ mm}$ · Vidrio DVH 24mm: $576.00 \times 976.00\text{ mm}$. | 🔒 **CONGELADO** |
| **G3** | **Oscilobatiente 1 Hoja** $1000 \times 1400\text{ mm}$ | Hoja: $902.00 / 1302.00\text{ mm}$ · Vidrio DVH 20mm: $776.00 \times 1176.00\text{ mm}$ · Kit Vorne OB (100kg). | 🔒 **CONGELADO** |
| **G4** | **Compuesta Fijo + OB con Poste** $1800 \times 1500\text{ mm}$ | Poste: $1380.00\text{ mm}$ · Acero Poste: $1370.00\text{ mm}$ · Vidrio Fijo: $830 \times 1410$ · Vidrio OB: $696 \times 1276$. | 🔒 **CONGELADO** |
| **G5** | **Corredera 2 Hojas** $2000 \times 2100\text{ mm}$ | Hojas PVC: 4 de $966.00\text{ mm}$ (H) y 4 de $1956.00\text{ mm}$ (V) · Vidrios: 2 de $820.00 \times 1810.00\text{ mm}$. | 🔒 **CONGELADO** |
| **G6** | **Proyectante** $1200 \times 800\text{ mm}$ | Hoja: $1102.00 / 702.00\text{ mm}$ · Compás a fricción $16''$ ($45\text{ kg}$). | 🔒 **CONGELADO** |
| **G7** | **Puerta de Entrada Multipunto** $950 \times 2150\text{ mm}$ | Cabezal: $956\text{ mm}$ · Jambas: $2153\text{ mm}$ · Umbral Alu: $830\text{ mm}$ · Panel sándwich: $696 \times 1928\text{ mm}$. | 🔒 **CONGELADO** |
| **G8** | **Corredera 3 Hojas** | Valida traslape doble + Regla R12. | ⏳ **CONGELAR TRAS 1ª CORRIDA** |
| **G9** | **Corredera 4 Hojas** $4000 \times 2000\text{ mm}$ | Traslape triple central + asimetría opcional. | ⏳ **CONGELAR TRAS 1ª CORRIDA** |
| **G10** | **Corredera Monoriel 2 Hojas** $3000 \times 2400\text{ mm}$ | Regla R14 (Carros reforzados $\ge 80\text{ kg/rueda}$). | ⏳ **FASE 1.5** |
| **G11** | **Puerta Doble Hoja** $1800 \times 2100\text{ mm}$ | Perfil inversor central sin poste fijo. | ⏳ **CONGELAR TRAS 1ª CORRIDA** |
| **G12** | **Fijo Gran Formato** $3000 \times 2500\text{ mm}$ | Inercia $I_x$ crítica + vidrio laminado de seguridad (NCh 132). | ⏳ **CONGELAR TRAS 1ª CORRIDA** |
| **G-Pro1** | **Fijo 1000×1000 (Plantilla PRIVADA Proline Pro6004)** | Pérdida de fusión $2.5\text{ mm} \rightarrow$ Marco $1005.00\text{ mm}$, holgura acero $56.5\text{ mm}$. | 🟡 **AMARILLO (Sign-off Físico)** |
