# DEKOPEN — BIBLIA DE EJECUCIÓN Y SUITE MAESTRA COMPLETA (v1.2)
**Versión Oficial:** 1.2 (Enterprise AI Gateway & ReAct Governance Standard)
**Hash de Integridad Normativa:** [HASH-RECALCULAR-AL-EMITIR]
**Fecha de Emisión:** 30 de Agosto de 2026

---



<!-- INICIO DE CONSTITUTION.md -->


# DEKOPEN — CONSTITUCIÓN DEL BUILDER (v1.2)
**Estado:** Inmutable / Norma Suprema del Repositorio  
**Aplicabilidad:** Absoluta sobre todo agente, desarrollador y commit.

---

```
# DEKOPEN — CONSTITUCIÓN DEL BUILDER (no negociable, lee antes de escribir código)

1. NÚMEROS: si un número aparece en un documento de salida, salió de /engine o de un
   campo editado por humano. JAMÁS del texto libre de un LLM.
2. engine/ es puro: sin I/O, sin Django, sin HTTP. Testeable con `pytest engine/`.
3. Decimal para todo mm y dinero. Prohibido float. CLP sin decimales; USD con 2 decimales.
4. Toda tabla de negocio lleva org_id + política RLS + test de aislamiento. Un tenant
   jamás lee precios de otro. Catálogos globales legibles por todos los usuarios.
5. Escritura de IA → fila en ai_audit_logs ANTES de aplicar el diff. Sin excepciones.
6. Parámetros de serie viven en profile_systems (desde ficha). Cero hardcoded en UI.
   Cambiar una fórmula = PR con caso de oro nuevo. Nunca "ajuste de prompt".
   Precedencia de pesos: profile_articles.weight_kg_m prevalece sobre SystemParams.pvc_weight_kg_m.
7. Casos de Oro (Gold Cases G1–G12 excepto G10 en Fase 1.5; G-Pro1 con sign-off físico).
   Ningún PR se completa con discrepancia > 0.00 mm.
8. Un cambio de fórmula es un PR con caso de oro, no un ajuste de prompt.
9. Monolito modular (apps Django por dominio). Prohibido microservicios.
10. Error del inspector = frase de taller + botón de corrección. Nunca un log crudo.
11. Enviar a cliente, mandar a fábrica, comprar material: requieren clic humano
    explícito. Estados lo modelan; nada automático.
12. project_versions congela números en cada emisión. Cambiar precio enviado = revisión nueva.
13. Webhooks y pagos: idempotencia obligatoria (UNIQUE provider+event_id,
    provider_payment_id). Un retry jamás cobra dos veces.
14. Código/comentarios/DB en inglés. UI solo vía claves i18n ES-CL.
15. Dependencias: SOLO la lista cerrada (PRD-00 §10). Nuevo dep = decisión explícita del owner.
16. Archivos: Supabase Storage con path org_id/… y URLs firmadas con expiración.
17. Prohibido inventar U_w / R_w. Solo desde ficha certificada o no se muestra.
18. offcut_inventory: schema existe, producción prohibida hasta Fase 4.
19. Cada PR cierra con: pytest ✓ · vitest ✓ · ruff ✓ · mypy engine ✓ · checklist DoD.
20. Si el spec tiene un hueco: DETENTE y añade [PENDIENTE-DECISIÓN]. No rellenes con supuestos.
21. AUDITORÍA DE PRECIOS: todo cambio de precio genera fila en price_audit_logs antes de aplicarse.
22. GENERACIÓN AUTOMATIZADA DE GOLDEN SNAPSHOTS: Los fixtures golden de cálculo (e.g.
    golden_example.json) se generan mediante /engine y nunca se editan a mano. Cualquier
    cambio en fórmulas exige regenerar con `make goldgen` e incluir el diff explícito en el PR.
```



<!-- FIN DE CONSTITUTION.md -->

---



<!-- INICIO DE PRD-00.md -->


# PRD-00: CONTRATO MAESTRO, ARQUITECTURA Y PLAN DE EJECUCIÓN S1–S24 (v1.1.2)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.1.2 (Congelada y Bloqueada tras Enmienda F1)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Fase:** 0 (Fundacional)  
**Bloquea a:** Todo el proyecto

---

## 1. Misión del Producto y Tesis de Valor

Dekopen es el **primer sistema operativo de ingeniería, cálculo paramétrico, optimización de corte y cotización comercial para talleres y fabricantes de ventanas de PVC y aluminio** en Chile y Latinoamérica.

> **Tesis Central:** En carpintería de PVC, un error de $1.00\text{ mm}$ destruye el margen de un taller o descalza una obra completa. Dekopen garantiza tolerancia matemática de `0.00 mm` mediante un motor determinista en Python (`/engine`), despiece exacto de perfiles y vidrios, listas de corte optimizadas y generación instantánea de cotizaciones formales.

---

## 2. Precedencia Normativa de Diseño (Parche P1-6)

> [!IMPORTANT]
> **Precedencia de Diseño:** `PRD-DESIGN-SYSTEM-ADOBE.md` (v1.2, Dual Claro/Oscuro) es el documento CANÓNICO e inapelable para tokens de color, contrastes, tipografía y temas. El archivo `UI_UX_DESIGN_SYSTEM.md` queda **SUPERSEDED** salvo en las especificaciones anatómicas de sus componentes (§4), las cuales deben re-expresarse usando exclusivamente los tokens de `PRD-DESIGN-SYSTEM-ADOBE.md` (cero código hexadecimal hardcodeado).

---

## 3. Mapa Completo de Documentos PRD-00 a PRD-19

| ID | Documento | Contenido Principal | Bloquea a | Fase |
|---|---|---|---|---|
| **PRD-00** | Contrato Maestro | Arquitectura, D1–D30, Plan SHOT-01..24, Criterios Go/No-Go | Todo | 0 |
| **PRD-01** | Motor Técnico `/engine` | Fórmulas, dispatcher, `hardware_kits`, BFD 1D, Casos G1–G12 | 4,5,6,7 | 1 |
| **PRD-02** | Modelo de Datos DDL | PostgreSQL 16, RLS, `hardware_kits`, billing, auditoría | Todo | 0 |
| **PRD-03** | Tenancy y Facturación | Planes Starter/Pro/Business, Trial 7d/500cr, Ledger | 5–11 | 0 |
| **PRD-04** | Diseñador 2D SVG | Árbol paramétrico JSON, Canvas React, Atajos 8, 9, 0 | 6,7 | 1 |
| **PRD-05** | Precios y Rentabilidad | 5 Modos de precio, listas de costo, FX buffer 5% | 6 | 1 |
| **PRD-06** | Documentos de Salida | WeasyPrint PDF, Excel openpyxl, OT de taller, BOM Hash | — | 1 |
| **PRD-07** | Inspector Técnico | Reglas R01–R14, semáforo, fixes en 1-clic | 6 | 1 |
| **PRD-08** | Compilador de Catálogos | OCR Gemini multimodal, semáforo 90%, fixtures | 9,10 | 2 |
| **PRD-09** | Intérprete de Planos (S27) | Extracción de cuadros de vanos, bounding boxes | 10 | 2 |
| **PRD-10** | Comandos de Diseño NLP | Diff paramétrico antes/después, Sacred Undo | — | 2 |
| **PRD-11** | Plantillas PDF | 3 slots configurables, bloques protegidos | — | 2 |
| **PRD-12** | Visor 3D Esquemático | React Three Fiber, cinemática de apertura | — | 3 |
| **PRD-13** | Catálogo Global | Publicación comunitaria sin precios privados | — | 3 |
| **PRD-14** | Certificado Fabricabilidad | Doble ciego Tool T8, NCh 432 / NCh 132 (Chile v1) | — | 3 |
| **PRD-15** | Autopilot Max | Cotización desasistida con espera humana obligatoria | — | 3 |
| **PRD-16** | Inventario de Retazos | Códigos QR térmicos, reserva en órdenes | — | 4 |
| **PRD-17** | Bandeja Omnicanal | Captura automática Email y WhatsApp | — | 4 |
| **PRD-18** | Go-To-Market (GTM) | Copy landing, cold outreach completo, Founding 50 | — | 0–1 |
| **PRD-19** | NFR y Seguridad | RPO $\le 5\text{ min}$, RTO $\le 60\text{ min}$, Dumps Cloudflare R2 | Todo | 0 |

---

## 4. Plan Maestro de Ejecución por Shots (SHOT-01 → SHOT-24)

*(Ver detalle de gates y pre-requisitos en [`PLAN_DE_EJECUCION_SHOTS.md`](file:///c:/Users/alios/Documents/antigravity/vibrant-hertz/docs/PLAN_DE_EJECUCION_SHOTS.md))*

- **SHOT-01:** Monorepo + CI + Constitución aplicada.
- **SHOT-02:** DDL completo + `hardware_kits` + RLS + tests de aislamiento (Supabase CLI).
- **SHOT-03:** Engine núcleo (G1–G4 en 0.00).
- **SHOT-04:** Auth + tenancy + API skeleton DRF/JWT/OpenAPI + PostHog base + shell app ADOBE dual.
- **SHOT-05:** Canvas 2D mínimo (fijo + cotas).
- **SHOT-06:** Engine total (SLIDING, DOOR, AWNING, `hardware_kits` $\rightarrow$ G5–G12 en 0.00 + golden test).
- **SHOT-07:** Corte 1D BFD + Inspector R01–R14 (G7 puerta en 0.00 + test optimizador barras 5.8m).
- **SHOT-08:** Precios 5 modos + listas de costo + `price_audit_logs`.
- **SHOT-09:** Documentos WeasyPrint & openpyxl + Pantalla S19 (Pedidos proveedor).
- **SHOT-10:** Flujo proyectos + versiones + **catálogos manuales (S02, S12, S13, S15, S16)**.
- **SHOT-11:** Billing Flow + créditos + trial + deploy prod con alertas de uptime.
- **SHOT-12:** **Starter end-to-end + validación fundador (Sign-off G-Pro1).**
- **SHOT-13:** AI Gateway + router `ai_routes` + semáforo + auditoría IA (costos T6/T8/T9).
- **SHOT-14:** Compilador T6 + preguntas T4 + G sintéticos (4 fixtures 0.00).
- **SHOT-15:** OCR T1 + pantalla S27 split-screen.
- **SHOT-16:** Comandos T2/T3/T5 + modal diff + undo sagrado.
- **SHOT-17:** Plantillas PDF 3 slots + bloques protegidos.
- **SHOT-18:** Paddle global + landing legal en Framer (w8-9) $\rightarrow$ **Profesional a cobro**.
- **SHOT-19:** 3D R3F + link `/view/`.
- **SHOT-20:** Catálogo global + cola admin.
- **SHOT-21:** Certificado T8 doble ciego + DOC-08 + QR $\rightarrow$ **Business a cobro**.
- **SHOT-22:** Comparador T10 + bandeja email (SendGrid).
- **SHOT-23:** Autopilot Max T9 + Fin + PostHog.
- **SHOT-24:** Retazos QR + WhatsApp + **G10 monoriel** + PT-BR + Vista instalador (S26).

---

## 5. Los 10 Criterios Go/No-Go del Negocio

1. **Tolerancia Cero en Casos de Oro:** Casos G1–G12 (excepto G10) con discrepancia de $0.00\text{ mm}$ en CI.
2. **Aislamiento Multi-Tenant Certificado:** Cero filtraciones de precios o datos entre organizaciones.
3. **Idempotencia de Pagos:** Ningún webhook duplicado puede cobrar o acreditar doble saldo.
4. **Motor Inmune a Saldo Cero:** Agotar créditos de IA jamás bloquea el motor 2D ni la exportación de PDFs.
5. **Inmutabilidad Documental:** Todo PDF comercial emitido queda congelado con hash SHA-256 inmutable.
6. **Lenguaje Humano de Taller:** Cero excepciones no controladas o trazas crudas mostradas al usuario.
7. **Trazabilidad Integral:** Toda acción de IA en `ai_audit_logs` y todo cambio de precio en `price_audit_logs`.
8. **Términos Legales Publicados:** Landing Framer con pricing y disclaimer "humano aprueba" activo.
9. **Checkout Funcional:** Integración de pasarelas Flow y Paddle probada de extremo a extremo.
10. **Débito de Créditos Idempotente:** Reintento de webhook/red jamás duplica saldo ni créditos.



<!-- FIN DE PRD-00.md -->

---



<!-- INICIO DE PRD-01.md -->


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



<!-- FIN DE PRD-01.md -->

---



<!-- INICIO DE PRD-02.md -->


# PRD-02: MODELO DE DATOS, DDL Y POLÍTICAS DE AISLAMIENTO RLS (v1.1.2)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.1.2 (Congelada y Bloqueada tras Auditoría Final)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Fase:** 0 (Fundacional)  
**Bloquea a:** Todos los módulos del backend y frontend

---

## 1. Principios Rectores de la Base de Datos

1. **Aislamiento Multi-Tenant Absoluto:** Toda tabla de negocio posee la columna `org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE`.
2. **Row Level Security (RLS) Exhaustivo:** Ninguna consulta desde la capa de aplicación o Supabase Client puede ejecutarse sin la evaluación estricta de políticas RLS. Los catálogos globales (`is_global = TRUE`) son legibles por cualquier usuario autenticado de cualquier organización.
3. **Roles de Organización vs. Plataforma (H3 — Seguridad Reforzada):** `SUPERADMIN` es un rol de plataforma a nivel de sistema (`auth.jwt() -> 'app_metadata' ->> 'is_superadmin' = 'true'` — editable únicamente vía service_role / Admin API de Supabase, jamás desde `user_metadata` — o tabla `platform_admins` con consultas exclusivas del backend). **NO forma parte del enum `org_role`**, el cual modela exclusivamente los 4 roles internos del taller (`OWNER`, `ESTIMATOR`, `WORKSHOP_MANAGER`, `INSTALLER`).
4. **Tipado Numérico Exacto:** Prohibido el uso de `FLOAT` o `REAL`.
   - Dimensiones milimétricas: `NUMERIC(10, 2)` (rango hasta 99,999.99 mm).
   - Precios y montos monetarios: `NUMERIC(14, 2)` para moneda internacional/costos, `NUMERIC(14, 0)` para CLP en cotizaciones finales.
   - Factores, mermas y márgenes porcentuales: `NUMERIC(6, 4)`.
5. **Idempotencia Financiera y Auditoría (P1-1, C.1, C.2):** Tablas de pagos con restricciones de unicidad estricta (`payment_events(provider, event_id)` y `payments(provider_payment_id)`), auditoría previa de precios (`price_audit_logs`) y trazabilidad de IA (`ai_audit_logs`).

---

## 2. DDL Canónico Completo (PostgreSQL 16)

```sql
-- Extensiones requeridas
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- 1. TENANCY & AUTHENTICATION
-- ============================================================================

CREATE TYPE org_role AS ENUM ('OWNER', 'ESTIMATOR', 'WORKSHOP_MANAGER', 'INSTALLER');
CREATE TYPE subscription_tier AS ENUM ('TRIAL', 'STARTER', 'PRO', 'BUSINESS', 'BUSINESS_2X');
CREATE TYPE currency_code AS ENUM ('CLP', 'USD');

CREATE TABLE tenancy_organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    tax_id VARCHAR(50) NOT NULL, -- RUT en Chile (e.g. 76.123.456-7)
    country VARCHAR(2) NOT NULL DEFAULT 'CL',
    currency currency_code NOT NULL DEFAULT 'CLP',
    timezone VARCHAR(50) NOT NULL DEFAULT 'America/Santiago',
    subscription_tier subscription_tier NOT NULL DEFAULT 'TRIAL',
    subscription_active BOOLEAN NOT NULL DEFAULT TRUE,
    billing_cycle VARCHAR(10) NOT NULL DEFAULT 'annual' CHECK (billing_cycle IN ('monthly', 'annual')),
    founding_member BOOLEAN NOT NULL DEFAULT FALSE,
    trial_ends_at TIMESTAMPTZ,
    points_balance INT NOT NULL DEFAULT 500 CHECK (points_balance >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE tenancy_memberships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL, -- Enlaza con auth.users de Supabase
    role org_role NOT NULL DEFAULT 'ESTIMATOR',
    totp_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_org_user UNIQUE (org_id, user_id)
);

-- ============================================================================
-- 2. CATALOGS, PROFILES & HARDWARE KITS (Enmienda F1)
-- ============================================================================

CREATE TYPE material_type AS ENUM ('PVC', 'ALUMINIUM');
CREATE TYPE profile_role AS ENUM ('FRAME', 'SASH', 'MULLION_V', 'MULLION_H', 'INVERSOR', 'GLAZING_BEAD', 'COUPLER', 'ADDITIONAL');

CREATE TABLE profile_systems (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID REFERENCES tenancy_organizations(id) ON DELETE CASCADE, -- NULL si es catálogo global público
    name VARCHAR(150) NOT NULL,
    code VARCHAR(50) NOT NULL,
    depth_mm NUMERIC(10, 2) NOT NULL,
    material material_type NOT NULL DEFAULT 'PVC',
    chamber_count INT NOT NULL DEFAULT 3,
    
    -- Parámetros canónicos de sistema
    sash_overlap_mm NUMERIC(4, 2) NOT NULL DEFAULT 8.00,
    glass_clearance_white_mm NUMERIC(4, 2) NOT NULL DEFAULT 3.00, -- Demo 60 congela 5.00
    glass_clearance_foil_mm NUMERIC(4, 2) NOT NULL DEFAULT 5.00,
    pulley_height_mm NUMERIC(4, 2) NOT NULL DEFAULT 12.00,
    central_overlap_mm NUMERIC(4, 2) NOT NULL DEFAULT 35.00,
    sliding_lateral_clearance_mm NUMERIC(4, 2) NOT NULL DEFAULT 0.00,
    sliding_end_add_mm NUMERIC(4, 2) NOT NULL DEFAULT 6.00,
    corner_bracket_loss_mm NUMERIC(4, 2) NOT NULL DEFAULT 0.00,
    hook_depth_mm NUMERIC(4, 2) NOT NULL DEFAULT 0.00,
    door_threshold_mm NUMERIC(4, 2) NOT NULL DEFAULT 30.00,
    door_bottom_clearance_mm NUMERIC(4, 2) NOT NULL DEFAULT 20.00,
    rail_type VARCHAR(10) NOT NULL DEFAULT 'dual' CHECK (rail_type IN ('dual', 'mono')),
    
    is_global BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    version INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_org_system_code UNIQUE (org_id, code, version)
);

CREATE TABLE profile_articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    system_id UUID NOT NULL REFERENCES profile_systems(id) ON DELETE CASCADE,
    org_id UUID REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    sku VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role profile_role NOT NULL,
    face_width_mm NUMERIC(10, 2) NOT NULL,
    commercial_length_mm NUMERIC(10, 2) NOT NULL DEFAULT 6000.00,
    welding_loss_mm NUMERIC(10, 2) NOT NULL DEFAULT 6.00,
    reinforcement_sku VARCHAR(100),
    reinforcement_gap_mm NUMERIC(10, 2) NOT NULL DEFAULT 15.00,
    weight_kg_m NUMERIC(8, 4) NOT NULL DEFAULT 1.2000,
    steel_weight_kg_m NUMERIC(8, 4) NOT NULL DEFAULT 1.7000, -- Peso acero de refuerzo
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_system_sku UNIQUE (system_id, sku)
);

CREATE TABLE glazing_bead_matrix (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    system_id UUID NOT NULL REFERENCES profile_systems(id) ON DELETE CASCADE,
    org_id UUID REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    glass_thickness_mm NUMERIC(6, 2) NOT NULL,
    bead_article_id UUID NOT NULL REFERENCES profile_articles(id) ON DELETE RESTRICT,
    bead_width_mm NUMERIC(6, 2) NOT NULL,
    gasket_interior_mm NUMERIC(6, 2) NOT NULL DEFAULT 3.00,
    gasket_exterior_mm NUMERIC(6, 2) NOT NULL DEFAULT 3.00,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uk_system_glass_thickness UNIQUE (system_id, glass_thickness_mm)
);

CREATE TABLE hardware_kits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES tenancy_organizations(id) ON DELETE CASCADE, -- NULL si global
    system_id UUID REFERENCES profile_systems(id) ON DELETE CASCADE,
    sku VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    opening_type VARCHAR(30) NOT NULL,   -- 'TURN','TILT_TURN','SLIDING','AWNING','DOOR'
    min_leaf_width_mm NUMERIC(10,2) NOT NULL,
    max_leaf_width_mm NUMERIC(10,2) NOT NULL,
    min_leaf_height_mm NUMERIC(10,2) NOT NULL,
    max_leaf_height_mm NUMERIC(10,2) NOT NULL,
    max_leaf_weight_kg NUMERIC(6,2) NOT NULL,   -- alimenta Regla R01
    rail_type VARCHAR(10) NOT NULL DEFAULT 'dual',
    carriages_qty INT NOT NULL DEFAULT 2,        -- alimenta Regla R14
    stay_arms_qty INT NOT NULL DEFAULT 1,        -- alimenta Regla R13
    contents JSONB NOT NULL DEFAULT '[]',        -- [{sku, name, qty, unit}]
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_kit_system_sku UNIQUE (system_id, sku)
);

-- ============================================================================
-- 3. COST LISTS, PRICING & PRICE AUDIT LOGS (Enmienda C.1 & M3)
-- ============================================================================

CREATE TABLE cost_lists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    supplier_name VARCHAR(200) NOT NULL,
    description TEXT,
    currency currency_code NOT NULL DEFAULT 'CLP',
    valid_from DATE NOT NULL,
    valid_to DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE cost_list_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cost_list_id UUID NOT NULL REFERENCES cost_lists(id) ON DELETE CASCADE,
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    sku VARCHAR(100) NOT NULL,
    item_type VARCHAR(50) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    unit_cost NUMERIC(14, 4) NOT NULL CHECK (unit_cost >= 0),
    CONSTRAINT uk_cost_list_sku UNIQUE (cost_list_id, sku)
);

CREATE TABLE pricing_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    pricing_mode VARCHAR(50) NOT NULL DEFAULT 'COST_PLUS_MARGIN',
    default_margin_pct NUMERIC(6, 4) NOT NULL DEFAULT 0.3500,
    tax_rate_pct NUMERIC(6, 4) NOT NULL DEFAULT 0.1900,
    waste_factor_pct NUMERIC(6, 4) NOT NULL DEFAULT 0.0800,
    labor_rate_per_m2 NUMERIC(14, 2) NOT NULL DEFAULT 15000.00,
    installation_rate_per_m2 NUMERIC(14, 2) NOT NULL DEFAULT 12000.00,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_org_pricing_rules UNIQUE (org_id)
);

CREATE TABLE price_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    project_id UUID,
    entity VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    field VARCHAR(50) NOT NULL,
    old_value NUMERIC(14, 2),
    new_value NUMERIC(14, 2),
    actor_type VARCHAR(20) NOT NULL,
    actor_user_id UUID,
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 4. PROJECTS, POSITIONS & REVISIONS
-- ============================================================================

CREATE TYPE project_status AS ENUM ('DRAFT', 'QUOTED', 'APPROVED', 'IN_PRODUCTION', 'COMPLETED', 'CANCELLED');
CREATE TYPE inspector_status AS ENUM ('GREEN', 'YELLOW', 'RED');

CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    client_name VARCHAR(255) NOT NULL,
    client_rut VARCHAR(50),
    client_email VARCHAR(255),
    client_phone VARCHAR(50),
    delivery_address TEXT,
    status project_status NOT NULL DEFAULT 'DRAFT',
    total_cost_net NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    total_price_net NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    total_price_tax NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    total_price_gross NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    current_revision VARCHAR(10) NOT NULL DEFAULT 'REV-A',
    notes_commercial TEXT,
    notes_internal TEXT,
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_org_project_code UNIQUE (org_id, code)
);

CREATE TABLE project_positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    position_index INT NOT NULL,
    location_tag VARCHAR(100),
    typology VARCHAR(50) NOT NULL,
    width_mm NUMERIC(10, 2) NOT NULL CHECK (width_mm >= 250.00),
    height_mm NUMERIC(10, 2) NOT NULL CHECK (height_mm >= 250.00),
    quantity INT NOT NULL DEFAULT 1 CHECK (quantity >= 1),
    system_id UUID NOT NULL REFERENCES profile_systems(id) ON DELETE RESTRICT,
    color_interior VARCHAR(50) NOT NULL DEFAULT 'WHITE',
    color_exterior VARCHAR(50) NOT NULL DEFAULT 'WHITE',
    glass_spec VARCHAR(200) NOT NULL DEFAULT '4-12-4 Float Incoloro',
    parametric_tree JSONB NOT NULL,
    bom_snapshot JSONB NOT NULL,
    cost_net NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    price_net NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    discount_pct NUMERIC(6, 4) NOT NULL DEFAULT 0.0000,
    inspector_status inspector_status NOT NULL DEFAULT 'GREEN',
    inspector_findings JSONB NOT NULL DEFAULT '[]'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_project_position_idx UNIQUE (project_id, position_index)
);

CREATE TABLE project_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    revision_code VARCHAR(10) NOT NULL,
    snapshot_json JSONB NOT NULL,
    pdf_storage_path VARCHAR(500),
    emitted_by UUID NOT NULL,
    emitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_project_revision UNIQUE (project_id, revision_code)
);

-- ============================================================================
-- 5. ORDERS, OFFCUTS & AI AUDIT LOGS
-- ============================================================================

CREATE TYPE order_type AS ENUM ('WORKSHOP_OT', 'SUPPLIER_PROFILE_PO', 'SUPPLIER_GLASS_PO', 'SUPPLIER_HARDWARE_PO');
CREATE TYPE order_status AS ENUM ('DRAFT', 'SENT', 'PARTIALLY_RECEIVED', 'FULFILLED', 'CANCELLED');
CREATE TYPE offcut_status AS ENUM ('AVAILABLE', 'RESERVED', 'CONSUMED', 'DISCARDED');

CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE RESTRICT,
    order_type order_type NOT NULL,
    order_code VARCHAR(50) NOT NULL,
    status order_status NOT NULL DEFAULT 'DRAFT',
    supplier_name VARCHAR(200),
    payload_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_org_order_code UNIQUE (org_id, order_code)
);

CREATE TABLE offcut_inventory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    profile_article_id UUID NOT NULL REFERENCES profile_articles(id) ON DELETE RESTRICT,
    color VARCHAR(50) NOT NULL,
    length_mm NUMERIC(10, 2) NOT NULL CHECK (length_mm >= 500.00),
    rack_location VARCHAR(50),
    source_order_id UUID REFERENCES orders(id) ON DELETE SET NULL,
    reserved_order_id UUID REFERENCES orders(id) ON DELETE SET NULL,
    status offcut_status NOT NULL DEFAULT 'AVAILABLE',
    qr_code VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    consumed_at TIMESTAMPTZ,
    CONSTRAINT uk_org_offcut_qr UNIQUE (org_id, qr_code)
);

CREATE TABLE ai_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    model_used VARCHAR(100) NOT NULL,
    prompt_version VARCHAR(50) NOT NULL,
    retention_until TIMESTAMPTZ NOT NULL,
    input_payload JSONB NOT NULL,
    output_payload JSONB NOT NULL,
    points_debited INT NOT NULL DEFAULT 0,
    tokens_prompt INT NOT NULL DEFAULT 0,
    tokens_completion INT NOT NULL DEFAULT 0,
    latency_ms INT NOT NULL DEFAULT 0,
    state_hash_before VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 5-BIS. BILLING, PAYMENTS & CREDIT LEDGER (Enmienda 1 / P1-1)
-- ============================================================================

CREATE TABLE payment_customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    provider VARCHAR(30) NOT NULL CHECK (provider IN ('flow', 'paddle', 'mercadopago')),
    provider_customer_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_org_provider UNIQUE (org_id, provider)
);

CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    provider VARCHAR(30) NOT NULL,
    provider_subscription_id VARCHAR(100),
    plan_tier subscription_tier NOT NULL CHECK (plan_tier <> 'TRIAL'),
    billing_cycle VARCHAR(10) NOT NULL CHECK (billing_cycle IN ('monthly', 'annual')),
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'past_due', 'cancelled', 'trialing')),
    currency currency_code NOT NULL DEFAULT 'USD',
    amount NUMERIC(12, 2) NOT NULL,
    current_period_end TIMESTAMPTZ,
    founding_member BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_org_subscription UNIQUE (org_id)
);

CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    subscription_id UUID REFERENCES subscriptions(id) ON DELETE SET NULL,
    provider VARCHAR(30) NOT NULL,
    provider_payment_id VARCHAR(100) NOT NULL UNIQUE,
    amount NUMERIC(12, 2) NOT NULL,
    currency currency_code NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'succeeded', 'failed', 'refunded')),
    tax_doc_type VARCHAR(20),
    tax_doc_folio VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE payment_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(30) NOT NULL,
    event_id VARCHAR(150) NOT NULL,
    event_type VARCHAR(100),
    payload JSONB NOT NULL,
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_provider_event UNIQUE (provider, event_id)
);

CREATE TABLE credit_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    amount INT NOT NULL,
    balance_after INT NOT NULL CHECK (balance_after >= 0),
    action_type VARCHAR(50) NOT NULL,
    reference_id UUID,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ledger_org_created ON credit_ledger (org_id, created_at DESC);

-- ============================================================================
-- 6. POLÍTICAS RLS DE AISLAMIENTO MULTI-TENANT (P2-1 & F1)
-- ============================================================================

ALTER TABLE tenancy_organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenancy_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE profile_systems ENABLE ROW LEVEL SECURITY;
ALTER TABLE profile_articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE glazing_bead_matrix ENABLE ROW LEVEL SECURITY;
ALTER TABLE hardware_kits ENABLE ROW LEVEL SECURITY;
ALTER TABLE cost_lists ENABLE ROW LEVEL SECURITY;
ALTER TABLE cost_list_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE pricing_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE price_audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_positions ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE offcut_inventory ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE credit_ledger ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION current_user_org_ids()
RETURNS SETOF UUID AS $$
    SELECT org_id 
    FROM tenancy_memberships 
    WHERE user_id = auth.uid() AND is_active = TRUE;
$$ LANGUAGE SQL STABLE SECURITY DEFINER;

-- Tenancy & Memberships (Lectura de la propia organización para miembros activos)
CREATE POLICY tenancy_organizations_select ON tenancy_organizations
    FOR SELECT USING (id IN (SELECT current_user_org_ids()));

CREATE POLICY tenancy_memberships_select ON tenancy_memberships
    FOR SELECT USING (org_id IN (SELECT current_user_org_ids()));

-- Catálogos (Lectura: Propios O Globales; Escritura: Solo Propios)
CREATE POLICY profile_systems_select ON profile_systems
    FOR SELECT USING (is_global = TRUE OR org_id IN (SELECT current_user_org_ids()));

CREATE POLICY profile_systems_modify ON profile_systems
    FOR ALL USING (org_id IN (SELECT current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT current_user_org_ids()));

CREATE POLICY profile_articles_select ON profile_articles
    FOR SELECT USING (
        system_id IN (SELECT id FROM profile_systems WHERE is_global = TRUE)
        OR org_id IN (SELECT current_user_org_ids())
    );

CREATE POLICY profile_articles_modify ON profile_articles
    FOR ALL USING (org_id IN (SELECT current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT current_user_org_ids()));

CREATE POLICY glazing_bead_matrix_select ON glazing_bead_matrix
    FOR SELECT USING (
        system_id IN (SELECT id FROM profile_systems WHERE is_global = TRUE)
        OR org_id IN (SELECT current_user_org_ids())
    );

CREATE POLICY glazing_bead_matrix_modify ON glazing_bead_matrix
    FOR ALL USING (org_id IN (SELECT current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT current_user_org_ids()));

CREATE POLICY hardware_kits_select ON hardware_kits
    FOR SELECT USING (
        system_id IN (SELECT id FROM profile_systems WHERE is_global = TRUE)
        OR org_id IN (SELECT current_user_org_ids())
    );

CREATE POLICY hardware_kits_modify ON hardware_kits
    FOR ALL USING (org_id IN (SELECT current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT current_user_org_ids()));

-- Negocio y Proyectos
CREATE POLICY projects_isolation ON projects
    FOR ALL USING (org_id IN (SELECT current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT current_user_org_ids()));

CREATE POLICY positions_isolation ON project_positions
    FOR ALL USING (org_id IN (SELECT current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT current_user_org_ids()));

CREATE POLICY project_versions_isolation ON project_versions
    FOR ALL USING (org_id IN (SELECT current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT current_user_org_ids()));

CREATE POLICY orders_isolation ON orders
    FOR ALL USING (org_id IN (SELECT current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT current_user_org_ids()));

CREATE POLICY offcut_inventory_isolation ON offcut_inventory
    FOR ALL USING (org_id IN (SELECT current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT current_user_org_ids()));

CREATE POLICY price_audit_logs_isolation ON price_audit_logs
    FOR ALL USING (org_id IN (SELECT current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT current_user_org_ids()));

CREATE POLICY ai_audit_logs_isolation ON ai_audit_logs
    FOR ALL USING (org_id IN (SELECT current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT current_user_org_ids()));

-- Billing y Pagos
CREATE POLICY payment_customers_isolation ON payment_customers
    FOR ALL USING (org_id IN (SELECT current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT current_user_org_ids()));

CREATE POLICY subscriptions_isolation ON subscriptions
    FOR ALL USING (org_id IN (SELECT current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT current_user_org_ids()));

CREATE POLICY payments_isolation ON payments
    FOR ALL USING (org_id IN (SELECT current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT current_user_org_ids()));

CREATE POLICY credit_ledger_isolation ON credit_ledger
    FOR SELECT USING (org_id IN (SELECT current_user_org_ids()));

CREATE POLICY payment_events_service_role ON payment_events
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');
```



<!-- FIN DE PRD-02.md -->

---



<!-- INICIO DE PRD-03.md -->


# PRD-03: GESTIÓN DE TENANCY, AUTENTICACIÓN, FACTURACIÓN Y BILLETERA DE CRÉDITOS (v1.1.2)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.1.2 (Congelada y Bloqueada tras Auditoría Final)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Fase:** 0 (Fundacional)  
**Bloquea a:** PRD-05 a PRD-17

---

## 1. Arquitectura de Autenticación y Control de Acceso

Dekopen implementa una capa de autenticación delegada en **Supabase Auth** con mecanismos de inicio de sesión sin contraseña (Magic Link) y autenticación multifactor (MFA/TOTP) obligatoria para el rol `OWNER`.

```
+---------------+      1. SignIn OTP       +----------------+
|  Usuario      | -----------------------> | Supabase Auth  |
|  (Navegador)  | <----------------------- | (Magic Link)   |
|               |      2. Email con Link   +----------------+
|               |                                  |
|               |      3. Valida JWT               v
|               | -----------------------> +----------------+
|               | <----------------------- | Django API     |
+---------------+   {org_id, role, saldo}  | (/api/v1/auth) |
                                           +----------------+
```

---

## 2. Facturación y Pasarelas de Pago Multi-Región

- **Chile (CL):** **Flow.cl** (Suscripciones nativas con Webpay Plus, Servipag y Khipu). Moneda de cobro local CLP ajustada por tipo de cambio con buffer del 5% e IVA incluido.
- **Internacional (US/EU/Resto):** **Paddle** (Merchant of Record - MoR que gestiona automáticamente Sales Tax, VAT y facturación internacional sin carga impositiva para el taller). Moneda ancla oficial: **USD**.
- **LatAm Expansión (MX, CO, PE, AR):** MercadoPago (Fase 2+).

---

## 3. Planes de Suscripción Oficiales

| Parámetro | Trial | Starter | Profesional ⭐ | Business | Business 2x |
|---|---|---|---|---|---|
| **Mensual** | — | USD 39 | USD 69 | USD 129 | USD 149 |
| **Anual (billed annually)** | — | USD 35/mo | USD 59/mo | USD 99/mo | USD 129/mo |
| **Total anual** | — | USD 420 | USD 708 | USD 1.188 | USD 1.548 |
| **Usuarios Incluidos** | 1 | 2 | 3 | 5 | 5 |
| **Créditos IA / mes** | 500 (techo total trial) | 0 | 2.000 | 6.000 | 12.000 |
| **Motor 0.00 mm, 2D SVG, BOM, corte 1D, PDF/OT/Excel, pedido** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **OCR planos, compilador, comandos, plantillas PDF** | — | — | ✓ | ✓ | ✓ |
| **Certificado doble ciego (v1.5), Autopilot (v2), comparador, soporte prioritario** | — | — | — | ✓ | ✓ |
| **Diferenciador** | Prueba completa 7 días | El motor completo. Sin IA, por elección. | **MÁS POPULAR** | Todo el producto | Solo 2× créditos. Nada más. |

- **Trial:** 7 días sobre Profesional completo, sin tarjeta, techo duro de 500 créditos totales. Signup directo a Starter = 0 créditos. Al expirar el trial, downgrade automático a Starter (*el motor de cálculo nunca se bloquea*).
- **Usuario Extra:** USD 12/mes (USD 10/mes en ciclo anual), en todos los planes pagos.
- **Cláusula de Grandfathering:** Todo cambio futuro en los precios de lista de las suscripciones exige un aviso previo de 60 días a los clientes y garantiza el precio congelado por 12 meses para suscriptores activos.

---

## 4. Billetera y Consumo de Créditos de IA

### 4.1. Conversión Interna Privada y Saldo Cero
- **Conversión Interna Privada:** 200 créditos = USD 1 de costo API real ($1\text{ crédito} = \text{USD } 0.005$). Esta equivalencia es estrictamente privada y nunca visible en la UI.
- **Saldo Cero:** Al agotarse los créditos, las funciones de IA se pausan. **El motor de cálculo, diseñador 2D, cotizador manual, corte 1D y exportación de PDFs siguen 100% operativos** (*retención, no castigo*).

### 4.2. Packs de Recarga de Emergencia
| Pack | Precio | Créditos Incluidos |
|---|---|---|
| **Top-up 1.000** | USD 15 | 1.000 créditos |
| **Top-up 3.000** | USD 40 | 3.000 créditos |
| **Top-up 7.500** | USD 90 | 7.500 créditos |

### 4.3. Tabla de Consumo por Herramienta de IA

| Tool ID | Función | Operación Realizada | Costo en Créditos | Justificación de Costo API |
|---|---|---|---|---|
| `T1` | `extract_positions(file)` | OCR multimodal de plano/pliego y extracción de vanos | **10 créditos** por plano | Gemini Flash OCR multimodal |
| `T2` | `propose_window_command(text)` | Interpretación NLP de instrucción de diseño geométrico | **4 créditos** | Mutación paramétrica tipada |
| `T3` | `apply_pricing_command(mode,params)` | Cálculo y preview de ajuste comercial por comando | **3 créditos** | Diff comercial |
| `T4` | `missing_questions(ctx)` | Diagnóstico de variables faltantes para cotización | **2 créditos** | Consulta quirúrgica |
| `T5` | `explain_item(bom_line)` | Explicación técnica de taller de una partida de material | **1 crédito** | Micro-explicación |
| `T6` | `compile_catalog(file)` | Compilación completa de catálogo técnico desde PDF | **25 + 2 créditos / pág** *(mín 25)* | Extracción profunda de tablas y matrices |
| `T7` | `propose_compatibility_edge(a,b)` | Sugerencia de compatibilidad perfil-herraje | **2 créditos** | Grafo de herrajes |
| `T8` | `cross_verify_certificate(pos)` | Doble verificación cruzada con modelo alternativo | **50 créditos** | Doble modelo LLM independiente (~$0.25) |
| `T9` | `draft_autopilot(request)` | Generación integral de cotización borrador desasistida | **30 + 2 créditos / pág** | Pipeline completo multimodal + BOM |
| `T10` | `compare_plans(v1,v2)` | Análisis de diferencias entre dos versiones de plano | **8 créditos** | Comparativa visual de planos |
| `T11` | `margin_alert(ctx)` | Detección preventiva de márgenes comerciales negativos | **1 crédito** | Análisis financiero de riesgo |
| `T12` | `forecast_materials(h)` | Pronóstico de compra de barras según histórico | **5 créditos** | Modelo predictivo de compras |



<!-- FIN DE PRD-03.md -->

---



<!-- INICIO DE PRD-04.md -->


# PRD-04: DISEÑADOR 2D Y EDITOR PARAMÉTRICO EN CANVAS SVG (v1.1.1)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.1.1 (Congelada y Bloqueada)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Fase:** 1 (Núcleo)  
**Bloquea a:** PRD-06, PRD-07, PRD-10, PRD-12

---

## 1. Visión y Justificación Técnica del Canvas SVG

El diseñador 2D es la interfaz central de cotización y diseño técnico de Dekopen (Pantalla **S06**). Se implementa en **SVG puro interactivo dentro del Virtual DOM de React** (sin librerías intermedias como Konva, Fabric.js o D3.js).

---

## 2. Esquema del Árbol Paramétrico (`parametric_tree`) — Parche P1-4

Toda ventana se representa como un árbol jerárquico inmutable serializado en formato JSON:

```typescript
export type NodeType = 'ROOT' | 'SPLIT_H' | 'SPLIT_V' | 'BAY';

export type BayOpeningType = 
  | 'FIXED'                   // Paño Fijo
  | 'TURN_LEFT'               // Practicable Izquierda
  | 'TURN_RIGHT'              // Practicable Derecha
  | 'TILT_TURN_LEFT'          // Oscilobatiente Izquierda
  | 'TILT_TURN_RIGHT'         // Oscilobatiente Derecha
  | 'SLIDING_2L'              // Corredera 2 Hojas
  | 'SLIDING_3L'              // Corredera 3 Hojas (P1-4)
  | 'SLIDING_4L'              // Corredera 4 Hojas (P1-4)
  | 'AWNING'                  // Proyectante Superior
  | 'DOOR_ENTRY'              // Puerta de Entrada 1 Hoja
  | 'DOOR_DOUBLE';            // Puerta Doble con Inversor (P1-4)

export interface ParametricNode {
  id: string;
  type: NodeType;
  width_mm: number;
  height_mm: number;
  // Solo para nodos de tipo SPLIT_H o SPLIT_V
  split_offset_mm?: number;
  mullion_profile_sku?: string;
  children?: ParametricNode[];
  // Solo para nodos hoja de tipo BAY
  opening_type?: BayOpeningType;
  glass_article_sku?: string;
  hardware_set_sku?: string;
  handle_height_mm?: number;
}

export interface WindowDesignState {
  system_id: string;
  nominal_width_mm: number;
  nominal_height_mm: number;
  color_interior: string;
  color_exterior: string;
  root: ParametricNode;
}
```

---

## 3. Simbología y Gramática Visual Europea (DIN EN 12519)

El canvas SVG renderiza las líneas de apertura y dirección de herraje respetando la norma técnica internacional:

1. **Paño Fijo (`FIXED`):** Sin líneas diagonales de apertura. Fondo de cristal con sombreado sutil.
2. **Practicable Giro Interior (`TURN_LEFT` / `TURN_RIGHT`):** Dos líneas continuas trazadas desde las esquinas del lado de las bisagras que convergen en el centro de la manilla.
3. **Oscilobatiente (`TILT_TURN`):** Triángulo de giro lateral continuo + Triángulo de abatimiento superior en línea punteada (`stroke-dasharray="4 4"`).
4. **Corredera (`SLIDING_2L`, `SLIDING_3L`, `SLIDING_4L`):** Flechas horizontales vectoriales superpuestas indicando el sentido de traslación.
5. **Proyectante (`AWNING`):** Triángulo punteado desde las esquinas superiores que converge en el punto medio del perfil inferior.
6. **Puerta Doble (`DOOR_DOUBLE`):** Dos triángulos de giro opuestos con indicación de manilla en hoja activa y manilla pasiva / pasador en hoja secundaria.

---

## 4. Tabla de Atajos de Teclado (Shortcuts) — Parche P1-4

| Atajo | Acción | Contexto |
|---|---|---|
| `Cmd + Z` / `Ctrl + Z` | Deshacer última modificación paramétrica | Editor 2D |
| `Cmd + Shift + Z` / `Ctrl + Y` | Rehacer modificación | Editor 2D |
| `V` | Dividir el vano seleccionado con Poste Vertical | Vano seleccionado |
| `H` | Dividir el vano seleccionado con Travesaño Horizontal | Vano seleccionado |
| `1` | Convertir vano a **Paño Fijo** (`FIXED`) | Vano seleccionado |
| `2` | Convertir vano a **Practicable Giro Izq** (`TURN_LEFT`) | Vano seleccionado |
| `3` | Convertir vano a **Practicable Giro Der** (`TURN_RIGHT`) | Vano seleccionado |
| `4` | Convertir vano a **Oscilobatiente Izq** (`TILT_TURN_LEFT`) | Vano seleccionado |
| `5` | Convertir vano a **Oscilobatiente Der** (`TILT_TURN_RIGHT`) | Vano seleccionado |
| `6` | Convertir vano a **Corredera 2 Hojas** (`SLIDING_2L`) | Vano seleccionado |
| `7` | Convertir vano a **Proyectante** (`AWNING`) | Vano seleccionado |
| `8` | Convertir vano a **Corredera 3 Hojas** (`SLIDING_3L`) | Vano seleccionado |
| `9` | Convertir vano a **Corredera 4 Hojas** (`SLIDING_4L`) | Vano seleccionado |
| `0` | Convertir vano a **Puerta Doble con Inversor** (`DOOR_DOUBLE`) | Vano seleccionado |
| `Backspace` / `Delete` | Eliminar división o resetear vano a Fijo | Elemento seleccionado |
| `Escape` | Deseleccionar vano o cancelar acción actual | Global |



<!-- FIN DE PRD-04.md -->

---



<!-- INICIO DE PRD-05.md -->


# PRD-05: MOTOR DE PRECIOS, LISTAS DE COSTO Y RENTABILIDAD (v1.1.0)
**Estado:** Bloqueado / Congelado  
**Fase:** 1 (Núcleo)  
**Bloquea a:** PRD-06, PRD-09, PRD-10, PRD-15

---

## 1. Visión y Filosofía Comercial

El motor de precios de Dekopen (`/engine/pricing.py` y `apps.pricing`) garantiza que ninguna carpintería venda bajo costo por errores de cálculo o desactualización de insumos.

### Principios Fundamentales
1. **Separación Estricta Costo vs. Precio:** Los costos de compra al proveedor son confidenciales y solo visibles para los roles `OWNER` y `WORKSHOP_MANAGER`. Los cotizadores (`ESTIMATOR`) operan con precios de venta y márgenes autorizados.
2. **Buffer de Tipo de Cambio (FX Buffer 5%):** Los insumos cotizados en USD (perfiles importados, herrajes alemanes/turcos) se convierten a CLP utilizando el tipo de cambio observado más un buffer de seguridad del $5\%$ para absorber fluctuaciones cambiarias durante la vigencia de la oferta.
3. **Inmutabilidad por Versión:** Al emitir una cotización, los costos y precios se congelan en `project_versions`. La actualización de una lista de costos de un proveedor jamás altera cotizaciones históricas vigentes.

---

## 2. Los 5 Modos Canónicos de Fijación de Precios (§6.2)

```mermaid
graph TD
    BOM[BOM Calculado por /engine] --> ModeRouter{Modo de Fijación de Precio}
    ModeRouter --> M1[1. Cost Plus Margin - Costo Real + Margen]
    ModeRouter --> M2[2. Price Per M2 - Tarifa m² por Tipología]
    ModeRouter --> M3[3. Matrix Dimensional - Tabla Ancho x Alto]
    ModeRouter --> M4[4. Target Margin Project - Margen Global Objetivo]
    ModeRouter --> M5[5. Commercial List - Lista Oficial + Descuentos]
```

---

### Modo 1: Costo Real Más Margen (`COST_PLUS_MARGIN`) [Modo Recomendado por Defecto]
Es el cálculo más preciso. Desglosa cada centavo de material, merma, mano de obra e instalación:

$$\text{Costo Materiales Base} = \sum (\text{Metros Perfil} \times \text{Costo/m}) + \sum (\text{m}^2 \text{Vidrio} \times \text{Costo/m}^2) + \sum (\text{Kits Herrajes}) + \sum (\text{Accesorios})$$

$$\text{Costo Materiales con Merma} = \text{Costo Materiales Base} \times (1 + \text{waste\_factor\_pct})$$
*Donde $\text{waste\_factor\_pct} = 0.08$ ($8\%$ merma promedio de taller).*

$$\text{Costo Mano de Obra (Taller)} = \text{Área m}^2 \times \text{labor\_rate\_per\_m2}$$
$$\text{Costo Instalación (Faena)} = \text{Área m}^2 \times \text{installation\_rate\_per\_m2}$$

$$\text{Costo Directo Total} = \text{Costo Materiales con Merma} + \text{Costo Mano de Obra} + \text{Costo Instalación}$$

$$\text{Precio Venta Neto} = \frac{\text{Costo Directo Total}}{1 - \text{default\_margin\_pct}}$$
*Ejemplo:* Con costo directo de $\$100.000\text{ CLP}$ y margen del $35\%$ ($0.35$):
$$\text{Precio Neto} = \frac{100000}{1 - 0.35} = \frac{100000}{0.65} = \$153.846\text{ CLP}$$
$$\text{Margen Bruto Real Obtenido} = \frac{153846 - 100000}{153846} = 35.00\%$$

---

### Modo 2: Precio por Metro Cuadrado por Tipología (`PRICE_PER_M2_BY_TYPOLOGY`)
Utilizado para cotizaciones rápidas preliminares basadas en valores históricos de taller:
$$\text{Precio Base} = \text{Área m}^2 \times \text{Tarifa Base Tipología}$$
- Paño Fijo: $\$65.000\text{ CLP/m}^2$
- Practicable 1 Hoja: $\$110.000\text{ CLP/m}^2$
- Oscilobatiente: $\$135.000\text{ CLP/m}^2$
- Corredera 2 Hojas: $\$95.000\text{ CLP/m}^2$
- Puerta de Entrada: $\$180.000\text{ CLP/m}^2$

**Recargos por Opciones:**
- Foliado Color Madera / Antracita: $+25\%$ sobre el precio base de carpintería.
- Vidrio Especial Acústico / Laminado: $+(\text{Diferencial Costo Vidrio} \times 1.40)$.

---

### Modo 3: Matriz Dimensional Tabulada (`FIXED_PRICE_MATRIX_DIMENSIONAL`)
Matriz bidimensional de precios precalculados para medidas estándar (utilizada por fabricantes en serie):
- Filas: Alturas de $600\text{ mm}$ a $2400\text{ mm}$ (pasos de $200\text{ mm}$).
- Columnas: Anchos de $600\text{ mm}$ a $2400\text{ mm}$ (pasos de $200\text{ mm}$).
- Interpolación bilineal automática para medidas intermedias no tabuladas.

---

### Modo 4: Margen Global Objetivo de Proyecto (`TARGET_GROSS_MARGIN_PROJECT`)
Permite al Propietario fijar un margen consolidado para una licitación o constructora completa (e.g. $42\%$ neto). El sistema distribuye automáticamente los precios de cada posición ponderando su complejidad y consumo de insumos.

---

### Modo 5: Lista Comercial con Escala de Descuentos (`COMMERCIAL_LIST_WITH_DISCOUNTS`)
Lista de precios de catálogo público con matriz de descuentos por segmento de cliente:
- Particular / Consumidor Final: $0\%$ descuento.
- Arquitecto / Diseñador Frecuente: $8\%$ a $12\%$ descuento.
- Empresa Constructora (Volumen $> 50\text{ ventanas}$): $18\%$ a $25\%$ descuento.

---

## 3. Listas de Costo de Proveedores y Vigencias

1. **Campos Temporales:** Las listas de costo poseen `valid_from` (fecha inicio obligatoria) y `valid_to` (fecha fin opcional).
2. **Resolución Automática:** Al crear o duplicar una posición, el motor busca la lista de costo activa cuya vigencia cubra la fecha actual del sistema.
3. **Importación Rápida desde Excel:** Soporte para importar archivos `.xlsx` de proveedores (Aluplast, Rehau, VEKA, Roto, Winkhaus, Vorne) mapeando columnas SKU, Descripción, Unidad y Precio Unitario.

---

## 4. Gobernanza de Descuentos y Permisos Comerciales

| Rango de Descuento | Rol Requerido para Aplicar | Comportamiento del Sistema |
|---|---|---|
| **$0\% \le \text{Desc} \le 10\%$** | `ESTIMATOR`, `OWNER` | Aplicación instantánea en la cotización. |
| **$10\% < \text{Desc} \le 20\%$** | `OWNER` (o `ESTIMATOR` con aprobación) | La cotización queda en estado `PENDING_OWNER_APPROVAL`. El Propietario recibe alerta en dashboard. |
| **$\text{Desc} > 20\%$** | Exclusivo `OWNER` | Requiere confirmación con advertencia de margen crítico. |
| **Margen Negativo ($\text{Precio} < \text{Costo}$)** | **PROHIBIDO** | El sistema bloquea el guardado con alerta de inspector comercial: *"Pérdida detectada en posición"*. |



<!-- FIN DE PRD-05.md -->

---



<!-- INICIO DE PRD-06.md -->


# PRD-06: GENERACIÓN DE DOCUMENTOS DE SALIDA (PDF, EXCEL, OT Y CORTE 1D) (v1.1.0)
**Estado:** Bloqueado / Congelado  
**Fase:** 1 (Núcleo)  
**Bloquea a:** PRD-11, PRD-14, PRD-15

---

## 1. Misión y Principio de Integridad Documental

Toda la documentación emitida por Dekopen se deriva estrictamente del cálculo determinista de `/engine`. 

### Regla del Hash de Integridad BOM
Antes de generar cualquier documento (comercial, de taller o de compras), el sistema calcula el hash `SHA-256` del snapshot JSON del proyecto y su BOM:
$$\text{BOM\_HASH} = \text{SHA256}(\text{project\_id} + \text{revision} + \text{positions\_json} + \text{bom\_json})$$
Este hash se incrusta como código de verificación en el pie de página de todos los documentos emitidos. Si el hash no coincide exactamente entre la cotización del cliente, la OT del taller y la orden de compra de vidrios, el documento es rechazado automáticamente por no coincidencia de versión.

---

## 2. Inventario de Documentos del Sistema

| ID | Documento | Formato / Motor | Destinatario | Contenido Clave |
|---|---|---|---|---|
| **DOC-01** | **Cotización Comercial Formal** | PDF (WeasyPrint) | Cliente Final / Arquitecto | Membrete de empresa, renders vectoriales 2D (SVG), desglose de vanos, especificación de vidrios y colores, totales neto/IVA/bruto, condiciones de pago y validez de oferta. |
| **DOC-02** | **Planilla de Pedido de Vidrios** | Excel `.xlsx` (openpyxl) | Fábrica de Termopaneles / Vidriería | Pestaña estandarizada con vanos, composición exacta, anchos, altos, cantidades, m² totales, cantos pulidos y etiquetas de ubicación. |
| **DOC-03** | **Orden de Trabajo de Taller (OT)** | PDF (WeasyPrint) | Jefe de Taller / Operarios | Planos técnicos acotados con cotas de corte exterior, medidas de refuerzo de acero, orificios de desagüe, altura de manillas y matriz de ensamble. |
| **DOC-04** | **Pedido de Barras y Perfiles** | PDF + Excel | Distribuidor de Perfilería | Consolidado de barras comerciales de $6.00\text{ m}$ por SKU y color, barras de acero galvanizado y accesorios. |
| **DOC-05** | **Hoja de Optimización de Corte 1D** | PDF (WeasyPrint) | Operario de Tronzadora / Sierra | Secuencia de corte barra por barra, IDs de piezas, longitudes exactas con pérdida de fusión, ángulos (45°/90°) y retazos resultantes. |
| **DOC-06** | **Checklist de Calidad y Control Final** | PDF (WeasyPrint) | Control de Calidad en Taller | Hoja de verificación física: escuadra de diagonales ($\le 1.0\text{ mm}$), estanqueidad de burletes, desagües destapados, calibración de herraje. |
| **DOC-07** | **Informe Ejecutivo de Costos y Margen** | PDF (Solo Propietario) | Dueño de Empresa / Gerencia | Desglose confidencial de costo de materiales, mano de obra, mermas reales, margen bruto por posición y rentabilidad consolidada. |

---

## 3. Especificación Técnica de WeasyPrint (HTML/CSS Pautado)

Los PDFs se compilan renderizando plantillas HTML con estilos CSS pautados compatibles con la especificación W3C Paged Media:

```css
@page {
  size: letter portrait;
  margin: 15mm 12mm 20mm 12mm;
  @top-left {
    content: "Dekopen ERP • Sistema de Fabricación";
    font-family: 'Inter', sans-serif;
    font-size: 8pt;
    color: #64748b;
  }
  @top-right {
    content: "Proyecto: " attr(data-project-code);
    font-family: 'Inter', sans-serif;
    font-size: 8pt;
    font-weight: bold;
    color: #1e293b;
  }
  @bottom-left {
    content: "Verificación de Integridad: " attr(data-bom-hash);
    font-family: monospace;
    font-size: 7pt;
    color: #94a3b8;
  }
  @bottom-right {
    content: "Página " counter(page) " de " counter(pages);
    font-family: 'Inter', sans-serif;
    font-size: 8pt;
    color: #64748b;
  }
}

.avoid-break {
  page-break-inside: avoid;
}
```

---

## 4. Estructura de la Planilla Excel de Vidrios (`DOC-02` - openpyxl)

El archivo `.xlsx` generado para la vidriería cumple estrictamente con el formato estándar de la industria:

```python
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

def generate_glass_order_excel(project_data, glasses_list) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Pedido Vidrios"
    
    # Encabezado Corporativo
    ws.merge_cells('A1:H1')
    ws['A1'] = f"PEDIDO DE CRISTALES / TERMOPANELES — {project_data['code']}"
    ws['A1'].font = Font(name='Arial', size=14, bold=True, color='FFFFFF')
    ws['A1'].fill = PatternFill(start_color='1E3A8A', end_color='1E3A8A', fill_type='solid')
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    
    # Columnas Técnicas
    headers = [
        "Ítem", "Posición", "Vano", "Composición Vidrio", 
        "Ancho (mm)", "Alto (mm)", "Cantidad", "Área Unitaria (m²)", "Área Total (m²)"
    ]
    ws.append(headers)
    
    for row_idx, g in enumerate(glasses_list, start=3):
        ws.append([
            row_idx - 2,
            g['position_index'],
            g['bay_index'],
            g['composition'],
            float(g['width_mm']),
            float(g['height_mm']),
            g['quantity'],
            float(g['area_m2']),
            f"=G{row_idx}*H{row_idx}" # Fórmula Excel nativa
        ])
    
    # Fila de Totales
    last_row = len(glasses_list) + 2
    ws.append(["TOTALES", "", "", "", "", "", f"=SUM(G3:G{last_row})", "", f"=SUM(I3:I{last_row})"])
    return save_virtual_workbook(wb)
```

---

## 5. Hoja de Optimización de Corte 1D (`DOC-05`)

Para cada tipo de perfil (Marco, Hoja, Travesaño, Junquillo), la hoja de corte muestra el mapa gráfico y numérico de utilización:

```
================================================================================
PERFIL: MARCO PRINCIPAL 60mm (SKU: PF-DEMO-60-BL) | BARRA: 6000 mm | COLOR: BLANCO
TOTAL BARRAS REQUERIDAS: 4 BARRAS | APROVECHAMIENTO: 94.2% | MERMA: 5.8%
================================================================================
BARRA #1: [Despunte: 15mm] 
  ├── [Pos 1 - Marco Inf]  1006 mm  (45°/45°) -> Refuerzo: 970 mm
  ├── [Pos 1 - Marco Sup]  1006 mm  (45°/45°) -> Refuerzo: 970 mm
  ├── [Pos 1 - Marco Izq]  1006 mm  (45°/45°) -> Refuerzo: 970 mm
  ├── [Pos 1 - Marco Der]  1006 mm  (45°/45°) -> Refuerzo: 970 mm
  ├── [Pos 2 - Marco Inf]   806 mm  (45°/45°) -> Refuerzo: 770 mm
  ├── [Pos 2 - Marco Sup]   806 mm  (45°/45°) -> Refuerzo: 770 mm
  └── [Retazo Sobrante: 320 mm] (Kerf acumulado: 24mm | Despunte fin: 15mm)
--------------------------------------------------------------------------------
```

---

## 6. Almacenamiento y Seguridad de Archivos

1. **Bucket:** Supabase Storage (`bucket: documents`).
2. **Ruta:** `org_{org_id}/projects/{project_id}/{revision_code}/{document_type}_{hash}.pdf`.
3. **Acceso:** Exclusivamente a través de URLs firmadas con expiración máxima de $3600\text{ segundos}$ ($1\text{ hora}$) generadas por el backend tras validar la sesión del usuario.



<!-- FIN DE PRD-06.md -->

---



<!-- INICIO DE PRD-07.md -->


# PRD-07: INSPECTOR TÉCNICO DE TALLER Y REGLAS DE FABRICABILIDAD (v1.1)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.1 (Congelada y Bloqueada)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Fase:** 1 (Núcleo)  
**Bloquea a:** PRD-06, PRD-08, PRD-14

---

## 1. Misión y Filosofía del Inspector

El Inspector Técnico de Dekopen (`/engine/inspector.py` y Pantalla **S07**) actúa como el "Jefe de Taller Digital". Su objetivo es detectar incompatibilidades físicas, excesos de peso y fallas normativas en tiempo real durante el diseño 2D, antes de cortar un solo perfil.

### Regla Constitucional de Comunicación
Ningún hallazgo del inspector puede presentarse como un código de error crudo o traza técnica. Todo hallazgo debe expresarse en lenguaje claro de taller de PVC, indicando:
1. **Qué ocurre** (Diagnóstico claro).
2. **Por qué es un problema** (Riesgo físico: descuelgue de hoja, filtración, rotura de vidrio).
3. **Cómo solucionarlo en 1 Clic** (Acción correctiva automatizada).

---

## 2. Las 14 Reglas Canónicas de Validación (§6.6 + Enmienda B.4)

Todas las constantes son configurables y overridibles por sistema de perfiles en base de datos.

| # | Regla | Condición Matemática de Fallo | Severidad | Acción Correctiva en 1 Clic |
|---|---|---|---|---|
| **R01** | **Peso Máximo de Hoja** | $P_{total\_sash} = P_{pvc} + P_{acero} + P_{vidrio} > P_{max\_herraje}$ *(e.g. $> 100\text{ kg}$ en herraje estándar)* | 🔴 **ROJO** | *"Actualizar a kit de bisagras reforzadas 130 kg"* o *"Dividir vano en 2 hojas"*. |
| **R02** | **Relación de Aspecto (Proporción)** | $H_{sash} / W_{sash} > 2.5$ O $H_{sash} / W_{sash} < 0.4$ | 🟡 **AMARILLO** | *"Ajustar división a proporción recomendada 1:1.5"*. |
| **R03** | **Dimensiones Mínimas / Máximas** | $W_{sash} < 350\text{ mm}$ O $W_{sash} > 1600\text{ mm}$ O $H_{sash} > 2400\text{ mm}$ | 🔴 **ROJO** | *"Redimensionar vano al límite permitido por la serie"*. |
| **R04** | **Área vs. Espesor de Vidrio** | Monolítico 4mm: Área $> 1.80\text{ m}^2$ / DVH 4-12-4: Área $> 2.60\text{ m}^2$ | 🔴 **ROJO** | *"Aumentar cristal a 6 mm templado o termopanel 6-12-6"*. |
| **R05** | **Inercia Eólica en Travesaños (NCh 432)** | Momento de inercia del refuerzo $I_x < I_{req}$ para luz $> 1800\text{ mm}$ | 🔴 **ROJO** | *"Cambiar a refuerzo de acero pesado 2.0 mm (SKU: RF-HEAVY)"*. |
| **R06** | **Matriz Junquillo–Vidrio** | $\text{Espesor Vidrio} \notin \text{glazing\_bead\_matrix}(\text{system\_id})$ | 🔴 **ROJO** | *"Seleccionar espesor estándar (20 mm o 24 mm) disponible en catálogo"*. |
| **R07** | **Desagües y Descompresión** | Ancho vano $> 800\text{ mm}$ requiere $\ge 3$ orificios de desagüe inferiores | 🟡 **AMARILLO** | *"Añadir orificio de desagüe central automáticamente"*. |
| **R08** | **Espaciado de Cerraderos Perimetrales** | Distancia entre puntos de cierre consecutivos $> 800\text{ mm}$ | 🟡 **AMARILLO** | *"Añadir reenvío de esquina con punto de cierre adicional"*. |
| **R09** | **Junta de Dilatación Térmica** | Ancho continuo $> 4000\text{ mm}$ en blanco ($> 3000\text{ mm}$ foliado) sin acople | 🔴 **ROJO** | *"Insertar perfil de acople de dilatación con junta elástica"*. |
| **R10** | **Tolerancia Diagonal de Marco** | Diferencia teórica $|D_1 - D_2| > 1.50\text{ mm}$ | 🔴 **ROJO** | *"Recalcular escuadra ortogonal de marco"*. |
| **R11** | **Holgura Perimetral de Cámara** | Holgura entre hoja y marco fuera del rango $12.0\text{ mm} \pm 1.5\text{ mm}$ | 🔴 **ROJO** | *"Restablecer solape nominal de 8.0 mm"*. |
| **R12** | **Inercia en Corredera 3 Hojas** | Corredera 3 hojas con vano $> 4500\text{ mm}$ exige refuerzo con $I_x \ge 45\text{ cm}^4$ | 🔴 **ROJO** | *"Cambiar a refuerzo pesado (SKU RF-HEAVY)"*. |
| **R13** | **Proyectante de Gran Altura** | Proyectante con $H > 1200\text{ mm}$ exige compás doble | 🟡 **AMARILLO** | *"Añadir segundo compás"*. |
| **R14** | **Carga de Carros Monoriel** | Corredera `rail_type='mono'` con hoja $> 150\text{ kg}$ exige 4 carros de carga ($\ge 80\text{ kg/rueda}$) | 🔴 **ROJO** | *"Configurar kit monoriel cuádruple"*. |

---

## 3. Comportamiento del Semáforo y Bloqueo de Producción

1. **Estado VERDE (Aprobado):** Cero infracciones. Habilita botón *"Aprobar para Taller"*.
2. **Estado AMARILLO (Advertencia de Taller):** Alerta no estructural (e.g. compás doble sugerido). Permite cotizar y deja constancia en la OT.
3. **Estado ROJO (Bloqueo Crítico P0):** Infracción de seguridad o ensamble. Bloquea físicamente la emisión de la orden de producción.



<!-- FIN DE PRD-07.md -->

---



<!-- INICIO DE PRD-08.md -->


# PRD-08: COMPILADOR ASISTIDO DE CATÁLOGOS TÉCNICOS (v1.1.1)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.1.1 (Congelada y Bloqueada)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Fase:** 2 (Inteligencia de Catálogo)  
**Bloquea a:** PRD-09, PRD-10, PRD-13

---

## 1. Misión y Pipeline de Ingestión

El Compilador de Catálogos (Tool **T6** y Pantalla **S14**) permite a una carpintería cargar el catálogo técnico en PDF o planilla Excel de cualquier fabricante de perfiles de PVC (Aluplast, Rehau, VEKA, Kömmerling, Deceuninck, Proline, etc.) y transformarlo en un sistema paramétrico operable en menos de 24 horas.

*Costo de consumo:* **25 + 2 créditos / página** (mínimo 25 créditos) según el tamaño del PDF (Parche P1-2).

```
[ PDF / Excel ] ---> [ OCR Multimodal Gemini ] ---> [ Staging en DB ]
                           (Tool T6)               (profile_systems_draft)
                                                            |
[ Publicación v1 ] <--- [ Verif. /engine ] <--- [ Preguntas Quirúrgicas ]
                             (G-Cases)                    (Tool T4)
```

---

## 2. Parámetros Críticos Extraídos y Semáforo Unificado (Enmienda 3 M1)

El compilador extrae obligatoriamente los siguientes parámetros de sistema para alimentar `/engine`:
- `depth_mm`, `chamber_count`, `frame_face_width_mm`, `sash_face_width_mm`, `mullion_face_width_mm`, `rebate_depth_mm`.
- `welding_loss_per_corner` ($3.00\text{ mm}$ default), `sash_overlap_mm` ($8.00\text{ mm}$ default).
- `glass_clearance_white_mm` ($3.00\text{ mm}$ default, $5.00\text{ mm}$ en Demo 60), `glass_clearance_foil_mm` ($5.00\text{ mm}$).
- **Parámetros Críticos Adicionales (M1):** `rail_type` (`'dual'` | `'mono'`), `pulley_height_mm` ($12.00\text{ mm}$ default), `central_overlap_mm` ($35.00\text{ mm}$ default), `door_threshold_mm` ($30.00\text{ mm}$), `door_bottom_clearance_mm` ($20.00\text{ mm}$), `sliding_lateral_clearance_mm` ($0.00\text{ mm}$).
- Matriz junquillo-vidrio completa (`glazing_bead_matrix`).

### Semáforo de Confianza
- **Verde ($\ge 90\%$):** Extraído directamente de una tabla técnica o plano acotado con cota explícita.
- **Amarillo ($70\% - 89\%$):** Inferido por proximidad visual o cálculo geométrico indirecto. Requiere confirmación visual.
- **Rojo ($< 70\%$ o Faltante):** No encontrado en el documento. Dispara pregunta quirúrgica (Tool T4).

---

## 3. Fixtures Verificados de Compilador (Enmienda B.6)

El compilador cuenta con 4 suites de fixtures reales congeladas para tests de regresión:

1. **VEKA Softline 70:** Profundidad $70.00\text{ mm}$ · 5 cámaras · Vidrio máx $42\text{ mm}$ · Soldadura $3.0\text{ mm}$ · Solape $8\text{ mm}$ · Clase A.
2. **Aluplast Ideal 4000:** Profundidad $70.00\text{ mm}$ · Vidrio máx $48\text{ mm}$ · Soldadura $3.0\text{ mm}$.
3. **Rehau Euro-Design 70:** Profundidad $70.00\text{ mm}$ · $U_w = 0.8\text{ W/m}^2\text{K}$.
4. **Proline Pro6004 (Plantilla PRIVADA):** Profundidad $60.00\text{ mm}$ · 3 cámaras · Soldadura $2.5\text{ mm}$ · Barra $5800.00\text{ mm}$.

> [!NOTE]
> [PENDIENTE-DECISIÓN: ficha v1 completa pre-F2 con standard_ref, doble QC dimensional+fusión y sanity check peso/densidad antes de abrir compilar libre a usuarios en Fase 2].



<!-- FIN DE PRD-08.md -->

---



<!-- INICIO DE PRD-09.md -->


# PRD-09: INTÉRPRETE MULTIMODAL DE PLANOS Y CUADROS DE VANOS (v1.1.1)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.1.1 (Congelada y Bloqueada)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Fase:** 2 (Inteligencia Operativa)  
**Bloquea a:** PRD-10, PRD-15, PRD-17

---

## 1. Misión y Flujo de Procesamiento

El Intérprete de Planos (Tool **T1** `extract_positions` y Pantalla **S27** `/ai/extract-positions`, roles: `OWNER`, `ESTIMATOR`) permite a los cotizadores subir planos de arquitectura en PDF, imágenes de cuadros de vanos o fotos de croquis de taller y convertirlos en proyectos estructurados con múltiples posiciones en menos de 3 minutos.

---

## 2. Esquema JSON de Salida y Semáforo Unificado (Enmienda C.3)

Cada dato extraído por el modelo multimodal recibe un índice de confianza normalizado:
- **Verde ($\ge 90\%$):** Coincidencia visual y textual nítida.
- **Amarillo ($70\% - 89\%$):** Tipografía ambigua, manuscrito o inferencia por escala.
- **Rojo ($< 70\%$):** Cota faltante o tipología incierta (requiere corrección obligatoria antes de importar).

```typescript
export interface ExtractedPositionCandidate {
  tag: { value: string; confidence: number };
  width_mm: { value: number; confidence: number };
  height_mm: { value: number; confidence: number };
  quantity: { value: number; confidence: number };
  typology: { value: string; confidence: number };
  glass_spec: { value: string; confidence: number };
  bounding_box: { page: number; x: number; y: number; w: number; h: number };
}
```

---

## 3. Normalización de Unidades
- Valores $\le 10.00$ (e.g. $1.50 \times 1.20$) $\rightarrow$ Multiplica por $1000 \rightarrow 1500 \times 1200\text{ mm}$.
- Valores en rango $[25.0, 500.0]$ (e.g. $150 \times 120$) $\rightarrow$ Normaliza a $1500 \times 1200\text{ mm}$.



<!-- FIN DE PRD-09.md -->

---



<!-- INICIO DE PRD-10.md -->


# PRD-10: INTERFAZ DE COMANDOS DE DISEÑO Y PRECIO EN LENGUAJE NATURAL (v1.1.0)
**Estado:** Bloqueado / Congelado  
**Fase:** 2 (Inteligencia Operativa)  
**Bloquea a:** PRD-15

---

## 1. Misión y Filosofía de los Comandos

La interfaz de comandos (Tools **T2**, **T3** y Pantalla **S21**) permite a los carpinteros y cotizadores interactuar con el sistema mediante lenguaje natural conversacional ("Divide la ventana al medio y pon la derecha oscilobatiente", "Aplica 5% de descuento por volumen").

### Las Tres Leyes de los Comandos de IA
1. **La IA muta parámetros, el motor calcula:** El LLM interpreta la intención del usuario y emite un diff estructurado de parámetros (`parametric_tree_diff` o `pricing_diff`). El LLM **JAMÁS** calcula o escribe números de corte o precios finales directamente.
2. **Preview Obligatorio Antes/Después:** Ninguna mutación se aplica a ciegas. El usuario siempre visualiza una vista previa gráfica y numérica con los deltas de costo, precio y estado del inspector antes de confirmar.
3. **Deshacer Sagrado (Undo Transaccional):** Toda acción ejecutada por un comando de IA se registra en el stack de deshacer con su snapshot previo íntegro, permitiendo revertir la operación con `Cmd + Z` o mediante un botón visible en la UI.

---

## 2. Tipos de Comandos y Esquemas de Herramientas

```mermaid
graph TD
    UserPrompt[Instrucción en Lenguaje Natural] --> Classifier{Clasificador de Intención}
    Classifier -->|Modificación Geométrica| T2[Tool T2: propose_window_command]
    Classifier -->|Ajuste Comercial| T3[Tool T3: apply_pricing_command]
    Classifier -->|Consulta Técnica| T5[Tool T5: explain_item]
    
    T2 --> DiffGenerator[Generador de Diff Paramétrico]
    T3 --> PricingDiff[Generador de Diff de Precios]
    
    DiffGenerator --> EngineCalc[/engine: Cálculo Determinista]
    PricingDiff --> EngineCalc
    
    EngineCalc --> PreviewModal[Modal de Vista Previa Antes/Después]
    PreviewModal -->|Aprobación Humana| ApplyState[Aplicación de Estado + Audit Log]
```

---

### 2.1. Herramienta T2: `propose_window_command` (Diseño Geométrico)
- **Costo:** 4 puntos.
- **Entrada:**
  ```json
  {
    "current_tree": { ... },
    "command_text": "Divide verticalmente al centro y pon la hoja derecha oscilobatiente con manilla a 400mm"
  }
  ```
- **Salida Tipada:**
  ```json
  {
    "mutation_type": "SPLIT_NODE",
    "target_node_id": "root",
    "operations": [
      {
        "op": "SPLIT_V",
        "split_ratio": 0.5,
        "children": [
          { "type": "BAY", "opening_type": "FIXED" },
          { "type": "BAY", "opening_type": "TILT_TURN_RIGHT", "handle_height_mm": 400 }
        ]
      }
    ],
    "explanation_es": "Se dividió el vano en 2 partes iguales: Paño fijo a la izquierda y Oscilobatiente derecha con manilla a 400 mm."
  }
  ```

---

### 2.2. Herramienta T3: `apply_pricing_command` (Ajustes Comerciales)
- **Costo:** 3 puntos.
- **Entrada:**
  ```json
  {
    "project_id": "proj_123",
    "command_text": "Aplica un margen del 38% para constructora y descuenta 3% en las ventanas de dormitorios"
  }
  ```
- **Salida Tipada:**
  ```json
  {
    "target_mode": "COST_PLUS_MARGIN",
    "global_margin_pct": 0.3800,
    "position_overrides": [
      { "location_tag_pattern": "Dormitorio*", "discount_pct": 0.0300 }
    ],
    "delta_summary": {
      "previous_total_net": 3450000,
      "new_total_net": 3620000,
      "net_difference": 170000
    }
  }
  ```

---

## 3. Experiencia de Usuario: Modal de Vista Previa (Preview & Diff)

Al procesar cualquier comando, la UI despliega un panel flotante de confirmación con 3 secciones:
1. **Comparativa Visual 2D (Side-by-Side):**
   - Panel Izquierdo: Estado actual (SVG previo).
   - Panel Derecho: Estado propuesto con resaltado de modificaciones en color verde.
2. **Impacto Técnico y Comercial:**
   - Variación de Costo de Materiales ($\Delta \text{Costo}$).
   - Variación de Precio de Venta ($\Delta \text{Precio}$).
   - Estado del Inspector Técnico: Si el comando introduce una infracción (e.g. hoja demasiado pesada), se muestra la advertencia en amarillo/rojo antes de aplicar.
3. **Botones de Decisión:**
   - `[Aplicar Cambios (Enter)]` (Color primario azul).
   - `[Descartar (Esc)]` (Gris).
   - Botón contextual post-aplicación: `[↶ Deshacer Comando]`.



<!-- FIN DE PRD-10.md -->

---



<!-- INICIO DE PRD-11.md -->


# PRD-11: MOTOR DE PLANTILLAS Y PERSONALIZACIÓN DE COTIZACIONES PDF (v1.1.0)
**Estado:** Bloqueado / Congelado  
**Fase:** 2 (Personalización Comercial)  
**Bloquea a:** Ninguno (Módulo terminal de Fase 2)

---

## 1. Misión y Alcance del Módulo

El Motor de Plantillas PDF (Pantalla **S22** y `apps.templates_pdf`) permite a cada carpintería adaptar la presentación gráfica de sus cotizaciones comerciales (colores de marca, tipografías, logotipos, cláusulas legales y distribución de columnas) sin comprometer la integridad matemática de los cálculos.

---

## 2. Los 3 Slots de Plantillas por Organización

Cada organización dispone de 3 ranuras (slots) independientes para configurar formatos de salida según el tipo de cliente:

| Slot | Nombre de Plantilla | Caso de Uso Primario | Características de Diseño |
|---|---|---|---|
| **Slot 1** | **Corporativa / Minimalista** | Clientes particulares y casas residenciales | Diseño limpio a 1 o 2 páginas, enfoque en renders vectoriales grandes, descripción clara de vidrios y valor cuota. |
| **Slot 2** | **Comercial / Detallada** | Oficinas de arquitectura y diseño | Incluye fichas de herrajes, especificaciones acústicas/térmicas certificadas y renderizado de perfiles foliados. |
| **Slot 3** | **Licitación / Constructora** | Licitaciones de edificios y obras de gran escala | Formato compacto tipo tabla de vanos, cronograma de entregas por etapas, desglose de pagos e hitos de faena. |

---

## 3. Arquitectura de Bloques Protegidos

Para evitar que una personalización estética elimine información legal obligatoria o altere datos de cálculo, las plantillas se dividen en **Bloques Editables** y **Bloques Estructurales Protegidos**:

```
┌────────────────────────────────────────────────────────┐
│ [EDITABLE] Encabezado: Logo + Datos Empresa            │
├────────────────────────────────────────────────────────┤
│ [EDITABLE] Datos del Cliente y Proyecto                │
├────────────────────────────────────────────────────────┤
│ 🔒 [BLOQUE PROTEGIDO: Render Vectorial SVG del Vano]   │
│   - El usuario puede cambiar bordes y fondos, pero el  │
│     motor inyecta el SVG canónico de /engine.          │
├────────────────────────────────────────────────────────┤
│ 🔒 [BLOQUE PROTEGIDO: Tabla de Resumen Económico]      │
│   - Subtotal Neto, IVA 19%, Total Bruto y Moneda       │
│     calculados estrictamente por el motor de precios.  │
├────────────────────────────────────────────────────────┤
│ [EDITABLE] Condiciones Comerciales y Validez de Oferta │
├────────────────────────────────────────────────────────┤
│ 🔒 [BLOQUE PROTEGIDO: Sello Criptográfico BOM Hash]    │
│   - Hash SHA-256 inmutable + Número de Revisión.       │
└────────────────────────────────────────────────────────┘
```

---

## 4. Variables Dinámicas de Inyección (Template Tags)

Las plantillas utilizan una sintaxis segura basada en placeholders declarativos:

```html
<header class="company-header" style="border-bottom: 2px solid {{ theme.primary_color }};">
  <img src="{{ org.logo_url }}" alt="{{ org.name }}" class="company-logo" />
  <div class="company-info">
    <h1>{{ org.name }}</h1>
    <p>RUT: {{ org.tax_id }} | Fono: {{ org.phone }}</p>
    <p>{{ org.address }}</p>
  </div>
</header>

<section class="quote-meta">
  <p><strong>Cotización:</strong> {{ project.code }} ({{ project.revision }})</p>
  <p><strong>Fecha Emisión:</strong> {{ project.emitted_date }}</p>
  <p><strong>Validez de la Oferta:</strong> {{ project.validity_days }} días</p>
  <p><strong>Cliente:</strong> {{ client.name }} | RUT: {{ client.tax_id }}</p>
</section>

<!-- El bloque protegido inyecta el bucle de posiciones -->
{{ protected_block_positions_loop }}

<!-- El bloque protegido inyecta los totales económicos -->
{{ protected_block_financial_totals }}

<footer class="legal-terms">
  <h3>Condiciones Generales</h3>
  <p>{{ custom_terms_and_conditions }}</p>
  <div class="integrity-stamp">
    <small>Firma Digital BOM Hash: <code>{{ project.bom_hash }}</code></small>
  </div>
</footer>
```

---

## 5. Función de Restauración a Valores de Fábrica (Reset Sagrado)

En la pantalla **S22**, cada slot dispone de un botón de emergencia:
- `[Restaurar Plantilla Original]`
- Al confirmarse, el sistema sobreescribe el HTML/CSS del slot con el template base oficial de Dekopen versionado en el código fuente, garantizando que una plantilla con sintaxis CSS rota pueda recuperarse instantáneamente en 1 clic.



<!-- FIN DE PRD-11.md -->

---



<!-- INICIO DE PRD-12.md -->


# PRD-12: VISOR 3D ESQUEMÁTICO Y ENLACE INTERACTIVO PARA CLIENTES (v1.1.0)
**Estado:** Bloqueado / Congelado  
**Fase:** 3 (Experiencia Visual)  
**Bloquea a:** Ninguno

---

## 1. Misión y Propósito Comercial

El módulo 3D (implementado con **React Three Fiber / Three.js**) permite a los talleres generar una visualización tridimensional interactiva y fotorrealista de las aberturas cotizadas a partir del `parametric_tree` 2D, elevando el valor percibido por el cliente final y acelerando la tasa de cierre de ventas.

---

## 2. Generación Procedural de Geometrías 3D

El visor 3D extruye y ensambla proceduralmente cada componente a partir de los datos geométricos calculados en `/engine`:

```mermaid
graph TD
    ParamTree[parametric_tree JSON] --> Extruder[Generador Procedural R3F]
    
    Extruder --> FrameMesh[1. Mesh Marco: Extrusión perimetral con ingletes 45°]
    Extruder --> SashMesh[2. Mesh Hoja: Extrusión con eje de rotación cinemático]
    Extruder --> GlassMesh[3. Mesh Vidrio: Material dieléctrico con IOR 1.52 y espaciador]
    Extruder --> HardwareMesh[4. Mesh Accesorios: Manillas 3D y bisagras normalizadas]
    
    FrameMesh --> Scene[Escena 3D Iluminada con HDRI]
    SashMesh --> Scene
    GlassMesh --> Scene
    HardwareMesh --> Scene
    
    Scene --> OrbitControls[Control Orbital 360° + Zoom]
    Scene --> Kinematics[Animación Interactiva de Apertura]
    Scene --> SnapshotExport[Exportación de PNG en Alta Resolución]
```

### 2.1. Cinemática y Animación de Aperturas
Al hacer clic sobre la manilla o presionar el botón *"Simular Apertura"*:
1. **Practicable (Giro Lateral):** La manilla rota $90^\circ$ hacia abajo y la hoja pivota sobre el eje vertical de las bisagras de $0^\circ$ a $90^\circ$.
2. **Oscilobatiente (Abatimiento):** La manilla rota $180^\circ$ hacia arriba y la hoja bascula hacia el interior sobre el eje horizontal inferior de $0^\circ$ a $15^\circ$.
3. **Corredera (Traslación):** La hoja móvil se desliza horizontalmente sobre su carril respectivo hasta el tope lateral.

---

## 3. Shader de Materiales y Renderizado de Colores

El motor de materiales implementa shaders PBR (Physically Based Rendering) estandarizados:
- **PVC Blanco:** `roughness: 0.25`, `metalness: 0.0`, `color: #F8FAFC`.
- **Foliado Roble Dorado (Golden Oak):** Textura procedural con relieve sutil de veta de madera (`normalMap`).
- **Foliado Gris Antracita (RAL 7016):** `roughness: 0.40`, `color: #374151`.
- **Vidrio Termopanel (DVH):** `transmission: 0.92`, `ior: 1.52`, `roughness: 0.05`, `thickness: 24.0`, intercalario interior de aluminio con sellado de butilo negro.

---

## 4. Enlace Público Compartible para Clientes (`/view/{share_token}`)

Cada cotización aprobada puede generar un enlace público protegido:
- **URL:** `https://app.dekopen.com/view/dko_live_7a9f8e21`
- **Capacidades del Cliente:**
  - Inspección 3D orbital completa desde cualquier smartphone o computadora sin instalar software.
  - Alternancia interactiva de colores de perfil (Blanco vs. Madera vs. Antracita) para ver el impacto visual.
  - Simulación de apertura de todas las hojas móviles.
  - Botón de Aceptación Digital: *"Aprobar Cotización Formalmente"* con firma táctil en pantalla y confirmación por email.
- **Seguridad:** Vista 100% en modo lectura. Los costos brutos, despieces de corte, marcas de perfiles y márgenes están totalmente ocultos y purgados del bundle de datos enviado al navegador.



<!-- FIN DE PRD-12.md -->

---



<!-- INICIO DE PRD-13.md -->


# PRD-13: AI GATEWAY, ENRUTAMIENTO Y GOBERNANZA DE PROMPTS (v1.2)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.2 (Enterprise AI Gateway & ReAct Governance Standard)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Fase:** 2 (Inteligencia Asistida y Automatización)  
**Bloquea a:** PRD-09, PRD-10, PRD-14, PRD-15

---

## 1. Arquitectura del AI Gateway y Gobernanza de Producción

El AI Gateway (`backend/apps/ai_gateway/`) es el único punto de entrada para todas las operaciones de inteligencia artificial en Dekopen. Aplica los principios de **ReAct Governance**, **Pre/Post-Invocation Hooks**, **Token Budgeting** y **Prompt Versioning**.

```
[ Frontend / Canvas S06 ] ──► [ AI Gateway Django Middleware ]
                                      │
     ┌────────────────────────────────┴────────────────────────────────┐
     ▼                                                                 ▼
[ PRE-INVOCATION HOOKS ]                                      [ ENRUTADOR DE MODELOS ]
• Validación de saldo (credit_ledger)                         • Dekopen Neural Core (Luna 99%)
• Sanitización de inyecciones (Indirect Prompt Injection)     • Dekopen Vision CAD (Gemini 3.7)
• Inyección de identidad y RLS (org_id)                       • Dekopen Titan (Sol / Kimi Opt-In)
     │                                                                 │
     └────────────────────────────────┬────────────────────────────────┘
                                      │
                                      ▼
                      [ EJECUCIÓN TOOL / LLM CALL ]
                                      │
     ┌────────────────────────────────┴────────────────────────────────┐
     ▼                                                                 ▼
[ POST-INVOCATION HOOKS ]                                     [ AUDITORÍA INMUTABLE ]
• Validación de Schema JSON (Pydantic)                        • Registro en `ai_audit_logs`
• Detección de secretos o datos cruzados                      • Registro en `price_audit_logs`
• Entrega a /engine para cálculo 0.00 mm                      • Habilitación de Sacred Undo (Cmd+Z)
```

---

## 2. Técnicas de Prompting Aplicadas por Herramienta

| Tool ID | Herramienta | Técnica Canónica | Justificación de Arquitectura |
|---|---|---|---|
| **T1** | OCR de Planos (S27) | **Few-Shot Multimodal** | Ejemplos de vanos etiquetados para garantizar el formato JSON sin alucinación de cotas. |
| **T2** | Comandos NLP (Canvas) | **ReAct con Hooks** | Alternancia *Thought $\rightarrow$ Action $\rightarrow$ Observation*. La acción llama a `/engine` para diff numérico. |
| **T3** | Sugerencia de Descuentos | **Chain-of-Thought (CoT)** | Razonamiento paso a paso sobre márgenes antes de sugerir el porcentaje. |
| **T6** | Compilador de Catálogos | **Directional Stimulus** | Guías semánticas dirigidas a matrices de junquillos y holguras de perfiles. |
| **T8** | Certificado Fabricabilidad | **Self-Consistency Doble Ciego** | Auditoría dual independiente cruzando Neural Core y Vision CAD (o Titan Sol en Max Effort). |

---

## 3. Pre & Post-Invocation Hooks (Gobernanza a Nivel de Ejecución)

1. **Pre-Invocation:**
   - **Bloqueo Transaccional de Saldo:** `SELECT ... FOR UPDATE` sobre `credit_ledger`. Si saldo $\le 0$, cancela la llamada antes de facturar tokens.
   - **Aislamiento Multi-Tenant:** Inyecta automáticamente el `org_id` y valida que el usuario pertenezca a la organización.
2. **Post-Invocation:**
   - **El LLM jamás escribe números finales:** Todo diff paramétrico generado por el LLM se envía obligatoriamente a `/engine` para recálculo determinista a `0.00 mm`.
   - **Trazabilidad Obligatoria:** Escribe en `ai_audit_logs` con `latency_ms`, `tokens_in`, `tokens_out`, `model_name` y hash de payload.

---

## 4. Versionado de Prompts y Rate Limiting

- **Prompt Registry (FQN):** Todos los templates de prompts están versionados en código (`prompts/v1/`, `prompts/v2/`) con identificadores unívocos (ej: `dekopen:prompt:t2_nlp_command:v1.2`). Un rollback de prompt se hace en segundos sin alterar la lógica de negocio.
- **Techo de Tokens por Taller:** Cada organización tiene un límite diario de tokens para prevenir fugas de consumo en llamadas masivas.



<!-- FIN DE PRD-13.md -->

---



<!-- INICIO DE PRD-14.md -->


# PRD-14: CERTIFICADO DE FABRICABILIDAD Y DOBLE VERIFICADOR (v1.2)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.2 (Agent-Ready Bootstrap)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Fase:** 3 (Garantía y Certificación)  
**Bloquea a:** PRD-15

---

## 1. Misión del Certificado de Fabricabilidad

El Certificado de Fabricabilidad (Documento **DOC-08** y Tool **T8**) es una garantía técnica digital que valida que un proyecto cumple al 100% con las normas de resistencia mecánica al viento (NCh 432), seguridad en acristalamiento (NCh 132), límites dimensionales y capacidades de herrajes de los sistemas de perfiles utilizados.

---

## 2. Protocolo de Doble Verificación Cruzada (Tool T8 — 50 Créditos)

Para emitir el sello de certificación oficial sin quemar tokens innecesarios, el sistema ejecuta una auditoría de **doble ciego** entre dos arquitecturas independientes:

```
                  [ Árbol Paramétrico + BOM + Memoria de Cálculo ]
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
     [ Modelo A: Dekopen Neural Core™ ]           [ Modelo B: Dekopen Vision CAD™ ]
        (GPT 5.6 Luna xHigh-Max)                      (Gemini 3.7 High / GLM 5.3)
                 │                                               │
                 └───────────────────────┬───────────────────────┘
                                         ▼
                             [ Árbitro Determinista ]
                                (Concordancia 100%)
                                         │
                     ┌───────────────────┴───────────────────┐
                     ▼                                       ▼
        [ 🟢 Coincidencia Total ]               [ 🔴 Discrepancia > 0.00 mm ]
        Sello DOC-08 + Hash + QR                Alerta Crítica + Bloqueo OT
```

### Reglas Normativas de T8
1. **Auditoría Estándar (Default 50 créditos):** Cruza **Dekopen Neural Core™ (GPT 5.6 Luna)** con **Dekopen Vision CAD™ (Gemini 3.7 High)**. No consume tokens de modelos masivos.
2. **Opción Ultra-Ingeniería (Modo Titan):** Si el usuario activa explícitamente el toggle *"Auditoría Titan (Max Effort)"*, el segundo árbitro escala a **Dekopen Titan Engine™ (GPT 5.6 Sol)**.
3. **Concordancia Matemática:** Cualquier desviación $> 0.00\text{ mm}$ en holguras o $> 0.1\text{ kg}$ en peso de hoja bloquea la emisión del certificado y alerta al taller con frase de inspección.



<!-- FIN DE PRD-14.md -->

---



<!-- INICIO DE PRD-15.md -->


# PRD-15: AUTOPILOT MAX — COTIZACIÓN AUTOMÁTICA DESASISTIDA (v1.1.1)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.1.1 (Congelada y Bloqueada)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Fase:** 3 (Automatización de Alto Nivel)  
**Bloquea a:** Ninguno

---

## 1. Misión de Autopilot Max

Autopilot Max (Tool **T9** `draft_autopilot`, **30 + 2 créditos / página**) procesa solicitudes de cotización entrantes (PDFs de licitación, cuadros de vanos por correo) y genera un **borrador de cotización 100% calculado y listo para revisión humana**.

---

## 2. Invariable Constitucional: Espera Humana Obligatoria

Ninguna cotización generada por Autopilot se envía directamente al cliente sin el clic de aprobación y firma de un usuario con rol `OWNER` o `ESTIMATOR` (Regla 11 de la Constitución).

---

## 3. Pipeline de Ejecución y Reglas del Inspector (R01–R14)

1. Ingestión y OCR del archivo con Tool `T1`.
2. Asignación automática de la serie por defecto (`profile_systems`) y color.
3. Despiece determinista en `/engine`.
4. Evaluación estricta de las **14 Reglas Canónicas del Inspector Técnico (R01 a R14)**.
5. Si el semáforo arroja 🔴 **Rojo**, Autopilot marca las partidas afectadas con sugerencias de 1-clic fix y bloquea la emisión hasta la resolución manual.



<!-- FIN DE PRD-15.md -->

---



<!-- INICIO DE PRD-16.md -->


# PRD-16: GESTIÓN E INTEGRACIÓN DE INVENTARIO DE RETAZOS (OFFCUTS) (v1.1.0)
**Estado:** Bloqueado / Congelado  
**Fase:** 4 (Optimización de Taller)  
**Bloquea a:** Ninguno

---

## 1. Misión y Justificación del Módulo

El módulo de Inventario de Retazos (`offcut_inventory`) permite a las carpinterías recuperar entre el $6\%$ y el $12\%$ del costo total de perfilería mediante el etiquetado por código QR y la reutilización automatizada de sobrantes de barra en futuras órdenes de trabajo.

---

## 2. Esquema DDL de Retazos (`offcut_inventory`)

```sql
CREATE TYPE offcut_status AS ENUM ('AVAILABLE', 'RESERVED', 'CONSUMED', 'DISCARDED');

CREATE TABLE offcut_inventory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    profile_article_id UUID NOT NULL REFERENCES profile_articles(id) ON DELETE RESTRICT,
    color VARCHAR(50) NOT NULL,
    length_mm NUMERIC(10, 2) NOT NULL CHECK (length_mm >= 500.00),
    rack_location VARCHAR(50), -- e.g. "Rack B, Nivel 2"
    source_order_id UUID REFERENCES orders(id) ON DELETE SET NULL,
    reserved_order_id UUID REFERENCES orders(id) ON DELETE SET NULL,
    status offcut_status NOT NULL DEFAULT 'AVAILABLE',
    qr_code VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    consumed_at TIMESTAMPTZ,
    CONSTRAINT uk_org_offcut_qr UNIQUE (org_id, qr_code)
);

CREATE INDEX idx_offcut_lookup ON offcut_inventory (org_id, profile_article_id, color, status, length_mm);
```

---

## 3. Ciclo de Vida del Retazo y Etiquetado QR

```mermaid
graph LR
    Cut[1. Corte 1D en Sierra] -->|Sobrante > 1000 mm| Label[2. Impresión Etiqueta QR Térmica]
    Label --> Rack[3. Almacenamiento en Rack de Taller]
    Rack --> Optimizer[4. Optimizador 1D: Asigna Retazo antes de Barra Nueva]
    Optimizer --> Reserve[5. Estado RESERVED para nueva OT]
    Reserve --> ScanUse[6. Operario Escanea QR y Corta Pieza]
    ScanUse --> Consumed[7. Estado CONSUMED]
```

---

## 4. Integración en el Algoritmo de Corte 1D

1. Al ejecutar la optimización de corte de una orden de producción:
   - El optimizador consulta los retazos `AVAILABLE` para el SKU y color requeridos.
   - Si una pieza requerida cabe en un retazo existente (considerando $15\text{ mm}$ de despunte y $4\text{ mm}$ de kerf), se prioriza el retazo antes de abrir una barra comercial nueva de $6.00\text{ m}$.
   - Se actualiza el estado del retazo a `RESERVED` vinculado al `order_id` de la OT.



<!-- FIN DE PRD-16.md -->

---



<!-- INICIO DE PRD-17.md -->


# PRD-17: BANDEJA DE ENTRADA OMNICANAL (EMAIL Y WHATSAPP) (v1.1.0)
**Estado:** Bloqueado / Congelado  
**Fase:** 4 (Captura Omnicanal)  
**Bloquea a:** Ninguno

---

## 1. Misión del Módulo

La Bandeja de Entrada Omnicanal (`apps.inbox`) centraliza la recepción de solicitudes de presupuesto provenientes de correos electrónicos y mensajes de WhatsApp con archivos adjuntos, canalizándolos hacia el pipeline de Autopilot Max (PRD-15).

---

## 2. Arquitectura de Ingestión

```mermaid
graph TD
    EmailClient[Cliente envía Email con PDF] --> SendGrid[Inbound Webhook SendGrid]
    WhatsAppClient[Cliente envía WhatsApp con Foto] --> WABA[Meta Cloud API / Twilio Webhook]
    
    SendGrid --> InboundRouter[Inbound Request Router]
    WABA --> InboundRouter
    
    InboundRouter --> TenantResolver[Identificación de Org por Dirección / Teléfono]
    TenantResolver --> DBInbox[Creación en inbound_requests]
    DBInbox --> AutopilotWorker[Disparo de Huey Task: Autopilot Max T9]
    AutopilotWorker --> DraftProject[Creación de Proyecto DRAFT en Dekopen]
```

---

## 3. Esquema DDL de Ingestión (`inbound_requests`)

```sql
CREATE TYPE inbound_source AS ENUM ('EMAIL', 'WHATSAPP', 'WEB_FORM');
CREATE TYPE inbound_status AS ENUM ('RECEIVED', 'PROCESSING', 'STAGED', 'FAILED', 'ARCHIVED');

CREATE TABLE inbound_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES tenancy_organizations(id) ON DELETE CASCADE,
    source inbound_source NOT NULL,
    sender_identifier VARCHAR(255) NOT NULL, -- Email o número de teléfono
    sender_name VARCHAR(255),
    subject TEXT,
    raw_body TEXT,
    attachment_storage_paths JSONB NOT NULL DEFAULT '[]'::JSONB,
    status inbound_status NOT NULL DEFAULT 'RECEIVED',
    created_project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 4. Gobernanza y Seguridad de Adjuntos

1. **Escaneo de Seguridad:** Todos los archivos adjuntos se validan mediante análisis de MIME-type estricto (solo `.pdf`, `.png`, `.jpg`, `.jpeg`, `.xlsx`) y escaneo antivirus antes de almacenarse en Supabase Storage.
2. **Aislamiento por Tenant:** Los archivos de la bandeja se enrutan a la carpeta `org_{org_id}/inbox/{request_uuid}/`.



<!-- FIN DE PRD-17.md -->

---



<!-- INICIO DE PRD-18.md -->


# PRD-18: ASSETS GO-TO-MARKET (GTM), LANDING Y PLAYBOOK DE CRECIMIENTO B2B (v1.1.2)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.1.2 (Congelada y Bloqueada tras Auditoría Final)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Fase:** 0 – 1 (Lanzamiento y Adquisición)  
**Bloquea a:** Ninguno

---

## 1. Misión y Posicionamiento de Marca

Dekopen se posiciona como el **primer sistema operativo especializado para talleres y fabricantes de ventanas de PVC en Chile y Latinoamérica**. 

### Mensaje Central de Posicionamiento
> *"El software de cálculo, optimización de corte y cotización para carpinterías de PVC con tolerancia 0.00 mm. Deja atrás el Excel y los vidrios mal pedidos."*

---

## 2. Estructura de la Landing Page (`dekopen.com`) — Enmienda A.8

```
┌────────────────────────────────────────────────────────┐
│ [Nav] Dekopen | Características | Precios | Testimonios │ [Empezar Prueba Gratis]
├────────────────────────────────────────────────────────┤
│ [Hero]                                                 │
│ 🎯 El software de cálculo y cotización de PVC           │
│    que no perdona ni 1 mm.                             │
│ ⚡ Diseña en 2D, optimiza el corte 1D, cotiza en 2 min  │
│    y genera pedidos de vidrio sin margen de error.     │
│                                                        │
│ [Botón CTA: Empezar prueba gratis — 7 días · 500 créditos · sin tarjeta] │
├────────────────────────────────────────────────────────┤
│ 🛡️ "El motor de tolerancia 0.00 mm está incluido en TODOS los planes." │
├────────────────────────────────────────────────────────┤
│ [Toggle Pricing: (•) Anual (billed annually) - Ahorra hasta 23% | ( ) Mensual] │
│                                                        │
│ [Starter]          [Profesional ⭐]       [Business]       [Business 2x]   │
│ $35/mo (~$39~)     $59/mo (~$69~)        $99/mo (~$129~)  $129/mo (~$149~)│
│ Billed ann: $420   Billed ann: $708      Billed ann: $1188 Billed ann: $1548│
│ CLP Anual: 35.990  CLP Anual: 59.990     CLP Anual: 99.990 CLP Anual: 129.990│
│ CLP Mes: 39.990    CLP Mes: 69.990       CLP Mes: 129.990  CLP Mes: 149.990 │
│                    ⭐ MÁS POPULAR                                          │
│ "El motor          "Todo el poder con    "Todo el         "Solo más       │
│ completo. Sin IA,  IA para cotizar       producto para    créditos. Todo  │
│ por elección."     más rápido."          equipos."        lo demás ya lo  │
│                                                           tienes."        │
│ 2 usuarios         3 usuarios            5 usuarios       5 usuarios      │
│ 0 créditos IA      2.000 créditos/mes    6.000 créditos   12.000 créditos │
│                                                                           │
│ [Probar 7 días]    [Probar 7 días]       [Probar 7 días]  [Probar 7 días] │
├────────────────────────────────────────────────────────┤
│ 💎 "Devolución íntegra 14 días en tu primera compra anual."               │
│ 🏆 "Founding 50: Los primeros 50 suscriptores anuales congelan su precio  │
│     de por vida. (Quedan N de 50 disponibles)."                           │
└────────────────────────────────────────────────────────┘
```

---

## 3. Secuencia de Prospección Fría B2B (Cold Outreach Templates Completos)

### Correo 1: El Dolor del Vidrio Mal Pedido y Desperdicio de Perfiles
**Asunto:** Consulta rápida sobre cortes de PVC y pedidos de vidrio en {{taller_nombre}}  
**Cuerpo:**
> Hola {{nombre_contacto}},
>
> Te escribo directamente porque en talleres de PVC como {{taller_nombre}}, un error de apenas 2 mm al pedir un termopanel o al cortar un refuerzo de acero significa perder dinero, tiempo y retrasar la entrega en obra.
>
> Desarrollamos **Dekopen**: el primer software especializado para carpinterías de PVC en Chile con motor de cálculo de tolerancia 0.00 mm. Diseñas en 2D, optimizas el corte de barras reduciendo la merma al mínimo y generas la orden exacta de vidrios y cotización en menos de 2 minutos.
>
> ¿Tendrías 10 minutos este jueves o viernes para mostrarte cómo optimizar un proyecto real de tu taller?
>
> Saludos cordiales,  
> **Equipo Dekopen** | dekopen.com

---

### Correo 2: Demostración Práctica con Caso de 20 Vanos
**Asunto:** ¿Cuánto tiempo tarda tu equipo cotizando 20 vanos en {{taller_nombre}}?  
**Cuerpo:**
> Hola {{nombre_contacto}},
>
> La mayoría de los talleres que usan planillas de Excel tardan entre 2 y 4 horas en calcular despieces, junquillos y cotizaciones para una obra mediana de 20 ventanas.
>
> Con Dekopen, puedes subir el plano o cuadro de vanos en PDF y obtener el proyecto estructurado, la lista de corte 1D optimizada y la cotización formal con IVA en menos de 3 minutos.
>
> Puedes probarlo gratis por 7 días con 500 créditos incluidos y sin ingresar tarjeta de crédito aquí: [dekopen.com/trial](https://dekopen.com)
>
> Si me envías un cuadro de vanos típico de tu taller, te preparo una demostración personalizada sin compromiso.
>
> Un abrazo,  
> **Equipo Dekopen**

---

### Correo 3: Calculadora de Retazos y Descuento por Lanzamiento
**Asunto:** Ahorro en barras de PVC: optimización 1D para {{taller_nombre}}  
**Cuerpo:**
> Estimado {{nombre_contacto}},
>
> Con el costo actual de los perfiles de PVC, cada retazo desperdiciado impacta directamente tu margen neto.
>
> Nuestro algoritmo de optimización lineal 1D aprovecha hasta el 94% de cada barra comercial, calcula la merma exacta y genera etiquetas de taller para tu personal de corte.
>
> Estamos abriendo el programa **Founding 50** para las primeras 50 carpinterías en Chile, con precio congelado de por vida y acompañamiento directo en la carga de tus listas de precios.
>
> ¿Te gustaría que coordinemos una llamada breve de 15 minutos esta semana?
>
> Atentamente,  
> **Equipo Dekopen** | dekopen.com



<!-- FIN DE PRD-18.md -->

---



<!-- INICIO DE PRD-19.md -->


# PRD-19: REQUERIMIENTOS NO FUNCIONALES (NFR), SEGURIDAD, OBSERVABILIDAD Y RECUPERACIÓN ANTE DESASTRES (v1.1.0)
**Estado:** Bloqueado / Congelado  
**Fase:** 0 (Fundacional)  
**Bloquea a:** Todo el despliegue a producción

---

## 1. Matriz de Requerimientos No Funcionales (NFR)

| Dimensión | Métrica Objetivo | Umbral Crítico de Alarma | Estrategia de Mitigación |
|---|---|---|---|
| **Disponibilidad (SLA)** | $\ge 99.9\%$ uptime mensual | $< 99.5\%$ | Railway multi-replica + Supabase Pro con alta disponibilidad gestionada. |
| **Latencia del Engine** | $< 50\text{ ms}$ por cálculo de posición | $> 150\text{ ms}$ | Pureza del paquete `/engine` sin llamadas I/O en caliente. |
| **Fluidez del Canvas 2D** | $\ge 60\text{ FPS}$ en renderizado SVG | $< 30\text{ FPS}$ | React memoization de nodos, renderizado vectorial SVG nativo sin capas pesadas. |
| **Generación de PDFs** | $< 2.5\text{ s}$ para cotización de 10 vanos | $> 5.0\text{ s}$ | WeasyPrint pre-compilado en workers dedicados de Huey. |
| **Pérdida de Datos (RPO)** | $\le 5\text{ minutos}$ | $> 15\text{ minutos}$ | Supabase Point-in-Time Recovery (PITR) continuo. |
| **Tiempo de Recuperación (RTO)** | $\le 60\text{ minutos}$ | $> 120\text{ minutos}$ | Scripts automatizados de aprovisionamiento de infraestructura. |

---

## 2. Estrategia de Respaldos y Protocolo de Restauración Ensayada (Gate 7)

> [!IMPORTANT]
> Un respaldo que nunca ha sido restaurado en un simulacro real equivale a no tener respaldo.

1. **Respaldos Continuos (PITR):** Supabase Pro mantiene bitácora de transacciones WAL (Write-Ahead Logging) con capacidad de restauración a cualquier segundo de los últimos 7 días.
2. **Dump Diario Cifrado Externo:**
   - Cada noche a las 03:00 UTC, una tarea cron ejecuta `pg_dump` con compresión máxima.
   - El archivo se cifra simétricamente con `AES-256` utilizando una clave maestra en variables de entorno.
   - Se transfiere a un bucket secundario en **Cloudflare R2** (proveedor independiente a Supabase).
3. **Simulacro de Restauración Obligatorio (Gate 7):**
   - Antes de pasar a producción comercial, se debe ejecutar y documentar un simulacro de recuperación completo en un ambiente de staging limpio a partir del último dump cifrado.

---

## 3. Seguridad, Rate Limiting y Protección de API

```mermaid
graph TD
    ClientRequest[Petición Entrante] --> CloudflareWAF[Cloudflare WAF / SSL TLS 1.3]
    CloudflareWAF --> RateLimiter{Rate Limiter en Redis}
    
    RateLimiter -->|API Estándar: > 100 req/min| Throttle429[HTTP 429 Too Many Requests]
    RateLimiter -->|AI Gateway: > 10 req/min| Throttle429
    RateLimiter -->|Dentro de límites| DjangoAPI[Django Backend DRF]
    
    DjangoAPI --> AuthValidate[Validación JWT Supabase + RLS Context]
    AuthValidate --> Execution[Ejecución de Negocio]
```

### 3.1. Políticas de Seguridad de Aplicación
- **Cero Credenciales en Código:** Variables de entorno administradas exclusivamente vía Railway Environment Secrets.
- **Sanitización XSS y CSP:** Content Security Policy estricto en cabeceras HTTP emitidas por Django y Vercel.
- **URLs Firmadas con Expiración:** Todo acceso a planos, PDFs y comprobantes en Supabase Storage requiere firma criptográfica temporal ($3600\text{ s}$).

---

## 4. Pila de Observabilidad y Telemetría

1. **Grabación Visual de Sesiones y Bugs:** **Jam.dev** integrado en la SPA. Permite al usuario reportar un problema en 1 clic capturando automáticamente el estado de la consola, logs de red y grabación de pantalla sin fricción.
2. **Métricas de Producto y Adopción:** **PostHog Cloud** para análisis de embudos de conversión (Onboarding $\rightarrow$ Primera cotización $\rightarrow$ Aprobación de OT), retención de usuarios y feature flags.
3. **Logs Estructurados en Producción:** Formato JSON unificado en backend (`structlog` en Python) con inyección automática de `org_id`, `user_id` y `trace_id` para trazabilidad inmediata en los paneles de logs de Railway.



<!-- FIN DE PRD-19.md -->

---



<!-- INICIO DE PRD-DESIGN-SYSTEM-ADOBE.md -->


# PRD-DESIGN-SYSTEM-ADOBE: SISTEMA DE DISEÑO DUAL (LIGHT STUDIO / DARK GRAPHITE) (v1.2)
**Estado:** Bloqueado / Congelado  
**Filosofía Visual:** Adobe Precision Tooling (Inspirado en Illustrator, InDesign, AutoCAD y Fusion 360).  
**Soporte Dual:** Modo Claro (Studio Light) y Modo Oscuro (Dark Graphite) seleccionables por el usuario con 1 clic.

---

## 1. Paleta Dual de Tokens Semánticos (Light Studio & Dark Graphite)

El usuario puede alternar en cualquier momento entre el **Modo Claro (Light Studio)** y el **Modo Oscuro (Dark Graphite)** mediante el switch de tema en la barra superior.

```
========================================================================================================================
TOKEN SEMÁNTICO              MODO CLARO (LIGHT STUDIO)     MODO OSCURO (DARK GRAPHITE)   APLICACIÓN EN INTERFAZ
========================================================================================================================
--theme-bg-canvas (Base)     #F4F5F7  (Gris Estudio Claro) #121214  (Grafito Mate)       Lienzo de dibujo CAD infinito
--theme-surface-panel        #FFFFFF  (Blanco Puro)        #1A1A1E  (Panel Oscuro)       Paneles dockables (Árbol, Inspector)
--theme-surface-card         #EAECEF  (Gris Suave Card)    #222228  (Tarjeta Oscura)     Accordions, inputs, cards de vanos
--theme-surface-hover        #DFE2E6  (Hover Claro)        #2C2C34  (Hover Oscuro)       Hover en botones de herramientas y filas
--theme-border-subtle        #D1D5DB  (Borde Estructural)  #3A3A46  (Borde Oscuro)       Separadores de paneles (1px sólido)
--theme-text-primary         #0F172A  (Negro Pizarra)      #F8FAFC  (Blanco Tiza)        Títulos, cotas activas, precios
--theme-text-secondary       #475569  (Gris Pizarra)       #94A3B8  (Gris Plata)         Etiquetas de formulario, roles
--theme-text-muted           #94A3B8  (Gris Atenuado)      #626274  (Gris Oscuro Muted)  Placeholders, atajos de teclado

--theme-cyan-tool            #0091EA  (Azul Técnico Intenso)#00E5FF  (Cian Neón CAD)     Líneas de cota milimétricas y guías
--theme-amber-opening        #D97706  (Ámbar Cálido)       #FFB300  (Ámbar Luminoso)     Líneas DIN de apertura en hojas
--theme-emerald-action       #059669  (Verde Esmeralda)    #00C853  (Verde Neón)         Botón primario "Aprobar para OT"
--theme-crimson-alert        #DC2626  (Rojo Alerta)        #FF1744  (Rojo Carmesí)       Bloqueos críticos del inspector
--theme-glass-tint           rgba(0,145,234,0.06)          rgba(0,229,255,0.08)         Sombreado interior de cristales
========================================================================================================================
```

---

## 2. Tipografía Estricta y Escala Tabular

- **Interfaz de Usuario:** `'Inter', -apple-system, BlinkMacSystemFont, sans-serif`
- **Cotas, Fórmulas y Dinero:** `'JetBrains Mono', 'SF Mono', monospace` (`font-variant-numeric: tabular-nums`).

| Nivel | Tamaño | Peso | Line Height | Uso |
|---|---|---|---|---|
| **App Title** | `14px / 0.875rem` | 700 (Bold) | `18px` | Título de proyecto, código COT |
| **Panel Header** | `11px / 0.6875rem` | 700 (Bold) | `16px` | Encabezados de acordeón en mayúsculas |
| **Body UI** | `12px / 0.75rem` | 400 / 500 | `16px` | Etiquetas, opciones de selección |
| **Cota Dimensión** | `11px / 0.6875rem` | 700 (Bold) | `14px` | Cotas milimétricas sobre el canvas |
| **Precios / Totales**| `13px / 0.8125rem` | 700 (Bold) | `16px` | Desglose económico e IVA |

---

## 3. Disposición de Pantalla y Docking Modular (Adobe CAD Grid)

```
+----------------------------------------------------------------------------------------------------+
| 1. APPLICATION RIBBON (Height: 48px) - [Logo] [Archivo v] [Edición v] | [COT-2026-0142] | [🌓 Modo]|
+--------------+--------------------------------------------------------------------+----------------+
| 2. TOOLBAR   | 3. CAD CANVAS VIEWPORT (Infinito con Pan/Zoom en Modo Claro/Oscuro)| 4. DOCKABLE    |
| (Width: 52px)|                                                                    | INSPECTOR      |
|              |             [ ← 1500.00 mm (Cota Editable Teclado) → ]             | (Width: 320px) |
| [ ⇱ Cursor ] |     +---------------------------+---------------------+            |                |
| [ ┼ Snapping]|     |                           |       / \ (OB)      |            | ▼ Dimensions   |
| [ ⧉ Dividers]| 1400|        PAÑO FIJO          | 1400/     \ (Manilla|            |   W: [1500 mm] |
| [ ◫ Sashes  ]|  mm |        DVH 24mm           |  mm/       \   o    |            |   H: [1400 mm] |
| [ ⎔ Openings]|     |        690x1310 mm        |   /         \  |    |            |                |
| [ 📏 Measure]|     +---------------------------+---------------------+            | ▼ Profile Spec |
|              |               [ 750 mm ]                  [ 750 mm ]               |   Demo 60 mm v |
|              |                                                                    |                |
|              |                                                                    | ▼ Inspector    |
|              |                                                                    |   🟢 0 Errores |
|              |                                                                    |   Weight: 38kg |
|              |                                                                    |                |
|              |                                                                    | [ APROBAR OT ] |
+--------------+--------------------------------------------------------------------+----------------+
| 5. STATUS BAR (Height: 24px) - [Engine: 0.00mm] [Grid: 10mm] [Snap: ON] [X: 750 Y: 1400]           |
+----------------------------------------------------------------------------------------------------+
```

---

## 4. Arquitectura de Funcionamiento de Inteligencia Artificial (AI Engine & Diff Workflow)

El motor de IA opera bajo un protocolo estricto de 5 pasos con previsualización comparativa:

```
[1. Entrada de Usuario] ---> [2. Gateway IA (Tool Tx)] ---> [3. Cálculo Determinista /engine]
  • Prompt NLP                 • Extracción tipada            • Explosión BOM
  • Plano PDF / Croquis        • Auditoría previa             • Semáforo Inspector
                                • Débito de créditos                  |
                                                                      v
[5. Aprobación Humana] <---------------------------------- [4. Modal de Diff Antes/Después]
  • [Aplicar Mutación]                                       • Comparativa visual 2D
  • [Deshacer Sagrado (⌘Z)]                                  • Delta de Costo y Precio
```

1. **Ingestión:** El usuario ingresa una instrucción en lenguaje natural (e.g. *"Divide la ventana al medio y pon la hoja derecha oscilobatiente"*) o arrastra un plano PDF.
2. **Ejecución Tipada:** La herramienta correspondiente (`T1` a `T12`) genera una propuesta estructurada de mutación en formato JSON. Se audita en `ai_audit_logs` y se descuentan los créditos de la organización.
3. **Validación en `/engine`:** El motor matemático calcula las nuevas cotas, despiece y corre las 14 reglas del inspector.
4. **Modal Visual Diff (Antes / Después):** Se despliega una ventana flotante modal mostrando el estado previo vs. el estado propuesto con los nuevos elementos resaltados en verde, junto con los deltas de costo y precio de venta.
5. **Aprobación Humana y Deshacer:** El cambio solo se aplica a la base de datos tras el clic explícito del usuario (`[Apply Mutation]`), y se puede revertir inmediatamente con el botón `[Sacred Undo]` (`⌘Z`).



<!-- FIN DE PRD-DESIGN-SYSTEM-ADOBE.md -->

---



<!-- INICIO DE PRD-FRONTEND-APIS-COMPONENTS.md -->


# PRD-FRONTEND-APIS-COMPONENTS: ARQUITECTURA DE COMPONENTES REACT Y CONTRATOS DE API (v1.1.2)
**Estado:** Bloqueado / Congelado  
**Stack Frontend:** React 18 + TypeScript 5.6 + Vite + Tailwind CSS + TanStack Query v5 + Zustand

---

## 1. Contratos de API REST (Endpoints, Payloads y Tipos)

Todos los endpoints responden en formato JSON y requieren encabezado `Authorization: Bearer <Supabase_JWT>`.

```
=====================================================================================================
MÉTODO & RUTA                         PROPÓSITO & ALCANCE                    CACHE KEY TANSTACK QUERY
=====================================================================================================
POST /api/v1/engine/calculate/        Cálculo determinista instantáneo       ['engine', 'calc', hash]
GET  /api/v1/projects/                Lista paginada de proyectos             ['projects', { page, status }]
GET  /api/v1/projects/:id/            Detalle completo de proyecto + vanos    ['projects', projectId]
POST /api/v1/projects/:id/positions/  Creación de nueva posición/vano         Invalida ['projects', id]
PUT  /api/v1/positions/:id/           Actualización paramétrica de posición   Invalida ['projects', id]
POST /api/v1/projects/:id/freeze/     Congelar revisión (REV-A -> REV-B)      ['project_versions', id]
POST /api/v1/ai/extract-positions/    OCR Gemini Flash de planos (Tool T1)    ['ai', 'jobs', jobId]
POST /api/v1/orders/generate-ot/      Emisión de orden de trabajo (OT)        Invalida ['orders', orgId]
GET  /api/v1/wallet/ledger/           Historial de transacciones de créditos  ['wallet', 'ledger']
=====================================================================================================
```

### 1.1. Esquema del Endpoint `/api/v1/engine/calculate/` (Enmienda 2 Golden Snapshot)

> [!IMPORTANT]
> **Regla de Generación Automatizada (Enmienda 2 & H1):** El archivo `engine/tests/golden_example.json` se **GENERA** ejecutando `/engine` sobre el request de entrada en el SHOT-06 y se commitea como snapshot de prueba en CI. El request transmite obligatoriamente `glass_spec` y el motor deriva `thickness_net_mm` sumando exclusivamente los paños de cristal (`4-16-4` $\rightarrow 8.00\text{ mm}$, `4-12-4` $\rightarrow 8.00\text{ mm}$, `6-12-6` $\rightarrow 12.00\text{ mm}$, monolítico $\rightarrow$ espesor propio).

- **Request Payload:**
  ```json
  {
    "system_id": "d0000000-0000-0000-0000-000000000001",
    "nominal_width_mm": "1500.00",
    "nominal_height_mm": "1400.00",
    "color": "WHITE",
    "parametric_tree": {
      "id": "root",
      "type": "SPLIT_V",
      "split_offset_mm": "750.00",
      "children": [
        { 
          "id": "bay_1", 
          "type": "BAY", 
          "opening_type": "FIXED", 
          "glass_thickness_mm": "24.00",
          "glass_spec": "4-16-4 Float Incoloro"
        },
        { 
          "id": "bay_2", 
          "type": "BAY", 
          "opening_type": "TILT_TURN_RIGHT", 
          "glass_thickness_mm": "20.00",
          "glass_spec": "4-12-4 Float Incoloro"
        }
      ]
    }
  }
  ```
- **Response Schema Esperado (Verificación Matemática Demo 60 mm):**
  ```json
  {
    "calculation_hash": "sha256_[GENERAR-AL-COMPILAR]",
    "profile_cuts": [
      { "role": "FRAME",        "length_mm": "1506.00", "angle_left": "45.0", "angle_right": "45.0", "qty": 2 },
      { "role": "FRAME",        "length_mm": "1406.00", "angle_left": "45.0", "angle_right": "45.0", "qty": 2 },
      { "role": "MULLION_V",    "length_mm": "1280.00", "angle_left": "90.0", "angle_right": "90.0", "qty": 1 },
      { "role": "SASH",         "length_mm": "672.00",  "angle_left": "45.0", "angle_right": "45.0", "qty": 2 },
      { "role": "SASH",         "length_mm": "1302.00", "angle_left": "45.0", "angle_right": "45.0", "qty": 2 },
      { "role": "GLAZING_BEAD", "length_mm": "689.00",  "angle_left": "45.0", "angle_right": "45.0", "qty": 2 },
      { "role": "GLAZING_BEAD", "length_mm": "1319.00", "angle_left": "45.0", "angle_right": "45.0", "qty": 2 },
      { "role": "GLAZING_BEAD", "length_mm": "555.00",  "angle_left": "45.0", "angle_right": "45.0", "qty": 2 },
      { "role": "GLAZING_BEAD", "length_mm": "1185.00", "angle_left": "45.0", "angle_right": "45.0", "qty": 2 }
    ],
    "reinforcements": [
      { "role": "FRAME",     "length_mm": "1470.00", "qty": 2 },
      { "role": "FRAME",     "length_mm": "1370.00", "qty": 2 },
      { "role": "MULLION_V", "length_mm": "1270.00", "qty": 1 },
      { "role": "SASH",      "length_mm": "636.00",  "qty": 2 },
      { "role": "SASH",      "length_mm": "1266.00", "qty": 2 }
    ],
    "glasses": [
      { "bay_id": "bay_1", "width_mm": "680.00",  "height_mm": "1310.00",
        "area_m2": "0.8908", "weight_kg": "17.82", "thickness_net_mm": "8.00" },
      { "bay_id": "bay_2", "width_mm": "546.00",  "height_mm": "1176.00",
        "area_m2": "0.6421", "weight_kg": "12.84", "thickness_net_mm": "8.00" }
    ],
    "inspector": {
      "status": "GREEN",
      "findings": [],
      "sash_weight_kg": "26.55",
      "sash_max_allowed_kg": "100.00"
    }
  }
  ```

---

## 2. Jerarquía de Componentes React (`src/features/canvas/`)

```
<CanvasEditor2DView>
  ├── <CADTopMenuBar />                  // Ribbon superior con acciones de archivo, zoom y switch claro/oscuro
  ├── <FloatingToolPalette />            // Barra de herramientas flotante estilo Illustrator (52px)
  │     ├── <ToolButton type="select" />
  │     ├── <ToolButton type="split_v" />
  │     ├── <ToolButton type="split_h" />
  │     └── <ToolButton type="opening_selector" />
  ├── <CADViewportSVG>                   // Lienzo principal vectorial en modo Dual
  │     ├── <GridBackgroundOverlay />    // Cuadrícula métrica milimétrica
  │     ├── <OuterFrameMesh />           // Renderizado de marco exterior en SVG
  │     ├── <MullionsLayer />            // Travesaños y postes con tacones de testa
  │     ├── <SashesLayer>                // Hojas móviles con solapes y perfiles
  │     │     ├── <SashProfilesVector />
  │     │     ├── <DINOpeningLines />    // Triángulos de giro y basculación
  │     │     └── <HardwareHandleGizmo />// Manilla vectorial con eje de rotación
  │     ├── <GlassesLayer />             // Cristales con shader de tinte sutil
  │     └── <DimensionsOverlay>          // Capa de cotas interactivas
  │           ├── <CotaWidthBox />
  │           ├── <CotaHeightBox />
  │           └── <CotaSplitOffsetBox />
  └── <DockableInspectorPanel>           // Panel lateral dockable estilo Adobe (320px)
        ├── <AccordionDimensions />      // Inputs numéricos directos (W, H, Offset)
        ├── <AccordionProfileSystem />   // Selector de serie, color y pérdidas
        ├── <AccordionGlazing />         // Matriz junquillo-vidrio
        ├── <AccordionHardwareKits />    // Selector y reglas de herrajes normalizados
        ├── <AccordionInspector />       // Semáforo y hallazgos con botón 1-clic fix
        └── <WorkshopApprovalBar />      // Botón primario verde para generar OT
```



<!-- FIN DE PRD-FRONTEND-APIS-COMPONENTS.md -->

---



<!-- INICIO DE PRD-ANIMATIONS-INTERACTIONS.md -->


# PRD-ANIMATIONS-INTERACTIONS: MICRO-INTERACCIONES Y FÍSICA CAD (v1.0)
**Estado:** Bloqueado / Congelado  
**Norma de Interacción:** 60 FPS mínimos en rendering SVG, Curvas de Aceleración Industrial, Snapping Magnético.

---

## 1. Tokens de Animación y Curvas de Aceleración

Prohibido el uso de animaciones rebotantes o "bouncy" decorativas. Toda transición es rápida, seca y precisa:

```css
/* Curva estándar Adobe: Inicio rápido y desaceleración suave */
--ease-adobe-cad: cubic-bezier(0.16, 1, 0.3, 1);

/* Tiempos de transición */
--duration-instant: 75ms;   /* Feedback de click, hover en botones */
--duration-fast:    150ms;  /* Despliegue de accordions, popovers, tooltips */
--duration-normal:  250ms;  /* Transición de cotas, reacomodo de vanos */
--duration-modal:   200ms;  /* Entrada/Salida de diálogos y drawers */
```

---

## 2. Física de Navegación del Viewport CAD

1. **Zoom Centrado en Cursor:**
   - Control: Rueda del ratón (`wheel`) o gesto *pinch-to-zoom* en trackpad.
   - Rango: $20\%$ ($0.20\times$) a $500\%$ ($5.0\times$).
   - Fórmula: El punto bajo el puntero $(X_{mouse}, Y_{mouse})$ permanece estacionario en pantalla tras recalcular el `scale` y los offsets.
2. **Desplazamiento (Pan):**
   - Disparador: Clic con botón central de la rueda, o tecla `Espacio` presionada + arrastre del botón izquierdo.
   - Cursor: `cursor: grab` $\rightarrow$ `cursor: grabbing`.
3. **Ajuste Automático a Pantalla (Zoom-to-Fit):**
   - Atajo: Tecla `F` o botón *"Encuadrar"*.
   - Transición: $250\text{ ms}$ con `--ease-adobe-cad`, dejando un margen perimetral fijo de $48\text{ px}$.

---

## 3. Algoritmo de Snapping Magnético de Divisiones

Al arrastrar un poste o travesaño con el ratón:
1. **Puntos Magnéticos de Atracción:**
   - **Centro exacto del vano ($50.0\%$ / $50.0\%$):** Rango de atracción de $\pm 12\text{ px}$ en pantalla. Se activa una línea guía punteada cian con halo.
   - **Incrementos de $10\text{ mm}$ y $50\text{ mm}$:** Redondeo numérico automático para cortes estándar de taller.
2. **Restricción de Seguridad Mínima ($250.00\text{ mm}$):**
   - Si el operario intenta arrastrar una división dejando un vano libre menor a $250\text{ mm}$, la línea se detiene bruscamente y la cota cambia temporalmente a color carmesí `#FF1744`.

---

## 4. Micro-Interacciones de Corrección en 1 Clic

Al presionar el botón `[⚡ Corregir en 1 Clic]` en el inspector técnico:
1. El componente corregido en el canvas (e.g. la hoja con sobrepeso) emite un pulso visual de destello esmeralda `#00C853` de $300\text{ ms}$.
2. El semáforo del panel superior realiza una transición de rojo a verde en $150\text{ ms}$.
3. El botón principal *"Aprobar para Taller"* se desbloquea inmediatamente iluminándose con sombra esmeralda.



<!-- FIN DE PRD-ANIMATIONS-INTERACTIONS.md -->

---



<!-- INICIO DE SCREENS_SPECIFICATION_S01_S28.md -->


# ESPECIFICACIÓN CANÓNICA DE PANTALLAS (S01 – S28) (v1.1.2)
**Estado:** Bloqueado / Congelado  
**Total Pantallas:** 28 pantallas completas  
**Stack UI:** React 18 + Tailwind CSS + TanStack Query + Zustand

---

## Índice y Mapeo de Rutas de Pantallas (S01 a S28)

| ID | Nombre de Pantalla | Ruta Frontend | Roles con Acceso |
|---|---|---|---|
| **S01** | Inicio de Sesión y Magic Link | `/login` | Público / Todos |
| **S02** | Configuración de Organización (Onboarding) | `/onboarding` | OWNER |
| **S03** | Dashboard Operativo y KPIs de Taller | `/dashboard` | OWNER, ESTIMATOR, WORKSHOP_MANAGER |
| **S04** | Listado de Proyectos y Cotizaciones | `/projects` | OWNER, ESTIMATOR, WORKSHOP_MANAGER |
| **S05** | Detalle de Proyecto y Grilla de Vanos | `/projects/:id` | OWNER, ESTIMATOR, WORKSHOP_MANAGER |
| **S06** | Editor 2D / Canvas SVG Paramétrico | `/projects/:id/positions/:posId/edit` | OWNER, ESTIMATOR |
| **S07** | Inspector Técnico y Corrección en 1 Clic | Modal en `/positions/:id/edit` | OWNER, ESTIMATOR |
| **S08** | Explosión BOM y Despiece Milimétrico | `/projects/:id/bom` | OWNER, ESTIMATOR, WORKSHOP_MANAGER |
| **S09** | Gestión de Listas de Costo y Precios | `/pricing/cost-lists` | OWNER |
| **S10** | Vista Previa y Congelación de Cotización PDF | `/projects/:id/quote-preview` | OWNER, ESTIMATOR |
| **S11** | Orden de Trabajo de Taller (OT) | `/orders/ot/:id` | OWNER, WORKSHOP_MANAGER |
| **S12** | Visor 3D Esquemático de Ventana | `/viewer-3d/:posId` | Todos / Enlace Público |
| **S13** | Catálogo de Perfiles, Series y Kits de Herrajes | `/catalogs/systems` | OWNER, WORKSHOP_MANAGER |
| **S14** | Compilador de Catálogos Asistido por IA | `/catalogs/compiler` | OWNER |
| **S15** | Matriz Junquillo–Vidrio | `/catalogs/systems/:id/glazing` | OWNER, WORKSHOP_MANAGER |
| **S16** | Inventario y Registro de Retazos QR | `/inventory/offcuts` | WORKSHOP_MANAGER |
| **S17** | Panel de Certificado de Fabricabilidad | `/quality/certificates/:id` | OWNER, ESTIMATOR |
| **S18** | Bandeja de Entrada Omnicanal (Email/WA) | `/inbox` | OWNER, ESTIMATOR |
| **S19** | Optimizador y Mapa de Corte 1D / Compras | `/orders/ot/:id/cutting-plan` | WORKSHOP_MANAGER |
| **S20** | Billetera y Consumo de Créditos IA | `/settings/wallet` | OWNER |
| **S21** | Consola de Comandos NLP y Diff Preview | Drawer flotante en S06 | OWNER, ESTIMATOR |
| **S22** | Personalizador de Plantillas PDF | `/settings/templates` | OWNER |
| **S23** | Gestión de Usuarios y Roles de Taller | `/settings/team` | OWNER |
| **S24** | Suscripción y Facturación (Starter / Profesional / Business / Business 2x) | `/settings/billing` | OWNER |
| **S25** | Configuración General y Políticas RLS | `/settings/general` | OWNER |
| **S26** | Portal Público de Firma de Cotizaciones / Vista Instalador | `/p/quote/:uuid` | Cliente Final / INSTALLER |
| **S27** | Intérprete Multimodal de Planos OCR | `/ai/extract-positions` | OWNER, ESTIMATOR |
| **S28** | Cola de Moderación de Catálogo Global | `/admin/queue` | SUPERADMIN |



<!-- FIN DE SCREENS_SPECIFICATION_S01_S28.md -->

---



<!-- INICIO DE PLAN_SHOTS.md -->


# PLAN DE EJECUCIÓN SHOT-01 → SHOT-24 — DEKOPEN (v1.1.2)

> **Nota de nomenclatura:** Los shots se numeran **SHOT-01…SHOT-24** (mayúscula + guion) para no colisionar con las pantallas S01–S28. Este documento es la tercera y última pieza de la biblia: PRD v1.1.0 (contrato) → Biblia v1.1.2 (especificación) → **este plan (ejecución)**. A partir de aquí, ninguna decisión se toma en caliente: si el builder encuentra un vacío, aplica la Regla 20 (`[PENDIENTE-DECISIÓN]`), nunca improvisa.

---

## 1. Principios Operativos (No Negociables)

1. **Un shot a la vez, en orden.** Prohibido adelantar shots. Cada shot consume su PRD fuente bloqueado y nada más.
2. **El shot no cierra sin su gate completo.** Si el gate falla, se corrige dentro del shot — la deuda técnica no viaja al siguiente shot.
3. **Demo semanal al fundador.** El fundador es el usuario real: cada viernes, flujo funcionando en su máquina. Si no se puede demostrar, el shot no avanzó.
4. **Un PR por shot, tag `shot-XX`.** El merge requiere el DoD de la Regla 19 (Constitución) + el gate específico del shot.
5. **Los checkpoints de negocio (SHOT-12, SHOT-18, SHOT-21) requieren decisión explícita del fundador** para abrir el cobro. La IA nunca abre un plan.

---

## 2. Pre-requisitos del Fundador (Antes del SHOT-01, Día 0)

| # | Requisito | Por qué |
|---|---|---|
| **P1** | Cuentas: GitHub, Supabase Pro, Railway, Vercel, Linear, Cloudflare R2, PostHog, Intercom/Fin, Resend | Infraestructura base del stack D8–D28 |
| **P2** | Cuenta Flow.cl + credenciales sandbox | SHOT-11 |
| **P3** | Dominios: `dekopen.com`, `app.dekopen.com`, `dekopenmail.com` + DNS | D25 |
| **P4** | Iniciar trámite **SpA Chile** (contador) | D4 — antes del primer cobro, no bloquea build |
| **P5** | Ficha técnica Pro6004 + perfil físico + calibrador + balanza | Sign-off G-Pro1 (SHOT-12) |
| **P5-bis** | Cuenta Paddle sandbox (crear pre-semana 15) | SHOT-18 |
| **P6** | Este documento + Biblia v1.1.2 cargados en Notion y como fuente de Fin | Base de conocimiento |
| **P7** | **Tarea Fundador Semanas 8–9 (No-Code):** Landing en Framer con pricing v1.1 + waitlist + página de términos legales "humano aprueba" (con abogado, en paralelo a SpA) | Aterriza Go/No-Go 8 antes de SHOT-11 y SHOT-18 |

---

## 3. Insight de Resiliencia y Ruta Crítica

> [!TIP]
> **Ruta Crítica Resiliente:** El plan Starter solo necesita **G1 a G7**. Los casos complejos G8, G9, G11 y G12 (correderas 3-4H, puerta doble, gran formato) pueden deslizar a Fase 2 sin bloquear el ingreso de dinero en Semana 10.
> **Ruta Crítica:** `SHOT-01 → SHOT-02 → SHOT-03 (G1-G4) → SHOT-04 → SHOT-05 → SHOT-06 (SLIDING_2L/DOOR/AWNING + G5-G7) → SHOT-07 → SHOT-08 → SHOT-09 → SHOT-10 → SHOT-11 → SHOT-12`. Si una semana se complica, se recorta primero G9/G11/G12 de SHOT-06, pero **jamás** G5/G6/G7 ni la resolución de `hardware_kits`.

---

## 4. Tabla Maestra de Shots (v1.1.2)

| Shot | Fase / Sem | PRD Fuente | Entrega Principal | Gate de Cierre |
|---|---|---|---|---|
| **SHOT-01** | 0 · s1 | PRD-00 | Monorepo + CI + Constitución aplicada | Pipeline verde sobre stubs: ruff + mypy + pytest + vitest + build en CI, branch protection |
| **SHOT-02** | 0 · s1–2 | PRD-02 (+Enm. 1 & F1) | DDL completo + `hardware_kits` + RLS + tests aislamiento (Supabase CLI en CI) | SQL aplica en Supabase limpio; test tenant-A≠tenant-B pasa; seed Demo 60 visible global; `payment_events`/`credit_ledger`/`hardware_kits` existen |
| **SHOT-03** | 0 · s2–3 | PRD-01 §2–4 (+M9, M5) | Engine núcleo: models, geometry FIXED/TURN/TILT_TURN/MULLION, BOM base | `pytest engine/`: **G1, G2, G3, G4 en 0.00**; G8/G9/G11/G12 en xfail declarado |
| **SHOT-04** | 0 · s3 | PRD-03 §1, PRD-19 §3 | Auth + tenancy + API skeleton DRF/JWT/OpenAPI + PostHog base + shell app ADOBE dual | Magic link E2E; TOTP owner; OpenAPI $\rightarrow$ TS client autogenerado en CI; PostHog captura eventos base; shell navegable claro/oscuro |
| **SHOT-05** | 0 · s3 | PRD-04, ADOBE, ANIM | Canvas 2D mínimo (fijo + cotas) | Dibuja G1 en pantalla = números del engine (<300 ms); cota editable por teclado; snapping |
| **SHOT-06** | 1 · s4–5 | PRD-01 completo, F1 | Engine total: SLIDING_2L/3L/4L, DOOR_ENTRY, DOOR_DOUBLE, AWNING, monoriel, resolución `hardware_kits`, peso+fallback, pricing puro | **G5, G6, G7, G8, G9, G11, G12 pasan 0.00** (G10 sigue xfail); test CI de `golden_example.json` generado por el engine bit a bit |
| **SHOT-07** | 1 · s5–6 | PRD-01 §6, PRD-07, ANIM | Corte 1D BFD + Inspector R01–R14 + panel inspector | **G7 (puerta multipunto) en 0.00**; test optimizador: pedido Proline barras 5.800m con SKU comercial $\ne$ lista corte taller; inspector bloquea OT en rojo; fix-1-clic aplica diff |
| **SHOT-08** | 1 · s6–7 | PRD-05, PRD-02 (audit) | Precios 5 modos + listas costo + `price_audit_logs` | 5 modos con tests; gobernanza descuentos (margen negativo bloqueado); **cada mutación de precio genera fila de auditoría (test)** |
| **SHOT-09** | 1 · s7–8 | PRD-06, S19 | DOC-01…DOC-07 (WeasyPrint + openpyxl) + Pantalla S19 (Pedidos proveedor) | PDF/Excel/OT/corte/checklist/informe con **BOM hash idéntico entre todos**; storage firmado 3600 s; S19 renderiza lista de compra |
| **SHOT-10** | 1 · s8–9 | PRD-02, S02–S05, S08, S12, S13, S15, S16 | Flujo proyectos + versiones + clonación + **catálogos manuales (S02, S12, S13, S15, S16)** | Autómata de estados; freeze REV-A congela snapshot; editar enviada $\rightarrow$ REV-B; CRUD manual de series, junquillos y kits de herraje funcional para el fundador |
| **SHOT-11** | 1 · s9–10 | PRD-03 §2–5, PRD-19 §2, Enm. 1 | Billing Flow + créditos + trial + **deploy producción + Uptime alerts** | Checkout sandbox Flow; webhook idempotente (reintento$\ne$doble); débito transaccional ledger; trial 7d/500 cap; **dump cifrado R2 + simulacro restauración documentado**; alertas Railway activas |
| **SHOT-12** | 1 · s10 | Todo Fase 1 | **Starter end-to-end + validación fundador** | **Gate-N:** fundador cotiza 10 trabajos reales en paralelo a NuveraPro sin perder en cortes ni pedido Proline $\rightarrow$ **sign-off G-Pro1**. Checkpoint: se abre cobro Starter |
| **SHOT-13** | 2 · s11 | PRD-03 §4, PRD-08 §3, F7 | AI Gateway + router `ai_routes` + semáforo + auditoría IA (costos recalibrados T6/T8/T9) | Toda tool audita ANTES de aplicar (payload, hash, retención); débito con cap; semáforo 90/70; fallback de modelo probado; T6=25+2, T8=50, T9=30+2 |
| **SHOT-14** | 2 · s11–12 | PRD-08 (+M1) | Compilador T6 + preguntas T4 + G sintéticos | **Los 4 fixtures (VEKA/Aluplast/Rehau/Proline) parsean a ficha v1 y validan contra engine 0.00**; serie nueva exige G-case mínimo antes de uso |
| **SHOT-15** | 2 · s12–13 | PRD-09 | OCR T1 + pantalla S27 split-screen | **PDF 8 vanos $\rightarrow$ borrador revisable < 5 min humanos**; anclas bidireccionales; celdas rojas bloquean importación |
| **SHOT-16** | 2 · s13–14 | PRD-10 | Comandos T2/T3/T5 + modal diff + undo sagrado | "20% ganancia" recalcula con preview antes/después; Cmd+Z revierte; **T3 jamás escribe número** (solo diff $\rightarrow$ engine) |
| **SHOT-17** | 2 · s14–15 | PRD-11 | Plantillas PDF 3 slots + bloques protegidos | Re-estiliza sin reescribir números (test: totales intactos tras CSS loco); restaurar original 1 clic; CSP |
| **SHOT-18** | 2 · s15–16 | PRD-18, PRD-03 | Paddle Global (USD MoR) + MP stub + página pricing + Founding 50 | Checkout USD sandbox Paddle; toggle anual default; **checkpoint: Profesional se abre a cobro** tras verificar go/no-go 2, 4, 5, 8 (landing legal s8-9), 9, 10 |
| **SHOT-19** | 3 · s17–18 | PRD-12 | 3D R3F + link `/view/` | PNG + link read-only **sin costos ni despiece en el bundle**; cinemática 3 aperturas; si no llega a nivel Apple $\rightarrow$ se mantiene 2D (criterio §7.9) |
| **SHOT-20** | 3 · s18–20 | PRD-13, S28 | Catálogo global + cola admin (Pantalla S28) | Flujo solicitud $\rightarrow$ revisión $\rightarrow$ publicación sin precios; **test: admin no puede consultar costos ajenos** (blindaje) |
| **SHOT-21** | 3 · s20–22 | PRD-14 | Certificado T8 doble ciego + DOC-08 + QR | Modelos distintos obligatorios; árbitro 100% concordancia $\rightarrow$ sello; discrepancia $\rightarrow$ flag; **checkpoint: Business y Business 2x abren cobro** |
| **SHOT-22** | 3 · s22–24 | PRD-15 parcial, PRD-17 parcial | Comparador T10 + bandeja email (SendGrid) | V1 vs V2 diff correcto; email $\rightarrow$ inbound_request $\rightarrow$ Huey $\rightarrow$ borrador |
| **SHOT-23** | 4 · m7 | PRD-15, PRD-19 §4 | Autopilot Max T9 + Fin + PostHog | Salida SIEMPRE DRAFT (test de contención); **Fin responde las 20 preguntas (Gate 6)**; embudos PostHog activos |
| **SHOT-24** | 4 · m7–9 | PRD-16, PRD-17, PRD-01, S26 | Retazos QR + WhatsApp + **G10 monoriel completo** + PT-BR + Pantalla S26 (Vista instalador) | G10 0.00 (sale de xfail); ciclo retazo completo (RESERVED $\rightarrow$ CONSUMED); i18n pt-BR; portal S26 en solo lectura para instalador |

---

## 5. Mapa de los 10 Go/No-Go → Shots

| Go/No-Go | Se cierra en |
|---|---|
| **1 · G-cases verdes + sign-off físico** | SHOT-06 (verde) + SHOT-12 (sign-off G-Pro1) |
| **2 · 5 proyectos reales fabricados sin desvío** | Piloto s12–16 (fundador + 2 talleres aliados), verificado antes de SHOT-18 |
| **3 · Documentos consistentes (BOM hash)** | SHOT-09 |
| **4 · Usuario nuevo cotiza sin llamada** | Beta externa s14–16, verificado antes de SHOT-18 |
| **5 · Cap de créditos anti-loop** | SHOT-11 + SHOT-13 |
| **6 · Fin responde 20 preguntas** | SHOT-23 |
| **7 · Backup restaurado en ensayo** | SHOT-11 |
| **8 · Términos "humano aprueba" publicados** | Tarea Fundador Semanas 8–9 (Framer / Legal) |
| **9 · Checkout funciona** | SHOT-11 (Flow) + SHOT-18 (Paddle) |
| **10 · Débito de créditos idempotente** | SHOT-11 (test de reintento en staging) |

---

## 6. Prompt Ejecutable para SHOT-01 (Copiar y Pegar al Builder)

```
[CONSTITUTION.md v1.1.2 — 21 reglas vigentes]
[Plan de Ejecución — SHOT-01 de 24: Monorepo, CI y Tooling Fundacional]

CONTEXTO BLOQUEADO:
- PRD-00 v1.1.2 (Arquitectura general, stack D8–D28)
- CONSTITUTION.md v1.1.2 (Reglas normativas 1 a 21)

TAREA (alcance EXACTO — nada fuera de esto):
1. Estructurar el monorepo unificado:
   /engine        (Paquete Python puro, pyproject.toml, pytest, ruff, mypy)
   /backend       (Django 5.1 LTS + DRF 3.15 + drf-spectacular + pytest-django)
   /frontend      (React 18 + Vite + Tailwind CSS + TypeScript 5.6 + Vitest)
   /docs          (Documentación bloqueada v1.1.2)
2. Configurar Tooling y Linters:
   - Python: ruff (linter + formatter), mypy con tipado estricto para /engine.
   - Frontend: ESLint, Prettier, TypeScript strict mode (`tsconfig.json`).
3. Crear Pipeline de CI en GitHub Actions (.github/workflows/ci.yml):
   - Job 1: Lint & Typecheck (ruff check, mypy engine, tsc --noEmit).
   - Job 2: Test Suite (pytest engine, pytest backend, vitest run).
   - Job 3: Frontend Build (npm run build).
4. Branch Protection Rules documentadas en README.

GATE DE CIERRE (debe pasar íntegro al 100%):
$ ruff check . && mypy engine/ && pytest engine/ -q && pytest backend/ -q && npx vitest run && npm run build
Pipeline verde en CI sobre stubs y branch protection activa.
```



<!-- FIN DE PLAN_SHOTS.md -->

---



<!-- INICIO DE STACK_APLICACIONES_Y_SERVICIOS.md -->


# STACK OFICIAL DE MODELOS Y AI ROUTER 2026 — DEKOPEN (v1.2)
**Fecha:** 30 de Agosto de 2026  
**Estado:** Bloqueado / Congelado  
**Filosofía:** Nombres de marca propios (White-label), 99% de operaciones sobre GPT 5.6 Luna xHigh-Max (eficiente y ultra-rápido), activación explícita ("Modo Titan / Ultra-Ingeniería") para modelos pesados (Sol / Kimi k3), y pasarela internacional vía **Paddle (Merchant of Record - MoR)**.

---

## 1. Arquitectura del AI Gateway y Nombres Propios de Marca

El usuario final y los clientes de los talleres **jamás ven nombres comerciales de proveedores de IA** ("GPT", "Gemini", "OpenAI", "Kimi"). La interfaz expone la suite de marca propia de Dekopen con tres niveles de potencia:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                DEKOPEN AI INTELLIGENCE SUITE                                     │
├───────────────────────────────┬──────────────────────────────────┬───────────────────────────────┤
│ ⚡ DEKOPEN NEURAL CORE™       │ 👁️ DEKOPEN VISION CAD™           │ 🔬 DEKOPEN TITAN ENGINE™      │
│ (99% de las Operaciones)      │ (Visión y Planos Multimodal)     │ (Modo Ultra-Ingeniería / Opt) │
├───────────────────────────────┼──────────────────────────────────┼───────────────────────────────┤
│ Backend: GPT 5.6 Luna xHigh   │ Backend: Gemini 3.7 High/GLM 5.3 │ Backend: GPT 5.6 Sol / Kimi k3│
│ Consumo: 1x (Ultra eficiente) │ Consumo: 2x (Solo con imágenes)  │ Consumo: 5x–10x (Bajo demanda)│
│ Para: Comandos, diffs, cotizar│ Para: OCR planos PDF y cuadros   │ Para: Catálogos 100p / Mega QC│
└───────────────────────────────┴──────────────────────────────────┴───────────────────────────────┘
```

---

## 2. Matriz de Enrutamiento Inteligente (AI Router)

| Nombre de Marca en UI | Nivel de Potencia / Modo | Backend Real | Casos de Uso Exclusivos | Consumo de Créditos |
|---|---|---|---|:---:|
| **Dekopen Neural Core™** | **Estándar (Default 99%)** | `gpt-5.6-luna-xhigh-max` | Comandos NLP (T2/T3), árbol paramétrico, explicaciones de taller (T5), cálculo comercial, semáforo y cotizador rápido (T9). | **Bajo** (1 a 4 cr) |
| **Dekopen Vision CAD™** | **Visión Multimodal** | `gemini-3.7-high` / `glm-5.3` | Se invoca **exclusivamente** al subir archivos visuales: extracción de vanos en planos arquitectónicos (T1) y reconocimiento de perfiles. | **Medio** (10 cr / plano) |
| **Dekopen Titan Engine™** | **Ultra-Ingeniería (Max Effort)** | `gpt-5.6-sol` | **Solo activable por el usuario con toggle explícito** en UI ("Activar Razonamiento Titan") para resolver proyectos de extrema complejidad o estructuras especiales. | **Alto** (15 a 50 cr) |
| **Dekopen Matrix Reader™** | **Catálogos Masivos (Long Context)** | `kimi-k3` | **Solo con toggle explícito** al compilar catálogos técnicos de más de 50 páginas con cientos de matrices de junquillos. | **Por página** ($25 + 2\text{ cr/pág}$) |

---

## 3. Pasarelas de Pago Multi-Región

| Región | Pasarela | Rol | Moneda | Razón de Elección |
|---|---|---|---|---|
| **Chile** | **Flow.cl** | Pasarela Directa | **CLP** | Medios de pago chilenos (Webpay, Khipu, Servipag) y emisión obligatoria de DTE / Factura Electrónica. |
| **Internacional (Global)** | **Paddle** | **Merchant of Record (MoR)** | **USD** | **Cero fricción fiscal:** Paddle recauda, declara y paga automáticamente los impuestos (Sales Tax en EE. UU., IVA/VAT en Europa y LatAm). |

---

## 4. UI/UX: Selector de Potencia en el Canvas CAD

En la barra de estado superior del Canvas 2D (Pantalla S06) y en la configuración de la Billetera (S20):

```
+----------------------------------------------------------------------------------------------------+
| MOTOR DE IA: [ (•) Dekopen Neural Core (Rápido)  |  ( ) Modo Titan Ultra-Ingeniería (Max Effort) ]  |
| ⚡ Modo Neural activo: 99.4% precisión matemática • 1.420 créditos disponibles                     |
+----------------------------------------------------------------------------------------------------+
```

---

## 5. Protocolo de Protección contra Desperdicio de Tokens (Zero-Waste)

Para garantizar un consumo mínimo de tokens tanto en desarrollo (Codex) como en la aplicación en producción (SaaS):

1. **Cálculos Matemáticos a $0 Token:** Ningún corte, medida, vidrio o cálculo de rentabilidad pasa por un LLM. Todo es procesado en microsegundos por el motor en Python `/engine`.
2. **Bloqueo Preventivo de Saldo Cero:** El backend verifica y bloquea el saldo en `credit_ledger` *antes* de enviar cualquier request a la API de OpenAI/Google. Si el saldo es 0, no se realiza la llamada HTTP.
3. **Payloads Estrictos con `max_output_tokens`:** Las respuestas de las Tools (T1 a T12) están forzadas a JSON estructurado y conciso (e.g., T2 devuelve ~50 tokens de diff, jamás párrafos explicativos innecesarios).
4. **Gating Visual:** Modelos multimodales (`Gemini 3.7 High`) se invocan **únicamente** cuando se adjunta un archivo PDF/imagen; las peticiones de texto plano se enrutan a modelos ultralivianos.
5. **Anti-Loop Circuit Breaker:** Cualquier fallo en OCR o NLP tiene un límite estricto de **1 reintento**. Prohibidos los bucles de llamadas infinitas.
6. **En Desarrollo (Codex):** El agente utiliza contexto JIT (lee solo el PRD del shot actual, ~2k tokens) y realiza ediciones quirúrgicas de líneas específicas en lugar de reescribir archivos enteros.

---

## 6. Plantilla de Variables de Entorno (`.env.example`)

```env
# ==============================================================================
# DEKOPEN AI GATEWAY & BILLING 2026 — VARIABLES DE ENTORNO
# ==============================================================================

# Core Backend
ENVIRONMENT=development
SECRET_KEY=django-insecure-change-this-in-production-key-seed-dekopen-2026
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,api.dekopen.com,backend-production.up.railway.app
CORS_ALLOWED_ORIGINS=http://localhost:5173,https://app.dekopen.com

# Supabase Pro (PostgreSQL 16 con RLS + Auth + Storage)
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
SUPABASE_URL=https://[PROJECT_REF].supabase.co
SUPABASE_ANON_KEY=eyJhbGciOi...anon_key
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOi...service_role_key
SUPABASE_JWT_SECRET=supabase-jwt-signing-secret-here

# Supabase Storage Buckets
SUPABASE_STORAGE_BUCKET_DOCS=dekopen-documents
SUPABASE_STORAGE_BUCKET_PLANS=dekopen-blueprints
SUPABASE_STORAGE_BUCKET_CATALOGS=dekopen-catalogs

# AI Gateway 2026 (99% Default: GPT 5.6 Luna xHigh-Max / Vision: Gemini 3.7 / Opt-in: Sol & Kimi)
OPENAI_API_KEY=sk-proj-your-openai-key-here
AI_MODEL_PRIMARY_NEURAL=gpt-5.6-luna-xhigh-max
AI_MODEL_TITAN_SOL=gpt-5.6-sol

GOOGLE_AI_API_KEY=AIzaSy-your-google-ai-key-here
AI_MODEL_VISION_CAD=gemini-3.7-high
GLM_API_KEY=glm-your-key-here
AI_MODEL_FALLBACK_VISION=glm-5.3

KIMI_API_KEY=kimi-your-key-here
AI_MODEL_TITAN_CATALOG=kimi-k3

AI_DEFAULT_EFFORT_LEVEL=neural_standard

# Payments: Flow.cl (Chile - CLP)
FLOW_API_KEY=flow_sandbox_api_key
FLOW_SECRET_KEY=flow_sandbox_secret_key
FLOW_API_URL=https://sandbox.flow.cl/api
FLOW_WEBHOOK_SECRET=flow_webhook_secret

# Payments: Paddle Global MoR (USD - Taxes/VAT automatizado)
PADDLE_ENVIRONMENT=sandbox
PADDLE_API_KEY=paddle_sandbox_api_key
PADDLE_WEBHOOK_SECRET=paddle_sandbox_webhook_secret
PADDLE_CLIENT_TOKEN=paddle_sandbox_client_token

# Mailing & Telemetry
RESEND_API_KEY=re_your_resend_api_key
DEFAULT_FROM_EMAIL=notificaciones@dekopen.com
CUSTOMERIO_SITE_ID=customerio_site_id
CUSTOMERIO_API_KEY=customerio_api_key

VITE_POSTHOG_KEY=phc_public_project_api_key
VITE_POSTHOG_HOST=https://us.i.posthog.com
VITE_FIN_INTERCOM_APP_ID=intercom_app_id
JAM_PROJECT_ID=jam_project_token
N8N_WEBHOOK_URL=https://dekopen.app.n8n.cloud/webhook/...
```



<!-- FIN DE STACK_APLICACIONES_Y_SERVICIOS.md -->

---
