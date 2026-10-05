---
type: state
status: active
updated: 2026-10-05
volatility: high
verified_ref: 353becaf
sources:
  - docs/cola/prompts/IA1-diagnostico-evals.md
  - backend/ai_gateway/evals/cases.yaml
  - backend/ai_gateway/evals/run.py
  - docs/ai/evals/README.md
  - docs/redesign/captures/diagnostico-evals/aceptacion.md
---

# AI acceptance by outcome

## Verified implementation

IA1 adds a 26-case harness using the real agent POST, registered worker handler and job GET under a local fixture JWT and PostgreSQL. Each case always rolls back the product setup, agent writes, route selection, audit and wallet debit. Proposals run through the frontend's `applyDesignOps` registry on a copy and the engine's assembly calculation endpoint. Exact graph, dimensions, openings, SKU, evidence and consequential-write oracles determine success.

The report records raw round documents, provider/grounding failures, rejected operations and their validator reasons, real fixture truth, copied products and engine results. `make ai-evals` runs MOCK; the configured-provider command is documented in [the baseline report](../../ai/evals/README.md).

A PostgreSQL observer regression test verifies that its snapshot inspection restores the caller's role and claims. Legacy projections can restore `authenticated` before an outer worker transaction ends; the rollback harness contains that effect in its observation scope. No production permissions or grants were changed.

## Baseline boundary

MOCK repeated all 26 verdicts/checks/structures/rejections exactly. The real MiMo configuration is used without printing or saving credential values. The report preserves a complete dated run; temperature zero does not guarantee identical responses from the external model.

The casa fixture has 12 positions but no applied prices, emitted A/B revisions or optimized OT. Its catalog is synthetic and cannot authorize manufacturing. Cases needing absent truth retain `contexto_insuficiente`; raw zero prices cannot prove a ranking. Other cases expose missing bay/position operations, ambiguous wire fields, missing authoritative context and literal numeric grounding.

The real browser flow can show a completed job while the operations are all rejected and no product mutation occurred. The harness prevents that UI state from being scored as completion. Inherited assistant style/state/copy failures are retained for IA3/P17; IA1 measures them without changing that UI.

## Owner intent and next verification

The owner's request is that the AI accomplish the requested result, ask when an input is missing and prepare consequential actions for a human click. IA2/IA3 should rerun these same owner cases and inspect the structural/engine results, keeping absent authority separate from a provider failure. Neither the wiki nor an LLM explanation supplies engineering truth.
