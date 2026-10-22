# DEKOPEN 2 · Estado de implementación

Encargo del dueño: 21-10-2026. Cada fase se entrega por PR y se fusiona con
Lint & Typecheck, Test Suite, Frontend Build y Database Gate aprobados.
Producción y precios comerciales requieren autorización aparte.

| Fase | Alcance                                            | Estado                               | Rama / PR                                                                                                                                                                                                                                                                                                                                  |
| ---- | -------------------------------------------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| P01  | Catálogo v2: backend, origen, niveles y plantillas | Hecha                                | [P01a #164](https://github.com/KaraAliOsman/framedex/pull/164), [P01b #165](https://github.com/KaraAliOsman/framedex/pull/165), [P01c #166](https://github.com/KaraAliOsman/framedex/pull/166), [P01d #167](https://github.com/KaraAliOsman/framedex/pull/167) y [P01e #168](https://github.com/KaraAliOsman/framedex/pull/168) fusionadas |
| P02  | Ficha de serie editable                            | Hecha                                | Sub-PR [#169](https://github.com/KaraAliOsman/framedex/pull/169)–[#173](https://github.com/KaraAliOsman/framedex/pull/173) fusionadas                                                                                                                                                                                                      |
| P03  | Alta de serie y ventana de prueba                  | Hecha | #174–#181 fusionadas; [P03h #181](https://github.com/KaraAliOsman/framedex/pull/181) fusionada el 22-10-2026 |
| P04  | Precio simple automático                           | Implementada; CI y fusiones en curso | [#182](https://github.com/KaraAliOsman/framedex/pull/182)–[#187](https://github.com/KaraAliOsman/framedex/pull/187), [#188](https://github.com/KaraAliOsman/framedex/pull/188)                                                                                                                                                             |
| P05  | Navegación, Hoy y Obras                            | En curso                             | [P05a #189](https://github.com/KaraAliOsman/framedex/pull/189), [P05b #190](https://github.com/KaraAliOsman/framedex/pull/190); P05c `gpt/dk2-p05c-hoy`                                                                                                                                                                                    |
| P06  | Mesa de la obra y edición directa                  | Pendiente                            | —                                                                                                                                                                                                                                                                                                                                          |
| P07  | Cotización y portal                                | Pendiente                            | —                                                                                                                                                                                                                                                                                                                                          |
| P08  | Agente v2                                          | Pendiente                            | —                                                                                                                                                                                                                                                                                                                                          |
| P09  | Taller e instalación                               | Pendiente                            | —                                                                                                                                                                                                                                                                                                                                          |
| P10  | Onboarding, biblioteca Chile y aceptación Proline  | Pendiente                            | —                                                                                                                                                                                                                                                                                                                                          |
| P11  | Pulido y cierre                                    | Pendiente                            | —                                                                                                                                                                                                                                                                                                                                          |

## P05 · Navegación, Hoy y Obras

- P05e publicada en [#193](https://github.com/KaraAliOsman/framedex/pull/193).
  P05f `gpt/dk2-p05f-cotizaciones-obras` conecta el índice de servidor y lleva
  las cotizaciones emitidas a Obras. `/quotes` conserva filtros, hash y offset
  exacto al redirigir; las filas conservan seguimiento y revisión de destino.
  La búsqueda mantiene foco, cancela consultas y separa caché por usuario,
  empresa y rol. El formulario completo de alta conserva cliente y serie.
  1.254 unitarias frontend y 69 regresiones finales aprobadas; seis E2E finales
  con roles, filtros, 500 obras, 320 px, texto 200 % y axe aprobados. Lint,
  tipos, formato, guardas y build aprobados. Carga local 271–304 ms.
  [Dieciséis capturas y límites](../redesign/captures/dk2-p05f/aceptacion.md).
  Queda la purga global de lenguaje con su guardián. P06–P11 pendientes.
- P03h ya está fusionada en `main` (`45c190a6`). P04a integró esa base en
  `d7998257` y repite los cuatro controles; las siguientes fusiones esperan
  ese orden. Un gate verde de un head anterior no autoriza el nuevo.

- P05d se publica en [#192](https://github.com/KaraAliOsman/framedex/pull/192)
  con los seis recorridos integrados aprobados y doce capturas seleccionadas.
  P05e `gpt/dk2-p05e-indice-obras` añade el índice de servidor sin límite de
  500 obras, con páginas y recuentos por etapa. Reutiliza los filtros exactos
  del índice anterior de cotizaciones, incluido su orden de emisión y offsets.
  El seguimiento sigue restringido al dueño/vendedor; taller consulta Obras.
  Una edición entre selección y detalle exige recargar, sin mezclar revisiones.
  La conexión de este índice a la pantalla y la redirección de `/quotes`
  corresponden a la siguiente sub-PR; la pantalla actual conserva su límite.
  Veinticuatro integraciones PostgreSQL y setenta unitarias dirigidas pasan;
  contrato OpenAPI/orval reproducible, lint, tipos, formato, guardas y build
  aprobados. El recorrido completo backend pasó 1.735 pruebas y detectó la
  ruta nueva en la allowlist; corregida explícitamente y comprobada de nuevo.

- P05c se publica en [#191](https://github.com/KaraAliOsman/framedex/pull/191).
  P05d `gpt/dk2-p05d-obras` conecta etapas reales, búsqueda, recuentos y páginas
  de 50 filas con enlaces completos. Conserva los filtros históricos de estado
  y declara el límite de las 500 obras más recientes de la API existente.
- La oferta vigente elegida aporta su total; precio aplicado solo se usa si
  corresponde a la revisión. Un borrador sin precio pide abrir para calcular.
  Seis E2E cubren dueño, vendedor y jefe de taller en 1440/390, 500 obras,
  0/500 ventanas, 255 caracteres, montos grandes, 320 px y texto al 200 %.
  [Aceptación P05d](../redesign/captures/dk2-p05d/aceptacion.md).
- Se integraron en orden las dependencias completas de P03h en P04 y P05,
  con merges ordinarios y API regenerada. Las PR esperan los cuatro controles
  nuevamente. No se fusiona un head solo por conservar un gate anterior verde.
- Pendientes P05: integrar `/quotes` conservando seguimiento, fase, moneda y
  paginación; purga global y guarda de lenguaje. P06–P11 siguen pendientes.

- P05c añade saludo y fecha, hasta tres métricas reales por rol, tarjeta de
  cotizaciones preparadas y cola compacta. Revisar abre borradores guardados;
  navegar a enviar no escribe en la API. La creación manual requiere clic
  y comparte su implementación entre Hoy y Obras.
- Catorce unitarias y doce E2E reales de Hoy/navegación pasan, con cinco roles,
  escritorio y móvil, revisión con teclado, 1.000 tareas, 320 px y texto al
  200 %. Lint, tipos, build y Ruff del seeder local aprobados.
  [Aceptación P05c y capturas](../redesign/captures/dk2-p05c/aceptacion.md).
- La prueba usa un trabajo IA sintético con recibo válido, sin atribuirlo a
  una llamada de proveedor. El editor bajo 1024 px conserva su lectura actual;
  edición móvil se revisará en P06. Obras y la purga global siguen pendientes.
- Correcciones de CI: reapertura/clonación compara el precio comercial que
  proyecta el motor; correo entregado sin enlace no compara una caducidad
  ausente; el glosario incluye las cuatro etapas nuevas. Sin reducir gates.

- P05b añade etapas derivadas de la oferta vigente y la solución elegida,
  órdenes de esa revisión e instalación completa. El motor proyecta el saldo
  con pagos reales; los anulados y simulados no cierran una obra. Una
  reposición activa vuelve a Taller; una cancelada no oculta la instalación.
- La lista de 500 obras obtiene su avance en tres lecturas adicionales, sin
  recalcular precios por fila ni presentar una caché como precio actual.
  Los borradores no heredan el importe de una cotización anterior.
- Hoy distingue el PDF emitido de un enlace compartido/correo entregado y
  propone revisar y enviar. Sugiere confirmar los valores vigentes de las
  series usadas en borradores. La tarjeta de IA consulta solo obras con
  ventanas, guardadas y verificadas por los trabajos del propio usuario.
- Veinte integraciones PostgreSQL y 24 unitarias aprobadas, incluidos cinco
  roles, cruce de tenant/usuario, opción elegida, reposiciones, anulación y
  simulación de pagos, sugeridos confirmados y 500 obras sin N+1.
- OpenAPI/orval se regeneran desde los serializers. Sin tablas nuevas,
  escrituras de estado, envíos automáticos ni cambios en fórmulas.

- P05a implementa los destinos y el inicio Hoy para cinco roles. Clientes sigue
  accesible por búsqueda y ruta; Empresa reúne Informes y Funciones avanzadas.
- Diez E2E reales de navegación en 1440/390 pasan; 21 unitarias de rutas/shell
  pasan. La suite frontend completa aprueba 1.184 pruebas. [Aceptación por rol y 16 capturas](../redesign/captures/dk2-p05a/aceptacion.md).
- El contenido nuevo de Hoy, las etapas y el glosario global siguen en curso.
  `/quotes` mantiene el índice anterior hasta preservar sus filtros en Obras.
- P04g publicó `f5c4f35f` para corregir una variable CSS inexistente detectada
  por CI; sus 34 comprobaciones de tokens pasan. Espera los cuatro gates
  nuevamente antes de fusionar. No se ha debilitado ninguna comprobación.

## P04 · Precio simple automático

### P04g · Total, desglose y cotización desde el precio de trabajo

- Cabecera, ventanas y Precio usan importes del backend con su moneda.
  READY permite cotizar sin Aplicar; PENDING conserva aprobación. El popover
  ofrece el desglose y política solo al dueño. Avanzado conserva sus ajustes.
- La interfaz admite los pendientes de fabricación permitidos por la API
  para cotizar, conservando condiciones, confirmaciones y revisión humana.
  Los precios emitidos de cada ventana salen de las líneas congeladas del
  motor; política futura no cambia total, versión ni bytes del PDF.
- Dos E2E reales aprueban en 1440/390; 43 unitarias UI y 39 integraciones
  aprueban. Extremos: 0, 3 y 500 ventanas, importes/nombres largos, 320 px y
  texto al 200 %. Corregidos contraste y desbordes de cabecera/listado.
  [Aceptación y veinte capturas](../redesign/captures/dk2-p04g/aceptacion.md).
- La regresión avanzada completa también aprueba sobre el build de producción:
  dos emisiones, correo sandbox y PDF inmutable. Vite observaba los HTML de
  las trazas de `.run` y provocaba recargas durante el ensayo de desarrollo.
- `9223078d` corrige en P04d–f la prueba de clonación: una lectura puede
  avanzar la fecha de cálculo de trabajo; los demás campos del original se
  comparan exactamente. Diez integraciones pasan en ambas bases.
- P04 espera sus cuatro controles por head y las fusiones de P03. P05–P11
  siguen pendientes; no se declara terminada la fase por tener interfaz local.

### P04f · Cómo calculo mis precios

- Pantalla de Empresa con servicios por m²/ventana, margen y redondeo; merma,
  IVA y moneda plegados. Sugeridos explícitos; reglas avanzadas solo tras
  guardar su interruptor. El ejemplo consulta una unidad real del borrador y
  descarta respuestas anteriores. Un 409 conserva los cambios para comparar.
- Dos E2E con Magic Link/TOTP y serie PRO6004 sintética aprobados, en escritorio
  y móvil. Cinco unitarias UI, 21 de contrato y 25 integraciones PostgreSQL
  aprobadas. Lint, tipos, build, guardas y API reproducible aprobados.
- Se corrigieron transporte científico de cero, importes largos y desborde al
  200 % de texto. [Aceptación y capturas](../redesign/captures/dk2-p04f/aceptacion.md).
- P04f publicada en [#187](https://github.com/KaraAliOsman/framedex/pull/187).
  P04g completa el total automático, su desglose y el E2E de emisión;
  las sub-PR P04 esperan completar P03 y sus cuatro gates.

### P04e · Revisar y emitir el mismo PDF

- La vista previa privada ya admite precio de trabajo sin aplicar ni bloquear
  la obra. Solo la emisión confirmada aplica dentro de su transacción.
- El mismo contenido y los mismos bytes pasan a la revisión emitida. Cambiar
  política, costo o cantidad exige revisar un PDF nuevo. Error posterior al
  aplicado revierte la operación y conserva el PDF privado para reintentar.
- 26 integraciones pasan: política simple/avanzada, dueño/estimador, privacidad,
  emisión directa/guiada, replay y concurrencia. Se corrigió la traducción de
  errores para que no intercepte los reintentos de serialización.
- OpenAPI/orval regenerados y reproducibles; Ruff, Django y guardas aprobados.
  La configuración en Empresa, el desglose y la aceptación E2E siguen pendientes.

### P04a · Política pura del motor

- Base `origin/main` en `6c3c013d`, después de fusionar P03a. P02 ya quedó
  fusionada; P03b–h esperan sus controles y fusiones ordenadas. P04 no se
  fusionará antes de completar esa cadena.
- Mano de obra e instalación por m² o por ventana, margen sobre venta y
  redondeo hacia arriba al múltiplo explícito de la moneda. Materiales sin
  precio no se convierten en cero; la instalación incluida no se duplica.
- Nuevos casos dorados de fija y abatible PRO6004 sintética con consumo real
  del motor y precios de prueba. No certifican Proline ni tarifas de mercado.
  Los goldens anteriores y el contrato comercial avanzado permanecen iguales.
- Verificación local: 1.119 pruebas del motor aprobadas y dos xfail previos;
  33 casos nuevos, mypy (143 archivos), Ruff, goldens de solo lectura y guardas
  aprobados. Esta subentrega no toca interfaz, API, SQL ni emisión.
- Pendientes: política por empresa con RLS, precio vigente del borrador,
  aplicación al emitir, pantalla de configuración, desglose y aceptación E2E.

### P04b · Política por empresa y vista previa

- Política con RLS, costos privados del dueño con MFA, revisión optimista e
  historial anterior/nuevo en la auditoría inmutable de precios. Las tarifas
  avanzadas históricas no se reescriben; una lectura no guarda sugeridos.
- API tipada y cliente generado. La vista previa resuelve una ventana real y
  todos sus materiales en una transacción repetible, sin crear operación ni
  modificar precio. Sin ventana informa la acción necesaria sin inventar cifras.
- 13 integraciones nuevas y las 54 comerciales anteriores aprobadas en
  PostgreSQL local; 22 aserciones pgTAP y lint SQL aprobados. Incluye concurrencia
  de primer guardado/edición, aislamiento, MFA, inmutabilidad de aplicado y una
  lista de costos que cambia durante la consulta de ejemplo.
- Ruff, Django, tipos, ESLint, Prettier, build y reproducción OpenAPI/orval
  aprobados. La suite backend aprobó 1.675 casos y detectó que el inventario
  cerrado de rutas necesitaba incluir los dos endpoints autorizados nuevos;
  se mantiene la comparación exacta y la seguridad Bearer de todas las rutas.
  La regresión final de contrato/OpenAPI aprobó sus 49 casos después del ajuste.
- Pendientes de P04: precio vigente del borrador, aplicación al emitir,
  configuración y desglose en pantalla, aceptación E2E con tres ventanas.

### P04c · Proyección privada del borrador

- Proyección mutable por revisión, con RLS y guardas que exigen un borrador
  editable. No escribe precios comerciales, no aplica una operación y no
  bloquea la edición. Un costo ausente elimina el total anterior de la proyección
  y devuelve una causa concreta. El precio aplicado o emitido se conserva.
- El motor compone cantidades, IVA y servicios. Los extras conservan su tarifa;
  no reciben merma dos veces ni se cobra dos veces una instalación explícita.
  Nuevos goldens cubren extras, servicio de obra y distribución de precio cero.
- 25 integraciones de política y precio de trabajo, ocho aserciones pgTAP,
  63 casos dirigidos del motor, Ruff y mypy aprobados. Se ejercitaron tres
  ventanas, cambio de margen, los cinco modos avanzados, privacidad de costos,
  permisos, aislamiento y conservación del diseño al faltar un costo.
- Esta subentrega todavía no conecta los hooks ni expone la proyección por HTTP.
  Siguen pendientes el automatismo público, la aplicación al emitir y la interfaz.

### P04d · Guardado automático y emisión transaccional

- Guardar/cambiar cantidad/eliminar una ventana actualiza su proyección sin
  bloquear el diseño. Los lotes difieren el cálculo hasta su respuesta final.
  Abrir la obra recalcula con la política y costos actuales y expone venta por
  ventana; el desglose de costos sigue limitado al dueño.
- La preparación documental admite precio de trabajo listo. El endpoint de
  emisión directa acepta omitir la operación manual: calcula, registra y aplica
  el precio dentro de la misma transacción repetible que guarda la revisión.
  Un error revierte ambos y el clic repetido conserva una sola aplicación.
- 57 integraciones de guardado, emisión y compatibilidad documental/catálogo/
  operaciones aprobadas. Incluyen dueño y estimador, ausencia de confirmación,
  rollback, cantidades y conservación de emitido después de cambiar el margen.
- Sigue pendiente adaptar el PDF revisable y el envío guiado a este contrato,
  además de mostrar configuración, totales y desglose en la interfaz.

## Base y comprobaciones previas

- Base inicial de aplicación: `origin/main` en `0207763c`, con dirección desde
  `claude/dekopen2-direccion` (`ec3762fe`), como permite el encargo. La sub-PR
  P01a ya incorporó ese paquete y las correcciones de base a `origin/main`
  mediante merge commit `077ad7944e7cb327b6d649cc1a67ad7875b53143`, después
  de aprobar los cuatro controles obligatorios.
- `main` local tiene cuatro commits propios antiguos y diverge del remoto.
  `git pull --ff-only` lo detectó sin modificar su historia. Se preserva.
- Se preservan los cinco archivos no rastreados preexistentes.
- CI previo de #163: Lint & Typecheck y Frontend Build aprobados; Test Suite
  falló en cinco pruebas de emisión de `ProjectPages.test.tsx`: sus cotizaciones
  vencían el 19-10-2026 y la validación real de vigencia empezó a rechazarlas.
  P01a fija el reloj de esa fixture al 09-10-2026, manteniendo temporizadores
  reales y todas las comprobaciones de revisión y emisión. Las 35 pruebas de
  ese archivo pasan después de la corrección.
- Motor previo en Windows: 1061 aprobadas, dos xfail y tres fallos. Dos se debían
  a leer JSON UTF-8 con la codificación de Windows; el tercero a CRLF introducido
  por `core.autocrlf`. P01a explicita UTF-8 y LF para los goldens. Se restauraron
  únicamente los bytes ya comprometidos en Git, sin ejecutar generación ni
  cambiar fórmulas, parámetros o resultados esperados.
- Ruff, mypy, Django check, ESLint/TypeScript aprobados. Prettier encontró cuatro
  capturas locales en `frontend/.run/`; esa carpeta temporal queda excluida del
  formateo, conservando sus archivos. Suites completas y demás guardas en curso.
- Esta estación no tiene GNU make; se ejecutan los mismos comandos de su
  Makefile mediante Python del proyecto y npm. El CI ejecuta los targets make.
- Primer Database Gate de P01a: 1.483 aserciones pgTAP y 601 pruebas de
  integración aprobaron. El E2E de emisión caducaba el 19-10-2026 y esperaba
  una petición que el control de vigencia rechazaba antes de enviarla. La
  fixture ahora usa una fecha 30 días posterior a la ejecución, conservando
  el reloj real necesario para Magic Link/TOTP y todos los controles de emisión.

## P01 · Trabajo y pendientes

Se revisan las autoridades existentes para conservar compatibilidad e historial
al añadir valores sugeridos. Cotizar admitirá sugeridos identificados; fabricar
exigirá confirmarlos y verificar la serie. La verificación de usuario pertenece
a P03; P01 deja preparado su contrato y su bloqueo.

### P01b · Traza de valores sugeridos

- `SystemParams.value_origins` aporta metadatos resueltos sin modificar cifras.
  El resultado añade `assumptions` solo para reglas SUGGESTED consumidas.
- El cálculo registra consultas a reglas de corte/refuerzo, vidrios, límites,
  herrajes y acabados; los módulos contribuyen al conjunto sin duplicados.
  Los contextos no se filtran entre hilos ni después de un error.
- Los campos nuevos se omiten al serializar contratos históricos que nunca
  los declararon. La comprobación de bytes dorados pasa sin regenerarlos.
- OpenAPI y orval regenerados. Las pruebas de inventario de parámetros ahora
  enumeran 37 campos y clasifican `value_origins` como metadato; mantienen la
  comprobación exhaustiva y apuntan al consumidor real tras extraer el wrapper.
- Pendiente de P01: persistencia/historial por celda, cuatro plantillas,
  niveles de uso, endpoints por pestaña/lote y bloqueos por dependencia.
  Esta sub-PR todavía no habilita una serie para cotizar ni fabricar.

### P01c · Historial por celda y plantillas versionadas

- Cuatro plantillas de familia en JSON, sin precios, SKU ni anchos visibles
  inventados. Sus valores típicos llevan SUGGESTED y «revisar con fabricante».
- `catalog_value_history` conserva cada cambio y confirmación, valor anterior,
  actor y fecha. Las cifras escalares usan NUMERIC; objetos se descomponen en
  celdas y tablas ordenadas permanecen atómicas. Borrar un valor deja una
  versión nula, sin convertir la ausencia en una confirmación.
- Los cambios de las rutas existentes también registran historia. Los registros
  históricos revisados se clasifican WORKSHOP, o MANUAL con evidencia vigente y
  coincidente. Las semillas sintéticas no se convierten en datos del fabricante.
- `catalog_series_setup` prepara la verificación de P03. Editar una regla
  invalida la comprobación anterior. Ambas tablas tienen tenant, RLS y permisos
  de escritura solo para el backend técnico.
- Base sintética aislada `dk2-catalog-20261021`: migraciones desde cero,
  1.507 aserciones pgTAP y cuatro pruebas nuevas de integración aprobadas;
  diez pruebas unitarias de plantilla aprobadas. REVIEW conserva su estado.
- Pendientes de las siguientes sub-PR: conectar creación desde plantilla,
  fichas y lotes, cargar orígenes al motor y aplicar niveles/bloqueos v2.

### P01d · Ficha por pestañas y lotes

- Alta transaccional desde las cuatro plantillas: perfiles, reglas, junquillos
  y kits conservan qué escribió el taller y qué completó la plantilla.
- API de seis pestañas, con coordenadas/origen de las celdas e historial.
  Los costos de compra solo se devuelven al dueño; los demás roles técnicos
  conservan su acceso a las referencias de catálogo.
- Edición y confirmación en lote con revisión optimista, rollback completo y
  rechazo de celdas repetidas, superpuestas o de otra serie. Las escrituras
  antiguas usan el mismo orden de bloqueo para convivir con los lotes.
- Las revisiones antiguas registran confirmaciones; revisar evidencia exacta
  añade MANUAL. Agregar o quitar perfiles también invalida la verificación.
- El repositorio carga al motor únicamente versiones que coinciden con el
  valor actual. Una ventana PRO6004 de prueba de 1200 × 1100 abatible produce
  despiece y sugeridos consumidos; confirmarlos elimina las suposiciones sin
  cambiar ninguna medida del despiece.
- OpenAPI y orval regenerados. P01d quedó fusionada en `68bf4e29` después de
  aprobar Lint & Typecheck, Test Suite, Frontend Build y Database Gate.
- Pendientes para completar P01: niveles de uso, precios/cotización QUOTABLE,
  fabricación MANUFACTURABLE y sus decisiones congeladas.

### P01e · Niveles y bloqueos por dependencia

- `usage` expone DRAWABLE, QUOTABLE, MANUFACTURABLE y MACHINE_READY, pendientes
  por campo/origen/acción y conteo de sugeridos actuales. `readiness` queda
  obsoleto en OpenAPI; `quote_ready` es el alias de QUOTABLE. Dibujar no exige
  inspector ni políticas de taller. Los costos solo bloquean cotización;
  las confirmaciones y la verificación bloquean salida física.
- QUOTABLE comprueba reglas y costos vigentes con sus unidades y ambigüedades.
  Precio verifica los materiales realmente consumidos; un artículo ajeno al
  diseño no invalida un precio que el motor ya resolvió. También comprueba
  tornillos de refuerzo. Los precios sintéticos resuelven las identidades de
  compra declaradas del propio ejemplo, copiando sus tarifas existentes.
- MANUFACTURABLE exige confirmar los valores y una verificación con actor,
  fecha y huella exacta de las reglas actuales. P03 implementará el clic y la
  ventana de prueba. Los ejemplos globales conservan su carácter sintético;
  no se etiquetan como manual ni como verificación real del taller.
- Optimización y borrador de corte usan el permiso de fabricación. La emisión
  admite una revisión solo comercial sin inventar inspector, políticas ni
  hechos de taller. Las políticas ausentes son NULL; las declaradas conservan
  claves foráneas, alcance de serie/tenant y protección de revisiones emitidas.
- La revisión guarda la decisión completa. OT y documentos de taller leen
  esos pendientes congelados; confirmar el catálogo después no modifica una
  cotización ya emitida ni la habilita retroactivamente para fabricar.
- Prueba local PRO6004: plantilla + perfiles y precios explícitos sintéticos,
  ventana abatible 1200 × 1100, precio del motor, PDF comercial, corte bloqueado
  con pendientes y optimización después de confirmar/verificar: aprobada.
  Las pruebas negativas incluyen políticas de otra serie y verificación con
  huella obsoleta. Motor: 1.071 aprobadas y dos xfail; backend: 1.638 aprobadas,
  más la nueva regresión de tarifa de ejemplo por serie; frontend: 1.134
  aprobadas. Ruff, mypy, Django, ESLint, tipos, Prettier, build, lint SQL,
  guardas y reproducción OpenAPI/orval aprobados. Goldens idénticos sin
  regeneración. La integración completa y el CI siguen en curso.
- El Database Gate de P01c detectó que la limpieza E2E intentaba borrar una
  empresa con historia nueva inmutable. La fixture ahora comprueba el rechazo
  y conserva esa empresa sintética hasta terminar la pila aislada; no se
  debilitaron restricciones ni se tocó REVIEW.
- Integración de compatibilidad: 47 pruebas de extras, terreno y medición,
  33 de contexto RLS y la regresión del PDF térmico aprobadas. Las fixtures
  separan ahora completitud técnica de cobertura de precios: una lista vacía
  no autoriza cotizar. El caso térmico conserva sus comprobaciones de cálculo
  y PDF inmutable como revisión comercial y comprueba expresamente que no
  habilita fabricación sin verificar la serie. Reejecución completa en curso.
- Doce integraciones de permisos y emisión aprobadas: una confirmación por
  celda seguida de la verificación vigente sustituye una revisión antigua
  marcada pendiente. La emisión conserva el diagnóstico anterior, pero decide
  con MANUFACTURABLE y mantiene los controles físicos de fabricación y proceso.
- La prueba DXF ejecuta también su lector secundario en UTF-8 explícito.
  Así conserva «Ñ» en Windows aunque Python padre use otra configuración;
  las dos regresiones de DXF y artefactos pasan sin cambiar el documento.
- P01d quedó fusionada con los cuatro controles aprobados. En P01e, CI aprobó
  1.514 aserciones pgTAP y 618 integraciones. El E2E detectó que el selector del
  editor aún exigía QUOTABLE: ahora consulta DRAWABLE, sin convertir una serie
  sin precios en cotizable. Las pruebas mantienen la negativa de precios y
  comprueban que los perfiles incompletos siguen fuera del selector.
- La ejecución local estable aprobó 15 de 16 E2E; el único fallo fue la carga
  completa de Catálogo, que superó los 20 segundos. El perfilado halló 6.189
  consultas para 51 versiones. La lista nueva `summary=true` conserva los
  niveles v2 exactos sin repetir el diagnóstico antiguo de taller. Los mapeos
  de compra se cargan en lote y las tarifas de ejemplo se indexan por serie/SKU
  y se leen una vez por petición. El contrato por defecto y el detalle
  mantienen el diagnóstico completo. Siete integraciones de resumen/niveles,
  26 pruebas de precio y 24 unitarias de catálogo/onboarding aprobadas;
  regresión E2E dirigida aprobada en 49,4 segundos con el límite original de
  respuesta del catálogo. CI final de #168 pendiente.
- El último gate aprobó 618 integraciones, pgTAP y 17 de 18 E2E. La prueba
  de reapertura comparaba el resumen nuevo con el diagnóstico histórico de
  la respuesta de edición. Ahora compara todos los campos persistidos, los
  niveles v2 completos y el alias de cotización; mantiene las comprobaciones
  de perfiles, junquillos, teclado, permisos y persistencia. CI reejecutado.
- P01e #168 quedó fusionada mediante merge commit `9f711d53` con los cuatro
  controles aprobados en la ejecución `39698605415`. P01 queda completada;
  la verificación humana de una ventana de prueba sigue correspondiendo a P03.

## P02 · Tabla y ficha editable

### P02a · Componente compartido

- Tabla reutilizable con números como texto exacto, coma decimal, navegación
  por flechas/Enter/Tab, pegado rectangular, límites por celda, guardado en lote,
  historial invocable y deshacer mediante una nueva escritura.
- Trece pruebas unitarias cubren precisión, pegado atómico, validación por fila,
  conflicto con borrador conservado, cero/vacío, consulta y teclado paginado.
  Cuatro E2E de la ruta de desarrollo pasan a 1440 × 900 y 390 × 844, con axe
  A/AA/2.1 AA y 300 perfiles. La ruta queda excluida del build productivo.
- Las diez capturas seleccionadas y su comparación con el mockup están en
  [aceptación P02a](../redesign/captures/dk2-p02a/aceptacion.md).
- Pendientes del conjunto P02: conectar el inicio y las seis pestañas,
  confirmar sugeridos, precios e historial auditados, glosario y aceptación
  completa del flujo PRO6004. P02a por sí sola no completa la fase.

### P02b · API y rendimiento del catálogo

- La lista permite filtrar ejemplos y series propias antes de calcular niveles.
  La consulta por defecto conserva compatibilidad y la biblioteca global sigue
  disponible. Tres integraciones verifican filtros estrictos y aislamiento.
- El origen se indexa por tabla/fila/campo con comparación exacta y evidencia
  vigente. El decorador de perfiles agrupa padres, evidencia y revisores por
  petición. Dieciocho unitarias verifican paridad y metadatos de 300 perfiles.
- El perfilado sintético pasó de 8,647 s/2.336 consultas a 2,421 s/383 consultas
  después del filtro y los índices. La lista que solo pide las series propias
  cargó en navegador entre 1.428 y 1.559 ms; no son métricas de producción.
- La edición de precios es un lote exclusivo del dueño, con revisión de serie,
  valor previo, aislamiento y auditoría. Deshacer añade una escritura. El nuevo
  ordinal inmutable desempata eventos con la misma fecha transaccional; para
  eventos antiguos aporta estabilidad, sin reconstruir cronología inexistente.
- Veintiuna integraciones de ficha, niveles, filtros, nombres por tenant, precios exactos, conflictos,
  permisos, aislamiento y rollback aprobadas. El rechazo de reglas identifica
  recurso/fila y conserva los errores por campo para señalarlos en la tabla.
  Nueve aserciones pgTAP del ordinal y las 1.514 anteriores aprobaron por separado;
  lint SQL aprobado en la base sintética aislada, sin tocar REVIEW.
- API regenerada y reproducción OpenAPI/orval aprobada. La conexión visual y
  el glosario se entregarán después; P02 continúa en curso.
- El CI de P02b detectó que el comparador de migración D08 no admitía el
  ordinal nuevo. El gate permite exclusivamente esa columna, exige BIGINT
  identity no nulo, ordinal positivo y único, y conserva la comparación exacta
  de todos los campos y el conjunto de eventos históricos. Catorce regresiones
  rechazan cambios de monto, actor, motivo, fecha, registros y ordinal previo;
  también eventos borrados/agregados y columnas desconocidas. La migración
  completa poblada de PostgreSQL 16 se vuelve a ejercitar.

### P02c · Componentes de ficha y precios

- Seis pestañas sobre la tabla compartida, origen por celda, historial,
  confirmación individual/en lote y navegación al primer sugerido. El guardado
  refresca nivel y pendientes; los borradores sobreviven a rechazos.
- Límites y precisión dependen de la celda. Los errores del servidor se asignan
  a su fila/campo exactos, incluidos valores dentro de tablas anidadas.
- Precios exactos de cuatro decimales, historial y deshacer por escritura nueva.
  La API mantiene los costos restringidos al dueño y los permisos de edición.
- Treinta y una unitarias, ESLint y tipos aprobados. Dos E2E de integración
  real aprobaron el flujo de seis pestañas en escritorio/móvil, axe y extremos.
  [Evidencia y límites](../redesign/captures/dk2-p02/aceptacion-ficha.md).
- P02c no activa la ruta. P02d aporta glosario/selector de ejemplos; P02e conecta
  inicio, ficha, prueba preliminar y E2E. La verificación persistida sigue en P03.

### P02d · Lenguaje de taller y ejemplos optativos

- El catálogo, sus ajustes y traducciones compartidas usan el glosario del
  encargo. Los vacíos piden completar; origen, documentos y revisiones emitidas
  conservan su significado técnico. La enmienda de Constitución registra esta
  dirección del dueño, sin modificar invariantes ni permisos.
- Nueva guarda AST de textos de interfaz, con pruebas del detector para JSX,
  expresiones, plantillas y concatenaciones. Se integra a `make lint` sin
  excluir pantallas ni aceptar nuevas infracciones del control de diseño.
- Los dos selectores del editor ocultan ejemplos hasta activar «Mostrar
  ejemplos». Una ventana histórica conserva visible su serie seleccionada.
- La edición avanzada conserva sus enlaces de regreso y alta desde cero;
  el E2E anterior se mantiene además en `catalog-advanced.spec.ts` para la
  activación posterior de la ficha nueva.

- Revisión del lenguaje servido por API: las etiquetas públicas de importación,
  errores de campos requeridos, metadatos y avisos usan el mismo glosario. Los
  encabezados del XLSX versionado se conservan para no romper su lectura.
  Sesenta y seis pruebas de importación, esquema y metadatos pasan.
- Los E2E comerciales existentes activan ejemplos mediante el control nuevo;
  el flujo de precio y emisión de dos revisiones aprobó sin cambiar sus
  comprobaciones de cálculo, documentos ni inmutabilidad.

### P02e · Activación e integración

- Inicio por fabricante/serie, búsqueda, alta desde biblioteca/plantilla/cero y
  ejemplos plegados con carga bajo demanda. Los indicadores excluyen ejemplos.
- Ruta simple activa, enlaces históricos redirigidos a ajustes y vuelta a ficha.
  La ventana de prueba preliminar consulta opciones y calcula con el motor.
- E2E real con Magic Link/TOTP en dos viewports: cinco filas pegadas, dos
  confirmaciones, cambio de nivel/franja sin recarga, seis pestañas, precios,
  historial, undo, prueba del motor y creación desde plantilla: aprobado.
  Edición avanzada conservada y probada. [Aceptación](../redesign/captures/dk2-p02/aceptacion.md).
- Diecinueve capturas seleccionadas e inspeccionadas; axe A/AA/2.1 AA y anchos
  de página correctos. Trescientos perfiles, nombres de 80 caracteres y cuatro
  decimales comprobados. Carga local de ficha 0,85–0,90 s.
- Revisión final de precios: la ficha usa las identidades de costo que ya
  comprueba el calculador, incluyendo kits, tornillos y procesos del vidrio.
  Seis integraciones de ficha/precio pasan; la nueva regresión comprueba los
  nueve materiales de la serie y edición/historia exactas del kit sin exigir
  un código de proveedor adicional.
- P02 espera sus cuatro controles por sub-PR y fusiones ordenadas. P03–P11
  continúan pendientes; no hay activación de producción ni precios comerciales.
- Database Gate detectó que la vista previa de marca usaba la zona predeterminada
  de Django para la vigencia, distinta del día de Santiago usado al preparar la
  emisión. La vista previa ahora declara Santiago explícitamente. Dos regresiones
  con reloj fijo a ambos lados de medianoche comprueban la fecha del PDF, incluso
  con otra zona activa, y conservan precio, moneda y huella de la revisión.

### P03a · Comparación y propuestas exactas del motor

- Preparación dependiente de la pila P02, sin adelantar su fusión. El motor
  proyecta cortes, refuerzos y medidas de vidrio para compararlos con decimales
  declarados por el taller. No publica ni confirma datos del fabricante.
- Ajustar una medida ofrece parámetros identificados y recalcula la ventana
  completa. Solo devuelve candidatos que reproducen exactamente la medida;
  varias causas posibles se presentan para elección humana. Conserva las
  restricciones del modelo y rechaza aproximaciones o claves que desaparecieron.
- Cuatro casos sintéticos nuevos se congelan mediante el comando de `goldgen`;
  todos los goldens anteriores permanecen idénticos. Motor completo: 1.086
  pruebas aprobadas y dos xfail existentes; mypy y Ruff aprobados.
- Faltan persistencia/RLS del caso del taller, protección de ediciones, doble
  lectura, mapeo de precios y asistente visual; P03 no está terminada.

### P03b · Verificación persistida y protección de la prueba

- API de comparación, propuestas, confirmación, historial de pruebas y progreso
  reanudable. Los resultados se recalculan en el servidor; un token liga la
  confirmación a entrada, resultado y catálogo vigentes. El clic puede confirmar
  explícitamente los valores sugeridos; nunca los atribuye al fabricante.
- Caso por empresa inmutable con entrada, salida esperada y autor. RLS impide
  leer otra empresa; ni el backend ni el usuario privilegiado reescriben o borran
  el caso. La referencia impide borrar la serie que lo originó.
- La ficha, el CRUD avanzado y publicación/deshacer de importaciones comparan el
  lote completo antes del commit. Si cambia la ventana, devuelven antes/después
  y un token de revisión ligado al cambio exacto. La edición no confirmada se
  revierte íntegra; la confirmada conserva el caso original e invalida la
  verificación de fabricación hasta volver a comprobar la serie.
- Progreso con revisión optimista y borrador técnico. Los costos no se guardan
  en ese estado compartido: conservan la API y permisos del dueño.
- Pruebas locales: 24 integraciones de prueba/ficha/precios más una nueva de
  publicación protegida; 23 pgTAP de RLS/inmutabilidad; 12 unitarias del contrato.
  La suite completa del backend aprobó 1.669 pruebas y detectó el inventario de
  cinco rutas nuevas; corregido ese inventario, sus 17 comprobaciones dirigidas
  pasan. Ruff, guardas, tipos, formato y build aprobados; API regenerada.
- Falta interfaz, doble lectura y mapeo de precios. Sin activación de producción.

### P03c · Dos lecturas independientes del manual

- Dos llamadas con instrucciones distintas y claves idempotentes separadas. La
  segunda nunca recibe la respuesta de la primera. Cada celda conserva ambas
  lecturas, citas, confianza y auditorías; el acuerdo exige soporte literal en
  ambas y una identidad completa y única, sin depender del orden de las filas.
- Solo los acuerdos quedan como propuestas. Las diferencias no publican un
  valor hasta la elección humana. Elegir una lectura citada conserva su origen
  documental tras publicar; corregir libremente queda como dato del taller.
  Fallar la segunda lectura no devuelve propuestas de una sola extracción.
- Se rechazan números binarios y no finitos antes de crear candidatos. La
  integración comprueba que la base no cambia antes del clic y que la elección
  citada termina con origen MANUAL, conservando las dos lecturas.
- Corregido el enlace de evidencias de corte/refuerzo a sus campos anidados:
  una revisión real ahora confirma el campo correcto, sin reescribir evidencia
  histórica. Las propuestas de ajuste también validan los rangos del catálogo
  antes de ofrecerse; el motor puro mantiene sus capacidades originales.
- Validación: 74 unitarias de ingesta/intercambio y 11 integraciones de
  publicación, intercambio y ajustes. Faltan el mapeo de precios y la interfaz.

### P03d · Mapeo exacto de precios del proveedor

- Inspección de XLSX/CSV con sugerencias por encabezado y diez filas de muestra.
  Los códigos conservan ceros iniciales; los precios de Excel se leen del XML y
  los de texto usan el separador declarado. No se convierten kilos a metros.
- La vista previa valida todo el archivo y devuelve diez filas y el total.
  Confirmar exige un token ligado al archivo, mapeo y lista revisados; aplica
  todas las filas en una transacción. No sobrescribe códigos ya existentes.
- Solo el dueño puede inspeccionar o guardar costos. Los precios son del taller
  y la auditoría registra actor, motivo, archivo y SHA256. No hay tabla paralela
  ni nuevos permisos SQL. El importador XLSX anterior conserva su contrato.
- 44 unitarias de precios/importación y ocho integraciones PostgreSQL aprobadas;
  API/OpenAPI regenerados. La interfaz del asistente se conecta a continuación.
- El CI de P03b detectó tres grupos nuevos sin traducción. Se añadieron al
  glosario sin debilitar su prueba exhaustiva: 211 comprobaciones aprobadas.

### P03e · Ventana de prueba y revisión de ediciones

- Comparación editable con cortes, refuerzos, vidrios, cantidades y ángulos del
  motor. El taller elige entre ajustes exactos, revisa las piezas afectadas y
  aplica/recalcula. Confirmar exige revisar el despiece y aceptar expresamente
  los valores sugeridos. Un cálculo vacío o fallido no permite verificar.
- Ediciones protegidas muestran antes/después y todos los cambios físicos,
  incluidos ángulos y componentes. Cancelar conserva el borrador; aceptar
  reenvía una sola vez la misma mutación y el token del cambio exacto. Un cambio
  de empresa impide reintentar la escritura con otra empresa.
- El ensayo móvil detectó contenido del fondo expuesto al lector de pantalla.
  El diálogo compartido ahora aísla y restaura el fondo, incluidos otros
  diálogos y portales. La tabla usa scroll local accesible y páginas de 50 filas.
- Validación local: 1.188 pruebas de frontend aprobadas; cinco E2E reales/de
  extremos aprobados, con Magic Link y TOTP, a 1440/390 y 320 px, texto al 200 %,
  0/1/500 piezas, códigos largos y números grandes. ESLint, TypeScript, formato,
  guardas y build aprobados. [Evidencia](../redesign/captures/dk2-p03e/aceptacion.md).
- Faltan el asistente completo de cinco pasos, su lectura documental integrada,
  la UI de precios mapeados y la aceptación del alta desde plantilla. P03 sigue
  en curso; ninguna de sus sub-PR se fusionará antes de completar P02.

### P03f · Importación visual de precios del proveedor

- La pestaña Precios abre el mapeo de XLSX/CSV. El dueño elige o crea una lista
  con proveedor, moneda y vigencia explícitos. Crear lista guarda solo esa lista
  vacía; inspeccionar y revisar el archivo no publica precios.
- Cuatro columnas sugeridas por el servidor, separador decimal explícito y una
  muestra de diez filas. Revisar valida todo el archivo; el clic posterior guarda
  con su token. Cambiar archivo, columna, separador o lista exige otra revisión.
  Códigos con ceros y precios de cuatro decimales se conservan como cadenas.
- La confirmación anuncia los precios guardados como datos del taller y recarga
  la ficha. Solo el dueño ve la acción; el backend conserva sus permisos. Un
  fallo de lectura permite reintentar el mismo archivo sin volver a seleccionarlo.
- 1.197 pruebas de frontend aprobadas en la suite completa y 19 dirigidas tras
  añadir la recuperación de lectura. E2E con Excel sintético comprueba 12 precios,
  ausencia de escrituras antes del clic, token descartado al cambiar columnas y
  exactitud en PostgreSQL a 1440/390 px. Tres E2E de extremos pasan a 1440/390/320,
  texto al 200 %, códigos de 100 caracteres y 0/1/500 precios. ESLint, TypeScript,
  guardas y build aprobados. [Evidencia](../redesign/captures/dk2-p03f/aceptacion.md).
- La muestra tiene altura acotada y desplazamiento local por teclado. Los montos
  enormes pueden distribuirse entre grupos de miles para permanecer completos a
  320 px con texto al 200 %. La ruta de ensayo no entra al build de producción.
- Falta integrar los cinco pasos reanudables, revisión de discrepancias del manual
  y apertura de la primera cotización. La aceptación integral de P03 sigue pendiente.

### P03g · Revisión de diferencias del manual

- Las dos lecturas se contrastan con sus páginas, citas y valores. Los acuerdos
  se resumen como propuestas; las diferencias requieren elección o corrección.
  Elegir no incluye la fila ni publica. La revisión completa permanece accesible.
- Los enlaces de fuente cargan solo su importación, esquema e historial; ya no
  esperan las cuatro colecciones del catálogo avanzado. Se conserva esa ruta
  avanzada para editar el catálogo completo. Hay recuperación de errores.
- 1.209 pruebas frontend y 19 dirigidas aprobadas. Dos E2E publican sobre
  PostgreSQL con lecturas simuladas, Magic Link/TOTP y almacenamiento reales;
  tres ensayos prueban 0/1/500 filas, 1440/390/320 y texto al 200 %, con axe.
  ESLint, TypeScript, Prettier, Ruff, guardas y build aprobados.
- Seis capturas inspeccionadas en [aceptación](../redesign/captures/dk2-p03g/aceptacion.md).
  No se añadió movimiento. Se corrigió el contraste de la fecha de importación.
- P03 no termina aquí: faltan el asistente reanudable, la primera obra con serie
  preseleccionada y la aceptación integral desde plantilla. P02e espera su gate
  de base; el formato de P03f señalado por CI se corrigió en `488dc936` y vuelve
  a ejecutar sus cuatro controles.

### P03h · Cinco pasos reanudables y primera obra

- El alta integra serie, revisión del manual, precios mapeados, ventana de
  prueba y primera cotización. Conserva archivos y decisiones al cambiar de
  paso; cerrar o recuperar advierte del descarte de borradores sin publicar.
  Los pasos ocultos permanecen fuera del foco y de la pantalla.
- El progreso usa revisiones consecutivas y detiene la cola ante conflicto.
  Reabrir espera el estado actual. La confirmación de la ventana incrementa
  también esa revisión, preserva el borrador técnico y conduce al paso cinco.
- El asistente solo publica filas con la identidad exacta de esta serie.
  Los costos conservan los permisos del dueño. El final exige capacidad real
  de cotización y ninguna tarea sin guardar; visitar el paso no verifica nada.
- La obra guarda la serie inicial y el primer editor la hereda, sin alterar
  la empresa. Corregido que la creación aceptaba `design_defaults` pero no
  los persistía. Otra empresa no puede aportar su serie ni dejar una obra parcial.
- Tres E2E finales aprobados: alta 1440/390 con 12 precios, corrección exacta
  1206 → 1208 mm, caso inmutable y obra; extremos 1440/390/320, 0/1/500 perfiles
  y pendientes, texto al 200 %, teclado y axe. Los perfiles/precios son
  sintéticos y las dos lecturas están simuladas; no son aceptación del manual
  real de Proline. [Capturas y límites](../redesign/captures/dk2-p03h/aceptacion.md).
- Frontend completo 1.218 PASS y 43 regresiones finales; backend 1.702 PASS;
  motor 1.086 PASS y dos xfail previos, bytes dorados intactos; 16 integraciones
  PostgreSQL aprobadas. Tipos, lint, formato, API reproducible, guardas y build
  aprobados. La apertura local tarda unos 3,8 s; el rendimiento final queda en P11.
- P03a #174 está fusionada. P03b #175 actualiza su base y repite CI por la
  protección de GitHub; las siguientes se fusionarán en orden, con sus cuatro
  controles. P03 permanece en curso hasta que toda la cadena esté fusionada.
