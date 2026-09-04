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

### 3.1. Asignación temporal de alcance — SHOT-05

El algoritmo de §3 conserva íntegramente su semántica de **divisiones**: postes,
travesaños, centro exacto del vano y mínimo de `250.00 mm` se implementan únicamente
en un shot futuro donde `SPLIT`/`MULLION` estén dentro del alcance. No pertenecen a
SHOT-05.

SHOT-05 satisface su gate de snapping exclusivamente al redimensionar las cotas
exteriores de un único `BAY / FIXED`, mediante grips horizontal y vertical:

1. Con Snap ON, la posición de puntero se transforma a candidate mm usando el
   viewport vigente.
2. Se elige el múltiplo de `50 mm` más cercano cuando queda dentro de `±12 px` en
   pantalla; fuera de ese radio se cuantiza al múltiplo de `10 mm` más cercano.
3. Con Snap OFF, el candidate se cuantiza únicamente a `0.01 mm`.
4. Todo desempate usa `ROUND_HALF_UP`; `Math.round()` no es autoridad técnica.
5. El drag sólo produce preview de presentación. `pointerup` envía el candidate al
   engine y únicamente una respuesta 200 consolida la dimensión.

Esta asignación no crea divisiones, no aplica snap a 50% y no aplica el mínimo de
`250 mm` de BAY hijo.

---

## 4. Micro-Interacciones de Corrección en 1 Clic

Al presionar el botón `[⚡ Corregir en 1 Clic]` en el inspector técnico:
1. El componente corregido en el canvas (e.g. la hoja con sobrepeso) emite un pulso visual de destello esmeralda `#00C853` de $300\text{ ms}$.
2. El semáforo del panel superior realiza una transición de rojo a verde en $150\text{ ms}$.
3. El botón principal *"Aprobar para Taller"* se desbloquea inmediatamente iluminándose con sombra esmeralda.
