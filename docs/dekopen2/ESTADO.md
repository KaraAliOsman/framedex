# DEKOPEN 2 · Estado de implementación

Encargo del dueño: 21-10-2026. Cada fase se entrega por PR y se fusiona con
Lint & Typecheck, Test Suite, Frontend Build y Database Gate aprobados.
Producción y precios comerciales requieren autorización aparte.

| Fase | Alcance | Estado | Rama / PR |
|---|---|---|---|
| P01 | Catálogo v2: backend, origen, niveles y plantillas | En curso | [P01a #164](https://github.com/KaraAliOsman/framedex/pull/164), [P01b #165](https://github.com/KaraAliOsman/framedex/pull/165), [P01c #166](https://github.com/KaraAliOsman/framedex/pull/166) y [P01d #167](https://github.com/KaraAliOsman/framedex/pull/167) fusionadas; [P01e #168](https://github.com/KaraAliOsman/framedex/pull/168) |
| P02 | Ficha de serie editable | Pendiente | — |
| P03 | Alta de serie y ventana de prueba | Pendiente | — |
| P04 | Precio simple automático | Pendiente | — |
| P05 | Navegación, Hoy y Obras | Pendiente | — |
| P06 | Mesa de la obra y edición directa | Pendiente | — |
| P07 | Cotización y portal | Pendiente | — |
| P08 | Agente v2 | Pendiente | — |
| P09 | Taller e instalación | Pendiente | — |
| P10 | Onboarding, biblioteca Chile y aceptación Proline | Pendiente | — |
| P11 | Pulido y cierre | Pendiente | — |

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
