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
