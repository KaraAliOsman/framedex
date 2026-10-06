---
type: concept
status: active
updated: 2026-10-06
volatility: medium
verified_ref: dc36fe8efa5829a462d1edd0fcd813bfccbe5a3f
sources:
  - engine/src/dekopen_engine/hardware_classes.py
  - engine/src/dekopen_engine/hardware_machining.py
  - engine/tests/golden_hardware_classes.json
  - backend/tests/integration/test_hardware_flow.py
  - supabase/migrations/20270101000000_hardware_classes.sql
  - docs/redesign/captures/herrajes-clases/aceptacion.md
---

# Herrajes por familia y clase

## Hechos comprobados en D04

Integrado por [PR #122](https://github.com/KaraAliOsman/framedex/pull/122),
con los cuatro checks obligatorios aprobados el 06-10-2026. La referencia
verificada es el squash en `integracion/v1`.

La clase pertenece al sistema y al movimiento físico de D03. Sus rangos,
prioridad, relación ancho/alto, altura mínima de compás, componentes, manillas y
opciones tienen fuente. El motor resuelve la clase con la masa exacta de la hoja,
incluida su expansión. La falta de masa bloquea la certificación de compatibilidad.
Un empate entre familias o prioridades no se resuelve por orden de lectura.

Las reglas de cantidad y largo son datos tipados; no admiten expresiones
ejecutables. Componentes por umbral, transmisiones cortables, masa por metro,
manillas por color y opciones de sustitución alimentan BOM y costo Decimal.
La sustitución no suma dos veces las bisagras; las combinaciones duplicadas se
rechazan. La hoja pasiva conserva su herraje propio y no toma la manilla activa.

El estimador consulta la clase y abre F6 para revisar medida, masa, rango,
componentes y fuente. Una reparación propone la siguiente clase o una división
vertical que el cálculo estricto acepta. El diff precede a la aplicación y se
puede deshacer. El precio mostrado es el neto de herrajes con merma/margen,
identificado como tal; la cotización confirma el precio completo de la posición.
El diagnóstico de un límite nunca convierte el BOM original inválido en válido.

La revisión emitida sella la expansión exacta. Picking agrupa SKU, largo y fuente
por OT y revisión; compra y stock consumen los componentes, sin reservar además
un kit agregado. Las piezas cortables conservan su variante de largo. La
precisión anidada nueva no cambia la escala ni los hashes de snapshots históricos.

Mecanizar exige fuente, pieza anfitriona inequívoca, coordenadas dentro de ella,
cara, herramienta, profundidad y cobertura de la cantidad. Una declaración
incompleta aparece como **declarada no emitida** y no permite completar la estación
de mecanizado. No se fabrica una coordenada a partir del nombre del componente.
P14 conectará esta proyección neutral con la configuración de máquinas.

La plantilla D01 transporta la misma autoridad por CSV y XLSX. SQL valida su
estructura finita y semántica sin depender de una extensión ausente en PostgreSQL 16. Tenant, publicación revisada y guardas de inmutabilidad se mantienen.
Seis series DEMO v4 se añaden sin reescribir v1/v2/v3 ni sus precios/snapshots.

## Intención, historia y límites

El dueño exige herrajes fabricables y explicación de cada número. Los cuatro
goldens congelan dos oscilobatientes, una corredera pesada y una puerta; el flujo
HTTP comprueba doce posiciones y el picking por cada componente/largo.
La historia anterior basada en un kit conserva su cálculo y precio.

Los datos DEMO no certifican capacidad, clase RC, viento ni mecanizados de un
fabricante. Las referencias históricas de packs orientan el documento; no son
autoridad de coordenadas. El proveedor debe entregar y revisar sus fichas y
tarifas siguiendo [activación](../../operations/ACTIVACION.md).
Colores de perfiles D05, accesorios D06 y movimientos D08 siguen en la cola.

Véanse [aperturas](physical-openings.md), [catálogo](catalog-authority.md) y la
[aceptación con evidencia](../../redesign/captures/herrajes-clases/aceptacion.md).
