---
type: state
status: active
updated: 2026-10-07
volatility: high
verified_ref: 383a013e8dacc8651165c3b321dfd92a96bb2f6a
sources:
  - docs/cola/prompts/IA1-diagnostico-evals.md
  - backend/ai_gateway/evals/cases.yaml
  - backend/ai_gateway/evals/run.py
  - docs/ai/evals/README.md
  - docs/redesign/captures/diagnostico-evals/aceptacion.md
  - docs/ai/evals/2026-10-07-ia2-mimo.json
  - docs/ai/evals/2026-10-07-ia2-comparativa.md
---

# AI acceptance by outcome

## IA3 · medición vigente (07-10-2026)

La corrida final completa MiMo sobre `dd98ba5634f1f7ab0ccb653206e4bf06ea39742d` pasa 22/26:
editor 13/13, proyecto 6/8, planta 1/3
y general 2/2. Editor/proyecto 19/21. Conserva dominio,
auditoría y billetera sin cambios; el delta físico explícito es 56 llamadas
y 109 eventos. Véanse [aceptación](../../ai/IA3-ACEPTACION.md) y
[comparativa completa](../../ai/evals/2026-10-07-ia3-comparativa-final.md).

La corrida previa IA3 19/26 y la histórica IA2 21/26 permanecen completas,
sin seleccionar resultados de otras ejecuciones. La fuente ejecutada es estable
y los fallos del fixture/oráculo se conservan. Véase [proveedor](../product/ai-provider.md).

## IA2 · medición vigente (07-10-2026)

La corrida completa con MiMo real sobre `5224dbfb` mide **21/26**:
editor 13/13, proyecto 6/8, planta 0/3 y general 2/2. La meta de IA2 se
cumple con **19/21 (90,48 %)** en editor/proyecto. Los informes confirman
fuentes ejecutadas y estado persistente sin cambios; ninguna acción
consecuente se ejecuta. No se mezclan mejores casos de corridas anteriores.

La corrida final no registra errores del proveedor y J01 pasa; el error de
la corrida anterior se conserva en el log histórico. J04 carece de precios
aplicados y J08 de revisiones emitidas A/B. F03 exige cobertura de compras
inaccesible al estimador. F01 anuncia una consulta de listado truncado sin
entregar el artefacto exacto; F02 no puede observar la OT solicitada fuera
del listado y pide confirmar la revisión. Ambos se puntúan como incorrectos,
aunque no inventan una cantidad de barras ni ejecutan una escritura.

Las operaciones nuevas se juzgan con aplicación real de la transacción de
proyecto dentro del rollback, además del motor y sus oráculos exactos. La
equivalencia de aperturas físicas conserva sentido, bisagras y papel de hoja;
un alias histórico no autoriza editar una corredera en una serie practicable.
UI/IA/API comparten el registro de 50 operaciones y consumen efectos del motor.
La vista previa dibuja hojas/manillas de esa autoridad, también para el antes.

La aclaración de manilla exige antepecho y continúa el mismo trabajo; sus
opciones de vidrio provienen del catálogo real. Las regresiones rechazan cifras
inventadas, referencias no observadas, evidencia de errores/historia del cliente
y propuestas obsoletas. Aplicar/recargar/deshacer conserva estado e identidades.
El rol del worker se restaura tras publicar progreso, sin otorgar permisos nuevos.

La revisión posterior conserva además la preparación documental completa al
eliminar/deshacer, mantiene contornos y módulos sin marco como `product-v2` y
deriva el espesor del vidrio histórico de su receta en el motor o lo deja
desconocido. Las regresiones verifican RLS, IDs/metadatos restaurados y
obsolescencia tras una edición documental. La evaluación completa se repitió
sobre estas correcciones; sus casos no se mezclan con la corrida anterior.

Véanse la [comparativa por caso y categoría](../../ai/evals/2026-10-07-ia2-comparativa.md)
y la [aceptación de navegador y rúbrica](../../redesign/captures/operaciones-herramientas/aceptacion.md).
El PR [#126](https://github.com/KaraAliOsman/framedex/pull/126) está integrado
por squash `0835e3f0834e2680674458693626617a84cc19f8` con sus cuatro checks
verdes sobre la revisión corregida `3f475b5c`. IA3 continúa proveedor/configuración
y P17 el rediseño del dock/Orb. La medición
histórica de IA1 siguiente sigue siendo la línea base, no el resultado vigente.

## Verified implementation

IA1 adds a 26-case harness using the real agent POST, registered worker handler and job GET under a local fixture JWT and PostgreSQL. Each case always rolls back the product setup, agent writes, route selection, audit and wallet debit. Proposals run through the frontend's `applyDesignOps` registry on a copy and the engine's assembly calculation endpoint. Exact graph, dimensions, openings, SKU, evidence and consequential-write oracles determine success.

The report records round documents with credential redaction, provider/grounding failures, rejected operations and their validator reasons, real fixture truth, copied products and engine results. The execution reference is captured before measuring, with committed source and a final source-consistency check. Fixture project identity is discovered after a clean-stack rebuild. `make ai-evals` runs MOCK; the configured-provider command is documented in [the baseline report](../../ai/evals/README.md).

Graph edits also require an engine-accepted design. Compatibility refusals need negative catalog/engine authority; bedroom duplication preserves design/quantity and requires bedroom destinations; five percent uses the pricing fraction 0.05. Current applied pricing, existing cut plans and A/B comparison authority are loaded when present, rather than permanently marked absent.

A PostgreSQL observer regression test verifies that its snapshot inspection restores the caller's role and claims. Legacy projections can restore `authenticated` before an outer worker transaction ends; the rollback harness contains that effect in its observation scope. No production permissions or grants were changed.

## Baseline boundary

MOCK repeated all 26 verdicts/checks/structures/rejections exactly. The real MiMo configuration is used without printing or saving credential values. The report preserves a complete dated run; temperature zero does not guarantee identical responses from the external model.

The final 48-regression harness measured MiMo at 3/26 (11.5%) and MOCK at 0/26. E03, F01 and G02 pass; F01 verifies the genuinely empty order list, not a populated blocked-order diagnosis. Both complete reports verified unchanged persistent state and unchanged executed source. Earlier runs were replaced after fixing false positives: a current glass mention is not an offered alternative, a requested handle-height note is not the missing installation datum, and LEFT/RIGHT must not be described as the swing direction.

The casa fixture has 12 positions but no applied prices, emitted A/B revisions or optimized OT. Its catalog is synthetic and cannot authorize manufacturing. Cases needing absent truth retain `contexto_insuficiente`; raw zero prices cannot prove a ranking. Other cases expose missing bay/position operations, ambiguous wire fields, missing authoritative context and literal numeric grounding.

The real browser flow can show a completed job while the operations are all rejected and no product mutation occurred. The harness prevents that UI state from being scored as completion. Inherited assistant style/state/copy failures are retained for IA3/P17; IA1 measures them without changing that UI.

## Owner intent and next verification

The owner's request is that the AI accomplish the requested result, ask when an input is missing and prepare consequential actions for a human click. IA2/IA3 should rerun these same owner cases and inspect the structural/engine results, keeping absent authority separate from a provider failure. Neither the wiki nor an LLM explanation supplies engineering truth.
