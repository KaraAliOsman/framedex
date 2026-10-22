---
type: state
status: active
updated: 2026-10-12
volatility: high
verified_ref: b8e62295bdcbf04c2427b0420551cbb2c1a30eec
sources:
  - engine/src/dekopen_engine/price_workspace.py
  - backend/pricing/workspace.py
  - backend/pricing/resolved.py
  - backend/pricing/visibility.py
  - supabase/migrations/20270110000100_p07_price_workspace.sql
  - supabase/migrations/20270129000000_pricing_read_scope.sql
  - backend/tests/integration/test_pricing_read_performance.py
  - docs/redesign/P07-ACEPTACION.md
---

# Precio del proyecto y confianza en el número

## Precio simple de DEKOPEN 2 · P04a

Verificado el 22-10-2026 en `gpt/dk2-p04a-precio-motor`, sobre `6c3c013d`.
Esta primera entrega incorpora aritmética pura; todavía no activa una política
persistida ni el precio automático del borrador.

`simple_pricing.py` recibe costos de materiales ya resueltos por el motor,
área y una política explícita. Mano de obra e instalación admiten m² o ventana.
El margen conserva el contrato comercial de margen sobre venta:
`precio = costo / (1 - margen)`. El redondeo sube al múltiplo declarado de la
moneda para conservar ese margen objetivo. Cantidad e IVA siguen pasando por
`finish_lines`; una instalación incluida como extra no se cobra dos veces.
Materiales ausentes se rechazan; un precio cero declarado sigue siendo válido.

Los casos `PRO6004-fija` y `PRO6004-abatible` congelan geometría, consumo de
barras/refuerzos, vidrio, herrajes, tornillos, tarifas y desglose comercial en
`engine/tests/golden_simple_pricing.json`. Son datos sintéticos de prueba,
sin autoridad de fabricante ni precios reales del taller. El generador oficial
incluye estos casos; los goldens anteriores permanecen idénticos.

La fórmula histórica por m² y el modo avanzado conservan sus resultados.
Persistencia, proyección de trabajo, emisión y pantalla se entregan en las
siguientes sub-PR de P04, sin crear operaciones APPLIED para un borrador vivo.

## Comportamiento avanzado verificado previamente

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

P20 acota la reutilización a una propuesta y su transacción de lectura repetible.
Los stocks se leen en lote con las mismas reglas de color, precedencia de tenant,
ambigüedad, unidad y longitud desconocida. Las listas completas siguen formando
la evidencia de reprecio: no se recortan los costos para acelerar el cálculo.
Los modelos técnicos y las lecturas de costos se reutilizan dentro de esa
propuesta; la siguiente propuesta vuelve a consultar la autoridad vigente.
La lectura comercial evalúa una vez el mismo conjunto de membresías activas,
roles y MFA. Los permisos de escritura y la proyección pública conservan sus
reglas. La espera del formulario baja a 180 ms y mantiene la protección frente
a respuestas anteriores. Véase la evidencia de rendimiento de la aceptación P20.

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
