---
type: state
status: active
updated: 2026-10-09
volatility: high
verified_ref: codex/P07-workspace-precios
sources:
  - engine/src/dekopen_engine/price_workspace.py
  - backend/pricing/workspace.py
  - backend/pricing/resolved.py
  - backend/pricing/visibility.py
  - supabase/migrations/20270110000100_p07_price_workspace.sql
  - docs/redesign/P07-ACEPTACION.md
---

# Precio del proyecto y confianza en el número

## Comportamiento verificado

La lectura principal compara el aplicado con una proyección sin guardar.
La cascada y el Δ son del motor. OWNER y WORKSHOP_MANAGER conservan compra;
ESTIMATOR recibe solo venta por allowlist, incluidas sus trazas públicas.
Las listas, FX, cobertura de SKU y auditoría se administran por separado.
Ajustes abre la banda sin exigir conocer la ruta de administración.
Costos, matrices, tarifas e importación usan la moneda de su autoridad;
una autoridad sin moneda declara Sin dato. CLP/USD/moneda ausente tienen
regresiones y el registro USD se inspecciona en ambos temas.

El motor conserva el costo consumido de barra con precisión 80 y agrega
composición/cascada con precisión 256. No reparte residuales. Neto de línea,
IVA por proyecto y lectura del unitario conservan las reglas de venta.
La regresión de integración mantiene el unitario histórico `499.8074`;
12/100 posiciones y cantidad tres quedan fijadas por golden e integración.

El repricing recorre autoridades congeladas sin I/O en orden:
cantidad → medidas → vidrio → herrajes → diseño → lista de costos → FX →
lista comercial → margen → descuento → segmento → servicios → impuesto.
La interacción se atribuye al paso posterior y la suma cierra el Δ.
Si un intermedio no es físicamente válido o el histórico no tiene evidencia,
la explicación declara Sin dato con causa. No se consulta el catálogo actual.

Salir de la banda 25/35/60 % o exceder 10 % de descuento exige aprobación.
El dueño puede configurar esas reglas; la aplicación las relee bajo bloqueo
asesor, evitando carreras con una edición de política. Aprobar/rechazar
registra actor y comentario, y la decisión llega a Hoy/campana del solicitante.
Los recibos de lectura son append-only, por tenant y solicitante, e idempotentes.

## Intención del dueño y límites

P07 pide confiar en cada peso, mover el margen viendo la utilidad y pedir
aprobación desde el mismo workspace. F6 muestra entradas y autoridad real.
El aviso DEMO sigue la serie técnica aunque se use una lista humana.
Una revisión cerrada bloquea aplicar y enlaza al proyecto.

El historial consulta las últimas 100 operaciones por organización y agrupa
por revisión; identifica actor, campos y emisiones. El catálogo DEMO no
certifica un fabricante y los históricos incompletos no se reinterpretan.
Emisión/PDF mantienen sus contratos propios. Véanse
[aceptación](../../redesign/P07-ACEPTACION.md),
[valores](../../decisions/valores-por-defecto.md) y
[documento sellado](quotation-document.md).
