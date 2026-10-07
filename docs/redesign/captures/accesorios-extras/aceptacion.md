# D06 · accesorios y servicios con autoridad

La posición conserva vierteaguas, ensanches, tapajuntas, mosquiteros y accesorios
compatibles. El motor deriva cantidades, BOM y cortes; Precios reparte el neto
sellado entre la base y sus sublíneas sin perder un peso. Instalación, sellado,
retiro, andamio y flete pertenecen a la revisión del proyecto. La organización
define fuentes, tarifas, plantillas y presentación documental.

## Recorridos y evidencia

| Recorrido | Resultado y evidencia |
| --- | --- |
| Ancho 1 500 mm, vuelos 30 + 30 mm | PASA: vierteaguas de 1 560 mm; `engine/tests/golden_extras.json` |
| Dos posiciones de 1 500 × 1 400 mm, instalación por perímetro | PASA: 11,6 m y $17.400 de tarifa sintética; golden e integración |
| Base + extras, margen de proyecto y ajuste de moneda | PASA: reparto exacto; `test_gold_cases_extras.py` |
| Ensanche por lados → BOM → OT → optimización | PASA: piezas y tornillos con traza EXTRA; `recorrido/flujo-sellado-ot-corte.json` |
| Manilla especial y accesorios por hoja | PASA: sustitución de la manilla base y rechazo de duplicados; pruebas del motor |
| Palillaje y cruces | PASA: cantidades y tarifa de la autoridad D02; sin segundo BOM ni cobro duplicado |
| Sugerir con causa → aceptar/descartar → deshacer → guardar/reabrir | PASA: inspector real y regresiones `Extras.test.tsx` |
| Servicios por perímetro y zona → deshacer/rehacer → guardar | PASA: `servicios-perimetro-flete-deshacer.png` |
| Plantilla → nueva posición, clon y revisión sucesora | PASA: integración `test_extras_services.py` |
| Política con MFA real → diff → guardar/deshacer | PASA: integración `test_extra_policy_api.py` y capturas de Ajustes |
| Importar catálogo → editar → diff → publicar → deshacer | PASA: `catalogo-importacion-diff.png`, `catalogo-publicacion-deshacer.png`; autoridad original intacta |
| Carga, error/reintento, vacío, consulta y acceso denegado | PASA: `recorrido/navegador-more.json` y `estado-*.png` |
| Cotizar → aplicar → emitir → PDF → liberar y cortar | PASA: revisión inmutable, BOM extra y corte por su SKU; integración y recorrido real |
| PDF con precio por sublínea y precio agrupado | PASA: `cotizacion-extras-itemized.pdf`, `cotizacion-extras-grouped.pdf`, `politicas-pdf.json` |

Los dos PDF finales se emitieron como revisiones nuevas, se rasterizaron y se
inspeccionaron. La tabla de extras ocupa el ancho de la ficha y la tabla de
servicios conserva su título en la misma página. Tarifas, cantidades y ajustes
usan el neto del motor; no se reescribieron los artefactos emitidos anteriores.

La matriz formal tiene 40 comparaciones: editor, proyecto, precios, Ajustes y
Catálogo; 1440×900, 1280×800, 1024×768 y 390×844, en claro y oscuro.
[`comparacion.json`](comparacion.json) no registra hallazgos nuevos ni errores
HTTP/consola. Proyecto, servicios y precios no desbordan. El editor conserva su
desborde móvil anterior, fuera de los anchos obligatorios de oficina; su
redistribución pertenece a P04/P05. Los hallazgos heredados del cromo y Catálogo
permanecen visibles en los informes de antes/después, sin alterar los detectores.

La captura [`inspector-cantidad-visible.png`](recorrido/inspector-cantidad-visible.png)
usa el desplazamiento real del inspector y muestra 1,56 m × $7.500 = $11.700.
Las cinco superficies nuevas se verifican además con los detectores acotados del
recorrido. Las fallas de transporte de los ensayos de estado son deliberadas;
las verificaciones de permisos, revisión, publicación y precio usan el stack real.

## Pase editorial: dos rondas

Primera ronda:

1. Se eliminó el formulario de extras de texto libre y precio manual de Precios.
   Las definiciones se importan o editan con fuente y regla; las propuestas pasan
   por un diff y pueden descartarse o deshacerse.
2. El inspector agrupa por posición y explica las sugerencias. Regla y fuente
   quedan plegadas; el estimador acepta o descarta con efecto persistente.
3. La presentación monetaria se cuantiza a moneda y declara el ajuste exacto.
   Base y sublíneas suman el neto sellado; no se confunde una tarifa parcial con
   el precio final aplicado.

Segunda ronda:

1. La tabla PDF pasa al ancho completo de la ficha; servicios conserva caption y
   cuerpo juntos. Se emiten y revisan ambas políticas, sin editar lo sellado.
2. Se corrigen contraste del enlace a servicios, radios y brillo heredados
   visibles en el proyecto cotizado, interlineado, historial móvil y vocabulario
   de los nuevos herrajes. El BOM permite partir códigos largos sin desbordar.
3. Se retiran peticiones del estimador a la configuración de pagos reservada al
   dueño. El fixture almacena un PNG real con SHA verificable y la API devuelve
   sus bytes como imagen, con una regresión HTTP que impide procesarlos como JSON.

Momento de firma: extras alineados bajo la posición y servicios en su tabla
comercial. Idea que sube el techo: sugerencias del motor con causa geométrica y
decisión persistente; aceptar, descartar y deshacer se verifican con el producto.

| Rúbrica | Resultado | Evidencia del alcance D06 |
| --- | --- | --- |
| R1 | PASA | Cantidades, dimensiones y moneda en Mono; tarifas sin ceros sobrantes y ajuste explícito |
| R2 | PASA | Tokens de radio y delineado en controles y tablas nuevas |
| R3 | PASA | Reglas/fuentes plegadas y tablas alineadas; sin capas flotantes adicionales |
| R4 | PASA | Naranja reservado para la atención humana |
| R5 | PASA | Teal del sistema de diseño |
| R6 | PASA | Vierteaguas, ensanche, mosquitero y servicios en español; herrajes traducidos |
| R7 | PASA | Controles compactos y definiciones de catálogo plegadas por defecto |
| R8 | PASA | Cinco estados y revisión cerrada, con causa y responsable |
| R9 | PASA | Documento en papel, ficha y vista declarada |
| R10 | PASA | Elección por controles y contorno; sin brillo de selección |
| R11 | PASA | Simbología y dibujos del motor conservados |
| R12 | PASA | Etiquetas, foco de token, controles de teclado y deshacer |
| R13 | PASA | Sin movimiento decorativo; se conserva reduce-motion |
| R14 | PASA | Guardar plantilla o propuesta revisada como acción principal |
| R15 | PASA | Fuente visible y Sin dato con causa; ninguna cantidad o tarifa fabricada |
| R16 | PASA | Nuevas superficies sin degradado, blur, brillo ni morado |
| R17 | PASA | Matriz sin desbordes nuevos; tablas comerciales y servicios legibles |
| R18 | PASA | Persistencia, importación, publicación, precio, emisión y OT con efectos reales |
| R19 | PASA | Sublíneas bajo su posición y servicios del proyecto sellado |
| R20 | PASA | Sugerencias con causa calculada y decisión aplicable/deshacible |

## Validación técnica y límites

Revisión del PR (07-10-2026): las sugerencias del BOM agregado conservan su
módulo; el API calcula compatibilidad por módulo y admite un destino explícito.
Las regresiones aceptan/descartan una propuesta sin modificar el otro módulo.
«Por vano» significa un marco completo: el mosquitero fijo de un marco dividido
cuenta una unidad a sus dimensiones; la regla por hoja cuenta cada hoja, y cada
módulo del ensamblaje conserva su marco. Se mantiene la autoridad del catálogo.

La lectura comercial ahora aplica privacidad a preview, aplicar, retirar e
historial, y al costo de cambios en lote. El estimador recibe venta con causa de
restricción; el dueño ve la autoridad de compra exacta. Se prueban costos de
servicios, agregados, composición y autoridades anidadas; los snapshots internos
no cambian. Playwright pasa 12 lecturas dueño/estimador en los tres anchos de
oficina y ambos temas, sin hallazgos nuevos de extras ni errores de consola;
evidencia `recorrido/navegador-privacy.json` y `privacidad-*.png`. La matriz de
`ux:capture` para Precios se regenera con esta proyección.

La semilla DEMO v6 es aditiva: conserva v1–v5 y omite campos opcionales ausentes
en contratos históricos. Las tablas nuevas llevan organización y RLS;
historial, revisión y precio aplicado permanecen inmutables. Policy y precio
comparten un lock de organización y rechazan cambios concurrentes.

El gate anterior aislado sobre `eadf648b` pasa lint, typecheck, test y build:
647 pruebas del motor (+2 xfail históricos), 1 184 del backend y 725 del frontend.
Database Gate pasa 1 060 pgTAP, 330 integraciones, 11 recorridos E2E y ocho
upgrades poblados PG16; comprueba además la limpieza de sus recursos propios.
Las pinturas verificadas van de 88,5 a 174,2 ms, bajo el límite de 300 ms.
La fuente posterior de privacidad se valida de nuevo antes de integrar; este
resultado anterior no la certifica. Los cuatro checks de CI se registran al
integrar el PR. El primer gate falló
dos selectores E2E anclados a v5; se actualizan a v6 conservando las aserciones
de geometría, BOM, hash, persistencia y tiempo. Ese intento y el intento con
puerto ocupado no cuentan como aceptación completa.

La revisión adicional de permisos (07-10-2026) restringe la columna privada de
accesorios y publica una proyección por organización de sus definiciones y
zonas. 107 pruebas focalizadas PostgreSQL pasan, incluidos catálogo, precio,
MFA, rechazo de lectura directa y aislamiento de tenant. Seis pruebas de UI
incluyen venta por zona y causa de confidencialidad sin controles de costo.
El gate10 detectó una aserción de esquema que todavía omitía los campos
documentados `costs_visible` y `costs_reason`; se actualiza el contrato esperado
y se comprueban sus valores para el dueño. Se conserva cada aserción anterior.
El gate12 final sobre `3d1b98754640e982a971afa1ec9433845bf02709` aprueba
lint, typecheck, test y build: 650 pruebas del motor (+2 xfail históricos),
1 184 del backend y 727 del frontend. Database Gate pasa 337 integraciones,
11 recorridos E2E y los upgrades poblados PG16, con limpieza propia verificada.
El montaje de pg_prove conservaba una fuente anterior; se sincronizan y verifican
byte a byte los 75 archivos SQL del directorio propio y se ejecuta la suite
completa: 1 067 aserciones PASA, incluida `181_accessory_cost_visibility`.
Ese resultado complementa el gate12 y certifica la nueva restricción en RLS.

CI sobre esa fuente pasó lint/typecheck, test y build; el recorrido de proyecto
agotó la espera de la cabecera mientras llegaba la respuesta fría del catálogo.
La prueba ahora espera y valida esa respuesta HTTP con el mismo contrato acotado
que el resto del flujo, antes de exigir la cabecera y ausencia de edición para
el estimador. No se eliminan aserciones ni se cambian los límites del lienzo.
El recorrido focalizado propio pasa completo en 23,6 s, incluida la lectura HTTP
y los permisos del catálogo. Los cuatro checks se vuelven a ejecutar antes de integrar; el cierre con PR y
SHA queda registrado en `docs/cola/ESTADO.md` y la wiki.
El recorrido adicional `navegador-catalog-privacy.json` pasa 12 casos de catálogo
para estimador y encargado, tres anchos y ambos temas. La inspección visual
confirma venta visible y costo restringido; no hay errores, desbordes ni
hallazgos nuevos de accesorios. La matriz formal de catálogo se regenera y las
40 comparaciones globales conservan cero hallazgos nuevos. Las 20 imágenes de
esta lectura y matriz se comprimen conservando exactamente sus píxeles.

El gate11 pasó lint, tipos, 650 motor (+2 xfail históricos), 1 184 backend y
727 frontend; detectó cinco regresiones en publicación. Su causa fue una
lectura de todas las columnas para comprobar existencia de una autoridad.
La comprobación ahora lee solo identidad y organización. Las atestaciones de
`extra_authority` también quedan restringidas por RLS a quienes gestionan
esa organización, manteniendo exactamente su contenido e historial.
Las regresiones de roles incluyen la lectura HTTP y SQL de esas atestaciones.
El chequeo diferido de compatibilidad D03 también leía la fila completa. Ahora
lee únicamente estado, aperturas y organización: se mantienen sin cambios
todas sus condiciones de herrajes, hojas pasivas e inversor. No se amplían
permisos para volver a permitir la lectura privada.

No hecho / riesgos: los precios DEMO son sintéticos y no certifican fabricación.
Se requieren las fichas y tarifas reales descritas en
[`ACTIVACION.md`](../../../operations/ACTIVACION.md). Extras seleccionados sobre
geometrías contorneadas o vidrio sin marco quedan explícitamente incompletos
cuando falta su autoridad; nunca se ignoran ni se libera su fabricación. P07 y
P09 rediseñan la cascada y el documento completos. El
[incidente local previo](../../../operations/INCIDENTE-GATE-2026-10-06.md) permanece
visible; no se afirma conservación de los datos de la base ajena afectada.
