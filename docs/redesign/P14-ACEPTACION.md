# P14 · mecanizado con autoridad física

El jefe de taller puede revisar cada pieza desde su origen físico, ver el trabajo
que sigue sin emitir y declarar máquinas/herramientas con comparación y
confirmación. Generar exige revisar una huella vigente; un dato desconocido
bloquea. El resultado disponible es intercambio neutro, con esa limitación
visible antes de confirmar y descargar.

## Evidencia

- Fixture DEMO P-000601, dos unidades, fijo más hoja practicable, 34 piezas y
  diez declaraciones pendientes. La sección y el montaje son sintéticos, sin
  certificación ni validación en una máquina real. No se completó producción
  sin stock ni se inventaron movimientos.
- `captures/cnc-mecanizado/recorrido.json`: alta por UI, revisión, generación,
  repetición concurrente con mismos bytes, archivos/SHA-256, sucesor tras cambio
  de autoridad, retiro y reactivación. Cero errores de página.
- `captures/cnc-mecanizado/matriz.json`: piezas, comparación y CRUD a
  1440×900, 1280×800, 1024×768 y 390×844, claro/oscuro; estados vacío, carga,
  error, lectura sin permiso y bloqueo. Revisión obsoleta rechazada y
  restauración preparada desde historial, confirmada y auditada.
- `captures/cnc-mecanizado/ux/report.json`: detectores originales de texto y
  presentación, en las rutas de piezas y autoridad para jefe y estimador.
- Motor: profundidad, herramientas, recorrido completo contra mordaza, extremo
  final desde origen inicial, sección y montaje, transporte y determinismo.
- PostgreSQL: tenant/roles, evidencia inmutable, CRUD revisado, generación y
  manifiestos. pgTAP `235_cnc_authority.test.sql` verifica catorce condiciones.
- Regresión histórica: `0`, `0.00` y la omisión histórica de campos opcionales
  representan el mismo número exacto; cambios reales de `0.01` o fuente se
  rechazan. No se reescribe una BOM sellada para normalizar su transporte.

La aceptación anterior pasó 871 pruebas de motor (+2 xfail), 1.472 de backend,
967 de frontend, 1.299 pgTAP, 486 integraciones, 19 E2E y diez upgrades PG16.
Tras los cambios de sincronización, los cuatro gates completos pasan con
afinidad de cuatro CPU y salida 0: 871 motor (+2 xfail), 1.472 backend y
967 frontend. Los goldens siguen intactos y el fixture persistente se conserva.
La nueva ejecución DB pasa 1.299 pgTAP, 486 integraciones, 19 E2E y diez
upgrades PG16, con `[PASS] database gate` y salida 0. El proyecto aislado
se detuvo al terminar; el fixture persistente se conserva.

La corrida de CI `38072197716` falló una comprobación de SHOT-10: el selector
de vidrio se comprobó antes de que terminara la simulación del producto
compuesto. La respuesta del motor llegó después de vencer esa aserción. El
recorrido ahora registra la espera antes de seleccionar, identifica la operación
`set_glass` y exige HTTP 200, validez y el SKU esperado antes de comprobar el
selector. También distingue esa petición del precio indicativo que comparte
endpoint. Conserva las aserciones de guardado, emisión e inmutabilidad, sin
ampliar tiempos ni reintentos. La corrida fallida no cuenta como aceptación CI.

La repetición local pasó 1.299 pgTAP y 486 integraciones, pero acabó con
17 E2E PASA y dos fallos: el precio se comprobó mientras aún recalculaba y
la lista vacía se comprobó antes de recibir los proyectos. Los recorridos ahora
registran la espera antes de navegar o cambiar la fecha, verifican HTTP 200 y
las posiciones de la proyección, y exigen la operación de precio APPLIED antes
de avanzar. La lista inicial exige además `items:[]`. Conservan los límites de
tiempo y todas las aserciones comerciales.

La primera repetición de los cuatro gates pasó lint, tipos, motor y backend,
pero dos pruebas frontend agotaron cinco segundos con paralelismo local.
La repetición con afinidad de cuatro CPU pasa completa, sin cambiar checks,
aserciones, timeouts ni reintentos. Esa ejecución fallida se conserva como
evidencia; ambas pruebas pasan en la ejecución final de 967 pruebas frontend.

## Pase editorial

Primera ronda: se sustituyeron tablas/enums densos por una tarjeta por pieza;
se retiró la falsa inversión del extremo final; la sección distingue plano
completo de una trayectoria que no existe. Segunda ronda: las causas repetidas
se agrupan conservando sus unidades, las cifras de comparación usan Mono y
se corrigieron tamaño de fuentes, contraste, lenguaje y errores de transporte.
Se eliminó el CSS CNC anterior y sus veinticinco tokens sin consumidores;
no quedan dos implementaciones paralelas ni se amplía el baseline de deuda.

| R | Resultado | Evidencia y alcance |
|---|---|---|
| R1 | PASA | Medidas y recuentos en Mono; transporte exacto separado de presentación. |
| R2 | PASA | Tokens ≤4 px, sin píldoras. |
| R3 | PASA | Filetes separan piezas, operaciones y autoridad. |
| R4 | PASA | Naranja indica revisión humana; CTA teal. |
| R5 | PASA | Cromo y selección con tokens teal. |
| R6 | PASA | Español; códigos de herramienta son autoridad, enums quedan en detalles. |
| R7 | PASA | Campos en grilla, piezas paginadas de veinte y búsqueda. |
| R8 | PASA | Cinco estados, causas y destinos concretos. |
| R9 | PASA | Dibujo sobre superficie de papel, separado del cromo. |
| R10 | PASA | Operación seleccionada con contorno y tinte, sin brillo. |
| R11 | PASA | Trazo técnico; esta superficie no cambia simbología de apertura. |
| R12 | PASA | Controles nativos/primitivas con foco y navegación por teclado. |
| R13 | PASA | Sin animaciones nuevas; movimiento heredado de primitivas. |
| R14 | PASA | Revisar, confirmar y descargar son regiones sucesivas. |
| R15 | PASA | Fuente sellada, origen, montaje y Sin dato con causa. |
| R16 | PASA | Sin degradados, blur, brillo o morado. |
| R17 | PASA | Matriz en cuatro anchos y ambos temas, texto completo. |
| R18 | PASA | CRUD, retiro, restauración, comparación y descargas con efectos probados. |
| R19 | PASA | F7 y huella de plan/manifiesto preservan la decisión humana. |
| R20 | PASA | Sección y operaciones del motor; comparación y confirmación revalidadas. |

## Límites de aceptación

- Sin postprocesadores propietarios nuevos. Sin validación física en una CNC.
- Preparaciones de manilla sin patrón, Y/Z o profundidad bloquean. El dibujo
  del vano no acredita coordenadas transversales de herramienta.
- Drenajes, cierres y herrajes sin emisor/autoridad siguen explícitamente sin
  emitir. Confirmar intercambio no declara una OT completa ni autoriza esos
  trabajos faltantes.
- END cubre el plano completo del extremo; no se presenta como una trayectoria.
- Los históricos sin sección sellada requieren una nueva revisión; consultar
  el catálogo mutable no puede completar retroactivamente su autoridad.
- El historial visible acota las últimas cien declaraciones/programas. Las
  filas y archivos anteriores se conservan; la UI no afirma mostrar todo.

CI 4/4 PASA en [PR #143](https://github.com/KaraAliOsman/framedex/pull/143) sobre `970df75643c67b6bec9c3813803b071066627aab`. Squash en integración: `c4eb4159a45caef4bbf88fb770372a5d13993411`.
