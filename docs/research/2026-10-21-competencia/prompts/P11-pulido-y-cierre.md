# P11 · Pulido final, rendimiento, accesibilidad y cierre

**Rama:** `gpt/dk2-p11-pulido` · **Depende de:** P01–P10 · **Final**

## Objetivo

Dejar DEKOPEN 2 como producto terminado: consistente, rápido, accesible, sin
restos del sistema anterior en el camino normal, documentado y listo para que el
dueño lo revise en su stack local.

## Qué hacer

1. **Recorrido completo por rol** (dueño, vendedor, jefe de taller, operario,
   instalador, cliente del portal) con `testing-framedex`: captura cada pantalla
   a 1440 × 900 y 390 × 844 y corrige todo lo que no cumpla
   `04-experiencia-y-diseno.md` §5 (calidad exigida).
2. **Consistencia del sistema de diseño:** tokens, tipografía, espaciado,
   componentes únicos (una tabla, un inspector, un control segmentado, una
   píldora de búsqueda, un chip de aviso). Elimina estilos heredados y CSS
   huérfano; `scripts/check_guards.py` y la constitución en verde (actualiza la
   constitución donde DEKOPEN 2 la cambió y deja registro en el wiki).
3. **Rendimiento (`web-perf`):** carga inicial, cambio de pantalla, edición en el
   editor, apertura del PDF. Metas: interacción < 100 ms en el editor, pantalla
   lista < 1,5 s en local con datos de prueba grandes.
4. **Movimiento (`review-animations`):** revisa cada animación agregada; reduce o
   elimina lo innecesario; respeta reduced-motion.
5. **Accesibilidad:** contraste AA, foco visible, teclado completo en oficina,
   etiquetas en controles, objetivos ≥ 44 px (≥ 56 px en taller).
6. **Retiro del camino normal:** confirma que Laboratorio/DEMO, jerga y pasos
   manuales de «aplicar precio» no aparecen en ningún flujo normal; las funciones
   avanzadas siguen accesibles desde Empresa › Funciones avanzadas.
7. **Documentación:** `docs/dekopen2/ESTADO.md` final, `docs/GUIA-REVISION.md`
   actualizada para revisar DEKOPEN 2 en local, wiki (`state/current-reality.md`
   con ref verificada), y un resumen de cambios para el dueño en español claro.

## Criterios de aceptación

- [ ] Galería de capturas por rol adjunta a la PR.
- [ ] `make lint typecheck test build` y `make test-db` (o Database Gate en CI) en verde.
- [ ] Prueba de aceptación Proline (P10) en verde.
- [ ] Ninguna palabra prohibida del glosario en la interfaz (guardián).
- [ ] Reporte de `web-perf` con metas cumplidas o explicación de lo pendiente.
