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
