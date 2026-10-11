# P10 · propuesta, decisión y pago del cliente

El portal presenta la marca sellada del fabricante, doce posiciones con
precio unitario y de línea IVA incluido, condiciones y el PDF de la misma
revisión. El cliente compara soluciones completas, elige una y registra su
decisión. La elección es un registro aditivo; ningún documento emitido cambia.

## Recorrido y autoridad

El fixture real del motor emite A y después B, con cantidades diferentes,
servicio de instalación y despacho DEMO. Desde 390 px se elige A dentro de
la oferta B y se acepta con nombre, RUT válido y consentimiento del importe
y las condiciones exactas. La lectura posterior del proyecto y Cobranza
usa A. El PDF A conserva sus bytes después de emitir B. Las pruebas PostgreSQL
verifican además factura, copia de proyecto, compras, producción, calendario,
Hoy y apertura de sucesora desde la solución elegida. Las nuevas mediciones
y el precio del borrador no se dan por acreditados.

Si ya existe una factura ligada a otra solución, la aprobación alternativa
exige conciliación del fabricante. Emitir factura y aceptar comparten el
bloqueo transaccional del proyecto; el documento previo conserva sus bytes
y su importe. Aprobar la solución ya facturada sigue disponible. La consulta
de conflicto es privada y acotada a la organización/capacidad verificada.

Los importes sellados son **$4.446.954 CLP** para la solución A aceptada y
**US$ 7.610,62** para otro fixture de doce posiciones. La suma de posiciones,
servicios/cargos y ajuste explícito coincide exactamente con cada cabecera.
La proyección del motor reparte el impuesto sellado, sin presuponer 19 %,
con `Decimal`. El ajuste por cantidad y moneda se comunica por separado;
un histórico sin autoridad comercial muestra «Sin dato», con causa.

Desde el celular se pide un cambio con comentario obligatorio y posición
exacta, y se rechaza otra oferta sin motivo obligatorio. Las respuestas y
las vistas aparecen en las superficies privadas del estimador. La evidencia
conserva nombre, RUT, fecha, IP, navegador, revisión, huellas y consentimiento.
Las pruebas verifican inmutabilidad, privacidad, tenant, pertenencia exacta
de las alternativas y primera decisión entre dos enlaces concurrentes.

El recorrido de pago rechaza un intento sin descontar saldo, continúa el
cobro ya preparado, registra un único movimiento/recibo de prueba y retorna
al portal correcto. Recargar conserva el resultado consultado en servidor.
Con saldo cero desaparece la acción. La disponibilidad exige aprobación,
oferta vigente, moneda CLP, saldo y proveedor habilitado; el backend rechaza
sobrepago. Un enlace simulado directo tampoco evita esas condiciones.
Una respuesta incierta de Flow conserva la recuperación mediante consulta,
sin repetir el cargo. El contexto de retorno se cifra antes de despachar.

Las preferencias, moneda y tarifas originales del fixture se restauraron;
la lista USD sintética quedó inactiva. Las revisiones y el ledger de aceptación
se conservaron. Ninguna tarifa de aceptación se convirtió en precio productivo.

## Estados y evidencia visual

- [Antes](captures/portal-propuesta/antes/): vigente y reemplazada, escritorio
  y celular, ambos temas.
- [Matriz de estados](captures/portal-propuesta/despues/estados/matriz.json):
  36 vistas de vigente, aprobada, cambios, rechazada, revocada, expirada,
  reemplazada, no encontrada y USD a 1440/390, claro/oscuro; cero desbordes,
  errores de ejecución o hallazgos axe serious/critical.
- [Aprobada final](captures/portal-propuesta/despues/aprobada/matriz.json):
  los cuatro tamaños del contrato y ambos temas, después del pago.
- [Captura oficial](captures/portal-propuesta/ux/index.html): 40 vistas en
  cuatro tamaños y dos temas, sin hallazgos nuevos. El 410 de la capacidad
  revocada es el resultado esperado, con su página dedicada.
- [Recorrido](captures/portal-propuesta/recorrido/): selección A, decisión,
  proyecto/Cobranza, cambios, rechazo y retorno fallido/aprobado.
- [Sucesora permitida](captures/portal-propuesta/sucesora/): el QR histórico
  reemplazado lleva a B solo con permiso sellado del fabricante; nunca ofrece
  pago sobre A. Se verifica a 1440/390 y ambos temas.
- [Estados de superficie](captures/portal-propuesta/estados-superficie/):
  carga retenida, conexión interrumpida y reintento, vacío/bloqueo por inyección
  de fallo, y permisos reales del operario. La inyección no modifica el dominio.
- [Detalles inspeccionados](captures/portal-propuesta/detalles/): portada,
  condiciones y posición con formatos y texto legibles.

El dibujo comparte el renderer y los hechos físicos sellados: vista declarada,
acabado por cara y apertura. Se amplía en diálogo, cambia cara y vista,
y permite zoom/pan con teclado y punteros. A escala inicial se conserva
el desplazamiento vertical táctil. Escape cierra el diálogo.

## Rendimiento

[Lighthouse 13.5.0](captures/portal-propuesta/lighthouse.json) mide **81** en
móvil 390 × 844 sobre build de producción, backend local y doce posiciones,
con el throttling móvil simulado estándar. No es un gate de CI. La lectura
anterior dio 72: se difieren shell/asistente, ajustes e inicio ajenos al portal,
y se comprime su transporte con `Vary: Accept-Encoding`, manteniendo
`private, no-store` y datos exactos. No se cambia el método para alcanzar el mínimo.

## Dos rondas editoriales

Primera ronda:

1. Se elimina la proyección anterior con IVA calculado en React, enum/rechazo
   ambiguo y pago visible sin acuerdo. El documento usa solo autoridad sellada.
2. Se reemplazan tarjetas pequeñas y decisiones genéricas por dibujo ampliable,
   comparación de solución y consentimiento de la revisión y el importe elegidos.
3. Se eliminan footer/marca obligatoria de DEKOPEN y error genérico de enlace;
   emisor, favicon, atribución opcional y estados dedicados comparten su identidad.

Segunda ronda:

1. Las miniaturas usan caras y aperturas selladas, se declara la vista, y el
   gesto inicial permite desplazar la página en celular sin secuestrar el scroll.
2. El saldo CLP con escala decimal precarga el entero correcto; un cobro pendiente
   se continúa en lugar de pedir otro, y el retorno lee su estado verificado.
3. El arranque público deja de cargar el espacio privado; la respuesta comprimida
   conserva autoridad y política de caché. Los controles de formulario declaran
   su efecto de envío, y se borran tres aliases CSS que quedaron sin uso.

Firma F11: una oferta reemplazada explica su estado y, con permiso sellado,
lleva a la vigente sin habilitar pago. La idea del §8 funciona con comparación
de revisiones reales, elección aceptada y cambio referido a la posición exacta.

## Rúbrica editorial

| Ítem | Resultado | Evidencia |
|---|---|---|
| R1 | PASA | Medidas/dinero en Mono, CLP/USD, fecha chilena y ajustes explícitos. |
| R2 | PASA | Tokens de radio ≤ 4 px en documento, formulario y diálogo. |
| R3 | PASA | Jerarquía por borde/peso/espacio; una ampliación flotante. |
| R4 | PASA | Naranja reservado a consecuencia/atención, sin CTA naranja. |
| R5 | PASA | Teal común en controles y selección; papel del documento. |
| R6 | PASA | Trato usted, vocabulario de obra, estados traducidos. |
| R7 | PASA | Densidad document, detalle por posición y controles completos a 390. |
| R8 | PASA | Ocho estados de enlace/decisión y cinco estados de superficie probados. |
| R9 | PASA | Propuesta y elevaciones son papel sobre mesa. |
| R10 | PASA | Opción elegida por contorno/tinte y texto; sin brillo. |
| R11 | PASA | Renderer común, vista declarada, hechos físicos y acabado sellados. |
| R12 | PASA | Foco visible, teclado en zoom/pan, Escape; axe sin serious. |
| R13 | PASA | Sin animación ornamental; reduce-motion del sistema conservado. |
| R14 | PASA | Aprobación principal; cambio/rechazo secundarios y pago solo después. |
| R15 | PASA | Motor/importe sellado; desconocidos con causa y acción. |
| R16 | PASA | Cero gradiente, blur, brillo o morado IA. |
| R17 | PASA | Matrices 1440/1280/1024/390 sin desbordes. |
| R18 | PASA | Decisión, PDF, cambio, dibujo y pago ejecutan su flujo; camino viejo borrado. |
| R19 | PASA | Reemplazada y sucesora permitida preservan F11. |
| R20 | PASA | Comparación, elección real y posición de cambio gobiernan el dominio. |

## Validación y límites

La integración registra los cuatro checks y el SHA del squash en `ESTADO.md`.
Los cuatro gates de código locales pasan: 899 pruebas de motor y dos xfails
preexistentes, golden byte check, 1.493 de backend y 1.002 de frontend, junto
a lint, tipos y build. El gate completo de base de datos registra sus resultados
en la evidencia de integración antes del merge.
Las pruebas de motor incluyen golden CLP/USD revisado, cantidad/redondeo,
servicios y autoridad inconsistente. Las pruebas de backend, frontend y RLS
cubren contrato, consentimiento, aislamiento, carrera, opciones y retorno.

Flow real y el dominio/correo productivos siguen pendientes de activación
externa; el adaptador y su sandbox están implementados. El simulador no mueve
dinero y su procedencia acompaña el saldo/recibo. Flow cobra CLP; USD se
registra manualmente desde Cobranza. El catálogo y las tarifas de aceptación
son DEMO, sin certificación. La comparación ofrece revisiones completas del
mismo proyecto, sin crear una configuración no cotizada ni modificar snapshots.
La aceptación electrónica conserva evidencia; no se le atribuye una firma
electrónica avanzada ni una certificación jurídica externa.
