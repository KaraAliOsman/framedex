# P15 · compras, recepción e inventario físico

Base `7196d00d`, rama `codex/P15-compras-inventario`. Verificación con
Supabase, Django, worker, Mailpit y Chromium. Los proyectos, catálogos,
proveedores y suministros de aceptación están marcados DEMO.

## Resultado

Compras muestra qué falta para las OT liberadas, su proveedor y su origen.
Inventario tiene ruta propia y muestra existencia, reservas por OT, tránsito,
ubicación, retazos y movimientos. Se retiraron los KPI decorativos y la sección
de stock de Compras. Una consulta lenta o fallida de necesidades ya no impide
consultar el inventario físico.

Cada fuente sellada se relaciona con su posición y cantidad real. Se excluyen
estaciones que ya consumieron su material. Los pools de stock, tránsito y
reservas se descuentan una sola vez; las OC preparadas se distinguen del tránsito.
El motor elige retazos compatibles, con las mermas declaradas. Confirmar una
compra que depende de retazos reserva su plan en la misma transacción.

F6 explica cada cantidad por OT. Filtrar y paginar limita la compra a las líneas
visibles, con un detalle de cantidades y proveedores antes del clic de confirmación.
El hash protege contra cambios de stock; una clave reutilizada con contenido
diferente se rechaza. Dos decisiones simultáneas generan un único conjunto de OC.

Los precios provienen de la cotización declarada del proveedor; el motor suma
el neto. Sin cotización se muestra **Sin dato**, también en el PDF. El área de
vidrio procede del motor. Los pedidos nuevos muestran unidades de taller.

La recepción conserva guía, fecha, lote, rack y actor. Lo dañado se excluye de
stock útil y de cumplimiento. El excedente requiere confirmación. Las compras
parciales conservan el requisito sellado y su capacidad se serializa en SQL.
El error histórico de stock queda cubierto: un estimador no puede consultar las
líneas documentales directamente, pero la API cruza al rol documental manteniendo
RLS y responde con stock y tránsito correctos.

Los RT conservan suministro, color, largo, origen y destino. La declaración
manual no puede inventar color, identidad, sustrato ni dimensiones mayores que
su suministro. Mover y desechar requieren motivo y confirmación; la historia
con actor es inmutable. La etiqueta abre `/inventory`. Los suministros de D05
con identidad textual conservan su identidad sin convertirla en UUID.

## Recorrido comprobado

1. Liberar una revisión DEMO de dos ventanas fijas; aparecen cuatro necesidades
   ligadas a su OT. Elegibilidades y asignaciones contienen evidencia explícita.
2. Filtrar el proyecto, editar precios y confirmar por UI; se crean OC-000007 y
   OC-000008. Registrar envío con fecha/contacto y confirmar el correo por UI.
3. Recibir dos barras con una dañada: ingreso útil de una barra, guía
   GUIA-P15-PARCIAL, fecha, lote y rack conservados. El stock refleja el ingreso
   inmediatamente; el libro enlaza OC y REC. Recibir el saldo útil por UI.
4. Reservar el material recibido, escanear una pieza a 390 px oscuro y completar
   Corte. Los diez RT previstos aparecen con la misma dirección, origen y rack.
   Este recorrido no registra ajustes de stock.
5. Mover RT-000059 al rack R-02 con motivo; desechar RT-000060 con confirmación
   y motivo; imprimir/preparar su etiqueta QR. La historia conserva al actor.
6. El pool ofrece RT-000062 a una OT anterior con demanda pendiente. Se respeta
   su prioridad; el clic en Inventario reserva el plan completo de esa OT.
   Las OT protegidas de P12/P13 y sus retazos anteriores permanecen intactos.
7. Dos correos entregados a Mailpit, una entrega por OC y un PDF MIME idéntico al
   artefacto sellado. Los fallos de control previo observados durante desarrollo
   se recuperaron con clic humano; no hubo entrega SMTP en esos intentos.

Las capturas de estados vacío/carga/error son pruebas de transporte controlado,
no datos de negocio ni una aceptación de numeración sintética en producción.
Permisos se verifican además contra Postgres/RLS. Las necesidades incompatibles
con la compra sellada tienen causa y acción; los RT consumidos o desechados
conservan consulta e historia, sin acciones físicas incompatibles.

## Evidencia

- [Antes, Compras](captures/compras-inventario/antes-purchasing-1440-claro.png) y
  [antes, Inventario](captures/compras-inventario/antes-inventory-1440-claro.png).
- [Después, Compras](captures/compras-inventario/despues/compras-1440-claro.png) y
  [Inventario 1024 oscuro](captures/compras-inventario/despues/inventario-1024-oscuro.png).
- [Recorrido](captures/compras-inventario/recorrido/resultados.json),
  [reutilización](captures/compras-inventario/recorrido/reutilizacion.json),
  [correo](captures/compras-inventario/recorrido/correo-resultados.json),
  [PDF editorial](captures/compras-inventario/recorrido/pdf-editorial.json).
- [Matriz de estados y tamaños](captures/compras-inventario/matriz/resultados.json).
- `ux-compras/report.json` y `ux-inventario/report.json`: 16 vistas oficiales,
  cero hallazgos, claro/oscuro, 1440, 1280, 1024 y 390 px. La matriz adicional
  contiene doce vistas de escritorio sin desborde ni errores de página.
- 47 pruebas focales de stock/motor; 6 integraciones de compras, RLS, recepción,
  concurrencia y MIME; 19 pruebas frontend focales. `make goldgen` no cambia
  el golden histórico. Los gates completos y CI se registran al cerrar el PR.

## Dos rondas editoriales

Primera: quitar KPI y stock duplicado; explicar cantidades por OT con fuente
exacta; ampliar la causa bloqueante a una fila legible. La consulta de 135 OT
pasa de 51,22 s a 2,31 s al leer snapshots por revisión y reutilizar el catálogo
por petición. Son mediciones locales, no una garantía de tiempo de producción.

Segunda: evitar compras ocultas por filtro/página y mostrar su detalle antes de
confirmar; cerrar envío/PDF/worker y recuperación desde la bandeja de la revisión;
corregir texto pequeño y contraste en oscuro. Se retira el RUT interno del
directorio cuando el proveedor declaró su RUT fiscal. Se traducen unidades de
los nuevos pedidos PDF, conservando los artefactos ya emitidos byte a byte.
La inspección final corrige acabado/pulido, área a dos decimales y huella BOM
del cajetín; los detalles de paneles/herrajes usan medidas y nombres declarados
en vez de claves de implementación. Los previews actuales vuelven a verificarse.

El gate de integración detectó dos regresiones y se corrigieron sus causas:
la caché de autoridad se limita a una propuesta de lectura; el repositorio
ordinario vuelve a detectar cambios y ambigüedades entre transacciones. La
historia RT referencia su dirección permanente, conservando la eliminación
física privilegiada del contrato P02 sin borrar historia ni reutilizar códigos.
La regresión existente comprueba además la retención e inmutabilidad de esa historia.

Momento de firma: **F6 por cantidad y OT**. Capacidad del §8: **Comprar lo que
falta** usa el motor, el stock y los retazos; deja OC reales listas para envío
humano y recepción física.

| Rúbrica | Resultado | Evidencia                                                       |
| ------- | --------- | --------------------------------------------------------------- |
| R1      | PASA      | Qty/Money, unidades y fechas; neto/área del motor               |
| R2      | PASA      | Radios por tokens; detectores sin hallazgos                     |
| R3      | PASA      | Bordes y espacio; sin KPI ni stock duplicado                    |
| R4      | PASA      | Naranja reservado a intervención/marca                          |
| R5      | PASA      | Cromo teal común                                                |
| R6      | PASA      | Vocabulario de bodega, unidades de taller y RUT fiscal          |
| R7      | PASA      | Tabla densa, filtro y páginas de 50; causa aparte               |
| R8      | PASA      | Vacío, carga, error/reintento, permisos y bloqueo               |
| R9      | PASA      | Pedido impreso sobre papel; etiqueta física                     |
| R10     | PASA      | Contorno/foco del RT enlazado; sin elevación decorativa         |
| R11     | PASA      | Iconografía común; sin aperturas inventadas                     |
| R12     | PASA      | Controles nativos con foco; confirmación y detalles por teclado |
| R13     | PASA      | Movimiento común; sin animaciones añadidas                      |
| R14     | PASA      | Una confirmación por compra, recepción o decisión física        |
| R15     | PASA      | Fuente sellada y motor; precio desconocido Sin dato             |
| R16     | PASA      | Sin degradados, blur, brillo ni morado                          |
| R17     | PASA      | Matriz y capturas oficiales sin desborde                        |
| R18     | PASA      | Acciones ejercidas; correo y stock separados                    |
| R19     | PASA      | F6 muestra origen y cantidad por OT                             |
| R20     | PASA      | Compra, reserva, recepción, Corte y RT reales                   |

## Decisiones y límites

La antigüedad se revisa a los 90 días por defecto, configurable en Ajustes ›
General › Documentos. El rack inicial lo fija la preferencia integrada por P13.
No se infiere un precio ni un plazo del proveedor. Se permite comprar menos
que la propuesta, dentro de la capacidad sellada; el faltante sigue visible.

Una optimización separada por OT puede requerir más barras que la consolidación
sellada de la revisión. Se informa `uncovered` y se impide confirmar esa línea:
no se rebaja silenciosamente el faltante ni se amplía un requisito inmutable.
Debe revisarse la planificación o emitirse una revisión adicional. Este límite
conserva el contrato documental de los encargos integrados.

SMTP no garantiza entrega exactamente una vez. Una respuesta perdida queda
sin confirmar y necesita comprobación humana antes de recuperar. Producción
requiere conectar correo, identidad real, catálogo revisado y suministros físicos
según [ACTIVACION](../operations/ACTIVACION.md). Mailpit es sandbox; no se envió
correo a proveedores reales. Los PDF editoriales son previews actuales desde
el snapshot: no sustituyen las primeras versiones emitidas durante la prueba.
