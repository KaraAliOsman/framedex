---
type: synthesis
status: active
updated: 2026-10-10
volatility: medium
sources:
  - docs/redesign/P15-ACEPTACION.md
  - backend/purchasing/needs.py
  - backend/inventory/service.py
  - supabase/migrations/20270118000000_purchasing_inventory_trace.sql
---

# Compras e inventario físico

P15 separa Compra de Inventario. Las necesidades parten de OT liberadas y
fuentes selladas; cantidades, compatibilidad, área y neto proceden del motor.
Stock, reservas, tránsito y OC preparadas tienen significados distintos.
F6 relaciona cada cantidad con su OT. La confirmación compra solo lo visible
en la página revisada y conserva idempotencia, hash de propuesta y capacidad
del requisito. Una demanda que excede esa capacidad queda visible y bloqueada,
sin reescribir el documento original.

Recepciones retienen guía, fecha, lote, rack, OC/REC y actor. Daños no son stock
útil ni cumplimiento; excedentes necesitan confirmación. El cruce al rol
documental para leer tránsito conserva RLS: la falta de SELECT del miembro
sobre líneas documentales no debe convertirse en un error de stock.

Retazos son piezas físicas con RT, suministro, color, medidas y ubicación.
Mover/desechar conserva motivo y actor en historia inmutable. El motor ofrece
material compatible y la reserva recalcula el plan completo dentro de una
transacción. La etiqueta lleva a Inventario. La antigüedad es configurable;
el destino inicial procede de la preferencia de [Corte](cut-documents.md).
Las identidades textuales de [D05](color-finishes.md) no se reducen a UUID.

La OC sella precios declarados y usa el PDF documental. El correo comparte el
adaptador SMTP/Mailpit y la bandeja existente; requiere clic humano. El jefe de
taller recupera correos PURCHASE, conservando los permisos previos de cotización
y pago. El worker consulta la OC con servicio y alcance explícito de organización;
no intenta inferir un miembro desde claims de servicio. Una entrega incierta
requiere comprobación humana. Véase [identidad y correo](brand-identity.md).

La intención del dueño es saber qué falta, qué llega y qué sobra. La aceptación
verifica el flujo local con material DEMO; no certifica un fabricante, no conecta
un proveedor real y no modifica PDFs históricos. Los riesgos operativos y las
pruebas concretas están en la [aceptación P15](../../redesign/P15-ACEPTACION.md).
