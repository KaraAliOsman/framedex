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
