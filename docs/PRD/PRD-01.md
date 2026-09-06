# PRD-01: MOTOR TÉCNICO DE CÁLCULO Y OPTIMIZACIÓN (`/engine`) (v1.1.2)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.1.2 (Congelada y Bloqueada tras Micro-Parche Final)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Fase:** 1 (Núcleo)  
**Bloquea a:** PRD-04, PRD-05, PRD-06, PRD-07, PRD-08, PRD-16

**Enmienda SHOT-06:** resolución del owner PD-06-01…17 incorporada en
`docs/plans/PLAN_SHOT-06.md`. Los nuevos SKU, rangos y pesos sin ficha de fabricante
son **DEMO_60 SYNTHETIC FIXTURE**, nunca especificaciones comerciales certificadas.
**Regla 0 / Regla 20:** PD-06-19 y PD-06-20 resueltas por el owner.
G3 standalone = 33.29 kg; golden compuesto bay_2 = 26.55 kg. G7 incluye
retención de panel por beads 705.00/1937.00 qty2. Fase 2 autorizada; cero pendientes abiertos.

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
- **Convención de Soldadura:** `profile_articles.welding_loss_mm` es la única autoridad persistida/editable. El adapter entrega al motor el artículo efectivo de cada pieza/rol y la pérdida por extremo se deriva exclusivamente como `welding_loss_per_end(article) = article.welding_loss_mm / Decimal('2')`. FRAME, SASH, MULLION y GLAZING_BEAD nunca comparten un scalar global de pérdida.

---

## 2. Modelo de Objetos y Parámetros del Sistema (`engine/models.py`)

```python
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import List, Dict, Optional, Literal
import re
from pydantic import BaseModel, Field

class MaterialType(str, Enum):
    PVC = "PVC"
    ALUMINIUM = "ALUMINIUM"

class RailType(str, Enum):
    DUAL = "dual"
    MONO = "mono"

class ProfileRole(str, Enum):
    FRAME = "FRAME"
    SASH = "SASH"
    MULLION_V = "MULLION_V"
    MULLION_H = "MULLION_H"
    INVERSOR = "INVERSOR"
    GLAZING_BEAD = "GLAZING_BEAD"
    COUPLER = "COUPLER"
    ADDITIONAL = "ADDITIONAL"
    THRESHOLD = "THRESHOLD"

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
    leaf_id: Optional[str] = None
    width_mm: Decimal
    height_mm: Decimal
    area_m2: Decimal
    weight_kg: Decimal
    thickness_net_mm: Decimal

class HardwareComponent(BaseModel):
    sku: str
    name: str
    qty: Decimal
    unit: str

class HardwareItem(BaseModel):
    kit_sku: str
    name: str
    qty: int = 1
    unit: Literal["kit"] = "kit"
    bay_id: str
    leaf_id: Optional[str] = None
    contents: List[HardwareComponent] = Field(default_factory=list)

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
    contents: List[HardwareComponent] = Field(default_factory=list)
    weight_kg: Optional[Decimal] = None

class EffectiveProfileArticle(BaseModel):
    sku: str
    role: ProfileRole
    material: MaterialType
    face_width_mm: Decimal
    welding_loss_mm: Decimal
    reinforcement_gap_mm: Decimal
    weight_kg_m: Optional[Decimal]
    steel_weight_kg_m: Optional[Decimal]
    reinforcement_sku: Optional[str] = None

class GlazingBeadRule(BaseModel):
    glass_thickness_mm: Decimal
    bead_article: EffectiveProfileArticle
    bead_width_mm: Decimal
    gasket_interior_mm: Decimal
    gasket_exterior_mm: Decimal
    cut_add_mm: Decimal

class PanelRule(BaseModel):
    sku: str
    name: str
    kind: Literal["SANDWICH_PANEL"]
    thickness_mm: Decimal
    weight_kg_m2: Optional[Decimal]

class SystemParams(BaseModel):
    system_code: str
    depth_mm: Decimal
    material: MaterialType = MaterialType.PVC
    effective_profile_articles: Dict[ProfileRole, EffectiveProfileArticle]
    glazing_bead_rules: Dict[Decimal, GlazingBeadRule]
    rebate_depth_mm: Decimal = Decimal('20.00')
    end_milling_overlap_mm: Decimal = Decimal('0.00')
    
    # Parámetros avanzados
    sash_overlap_mm: Decimal = Decimal('8.00')
    glass_clearance_white_mm: Decimal = Decimal('3.00')  # Demo 60 congela 5.00 mm
    glass_clearance_foil_mm: Decimal = Decimal('5.00')
    pulley_height_mm: Decimal = Decimal('12.00')
    central_overlap_mm: Decimal = Decimal('35.00')       # Demo 60 = 40.00 mm
    sliding_lateral_clearance_mm: Decimal = Decimal('0.00')
    sliding_end_add_mm: Decimal = Decimal('6.00')
    sliding_glazing_deduction_width_mm: Decimal
    sliding_glazing_deduction_height_mm: Decimal
    corner_bracket_loss_mm: Decimal = Decimal('0.00')
    hook_depth_mm: Decimal = Decimal('0.00')
    door_threshold_mm: Decimal = Decimal('30.00')
    door_bottom_clearance_mm: Decimal = Decimal('20.00')
    door_leaf_side_clearance_mm: Decimal
    rail_type: RailType = RailType.DUAL
    
    # Pesos de perfiles y aceros seed (Demo 60 mm)
    pvc_weight_kg_m: Decimal = Decimal('1.2000')
    steel_weight_kg_m: Decimal = Decimal('1.7000')  # Refuerzo estándar 1.5mm
    hardware_kit_weight_kg: Decimal = Decimal('2.50') # Peso estándar kit herraje
    
    available_hardware_kits: List[HardwareKitRule] = Field(default_factory=list)
    available_panel_rules: Dict[str, PanelRule] = Field(default_factory=dict)

# Precedencia de pesos: profile_articles.weight_kg_m prevalece sobre SystemParams.pvc_weight_kg_m (fallback de sistema).
WEIGHT_FALLBACK_FACTOR = Decimal('1.10')
```

`PanelRule` es la autoridad de panel descrita arriba.
`available_panel_rules` es la colección pura por SKU para transportar los infill_articles,
sin lookup DB dentro del motor.

```python
class PanelPiece(BaseModel):
    sku: str
    name: str
    bay_id: str
    leaf_id: Optional[str]
    width_mm: Decimal
    height_mm: Decimal
    area_m2: Decimal
    weight_kg: Decimal

class LeafWeight(BaseModel):
    bay_id: str
    leaf_id: Optional[str]
    pvc_weight_kg: Decimal
    steel_weight_kg: Decimal
    infill_weight_kg: Decimal
    hardware_weight_kg: Decimal
    total_weight_kg: Decimal
    used_fallback: bool
```

El nodo paramétrico añade `panel_article_sku: Optional[str]`, obligatorio para
DOOR_ENTRY. Una BAY SLIDING_2L emite dos hojas, IDs `<bay_id>:L1`, `<bay_id>:L2`,
en orden izquierda→derecha. G1–G4 mantienen leaf_id null donde no se necesita.

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

#### 3.1.1. Área y peso canónicos de `GlassPiece` (PD-09)

```python
FLOAT_GLASS_DENSITY_KG_M3 = Decimal('2500')
GLASS_WEIGHT_FACTOR_KG_M2_PER_MM = Decimal('2.50')

area_m2_exact = (width_mm * height_mm) / Decimal('1000000')
area_m2 = area_m2_exact.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)

weight_kg_exact = (
    area_m2_exact
    * thickness_net_mm
    * GLASS_WEIGHT_FACTOR_KG_M2_PER_MM
)
weight_kg = weight_kg_exact.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
```

`FLOAT_GLASS_DENSITY_KG_M3` es una constante física del material dentro de
`/engine`, no un parámetro del sistema de perfiles y no forma parte de
`SystemParams`. `weight_kg` usa exclusivamente `thickness_net_mm`, es decir,
la suma de los paños de vidrio derivada desde `glass_spec`; cámara, gas,
separador y espesor total del paquete DVH no participan.

La autoridad intermedia es siempre `area_m2_exact`. Queda prohibido calcular
el peso desde `GlassPiece.area_m2` ya cuantizado. Cada campo público se
cuantiza una sola vez al emitirse mediante `ROUND_HALF_UP`: `area_m2` a cuatro
decimales, `weight_kg` a dos y `thickness_net_mm` a dos.

Fixtures congelados:

- `680.00 × 1310.00`, `4-16-4` → área `0.8908`, espesor neto `8.00`, peso
  `17.82`.
- `546.00 × 1176.00`, `4-12-4` → área exacta `0.642096`, área publicada
  `0.6421`, espesor neto `8.00`, peso `12.84`.

### 3.2. Resolución y Normalización de Herrajes (`engine/hardware.py`)

La resolución SHOT-06 usa dimensión terminada exterior, nunca corte.
Normalización: TURN_LEFT/RIGHT→TURN; TILT_TURN_LEFT/RIGHT→TILT_TURN;
SLIDING_2L/3L/4L→SLIDING; AWNING→AWNING; DOOR_ENTRY/DOUBLE→DOOR;
otros sin transformación. Normalizar no habilita ramas Extended ni G10.

Primero filtrar por opening normalizado, rail exacto y límites inclusivos W/H.
Calcular base_leaf_weight exacto SIN hardware. Por cada candidato:

```text
candidate_total_weight = base_leaf_weight + effective_hardware_kit_weight(kit)
compatible = candidate_total_weight <= kit.max_leaf_weight_kg
```

Con hardware_set_sku explícito, sólo ese SKU: debe existir y satisfacer todas las
restricciones; de lo contrario error determinista. Sin SKU: cero compatibles produce
NoCompatibleHardwareKit; uno selecciona ese kit; más de uno produce AmbiguousHardwareKit.
Prohibido first-match o elegir por orden de catálogo. FIXED no lleva kit.
Hardware_items emite UN HardwareItem por kit seleccionado por hoja, qty=1, unit=kit;
contents conserva orden persistido y composición, sin flatten ni líneas de costo.

### 3.3. Peso exacto por hoja y panel (PD-06-12/13/14)

Módulo puro weight.py dentro de engine/src/dekopen_engine, sin DB/I/O.
Por pieza SASH: masa PVC exacta=(cut_length_mm/1000)*qty*effective_weight_kg_m.
Acero: masa exacta=(reinforcement_cut_mm/1000)*qty*effective_steel_weight_kg_m.
Los pesos Core congelados usan SASH y su acero: no incluyen FRAME, MULLION,
THRESHOLD ni junquillos. El corte mide material consumido de la hoja.
Vidrio: recalcular masa exacta con área exacta según §3.1.1, nunca leer peso público
cuantizado para sumar. Panel: área exacta W*H/1000000 y masa exacta*weight_kg_m2;
PanelPiece publica área4 y kg2 ROUND_HALF_UP. No vidrio ficticio.

Base_leaf_weight suma PVC/acero/infill SIN kit. Cada candidato añade su masa efectiva
antes de comparar capacidad, usando total EXACTO. LeafWeight publica componentes
pvc/steel/infill/hardware/total a2 decimales HALF_UP; total se cuantiza una vez desde
exactos y puede diferir de sumar los componentes públicos redondeados. used_fallback
es true si cualquier componente usa autoridad fallback.

| Autoridad | Persistida presente | Ausente |
|---|---|---|
| Peso perfil PVC | PA.weight_kg_m exacto | params.pvc_weight_kg_m*1.10 sólo material PVC |
| Peso perfil no PVC | PA.weight_kg_m exacto | MissingWeightAuthority si se requiere masa |
| Acero de pieza con refuerzo | PA.steel_weight_kg_m exacto | params.steel_weight_kg_m*1.10 |
| Kit | HK.weight_kg exacto | params.hardware_kit_weight_kg*1.10 =2.75 con fallback2.50 |
| Panel participante | infill_articles.weight_kg_m2 exacto | MissingWeightAuthority, sin fallback |

None permitido en modelos internos de autoridad de peso; PA DB sigue NOT NULL,
el adapter entrega sus valores persistidos. No aplicar1.10 sobre valor persistido.
Todos los cinco kits DEMO_60 tienen peso persistido2.50, no fallback. Refuerzo no
existente (umbral) no produce masa de acero ni exige autoridad de acero.

| Fixture | PVC exacto | Steel exacto | Infill exacto | Kit exacto | Total exacto | Total público |
|---|---|---|---|---|---|---|
| G5 por hoja |7.0128|9.6900|29.6840|2.5000|48.8868|48.89|
| G6 |4.3296|5.8888|11.24352|2.50|23.96192|23.96|
| G7 |6.9024|9.5336|13.41888|2.50|32.35488|32.35|

PD-06-19: G3 standalone33.289920→33.29; golden OB26.546320→26.55 (§6.6).

### 3.4. Pricing puro SHOT-06 (PD-06-15)

pricing.py contiene sólo primitives sin DB, API de pricing, FX ni integración con
project_positions. price_from_cost_and_margin(direct_cost,margin_pct): cost>=0,
0<=margin<1, price_exact=cost/(1-margin), output price_net a2 HALF_UP.
gross_margin_pct(cost,price)=(price-cost)/price, output4 HALF_UP; división por cero
es entrada fuera del dominio matemático. Todos inputs Decimal finitos.
Fixture:100000.00/0.6500→153846.15. No es emisión CLP ni conversión de moneda;
redondeo monetario CLP/USD para cotización pertenece a capa comercial posterior.
SHOT-08 conserva listas, lookup de pricing_rules, FX, waste, labor, installation,
router Mode1–5, descuentos, autorización y price_audit_logs. Ver PRD-05 frontera.

## 4. Fórmulas Canónicas por Tipología (`engine/geometry.py`)

Todos los milímetros y factores son Decimal. F=FRAME efectivo, S=SASH efectivo,
e(A)=A.welding_loss_mm/2. Soldadura permanece exclusivamente en PA por artículo.

```text
rectangular_frame_cut_h = W + 2*e(F)
rectangular_frame_cut_v = H + 2*e(F)
frame_clear_width = W - 2*F.face_width_mm
frame_clear_height = H - 2*F.face_width_mm
steel_cut = pvc_cut - welded_end_count*e(article) - 2*article.reinforcement_gap_mm
```

Marcos rectangulares y hojas soldadas usan welded_end_count=2 y qty2 H/2 V.
Cortes PVC de esos rectángulos: ángulos45/45. La rama general ALUMINIUM conserva
el contrato futuro cut=nominal-2*corner_bracket_loss_mm; no se amplía su implementación
por introducir el umbral de G7.

FIXED conserva vidrio `bay_clear + 2*rebate_depth_mm - 2*clearance` por eje.
TURN/TILT_TURN/AWNING comparten primitive interna single_rectangular_sash_geometry,
sin copiar código: outer=bay_clear+2*sash_overlap_mm; cut=outer+S.welding_loss_mm;
steel con dos extremos; glass=outer-2*S.face+2*rebate_depth-2*clearance;
bead=glass_length+rule.cut_add_mm. Qty2 por eje; cambia apertura/orientación/herraje.

SLIDING_2L:

```text
sash_cut_width = (frame_clear_width + central_overlap_mm)/2 + sliding_end_add_mm
sash_cut_height = frame_clear_height - 2*pulley_height_mm
finished_width = sash_cut_width - S.welding_loss_mm
finished_height = sash_cut_height - S.welding_loss_mm
base_glass_width = finished_width - 2*S.face + 2*rebate_depth - 2*clearance
base_glass_height = finished_height - 2*S.face + 2*rebate_depth - 2*clearance
glass_width = base_glass_width - sliding_glazing_deduction_width_mm
glass_height = base_glass_height - sliding_glazing_deduction_height_mm
```

Cada deducción es TOTAL por eje, una vez por vidrio/hoja corredera; no por lado,
no cut_add_mm, no cambia bead global. Autoridad técnica del SISTEMA persistida en PS;
DEMO_60=20.00/20.00. Dos hojas L1/L2, cada una qty2 H/2 V PVC y acero, un vidrio,
qty2 beads por eje. Hardware y masa individuales usan dimensiones terminadas.

DOOR_ENTRY:

```text
head_cut = W + 2*e(F)                 # qty1, 45/45, dos extremos soldados
jamb_cut = H + e(F)                   # qty2, 45/90, un extremo soldado
threshold_cut = W - 2*F.face          # qty1, 90/90, aluminio, sin acero/soldadura
leaf_outer_width = frame_clear_width - 2*door_leaf_side_clearance_mm
leaf_outer_height = H - F.face - door_threshold_mm - door_bottom_clearance_mm + sash_overlap_mm
sash_cut_axis = leaf_outer_axis + S.welding_loss_mm
sash_steel_axis = sash_cut_axis - 2*e(S) - 2*S.reinforcement_gap_mm
panel_axis = leaf_outer_axis - 2*S.face + 2*rebate_depth_mm - 2*clearance
```

Cabezal soldado a jambas; jambas sólo arriba, abajo unión mecánica al umbral.
Jambas espejadas pueden agruparse 45/90 según orientación por pieza de máquina.
SASH puerta qty2 por eje, dos extremos soldados. Umbral tiene ProfileRole.THRESHOLD,
material ALUMINIUM y no participa en peso móvil. Panel obligatorio por panel_article_sku,
no GlassPiece; área exacta y masa según §3.3. PD-06-20: panel sí lleva junquillos,
bead_cut=infill_length+rule.cut_add_mm, regla por espesor de infill. G7:24.00 mm
selecciona GB24/JQ-10,705.00 qty2 y1937.00 qty2, ProfileCut GLAZING_BEAD con bay_id/leaf_id.
No se añade masa bead al hardware-selection leaf weight32.35.
Las expresiones DOOR_ENTRY anteriores desarrollan las operaciones de los ejemplos
numéricos explícitos del owner (los operadores de dos bloques llegaron mal formateados).

Fórmulas parciales Extended permanecen fuera del Core: SLIDING_3L usa
(w_inner-2*sliding_lateral_clearance_mm+2*central_overlap_mm)/3; SLIDING_4L usa
(w_inner+3*central_overlap_mm)/4; ambas alturas h_inner-2*pulley_height_mm.
DOOR_DOUBLE usa (w_inner+2*sash_overlap_mm-5.00)/2 y
H-door_threshold_mm-door_bottom_clearance_mm. No implementar por existir estas expresiones;
G8/G9/G11/G12→SHOT-06B, G10→SHOT-24.

### 4.1. Árbol, splits y dimensiones efectivas de BAY en SHOT-03

El contrato de nodo es PRD-04 §2. El motor acepta como top-level `BAY`,
`SPLIT_V`, `SPLIT_H` o un wrapper `ROOT`, que normaliza sin alterar la
semántica. Todas las dimensiones dentro del límite Python son `Decimal`.
`split_offset_mm` se mide desde el origen local hasta el eje del mullion:
desde la izquierda para `SPLIT_V` y desde arriba para `SPLIT_H`. Las
dimensiones efectivas de cada BAY se derivan durante el recorrido y no son
una segunda entrada editable.

G4 queda congelado como `SPLIT_V` de `1800.00 × 1500.00`, offset `900.00`,
perfil `POSTE-V`, con `bay_fixed` FIXED/24.00/`4-16-4 Float Incoloro` y
`bay_ob` TILT_TURN_RIGHT/20.00/`4-12-4 Float Incoloro`. Tras descontar el
FRAME de `60.00` y la media cara del MULLION de `80.00`, ambos BAY miden
`800.00 × 1380.00`.

### 4.2. Fórmulas de MULLION y GLAZING_BEAD

```python
# El artículo se selecciona por el rol/SKU efectivo de la pieza.
if mullion_article.role == ProfileRole.MULLION_V:
    mullion_cut = parent_clear_height + Decimal('2') * params.end_milling_overlap_mm
else:  # MULLION_H
    mullion_cut = parent_clear_width + Decimal('2') * params.end_milling_overlap_mm

mullion_steel = (
    mullion_cut - Decimal('2') * mullion_article.reinforcement_gap_mm
)

bead_rule = params.glazing_bead_rules[glass_thickness_mm]
bead_cut_length = infill_length + bead_rule.cut_add_mm
```

`glazing_bead_matrix.cut_add_mm` es la autoridad persistida del suplemento
longitudinal. DEMO_60 congela `9.00 mm` para sus cinco espesores; queda
prohibido hardcodear `+9.00` en `geometry.py`. Los cortes se emiten con el
artículo de `bead_rule` y rol `GLAZING_BEAD`.

### 4.3. Contrato puro de salida/BOM base de SHOT-03

```python
class ProfileCut(BaseModel):
    sku: str
    role: ProfileRole
    material: MaterialType
    length_mm: Decimal
    angle_left: Decimal
    angle_right: Decimal
    qty: int
    bay_id: Optional[str] = None
    leaf_id: Optional[str] = None

class ReinforcementPiece(BaseModel):
    parent_profile_sku: str
    reinforcement_sku: Optional[str] = None
    role: ProfileRole
    length_mm: Decimal
    qty: int
    bay_id: Optional[str] = None
    leaf_id: Optional[str] = None

class EngineResult(BaseModel):
    profile_cuts: List[ProfileCut]
    reinforcements: List[ReinforcementPiece]
    glasses: List[GlassPiece]
    panels: List[PanelPiece]
    hardware_items: List[HardwareItem]
    leaf_weights: List[LeafWeight]

# La respuesta de cálculo añade calculation_hash calculado por función pura
# sobre request explícito + resultado, según PRD-FRONTEND §1.1.

```

La salida SHOT-06 incluye material real en cortes, leaf_id nullable en piezas,
panels y leaf_weights. Hardware se resuelve según §3.2. Profile_cuts incluye THRESHOLD
para G7, sin refuerzo. No incluye inspector, BFD, pricing, costos, auditoría ni OT.
El hash requiere request explícito, sin leer HTTP/DB desde el motor; el contrato de
preimagen y response está en PRD-FRONTEND. G1–G4 preservan toda geometría.

---

---

## 5. Tabla Canónica de Correspondencia: Base de Datos ⟷ `/engine` (Regla Cero)

Para garantizar cero ambigüedad entre el esquema relacional PostgreSQL y las clases
Pydantic del motor, esta tabla define el mapeo exhaustivo de `SystemParams`. `DIRECTO`
significa columna persistida con correspondencia uno a uno; `DERIVADO` significa que el
loader obtiene el valor de filas relacionadas o transforma una autoridad persistida;
`FALLBACK` significa que no existe columna canónica y se usa el default tipado del motor.
Un fallback nunca prevalece sobre un valor persistido.

| Engine field | Origen DB | Tabla / columna | Unidad / tipo | Autoridad | Nullable | Quién modifica | DEMO_60 / fallback | Regla de derivación |
|---|---|---|---|---|:---:|---|---|---|
| `system_code` | DIRECTO | `profile_systems.code` | `str` ← `VARCHAR(50)` | Ficha fabricante | NO | Admin / Taller | `DEMO_60` | Copia exacta del sistema seleccionado. |
| `depth_mm` | DIRECTO | `profile_systems.depth_mm` | `Decimal`, mm ← `NUMERIC(10,2)` | Ficha fabricante | NO | Admin / Taller | `60.00` | Conversión exacta `NUMERIC` → `Decimal`; prohibido `float`. |
| `material` | DIRECTO | `profile_systems.material` | `MaterialType` ← `material_type` | Ficha fabricante | NO | Admin / Taller | `PVC` | Mapeo unívoco del enum PostgreSQL al enum del motor. |
| `effective_profile_articles` | DERIVADO como colección obligatoria; no persistido como agregado | Filas efectivas de `profile_articles` del sistema, indexadas por `role`; columnas `sku`, `role`, `material`, `face_width_mm`, `welding_loss_mm`, `reinforcement_gap_mm`, `weight_kg_m`, `steel_weight_kg_m`, `reinforcement_sku` | `Dict[ProfileRole, EffectiveProfileArticle]` | Cada fila `profile_articles`; soldadura, cara y gap pertenecen al artículo | NO | Taller mediante catálogo; adapter sólo mapea | FRAME cara/gap/soldadura `60.00/15.00/6.00`; SASH `75.00/15.00/6.00`; MULLION_V/H `80.00/5.00/0.00`; GLAZING_BEAD soldadura `0.00` | El adapter entrega un objeto distinto por artículo/rol efectivo. Geometría consume `face_width_mm` y `reinforcement_gap_mm` directamente del artículo; `welding_loss_per_end(article)` es derivado y nunca se almacena como scalar común. |
| `glazing_bead_rules` | DERIVADO como colección obligatoria; no persistido como agregado | `glazing_bead_matrix` unida con su `profile_articles` por `bead_article_id`; columnas `glass_thickness_mm`, `bead_width_mm`, `gasket_interior_mm`, `gasket_exterior_mm`, `cut_add_mm` y artículo efectivo | `Dict[Decimal, GlazingBeadRule]` | Fila de matriz + artículo GLAZING_BEAD referenciado | NO | Taller mediante catálogo; adapter sólo mapea | Cinco espesores `4/5/6/20/24`; `cut_add_mm=9.00` en todos | Indexar por `glass_thickness_mm`; `bead_cut_length = infill_length + rule.cut_add_mm`; prohibido hardcodear el suplemento. |
| `rebate_depth_mm` | FALLBACK; no persistido en SHOT-02 | — | `Decimal`, mm | Default tipado del motor hasta existir columna canónica | NO | Sistema / futura ficha aprobada | fallback `20.00` | Sin derivación DB; no inferir desde `depth_mm`, cara o junquillo. |
| `end_milling_overlap_mm` | FALLBACK; no persistido en SHOT-02 | — | `Decimal`, mm | Default tipado del motor hasta existir columna canónica | NO | Sistema / futura ficha aprobada | fallback `0.00` | Sin derivación DB; prohibido inferir desde `sash_overlap_mm`. |
| `sash_overlap_mm` | DIRECTO | `profile_systems.sash_overlap_mm` | `Decimal`, mm ← `NUMERIC(4,2)` | Catálogo técnico del sistema | NO | Taller | `8.00` | Copia exacta del sistema seleccionado. |
| `glass_clearance_white_mm` | DIRECTO | `profile_systems.glass_clearance_white_mm` | `Decimal`, mm ← `NUMERIC(4,2)` | Ficha de holgura del sistema | NO | Taller | `5.00`; fallback de clase `3.00` sólo sin catálogo | El valor persistido prevalece; seleccionar cuando `is_foiled = FALSE`. |
| `glass_clearance_foil_mm` | DIRECTO | `profile_systems.glass_clearance_foil_mm` | `Decimal`, mm ← `NUMERIC(4,2)` | Ficha de holgura del sistema | NO | Taller | `5.00`; fallback `5.00` | Seleccionar cuando `is_foiled = TRUE`. |
| `pulley_height_mm` | DIRECTO | `profile_systems.pulley_height_mm` | `Decimal`, mm ← `NUMERIC(4,2)` | Ficha de rodamientos del sistema | NO | Taller | `12.00` | Copia exacta del sistema seleccionado. |
| `central_overlap_mm` | DIRECTO | `profile_systems.central_overlap_mm` | `Decimal`, mm ← `NUMERIC(4,2)` | Ficha de traslape del sistema | NO | Taller | `40.00` | Copia exacta; valor canónico que produce G5 = `966.00 mm`. |
| `sliding_lateral_clearance_mm` | DIRECTO | `profile_systems.sliding_lateral_clearance_mm` | `Decimal`, mm ← `NUMERIC(4,2)` | Ficha de corredera del sistema | NO | Taller | `0.00` | Copia exacta del sistema seleccionado. |
| `sliding_end_add_mm` | DIRECTO | `profile_systems.sliding_end_add_mm` | `Decimal`, mm ← `NUMERIC(4,2)` | Ficha de corredera del sistema | NO | Taller | `6.00` | Copia exacta del sistema seleccionado. |
| `corner_bracket_loss_mm` | DIRECTO | `profile_systems.corner_bracket_loss_mm` | `Decimal`, mm ← `NUMERIC(4,2)` | Ficha del sistema de aluminio | NO | Taller | `0.00` | Copia exacta; sólo participa en la rama de material ALUMINIUM. |
| `hook_depth_mm` | DIRECTO | `profile_systems.hook_depth_mm` | `Decimal`, mm ← `NUMERIC(4,2)` | Ficha del sistema | NO | Taller | `0.00` | Copia exacta del sistema seleccionado. |
| `door_threshold_mm` | DIRECTO | `profile_systems.door_threshold_mm` | `Decimal`, mm ← `NUMERIC(4,2)` | Ficha de puerta del sistema | NO | Taller | `30.00` | Copia exacta del sistema seleccionado. |
| `door_bottom_clearance_mm` | DIRECTO | `profile_systems.door_bottom_clearance_mm` | `Decimal`, mm ← `NUMERIC(4,2)` | Ficha de puerta del sistema | NO | Taller | `20.00` | Copia exacta del sistema seleccionado. |
| `rail_type` | DIRECTO | `profile_systems.rail_type` | `RailType` ← `VARCHAR(10)` | Ficha de riel del sistema | NO | Taller | `dual` | Mapeo unívoco al enum; `hardware_kits.rail_type` se usa para matching, no como segunda autoridad del sistema. |
| `pvc_weight_kg_m` | DERIVADO por artículo | `profile_articles.weight_kg_m` del artículo seleccionado | `Decimal`, kg/m ← `NUMERIC(8,4)` | Ficha de peso del artículo | NO | Taller | `1.2000`; fallback `1.2000` | Resolver por artículo/rol; el peso persistido prevalece sobre el fallback de `SystemParams`. |
| `steel_weight_kg_m` | DERIVADO por artículo | `profile_articles.steel_weight_kg_m` del artículo seleccionado | `Decimal`, kg/m ← `NUMERIC(8,4)` | Ficha de refuerzo del artículo | NO | Taller | `1.7000`; fallback `1.7000` | Resolver por artículo/rol; no asumir el mismo refuerzo para artículos distintos. |
| `hardware_kit_weight_kg` | FALLBACK de sistema cuando hardware_kits.weight_kg es NULL | Sin columna PS; HK.weight_kg prevalece | `Decimal`, kg | Fallback tipado aprobado PD-06-14; HK.weight_kg prevalece | NO | Sistema / futura ficha aprobada | fallback `2.50` | Si HK.weight_kg es NULL: multiplicar este fallback por 1.10; no derivar desde contents ni capacidad. |
| `available_hardware_kits` | DERIVADO como colección | Filas de `hardware_kits` del `system_id` seleccionado; columnas `sku`, `name`, `opening_type`, límites, `rail_type`, cantidades, `contents` y `weight_kg` | `List[HardwareKitRule]` | Catálogo de herrajes visible por RLS | NO | Admin / Taller | 5 kits: `TURN`, `TILT_TURN`, `SLIDING`, `AWNING`, `DOOR`; `[]` no permite seleccionar hoja operable | Cargar sólo kits `is_active=TRUE` visibles para el tenant/globales y mapear cada columna sin inferencias. |

**Cobertura normativa SHOT-06:** `27/27` campos de SystemParams previstos: los 23
anteriores, tres parámetros PS y available_panel_rules. El runtime baseline aún tiene
23 campos; no se afirma que la implementación haya ocurrido. Se verificará N/N real
con modelos y tests una vez levantados los bloqueos Regla 0.

| Engine field nuevo | Origen DB | Tabla / columna | Unidad / tipo | Autoridad | Nullable | Quién modifica | DEMO_60 / fallback | Derivación |
|---|---|---|---|---|---|---|---|---|
| sliding_glazing_deduction_width_mm | DIRECTO | profile_systems.sliding_glazing_deduction_width_mm | Decimal mm, NUMERIC(10,2) | Resolución owner PD-01, sintético DEMO_60 | NO | Catálogo Admin/Taller autorizado | 20.00 / sin fallback | Deducción total W una vez por vidrio SLIDING |
| sliding_glazing_deduction_height_mm | DIRECTO | profile_systems.sliding_glazing_deduction_height_mm | Decimal mm, NUMERIC(10,2) | Misma autoridad | NO | Catálogo Admin/Taller autorizado | 20.00 / sin fallback | Deducción total H una vez por vidrio SLIDING |
| door_leaf_side_clearance_mm | DIRECTO | profile_systems.door_leaf_side_clearance_mm | Decimal mm, NUMERIC(10,2) | Resolución owner PD-05, sintético DEMO_60 | NO | Catálogo Admin/Taller autorizado | 7.00 / sin fallback | Dos lados de hoja puerta |
| available_panel_rules | DERIVADO | infill_articles visibles/activos del system | Dict[str,PanelRule] por SKU | Resolución owner PD-07 | Colección no nullable; masa sí | Catálogo Admin/Taller autorizado | PANEL-SANDWICH-DEMO-24; sin sustituto | Mapear SKU/name/kind/thickness/weight sin I/O engine |

Autoridades de submodelos añadidas/modificadas:

| Engine field | DB authority / tipo / unidad | Nullable | DEMO_60 | Fallback | Fuente / modificador |
|---|---|---|---|---|---|
| EffectiveProfileArticle.material / ProfileCut.material | profile_articles.material, material_type | NO | PVC existentes; UMBRAL-ALU ALUMINIUM | No material inferido | PD-06; catálogo autorizado |
| EffectiveProfileArticle.weight_kg_m | PA.weight_kg_m NUMERIC(8,4), kg/m | DB NO, modelo admite None | 1.2000 en artículos existentes | Sólo PVC: params.pvc_weight_kg_m*1.10 | PD-12/13; catálogo autorizado |
| EffectiveProfileArticle.steel_weight_kg_m | PA.steel_weight_kg_m NUMERIC(8,4), kg/m | DB NO, modelo admite None | 1.7000 | params.steel_weight_kg_m*1.10 si pieza lleva acero | PD-12/13; catálogo autorizado |
| HardwareKitRule.weight_kg | hardware_kits.weight_kg NUMERIC(8,2), kg | SÍ | 2.50 en los cinco kits | params.hardware_kit_weight_kg*1.10 =2.75 | PD-14; catálogo autorizado |
| PanelRule.sku/name/kind | infill_articles.sku/name/kind | NO | PANEL-SANDWICH-DEMO-24 / Panel Sándwich Demo 24mm / SANDWICH_PANEL | Ninguno | PD-07 sintético; catálogo autorizado |
| PanelRule.thickness_mm | infill_articles.thickness_mm NUMERIC(6,2), mm | NO | 24.00 | Ninguno | Misma autoridad |
| PanelRule.weight_kg_m2 | infill_articles.weight_kg_m2 NUMERIC(10,4), kg/m² | SÍ | 10.0000 | MissingWeightAuthority si usado sin peso | Misma autoridad |
| HardwareComponent.sku/name/qty/unit | hardware_kits.contents JSONB, qty Decimal | Shape requerido al usar contenido | AWNING: DEMO-STAY-16 / Compás a fricción 16 pulgadas /2/unit; DOOR: DEMO-LOCK-MULTIPOINT / Cerradura multipunto Demo /1/unit | No inventar componentes; conservar orden persistido | PD-04/08/09; catálogo autorizado |
| ParametricNode.panel_article_sku | Referencia request a infill_articles.sku del system | Obligatorio DOOR_ENTRY | PANEL-SANDWICH-DEMO-24 | Ninguno | PD-07; input humano/catálogo |
| leaf_id de piezas/pesos/hardware | Derivado BAY/hoja | SÍ | SLIDING :L1/:L2; null donde no necesario | Ninguno | PD-02; motor puro |


### 5.0.1. Mapping de reglas de hardware: 13/13 campos de HardwareKitRule

Valores de cinco kits en orden TURN / TILT_TURN / SLIDING / AWNING / DOOR;
HK=hardware_kits. Fuente: seed baseline para tres existentes y resolución sintética
PD-04/08/11/14 para modificaciones. Modificador: catálogo propio bajo RLS o admin global.
Ninguna restricción dimensional admite fallback.

| Engine field | DB authority / tipo | DEMO_60 en orden indicado | Fallback | Nullable |
|---|---|---|---|---|
| sku | HK.sku VARCHAR(100) | KIT-TURN / KIT-TILT-TURN / KIT-SLIDING / KIT-AWNING-16 / KIT-DOOR-MULTIPOINT | Ninguno | No |
| name | HK.name VARCHAR(255) | Kit Practicable Demo 60 / Kit Vorne OB 100kg / Kit Corredera Demo 60 / Kit Proyectante Compás 16" 45kg / Kit Puerta Entrada Multipunto Demo 60 | Ninguno; nombres literales §6 | No |
| opening_type | HK.opening_type VARCHAR(30) | TURN / TILT_TURN / SLIDING / AWNING / DOOR | Ninguno | No |
| min_leaf_width_mm | HK.min_leaf_width_mm NUMERIC(10,2), mm | 400 /450 /400 /400 /700 | Ninguno | No |
| max_leaf_width_mm | HK.max_leaf_width_mm NUMERIC(10,2), mm | 1200 /1400 /1500 /1200 /1200 | Ninguno | No |
| min_leaf_height_mm | HK.min_leaf_height_mm NUMERIC(10,2), mm | 500 /600 /500 /400 /1800 | Ninguno | No |
| max_leaf_height_mm | HK.max_leaf_height_mm NUMERIC(10,2), mm | 2400 /2400 /2500 /1000 /2400 | Ninguno | No |
| max_leaf_weight_kg | HK.max_leaf_weight_kg NUMERIC(6,2), kg | 80 /100 /120 /45 /120 | Ninguno; capacidad, no masa | No |
| rail_type | HK.rail_type VARCHAR(10) | Todos dual | Clase DUAL; DB prevalece | No |
| carriages_qty | HK.carriages_qty INT | 0 /0 /2 /0 /0 | Default DB2; fila aprobada prevalece | No |
| stay_arms_qty | HK.stay_arms_qty INT | 0 /1 /0 /2 /0 | Default DB1; fila aprobada prevalece | No |
| contents | HK.contents JSONB | [] /[] /[] /DEMO-STAY-16 qty2 unit /DEMO-LOCK-MULTIPOINT qty1 unit | No inventar componentes; orden persistido | No |
| weight_kg | HK.weight_kg NUMERIC(8,2), kg | Todos2.50 | params.hardware_kit_weight_kg*1.10 sólo NULL | Sí |

HardwareComponent mapea las cuatro claves SKU/name/qty/unit de cada elemento JSONB,
qty Decimal exacto; no float ni coerción desde float. JSONB array conserva orden.
HardwareItem hereda kit_sku/name de kit seleccionado; qty1/unit kit; bay_id del nodo,
leaf_id derivado; contents anidados. No otra autoridad ni expansión comercial.

### 5.0.2. Artículos efectivos y reglas de junquillo completos

Cada EffectiveProfileArticle contiene sku,role,material,face_width_mm,welding_loss_mm,
reinforcement_gap_mm,weight_kg_m,steel_weight_kg_m,reinforcement_sku:9/9 desde PA homónimos.
SKU/role/material no nullable; dimensiones NUMERIC(10,2) mm no nullable; masas lineales
NUMERIC(8,4) kg/m DB no nullable, Optional interno para fallback; reinforcement_sku
nullable. Fuente/edición: seed y resolución owner, catálogo autorizado bajo RLS.
Los siete artículos previos pesan1.2000/1.7000 por default DB y reinforcement_sku=NULL.
UMBRAL-ALU no participa en masa móvil ni genera acero; no inferir que otro NULL elimina acero.

| SKU PA | Rol | Material | Cara mm | Soldadura total mm | Gap mm | Autoridad / fallback |
|---|---|---|---|---|---|---|
| MARCO | FRAME | PVC |60.00|6.00|15.00|Seed baseline; sin fallback geométrico|
| HOJA | SASH | PVC |75.00|6.00|15.00|Seed baseline; sin fallback geométrico|
| POSTE-V | MULLION_V | PVC |80.00|0.00|5.00|Seed baseline; sin fallback geométrico|
| POSTE-H | MULLION_H | PVC |80.00|0.00|5.00|Seed baseline; sin fallback geométrico|
| JQ-24 | GLAZING_BEAD | PVC |24.00|0.00|15.00|Seed baseline; sin fallback geométrico|
| JQ-14 | GLAZING_BEAD | PVC |14.00|0.00|15.00|Seed baseline; sin fallback geométrico|
| JQ-10 | GLAZING_BEAD | PVC |10.00|0.00|15.00|Seed baseline; sin fallback geométrico|
| UMBRAL-ALU | THRESHOLD | ALUMINIUM |30.00|0.00|0.00|PD-06 sintético; sin fallback geométrico|

GlazingBeadRule:6/6 campos, de GB.glass_thickness_mm, bead_article_id→PA completo,
bead_width_mm,gasket_interior_mm,gasket_exterior_mm,cut_add_mm. Dimensiones GB son
NUMERIC(6,2) mm NOT NULL; sin fallback runtime; edición catálogo autorizado.

| Espesor total mm | Artículo | Ancho bead mm | Juntas int/ext mm | Cut add mm |
|---|---|---|---|---|
|4.00|JQ-24|24.00|3.00/3.00|9.00|
|5.00|JQ-24|24.00|2.50/2.50|9.00|
|6.00|JQ-24|24.00|2.00/2.00|9.00|
|20.00|JQ-14|14.00|3.00/3.00|9.00|
|24.00|JQ-10|10.00|3.00/3.00|9.00|

Loader: PS/PA/GB/HK/infill se restringen al system y organización activa, o global
visible bajo RLS. PS/HK/GB/infill deben estar activos; PA no tiene is_active en DDL.
PA.system_id e infill.system_id son NOT NULL; org_id nullable para global. HK.system_id
nullable en DDL, pero loader canónico sólo carga system exacto, no kits genéricos NULL.
PanelRule:5/5 sku/name/kind/thickness_mm/weight_kg_m2 desde infill homónimos;
kind SANDWICH_PANEL, espesor24.00, peso10.0000 sintético; sólo peso nullable y sin fallback.

### 5.1. Contrato canónico y generalizable de soldadura por rol

1. `profile_articles.welding_loss_mm` es la **única autoridad persistida y editable**.
   No existe ni debe crearse una segunda autoridad en `profile_systems`, `SystemParams`
   o cualquier otro objeto del motor.
2. `SystemParams` no contiene un scalar global de soldadura. Contiene los artículos
   efectivos como objetos separados por rol; una representación equivalente es válida
   sólo si preserva inequívocamente la identidad del artículo y no colapsa roles.
3. El adapter/loader que implemente SHOT-03 carga `welding_loss_mm` desde cada fila
   efectiva de `profile_articles`. FRAME consume el artículo FRAME; SASH consume SASH;
   MULLION_V, MULLION_H y GLAZING_BEAD consumen sus propios artículos.
4. La única transformación permitida es
   `welding_loss_per_end(article) = article.welding_loss_mm / Decimal('2')`. El resultado
   es efímero y derivado: nunca se persiste ni se vuelve editable.
5. `calculate_geometry` mantiene referencias y variables diferentes:
   `frame_article` → `frame_welding_loss_per_end` y
   `sash_article` → `sash_welding_loss_per_end`. Por ello una misma ejecución representa,
   sin reinterpretación contextual, por ejemplo FRAME `6.00 → 3.00 mm/end` y SASH
   `5.00 → 2.50 mm/end`.
6. DEMO_60 congela FRAME `6.00 → 3.00 mm/end`, SASH `6.00 → 3.00 mm/end`,
   MULLION_V/H `0.00 → 0.00 mm/end` y GLAZING_BEAD `0.00 → 0.00 mm/end`.

### 5.2. Contrato canónico de cara y gap por artículo

1. `profile_articles.face_width_mm` y
   `profile_articles.reinforcement_gap_mm` pertenecen al artículo efectivo;
   no existen scalars editables equivalentes en `SystemParams`.
2. FRAME y SASH calculan acero como
   `pvc_cut - welded_end_count × welding_loss_per_end(article) - 2 × article.reinforcement_gap_mm`.
   FRAME/SASH rectangulares: 2; jamba DOOR_ENTRY: 1; umbral: no refuerzo.
3. MULLION calcula acero como
   `mullion_cut - 2 × mullion_article.reinforcement_gap_mm`.
4. DEMO_60 congela FRAME `face=60.00/gap=15.00`, SASH
   `face=75.00/gap=15.00` y MULLION_V/H `face=80.00/gap=5.00`.
5. El cálculo de un split consume la cara del artículo MULLION_V o
   MULLION_H seleccionado, preservando catálogos futuros asimétricos.

---

## 6. Catálogo Maestro de Casos de Oro (G1 – G12 + G-Pro1)

### 6.1. Definición de Gates: Core Gate vs Extended Gate (SHOT-06)
* **Core Gate (Obligatorio en Fase 1 / Starter):** G1, G2, G3, G4 (SHOT-03) y G5, G6, G7 (SHOT-06) con tolerancia `0.00 mm`. Bloquea la entrega del cotizador Starter.
* **Extended Gate (Tipologías Complejas / Fase 2):** G8 (Corredera 3H), G9 (Corredera 4H), G11 (Puerta Doble), G12 (Fijo Gran Formato); pueden diferirse formalmente a SHOT-06B / Fase 2 mediante decisión explícita del owner sin bloquear el lanzamiento de Starter.
* **Deferred Gate (Fase 4):** G10 (Monorriel 2H con carros pesados $\ge 80\text{ kg}$).

### 6.2. Matriz de Casos de Oro y Derivación Analítica

| Caso ID | Gate | Tipología y Medidas Nominales | Especificación y Despiece Crítico | Estado de Aprobación |
|---|:---:|---|---|---|
| **G1** | **Core** | **Paño Fijo Simple** $1000 \times 1000\text{ mm}$ blanco | Marco: $1006.00\text{ mm}$ (H/V) · Acero: $970.00\text{ mm}$ · Vidrio: $910.00 \times 910.00\text{ mm}$ · Junquillo: $919.00\text{ mm}$. | 🔒 **CONGELADO** |
| **G2** | **Core** | **Practicable 1 Hoja** $800 \times 1200\text{ mm}$ | Hoja: $702.00 / 1102.00\text{ mm}$ · Acero Hoja: $666.00 / 1066.00\text{ mm}$ · Vidrio DVH 24mm: $576.00 \times 976.00\text{ mm}$. | 🔒 **CONGELADO** |
| **G3** | **Core** | **Oscilobatiente 1 Hoja** $1000 \times 1400\text{ mm}$ | Hoja: $902.00 / 1302.00\text{ mm}$ · Vidrio DVH 20mm: $776.00 \times 1176.00\text{ mm}$ · Kit Vorne OB (100kg). | 🔒 **CONGELADO** |
| **G4** | **Core** | **Compuesta Fijo + OB con Poste** $1800 \times 1500\text{ mm}$ | Poste: $1380.00\text{ mm}$ · Acero Poste: $1370.00\text{ mm}$ · Vidrio Fijo: $830 \times 1410$ · Vidrio OB: $696 \times 1276$. | 🔒 **CONGELADO** |
| **G5** | **Core** | **Corredera 2 Hojas** $2000 \times 2100\text{ mm}$ | Hojas PVC: 4 de $966.00\text{ mm}$ (H) y 4 de $1956.00\text{ mm}$ (V) · Vidrios: 2 de $820.00 \times 1810.00\text{ mm}$. *(Ver desglose §6.3)* | 🔒 **CONGELADO** |
| **G6** | **Core** | **Proyectante** $1200 \times 800\text{ mm}$ | Hoja: $1102.00 / 702.00\text{ mm}$ · Compás a fricción $16''$ ($45\text{ kg}$). | 🔒 **CONGELADO** |
| **G7** | **Core** | **Puerta de Entrada Multipunto** $950 \times 2150\text{ mm}$ | Cabezal: $956\text{ mm}$ · Jambas: $2153\text{ mm}$ · Umbral Alu: $830\text{ mm}$ · Panel sándwich: $696 \times 1928\text{ mm}$. | 🔒 **CONGELADO** |
| **G8** | **Extended** | **Corredera 3 Hojas** | Valida traslape doble + Regla R12. | ⏳ **CONGELAR EN SHOT-06B** |
| **G9** | **Extended** | **Corredera 4 Hojas** $4000 \times 2000\text{ mm}$ | Traslape triple central + asimetría opcional. | ⏳ **CONGELAR EN SHOT-06B** |
| **G10** | **Deferred** | **Corredera Monoriel 2 Hojas** $3000 \times 2400\text{ mm}$ | Regla R14 (Carros reforzados $\ge 80\text{ kg/rueda}$). | ⏳ **FASE 4** |
| **G11** | **Extended** | **Puerta Doble Hoja** $1800 \times 2100\text{ mm}$ | Perfil inversor central sin poste fijo. | ⏳ **CONGELAR EN SHOT-06B** |
| **G12** | **Extended** | **Fijo Gran Formato** $3000 \times 2500\text{ mm}$ | Inercia $I_x$ crítica + vidrio laminado de seguridad (NCh 132). | ⏳ **CONGELAR EN SHOT-06B** |
| **G-Pro1** | **Sign-Off** | **Fijo 1000×1000 (Plantilla PRIVADA Proline Pro6004)** | Pérdida de fusión $2.5\text{ mm} \rightarrow$ Marco $1005.00\text{ mm}$, holgura acero $56.5\text{ mm}$. | 🟡 **AMARILLO (Sign-off Físico)** |

---

### 6.3. G5: deducciones técnicas persistidas y fixture completo

DEMO_60 SYNTHETIC FIXTURE: W=2000.00, H=2100.00, WHITE, SLIDING_2L,
glass_thickness_mm=20.00, glass_spec="4-12-4 Float Incoloro", rail dual.
F.face=60.00, S.face=75.00, central_overlap=40.00, pulley_height=12.00,
clearance=5.00, rebate_depth=20.00, soldadura total F/S=6.00.

```text
frame_h=2000+6=2006; frame_v=2100+6=2106 (qty2 cada uno)
frame_steel_h=2006-6-30=1970; frame_steel_v=2106-6-30=2070 (qty2)
inner=1880×1980
sash_cut_w=(1880+40)/2+6=966; sash_cut_h=1980-2*12=1956
finished_w=966-6=960; finished_h=1956-6=1950
base_glass_w=960-150+40-10=840
base_glass_h=1950-150+40-10=1830
glass_w=840-PS.sliding_glazing_deduction_width_mm=840-20=820.00
glass_h=1830-PS.sliding_glazing_deduction_height_mm=1830-20=1810.00
sash_steel_w=966-6-30=930; sash_steel_h=1956-6-30=1920
beads=820+GB.cut_add_mm=829;1810+GB.cut_add_mm=1819
```

Deducciones TOTAL por eje, no por lado; columnas PS NOT NULL nuevas, valor20.00
sintético de sistema, sin hardcode en engine. No son cut_add_mm ni modifican beads.
Por hoja L1/L2: qty2 SASH y acero por eje, un vidrio, qty2 beads por eje. Total dos
vidrios820×1810, cuatro de cada longitud SASH/acero/bead. Hardware KIT-SLIDING por hoja.
Cortes966/1956 no son dimensiones exteriores; hardware usa960/1950.

### 6.4. G6 AWNING completo

DEMO_60:1200×800, WHITE, AWNING, thickness20.00, spec4-12-4 Float Incoloro.
FRAME1206/806 qty2; acero1170/770 qty2; SASH finished1096×696;
cortes1102/702 qty2, acero1066/666 qty2; vidrio976×576;
beads985/585 qty2. Primitive común TURN/TILT_TURN/AWNING.
KIT-AWNING-16, nombre `Kit Proyectante Compás 16" 45kg`, AWNING, W400–1200,
H400–1000, max45.00, dual, carros0, compases2, weight2.50.
Contents:[{sku:DEMO-STAY-16,name:Compás a fricción 16",qty:2,unit:unit}].
SKU/rangos sintéticos, no ficha comercial.

### 6.5. G7 DOOR_ENTRY completo, incluyendo PD-06-20

950×2150, hoja con PANEL-SANDWICH-DEMO-24 obligatorio. Cabezal956 qty1 45/45,
jambas2153 qty2 45/90; acero cabezal920 qty1, jambas2120 qty2.
UMBRAL-ALU830 qty1 90/90, THRESHOLD/ALUMINIUM; cara30, soldadura/gap0,
reinforcement_sku NULL y no genera acero. Hoja finished816×2048,
SASH822/2054 qty2 y acero786/2018 qty2. Panel696×1928, área exacta1.341888,
masa exacta13.41888, outputs área1.3419 y peso13.42.
PanelRule: nombre Panel Sándwich Demo 24mm, kind SANDWICH_PANEL, thickness24.00,
weight_kg_m2=10.0000 sintético. Beads panel705.00/1937.00 qty2, regla24.00/JQ-10.
Beads no se suman a masa móvil32.35 kg.
KIT-DOOR-MULTIPOINT, nombre Kit Puerta Entrada Multipunto Demo 60, DOOR,
W700–1200,H1800–2400,max120.00,dual,carros0,compases0,weight2.50.
Contents:[{sku:DEMO-LOCK-MULTIPOINT,name:Cerradura multipunto Demo,qty:1,unit:unit}].
No inventar otros componentes comerciales.

### 6.6. G3 hardware y golden compuesto: PD-06-19 resuelta

Renombrar sólo display name de KIT-TILT-TURN a `Kit Vorne OB 100kg`;
SKU y límites existentes intactos, weight2.50. Otros datos sintéticos no son ficha Vorne.
Hardware deja xfail y pasa a resolved SHOT-06. Se congelan dos expectations independientes:

| Caso | PVC exacto | Acero exacto | Vidrio exacto | Kit | Total exacto | HALF_UP2 |
|---|---|---|---|---|---|---|
| G3 1000×1400, hoja896×1296, vidrio776×1176 |5.2896|7.2488|18.25152|2.50|33.28992|33.29|
| Golden OB hoja666×1296, vidrio546×1176 |4.7376|6.4668|12.84192|2.50|26.54632|26.55|

PD-06-19 RESUELTA: G3 standalone33.289920→33.29 kg, comparación exacta33.289920<=100.00.
Golden compuesto bay_2 26.546320→26.55 kg. La cifra anterior26.55 para G3 queda revocada.
Tests independientes preservan ambas geometrías y totales; no comparten expectation.

### 6.7. Semántica neutral de retención de infill (PD-06-20)

GB.glass_thickness_mm conserva nombre DB por compatibilidad; significa espesor del
infill retenido (vidrio/panel u otro infill futuro explícitamente soportado).
Helper neutral resolve_bead_rule(infill_thickness_mm,params), sin duplicar lookup
vidrio/panel ni acoplar selección a GlassPiece. Panel sigue PanelPiece, sin glass_spec,
sin densidad/masa de vidrio. Beads siguen ProfileCut GLAZING_BEAD, no PanelBeadPiece.
