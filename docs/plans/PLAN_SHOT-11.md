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

## Material decisions pending

`PD-11-01 RESOLVED_BY_OWNER`: USD list prices are net; add 19% IVA after conversion
with the 5% FX buffer. OWNER answered on 2026-09-20: "USD netos; añadir IVA 19%".
Total CLP = USD list amount × observed USD/CLP rate × 1.05 × 1.19, rounded once at
the final CLP boundary using the existing commercial HALF_UP authority.

`[PENDIENTE-DECISIÓN] PD-11-02`: monthly credit allowances are specified, but rollover
and pack expiry are not. OWNER must define whether monthly balances expire or accumulate
and whether packs expire, including annual plans with monthly credit delivery.

`[PENDIENTE-DECISIÓN] PD-11-03`: effective date of changes/cancellation and proration are
unspecified. Proposed for decision: changes at paid-period end, no automatic proration
or refunds. No dependent financial behavior may be implemented as an assumption.

These decisions are requested under Constitution Rules 0/20. Independent implementation
continues; this record does not authorize the proposed choices.

## Evidence and closure gates

No material head is proven yet. Record exact SHA, command, result and affected surface
when evidence exists. Execute the canonical Gauntlet on the final material head only.

External gates currently unproven: Flow sandbox credentials and real subscription checkout;
production deployment, Cloudflare boundary and Railway alert delivery; Supabase PITR/RPO
and encrypted Storage backup plus clean-instance restore. No Flow/Railway/production DB
credentials were present in the process environment at initial inspection. GitHub access
and the local Supabase Docker stack are available. This is not evidence of production access.

Closure requires all roadmap gates, protected PR CI, authorized protected merge, verified
main and the conventional `shot-11` tag. Do not mark closed from configuration or mocks.

## Implemented checkpoint and remaining implementation

- Immutable atomic ledger and scoped backend capability; 500-credit, seven-day trial;
  zero-credit Starter and lazy expiry; audited debit contract for later AI consumers.
- Server-frozen payment orders and explicit grant schedules. Signed Flow status lookup,
  monotonic settlement, concurrent callback deduplication, transactional payment/event/lot
  writes and GET-only recovery after an ambiguous one-time pack dispatch. No public API
  accepts amounts, exchange rates, credit grants or provider customer identity.
- Flow native customer/register/subscription/cancel/invoice transport methods follow the
  real API. **Native subscription orchestration is not implemented yet.** Plan selection,
  paid entitlements, monthly allowances for annual plans, changes/cancellation and pack
  storefront remain unfinished pending the commercial policy decisions. Transport and
  pack settlement are not evidence of a working recurring subscription checkout.
- S20 and S24 expose real OWNER/aal2 wallet and billing read state through generated
  OpenAPI clients. S24 does not yet offer checkout or subscription management.
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

## Provider references checked 2026-09-20

- https://developers.flow.cl/api (API 3.0.1, signing and asynchronous confirmation)
- https://docs.railway.com/deployments/healthchecks (deployment readiness, not uptime monitoring)
- https://docs.railway.com/guides/alerts-crashes-failed-deploys (deployment events and resource monitors)
- https://supabase.com/docs/guides/platform/backups (PITR and database backup limitations)
