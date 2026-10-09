---
type: concept
status: active
updated: 2026-10-09
volatility: medium
verified_ref: c01fd3fe720f71ca8acf7ef8d86510d106e73075
sources:
  - P06 PR https://github.com/KaraAliOsman/framedex/pull/138, CI 4/4 sobre a77e21927feef91b7f519266ee5955688cc8f579, squash c01fd3fe720f71ca8acf7ef8d86510d106e73075, 2026-10-09
  - docs/redesign/P06-ACEPTACION.md
  - engine/src/dekopen_engine/assembly_measures.py
  - engine/tests/test_gold_cases_assemblies.py
  - frontend/tests/e2e/editor.spec.ts
---

# Conjuntos y autoridad de acoples

Bow, bay, puerta con lateral, sobreluz y esquina son recetas del mismo
ProductModel. No crean tipos de producto ni ramas nuevas de enum. El
editor comparte selección en planta/elevación, ángulo en la unión,
arrastre/simulación/commit/deshacer y vista desarrollada o proyectada.
Los módulos apilados conservan su huella coincidente: un rótulo común y
una fila de selección permiten elegirlos sin falsear su ubicación.

`CouplerRule` es autoridad opcional: límites de deflexión absoluta,
aporte desarrollado y fuente. El aporte representa separación sobre la
bisectriz de frentes; en STACKED aumenta la altura. No se infiere de SKU,
ancho de cara ni ángulo de corte. Sus límites incluyen los extremos.
El catálogo filtra recetas/uniones; un error identifica el campo o lleva
a la ficha técnica. El motor produce cuerda, desarrollo, proyección,
altura y posiciones de cada módulo. Las juntas se sitúan al centro del
aporte. Sin regla, no aparecen nuevas medidas y se preservan los bytes
de evaluación y artículos históricos.

DEMO v7 es aditivo sobre v1–v6. Declara pivote compartido y aporte cero,
manteniendo BOM/corte/refuerzo/venta. Su fuente declara sintético y sin
certificación; no constituye investigación ni autoridad de fabricante.
El catálogo usado mantiene su bloqueo. La plantilla CSV/XLSX conserva
la regla con fuente en importación/exportación revisada.

El precio indicativo de cada módulo se calcula de forma independiente
en el motor comercial. El residual «Acoples y ajustes» cierra exactamente
el precio unitario del conjunto: incluye uniones y efectos comerciales
comunes; no es un reparto proporcional. La revisión sellada conserva
las cotas usadas por DOC-01 sin consultar autoridad posterior.

Intención del dueño: construir conjuntos con la facilidad de una ventana
y conservar determinismo. Verificación: siete interacciones E2E para
el bow 600/1 200/600 a 22,5°, selección/igualdad después de recargar,
arrastre a 30° y deshacer, rechazo de 89°, cinco recetas y PDF real.
La [aceptación](../../redesign/P06-ACEPTACION.md) conserva evidencia y
límites; 3D de conjuntos pertenece a P19.
