---
type: state
status: active
updated: 2026-10-22
volatility: high
verified_ref: gpt/dk2-p04e-precio-pdf-revisable
sources:
  - backend/pricing/working.py
  - backend/tests/integration/test_working_prices.py
  - supabase/migrations/20270210000000_project_working_prices.sql
  - engine/src/dekopen_engine/simple_pricing.py
  - backend/pricing/simple_policy.py
  - supabase/migrations/20270209000000_workshop_pricing_policy.sql
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

## PDF revisable sin bloquear el borrador · P04e

Verificado el 22-10-2026 en `gpt/dk2-p04e-precio-pdf-revisable` mediante
`test_working_quotation.py`, `test_guided_quotation.py` y
`test_working_price_issuance.py`: 26 integraciones aprobadas en PostgreSQL.
La revisión privada puede omitir una operación aplicada. Guarda una propuesta
`AT_ISSUE`, compone importes del motor sin escribir precios comerciales y deja
la obra editable. El borrador temprano también usa esa propuesta.

El clic humano de emisión vuelve a comprobar diseño, costos y política vigentes,
la huella del contenido y los bytes revisados. Solo entonces aplica y emite en
una transacción. Un cambio requiere un PDF nuevo; fallo posterior revierte la
aplicación y conserva la revisión privada. La auditoría inmutable de operación
conserva aprobador/fecha; esos campos no forman parte de la identidad del PDF
automático para que el documento emitido sea exactamente el revisado.

Se ejercitaron política simple y avanzada, dueño y estimador, cambio de margen,
costo y cantidad, replay y dos clics concurrentes. La traducción pública de
errores ocurre después del bucle de reintento de serialización. La interfaz
de configuración y su aceptación visual siguen pendientes de P04.

## Conexión a guardado y emisión directa · P04d

Verificada el 22-10-2026 en `gpt/dk2-p04d-automatismo-emision`. El guardado
canónico de ventanas y cantidades y su borrado refrescan la proyección; los
lotes la calculan una vez al devolver la obra. El detalle expone `working_price`
y venta por ventana sin cambiar el significado histórico de `pricing_current`.
La preparación documental admite una proyección lista. La emisión directa
puede omitir `pricing_operation_id`; confirmarla registra y aplica el precio
dentro de la transacción repetible de emisión. Error documental revierte todo
y repetir emisión devuelve la misma revisión. Dueño y estimador se verificaron
en PostgreSQL, incluida la privacidad del desglose y la conservación de emitido.
El PDF privado y el envío guiado aún necesitan su adaptación antes de cerrar P04.

## Proyección privada del borrador · P04c

Verificada el 22-10-2026 en `gpt/dk2-p04c-precio-vigente`. La función
`refresh_working` recalcula costos actuales y guarda una proyección privada por
revisión. No escribe precios aplicados ni modifica el diseño. La política nueva
se refleja al recalcular; un costo ausente reemplaza la proyección anterior por
un bloqueo con causa. Los cinco modos avanzados simulan su contrato existente
y conservan la necesidad de aprobación cuando corresponde.

Las guardas SQL impiden escribir sobre una revisión emitida o con precio
aplicado. El estimador recibe únicamente importes de venta; BOM y desglose de
costos permanecen privados. Los extras conservan su tarifa explícita y el motor
calcula cantidades, servicios, IVA y partición documental, incluso precio cero.
Se verificaron 25 integraciones de política/proyección y ocho aserciones pgTAP
en la base sintética aislada. HTTP, hooks de edición y emisión siguen pendientes.

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

## Política por empresa · P04b

Verificación local del 22-10-2026 en `gpt/dk2-p04b-politica-empresa`.
`workshop_pricing_policies` conserva servicios/unidades, margen, redondeo,
merma, IVA, moneda e interruptor avanzado por organización. El dueño con MFA
puede configurarla; otros roles no leen sus costos directamente. El rol interno
del calculador mantiene RLS. Cada escritura incrementa revisión y registra
actor, motivo y versiones anterior/nueva en el historial inmutable de precios.
La primera inserción y las actualizaciones concurrentes se serializan;
una revisión obsoleta responde 409 y no sobrescribe el cambio ganador.

`GET/PUT /api/v1/pricing/simple-policy/` distingue sugeridos de política
guardada. Leer no confirma sugeridos ni escribe filas. Las reglas avanzadas
previas aportan los valores iniciales cuando existen y permanecen intactas.
Los valores de servicios ofrecidos sin reglas son sugerencias editables del
taller; jamás precios de materiales ni cifras del manual de un fabricante.

`POST /api/v1/pricing/simple-policy/example/` calcula una unidad de una ventana
en borrador con sus medidas, BOM y costos vigentes. La lectura completa usa
una transacción repetible y recupera conflictos de serialización. No crea
operaciones ni modifica precios. Sin ventana devuelve importes ausentes y una
acción para crearla, sin inventar un ejemplo comercial.

Esta API aún no activa el precio automático ni modifica cotizaciones emitidas.
El automatismo y la pantalla corresponden a las siguientes subentregas de P04.

## Pantalla simple de Empresa · P04f

Verificado el 22-10-2026 en `gpt/dk2-p04f-empresa-precios`, sobre `332a75ff`.
`SimplePricingSettings` reúne servicios/unidades, margen sobre venta y redondeo;
merma/IVA/moneda y reglas avanzadas se revelan al necesitarlos. El ejemplo usa
el endpoint real con una ventana del borrador; no inventa materiales ni guarda
al consultar. La entrada porcentual conserva exactitud con strings/BigInt.
Guardar conserva revisión optimista e invalida consultas de obra de la empresa;
un conflicto deja el borrador visible hasta recargar. Solo OWNER solicita costos.

La API normaliza la notación Decimal a texto plano en el ejemplo y desglose
público, sin redondear ni mutar caché/evidencia. La allowlist del estimador no
agrega campos privados. Regresiones HTTP y de precio público comprueban esta
frontera. Dos E2E, cinco unitarias UI y 25 integraciones aprueban;
[aceptación](../../redesign/captures/dk2-p04f/aceptacion.md) conserva capturas y
límites. Total/popover de obra y flujo UI de emisión siguen pendientes en P04g.

## Comportamiento avanzado verificado previamente

La aceptación histórica siguiente corresponde a
`b8e62295bdcbf04c2427b0420551cbb2c1a30eec`, del 12-10-2026.

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
