# ARCHIVED v1.2 — La especificación canónica de UI es S01-S28 + PRD-DESIGN-SYSTEM-ADOBE v1.2. Este documento se archiva para referencia histórica.

# PRD-MAQUETAS: SUITE MAESTRA DE MAQUETAS VISUALES Y LAYOUTS ESTILO ADOBE CAD (v1.1.2)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.1.2 (Congelada y Bloqueada)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  
**Filosofía de Diseño:** Adobe Dark & Light Studio CAD / Engineering Precision (Sin vibe coding, 100% utilitario, modular y legible directamente en texto estructurado).

---

## 1. Gramática Global de Layouts (Shell de Aplicación Estilo Adobe)

Todas las pantallas privadas de la plataforma utilizan el **Desktop CAD Shell Layout** con docking modular:

```
+----------------------------------------------------------------------------------------------------+
| TOPBAR RIBBON (h: 48px) - [Logo Dekopen] [Org: Taller Los Dominicos] [Saldo: 1.420 cr] [TOTP: OK]  |
+-----------+--------------------------------------------------------------------+-------------------+
| TOOLBAR   | ÁREA CENTRAL DE TRABAJO (Viewport CAD Infinito)                    | DOCKABLE PANEL    |
| (w: 52px) |                                                                    | (w: 320px)        |
|           |             [ ← 1500.00 mm (Cota Editable Teclado) → ]             |                   |
| [ ⇱ Move ]|     +---------------------------+---------------------+            | ▼ Accordion 1     |
| [ ┼ Snap ]|     |                           |       / \ (OB)      |            |   Dimensions      |
| [ ⧉ DivV ]| 1400|        PAÑO FIJO          | 1400/     \ (Manilla|            |                   |
| [ ⧈ DivH ]|  mm |        DVH 24mm           |  mm/       \   o    |            | ▼ Accordion 2     |
| [ ◫ Sash ]|     |        680x1310 mm        |   /         \  |    |            |   Profiles & Glass|
| [ 📏 Dim ] |     +---------------------------+---------------------+            |                   |
|           |               [ 750 mm ]                  [ 750 mm ]               | ▼ Inspector Tech  |
|           |                                                                    |   🟢 0 Errores    |
|           |                                                                    |   [ APROBAR OT ]  |
+-----------+--------------------------------------------------------------------+-------------------+
| STATUS BAR (h: 24px) - [Engine: 0.00mm] [Grid: 10mm] [Snap: ON] [Coords: X:750 Y:1400]              |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Maqueta S06: Editor Canvas 2D en SVG Puro (`/positions/:id/edit`)

```
+----------------------------------------------------------------------------------------------------+
| [COT-2026-0142] / Posición 3 (Living) • Fijo + Oscilobatiente (1500 x 1400 mm)  [Recalcular] [Guardar]|
+-------------------+---------------------------------------------------------+----------------------+
| PALETA DE CORTE   | CANVAS VECTORIAL SVG INTERACTIVO                        | INSPECTOR TÉCNICO    |
| (Width: 52px)     |                                                         | (Width: 320px)       |
|                   |          [ ← 1500.00 mm (Click para editar) → ]         |                      |
| [ ⇱ Cursor ]      |     +---------------------------+---------------------+     | Estado: 🟢 APROBADO  |
| [ ┼ Snapping]     |     |                           |       / \ (OB)      |     | 0 Infracciones       |
| [ ⧉ Dividers]     |     |                           |      /   \          |     |                      |
| [ ◫ Sashes  ]     | 1400|        PAÑO FIJO          | 1400/     \ (Manilla| 1400| Peso Hoja:           |
| [ ⎔ Openings]     |  mm |        Vidrio DVH 24mm    |  mm/       \   o    |  mm | [=====>    ] 26.5 kg |
| [ 📏 Measure]     |     |        680x1310 mm        |   /         \  |    |     | Máximo: 100 kg       |
|                   |     |                           |  <-----------+ |    |     |                      |
| [Colores Perfil]  |     +---------------------------+---------------------+     | Precio Venta:        |
| [• Blanco] [Nogal]|               [ 750 mm ]                  [ 750 mm ]    | $218.450 CLP         |
| [• Antracita]     |                                                         | Margen: 35.0% Neto   |
|                   | Atajos: [V] Poste Vert  [H] Travesaño H  [4] Oscilobat  |                      |
| [Deshacer ⌘Z]     | [⌘Z] Deshacer           [⌘Y] Rehacer     [1] Fijo       | [ APROBAR PARA OT  ] |
+-------------------+---------------------------------------------------------+----------------------+
```

---

## 3. Maqueta S27: Intérprete de Planos OCR Split-Screen (`/ai/extract-positions`)

```
+----------------------------------------------------------------------------------------------------+
| DEKOPEN ARCHITECTURAL BLUEPRINT OCR | SCREEN S27            [ 10 CREDITS REMAINING ] [ IMPORT CONF ]|
+----------------------------------------------------+-----------------------------------------------+
| VISOR PLANO CON BOUNDING BOXES BRILLANTES (X,Y)    | EXTRACTED OPENINGS SCHEDULE (8 Detectados)    |
|                                                    |                                               |
| +------------------------------------------------+ | TAG   | DIMENSIONS  | TYPOLOGY  | CONFIDENCE  |
| | Floorplan_Piso1.pdf (Zoom 100%)                | | ----- | ----------- | --------- | ----------- |
| |                                                | | V-01  | 1500 x 1400 | Tilt-Turn | 🟢 98% Conf |
| |   [🟩 V-01: 1500x1400 • 98% Confidence]        | | V-02  | 1800 x 1600 | Casement  | 🟢 94% Conf |
| |   +---------------------------------------+    | | V-03  |  900 x 2100 | SlideDoor | 🟡 82% Conf |
| |   |                                       |    | |                                               |
| |   +---------------------------------------+    | | Glass Spec: Double Glazed Low-E Argon         |
| |                                                | |                                               |
| |   [🟩 V-02: 1800x1600 • 94% Confidence]        | | [ ⚡ APLICAR EXTRACCIÓN AL PROYECTO (Enter) ] |
+----------------------------------------------------+-----------------------------------------------+
```

---

## 4. Maqueta S15: Matriz Junquillo–Vidrio (`/catalogs/systems/:id/glazing`)

```
+----------------------------------------------------------------------------------------------------+
| MATRIZ JUNQUILLO–VIDRIO — SERIE DEMO 60 MM (Canal: 32.00 mm)                [ Guardar Matriz ]     |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
| VIDRIO ESPESOR | EMPAQUETADURA EXT | EMPAQUETADURA INT | JUNQUILLO ANCHO | ARTÍCULO ASIGNADO       |
| -------------- | ----------------- | ----------------- | --------------- | ----------------------- |
|  4.00 mm       | 3.00 mm           | 3.00 mm           | 26.00 mm        | JQ-DEMO-26 (Junquillo)  |
|  6.00 mm       | 3.00 mm           | 3.00 mm           | 24.00 mm        | JQ-DEMO-24 (Junquillo)  |
| 20.00 mm (DVH) | 3.00 mm           | 3.00 mm           | 10.00 mm        | JQ-DEMO-10 (Junquillo)  |
| 24.00 mm (DVH) | 3.00 mm           | 3.00 mm           |  6.00 mm        | JQ-DEMO-06 (Junquillo)  |
| 28.00 mm (DVH) | 3.00 mm           | 3.00 mm           |  2.00 mm        | JQ-DEMO-02 (Junquillo)  |
+----------------------------------------------------------------------------------------------------+
```

---

## 5. Maqueta S28: Cola de Moderación Admin Global (`/admin/queue`)

```
+----------------------------------------------------------------------------------------------------+
| COLA DE MODERACIÓN DE CATÁLOGOS GLOBALES (Superadmin)                            [ Filtro: Pendientes v ]|
+----------------------------------------------------------------------------------------------------+
| SISTEMA SOLICITADO    | TALLER ORIGEN        | PERFILES | JUNQUILLOS | KITS HERRAJE | ACCIÓN       |
| --------------------- | -------------------- | -------- | ---------- | ------------ | ------------ |
| Rehau Euro-Design 70  | PVC Austral SpA      | 14 SKUs  | 6 Rangos   | 8 Kits Vorne | [Revisar QC] |
| Kömmerling 76AD       | Ventanas del Norte   | 18 SKUs  | 8 Rangos   | 12 Kits Roto | [Revisar QC] |
+----------------------------------------------------------------------------------------------------+
| PANEL DE AUDITORÍA Y CONTROL DE PRECIOS:                                                           |
| 🔒 BLINDAJE ACTIVO: Las listas de costos privadas y precios no son accesibles por el moderador.    |
| ✅ VALIDACIÓN REQUERIDA: Tests unitarios de Casos G sintéticos con tolerancia 0.00 mm antes de publicar. |
+----------------------------------------------------------------------------------------------------+
```
