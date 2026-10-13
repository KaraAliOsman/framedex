---
name: testing-framedex
description: Prepare or reuse DEKOPEN's owned local Supabase, Django, worker and web stack for browser review or affected E2E flows, with fixture roles, Mailpit login and real AI configuration.
---

# DEKOPEN local stack

Use this recipe when the task needs a running product. Determine the repository
root from the current checkout; host paths and prior agents' temporary servers
are not portable. For domain context use [the wiki routes](../../../docs/wiki/index.md).

## Choose the stack

- For product review use the owned REVIEW runner in
  [`scripts/review_stack.py`](../../../scripts/review_stack.py). It builds API,
  web and job-worker images from this checkout and prepares the DEMO fixture.
- Reuse the owner's active REVIEW when the task needs existing data or sessions.
  `start` recreates its application containers and executes fixture preparation;
  source edits alone do not update the built images. Rebuild deliberately when
  the requested work needs a new running ref.
- A clean Database Gate is a separate workflow. Its
  `scripts/local_gates.py::require_disposable_stack` rejects existing Supabase
  containers/volumes before start or reset. Use an isolated project for that
  gate; it is not a repair command for REVIEW or another populated local DB.

Read [workspace ownership and protected state](../../../docs/operations/WORKSPACE.md)
before changing local resources. Preserve `.run/review/`, browser profiles,
launchers and registered WSL storage; `.run/` contains persistent state.

## Start an owned REVIEW when needed

Requires Docker, Python 3.12+ and Supabase CLI **2.116.0** on PATH. Frontend
development on the host requires Node **22.22.2+** and installed dependencies.
Use the project's Python environment (`.venv/Scripts/python.exe` on Windows,
`.venv/bin/python` on Linux) when available.

From the repository root on Windows:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_local.ps1
```

On either OS the underlying entry point is:

```text
python scripts/review_stack.py start
```

The runner checks resource ownership, copies current migrations/seed into the
owned work directory and starts its Supabase project `framedex-review` without
resetting an existing DB. It reads root `.env` into process memory, configures
Auth/CORS/storage/mail, starts `runjobs` and invokes `scripts/dev_fixture.py`.
Do not print or persist the environment, Supabase key output or auth tokens.

| REVIEW service | Endpoint |
|---|---|
| Product | `http://127.0.0.1:5179` |
| Django API | `http://127.0.0.1:8004` |
| Supabase API | `http://127.0.0.1:25361` |
| Postgres | `127.0.0.1:25362` |
| Mailpit | `http://127.0.0.1:25364` |

These ports are derived from `review_stack.py`; the development/gate config
uses different ports. Do not mix their keys, API endpoints or fixtures.

## Accounts, fixture and AI

[The review guide](../../../docs/GUIA-REVISION.md) lists the five role accounts
and client-link flow. Sign in at `/login`, request a magic link and open the
latest message for that recipient in REVIEW Mailpit. OWNER uses the product's
MFA enrollment/challenge; preserve an existing factor and browser session.
The client uses a revision-bound quotation link rather than a tenant role.

Current fixture preparation is `scripts/dev_fixture.py`; canonical schema and
catalog inputs are `supabase/migrations/` and `supabase/seed.sql`. Inspect the
relevant fixture section before extending it. DEMO data does not establish
manufacturer, thermal, production or purchasing-price authority. Changes to
issued data go through the successor/domain APIs, preserving sealed history.

REVIEW sets `AI_GATEWAY_MOCK_ENABLED=0` and loads configured `AI_GATEWAY_*`
values from `.env`. Read [provider rules](../../../docs/wiki/product/ai-provider.md)
when changing AI behavior; exercise the real provider only when the task calls
for it. Check current response/error codes and the worker when diagnosing a
blocked job. Use a migration for missing schema/grants; retain MFA, RLS and
immutability protections during diagnosis.

## Evidence and shutdown

Exercise the affected flow at the sizes/themes required by the task and
[constitution](../../../docs/design/CONSTITUCION.md). Save exploratory captures,
traces and logs under `.run/<task>/`; commit a deliberate evidence selection
according to [workspace retention](../../../docs/operations/WORKSPACE.md).

Stop a REVIEW started for the task with `python scripts/review_stack.py stop`;
this preserves data. Keep it running when the requested deliverable is a
usable local product. Do not stop an owner's reused stack during unrelated work.

The [previous guide](https://github.com/KaraAliOsman/framedex/blob/2db4e13171884b93a989e68508a55f5590f9b34d/.agents/skills/testing-framedex/SKILL.md)
preserves historical phase notes. Use current scripts, routes and domain wiki
for present behavior; those old recipes are not the current stack procedure.
