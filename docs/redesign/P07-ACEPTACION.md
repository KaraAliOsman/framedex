# P07 · precio del proyecto, cascada y aprobación

Rama `codex/P07-workspace-precios`, base `3351066d40a4ad7b19943984efb0cfe8e0893351`.
Verificación local 09-10-2026. Evidencia en [capturas](captures/workspace-precios/).

El proyecto abre comparando el precio aplicado con una propuesta del motor.
La cascada conserva composición, merma, proceso, servicios, utilidad a lista,
descuento, cargos e IVA. El dueño ve compra y margen logrado; el estimador
recibe una proyección de venta por allowlist, sin costos ni utilidad interna.
La administración permanece separada y Ajustes abre directamente la banda.

## Flujos y evidencia

| Flujo | Resultado |
| --- | --- |
| Abrir proyectos de 12 y 100 posiciones | PASA: posiciones completas y cascadas que cierran al total del motor. `recorrido/aceptacion.json`. |
| Cantidad tres, unitario y neto línea | PASA: cálculo exacto antes del redondeo de línea; integración conserva unitario histórico `499.8074`. |
| Estimador baja margen a 20 % | PASA: cambia a Solicitar aprobación con causa precargada. |
| Solicitud → Hoy/campana del dueño → aprobar con comentario | PASA: precio aplicado, actor y comentario auditados. |
| Decisión → Hoy/campana del estimador → marcar leída | PASA: lectura idempotente, desaparece la decisión pendiente. |
| Rechazar o retirar | PASA en integración y pruebas del componente; no modifica una venta aplicada. |
| Cambiar reglas antes de aplicar | PASA: relee la política bajo bloqueo asesor; estimador no elude al dueño. |
| Reprecio canónico congelado | PASA: suma de aportes = Δ de proyecto y posición; la prueba prohíbe acceso a DB durante replay. |
| Cobertura de autoridades → Cargar costo | PASA: SKU/unidad reales de compra precargados; vigencia, unidad y ambigüedad comprobadas. |
| Revisión cerrada | PASA: aplicar deshabilitado, causa y enlace al proyecto; conserva precio e historia. |
| Vacío, carga, error/reintento y sin permiso | PASA: primera ventana, cargador de cota, transporte controlado y permiso del dueño. |

Las capturas antes conservan el formulario anterior. La matriz después recorre
precio, composición, cobertura, auditoría e historial en 1440×900, 1280×800 y
1024×768, claro/oscuro, más Hoy en 390×844. Bajo 1280, la propuesta se abre en
un panel; el precio y las posiciones siguen disponibles sin scroll horizontal.
El runner oficial `ux:capture` se conserva en `oficial/`.

La matriz complementaria termina con 62 vistas, incluidos ocho paneles
portados, los cinco estados, Ajustes y Hoy móvil: cero hallazgos y cero
desbordes. El runner oficial termina con 32 vistas de precios y ocho de
administración, incluyendo 390 px: cero hallazgos, desbordes, errores HTTP o
de consola. Dos vistas adicionales verifican el registro USD en claro/oscuro:
`US$ 12,50` según su lista, sin presumir CLP. Costos, matrices, tarifas e
importación leen la moneda de su autoridad; sin moneda muestran Sin dato.
Los tres casos CLP/USD/moneda ausente pasan en las 58 pruebas focalizadas.
En estas dos vistas se conserva además la observación textual de la página
completa: 3.978 coincidencias del detector de enums por tema corresponden a
códigos SKU sintéticos con guiones bajos, no a etiquetas de estado. No se
modificó el detector. La presentación de toda la administración y el texto
del registro USD se verifican por separado. Los tipos de insumo sintéticos
se leen como «Insumo DEMO». Los 241 PNG conservan sus píxeles al comprimirse.

## Números y autoridad

La compra por barra se resuelve con Decimal de 80 cifras. Sus entradas finitas
se suman y reagrupan con precisión 256: preserva el costo consumido sin redondeo
intermedio ni aporte residual. Venta, descuentos e IVA conservan sus reglas
anteriores; el unitario indicativo se lee con cuatro decimales HALF_UP y cada
línea se redondea una sola vez al quantum de moneda. Multiplicar un unitario
mostrado y ya redondeado puede diferir del neto sellado; la traza muestra el
unitario exacto y la cantidad. IVA se redondea por proyecto, no por posición.
Los golden históricos no tienen diferencias semánticas.

El motor atribuye interacciones al impulsor aplicado después, en este orden:
cantidad, medidas, vidrio, herrajes, diseño, lista de costos, FX, lista comercial,
margen, descuento, segmento, servicios, impuesto. Cada etapa recalcula desde
autoridades congeladas. Una operación histórica sin esos datos o un escenario
intermedio físicamente incompatible muestra Sin dato con su causa; no se
reparte el Δ por porcentajes estimados ni se consulta el catálogo de hoy.

F6 usa entradas reales de barra/largo, vidrio/tratamiento, herrajes, extras,
merma y proceso. Márgenes, diferencias absolutas, relativas y en puntos
porcentuales abren sus trazas. La tabla no sustituye un costo ausente por cero.
Los datos sintéticos se identifican como DEMO incluso cuando una lista de
costos humana se usa con una serie de catálogo demo.

## Dos rondas editoriales

Primera: retirar el formulario anterior, tarjetas de cifras y CSS muertos;
poner comparación antes de controles; permitir retiro tras solicitar sin
dejarlo bloqueado por una generación de cálculo distinta. Separar auditoría
legible de JSON/identificadores técnicos, y conectar trazas completas.

Segunda: corregir texto bajo 11 px, decimales comerciales sobrantes y enlaces
en oscuro; quitar scroll horizontal de posiciones sin esconder columnas.
Plegar controles a un panel a 1280/1024, agregar primera ventana y enlace desde
Ajustes a reglas, y mantener el aviso DEMO según autoridad técnica.
La inspección del panel real descubre la pérdida de estilos del portal y
la corrige; la composición recibe anchos propios y artículo alineado a la
izquierda. Los modos de precio se traducen también en la lectura de reglas.
El envío del formulario de importación se declara explícitamente como submit.
La conversión de moneda se lee como «Tipo de cambio registrado», sin el
anglicismo anterior. El recorrido de emisión usa los nuevos controles en
las revisiones A y B y conserva la comprobación de precios tras recargar.

## Gates locales

`make lint`, `make typecheck`, `make test` y `make build`: PASA. El cierre
verifica 827 pruebas del motor (+2 xfail históricos), 1.351 del backend y
887 del frontend; los golden históricos pasan la comparación de bytes.
Las 58 regresiones focalizadas de precios/autenticación también pasan.
`make test-db`: PASA, 82 archivos / 1.200 pgTAP, 435 integraciones, 17 E2E
y los upgrades poblados PG16. El recorrido E2E comprueba precio persistido,
actor auditado y emisión inmutable de A/B. Si una organización desaparece
durante una simulación indicativa, el adaptador rechaza con un 404 explícito
en vez de un error 500; la regresión del contrato pasa.
Los cuatro checks de CI pasan sobre `d6db60843adc4c65e2486d8e46cf9832a4244bd3` en la corrida
`37893278926`; PR #133 integrado con squash `d8e4d899a29d9f154f8c7d37b054581132dadbb1`.

| Rúbrica | Estado | Evidencia |
| --- | --- | --- |
| R1 · Números | PASA | Mono tabular; CLP, mm, porcentajes y pp; exactitud en API/motor. |
| R2 · Radios | PASA | Tokens ≤4 px. |
| R3 · Jerarquía | PASA | Filetes, comparación y cascada; una capa flotante. |
| R4 · Naranja | PASA | Solo marca y atención existente en shell. |
| R5 · Croma | PASA | Teal de tokens. |
| R6 · Voz | PASA | Español, tipologías legibles, autoridades/detalles progresivos. |
| R7 · Densidad | PASA | Controles compactos y panel; tabla de lectura completa. |
| R8 · Estados | PASA | Vacío, cota, error, permiso y bloqueo con acciones. |
| R9 · Papel | PASA | Sin lienzo/documento nuevo; conserva las hojas de P04/P09. |
| R10 · Selección | PASA | Pestañas con subrayado, panel/filas sin elevación decorativa. |
| R11 · Iconos | PASA | Gramática existente; sin dibujos nuevos de apertura. |
| R12 · Teclado | PASA | Trazas y panel accesibles; Escape y foco de componentes comunes. |
| R13 · Movimiento | PASA | Cota y panel con tokens; reduced-motion común. |
| R14 · Acción | PASA | Una acción principal de aplicar/solicitar/aprobar por región. |
| R15 · Fuente | PASA | Trazas del motor, operaciones selladas y Sin dato explícito. |
| R16 · Sin slop | PASA | Sin degradado, blur, brillo ni morado. |
| R17 · Anchos | PASA | Tabla sin desplazamiento horizontal, panel bajo 1280. |
| R18 · Efectos | PASA | Aplicar, decidir, retirar, leer y cargar costo conectados. |
| R19 · Firma | PASA | F6 en cada monto y cascada como lectura vertical. |
| R20 · Techo | PASA | Mover margen recalcula utilidad/banda con el motor y solicita aprobación. |

## Decisiones y límites

La banda inicial es 25/35/60 % y el umbral de descuento 10 %, editables por el
dueño. La migración conserva objetivos antiguos ampliando la banda inicial
cuando corresponde. Recibos por tenant/operación/solicitante son append-only.
El historial identifica emisiones, actor, fecha y cambios comerciales por campo.
Últimas 100 operaciones por organización es el límite de esta consulta.

No se introduce integración externa en P07. Emisión/PDF permanecen en sus
encargos, y el catálogo DEMO no certifica valores de fabricante. Operaciones
históricas sin evidencia completa siguen legibles con su límite de explicación.
