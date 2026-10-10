# P11 · cobranza, pagos y documentos internos

Base `4de7b9ba`, rama `codex/P11-cobranza-pagos-facturacion`. Verificación con
Supabase, Django, worker, MiMo real, Mailpit y Chromium. Clientes, proyectos y
catálogo son DEMO; los pagos de Flow y folios SIM no acreditan dinero ni DTE.

## Resultado

Cobranza tiene una vista de proyecto de ancho completo. El motor deriva sus
cuotas, cobrado, saldo, exceso y vencido desde el acuerdo sellado y movimientos
vigentes. F6 relaciona cada saldo con el acuerdo y sus recibos. Fecha declarada
prima sobre evento; aprobación pertenece a esa revisión y entrega requiere
comprobantes de todas las unidades vigentes. Una agenda o entrega parcial no
inventa vencimiento. Pagos anulados quedan en la historia y no se suman.

Cada pago manual conserva fecha America/Santiago, medio, referencia, actor y
recibo RC sellado. Monto mayor al saldo se rechaza en backend. Los enlaces tienen
monto, estado y caducidad; el estimador puede crearlos sin leer las llaves de la
organización. Flow verifica pedido, monto, moneda y ambiente en el servidor.
Callbacks simultáneos o anteriores a la respuesta de creación convergen en un
movimiento y recibo; un resultado pagado no vuelve a pendiente. Dinero real
recibido en exceso se conserva para conciliación, en vez de ocultarse del libro.

Sin conexión, el adaptador simulado ofrece una capacidad opaca con vencimiento,
retorno y confirmación. Revisión reemplazada, token incorrecto, monto excesivo
y capacidad vencida impiden el pago. No contacta Flow. Movimientos, saldo y PDF
mantienen la procedencia simulada, incluidos recibos manuales cuyo saldo la incluye.

Factura, boleta y nota de crédito internas conservan emisor, receptor, detalle
humano, cantidad, unitario neto, descuento, neto, IVA y total de la revisión.
La diferencia por presentación de moneda se explica fuera de las filas monetarias,
sin sumarla como un segundo cargo. Emisión repetida devuelve el documento sellado.
La NC conserva su original; abono parcial y anulación total se distinguen al recargar.
La leyenda «Documento interno — no válido como documento tributario electrónico»
es explícita y no imita un timbre SII. Folios SIM y estados aceptado/reparos/rechazado
viven en evidencia separada, inmutable y privada; no consumen CAF ni generan TED.

Hoy del dueño ofrece preparar un recordatorio con MiMo real. El modelo escribe
una plantilla con marcadores; el motor aporta monto y fecha. Preparar no envía.
El dueño revisa y confirma, el worker revalida el saldo antes de SMTP y la outbox
cifrada conserva la intención idempotente. Un saldo con pagos simulados no produce
cobranza real. La aceptación SMTP en Mailpit no demuestra lectura del cliente.

## Recorridos comprobados

1. Aprobar revisión 50/50; preparar el recordatorio con MiMo real y confirmar un
   envío a Mailpit. El reintento conserva la misma intención; no se reenvió como
   una operación nueva durante las verificaciones posteriores.
2. Registrar anticipo por UI, con validación de CLP entero en español y fecha;
   abrir su RC. Crear el enlace simulado por el saldo, completar el pago desde
   390 px, comprobar retorno y repetir el callback: dos movimientos, dos RC,
   saldo cero, «Pagado» y marca de simulación. Un intento sobre el saldo se rechaza.
3. Emitir factura interna y recorrer aceptado, reparos y rechazado del simulador
   SII. Proyectos documentales independientes verifican también boleta, factura,
   anulación con NC y acceso a cada PDF mediante sus controles reales.
4. Descargar quince documentos, comprobar su SHA almacenado y rasterizar el
   papel. Ocho artefactos históricos permanecen idénticos. BOL-0003 y FAC-0004
   ejercitan el renderer final sin sobrescribir los documentos anteriores.
5. Matriz de 41 vistas: Cobranza, F6, Integraciones y Hoy en 1440/1280/1024,
   claro/oscuro; pagador y retorno también en 390. Carga, error/reintento,
   vacío/bloqueado, ausencia de permiso de escritura y F6 por teclado pasan.

El error histórico «No pudimos cargar los links» no se reprodujo en las lecturas
actuales del dueño/estimador sin Flow conectado. Las brechas verificadas fueron
la creación inaccesible al estimador, la ausencia de un simulador y un prellenado
CLP con decimales inválidos. Se corrigieron esas causas; no se atribuye a la
captura histórica una causa que no se pudo comprobar. SQL/RLS y autorización
se verifican además contra PostgreSQL, sin depender de los controles de UI.

## Evidencia

- [Antes](captures/cobranza-pagos-facturacion/antes/cobranza-1440-claro.png),
  [saldo y traza](captures/cobranza-pagos-facturacion/despues/pagado-con-traza-1440.png),
  [validación](captures/cobranza-pagos-facturacion/despues/validacion-espanol.png).
- [Mensaje preparado/enviado](captures/cobranza-pagos-facturacion/despues/recordatorio-ia-enviado.png),
  [retorno móvil](captures/cobranza-pagos-facturacion/despues/retorno-simulado-390.png).
- [Matriz](captures/cobranza-pagos-facturacion/matriz/resultados.json) y
  [documentos sellados](captures/cobranza-pagos-facturacion/pdf/resultados.json).
- `ux-cobranza-proyecto/report.json`, `ux-ajustes/report.json` y
  `ux-pago-retorno/report.json`: 24 vistas oficiales, cero hallazgos finales,
  claro/oscuro, 1440/1280/1024/390. Ajustes pasó tras corregir el contraste oscuro.
- Golden `golden_collections.json`: calendario, saldo, fechas, exclusión de
  anulados, pagos simulados y reparto de NC con Decimal. Los goldens anteriores
  conservan sus valores. Regresiones de Flow, documentos, recordatorios y API
  distinguen autoridad del usuario de capacidad pública del pagador.

Implementación final `9838e8bd9af1116e8797299b0b878a042415d6f7`. Los cuatro gates locales PASA:
`make lint`, `make typecheck`, `make test`, `make build`; 856 pruebas de motor
(+2 xfail), 1.464 backend y 965 frontend. Golden byte check PASA.
`make test-db` PASA: 1.285 pgTAP, 483 integraciones, 19 E2E y upgrades
poblados PostgreSQL 16. CI y squash se registran al integrar.

La revisión de capacidades reproduce el fallo con texto Unicode y lo corrige.
La comparación interna devuelve 404 para tokens ASCII incorrectos, Unicode,
un sustituto aislado, vacío y nulo, antes de consultar el proyecto. La API
conserva su validación del cuerpo; la regresión HTTP usa un token Unicode de
longitud válida y exige 404. Diecisiete pruebas focales pasan.
El E2E espera y valida la simulación real del vidrio antes de comprobar su
selección; conserva todas sus aserciones y comprueba además HTTP 200/valid.
La comprobación del total se acota al resumen visible del proyecto, con una
única coincidencia y texto exacto; no selecciona el saldo de la vista oculta.
La plantilla pública de Magic Link se restauró byte a byte en el bind local
después del reinicio de Docker; no se reinició el fixture ni cambió producción.
Los 100 PNG se comprimieron sin modificar ningún píxel. Las 24 vistas oficiales
son la evidencia posterior a las correcciones editoriales de fechas y códigos;
la matriz funcional de 41 vistas precede ese ajuste de presentación.

## Dos rondas editoriales

Primera: hacer legible calendario/fecha y actor del movimiento; ofrecer el
simulador explícito cuando Flow no está conectado; corregir el prellenado CLP y
su validación en español. Se retiraron estados transmitidos solo por color y
mensajes que presentaban ausencia de proveedor como error de lectura.

Segunda: mover la cobranza del riel a una vista de ancho completo y retirar el
vacío/formulario repetidos; conservar abono parcial de NC tras recarga; explicar
el ajuste PDF sin duplicar el cargo y declarar procedencia simulada en cobrado,
saldo y recibos. Se impide partir fechas/códigos RC y se corrige contraste del
enlace de activación en oscuro. Se conserva un único panel de cobranza.

Momentos de firma: **F6 en saldos**, F2 en el cajetín y F11 en la revisión.
Capacidad que sube el techo: **Hoy prepara una cobranza vencida con MiMo real**,
con monto/fecha del motor y envío humano verificable.

| Rúbrica | Resultado | Evidencia |
| --- | --- | --- |
| R1 | PASA | Money/DateOnly/Mono, montos CLP enteros y códigos sin partir |
| R2 | PASA | Tokens de radios e inglete limitado al papel |
| R3 | PASA | Vista plana por reglas, riel liberado y vacíos duplicados retirados |
| R4 | PASA | Naranja reservado a marca/intervención humana |
| R5 | PASA | Cromo y enlaces con teal común |
| R6 | PASA | Documentos de cobro, voz de usted en pagador/PDF y validación española |
| R7 | PASA | Tablas y formulario compacto, calendario junto al saldo |
| R8 | PASA | Cinco estados ejercidos y simulación explícita |
| R9 | PASA | PDF blanco y cajetín técnico con fuente sellada |
| R10 | PASA | Foco/contorno comunes, sin elevación decorativa |
| R11 | PASA | Iconografía común y elevaciones de la revisión |
| R12 | PASA | Etiquetas accesibles, F6 y controles por teclado |
| R13 | PASA | Movimiento común y reduced-motion, sin animaciones nuevas |
| R14 | PASA | Una acción principal por registro, enlace o documento |
| R15 | PASA | Motor/acuerdo/movimientos; fecha pendiente conserva causa |
| R16 | PASA | Detectores sin degradado, blur, brillo ni morado |
| R17 | PASA | Matriz/UX sin desbordes; fechas/RC íntegros en 1024 |
| R18 | PASA | Pago, enlace, PDF, NC, simulación y correo ejercidos |
| R19 | PASA | F6 relaciona saldo y movimientos; cajetín conserva BOM |
| R20 | PASA | MiMo real prepara, clic humano envía y worker revalida |

## Decisiones y límites

Vigencia por defecto de 7 días (1–90), simuladores explícitos habilitados y SII
desactivado hasta certificación declarada. Ajustes conserva estos valores;
fechas/eventos de cuotas pertenecen a la revisión emitida. Se registran en
[valores por defecto](../decisions/valores-por-defecto.md).

Flow y SII reales quedan pendientes de conexión del dueño según
[ACTIVACION](../operations/ACTIVACION.md). El timbrador existente admite 33/61;
la boleta 39 real requiere un proveedor autorizado y no se ofrece como soportada.
P11 no implementa firma ni certificación propias. SMTP productivo, catálogo
real y datos del contribuyente también requieren activación. El ensayo usa
Mailpit y proveedores simulados; no envió correos ni cobros a terceros reales.
