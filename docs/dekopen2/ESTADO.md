# DEKOPEN 2 · Estado de implementación

Encargo del dueño: 21-10-2026. Cada fase se entrega por PR y se fusiona con
Lint & Typecheck, Test Suite, Frontend Build y Database Gate aprobados.
Producción y precios comerciales requieren autorización aparte.

| Fase | Alcance | Estado | Rama / PR |
|---|---|---|---|
| P01 | Catálogo v2: backend, origen, niveles y plantillas | Hecha | [P01a #164](https://github.com/KaraAliOsman/framedex/pull/164), [P01b #165](https://github.com/KaraAliOsman/framedex/pull/165), [P01c #166](https://github.com/KaraAliOsman/framedex/pull/166), [P01d #167](https://github.com/KaraAliOsman/framedex/pull/167) y [P01e #168](https://github.com/KaraAliOsman/framedex/pull/168) fusionadas |
| P02 | Ficha de serie editable | Hecha | Sub-PR [#169](https://github.com/KaraAliOsman/framedex/pull/169)–[#173](https://github.com/KaraAliOsman/framedex/pull/173) fusionadas |
| P03 | Alta de serie y ventana de prueba | Implementada; fusiones en curso | [P03a #174](https://github.com/KaraAliOsman/framedex/pull/174) fusionada; [#175](https://github.com/KaraAliOsman/framedex/pull/175)–[#181](https://github.com/KaraAliOsman/framedex/pull/181) pendientes |
| P04 | Precio simple automático | En curso: motor y política por empresa; automatismo e interfaz pendientes | [P04a #182](https://github.com/KaraAliOsman/framedex/pull/182), `gpt/dk2-p04b-politica-empresa` |
| P05 | Navegación, Hoy y Obras | Pendiente | — |
| P06 | Mesa de la obra y edición directa | Pendiente | — |
| P07 | Cotización y portal | Pendiente | — |
| P08 | Agente v2 | Pendiente | — |
| P09 | Taller e instalación | Pendiente | — |
| P10 | Onboarding, biblioteca Chile y aceptación Proline | Pendiente | — |
| P11 | Pulido y cierre | Pendiente | — |

## P04 · Precio simple automático

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
