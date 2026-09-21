# SHOT-11 — billing, wallet and production recovery

Status: IN PROGRESS. Base: `564195e1601a28ca33c4a2246a7fee5e7a7aa4da`.
Branch: `codex/shot-11`. SHOT-12 and SHOT-18 are not opened.

## Authority and scope

Constitution Rules 0/3/4/13/19/20, PLAN_SHOTS SHOT-11 and GNG-03/04/09/10,
PRD-03 §§2–4, PRD-19 §§1–3, PRD-02 and S20/S24 govern this work.
Deliver Flow native subscriptions and payments, an atomic immutable wallet, seven-day
500-credit trial, OWNER surfaces, production health, alerts, encrypted backups and a
clean restore drill. Preserve the modular monolith and all manual product functions.

## Decisions

- Flow confirmation uses a form POST token followed by a signed server-to-server status
  lookup. Callback fields are never payment authority. The user explicitly authorized
  correcting S24's inaccurate HMAC-webhook description; merchant API requests use HMAC.
- Reuse PD-08-02's explicit human FX source/date/rate snapshot and 5% buffer. A customer
  cannot choose their own billing exchange rate. No new FX provider or silent fallback.
- Billing tables must not be writable by authenticated clients. OWNER reads require
  active membership and aal2. Backend financial mutations need a separate restricted
  capability and transaction-local RLS; provider events remain server-only.
- Existing credit balances cannot be silently rewritten as historical trial grants.
  Migration must preserve evidence and reject an unaccounted financial state.

## Frozen commercial decisions

`PD-11-01 RESOLVED_BY_OWNER`: USD list prices are net; add 19% IVA after conversion
with the 5% FX buffer. OWNER answered on 2026-09-20: "USD netos; añadir IVA 19%".
Total CLP = USD list amount × observed USD/CLP rate × 1.05 × 1.19, rounded once at
the final CLP boundary using the existing commercial HALF_UP authority.

`PD-11-02 RESOLVED_BY_OWNER` / `PD-11-03 RESOLVED_BY_OWNER`, 2026-09-21.
The following rules are frozen by the OWNER's explicit decision:

- Monthly subscription credits expire at the end of each service cycle; no rollover.
  Purchased packs/top-ups never expire and survive downgrade or cancellation. Consume
  expiring monthly credits before purchased credits. Persist origin, grant/debit,
  expiration and attributable balance separately; the UI may aggregate balances.
  Spending retained packs still requires the active plan's relevant AI entitlement.
- Same-billing-cycle upgrades take effect only after Flow confirms the change. Call
  `subscription/changePlanPreview` before confirmation and `subscription/changePlan`
  to execute; persist Flow's monetary evidence without an independent money formula.
  Additional monthly credits are `floor((new_allowance-old_allowance) * remaining_period
  / total_period)` using authoritative subscription period boundaries. Grant only a
  positive delta, once, as a separate ledger grant. Next renewal grants the new full allowance.
- Downgrades take effect at the paid-period end, preserving paid benefits and monthly
  credits until then; no automatic prorated refund. At the boundary, expire that cycle's
  monthly credits, activate the new plan and grant only its allowance. Preserve packs.
- Monthly/annual frequency changes take effect at the next renewal; no local monetary
  proration between frequencies. Annual subscriptions deliver their allowance monthly.
- Voluntary cancellation defaults to Flow `at_period_end=1`. Preserve paid rights until
  the boundary; then end the subscription and expire monthly credits, preserving packs.
  No automatic refund. Immediate cancellation is exceptional: incorrect/duplicate charge,
  fraud, legal obligation or explicitly authorized administrative intervention.
- Refunds are exceptional (duplicate/incorrect charge, paid service that could not activate,
  legal obligation or authorized administrative decision) and use Flow's real refund flow.
  Never delete payments or ledger history. Record refunds and entitlement reversals as
  auditable idempotent compensation. Automatic credit reversal can remove only unused
  credit from the affected grant; consumed/ambiguous benefit requires administrative
  resolution, never negative credits or invented credit debt.
- Successful paid activation during trial ends the trial and expires its remaining credits
  before granting the paid period's allowance. Never stack unused trial credits on it.

Regression obligations: idempotency, concurrency, renewal, upgrade, downgrade,
cancellation, expiration, trial conversion and refund compensation.

## Infrastructure and integration decisions, 2026-09-21

`PD-11-04 RESOLVED_BY_OWNER`: "Autorizar PostgreSQL 17 con validación".
Production Supabase and the operational backup/restore image target PostgreSQL 17.
The independent PostgreSQL 16 compatibility gate remains intact. The existing local
Supabase configuration already uses major 17; its complete integration/RLS/Auth suite
and the clean PostgreSQL 17 encrypted restore must pass before integration.

`PD-11-05 RESOLVED_BY_OWNER`: the OWNER will pay for the infrastructure later and
explicitly requested "hasta mientras terminar y mergear asi". Integrate the tested
implementation through protected PR #38 with production activation deferred. This
supersedes earlier instructions in this plan to keep the PR draft until external gates
pass. It does not declare GNG-09/10 passed, close SHOT-11, create a closure tag, or open
SHOT-12. Preserve the external gates and known Flow reconciliation limitation below.

The OWNER selected `KaraAliOsman's Org` for a separate DEKOPEN Supabase project.
The connector quoted USD 0/month, completed its cost-confirmation flow, and created
`DEKOPEN` (`lexvdshnblbtxdkadnhm`) in `sa-east-1`, on Free. Project inspection reports
bundle `17.6.1.166`, PostgreSQL 17, `ACTIVE_HEALTHY`; a read-only SQL query confirms
`server_version_num=170006`. No existing project was repurposed. No paid subscription,
PITR add-on, live merchant credential, production schema rollout or recovered dataset
is implied by this empty project.

Railway authentication now works, but creating a separate private DEKOPEN project was
rejected: "Your trial has expired. Please select a plan to continue using Railway."
The existing `accurate-healing` project hosts unrelated OpenClaw code and was left intact.
The OWNER deferred payment: no plan upgrades were purchased. OAuth connectivity is
therefore resolved; paid capacity/activation and merchant credentials remain outstanding.

The deployment target is Supabase Pro with Small compute and seven-day PITR, plus
Railway Pro for resource monitors. The published one-project Supabase example is about
USD 130/month; Railway Pro has USD 20/month minimum usage. Additional usage and temporary
restore capacity can add cost. Recheck prices when the OWNER activates payment; the
USD 0 Free-project quote is not a production/PITR quote.

[Supabase PITR pricing](https://supabase.com/docs/guides/platform/manage-your-usage/point-in-time-recovery),
[Railway pricing](https://railway.com/pricing).

Checkout refinement: delayed card registration now freezes subscription start on the
merchant-local date of native intent preparation, rather than reusing the selection
date from days earlier. The organization lock serializes preparation; subsequent retries
reuse the immutable intent, including GET recovery after a lost provider response.
Four network-seam regressions cover delayed registration, UTC/Chile dates and lost replies.
The attempted native local run was interrupted because its PostgreSQL endpoint was no
longer responding; passing evidence must come from the exact-SHA runner below.

## Final integration evidence before paid activation

At exact implementation SHA `3d2b3ef7c561fd371fa35bdd2859c9b47df75a4e`, protected CI
passed all required contexts in [run 35652483190](https://github.com/KaraAliOsman/framedex/actions/runs/35652483190):
Lint & Typecheck, Test Suite, Frontend Build and Database Gate. The separate exact-head
workflow [run 35652494282](https://github.com/KaraAliOsman/framedex/actions/runs/35652494282)
also passed its canonical `python scripts/check_dod.py all`, fresh production-container
probe and PostgreSQL 17 encrypted clean-instance restore. The current restore job
verifies application row hashes, constraints, RLS/tenant isolation, ledger/lot balances
and refusal to overwrite a populated target. This is the final tested integration head;
documentation after it does not change executable behavior.

PR #38 is ready and mergeable. The OWNER authorized protected integration while deferring
paid activation (PD-11-05). Merge is therefore an integration checkpoint, not a claim that
Flow sandbox, Cloudflare/Railway production alerts, Supabase Pro/PITR, private Storage
delivery or managed Auth/Storage recovery have passed. Keep SHOT-11 `IN_PROGRESS` and do
not create the `shot-11` closure tag until those external gates are evidenced.

## Evidence and closure gates

Previous implementation checkpoint: `fe3f57dd0437c833ede3b8aaad440793449465b6`.
This is not a shot-closure declaration; checkout integration evidence follows below.
Draft [PR #38](https://github.com/KaraAliOsman/framedex/pull/38) targets protected main.
The canonical Gauntlet passed at `4eb2f2003f5ecedc81b6ecb921c0075282d5f667`;
the narrow Linux restore-probe refinement is verified separately below under Rule 19.

External gates currently unproven: Flow sandbox credentials and real subscription checkout;
production deployment, Cloudflare boundary and Railway alert delivery; Supabase PITR/RPO
and encrypted Storage backup plus clean-instance restore. No Flow/Railway/production DB
credentials were present in the process environment at initial inspection. GitHub access
is available. Docker Desktop is currently unavailable; the initial Supabase proofs below
predate that failure. This is not evidence of production access.

Closure requires all roadmap gates, protected PR CI, authorized protected merge, verified
main and the conventional `shot-11` tag. Do not mark closed from configuration or mocks.

## Implemented checkpoint and remaining implementation

- Immutable atomic ledger and scoped backend capability; 500-credit, seven-day trial;
  zero-credit Starter and lazy expiry; audited debit contract for later AI consumers.
- Server-frozen payment orders and explicit grant schedules. Signed Flow status lookup,
  monotonic settlement, concurrent callback deduplication, transactional payment/event/lot
  writes and GET-only recovery after an ambiguous one-time pack dispatch. No public API
  accepts amounts, exchange rates, credit grants or provider customer identity.
- Flow native customer/register/subscription/cancel/invoice transport follows the real API.
  Native subscription creation now has a persisted single-dispatch intent, immutable
  approved start terms, remote plan/customer validation and GET-only reconciliation
  after a timeout or local failure. Customer creation also has a persisted single-dispatch
  claim and signed GET recovery. Registration callbacks bind the token hash and verified
  provider customer; no card data or raw registration token is stored. Native invoices are bound to their subscription,
  customer and frozen quote before atomic settlement. These server primitives require
  preprovisioned merchant plans and explicit approved terms; no public client
  chooses them. The checkout checkpoint adds plan/pack selection, paid entitlements,
  annual-plan monthly allowances and change/cancellation UI. Real Flow sandbox evidence
  and administrative adjustment-invoice settlement remain outstanding.
- S20 and S24 expose real OWNER/aal2 wallet and billing read state through generated
  OpenAPI clients. S24 now provides checkout and subscription-management operations.
- Non-root Gunicorn image, PostgreSQL/Redis readiness, shared rate limit, safe structured
  request logs, Railway deployment config and executable daily encrypted backup cron.
- AES-256-GCM snapshot dump and clean-target restore verify all row hashes, constraints,
  RLS and balances. The synthetic PostgreSQL 16 drill passes; actual managed Supabase
  Auth/Storage recovery and production RPO remain external gates.

Upgrade limitation: the wallet migration rejects a pre-existing ledger until its lots
are explicitly reconciled. It preserves nonzero legacy balances without ledger as a
`MIGRATION_OPENING`, and rejects trial balances over 500. Do not deploy blindly over
existing financial history; no old grant provenance is fabricated.

Dependency rationale: Gunicorn 26.2.0 supplies the existing Python WSGI production
process; redis 8.1.0 implements the PRD-19 shared counter; structlog 26.1.0 implements
PRD-19 structured logging. They do not introduce a provider or separate service architecture.
Licenses: MIT (Gunicorn/redis), MIT or Apache-2.0 (structlog); all exact versions pinned.
Published wheel sizes approximately 228/560/73 kB; pip-audit of these three pinned
dependencies found no known vulnerabilities on 2026-09-20. Billing lazy frontend chunks
are approximately 1.01/1.06 kB gzip; no additional frontend dependency.

Development checks before a committed checkpoint: wallet/payment PostgreSQL 20 passed;
Flow/production/OpenAPI/money 29 passed; billing UI 5 passed; real Auth+TOTP browser
TRIAL/Starter/manual-calculation 2 passed; Ruff, frontend lint/build and canonical lint
surface passed. These working-tree runs are diagnostic, not SHA-bound closure evidence.
The canonical full Gauntlet remains due on the final material shot implementation head.

## SHA-bound evidence, 2026-09-20 (America/Santiago)

| SHA | Command / surface | Result |
|---|---|---|
| `a0037014a2c6baf82c7c46a03b02c217cf2a0ff3` | `python -m pytest backend/tests engine/tests/test_billing.py -m "not rls_integration" -q` | 197 passed; 205 integration cases intentionally selected by the separate live DB gate. |
| `a0037014a2c6baf82c7c46a03b02c217cf2a0ff3` | `npm --prefix frontend run test -- src/features/billing` | 5 passed; zero/manual state, OWNER boundary, pending payment and missing fiscal receipt. |
| `a0037014a2c6baf82c7c46a03b02c217cf2a0ff3` | `local_gates.run_auth_e2e(local_gates.running_environment(), 'tests/e2e/auth.spec.ts', '--grep', 'SHOT-11')` | 2 passed; real Supabase Magic Link, TOTP, aal1 rejection, trial/Starter reads and actual manual engine calculation/project creation. |
| `a0037014a2c6baf82c7c46a03b02c217cf2a0ff3` | `python scripts/check_production_boundary.py` | Fresh image; UID 10001; readiness 200; Redis failure readiness 503 and liveness 200; billing 401; CSP/HSTS; concurrent shared Redis quota: 100 requests accepted for validation, next 5 return 429. No Railway deployment proof. |
| `737800124179941cf8d4077586e81a28764f0917` | `python scripts/check_dod.py typecheck`; `python -m pytest engine/tests/test_billing.py -q`; `python scripts/check_dod.py lint` | All exit 0; strict annotations corrected in three money tests; 7 money cases pass. Generated API reproducible. |
| `525f2f2ec252f98ff61cc856a299e410690540fb` | `python scripts/check_dod.py database` | Exit 0: 355 pgTAP, 205 real PostgreSQL integration cases, PostgreSQL 16 migration and populated-upgrade checks. RLS DDL was made explicit to satisfy the existing checker without weakening it. |
| `525f2f2ec252f98ff61cc856a299e410690540fb` | `python scripts/check_restore_drill.py` | Fresh backup image; 48 tables restored in 0.912 s on synthetic PostgreSQL 16; all row hashes, relationships, RLS and ledger/lot balances consistent; populated target refused. |

Checkpoint `525f2f2` drill ciphertext SHA-256:
`551c94ab29fb1903877a0eede4476b41b87ac6e96bfc825a3c125038a3f398f0`.
The script builds its own image and refuses a dirty tree, so stale images cannot stand
in for the recorded source. The ephemeral synthetic backup is removed after the drill.
Earlier proof remains valid for unchanged application surfaces; the two refinements
only add strict test annotations and replace dynamic RLS enablement with equivalent
explicit statements. No Golden snapshot or existing engine formula was changed.

Protected CI passed all four required contexts on `370da59` and again on
`6653eab3559bcb707edcf2ee57781fd8b0052df4` ([run](https://github.com/KaraAliOsman/framedex/actions/runs/35549762047)).
This proves the corresponding checkpoints only, not subsequent code or shot closure.
No canonical `check_dod.py all` run, merge SHA or `shot-11` tag exists for this shot.

Native subscription checkpoint `f3015a4eaa05a2f5e07c1d828c1b6863a89c231c`:
52 targeted native/payment/wallet/production/Flow tests passed against real PostgreSQL
with HTTP simulated only at the provider boundary. Canonical lint passed. A fresh
encrypted restore recovered 49 tables in 0.994 seconds, with ciphertext SHA-256
`5249fadf12dfd7872fc82f06d8bcde5eeaa50948899fac9357a4f0320c8d48d5`.
The Windows Docker probe needed explicit UTF-8 output decoding (`6653eab`); its fresh
production image then passed readiness/dependency failure/non-root/security/quota checks.
Customer-registration checkpoint `164c05a714f5daeb5d6c815d90a4a9fb698b4d44`
(verified across 2026-09-20/21, America/Santiago):

| Command / surface | Result |
|---|---|
| `python -m pytest backend/tests engine/tests/test_billing.py -q` | 423 passed against real local Supabase PostgreSQL, no integration marker exclusions. Includes seven customer registration/recovery/callback/RLS cases. |
| `python scripts/check_dod.py lint` | Exit 0; guards, lint, generated OpenAPI and frontend clients reproducible. |
| `python scripts/check_production_boundary.py` | Fresh revision-labelled non-root image; readiness 200; Redis failure readiness 503/liveness 200; billing 401; security headers; shared quota 100 then 429. |
| `python scripts/check_restore_drill.py` | 50 tables restored in 1.082 seconds on isolated synthetic PostgreSQL 16; row hashes, constraints, RLS and ledger/lot integrity pass; populated target refused. |
| [Protected CI run 35550155086](https://github.com/KaraAliOsman/framedex/actions/runs/35550155086) | All four required contexts pass: Lint & Typecheck, Test Suite, Frontend Build, Database Gate. CodeRabbit skipped review because the PR is draft. |

This checkpoint's encrypted-backup SHA-256 is
`6b7d406dc5299388d61f3ed56537cf77947a2bf3c88e787d3ba11b19b6ab346d`.
These are local operational proofs, not a Railway deployment or production RPO claim.
A subsequent evidence-only commit does not change the tested implementation.

External access checked 2026-09-21: the available in-app browser shows login screens
for Railway, Supabase and Flow sandbox; no authenticated session is available there.
Supabase and Railway connectors were discovered and offered for connection; neither
was connected at this checkpoint. A Flow sandbox account and merchant configuration
are still required for the real checkout gate. No production configuration, access,
subscription or payment was changed during this access check.

### Owner decisions resolved

PD-11-01/02/03 are resolved. No further approval is required to implement the policies
above. External account access and honest sandbox/production evidence remain necessary.

## Provider references checked 2026-09-20

- https://developers.flow.cl/api (API 3.0.1, signing and asynchronous confirmation)
- https://docs.railway.com/deployments/healthchecks (deployment readiness, not uptime monitoring)
- https://docs.railway.com/guides/alerts-crashes-failed-deploys (deployment events and resource monitors)
- https://supabase.com/docs/guides/platform/backups (PITR and database backup limitations)

## OWNER policy implementation checkpoint, 2026-09-21

PD-11-02/03 are implemented in the lifecycle reducer, per-lot debit/expiration
attribution and native change/refund primitives. The wallet now exposes retained pack
and expiring credit origins. Evidence below is working-tree diagnostic evidence,
not the final material SHA or shot closure:

- All migrations applied to isolated native PostgreSQL 16.15 using the repository's
  PostgreSQL-16 compatibility bootstrap. 52 billing integration tests pass with real
  locks, RLS, constraints and rollback; only Flow HTTP is simulated.
- Twelve pure money/credit tests, 22 Flow/OpenAPI checks and five billing UI tests pass.
- Canonical lint surface passes, including generated API reproducibility.
- Docker Desktop remains unavailable because of its ingest socket startup error. Native
  PostgreSQL is a development test fallback, not a substitute for Supabase Auth E2E,
  production Docker probes or the final canonical Gauntlet.

Protected CI for `fe3f57dd0437c833ede3b8aaad440793449465b6` passed all four required
contexts in [run 35627827812](https://github.com/KaraAliOsman/framedex/actions/runs/35627827812).
CodeRabbit skipped its review because the PR is draft.

## Checkout integration checkpoint, 2026-09-21

- Audited, immutable per-organization offers use the PRD-03 engine catalogue and frozen
  FX/IVA conversion. Browser requests contain only offer and operation IDs. OWNER/aal2
  and tenant isolation are enforced before dispatch.
- Native customer/card registration and recurring checkout resume persisted operations.
  Signed invoice/payment lookup binds the customer, subscription, exact amount and
  provider period before atomically settling a paid period. A renewal replaces expired
  monthly credit; duplicate callbacks do not duplicate allowances. Pack checkout grants
  non-expiring purchased credit once, including after returning from Flow or retrying.
- S24 displays Flow's saved preview for a second human confirmation, restores pending
  operations after reload, and shows deferred changes. An undispatched preview can be
  abandoned. Overlapping scheduled changes are rejected instead of silently superseded.
- An unmatched adjustment invoice is retained immutably and flagged for administrative
  reconciliation without blocking valid renewals or granting another allowance. Automatic
  adjustment settlement/resolution remains unfinished pending real merchant evidence.
- Operator commands provision offers and prepare/dispatch exceptional refunds. The
  Railway reconciliation cron is configured for signed GET recovery every 15 minutes.
  No deployed cron or alert delivery is claimed from this configuration.
- Trial credit expiration and Starter transition use the same reconciliation instant;
  purchased lots remain intact and cannot enable AI on Starter.

Local diagnostic checks: 59 financial integration cases on PostgreSQL 16.15 (including
real locks/RLS/rollback), nine billing UI cases, 205 non-integration backend/engine cases,
frontend build, canonical lint and typecheck pass. SHA-bound confirmation is recorded
after committing this delta. The native database uses a local `auth.uid()` compatibility
function; it does not provide Supabase Auth. An exploratory full-backend run on this
incomplete environment had 351 passes, 31 failures and 63 setup errors (missing Auth
fixtures/schema privileges); it is not passing full-suite evidence.

Remaining closure work: real Flow sandbox checkout/change/refund response verification,
adjustment reconciliation, current Supabase/Auth E2E and canonical Gauntlet, deployed
production boundary and Railway alerts, encrypted Storage/PITR and clean managed restore.
Keep PR #38 draft and SHOT-11 open until the actual gates pass; no merge or tag yet.

### SHA-bound checkout evidence

Implementation SHA: `910934766b1ebee2b7de25f7716bc3490e44980f`.

| Surface | Result |
|---|---|
| Seven SHOT-11 financial integration modules on native PostgreSQL 16.15 | 59 passed; real locks, RLS, constraints and transactions. |
| Billing frontend components | 9 passed. |
| [Protected CI run 35631264401](https://github.com/KaraAliOsman/framedex/actions/runs/35631264401) | All four required contexts pass. Includes 437 backend cases, 260 engine passes with 5 existing expected failures, 226 frontend tests, 11 browser tests, and the separate DB gate with 244 integration cases plus pgTAP and populated-upgrade validation. CodeRabbit skipped draft review. |
| `python scripts/check_dod.py all` | Attempted once on this SHA. Lint, typechecks and source contracts passed; the live gate failed at `docker info` because the Docker Desktop Linux engine pipe is unavailable. This is not a successful Gauntlet. |
| Current encrypted backup/restore implementation on two isolated native PostgreSQL 16.15 instances | All 57 tables restored in 1.565 seconds. Content hashes, constraints, ledger/lot balances and RLS pass; a populated target is refused. Synthetic local DB proof only, not Storage delivery, managed Auth recovery or production RPO. |

The synthetic encrypted artifact SHA-256 was
`0f07d255ebb9a070d690f4c990a680da430a5039874e7d7b65fc1c6496d339c4`.
The native probe used all repository migrations and seed; its isolated source and restore
instances were stopped after verification. An earlier probe remains stalled because of
inherited Windows process handles; automatic approval review rejected stopping that
probe and cleaning its directories (`blocked by policy`). The successful retry used
independent output handles and separate instances, leaving the rejected targets intact.

The current environment has no configured Flow API credentials, Railway token,
Supabase access token or production database connection. Access was requested through
the task UI without asking for secrets in chat. Commercial OWNER decisions remain resolved.
This evidence-only update does not change the tested implementation or close the shot.

## Canonical runner proof and Linux recovery refinement

The OWNER explicitly authorized merging once SHOT-11 is finished. Actual external
gates still govern completion; no additional merge permission needs to be requested.

At SHA `4eb2f2003f5ecedc81b6ecb921c0075282d5f667`,
[runner 35648999286](https://github.com/KaraAliOsman/framedex/actions/runs/35648999286)
ran `python scripts/check_dod.py all` successfully (exit 0). This is the full canonical
command on the exact PR head, not an aggregation of separate check names. The subsequent
production-container probe also passed: UID 10001, readiness 200, Redis failure readiness
503 with liveness 200, unauthenticated billing 401, security headers and shared quota
100 requests then 429. All four protected CI contexts passed in
[run 35648988631](https://github.com/KaraAliOsman/framedex/actions/runs/35648988631).

That first closure workflow ended in failure only at the restore probe: Linux preserved
the private host temporary directory's ownership, so image UID 10001 could not write
the encrypted artifact. The fix in `4deafdc8fa6e0371d395f69bf78e7b4600209fc3` makes the
disposable probe run as the owning non-root host UID/GID; it does not open directory
permissions, change the production image, or bypass any restore assertion.

[Focused recovery run 35650078507](https://github.com/KaraAliOsman/framedex/actions/runs/35650078507)
passed on `4deafdc8fa6e0371d395f69bf78e7b4600209fc3`: all 57 tables restored in 0.524
seconds; content hashes, constraints, ledger/lot balances and tenant RLS match; a populated
target is refused. Ciphertext SHA-256:
`4f0eea793a29067fd4474be3938b7210672eae1f6a2ca2f51afdf92bae76edfb`.
The focused label intentionally reuses the prior unchanged Gauntlet/production proof
under Rule 19; its successful job name does not claim a second Gauntlet execution.
All four protected contexts also pass for `4deafdc8fa6e0371d395f69bf78e7b4600209fc3`
in [CI run 35650062928](https://github.com/KaraAliOsman/framedex/actions/runs/35650062928).

Remaining gates: authenticated Flow sandbox checkout, changes and refunds (including
actual adjustment invoice and period-boundary binding); deployed Railway/Cloudflare
boundary and delivered alerts; real Supabase private Storage, PITR/RPO and clean managed
Auth/Storage recovery. Fresh browser checks still show sign-in screens for all three
services. The synthetic runner proof does not establish those external facts.
