---
type: concept
status: active
updated: 2026-10-08
volatility: medium
verified_ref: 52f3ee8102753727b7ba9e568ec18593b5d269d3
sources:
  - P05 PR #131, CI run 37861454814 on 10805d86, squash 52f3ee81, 2026-10-08
  - engine/src/dekopen_engine/symbols.py
  - engine/src/dekopen_engine/drawing.py
  - engine/tests/fixtures/symbols/
  - docs/PRD/opening-symbols.md
  - docs/redesign/P05-ACEPTACION.md
---

# Dibujo de aperturas y cotas

## Hechos verificados de P05

La gramática Decimal del motor se exporta a TS con guarda de sincronización.
Python, React y PDF comparan 56 fixtures en mm, con discontinuidad, flecha y
manilla. La vista interior/exterior espeja una sola vez y contrarrefleja texto.
Las puertas usan triángulo de giro; no dibujan planta en la elevación.

Cada hoja móvil declara viaje; jamba y carriles incompatibles se rechazan. El
transporte histórico sin viaje conserva bytes/BOM y se rotula inferido. Carril
0 exterior es una convención explícita, sin autoridad del fabricante. La planta
usa cada bahía exacta; sin layout no se inventa franja de carriles.

El motor produce cadenas a ejes y extrema exactos del contorno, incluyendo
cardinales del arco. La altura total no se sustituye por el arranque nominal.
Las cotas cortas y módulos apilados reservan niveles fuera del conjunto.
Los dibujos de referencia DEV no habilitan fabricación sin acoplador autorizado.

El portal proyecta hojas/manillas de la revisión sellada mediante lista pública
de campos; excluye costos/fuentes privadas. Agrupar posiciones incluye geometría
sellada, por lo que no combina hojas de distinta autoridad.

## Intención y límites

Un fabricante debe leer movimiento, cierre y vista sin ambigüedad. Los fixtures
reservados de movimientos avanzados son gramática; D08 aporta capacidad real.
P06 mantiene bow, P07 el portal comercial y P09/P13 la composición documental.
Catálogo DEMO y orden de carriles no acreditan datos de un proveedor.
