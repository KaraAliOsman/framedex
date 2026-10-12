# P24 · analítica para decidir

Rama `codex/P24-analitica`, desde integración `97bd42a8`.
Definiciones y oráculos: [metricas.md](../analytics/metricas.md).
Evidencia: [antes](captures/analitica/antes-analitica.png),
[margen y causas](captures/analitica/margen-con-causas.png),
[movimiento valorado](captures/analitica/movimientos-con-valor.png),
[preview](captures/analitica/preview-costos.png),
[matriz](captures/analitica/matriz/), [estados](captures/analitica/estados/)
y [ux:capture](captures/analitica/ux/).

## Resultado

Cuatro preguntas, período explícito y CSV conservan la evidencia de ventas,
margen, planta y terreno. Cada cifra abre su definición, fórmula, cohortes y
registros. El costo cotizado corresponde a la revisión elegida, incluyendo
alternativas; el real reúne todas sus OT originales y reposiciones.

Los cierres de costos son aditivos e inmutables. Cada cantidad proviene del
inventario y las tarifas/horas efectivas se declaran con fuente y motivo.
Preview y clic humano anteceden el registro. Replay conserva el recibo original,
incluso después de una corrección. Una nueva evidencia de inventario, estaciones
o retazos invalida la cobertura previa. Un campo ausente nunca se transforma en cero.

Las causas del desvío suman exactamente: material útil/valoración, merma,
horas, otros servicios y reposiciones. Cada causa llega al monto cotizado y
movimientos reales firmados. El descuento tiene su fuente sellada, ya forma
parte del neto y no se resta nuevamente. El registro no modifica inventario,
precios, versiones ni documentos emitidos.

## Verificación

- 51 casos focales: 31 integraciones PostgreSQL (incluyendo un test SQL por
  métrica), nueve del motor y once de bordes HTTP/CSV. El oráculo manual
  acredita 1/4 de conversión, $900 netos, $500 de costo cotizado, $540 real,
  40 % de margen y −$40 de desvío. Cada contribución del puente cierra.
- Aislamiento B≠A, roles, revocación activa, moneda, IDs ajenos, faltantes,
  cobertura total, cierre invalidado, preview/confirmación/replay/corrección
  y rechazo de UPDATE/DELETE/TRUNCATE. El fixture histórico DEMO no reescribe
  sellos de producción; restaura guardas antes de probar el cierre.
- Ocho tests UI: permiso, F6/foco/destino, Sin dato sin cero, recuperación,
  vacío, dos clics del cierre y respuesta inicial tardía que no restaura
  un período antiguo. Valores Decimal pequeños/cero tienen texto exacto
  sin exponente, editable sin convertir a float. Una OT histórica sin moneda
  sellada bloquea valoración y registro, con enlace a su revisión.
- El golden se generó con `make goldgen`; los anteriores no cambian sus
  valores ni fórmulas. OpenAPI y orval pertenecen al mismo contrato.
- Recorrido persistente con preview, registro, corrección aditiva, CSV y
  preferencias recargadas: PASA. Matriz de 24 vistas y cinco estados,
  más 40 vistas `ux:capture`, sin hallazgos, desbordes ni errores de consola
  o HTTP. 76 PNG comprimidos conservan el hash de sus píxeles.
- Fechas con el control común, Mono y calendario oscuro; hover con tinte de
  selección. Axe en 1440 claro y 390 oscuro: cero serious/critical, incluido
  el puente abierto y la fila enfocada. Ocho tests UI, lint y tipos repasan
  esta corrección de presentación. [Controles](captures/analitica/controles-390-dark.png).
- Sobre código final `bab0df93` (rama P24), `make lint`, `make typecheck`,
  `make test` y `make build`: PASA. 1.061 tests del motor (dos xfail históricas),
  1.562 backend y 1.140 frontend; 135 fuentes mypy sin errores. Goldens y cliente
  generado reproducibles, build y activos de marca verificados.
- `make test-db`: PASA completo, exit 0. 1.483 pgTAP en 97 archivos,
  589 integraciones PostgreSQL, 19 E2E reales y trece comprobaciones de
  actualización PG16 conservan los snapshots e historiales previos.
  Un reinicio de Docker había dejado vacía la plantilla pública de acceso;
  restaurarla byte a byte permitió repetir el gate sin cambiar checks ni
  tiempos de espera. La evidencia válida corresponde a la corrida completa.

## Pase editorial

Primera ronda: se redujo la superficie a cuatro decisiones con fuente; se
separó tiempo transcurrido de horas laborales; se eliminó la suma de costos
parciales y el residuo inventado de una composición histórica. Las gráficas
solo existen con valores acreditados y no añaden colores por serie.

Segunda ronda: F6 llega al movimiento valorado y lo delinea; el período mantiene
la última lectura y bloquea edición durante la carga; error conserva reintento
real y falta de moneda lleva a la revisión. Se quitaron el descuento restado
dos veces, la fuente ancha con árboles/BOM que ralentizaba el detalle y los
ceros en notación exponencial que se mostraban como Sin dato al editar.

El momento de firma es F6. La capacidad superior es el puente de utilidad del
motor, con cada peso ocurrido una vez y la reposición separada del original.

| R | Resultado | Evidencia |
|---|---|---|
| R1 | PASA | Money/Percent/Qty/DateOnly comunes y CSV Decimal exacto |
| R2 | PASA | Tokens, radios ≤4 px y sin ornamentación de ingletes |
| R3 | PASA | Una pregunta por vista y un diálogo de evidencia a la vez |
| R4 | PASA | Naranja reservado a marca/intervención del sistema común |
| R5 | PASA | Teal de controles y cifras con fuente |
| R6 | PASA | Español, obras/OT/retazos; detalles técnicos plegados |
| R7 | PASA | Ingeniería y medición por secciones plegables |
| R8 | PASA | Vacío real, carga/error controlados, permiso y evidencia incompleta |
| R9 | PASA | La lectura conserva revisiones selladas y formatos del documento |
| R10 | PASA | Movimiento de origen delineado, sin brillo |
| R11 | PASA | Iconografía monolínea común; sin nueva gramática física |
| R12 | PASA | F6, foco restaurado, controles etiquetados y reintento |
| R13 | PASA | Movimiento común con reducción respetada |
| R14 | PASA | Aplicar período; registrar solo después del preview |
| R15 | PASA | Definición por cifra, oráculo SQL y faltantes explícitos |
| R16 | PASA | Paleta y filetes; sin degradados, blur ni brillo |
| R17 | PASA | Matriz de tres anchos y dos temas; captura móvil adicional |
| R18 | PASA | CSV, preferencias, revisión y cierre con persistencia real |
| R19 | PASA | F6 hasta obras, OT y movimientos |
| R20 | PASA | Causas exactas con origen; la suma cierra −$40 del oráculo |

Decisiones: [defaults P24](../decisions/valores-por-defecto.md).
Activación: [evidencia de costos](../operations/ACTIVACION.md).

## No hecho / riesgos

Las cohortes muestran decisiones y estados actuales, sin reconstruir un cierre
histórico al último día. No hay FX implícito, tarifa salarial inferida, costo
atribuido a inventario sin autoridad ni cargos globales repartidos a tipologías.
La medición de barras requiere cobertura total humana; no incluye láminas.
Un oráculo DEMO no acredita contabilidad ni datos reales de la fábrica.
No requiere un proveedor remoto nuevo y conserva los adaptadores sandbox previos.
