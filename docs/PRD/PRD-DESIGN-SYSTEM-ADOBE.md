# PRD: MOTOR VECTORIAL DE ALTA FIDELIDAD Y TEXTURAS ARQUITECTÓNICAS (v1.2)
**Estado:** Bloqueado / Congelado  
**Versión:** 1.2 (Fidelidad Geométrica Real • Texturas Renolit / Anodizados • Uniones PVC 45° vs Aluminio 90°)  
**Hash de Integridad Normativa:** `[HASH-RECALCULAR-AL-EMITIR]`  

---

## 1. Fidelidad Visual Absoluta: PVC Real vs. Aluminio Real

En Dekopen, el dibujo de cada ventana **NO es una representación genérica**. Se construye paramétricamente a partir de los datos exactos del catálogo técnico (`profile_articles`):

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                COMPARATIVA DE FIDELIDAD TÉCNICA                                  │
├───────────────────────────────────┬──────────────────────────────────────────────────────────────┤
│ 🪟 VENTANA DE PVC (Ej: Proline/Veka)│ 🪟 VENTANA DE ALUMINIO (Ej: Xelentia/Alas 20)                 │
├───────────────────────────────────┼──────────────────────────────────────────────────────────────┤
│ • Vista de perfil ancha: 60–70 mm.│ • Vista de perfil esbelta y recta: 35–45 mm.                 │
│ • Uniones esquineras a 45°        │ • Uniones esquineras a 90° mecánicas con corte recto y junta │
│   (Costura de soldadura técnica). │   milimétrica de ensamble con escuadra.                      │
│ • Textura: Foliado Renolit con    │ • Textura: Anodizado metálico satinado o pintura electrostá- │
│   veta natural de madera o mate.  │   tica micro-texturada (Polvo Qualicoat).                    │
│ • Junquillo biselado suave.       │ • Junquillo recto minimalista clipado a presión.             │
└───────────────────────────────────┴──────────────────────────────────────────────────────────────┘
```

---

## 2. Biblioteca de Texturas Arquitectónicas Curadas (Cero Inventos de IA)

En lugar de dejar que la IA invente colores o degradados aleatorios, el sistema utiliza una **biblioteca cerrada de patrones de alta resolución WebP sin costuras (*seamless patterns*)** ubicada en `/assets/textures/`:

| Código de Acabado | Material | Archivo de Textura Curada | Comportamiento Visual |
|---|---|---|---|
| `PVC_WHITE_9016` | PVC | `pvc_white_satin.webp` | Blanco cálido RAL 9016 con sombreado de profundidad en rebajes de cámara. |
| `PVC_FOIL_NOGAL` | PVC | `foil_renolit_nogal.webp` | Foliado original Renolit Nogal con vetas de madera oscura y relieve satinado. |
| `PVC_FOIL_ROBLE` | PVC | `foil_renolit_golden_oak.webp` | Roble Dorado con tinte miel y micro-fibras naturales. |
| `PVC_FOIL_ANTRACITA`| PVC | `foil_renolit_antracita_sand.webp`| Gris Antracita RAL 7016 con micro-textura arenada mate. |
| `ALU_MATE_NATURAL`| Aluminio | `alu_anodized_silver.webp` | Aluminio natural anodizado con sutil reflejo metálico direccional. |
| `ALU_TITANIO_ANOD`| Aluminio | `alu_anodized_titanium.webp` | Tono titanio/champagne satinado de alta gama. |
| `ALU_NEGRO_ELECTRO`| Aluminio | `alu_powder_black_matte.webp` | Negro mate electrostático Qualicoat micro-texturado. |

---

## 3. Renderizado Óptico del Vidrio y Termopanel

El acristalamiento se dibuja con fidelidad arquitectónica real:
1. **Luz de Vidrio Real:** Calculada descontando el ancho exacto del marco, la hoja y el junquillo según la serie seleccionada.
2. **Reflejo Arquitectónico Vectorial:** Gradiente suave a 45° con transparencia ($88\%$ de opacidad) y sutil tinte azul/verdoso técnico que simula el vidrio con tratamiento Low-E y cámara de gas Argón.
3. **Borde Perimetral de Espaciador (*Warm-Edge*):** Sutil línea oscura perimetral de $1\text{px}$ que representa el intercalario térmico de la cámara del termopanel.

---

## 4. Por qué esta arquitectura es la más "Top" y Ligera:

- **100% Vectorial y Nítida:** Pesa menos de $150\text{ KB}$ por ventana, carga instantáneamente en cualquier teléfono y se ve nítida en pantallas 4K/Retina.
- **Exportación Idéntica a PDF:** La misma textura y proporciones geométricas exactas se plasman en el PDF de cotización sin pixelarse al imprimir.
- **Cero Complejidad de Videojuego:** No sobrecalienta el celular del cliente ni la computadora del taller.
