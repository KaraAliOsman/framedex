---
type: concept
status: active
updated: 2026-10-08
volatility: medium
sources:
  - P04 acceptance in docs/redesign/P04-ACEPTACION.md
  - frontend/tests/e2e/editor.spec.ts
  - backend/tests/integration/test_project_operations.py
---

# Editor centrado en el dibujo

La intención del dueño es diseñar desde el lienzo, con cotas editables y
herramientas reconocibles. P04 convierte esa intención en franja compacta,
biblioteca por familias compatibles e inspector por selección. Desde 1280
se acopla; a 1024 se abre como drawer; debajo se conserva lectura, cotas,
precio/navegación sin escritura ni atajo de guardar.

Los cambios usan operaciones tipadas y simuladas por el registro del motor,
con una transacción del historial. Una operación rechazada devuelve el campo
al valor aceptado. La evaluación anterior conserva dibujo durante debounce
pero no autoriza guardar ni mostrar un precio como actual.

Venta indicativa usa el mismo endpoint con `ops=[]` y cantidad entera.
Evalúa sin mutación: producto/diff/fila persistida no cambian. El motor conserva
multiplicación/redondeo. La fuente distingue indicativo de aplicado para emitir.

El comando de tres paños usa `equalize_bays`/`set_opening`: fantasma/Δ antes
de aplicar, historial después. Una respuesta sobre otro diseño/cantidad se
descarta. Biblioteca, popover, menú/pie comparten exclusión de capas; enlaces
conservan el guard de cambios pendientes.

Pan/zoom se acotan sobre dibujo físico, separado del margen de cotas para
ajustar. La prueba de 10.000 px comprueba visibilidad antes de Centrar.
Once campos/lecturas se verifican a 1024×768. La
[aceptación](../../redesign/P04-ACEPTACION.md) conserva los recorridos.

El alcance es interacción/layout. P05 continúa glifos/cotas técnicas, P06
bow/planta y P19 3D. DEMO no acredita fabricación real.
