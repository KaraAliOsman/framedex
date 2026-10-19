# DEKOPEN — product direction

DEKOPEN is a professional engineering and quoting product for window/door
professionals that a fenestration company can run end to end **without AI**:
configure products, see manufacturability and price, produce documents,
BOM/cutting data and workshop work — without ever thinking about the
repository behind it. AI is an optional copilot that operates the same system
when a person delegates work to it ([owner direction 2026-10-18](research/2026-10-18-direccion-final/README.md)).

## What the product is

- **Manual first.** The base plan is the complete manual quoter: company and
  usual values → client/work → positions → design, dimensions, openings,
  glass, finish → engine/price → document/revision → materials/cut/operation
  by role. No step needs a model, credits or an AI session.
- **Two views of one work.** *Mesa de obra* (default) reads the whole work —
  positions, exceptions, price and deliverable. *Estudio* designs one position
  on a wide canvas. Both show the same work, revision, selection, draft and
  operations; switching view never saves, recalculates or duplicates.
- **Compositional product model.** Products are assemblies of modules joined by
  explicit couplings (angle, coupler profile, transform). Bow and bay windows are
  templates over that model, not enum branches. Geometry validity is independent
  of catalog completeness.
- **Direct manipulation + undo/redo.** Users edit physical objects; every edit is
  a typed domain operation with a stable before/after, so undo is reliable and
  the copilot uses the same operations as the UI.
- **Real catalogs.** Manufacturer → series → configuration/article, with source
  and version. Synthetic DEMO data lives in an explicit laboratory, never in the
  normal path and never renamed as a real brand.
- **Workshop language.** Validation explains what is wrong, why it matters, and
  how to fix it — one-click safe corrections where possible.

## The optional copilot

A global, non-modal popup opened only by the person (button «Asistente» or a
shortcut); it never reserves a column, replaces the inspector or shrinks the
canvas. **Chat** answers and prepares; **Trabajo** executes a delegated goal
with the system's domain tools. Three autonomy policies — *Solo proponer*,
*Con aprobación*, *Omitir todo* — control execution, never role or authority:

```
delegated goal → sealed destination/attachments/policy → typed operations →
deterministic engine evaluation → validation → server postconditions →
receipt (applied / pending / blocked) → undo that protects later manual edits
```

The engine stays the only source of computed numbers; the model is
replaceable reasoning behind a provider-neutral protocol (MiMo 2.6 Pro is the
owner's current selection for every AI plan, without silent fallback).
External effects — issuing, sending, publishing a catalog, buying/paying,
releasing physical work — keep an explicit human click in every policy. AI
plans differ by usage capacity and concrete professional extras, not by a
worse model, less control or fewer finished tasks.

## Design bar

Precision and direct manipulation (pro CAD), speed and command workflows
(Linear/Raycast), progressive disclosure and immediate feedback,
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
5. Copilot tool surface over the shared domain operations (optional plans).
6. Depth where it pays: cutting optimization, planning, documents, 3D.

Reference implementation for the domain: Oknosoft windowbuilder ecosystem —
study it for mature fenestration concepts (contours, generatrix, fillings,
connections, layers); DEKOPEN reproduces capabilities through its own
architecture.
