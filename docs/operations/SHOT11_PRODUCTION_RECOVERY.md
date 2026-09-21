# SHOT-11 production and recovery runbook

Status: deployable configuration and local proofs; external production gates remain unproven.
The shot plan records the resolved OWNER commercial decisions and current evidence.

## Merchant offers, checkout and reconciliation

Set server-only `FLOW_API_KEY`, `FLOW_SECRET_KEY`, the exact approved `FLOW_API_URL`,
`FLOW_MERCHANT_TIMEZONE` matching the merchant account, `BILLING_CALLBACK_ORIGIN` and
`BILLING_FRONTEND_ORIGIN` (public HTTPS origins without paths). Keep sandbox and production
credentials separate. No public endpoint accepts FX, amounts, grants or provider plan IDs.

Create the native recurring plan in the merchant account, then run the trusted operator
command `python backend/manage.py provision_billing_offer --help`. Supply the organization,
approved product/cycle, existing Flow plan ID, observed FX rate/source/date/snapshot UUID
and audit reason. The command verifies the remote amount/currency/interval against the
engine's net USD catalogue, 5% FX buffer and 19% IVA, records an immutable audited offer,
and prints its callback URL. Configure that exact URL as the merchant plan's `urlCallback`
before exposing the offer. Packs use `PACK_1000`, `PACK_3000` or `PACK_7500` without
`--cycle` or `--flow-plan`. Provisioning requires a trusted database session; the runtime
financial role cannot alter an offer's price. Retire an offer by setting `active=false`
through an audited operator transaction; never rewrite frozen historical terms.

An OWNER with aal2 selects an offer in S24. Flow handles payment/card registration.
Registration alone never activates paid rights. The OWNER can resume a persisted checkout
after returning from Flow. Each provider mutation has a committed dispatch claim; refreshes,
callbacks and reconciliation must reuse that operation instead of posting a second charge.
Plan changes display the saved Flow preview and need the separate confirmation action.
Prepared previews may be abandoned; dispatched operations can only be reconciled.
Scheduled changes remain visible after reload and prevent overlapping changes.

Configure a separate Railway cron service with `railway.billing.toml` and the same server
secrets. It runs `reconcile_billing` every 15 minutes using signed GETs, even if a callback
was lost. `--org UUID` restricts an operator run. Expiry is also checked on each wallet
read/debit, so a late cron cannot permit spending expired credits. Configure failed cron
alerts; the TOML file itself is not evidence of an active schedule or alert delivery.

An invoice whose amount cannot be matched to the frozen recurring offer is retained in
`billing_invoice_observations`; it does not create an additional allowance or block other
valid renewals. The UI and cron flag administrative reconciliation. Do not equate a Flow
adjustment invoice with a full renewal or invent a second monetary proration formula.
Automatic adjustment-invoice settlement and resolution of these observations remain
unfinished; validate the real merchant responses before completing this surface.

For an authorized exceptional refund, run `prepare_billing_refund --help` with the paid
order, explicit CLP amount, permitted reason, administrative case reference and affected
grant IDs. `--end-entitlement` requests the audited period reversal subject to unused-credit
checks. Inspect the returned operation and its frozen authority before the separate
`dispatch_billing_refund --help` action. That command sends one refund to Flow; the signed
refund callback establishes completion. A lost dispatch response or consumed benefit
requires administrative reconciliation. Never delete a payment, grant or ledger entry,
and never retry an ambiguous refund POST with a new operation key.

## Application process

Railway builds the root `Dockerfile`. It runs Gunicorn as UID 10001, two gthread workers,
four threads each, with graceful shutdown. The image includes the native libraries and
fonts required by the existing WeasyPrint document implementation. Vite builds the SPA
for the existing frontend hosting boundary; never expose `vite` or Django `runserver`
as a production process. Apply reviewed Supabase migrations separately; web startup
does not mutate the production schema.

Set Railway secrets: `ENVIRONMENT=production`, a random `SECRET_KEY` of at least 50
characters, `DATABASE_URL` (PostgreSQL session connection; SSL and `connect_timeout=5`),
`SUPABASE_URL`, `SUPABASE_ANON_KEY`, existing server Storage credential, `REDIS_URL`,
explicit HTTPS `CORS_ALLOWED_ORIGINS`, and `ALLOWED_HOSTS` including the API hostname
and `healthcheck.railway.app`. Browser variables contain only the public Supabase key
and URL. Never put any server secret in a `VITE_*` variable. Use Railway's release SHA
in logs. The application must be reached through the trusted Railway/Cloudflare proxy,
which owns forwarded-protocol headers. Configure Cloudflare DNS/WAF and strict TLS
for the actual production domain; code does not prove this external configuration.

`GET /health/live/` proves the process responds. `GET /health/ready/` checks PostgreSQL,
the billing boundary migration, and Redis, returning 503 on failure without disclosing
connection details. `railway.toml` uses readiness for deployment promotion. These checks
do not contact Flow and do not declare a paid subscription active. The shared Redis
counter enforces the standard authenticated API quota; the SHOT-13 AI quota is not opened.
The API emits CSP, HSTS and no-store headers. Request logs exclude tokens, query strings
and bodies; verified organization context is attached after tenancy resolution.

## Alerts: capabilities and required external evidence

Railway deployment healthchecks run at deployment time, not continuously. Configure
project webhooks for failed builds/deployments and crashed/restarted services. Configure
resource monitors in the Observability Dashboard for CPU, RAM, disk and egress using
thresholds appropriate to measured capacity. Railway resource monitors require Pro;
they can notify by email/in-app and through configured project webhooks.

Record project/environment/service, notification destination (without its secret URL),
enabled events, thresholds, timestamp, and one actual delivered failure/monitor alert.
Do not use a browser-generated test webhook as proof of server event delivery. A real
deployment/crash event is required. Never claim continuous HTTP uptime monitoring from
these mechanisms. The PRD-19 monthly uptime threshold needs an actual HTTP monitor or
equivalent measured availability evidence before a continuous uptime claim is made.
No new external observability provider is selected by this patch.

Sources checked 2026-09-20:
[Railway healthchecks](https://docs.railway.com/deployments/healthchecks),
[Railway alert mechanisms](https://docs.railway.com/guides/alerts-crashes-failed-deploys).

## Encrypted logical backup

Build `docker build -f scripts/Dockerfile.backup -t dekopen-shot11-backup .`.
This separate operational image supplies PostgreSQL 16 tools and the backup runtime.
The database server major must match the image; a PostgreSQL 17 development stack is
not evidence that a PostgreSQL 16 dump client can back it up.

Provision `BACKUP_DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` and
`BACKUP_ENCRYPTION_KEY` through server secrets. The encryption key is 32 random bytes
encoded as exactly 64 hex characters; preserve it independently of the backed-up DB.
Never record a live key, DSN, plaintext dump or account credential in Git or an evidence log.

Create the backup service using `railway.backup.toml` as its config path. It runs at
03:00 UTC daily using `python scripts/backup_database.py scheduled`, which creates a
unique private temporary filename, uploads and removes the local ciphertext. Configuration
is executable but does not prove that the service or schedule exists in Railway.
`backup_database.py` exports
a repeatable-read snapshot, captures row counts/hashes and role authorization metadata,
and creates a compressed custom-format dump from that same snapshot. It packages the
dump and manifest, encrypts with AES-256-GCM and uploads to the private `dekopen-backups`
bucket without overwriting an earlier object. Validate Storage object-size limits against
the real database size. Temporary plaintext files are confined to a private directory
and removed on exit; use an encrypted ephemeral filesystem for the operational container.

Any failed backup/upload must generate an operational alert. Retain the actual successful
cron execution, object timestamp and ciphertext SHA-256 as evidence. The bucket migration
creates no client access policy. Configure retention/key custody in the production account.

## PITR and RPO

Enable Supabase PITR and verify its recovery window, operational status and latest
recoverable timestamp in the actual project. PRD-19's RPO is at most one hour; the nightly
dump alone cannot satisfy it. Schedule additional encrypted snapshots within the required
window if needed for the contracted continuous-dump path, but continue to verify PITR.
Measure the latest recoverable point during a real incident/drill, not merely the cron
schedule. Record the observation without credentials. No production RPO is proven locally.

Supabase database backups do not include Storage object bytes. Preserve documents,
blueprints and other object data through an independently verified Storage recovery path;
restoring metadata alone does not restore files. The logical dump and local drill prove
the database portion only. Managed Supabase roles/extensions/Auth services may require
platform provisioning in a fresh target before an actual Supabase recovery.
[Supabase backup limitations and PITR](https://supabase.com/docs/guides/platform/backups).

## Clean restore drill

Retrieve the encrypted backup from private Storage using the server/operator credential
into protected temporary storage. Verify its expected ciphertext hash. Provision a clean
PostgreSQL instance with the same major and required extension binaries. Set
`RESTORE_DATABASE_URL` to that separate instance and supply the independently held key.
Run `scripts/restore_drill.sh /path/to/backup.aes` (or `python scripts/backup_database.py
restore /path/to/backup.aes`). No production/source database is overwritten.

Restoration authenticates GCM before extracting or executing the dump; checks the manifest;
refuses existing tables, non-system schemas and conflicting roles; restores authorization
roles with logins disabled and no password hashes; and restores in a single transaction.
It compares every backed-up application/Auth/Storage table's row hashes and counts,
validates relationships including historical NOT VALID foreign keys, checks tenant RLS
and ledger balances, and rejects RTO over two hours. Re-enable required platform logins
only after rotating credentials and verifying the managed Auth/service boundary.

`python scripts/check_restore_drill.py` provides a repeatable **synthetic local** proof:
two disposable PostgreSQL 16 instances, all migrations/seed, a trial wallet and payment
evidence, backup, actual decryption/restore and refusal to overwrite the populated target.
It deletes only its own containers/network and its own temporary artifacts. The result
is not a production-sized RTO, remote Storage restore, or production PITR proof.

For GNG-10 closure, record release SHA, backup timestamp/hash, clean target identity,
recovery-start/end times, observed data-loss interval, integrity checks, Storage object
recovery, Auth verification and operator sign-off. A local fixture duration cannot replace
the production recovery drill or externally observed RPO.
