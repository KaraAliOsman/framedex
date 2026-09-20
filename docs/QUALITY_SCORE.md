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
| **Agent Harness** | Production-Grade Operating Model | `PROVEN` | PR #17 (merged 5be2b99), unified Maker/Checker protocol, durable quality score. |
| **SHOT-07** | 1D BFD Cutting & Inspector R01–R14 | `PROVEN` | [PR #19](https://github.com/KaraAliOsman/framedex/pull/19); approved head `e29c6e8eb5b5314400b0cec4f82952c30ec52a47`; technical merge `68ce52f62eb6a37373435c6ff1a14905d4fc885f`; 4/4 required CI completed/success: Lint & Typecheck, Test Suite, Frontend Build, Database Gate. |
| **SHOT-06B** | Complex Cases (G8, G9, G11, G12) | `DEFERRED_BY_ROADMAP` | Extended sliding 3-4L and double door scheduled for Phase 1.5. |
| **SHOT-08** | 5-Mode Pricing Engine & Auditing | `PROVEN` | [PR #21](https://github.com/KaraAliOsman/framedex/pull/21); approved head `e19351ee23896678eacb5c19a9bdf17376c74aad`; technical merge `063b6a4d6eb7a6b43105169c1dc30c8c809fe9a4`; 4/4 required CI completed/success: Lint & Typecheck, Test Suite, Frontend Build, Database Gate. |
| **SHOT-09** | Workshop Technical Outputs (DOC-01..07) | `PROVEN` | Implementation [PR #23](https://github.com/KaraAliOsman/framedex/pull/23) (merge `251f4417a85b9e37ffad905d84147d76f21b68f6`); final corrective [PR #29](https://github.com/KaraAliOsman/framedex/pull/29) with tested head `061990f0d3ac749a4ec1b775a5535d7d5cc02f4a` merged at `4662ec6ee15d1ed3cc365a8072cdc3db318f078f`; final closure main `b7ccc6c548d3c0455e745d74890fea0acc2abd5b` ([PR #30](https://github.com/KaraAliOsman/framedex/pull/30)). Required CI 4/4 green; canonical Gauntlet EXIT 0 on `061990f`; engine 244 + canonical xfails, backend 219, frontend suite, pgTAP PASS; real PostgreSQL concurrency/RLS proof; DOC-01…07 + S19; Golden byte check PASS; 22/22 core formula mutations killed (11 sites × ±0.01 mm). Final two-issue hotfix [PR #32](https://github.com/KaraAliOsman/framedex/pull/32) (tested head `3aafccb`, merge `d94d7c241ee0b6def18ca2b42ea8d1f13f12979f`, Gauntlet exit 0): canonicalizes eligibility keys server-side and binds artifact replay to active-org/version/order authority; tag `shot-09` → `d94d7c2`. |
| **SHOT-10** | Project Versioning & Catalog CRUD | `PROVEN` | [PR #34](https://github.com/KaraAliOsman/framedex/pull/34) merged in `main` at `8712d67f66601cd63209128ee29fe2a043d9b755`; full Gauntlet EXIT 0 on `85893c365a7228ef5805afe1e8292d1335ddc8dc`; narrow executable refinement ended at `4e1f7af367438f11a723e20f22fc771177a0ce40`; documentation head `99f18562f0378712d0db668abcd6f47b15e9c5ff`; protected CI 4/4 green. |
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
5. **Mutation Resilience:** 22/22 core formula mutations killed at $\pm 0.01\text{ mm}$ (11 mutation sites in `scripts/check_core_mutations.py`, each executed at `+0.01` and `-0.01`).
