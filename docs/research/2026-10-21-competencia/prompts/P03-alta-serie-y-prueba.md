# P03 · Alta guiada de serie, lectura del manual y ventana de prueba

**Rama:** `gpt/dk2-p03-alta-serie` · **Depende de:** P01, P02 · **Siguiente:** P04

## Objetivo

Que un taller cargue su serie en **10 minutos**: subir manual y lista de
precios, completar con plantilla, revisar una ventana de prueba y quedar listo
para cotizar. Que la serie verificada quede **protegida por su propio caso dorado**.

Especificación: `03-catalogo-y-calculo.md` §5–§6; `05-agente-ia.md` §1 (doble
lectura) y automatización 4. Mockup: `mockups/Prueba.dc.html`.

## Qué construir

1. **Asistente de alta** (pasos numerados: Serie · Manual · Precios · Ventana de
   prueba · Primera cotización), reanudable, con progreso guardado.
2. **Lectura del manual con IA** (`backend/ingest/`, `backend/jobs/`,
   `backend/ai_gateway/`): PDF/imagen/Excel → tablas pequeñas → **dos
   extracciones independientes** (distinto prompt o distinto recorte) →
   comparar celda a celda → solo las diferencias van a revisión humana. Los
   números se parsean a `Decimal` en código Python, nunca en el modelo. Cada
   valor extraído guarda `origin=MANUAL` con `source_ref` (archivo + página) solo
   después de la revisión humana; antes es una propuesta. Reutiliza la ingesta
   existente si sirve.
3. **Precios desde Excel/CSV** con mapeo de columnas asistido (detectar columnas
   de código, descripción, unidad, precio; previsualizar 10 filas; confirmar).
   El precio es siempre del taller (`origin=WORKSHOP`).
4. **Ventana de prueba:** el usuario elige tipología y medidas (por defecto
   1200 × 1100 abatible); se muestra el despiece del motor junto a una columna
   editable «Según tu manual». Diferencia → botón **Ajustar regla** que propone
   el cambio de regla exacto (p. ej. descuento de hoja −62 → −60) y recalcula.
   Al confirmar: `verified_at`, y se guarda un **caso dorado del tenant**
   (entrada + salida esperada) que se recalcula al editar reglas de la serie; si
   el resultado cambia, la edición muestra el antes/después y pide confirmar.
5. **Fin del alta:** botón **Crear mi primera cotización** que abre la obra
   nueva con esa serie preseleccionada.

## Criterios de aceptación

- [ ] e2e: alta de PRO6004 desde plantilla + Excel de precios de prueba (crea un
      fixture en `frontend/tests/e2e/fixtures/`) + ventana de prueba con una
      corrección → serie MANUFACTURABLE y caso dorado guardado.
- [ ] Prueba de backend de la doble extracción con respuestas del modelo
      simuladas: celdas iguales → aceptadas como propuesta; distintas → en revisión;
      ningún número llega a la base sin pasar por `Decimal` y revisión.
- [ ] Editar una regla que altera la ventana de prueba muestra la diferencia antes de guardar.
- [ ] Capturas comparadas con el mockup; `break-ui` en la tabla de prueba.
- [ ] Todo verde; wiki y ESTADO.md actualizados.
