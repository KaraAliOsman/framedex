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

> **Contrato vigente SHOT-04:** este apartado congela el request del adaptador HTTP
> fino sobre el engine aprobado en SHOT-03. El resultado contiene exclusivamente
> `profile_cuts`,
> `reinforcements`, `glasses` y `hardware_items`. Cada corte añade `sku` y
> `bay_id` nullable; cada refuerzo añade `parent_profile_sku`,
> `reinforcement_sku` nullable y `bay_id` nullable. `hardware_items` es `[]`
> y no ejecuta resolución de kits. `calculation_hash` se incorpora en
> SHOT-06 y `inspector` en SHOT-07, fuera de la respuesta actual. Área y
> peso de cada `GlassPiece` se calculan exclusivamente mediante PRD-01
> §3.1.1, conservando el área exacta hasta la cuantización final.
>
> El endpoint sólo ejecuta tipologías soportadas por SHOT-03. Un contrato sintáctico
> válido pero diferido responde `422 unsupported_engine_contract`; un sistema inexistente
> o no visible responde `404 system_not_found`; una entrada inválida responde
> `400 validation_error`. Dimensiones y resultados se serializan como strings decimales,
> nunca como `float`.

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
    "profile_cuts": [
      { "sku": "MARCO",  "role": "FRAME",        "length_mm": "1506.00", "angle_left": "45.0", "angle_right": "45.0", "qty": 2, "bay_id": null },
      { "sku": "MARCO",  "role": "FRAME",        "length_mm": "1406.00", "angle_left": "45.0", "angle_right": "45.0", "qty": 2, "bay_id": null },
      { "sku": "POSTE-V", "role": "MULLION_V",   "length_mm": "1280.00", "angle_left": "90.0", "angle_right": "90.0", "qty": 1, "bay_id": null },
      { "sku": "HOJA",   "role": "SASH",         "length_mm": "672.00",  "angle_left": "45.0", "angle_right": "45.0", "qty": 2, "bay_id": "bay_2" },
      { "sku": "HOJA",   "role": "SASH",         "length_mm": "1302.00", "angle_left": "45.0", "angle_right": "45.0", "qty": 2, "bay_id": "bay_2" },
      { "sku": "JQ-10",  "role": "GLAZING_BEAD", "length_mm": "689.00",  "angle_left": "45.0", "angle_right": "45.0", "qty": 2, "bay_id": "bay_1" },
      { "sku": "JQ-10",  "role": "GLAZING_BEAD", "length_mm": "1319.00", "angle_left": "45.0", "angle_right": "45.0", "qty": 2, "bay_id": "bay_1" },
      { "sku": "JQ-14",  "role": "GLAZING_BEAD", "length_mm": "555.00",  "angle_left": "45.0", "angle_right": "45.0", "qty": 2, "bay_id": "bay_2" },
      { "sku": "JQ-14",  "role": "GLAZING_BEAD", "length_mm": "1185.00", "angle_left": "45.0", "angle_right": "45.0", "qty": 2, "bay_id": "bay_2" }
    ],
    "reinforcements": [
      { "parent_profile_sku": "MARCO",  "reinforcement_sku": null, "role": "FRAME",     "length_mm": "1470.00", "qty": 2, "bay_id": null },
      { "parent_profile_sku": "MARCO",  "reinforcement_sku": null, "role": "FRAME",     "length_mm": "1370.00", "qty": 2, "bay_id": null },
      { "parent_profile_sku": "POSTE-V", "reinforcement_sku": null, "role": "MULLION_V", "length_mm": "1270.00", "qty": 1, "bay_id": null },
      { "parent_profile_sku": "HOJA",   "reinforcement_sku": null, "role": "SASH",      "length_mm": "636.00",  "qty": 2, "bay_id": "bay_2" },
      { "parent_profile_sku": "HOJA",   "reinforcement_sku": null, "role": "SASH",      "length_mm": "1266.00", "qty": 2, "bay_id": "bay_2" }
    ],
    "glasses": [
      { "bay_id": "bay_1", "width_mm": "680.00",  "height_mm": "1310.00",
        "area_m2": "0.8908", "weight_kg": "17.82", "thickness_net_mm": "8.00" },
      { "bay_id": "bay_2", "width_mm": "546.00",  "height_mm": "1176.00",
        "area_m2": "0.6421", "weight_kg": "12.84", "thickness_net_mm": "8.00" }
    ],
    "hardware_items": []
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
