# P06 · Mesa de la obra y editor de ventana

**Rama:** `gpt/dk2-p06-mesa-obra` · **Depende de:** P05 · **Siguiente:** P07

## Objetivo

El corazón del producto: lista de ventanas, dibujo y un inspector simple en una
sola pantalla, con el total siempre visible y un único botón principal
**Enviar cotización**. Edición directa sobre el dibujo.

Especificación: `04-experiencia-y-diseno.md` §2 (F2) y §3.3. Mockup:
`mockups/Main.dc.html`. Revisa `features/projects/ProjectPages.tsx`,
`ProjectPositionEditor.tsx`, `PositionCollection.tsx`, `features/canvas/`
(`AssemblyEditor.tsx`, `ProductFrontSvg.tsx`, `Product3DScene.ts`,
`StarterGallery.tsx`, `OpeningPalette.tsx`), y el motor de operaciones
(`engine/src/dekopen_engine/design_operations.py`).

## Decisión pendiente del dueño

Mesa de obra + Estudio (`04` §6). Implementa la vista única descrita aquí detrás
de la bandera `obra_vista_unica` **activada por defecto**, manteniendo Estudio
accesible si la bandera se apaga. No borres Estudio en esta fase.

## Qué construir

1. **Layout de tres columnas** (ventanas · dibujo · inspector) con cabecera:
   volver a Obras, nombre de obra y cliente, total IVA incluido, **Pedir a
   DEKOPEN**, **Enviar cotización**. Columna de ventanas con miniatura vectorial,
   nombre, medidas y cantidad; **+ Añadir ventana**.
2. **Nueva ventana:** abre la biblioteca de tipologías de la serie (la serie por
   defecto de la empresa preseleccionada; si no hay, el selector de serie va
   primero, como ya existe). Elegir tipología → medidas → listo.
3. **Dibujo:** cotas editables sobre el dibujo (clic, escribir, Enter; Esc
   cancela); arrastrar montantes/travesaños con la cota en vivo y validación del
   motor en cada gesto; pestañas **2D | 3D** e **Interior | Exterior** en el
   lienzo (el 3D deja de ser panel flotante). Símbolos de apertura DIN como hoy.
4. **Inspector simple:** Serie, Apertura, Ancho, Alto, Vidrio, Color, Cantidad,
   precio de la ventana con desglose (P04) y enlace **Ver despiece y
   materiales**. Lo avanzado (montaje, extras, perfiles específicos, datos de
   fabricación) en una sección plegada «Más opciones».
5. **Avisos del motor como chips** sobre la ventana afectada con la corrección
   propuesta como botón (p. ej. «La hoja pesa 31 kg; el herraje soporta 30 kg ·
   Usar herraje reforzado»). Nada de modales.
6. **Rendimiento:** respuesta del dibujo < 100 ms al editar una cota (cálculo del
   motor en segundo plano con indicador sutil); deshacer/rehacer con Ctrl Z/Y.
7. **Móvil (≥ 390 px):** lista y dibujo apilados, inspector en hoja inferior;
   edición permitida (quitar el bloqueo actual de < 1024 px salvo herramientas
   de dibujo fino, que muestran un aviso claro).

## Criterios de aceptación

- [ ] Captura 1440 × 900 indistinguible en jerarquía del mockup `Main.dc.html`.
- [ ] e2e: crear obra → 3 ventanas (fija, abatible 2 hojas, corredera) con la
      biblioteca → editar una cota en el dibujo → precio y total cambian → chip
      de aviso con corrección aplicada → deshacer.
- [ ] Pruebas de interacción del editor existentes en verde o actualizadas con justificación.
- [ ] `break-ui`: obra de 120 ventanas, nombres largos, medidas extremas.
- [ ] `web-perf` y `review-animations` sobre el editor; reporte en la PR.
- [ ] Todo verde; wiki (`product/editor-canvas.md`, `project-workspace.md`) y ESTADO.md.
