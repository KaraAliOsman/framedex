# DEKOPEN — AGENT OPERATING MODEL (v1.0)

> **Status:** OPERATING GUIDANCE — NON-NORMATIVE
> **Target Agents:** Astra, Claude, Codex, Gemini, Antigravity, and Future Autonomous Engineering Agents
> **Normative Authority:** The supreme governing rules of this repository reside exclusively in [`docs/CONSTITUTION.md`](./CONSTITUTION.md) (v1.3 MASTER — 23 Rules) and [`docs/PRD/PLAN_SHOTS.md`](./PRD/PLAN_SHOTS.md). This document establishes operational discipline, context ergonomics, and engineering execution doctrines.

---

## 1. Production-Grade Doctrine

Dekopen is constructed incrementally shot by shot (**SHOT-01** to **SHOT-24**). An incremental development roadmap is strictly separated from software quality:

```
INCREMENTAL SCOPE != PROTOTYPE QUALITY
EVERY ACCEPTED INCREMENT MUST BE PRODUCTION-GRADE WITHIN ITS AUTHORIZED SCOPE
```

A planned future capability that is not yet implemented does **not** make existing closed shots a "prototype". Every increment merged into `main` must be engineered to stay permanently in the production product within its authorized boundary.

### 1.1. Explicitly Forbidden in Any Increment
The following practices are never considered production-grade and must not be introduced or accepted:
- **Fake Success:** Operations reporting success without executing real underlying work.
- **Phantom Persistence:** Forms or buttons that visually simulate saving or updating data but fail to commit transactions.
- **Buttons Without Contracts:** UI controls lacking actual event handlers or contract-backed APIs.
- **Hidden Placeholders:** Hardcoded values masquerading as calculated or dynamic domain data.
- **Mocks/Stubs in Production Paths:** Test stubs, in-memory mocks, or fake adapters leaking into runtime services.
- **Silent Fallbacks Changing Results:** Catch-all fallbacks that quietly substitute incorrect values instead of failing cleanly.
- **Invented Technical Data:** Profile dimensions, thermal values ($U_w$), sound attenuation ($R_w$), or prices fabricated outside `/engine` or certified catalog inputs.
- **Misused Synthetic Fixtures:** Treating `DEMO_60` (or any synthetic fixture) as certified manufacturer or commercial authority. `DEMO_60` is strictly a synthetic test fixture.
- **Swallowed Exceptions:** Catch blocks that suppress errors without logging or appropriate domain recovery.
- **Security / RLS Bypasses:** Skipping `current_user_org_ids()` isolation or tenant guards for convenience.
- **Dead UI State:** Visual representations decoupled from the reactive client store or engine results.
- **Unverified Numeric Outputs:** Numbers in quotes, cut lists, or work orders originating outside `/engine` or explicit human input.
- **Untyped API Endpoints:** Public or internal API routes lacking OpenAPI schemas, serializers, or typed client models.
- **"Works on My Machine":** Relying on subjective local operation instead of reproducible deterministic gates.
- **Implementation-Echoing Tests:** Trivial tests that merely mirror source code without verifying business behavior or boundary mutations ($\pm 0.01\text{ mm}$).
- **Bypassed / Skipped Gates:** Weakening, filtering, or ignoring required DoD checks or CI contexts.
- **Accepted Visual Degradation:** Known broken layouts, clipping, contrast failures, or missing states accepted as "good enough".
- **Token-Saving Shortcuts:** Leaving work partially done under the pretext of context limits.

### 1.2. Scope vs. Quality Boundary
- **High Quality within Current Scope:** Polish, type, test, and harden the authorized work of the active shot.
- **No Premature Implementation:** Do not secretly implement future shots or unapproved scope just to make an increment feel larger. Quality means perfection within the assigned boundary.

---

## 2. Context Model: The Repository Is Memory

```
REPO = MEMORY
AGENTS = MAP
PROMPT = GOAL + DELTA + SUCCESS CRITERIA + STOP CONDITION
```

The long conversational chat history is ephemeral and is **never** the normative authority of Dekopen. The repository files are the persistent ground truth: *"The agent forgets, the repo doesn't."*

### 2.1. Standard JIT Reading Ladder
When beginning or resuming a task, load only the context necessary for the active scope, in this strict order:
1. [`AGENTS.md`](../AGENTS.md) — The operational map and entry protocol.
2. [`docs/CONSTITUTION.md`](./CONSTITUTION.md) — The 23 Supreme Constitutional Rules.
3. [`docs/PRD/PLAN_SHOTS.md`](./PRD/PLAN_SHOTS.md) — The master roadmap, sequence, and contractual gates.
4. Current `docs/plans/PLAN_SHOT-XX.md` — The active shot's plan and approved design decisions (PDs).
5. Only the specific affected PRDs (in `docs/PRD/`) and relevant source code.

### 2.2. What NOT to Load by Default
- Do not ingest entire monolithic historical files (`DEKOPEN_BIBLIA_COMPLETA_*.md`).
- Do not load all 24 PRDs simultaneously.
- Do not load historical plans from past, closed shots unless verifying an explicit upstream contract interface.
- Do not load files under `docs/archive/**`.

### 2.3. Authority Status of Ancillary Documents
- **`docs/archive/**`:** `HISTORICAL / NON-NORMATIVE`. Archival context only; holds zero power to veto or block active development.
- **`DEKOPEN_BIBLIA_*.md`:** `NON-NORMATIVE VIEW`. Generated snapshot views for human reading; if any discrepancy exists, active individual files in `docs/PRD/` and `docs/CONSTITUTION.md` govern completely.

---

## 3. Token and Context Efficiency Doctrine

```
TOKEN/CONTEXT EFFICIENCY IS ALLOWED ONLY WHEN QUALITY IS PRESERVED OR IMPROVED.
TOKEN SAVINGS MUST NEVER REDUCE TASK COMPLETENESS OR QUALITY.
```

### 3.1. Legitimate Token Savings
Token efficiency is an engineering discipline of maximizing signal-to-noise ratio:
- **JIT Context Loading:** Read only the files relevant to the current decision or module.
- **Direct Navigation:** Grep for exact symbols, files, and paths rather than dumping whole directories.
- **No Re-narrating History:** Do not restate the background of the entire project or past closed shots in responses.
- **Targeted Verification Cycles:** Run fast, focused tests (e.g. `pytest engine/tests/test_x.py`) during development iterations.
- **Concise Outputs:** Present structured diffs, exact test traces, and clear delta reports without boilerplate padding.
- **Reasoning Escalation:** Scale reasoning effort to the difficulty of the task (see Section 8).

### 3.2. Prohibited Token-Saving Anti-Patterns
Never sacrifice rigor to save tokens:
- Never skip edge cases, negative assertions, or mutation tests.
- Never omit required real-browser E2E, multi-tenant RLS, or database upgrade gates.
- Never truncate implementations by leaving `TODO`, `pass`, or placeholder functions in production paths.
- Never substitute actual test execution with speculative claims (e.g. "tests should pass").

---

## 4. Agent Autonomy and Bias Toward Action

Agents acting as Lead Builders are expected to operate with high engineering initiative:
- **Infer Scope Accurately:** Derive requirements from the user request, repository state, active `PLAN_SHOT-XX.md`, and canonical PRDs.
- **Bias Toward Action:** Proceed autonomously with reversible engineering tasks without halting to ask permission for:
  - Internal variable, helper, or file naming (following codebase conventions).
  - Flexible UI layout composition that satisfies the capability contract.
  - Internal refactoring of components or functions that preserves external observable behavior.
  - Adding necessary unit, integration, or contract tests.
  - Using tools, linters, formatters, and typecheckers.
  - Routine bug fixes and error resolution during the self-healing loop.
  - Any non-material decision under Rule 0.

### 4.1. The Three Legitimate Stop Conditions
Under Rule 0, the agent must **STOP IMMEDIATELY** only when:
1. **New Material Contradiction:** A genuine contradiction between normative sources (Constitution, PRD, Golden case, DB schema, or security policy) affects dimensions, math, money, RLS, permissions, hardware, audit, or deterministic observable output.
2. **Missing Material Domain Decision:** An essential product or architectural decision is unaddressed in the specifications (insert `[PENDIENTE-DECISIÓN]` under Rule 20).
3. **Unauthorized Irreversible Action:** An action that alters remote production state, pushes to protected branches without PR, forces merges without passing CI, or executes destructive irreversible operations.

*Before escalating to the Owner for a decision, the agent must complete all reversible scaffolding and analysis so the problem is presented with concrete, actionable options.*

---

## 5. Instruction Provenance: No Silent Conflicts

```
NO SILENT INSTRUCTION CONFLICTS.
SEPARATE "RULE SAYS" FROM "AGENT INTERPRETS".
```

If an agent decides to pause, reject a request, or alter execution direction based on a repository instruction or rule, it must report its provenance transparently:
1. **Exact Path:** The file where the instruction is written.
2. **Section / Rule:** The specific rule ID or section heading.
3. **Literal Requirement:** The exact text as written in the source file (`RULE SAYS`).
4. **Applied Interpretation:** The technical inference made by the agent (`AGENT INTERPRETS`).
5. **Why It Blocks:** The concrete material impact justifying the stop.

---

## 6. Maker / Checker Mechanics

The engineering workflow strictly enforces the separation of roles to eliminate "verifier theater":

```
THE MAKER MAY EXECUTE EVERY DETERMINISTIC CHECKER AND REPAIR FAILURES AUTONOMOUSLY.
THE MAKER DOES NOT DEFINE, WEAKEN OR OVERRIDE THE CHECKER'S VERDICT.
PROTECTED CI PROVIDES THE INDEPENDENT INTEGRATION VERDICT.
```

- **The Maker:** Writes code, creates tests, executes local targeted checkers, runs the Gauntlet, inspects failures, and repairs code autonomously.
- **The Checker:** A deterministic, automated test and linting harness (`scripts/check_dod.py`) configured with *fail-closed / rejection by default*.
- **No Self-Approval:** The Maker cannot declare a task complete through subjective natural language ("looks good to me", "verified").
- **No Weakening of Gates:** The Maker is strictly forbidden from editing test fixtures, weakening assertions, adding warning filters, or modifying `scripts/check_dod.py` to turn a failing check green.
- **No Artificial Second Agent:** If the deterministic checker outputs `EXIT CODE 0` and protected CI passes all required contexts, the increment is mechanically proven. There is no artificial requirement to spawn a secondary LLM to duplicate what the deterministic checker has already verified.

---

## 7. Progressive Verification Ladder

Verification is applied progressively to keep feedback loops fast during development, while ensuring 100% mechanical rigor before closure:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ LEVEL 1: Local Unit / Change Cycle                                      │
│ Targeted meaningful tests (pytest engine/tests/test_x.py, ruff check)   │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ LEVEL 2: Module Stabilization Cycle                                     │
│ Affected module suite (pytest engine/ -q, npm run test)                 │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ LEVEL 3: Integration Cycle                                              │
│ Relevant integration, DB, and real browser tests (Playwright, RLS)     │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ LEVEL 4: Shot Closure Cycle (MANDATORY GAUNTLET)                        │
│ Canonical Full Gauntlet: python scripts/check_dod.py all                │
│ All 6 Filters: Guards + Linters + Types + Tests + Build + DB Live       │
└─────────────────────────────────────────────────────────────────────────┘
```

> [!IMPORTANT]
> **Progressive verification optimizes ONLY the intermediate development cycle.**
> It never skips, weakens, or eliminates any test, mutation check, DB/RLS test, Golden check, real-browser E2E, or CI context at the time of shot closure.

---

## 8. Golden Snapshot Policy

```
DEFAULT: GOLDEN = READ-ONLY
```

The golden test fixtures (`engine/tests/golden_example.json`) guarantee byte-for-byte mathematical immutability across releases.
- **Default State:** Golden snapshots are read-only and must be checked with `--check`.
- **Regeneration Requirements:** `make goldgen` or `python -m engine.scripts.regenerate_golden` may only be executed if:
  1. An explicit, authorized material formula change has been approved.
  2. The normative PRD source was updated and approved first.
  3. The active shot explicitly authorizes the formula modification.
  4. The generated diff in the snapshot is inspected and included explicitly in the commit.
- **Prohibited:** Never regenerate a Golden snapshot simply to make a failing test pass.

---

## 9. Reasoning Escalation Matrix

Reasoning effort should match the intrinsic complexity of the engineering problem:

| Task Type | Recommended Effort | Focus |
|---|:---:|---|
| **Routine Implementation** | `LOW` | Boilerplate, standard typing, known patterns, straightforward components. |
| **Multi-File Scaffolding** | `LOW / MEDIUM` | Wiring repositories, serializers, API routing, standard tests. |
| **Complex Debugging** | `MEDIUM` | Tracing state lifecycle, race conditions, browser layout discrepancies. |
| **Rule 0 / RLS / Security / Deterministic Math** | `HIGH` | Algebraic formulas, RLS policy boundaries, permission matrices, pricing. |
| **Major Architecture / Adversarial Review** | `XHIGH` | ADR formulation, constitutional alignment, cross-shot data contracts. |
| **Exceptional Frontier Problems** | `MAX` | Truly novel algorithmic optimization with clear, concrete ROI. |

```
QUALITY COMES FROM ENGINEERING CONTRACTS + EVIDENCE + GATES, NOT FROM MAX REASONING ON EVERY TOKEN.
```

---

## 10. Single Writer and Subagent Protocol

To prevent workspace corruption, race conditions, and divergent states:
- **Single Canonical Writer:** Only the primary root agent possesses write permissions to the canonical working tree and repository files.
- **Read-Only Parallelism:** Subagents may be invoked concurrently exclusively for read-only tasks:
  - Database schema audits.
  - Frontend component analysis.
  - Security and RLS reviews.
  - Documentation and PRD research.
  - Cross-codebase symbol searches.
- **Integration Responsibility:** The root agent receives all subagent findings, reconciles contradictions under Rule 0, and writes the unified solution.

---

## 11. Technology and Provider Neutrality Framework

Dekopen's long-term endurance requires distinguishing binding business requirements from current baseline implementations:

### 11.1. Classification System
Every technology, library, or provider mention in the documentation falls into one of five categories:
- **Tier A — Contractual Requirement (Binding):** Mandatory system invariant (e.g., Python `/engine` purity, PostgreSQL 16+ RLS, `Decimal` precision, tolerance $0.00\text{ mm}$).
- **Tier B — Current Implementation Baseline (Operational):** The presently adopted, working implementation stack (e.g., Django 5 Ninja/DRF, Vite React SPA, Supabase CLI).
- **Tier C — Example (Illustrative):** Concrete examples illustrating an approach without binding future choices (e.g., Three.js/R3F as an example for 3D viewing).
- **Tier D — Historical Reference (Non-Normative):** Past notes or milestones (e.g., legacy migration records).
- **Tier E — Accidental / Harmful Lock-in:** Accidental restrictions freezing a temporary tool as an unchangeable law (must be neutralized documentarily).

### 11.2. Technology Neutrality Invariant
Documentary neutrality refactoring **never** modifies functional code, runtime dependencies, configured providers, or observable behavior.

### 11.3. Active PRD Authority and Conservative Baseline (PRD-12, PRD-13, PRD-14)
- **PRD-12 (3D Viewer):** Concrete renderer (Three.js / R3F) is Tier C (Illustrative Example), as PRD-12 §3.1 explicitly grants surface and engine flexibility (Babylon.js, WebGPU, WebGL).
- **PRD-13 (AI Gateway):** Backend models are dynamic routing configuration (`ai_routes`), as PRD-13 §4 explicitly specifies dynamic router updates without altering business core.
- **PRD-14 (Fabricability Certificate T8):** Classified conservatively as `CURRENT BASELINE UNDER ACTIVE PRD AUTHORITY`. If an active PRD does not contain an explicit delegation clause for replacing model names, the non-normative harness does not declare them neutralized. Provider/model replacement is permitted only insofar as the active PRD-13/PRD-14 contracts preserve dual independence, deterministic arbitration, auditability, and all observable requirements.

---

## 12. Active and Closed Shot Precedence

```
GLOBAL FLEXIBILITY DOES NOT RETROACTIVELY DESTABILIZE AN ACTIVE OR CLOSED SHOT CONTRACT.
```

- **Closed Shots Remain Closed:** Completed decisions in closed shots (SHOT-01 to SHOT-06) are immutable historical contracts.
- **Active Shot Contracts Govern:** If a design decision was formally resolved and frozen in an active `PLAN_SHOT-XX.md` (e.g. `PD-07-27` establishing S07 as a modal within S06 during SHOT-07), that decision remains the contractual law of that shot. Broader global flexibility in future roadmaps does not reopen or destabilize active work.

---

## 13. UX and Visual Production Quality

Token and context efficiency must never diminish user experience or visual rigor:
- Visual verification in a real browser (via Playwright or local serve) is essential for UI changes.
- Ensure proper rendering across:
  - Both Dual Themes (Light Studio `#F8F9FA` and Dark Graphite `#1E1E1E`).
  - Mobile, tablet, and workshop touchscreen viewports.
  - Interactive states: hover, focus, keyboard navigation, loading skeletons, empty states, and descriptive error dialogs.
  - Zero raw hex colors in UI code (strictly CSS semantic tokens).

---

## 14. Concise Reporting Protocol

Communication during execution must be direct, dense, and focused on verifiable deltas:
- **Intermediate Updates:** Report only new information, blockers, or task completions. Avoid repeating the plan or narrating obvious steps.
- **Closure Reports:** Deliver structured reports containing:
  1. `HEAD` commit SHA.
  2. Exact changed files (`git status --short`).
  3. Mechanical verification outputs (`test`, `all`, linters, typecheck).
  4. Golden snapshot status (byte-identical).
  5. Remaining material contradictions or pending decisions (if any).
  6. Clear statement of the next irreversible action.
