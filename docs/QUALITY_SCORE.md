# DEKOPEN — OPERATIONAL QUALITY MAP (v1.0)

> **Status:** OPERATIONAL QUALITY MAP — NON-NORMATIVE
> **Authority Precedence:** This map provides agents with a rapid JIT lookup of proven capabilities versus work in progress. It is strictly informative and does **not** override normative specifications in [`docs/CONSTITUTION.md`](./CONSTITUTION.md) or [`docs/PRD/PLAN_SHOTS.md`](./PRD/PLAN_SHOTS.md).

---

## 1. Classification Methodology

To eliminate ambiguity and "verifier theater", every module and shot is classified into one of five rigorous operational states backed by mechanical evidence:

| State | Definition | Required Mechanical Evidence |
|---|---|---|
| `PROVEN` | Production-grade implementation closed, verified by the Gauntlet, and merged into `main`. | Closed SHOT, merged PR with 4 green CI checks, passing tests, RLS, or Golden. |
| `IN_PROGRESS` | Increment currently under active implementation or verification. | Active `PLAN_SHOT-XX.md` with approved design decisions (PDs), branch work. |
| `DEFERRED_BY_ROADMAP` | Capability deliberately scheduled for a future milestone or sub-shot. | Formal deferral record in `PLAN_SHOTS.md` or active plan (not a defect). |
| `BLOCKED` | Progress halted by a material contradiction or missing domain authority. | Explicit `[PENDIENTE-DECISIÓN]` under Rule 0 / Rule 20. |
| `NOT_EVALUATED` | Future milestone not yet reached in the sequential roadmap. | Unstarted shot in Phase 2, 3, or 4. |

---

## 2. Capability Quality Matrix

| Scope / Shot | Capability Domain | Operational State | Contractual Evidence & Artifacts |
|---|---|:---:|---|
| **SHOT-01** | Monorepo, Tooling & CI Base | `PROVEN` | PR #2, GitHub Actions CI green, Ruff + Mypy + Pytest + Vitest foundational pipeline. |
| **SHOT-02** | PostgreSQL Schema, RLS & Tenancy | `PROVEN` | PR #4, DDL migrations, pgTAP suite, strict `org_id` multi-tenant RLS isolation. |
| **SHOT-03** | Pure Engine Core & Geometry G1–G4 | `PROVEN` | PR #8, G1–G4 exact $0.00\text{ mm}$, pure Decimal engine contract, golden baseline. |
| **SHOT-04** | Auth, Django API & Dual Theme Shell | `PROVEN` | PR #10, Magic Link + TOTP E2E tests, OpenAPI TS generation, Studio Light / Dark Graphite. |
| **SHOT-05** | Canvas 2D Interactive Editor | `PROVEN` | PR #12, Playwright paint benchmarks (<300 ms), transactional dimension edits, snapping. |
| **SHOT-06** | Extended Typologies & Hardware Kits | `PROVEN` | PR #14, SLIDING_2L, DOOR, AWNING, G5–G7 in $0.00\text{ mm}$, 20/20 core mutations killed. |
| **v1.3 MASTER** | Normative & Capability Alignment | `PROVEN` | PR #16 (merged aaf739a), Single Constitution, PRD-20 community catalog, 4/4 CI contexts green. |
| **Agent Harness** | Production-Grade Operating Model | `IN_PROGRESS` | Local validation passed (6/6 filters exit 0); protected integration pending. |
| **SHOT-07** | 1D BFD Cutting & Inspector R01–R14 | `IN_PROGRESS` | Branch `shot-07`, 1D BFD optimizer, R01–R14 inspector, S07 modal design. |
| **SHOT-06B** | Complex Cases (G8, G9, G11, G12) | `DEFERRED_BY_ROADMAP` | Extended sliding 3-4L and double door scheduled for Phase 1.5. |
| **SHOT-08** | 5-Mode Pricing Engine & Auditing | `NOT_EVALUATED` | Phase 1 milestone, scheduled after SHOT-07 closure. |
| **SHOT-09** | Workshop Technical Outputs (DOC-01..07) | `NOT_EVALUATED` | Phase 1 milestone, PDF/Excel generation and BOM hashing. |
| **SHOT-10** | Project Versioning & Catalog CRUD | `NOT_EVALUATED` | Phase 1 milestone, state machine and revision freezes. |
| **SHOT-11** | Flow.cl Billing & Ledger Integration | `NOT_EVALUATED` | Phase 1 commercial checkpoint, CLP checkout and disaster recovery drill. |
| **SHOT-12** | Starter Pilot Sign-off (G-Pro1) | `NOT_EVALUATED` | Phase 1 closure checkpoint, physical calibration sign-off. |
| **SHOT-13..24** | Advanced Capabilities (AI, 3D, Global) | `NOT_EVALUATED` | Phases 2, 3, and 4 roadmap milestones. |
| **G10 Monorail**| Monorail Typology Resolution | `DEFERRED_BY_ROADMAP` | Explicitly scheduled for SHOT-24 (Phase 4). |

---

## 3. Operational Guarantees Ledger

Every capability marked `PROVEN` satisfies the invariant guarantees of Dekopen:
1. **Mathematical Accuracy:** $0.00\text{ mm}$ tolerance across all core cases.
2. **Deterministic Engine:** Calculations execute purely in `/engine` with `Decimal` precision.
3. **Multi-Tenant Security:** Every business table is shielded by RLS with `current_user_org_ids()`.
4. **Immutable Golden Byte Match:** Golden example fixture checked via `--check` on every CI run.
5. **Mutation Resilience:** 20/20 core formula mutations killed at $\pm 0.01\text{ mm}$.
