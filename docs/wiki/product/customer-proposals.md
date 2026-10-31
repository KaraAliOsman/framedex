---
type: concept
status: active
updated: 2026-10-11
volatility: medium
sources:
  - backend/documents/agreements.py
  - backend/portal/proposal_service.py
  - backend/portal/payments.py
  - backend/tests/integration/test_proposal_v2.py
---

# Propuesta y acuerdo comercial

La intención del dueño es que el cliente comprenda qué compra, elija y
decida desde su celular con la identidad del fabricante. La implementación
P10 ofrece alternativas selladas completas del mismo proyecto. La oferta
vigente mantiene su revisión; `quote_decisions` liga oferta y solución elegida,
huellas, decisión y evidencia personal inmutable. Un token público puede leer
el estado y el documento; la evidencia personal queda en la consulta comercial.

El resolver comprueba tenant, proyecto, revisión, hash y los cuatro bloques
que realmente se ofrecieron. Usa después la versión íntegra, incluyendo
manufactura/BOM; no fabrica con el resumen comercial de alternativas.
La solución aceptada gobierna proyecto, Hoy, cobros/calendario, factura,
compras y liberación de producción. La siguiente revisión preserva la
comprobación de igualdad de la oferta y abre un borrador desde la elección,
sin certificar la nueva medición ni trasladar precio como aplicado.

Cobros, cargos pendientes, compras, producción o una factura de otra solución
exigen conciliación antes de aprobar una alternativa. La emisión de factura
comparte el bloqueo del acuerdo; no reescribe un documento ya emitido.

El motor `gross_quotation` reparte el impuesto sellado entre posiciones,
servicios y cargos. Usa Decimal y muestra ajustes de cantidad/redondeo;
no asume una tasa fiscal ni cambia la deuda histórica. USD conserva su
moneda, aunque Flow solo cobre CLP. Ausencia de autoridad es «Sin dato».

Un pago público se autoriza desde la capacidad ya verificada, con aprobación,
vigencia, saldo, moneda y proveedor. El contexto cifrado se crea antes del
dispatch. El retorno consulta el proveedor; una respuesta incierta conserva
recuperación por GET. El mismo enlace puede continuar su cobro pendiente,
sin exponerlo a una capacidad distinta. El simulador conserva procedencia
de prueba en saldo y recibo; no acredita una transferencia real.

La sucesora pública requiere permiso sellado del emisor, desactivado por
defecto. Un histórico revocado/vencido/reemplazado no ofrece pago ni documento
vigente implícito. Cambiar las preferencias actuales no reescribe autoridad
histórica. La aceptación electrónica preserva evidencia; su calificación
jurídica externa no se infiere de una prueba de software.
