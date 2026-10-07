"""Provider metadata and budget reservations, independent of domain rollback.

Financial audits still debit atomically with the proposal. This ledger measures
the real provider exchange, including a subsequently rejected proposal. It
stores neither prompts nor responses. Public readers receive allowlisted fields.
"""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from decimal import Decimal
import json
import logging
from uuid import UUID
from zoneinfo import ZoneInfo

from django.db import connection

from authentication.errors import contract_error
from billing.wallet import financial_transaction
from dekopen_engine.billing import ai_usage_cost_usd
from pricing.repository import rows

logger = logging.getLogger(__name__)
_job: ContextVar[tuple | None] = ContextVar("ai_provider_job", default=None)
CAPABILITIES = ("design_assist", "agent", "context_assist", "catalog_import")


@contextmanager
def job_context(job_id, ai_job_id):
    token = _job.set((job_id, ai_job_id))
    outcome = "SUCCEEDED"
    try:
        yield
    except Exception as error:
        outcome = getattr(error, "contract_code", None) or getattr(error, "code", None) or "ai_job_failed"
        raise
    finally:
        _job.reset(token)
        if connection.vendor == "postgresql":
            _log_job(job_id, ai_job_id, outcome)


def _log_job(job_id, ai_job_id, outcome):
    def read():
        with connection.cursor() as cursor:
            cursor.execute("SELECT capability,provider_model,latency_ms,tokens_prompt,tokens_completion FROM public.ai_provider_usage WHERE job_id=%s AND ai_job_id=%s ORDER BY created_at", [str(job_id), str(ai_job_id)])
            return cursor.fetchall()
    records = independent(read)
    if records:
        logger.info(json.dumps({"event": "ai_provider_job", "job_id": str(job_id),
            "capability": records[-1][0], "model": records[-1][1], "rounds": len(records),
            "latency_ms": sum(item[2] for item in records) if all(item[2] is not None for item in records) else None,
            "tokens_prompt": sum(item[3] for item in records) if all(item[3] is not None for item in records) else None,
            "tokens_completion": sum(item[4] for item in records) if all(item[4] is not None for item in records) else None,
            "result": outcome}, sort_keys=True))


def independent(call):
    """Django connections are thread-local; this write cannot join act's atomic.
    Await the commit and propagate failures. Never silently lose usage metadata.
    """
    def run():
        try:
            return call()
        finally:
            connection.close()
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(run).result()


def month_start(now=None):
    local = (now or datetime.now(timezone.utc)).astimezone(ZoneInfo("America/Santiago"))
    return local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def begin(*, org_id, user_id, route, operation_key, input_hash):
    if connection.vendor != "postgresql":
        return None
    job = _job.get()
    def reserve():
        with financial_transaction(org_id):
            rows("INSERT INTO public.ai_settings(org_id) VALUES(%s) ON CONFLICT DO NOTHING RETURNING org_id", [str(org_id)])
            settings = rows("SELECT * FROM public.ai_settings WHERE org_id=%s FOR UPDATE", [str(org_id)])[0]
            existing = rows("SELECT * FROM public.ai_provider_usage WHERE org_id=%s AND operation_key=%s ORDER BY attempt DESC LIMIT 1 FOR UPDATE", [str(org_id), operation_key])
            if existing:
                old = existing[0]
                if old["input_hash"] != input_hash or old["capability"] != route["capability"] or str(old["user_id"]) != str(user_id):
                    raise contract_error(409, "ai_operation_conflict", "La operación ya se usó con otra solicitud.")
                # The financial audit replays first. A paid exchange whose
                # proposal rolled back cannot be paid a second time under the
                # same key; the user starts a new explicit request instead.
                if old["status"] != "FAILED" or old["tokens_prompt"] is not None:
                    raise contract_error(409, "ai_operation_in_progress", "Esta solicitud ya consultó al proveedor o sigue en curso. Revisa Trabajos antes de iniciar otra.")
            consumed = rows("SELECT coalesce(sum(credits_reserved),0) AS consumed FROM public.ai_provider_usage WHERE org_id=%s AND created_at >= %s AND (status IN ('RUNNING','SUCCEEDED') OR tokens_prompt IS NOT NULL OR error_code IN ('ai_provider_error','ai_provider_timeout','ai_provider_output_too_large'))", [str(org_id), month_start()])[0]["consumed"]
            budget = settings["monthly_budget_credits"]
            if budget is not None and int(consumed) + int(route["credits_cost"]) > budget:
                rows("UPDATE public.ai_settings SET budget_notice_at=now() WHERE org_id=%s RETURNING org_id", [str(org_id)])
                # Commit the OWNER notice before reporting the soft block.
                return {"blocked": True}
            values = [str(org_id), str(user_id), str(job[0]) if job else None, str(job[1]) if job else None,
                      operation_key, input_hash, route["capability"], route["provider"], route["provider_model"],
                      route["provider"] == "MOCK", int(route["credits_cost"]), route.get("input_usd_per_million"), route.get("output_usd_per_million")]
            record = rows("INSERT INTO public.ai_provider_usage(org_id,user_id,job_id,ai_job_id,operation_key,input_hash,capability,provider,provider_model,test_mode,credits_reserved,input_usd_per_million,output_usd_per_million,attempt) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *", [*values, int(existing[0]["attempt"]) + 1 if existing else 1])[0]
            return record
    reservation = independent(reserve)
    if reservation.get("blocked"):
        raise contract_error(409, "ai_budget_exceeded", "La IA llegó al presupuesto mensual de esta organización. El dueño puede ajustarlo en Ajustes › Inteligencia artificial. Las funciones manuales siguen disponibles.")
    return reservation


def finish(reservation, *, result=None, error_code=None):
    if reservation is None:
        return
    result = result or {}
    known = result.get("usage_known", bool(result))
    prompt = int(result["tokens_prompt"]) if known else None
    completion = int(result["tokens_completion"]) if known else None
    cost = ai_usage_cost_usd(prompt, completion, reservation["input_usd_per_million"], reservation["output_usd_per_million"]) if known else None
    def persist():
        with financial_transaction(reservation["org_id"]):
            rows("UPDATE public.ai_provider_usage SET status=%s,tokens_prompt=%s,tokens_completion=%s,estimated_cost_usd=%s,latency_ms=%s,retries=%s,fallback=%s,tool_names=%s::jsonb,error_code=%s,completed_at=now(),provider_model=%s WHERE org_id=%s AND id=%s AND status='RUNNING' RETURNING id",
                 ["FAILED" if error_code else "SUCCEEDED", prompt, completion, cost,
                  result.get("latency_ms"), int(result.get("retries", 0)), bool(result.get("fallback")), "[]", error_code,
                  result.get("model") or reservation["provider_model"], str(reservation["org_id"]), str(reservation["id"])])
    independent(persist)
    logger.info(json.dumps({"event": "ai_provider_exchange", "job_id": str(reservation["job_id"]) if reservation["job_id"] else None,
                "capability": reservation["capability"], "model": result.get("model") or reservation["provider_model"],
                "latency_ms": result.get("latency_ms"), "rounds": 1, "tokens_prompt": prompt, "tokens_completion": completion,
                "result": error_code or "SUCCEEDED", "retries": result.get("retries", 0)}, sort_keys=True))


def note(org_id, usage_id, tool_name, status="OK"):
    if not usage_id:
        return
    from ai_gateway.engine_tools import BY_NAME
    from ai_gateway.agent import QUERY_TOOLS
    if tool_name not in set(BY_NAME) | set(QUERY_TOOLS.values()) | {"get_context", "validate_operations"} or status not in {"OK", "ERROR", "CACHED"}:
        raise ValueError("Unknown usage event")
    def persist():
        with financial_transaction(org_id):
            found = rows("INSERT INTO public.ai_usage_events(org_id,usage_id,tool_name,status) SELECT %s,id,%s,%s FROM public.ai_provider_usage WHERE org_id=%s AND id=%s RETURNING id", [str(org_id), tool_name, status, str(org_id), str(UUID(str(usage_id)))])
            if not found:
                raise ValueError("Usage event requires an owned exchange")
    independent(persist)


def summary(org_id, user_id=None):
    with financial_transaction(org_id):
        parameters = [str(org_id), month_start()]
        user_clause = " AND user_id=%s" if user_id else ""
        if user_id:
            parameters.append(str(user_id))
        records = rows("SELECT user_id,status,test_mode,credits_reserved,tokens_prompt,tokens_completion,estimated_cost_usd,error_code FROM public.ai_provider_usage WHERE org_id=%s AND created_at >= %s" + user_clause, parameters)
        settings = rows("SELECT * FROM public.ai_settings WHERE org_id=%s", [str(org_id)])
        debited = rows("SELECT coalesce(sum(points_debited),0) AS debited FROM public.ai_audit_logs WHERE org_id=%s AND created_at >= %s" + user_clause, parameters)[0]["debited"]
    def totals(items):
        complete = all(item["tokens_prompt"] is not None for item in items if item["status"] in ("RUNNING", "SUCCEEDED") or item["error_code"] in ('ai_provider_error','ai_provider_timeout','ai_provider_output_too_large'))
        charged = [item for item in items if item["tokens_prompt"] is not None]
        known_cost = all(item["estimated_cost_usd"] is not None for item in charged) and complete
        return {"calls": len(items), "tokens_prompt": sum(item["tokens_prompt"] for item in charged) if complete else None,
                "tokens_completion": sum(item["tokens_completion"] for item in charged) if complete else None,
                "capacity_credits": sum(item["credits_reserved"] for item in items if item["status"] in ("RUNNING", "SUCCEEDED") or item["tokens_prompt"] is not None or item["error_code"] in ('ai_provider_error','ai_provider_timeout','ai_provider_output_too_large')),
                "estimated_cost_usd": str(sum((item["estimated_cost_usd"] for item in charged), Decimal(0))) if known_cost and charged else None}
    total = totals(records)
    budget = settings[0]["monthly_budget_credits"] if settings else None
    names = user_names(org_id)
    return {**total, "credits_debited": int(debited), "monthly_budget_credits": budget,
            "budget_blocked": budget is not None and total["capacity_credits"] >= budget,
            "budget_notice_at": str(settings[0]["budget_notice_at"]) if settings and settings[0]["budget_notice_at"] else None,
            "month_start": month_start().isoformat(),
            "users": [{"user_id": user, "user_label": names.get(user), **totals([item for item in records if str(item["user_id"]) == user])} for user in sorted({str(item["user_id"]) for item in records})]}


def user_names(org_id):
    from django.db import transaction
    from jobs.service import job_owner
    with transaction.atomic(), job_owner():
        found = rows("SELECT m.user_id,coalesce(nullif(u.raw_user_meta_data->>'full_name',''),u.email) AS label FROM public.tenancy_memberships m JOIN auth.users u ON u.id=m.user_id WHERE m.org_id=%s", [str(org_id)])
    return {str(item["user_id"]): item["label"] for item in found}


def list_work(org_id, user_id=None, *, capability=None, state=None, limit=50, offset=0):
    from ai_gateway.configuration import cause
    from django.db import transaction
    from jobs.service import job_owner
    clauses, parameters = ["u.org_id=%s"], [str(org_id)]
    for column, value in (("u.user_id", user_id), ("u.capability", capability)):
        if value:
            clauses.append(f"{column}=%s")
            parameters.append(str(value))
    if state:
        clauses.append("coalesce(j.state,u.status)=%s")
        parameters.append(state)
    where = " AND ".join(clauses)
    with transaction.atomic(), job_owner():
        groups = rows(f"SELECT coalesce(u.job_id,u.id) AS group_id,max(u.created_at) AS created_at FROM public.ai_provider_usage u LEFT JOIN public.job_runs j ON j.id=u.job_id AND j.org_id=u.org_id WHERE {where} GROUP BY coalesce(u.job_id,u.id) ORDER BY max(u.created_at) DESC,coalesce(u.job_id,u.id) DESC LIMIT %s OFFSET %s", [*parameters, limit, offset])
    with financial_transaction(org_id):
        if not groups:
            return []
        ids = [str(group["group_id"]) for group in groups]
        # Filter actor again; no expanded projection can borrow another user.
        records = rows("SELECT id,job_id,ai_job_id,user_id,capability,status,test_mode,credits_reserved,tokens_prompt,tokens_completion,estimated_cost_usd,latency_ms,retries,fallback,tool_names,error_code,created_at FROM public.ai_provider_usage WHERE org_id=%s AND coalesce(job_id,id)=ANY(%s::uuid[])" + (" AND user_id=%s" if user_id else ""), [str(org_id), ids, *([str(user_id)] if user_id else [])])
        events = rows("SELECT usage_id,tool_name,status,created_at FROM public.ai_usage_events WHERE org_id=%s AND usage_id=ANY(%s::uuid[]) ORDER BY created_at,id", [str(org_id), [str(record["id"]) for record in records]])
    names = user_names(org_id)
    job_ids = [str(record["job_id"]) for record in records if record["job_id"]]
    with transaction.atomic(), job_owner():
        jobs = rows("SELECT id,state FROM public.job_runs WHERE org_id=%s AND id=ANY(%s::uuid[])", [str(org_id), job_ids]) if job_ids else []
    states = {str(job["id"]): job["state"] for job in jobs}
    result = []
    for group in groups:
        items = [record for record in records if str(record["job_id"] or record["id"]) == str(group["group_id"])]
        last = max(items, key=lambda record: record["created_at"])
        known = all(record["tokens_prompt"] is not None for record in items)
        cost_known = all(record["estimated_cost_usd"] is not None for record in items)
        usage_ids = {str(record["id"]) for record in items}
        trace = [{"tool": event["tool_name"], "status": event["status"]} for event in events if str(event["usage_id"]) in usage_ids]
        tools = {event["tool"] for event in trace}
        result.append({"id": str(group["group_id"]), "job_id": str(last["job_id"]) if last["job_id"] else None,
                       "ai_job_id": str(last["ai_job_id"]) if last["ai_job_id"] else None,
                       "capability": last["capability"], "user_id": str(last["user_id"]), "user_label": names.get(str(last["user_id"])),
                       "calls": len(items), "status": last["status"], "job_state": states.get(str(last["job_id"])),
                       "test_mode": any(record["test_mode"] for record in items),
                       "tokens_prompt": sum(record["tokens_prompt"] for record in items) if known else None,
                       "tokens_completion": sum(record["tokens_completion"] for record in items) if known else None,
                       "capacity_credits": sum(record["credits_reserved"] for record in items if record["status"] in ("RUNNING", "SUCCEEDED") or record["tokens_prompt"] is not None or record["error_code"] in ('ai_provider_error','ai_provider_timeout','ai_provider_output_too_large')),
                       "estimated_cost_usd": str(sum((record["estimated_cost_usd"] for record in items), Decimal(0))) if cost_known else None,
                       "latency_ms": sum(record["latency_ms"] for record in items) if all(record["latency_ms"] is not None for record in items) else None,
                       "retries": sum(record["retries"] for record in items), "fallback": any(record["fallback"] for record in items),
                       "tools": sorted(tools), "trace": trace, "last_cause": cause(last["error_code"]) if last["error_code"] else None,
                       "created_at": str(group["created_at"])})
    return result
