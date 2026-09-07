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
GET  /api/v1/engine/systems/          Discovery read-only de series visibles ['engine', 'systems', orgId]
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

**Contrato normativo SHOT-06, Fase 2 autorizada tras resolver PD-06-19/20:** resultado con
profile_cuts, reinforcements, glasses, panels, hardware_items, leaf_weights y
calculation_hash. Ningún inspector/BFD/pricing/costs/price/audit/OT.
Cortes incluyen material real del artículo y leaf_id nullable; refuerzos, vidrios,
paneles, pesos y hardware incluyen leaf_id nullable. G1–G4 mantienen geometría exacta.
HardwareItem tiene kit_sku,name,qty:int=1,unit="kit",bay_id,leaf_id,contents tipados;
contents no se flattenea y conserva orden del catálogo. LeafWeight publica componentes
PVC/acero/infill/hardware y total a2 HALF_UP, más used_fallback; cálculo interno exacto.
PanelPiece no es GlassPiece. Detalles en PRD-01 y resolución íntegra del plan SHOT-06.

Adapter conserva auth/RLS/organización activa, WHITE aprobado, errores de validación
400, sistema inexistente/no visible404 y contrato diferido422. La implementación
SHOT-04/05 permanece intacta hasta autorización efectiva tras Regla0. Extended sigue
sin geometría ejecutable. OpenAPI y Orval se regeneran después de implementar contrato.
Dimensiones/pesos/áreas son strings Decimal, nunca float; qty entero cuando se define int.

- **Request Payload:**
  ```json
  {
    "system_id": "3067da09-3119-5ad0-a1d5-498cd2dfd753",
    "nominal_width_mm": "1500.00",
    "nominal_height_mm": "1400.00",
    "color": "WHITE",
    "parametric_tree": {
      "id": "root",
      "type": "SPLIT_V",
      "split_offset_mm": "750.00",
      "mullion_profile_sku": "POSTE-V",
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
**Response SHOT-06: contrato de campos (el archivo golden sólo se genera):**

| Campo | Contenido |
|---|---|
| calculation_hash | sha256:<64 lowercase hex>, sin self-hash |
| profile_cuts | SKU,rol,material,length_mm,ángulos,qty,bay_id,leaf_id |
| reinforcements | parent_profile_sku,reinforcement_sku nullable,rol,length_mm,qty,bay_id,leaf_id |
| glasses | bay_id,leaf_id,width_mm,height_mm,area_m2,weight_kg,thickness_net_mm |
| panels | sku,name,bay_id,leaf_id,width_mm,height_mm,area_m2,weight_kg; [] en este request |
| hardware_items | Un HardwareItem por hoja operable con kit/composición; bay_2→KIT-TILT-TURN / Kit Vorne OB 100kg |
| leaf_weights | bay_id,leaf_id,pvc_weight_kg,steel_weight_kg,infill_weight_kg,hardware_weight_kg,total_weight_kg,used_fallback |

Fixture geométrica compuesta intacta:

| Grupo | Valores mm y cantidades |
|---|---|
| FRAME PVC | 1506×2 /1406×2, bay_id null |
| MULLION_V PVC | POSTE-V1280×1, 90/90 |
| SASH PVC bay_2 | 672×2 /1302×2 |
| Beads fijo bay_1 | JQ-10:689×2 /1319×2 |
| Beads OB bay_2 | JQ-14:555×2 /1185×2 |
| Acero FRAME | 1470×2 /1370×2 |
| Acero MULLION | 1270×1 |
| Acero SASH | 636×2 /1266×2 |
| Vidrio fijo | 680×1310; area0.8908; weight17.82; net8.00 |
| Vidrio OB | 546×1176; area0.6421; weight12.84; net8.00 |
| Peso OB exacto/publicado | 26.54632→26.55 kg; kit2.50 persistido; used_fallback=false |

Leaf_id permanece null para las piezas de hoja única de este request. Todos los
cortes salvo mullion tienen45/45. Cantidades, SKU y geometría anteriores se preservan.
G3 standalone publica33.29 kg; golden compuesto bay_2 publica26.55 kg (PD-06-19).
G7 emite PanelPiece y ProfileCut GLAZING_BEAD705.00/1937.00 qty2, sin glass ficticio
y sin sumar beads al peso móvil32.35 (PD-06-20).

**Hash:** objeto {request,response_without_calculation_hash}. UTF-8,
ensure_ascii=False, keys lexicográficas, separators=(",",":"), sin whitespace ni LF;
arrays en orden canónico del motor, Decimal→string, nunca float. SHA-256 hexdigest
minúsculo con prefijo público sha256:. Hash no entra en sus propios bytes.

**Snapshot:** {request,response}, incluyendo calculation_hash en response. UTF-8,
LF, indent=2, sort_keys=True, ensure_ascii=False, exactamente un newline final.
Orden de arrays conserva orden estable de roles/recorrido del engine y hojas L1/L2;
contents mantiene orden persistido. La serialización de Decimal respeta escalas
públicas del contrato; no hace aritmética ni redondeo dimensional que oculte drift.
No se calcula un hash de este documento ni se escribe manualmente un response golden.

**Generación:** make goldgen conserva la interfaz existente y es la única ruta de
escritura. python -m engine.scripts.regenerate_golden --check calcula bytes en memoria
y compara archivo existente; CI usa --check, nunca reescribe. Drift/archivo ausente
produce FAIL. Tests: segunda generación idéntica, mutación de un byte falla, cambio
request/response cambia hash, no self-hash y sin inspector. El request usa UUID real
y POSTE-V explícito; engine matemático no consulta DB ni HTTP.

### 1.2. Discovery read-only de sistemas para SHOT-05

`GET /api/v1/engine/systems/` es el único discovery de catálogo autorizado en
SHOT-05. No constituye CRUD ni persiste una selección. Exige exactamente el mismo
JWT, organización activa, `aal2` para OWNER y contexto RLS que
`POST /api/v1/engine/calculate/`.

Devuelve únicamente sistemas `is_active = TRUE` que sean globales o pertenezcan a
la organización activa, con orden determinista `is_demo DESC`, `code ASC`,
`id ASC`:

```json
{
  "systems": [
    {
      "id": "<uuid>",
      "code": "DEMO_60",
      "name": "Sistema Demo 60mm PVC",
      "is_demo": true
    }
  ]
}
```

Cada elemento expone exclusivamente `id`, `code`, `name` e `is_demo`. Queda
prohibido devolver artículos, costos, precios, hardware, fórmulas o configuración
completa.

En `/projects/demo/positions/g1/edit`, el frontend debe buscar exactamente una fila
`code === "DEMO_60" && is_demo === true`. Cero coincidencias produce el estado
fail-closed `demo_system_unavailable`; más de una produce
`demo_system_ambiguous`. Nunca se selecciona implícitamente el primer elemento y el
UUID de DEMO_60 no se hardcodea como autoridad productiva del navegador.

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
  └── <InspectorModalS07>               // Modal dentro de S06; tabs Inspector y Corte 1D
        ├── <AccordionDimensions />      // Inputs numéricos directos (W, H, Offset)
        ├── <AccordionProfileSystem />   // Selector de serie, color y pérdidas
        ├── <AccordionGlazing />         // Matriz junquillo-vidrio
        ├── <AccordionHardwareKits />    // Selector y reglas de herrajes normalizados
        ├── <AccordionInspector />       // Semáforo y hallazgos con botón 1-clic fix
        └── <WorkshopApprovalBar />      // Botón primario verde para generar OT
```

## SHOT-07 — S07, derivados y fix autorizado

S07 es MODAL de /projects/:id/positions/:posId/edit, superficie demo vigente,
sin ruta /inspector. Tabs Inspector y Corte1D; Pedido muestra SKU comercial;
Plan de corte de taller muestra SKU técnico, barras/cortes, kerf/trims/remanente.
TanStack Query guarda Inspector/BFD remotos; Zustand sólo inputs técnicos,
WorkshopAnnotations y preview diff. No duplicar EngineResult. Light/Dark.

POST /api/v1/engine/inspect/: calculation request, annotations, structural
inputs y mode DESIGN/WORKSHOP_QC. source_calculation_hash coincide con calculate
si geometry completa; nullable en preflight bloqueado. Errores tipados humanos.
POST /api/v1/engine/optimize-cut/: calculation request; server calcula piezas,
carga stock/política y optimiza. No confiar en cortes enviados por navegador.
Devuelve source_calculation_hash sin modificar identidad.
Ambos JWT/org/OWNER aal2/RLS y catálogo server-authoritative.
Calculate conserva exactamente sus siete claves; Inspector/BFD fuera de hash y
golden byte-identical. Contratos detallados en resolución íntegra del plan SHOT07.

R07 fix tipado ADD_BOTTOM_DRAIN_HOLE: width1000 con dos drenajes válidos y centro
ausente propone500. InspectorDiff contiene diff_id/rule_id/target/preconditions/
operations; union discriminada, nunca JSON Patch arbitrario. Preview→clic→validar
precondiciones→draft→calculate→inspect→commit sólo con ambos success; rollback
exacto ante fallo. Reaplicar no duplica y una precondición obsoleta falla sin mutar.
R07 desaparece tras recálculo y hash geométrico sigue igual.
WorkshopReadiness=inspector.production_allowed AND cut_optimization.ok; errores
config/stock/fit deshabilitan gate sin falsificar el semáforo. No OT/persistencia.
