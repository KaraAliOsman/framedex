---
type: synthesis
status: active
updated: 2026-10-10
volatility: medium
sources:
  - docs/redesign/P11-ACEPTACION.md
  - engine/src/dekopen_engine/collections.py
  - backend/projects/payments.py
  - backend/projects/payment_links.py
  - supabase/migrations/20270119000000_collection_authority.sql
---

# Cobranza y evidencia del cobro

El motor proyecta calendario, cobrado, saldo firmado, exceso y vencido desde el
acuerdo sellado y movimientos vigentes. Una fecha declarada prima sobre el
evento; aprobación usa la decisión de esa revisión y entrega exige comprobante
de todas las unidades de las OT vigentes. No se usan fechas de agenda para
inventar deuda vencida. Anulados no se suman; pagos simulados siguen visibles.

El registro manual fija fecha America/Santiago, actor y recibo RC inmutable.
F6 relaciona saldo, acuerdo y movimientos; la cobranza tiene su propia vista
de proyecto de ancho completo. El estimador crea enlaces sin necesitar acceso
a llaves de la organización. La consulta no depende de Flow conectado.

Flow real verifica el token contra el proveedor en el servidor; monto, pedido,
ambiente y vínculo deben coincidir. Proyecto y enlace se bloquean en ese orden.
Un callback anterior a la respuesta de creación no pierde «Pagado» ni la URL
de un cobro pendiente. Replay y recuperación convergen en un único movimiento
y recibo. El RC conserva los datos de la revisión que originó el enlace,
incluso después de repricing. Dinero real recibido en exceso se registra y
exige conciliación humana; no se omite del libro.

El simulador no contacta Flow. Su capacidad opaca vence, el monto no puede
superar el saldo y una revisión sustituida bloquea la confirmación. Conserva
la procedencia en movimientos, recibos y saldos. No es un cobro real.

Factura, boleta y NC internas se sellan con detalle humano y totales del motor.
El ajuste de moneda explica cantidad × unitario = total sellado; no se añade
como un segundo cargo. Un documento por revisión, replay idéntico; la NC
conserva el original y distingue abono parcial de anulación total al recargar.
La leyenda interna es explícita y no imita un timbre tributario.

El adaptador SII real existente soporta 33/61; la boleta 39 tributaria sigue
requiriendo un proveedor autorizado. La simulación 33/39/61 guarda folio SIM
y aceptado/reparos/rechazado en evidencia separada, sin CAF/TED/XML ni envío.
Conexión real exige declaración del dueño, certificado vigente y transporte;
las [instrucciones de activación](../../operations/ACTIVACION.md) delimitan
qué está construido y qué debe aportar el contribuyente.

Hoy del dueño prepara un recordatorio con MiMo real. El modelo solo escribe
una plantilla con cuatro marcadores; montos y fechas provienen del motor.
El envío requiere revisión, clic y confirmación, conserva auditoría y outbox
cifrada, y comprueba el saldo nuevamente antes de SMTP. Un mensaje obsoleto
no se manda. Los saldos simulados no generan cobranza real.

La aceptación usa catálogo/clientes/obras DEMO y Mailpit. Los pagos de ensayo
y estados SIM no certifican proveedores ni acreditan ingresos reales.
