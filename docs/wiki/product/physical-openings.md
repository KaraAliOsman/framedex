---
type: concept
status: active
updated: 2026-10-06
volatility: medium
verified_ref: 8aa84f7ec8bb15bc7ca7117811cb77e862da04bd
sources:
  - engine/src/dekopen_engine/openings.py
  - engine/src/dekopen_engine/models.py
  - engine/tests/golden_openings.json
  - scripts/check_opening_upgrade.py
  - supabase/migrations/20261231000000_opening_capabilities.sql
  - docs/redesign/captures/aperturas-tipologias/aceptacion.md
---

# Aperturas físicas y composiciones

## Hechos verificados de D03

`Opening` identifica movimiento, bisagras, dirección, rol activo/pasivo y fijo en
hoja. El uso ventana/puerta y las composiciones de hojas o carriles son contratos
separados. Una francesa lleva dos hojas practicables, bisagras en los extremos,
una activa con manilla y una pasiva con falleba e inversor; no se sustituye por
dos bahías con un montante central. La puerta con lateral conserva su montante.

Los doce enums históricos conservan su camino de cálculo y su representación
sellada. El mapeo total preserva incluso la orientación desconocida de una puerta
antigua. La API admite ambos transportes durante esta versión, sin convertir una
notación histórica en autoridad física nueva. El upgrade poblado compara BOM,
precio aplicado, revisión emitida y catálogos anteriores byte por byte.

La autoridad nueva se publica como seis series DEMO v3 con fuente explícita.
No se reescriben v1/v2. Las capacidades vinculan apertura, dirección y rol con
los kits de la misma serie; el encuentro y las manillas tienen reglas con fuente.
El motor obtiene el lado de cierre, las coordenadas y el rango editable. El
transporte del catálogo conserva las medidas anidadas como texto Decimal.

La base de datos rechaza herrajes ausentes, de otra organización, desactivados o
incompatibles, y una pasiva con manilla. El retiro atómico de una serie sin uso
puede retirar sus kits; reactivarla exige recuperar autoridad completa. El rol
de catálogo lee el inspector con el mismo RLS para preservar su holgura, sin
ganar permisos de escritura sobre reglas del inspector.

La paleta usa las capacidades y una vista previa calculada por el motor antes
del clic. Lienzo y PDF declaran vista interior, bisagras y manilla correctas;
continuo hacia el observador y discontinuo hacia afuera. Las ediciones y la IA
usan la misma operación tipada, con deshacer y persistencia comprobados.

El uso de puerta sigue siendo autoridad para la seguridad del vidrio cuando no
existe alias histórico. Vista previa, guardado y precio aplican la misma zona;
una regla obligatoria sin clase de vidrio compatible bloquea los tres caminos.
El asistente exige la bisagra pasiva opuesta antes de ofrecer una pareja; un
catálogo parcial no impide elegir sus aperturas independientes válidas.

## Intención y límites

La constitución §3.6 prevalece sobre el vértice inverso del tablero histórico de
iconos. El estimador debe reconocer la apertura en el dibujo y elegir únicamente
lo que admite su sistema. P04/P05 continúan el rediseño integral del editor.

Los movimientos avanzados están declarados para D08 y todavía no se ofrecen
como capacidad fabricable. Los kits, medidas y precios DEMO no acreditan un
catálogo comercial. La puerta con lateral de 2 200 mm conserva el bloqueo R05
cuando falta inercia estructural: una carga ficticia de prueba no certifica viento.
D04 amplía reglas y selección de herrajes sobre este contrato.
