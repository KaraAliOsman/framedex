---
type: concept
status: active
updated: 2026-10-22
volatility: medium
verified_ref: gpt/dk2-p06a-obra-unica
sources:
  - docs/redesign/captures/dk2-p06a/aceptacion.md
  - P04 acceptance in docs/redesign/P04-ACEPTACION.md
  - frontend/tests/e2e/editor.spec.ts
  - backend/tests/integration/test_project_operations.py
  - docs/redesign/captures/aceptacion-final/ux/error-posicion/produccion-verificacion.json
---

# Editor centrado en el dibujo

## DEKOPEN 2 P06a · edición en la mesa · 22-10-2026

Comprobado en `gpt/dk2-p06a-obra-unica`, sobre P05k `1e1ead31`, con la bandera
`VITE_OBRA_VISTA_UNICA` activa. Este apartado sustituye el límite móvil de la
base histórica de abajo únicamente para la propuesta de mesa única.

Desde 390 px se puede editar cantidad, medidas, apertura, vidrio y color y
guardar mediante el servidor. El inspector es una hoja inferior; lista y dibujo
se apilan. Las herramientas de división fina y acople requieren una pantalla
más amplia, con explicación visible y bloqueo de sus atajos de herramienta.
Permisos y revisiones emitidas conservan la validación del servidor.

El inspector reúne serie, color, cantidad y propiedades de la selección; las
opciones técnicas y datos de fabricación quedan plegados. El precio guardado
abre el desglose de P04 de la posición, evitando confundirlo con otra estimación.
El precio vivo del diseño sin guardar aún requiere la integración simple de P06b.

2D/3D ocupan el mismo espacio del dibujo; Interior/Exterior comparten la cara
de vista. Escape cancela la edición de una cota antes de blur y no despacha
una operación. El resto de cambios conserva simulación tipada, rollback,
undo/redo y rechazo de respuestas obsoletas. No cambia una fórmula ni un catálogo.

No hay transiciones nuevas en edición frecuente. El desplazamiento a los avisos
respeta `prefers-reduced-motion`; el 3D conserva carga diferida. Véanse
[capturas, pruebas y límites de P06a](../../redesign/captures/dk2-p06a/aceptacion.md).

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

El E2E sincroniza cada edición probada con su respuesta real de simulación
(`200`, `valid=true`) antes de comprobar la evaluación vigente y los controles.
La reproducción del fallo CI de P03 (`37915677274`, 09-10-2026) midió
7,4–7,9 s para vidrio/ancho/propuesta en el stack local. Una aserción de
botón de 5 s no representa el término de esa transacción. El recorrido
focalizado pasa en 43,5 s sin retries ni cambiar timeouts globales; conserva
aplicar/deshacer y descartar propuestas de una cantidad anterior.

P20 verifica recuperación ante lectura fallida en `de3e0cba`: Reintentar vuelve
a consultar la misma posición y organización. El error conserva su causa y un
título h1; el diseño tiene una región accesible con h2. El clic no guarda ni
aplica cambios. Las solicitudes de cálculo, preview y simulación se registran
separadas de las escrituras.

La evidencia conserva ocho pares ancho/tema en Vite y ocho en producción,
cada uno con error y recuperación, sin hallazgos, axe, desbordes ni escrituras.
A 390 px, el CSS compartido del portal ya no crea filas implícitas que oculten
el dibujo. A 1024 px, un nombre largo conserva los controles de cabecera dentro
del viewport. Los archivos mantienen el ref de cada corrida; la medición
histórica de precio no se reatribuye a esta revisión posterior.
