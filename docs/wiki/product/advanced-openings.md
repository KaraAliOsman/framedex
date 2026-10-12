---
type: concept
status: active
updated: 2026-10-11
volatility: medium
verified_ref: d6921a893fcc3b303fcd693bd934380e7227f3d0
sources:
  - engine/src/dekopen_engine/advanced_openings.py
  - engine/tests/golden_advanced_openings.json
  - backend/catalogs/demo_advanced.py
  - supabase/migrations/20270126000000_advanced_opening_authority.sql
  - supabase/migrations/20270126000100_demo_advanced_catalog.sql
  - docs/redesign/D08-ACEPTACION.md
---

# Tipologías avanzadas con autoridad

## Hechos verificados

D08 usa `Opening` y recetas de catálogo para HST, PSK, plegables, pivotes,
guillotinas y puerta corredera. El esquema, perfiles, encuentros, umbral,
eje/plano, recorrido y kits son explícitos. Una serie sin receta conserva
Sin dato con causa y no ofrece el diseño como seleccionable. La biblioteca
identifica las series visibles que lo permiten y enlaza Catálogo.

Siete series DEMO v8 aportan catorce recetas y goldens de cortes/BOM/kits.
Los v1–v7 y los doce enums históricos conservan sus snapshots. Publicar v8
usa migración y no depende de reproducir seed. No se infieren HST G/K.
SQL aplica fuentes y compatibilidad de familia, kit y tenant; el editor
estructurado comparte las validaciones y la autoridad de P16.

Los campos de receta conservan el borrador decimal literal durante la escritura,
incluyendo signo y separador en curso; al salir normalizan sin redondear y
explican los valores incompletos. El modo de hoja de paso sólo altera el vano
plegable; los carriles y polígonos de otros vanos se conservan.

El motor calcula el movimiento y produce geometría cerrada/abierta y ejes.
Los plegables conservan longitud rígida, paquete y cierre de paso independiente.
Las guillotinas declaran muelle/contrapeso y recorrido por hoja/carril.
HST tiene elevación de catálogo; PSK basculación y separación paralela.
El fijo no recibe herrajes. Recetas avanzadas calculan con contexto Decimal
local de 80 dígitos; guardar/preciar/emitir conserva BOM exacta aunque cambie
el contexto ambiental. Los históricos mantienen su camino aritmético anterior.

Python, PDF y React comparten símbolos. La proyección visual JS compara a
0,01 mm; no se convierte en autoridad de fabricación. El transporte exacto
del motor y el PDF conservan Decimal. La planta explica trazo cerrado/abierto.
El portal proyecta la revisión sellada sin exponer costos ni fuentes privadas.
Se ejercitan las catorce recetas, 84 vistas, emisión DOC-01 y dos propuestas
MiMo reales. Véase [aceptación](../../redesign/D08-ACEPTACION.md).

## Intención y límites

El estimador debe reconocer también las ventanas difíciles y conocer qué falta
para habilitarlas. Los kits, capacidad, medidas y precios DEMO no certifican
un fabricante ni un cálculo de viento para obra. Se exigen fuentes reales
para producción. P19 continúa el 3D con estas hojas y recorridos del motor.

Relacionadas: [aperturas físicas](physical-openings.md),
[dibujo común](opening-drawings.md), [catálogo técnico](catalog-authority.md).
