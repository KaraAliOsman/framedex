# DEKOPEN — product direction

DEKOPEN is an AI-native engineering and quoting product for window/door
professionals. The bar: a real fenestration company could run daily work in it —
configure products, see manufacturability and price, produce BOM/cutting data —
without ever thinking about the repository behind it.

## What the product is

- **Unified workspace.** The configured product is the center: project/position
  context, object hierarchy (product → assembly → module → member/filling),
  canvas, contextual properties, validation, price, BOM, history.
- **Compositional product model.** Products are assemblies of modules joined by
  explicit couplings (angle, coupler profile, transform). Bow and bay windows are
  templates over that model, not enum branches. Geometry validity is independent
  of catalog completeness.
- **Direct manipulation + undo/redo.** Users edit physical objects; every edit is
  a typed domain operation with a stable before/after, so undo is reliable and AI
  uses the same operations as the UI.
- **Workshop language.** Validation explains what is wrong, why it matters, and
  how to fix it — one-click safe corrections where possible.

## AI as a core interface

The agent operates through the same typed product operations the UI exposes —
never manufacturing numeric truth itself:

```
user intent → agent reasoning → typed proposed actions → deterministic engine
evaluation → validation → understandable diff → apply (undo is the safety net)
→ history/audit
```

Provider-neutral boundary: the domain tools are the product; the model is
replaceable reasoning. Candidate interaction surfaces: command bar, contextual
agent, inline "fix" actions, explain-selection, generate-alternative.

## Design bar

Precision and direct manipulation (pro CAD), speed and command workflows
(Linear/Raycast), progressive disclosure and immediate feedback (Duolingo),
restrained intentional hierarchy. DEKOPEN looks like itself — no generic SaaS
cards, no AI-startup gradients, no arbitrary choices. Judge UX in the running
product, not in JSX.

## Capability roadmap

1. Compositional product model + bow windows end-to-end (module count, widths,
   coupling angles, equal-module, per-module openings, validation, BOM).
2. Bay/coupled assemblies on the same mechanism (straight/angular couplers,
   corner relationships).
3. Non-rectangular contours (trapezoids, angled tops, arches) — geometry and
   editing first; manufacturing only where catalog authority exists.
4. Full undo/redo across all authoring operations.
5. Agent tool surface over the shared domain operations.
6. Depth where it pays: cutting optimization, planning, documents, 3D.

Reference implementation for the domain: Oknosoft windowbuilder ecosystem —
study it for mature fenestration concepts (contours, generatrix, fillings,
connections, layers); DEKOPEN reproduces capabilities through its own
architecture.
