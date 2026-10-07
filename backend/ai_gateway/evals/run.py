"""Run all owner cases through POST agent → worker handler → GET job.

Run from backend/, with the local stack and scripts/dev_fixture.py prepared:
    python -m ai_gateway.evals.run --provider MOCK --out ../docs/ai/evals/mock.json

All SQL, including sandbox setup, jobs, routing, audit and wallet debit, stays
inside an outer transaction that always rolls back. The ordinary worker cannot
see these uncommitted jobs; its registered handler runs on this same connection.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback
from typing import Any
from unittest.mock import patch
from uuid import UUID, uuid4, uuid5, NAMESPACE_URL

import yaml

from ai_gateway.evals.outcomes import canonical, classify, evaluate, summarize
from ai_gateway.evals.facts import engine_accepted, frame_bar_count, priced_winner
from ai_gateway.evals.redaction import redact_report

ROOT = Path(__file__).resolve().parents[3]
NAMESPACE = uuid5(NAMESPACE_URL, "https://dekopen.local/dev-fixture")
ORG_ID = uuid5(NAMESPACE, "org")
PHYSICAL_USAGE_TABLES = frozenset({"ai_provider_usage", "ai_usage_events"})
AI_TABLES = frozenset({
    "ai_jobs", "ai_job_cancel_signals", "ai_audit_logs", "job_runs", "job_events",
    "credit_ledger", "credit_lots", "credit_lot_movements", "credit_grants",
})


def load_cases() -> list[dict]:
    cases = yaml.safe_load(Path(__file__).with_name("cases.yaml").read_text(encoding="utf-8"))["cases"]
    if len(cases) != 26 or len({c["id"] for c in cases}) != 26:
        raise ValueError("The owner suite must contain exactly 26 unique cases")
    return cases


def fixture_project(items: list[dict]) -> UUID:
    matches = [p for p in items if p.get("name", "").endswith("[CASA_LOMAS]")]
    if len(matches) != 1:
        raise ValueError("Prepare exactly one CASA_LOMAS demo fixture in the active organization")
    return UUID(matches[0]["id"])


def apply_copy(product: dict, ops: list[dict]) -> tuple[dict, dict]:
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node and npm ci in frontend/ are required")
    # A canvas applier needs no credentials. Do not inherit backend secrets.
    environment = {k: v for k, v in os.environ.items() if k.upper() in {
        "PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATHEXT",
    }}
    completed = subprocess.run(
        [node, str(Path(__file__).with_name("sandbox.mjs"))],
        input=canonical({"product": product, "ops": ops}), text=True,
        encoding="utf-8", capture_output=True, timeout=30, cwd=ROOT,
        env=environment, check=False,
    )
    if completed.returncode:
        # Do not publish stack dumps/provider environment in result artifacts.
        raise RuntimeError("canvas_registry_application_failed")
    output = json.loads(completed.stdout)
    return output["product"], output["wire"]


class Recorder:
    """Observe the gateway boundary without replacing prompts/providers/validation."""

    def __init__(self, invoke: Callable[..., dict]):
        self.invoke = invoke
        self.rounds: list[dict] = []

    def __call__(self, **kwargs: Any) -> dict:
        payload = kwargs.get("input_payload") or {}
        entry: dict = {
            "round": len(self.rounds) + 1,
            "phase": "grounding" if payload.get("correction") else "planning",
            "context_fields": sorted((payload.get("context") or {}).keys()),
            "observation_surfaces": [o.get("surface") for o in payload.get("observations") or []],
            "correction": payload.get("correction"),
        }
        self.rounds.append(entry)
        started = time.perf_counter()
        try:
            output = self.invoke(**kwargs)
        except Exception as error:
            entry["error_code"] = str(getattr(error, "contract_code", None) or
                                      getattr(error, "code", None) or type(error).__name__)
            raise
        else:
            entry.update({k: output.get(k) for k in (
                "model", "tokens_prompt", "tokens_completion", "latency_ms", "credits_debited",
            )})
            try:
                entry["document"] = json.loads(output["output"])
            except (json.JSONDecodeError, TypeError):
                entry["format_error"] = True
            return output
        finally:
            entry["wall_latency_ms"] = round((time.perf_counter() - started) * 1000)
            sanitized = redact_report(entry)
            entry.clear()
            entry.update(sanitized)


def _snapshot(*, include_ai: bool = False) -> dict[str, str]:
    from django.db import connection, transaction
    from authentication.rls import tx_aborted

    # Some legacy projection scopes restore `authenticated`, because their
    # normal worker transaction ends immediately afterwards. Here the outer
    # sandbox deliberately stays open. Inspect as the local connection owner
    # without changing the actor/role used by any product endpoint or handler.
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.execute("SELECT current_setting('role')")
        previous_role = cursor.fetchone()[0]
        cursor.execute("SET LOCAL ROLE NONE")
        try:
            return _snapshot_rows(cursor, include_ai=include_ai)
        finally:
            if not tx_aborted():
                cursor.execute("SELECT set_config('role', %s, true)", [previous_role])


def _snapshot_rows(cursor: Any, *, include_ai: bool) -> dict[str, str]:
    from django.db import connection

    snapshots = {}
    cursor.execute(
        "SELECT c.table_name FROM information_schema.columns c "
        "JOIN information_schema.tables t USING (table_schema, table_name) "
        "WHERE c.table_schema='public' AND c.column_name='org_id' "
        "AND t.table_type='BASE TABLE' ORDER BY c.table_name"
    )
    tables = [r[0] for r in cursor.fetchall()]
    for table in tables:
        # Paid exchanges cannot be rolled back. Report their delta separately;
        # domain, wallet and sealed audit snapshots retain their original gate.
        if table in PHYSICAL_USAGE_TABLES:
            continue
        if table in AI_TABLES and not include_ai:
            continue
        quoted = connection.ops.quote_name(table)
        cursor.execute(f"SELECT row_to_json(t) FROM public.{quoted} t WHERE org_id=%s", [ORG_ID])
        rows = sorted(canonical(row[0]) for row in cursor.fetchall())
        snapshots[table] = hashlib.sha256(canonical(rows).encode()).hexdigest()
    if include_ai:
        cursor.execute("SELECT row_to_json(t) FROM public.tenancy_organizations t WHERE id=%s", [ORG_ID])
        snapshots["organization"] = hashlib.sha256(canonical(cursor.fetchall()).encode()).hexdigest()
        cursor.execute("SELECT row_to_json(t) FROM public.ai_routes t WHERE capability='agent'")
        snapshots["agent_route"] = hashlib.sha256(canonical(cursor.fetchall()).encode()).hexdigest()
    return snapshots


def _physical_usage_counts():
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM public.ai_provider_usage WHERE org_id=%s", [ORG_ID])
        exchanges = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM public.ai_usage_events WHERE org_id=%s", [ORG_ID])
        return {"exchanges": exchanges, "events": cursor.fetchone()[0]}


def _request(client: Any, method: str, path: str, data: dict | None = None) -> tuple[int, dict]:
    response = getattr(client, method)(f"/api/v1/{path}", data=data, format="json", HTTP_HOST="localhost")
    return response.status_code, response.json()


def _setup_product(source: dict, setup: str) -> dict:
    tree = source["design"]["parametric_tree"]

    def find_bay(node: dict) -> dict:
        if node.get("type") == "BAY":
            return node
        return find_bay(node["children"][0])

    bay = deepcopy(find_bay(tree))
    bay.update({"id": "eval-left", "type": "BAY", "opening_type": "FIXED"})
    for key in ("width_mm", "height_mm", "handle_height_mm", "sliding_layout"):
        bay.pop(key, None)
    if setup == "tilt_left":
        bay["opening_type"] = "TILT_TURN_LEFT"
    if setup in {"two_fixed", "fixed_tilt"}:
        right = {**deepcopy(bay), "id": "eval-right"}
        if setup == "fixed_tilt":
            right["opening_type"] = "TILT_TURN_LEFT"
        bay = {"id": "eval-mullion", "type": "SPLIT_V", "split_offset_mm": "750.00",
               "mullion_profile_sku": tree.get("mullion_profile_sku", "POSTE-V"),
               "children": [bay, right]}
    return {"version": "product-v2", "assembly": {"modules": [
        {"id": "eval-module", "width_mm": "1500.00", "height_mm": "1200.00", "tree": bay},
    ], "couplings": []}}


def _claims_context(claims: dict, surface: str, refs: dict) -> dict:
    from authentication.rls import authenticated_rls_context
    from ai_gateway.context import build_context

    with authenticated_rls_context(claims):
        return build_context(ORG_ID, surface, refs)


def _engine_copy(client: Any, product: dict, design: dict) -> dict:
    from engine_api.adapter import elevation_envelope, parse_product_model

    try:
        parsed = parse_product_model(product)
        width, height = elevation_envelope(parsed.assembly)
        status, output = _request(client, "post", "engine/assembly/calculate/", {
            "system_id": design["system_id"], "color": design["color"],
            "nominal_width_mm": str(width), "nominal_height_mm": str(height), "product": product,
        })
        return {"http_status": status, "result": output}
    except (ValueError, TypeError):
        return {"http_status": None, "error_code": "invalid_proposed_product"}


def sliding_probe(product: dict, *, kitchen: bool = False) -> dict:
    """New authoring is judged on physical capabilities, not legacy transport."""
    proposed = deepcopy(product)
    module = proposed["assembly"]["modules"][0]
    if kitchen:
        module.update(width_mm="1600.00", height_mm="1100.00")
    tree = module["tree"]
    tree.pop("opening_type", None)
    tree["opening"] = {"movement": "SLIDE", "hinge_side": "NONE", "direction": "INWARD",
                       "leaf_role": "SINGLE", "fixed_in_sash": False}
    tree["opening_use"] = "WINDOW"
    tree["sliding_layout"] = {"tracks": 2, "panels": [
        {"slot": "1", "kind": "MOVING", "track": 0},
        {"slot": "2", "kind": "MOVING", "track": 1}]}
    return proposed


def physical_sliding_supported(product: dict, params: Any) -> bool:
    from dekopen_engine.models import ParametricNode
    from dekopen_engine.openings import OpeningCapabilityError, normalize_opening_tree
    try:
        normalize_opening_tree(ParametricNode.model_validate_json(canonical(product["assembly"]["modules"][0]["tree"])), params)
    except OpeningCapabilityError:
        return False
    return True


def design_step_ops(result: dict) -> list[dict]:
    return [op for step in result.get("steps") or [] if step.get("kind") == "ops"
            for op in step.get("ops") or []]


def _intent(op: dict) -> dict:
    return {key: ([_intent(child) for child in value] if key == "ops" else value)
            for key, value in op.items() if key not in {"base_sig", "result", "description", "context_effect"}}


def _sandbox_project(client: Any, project: dict, result: dict) -> dict | None:
    """Exercise the normal human-click apply API in the rollback sandbox."""
    current = None
    for step in result.get("steps") or []:
        if step.get("kind") == "project_ops":
            ops = [_intent(op) for op in step.get("ops") or []]
        elif step.get("kind") == "batch_ops":
            ops = [{"op": "apply_to_positions", "filter": {"position_ids": [item["position_id"]]},
                    "ops": [_intent(op) for op in item["ops"]]} for item in step.get("items") or []]
        else:
            continue
        path = f"projects/{project['id']}/operations/"
        status, preview = _request(client, "post", path + "preview/", {"ops": ops})
        if status != 200 or not preview.get("valid"):
            raise RuntimeError("project_sandbox_preview_failed")
        status, applied = _request(client, "post", path + "apply/", {
            "ops": ops, "before_sig": preview["before_sig"], "operation_key": f"eval:apply:{uuid4().hex}"})
        if status != 200 or applied.get("state") != "APPLIED":
            raise RuntimeError("project_sandbox_application_failed")
        current = applied["project"]
    return current


def _ground_truth(client: Any, claims: dict, project: dict, position: dict,
                  product: dict, case: dict) -> dict:
    from authentication.rls import authenticated_rls_context
    from projects.design_assist import _catalog
    from engine_api.repository import SystemParamsRepository
    from django.db import connection

    project_id = project["id"]

    with authenticated_rls_context(claims):
        catalog = _catalog(UUID(position["design"]["system_id"]), ORG_ID)
        params = SystemParamsRepository().load_visible(UUID(position["design"]["system_id"]), ORG_ID)
    truth: dict = {
        "glass_recipes": catalog["glass_recipes"],
        "existing_sku": sorted(catalog["glass_skus"])[0] if catalog["glass_skus"] else None,
        "second_floor_ids": [p["id"] for p in project["positions"] if
                             any(t in p["location_tag"].lower() for t in ("segundo piso", "2º piso", "piso 2"))],
        "position_three": next((p for p in project["positions"] if p["position_index"] == 3), None),
        "quote_path": f"/projects/{project_id}/pricing",
        "most_expensive": None,
        "frame_bars": None,
        "revision_differences": None,
        "mullion_half_face_mm": str(next(article.face_width_mm / 2
                                        for role, article in params.effective_profile_articles.items()
                                        if role.value == "MULLION_V")),
    }
    with connection.cursor() as cursor:
        cursor.execute("SELECT revision_code FROM public.project_versions WHERE org_id=%s AND project_id=%s",
                       [ORG_ID, project_id])
        truth["revisions"] = [r[0] for r in cursor.fetchall()]
        cursor.execute("SELECT id, order_code, payload_json FROM public.orders "
                       "WHERE org_id=%s AND order_type='WORKSHOP_OT' ORDER BY order_code", [ORG_ID])
        orders = cursor.fetchall()
    truth["work_order_code"] = str(orders[0][1]) if orders else None
    if orders:
        order_payload = orders[0][2]
        if isinstance(order_payload, str):
            order_payload = json.loads(order_payload)
        truth["frame_bars"] = frame_bar_count(order_payload)
    pricing_status, operations = _request(client, "get", "pricing/operations/")
    if pricing_status == 200:
        truth["most_expensive"] = priced_winner(project, operations)
    if {"REV-A", "REV-B"} <= set(truth["revisions"]):
        status, comparison = _request(client, "get",
            f"documents/projects/{project_id}/versions/compare/?base=REV-A&head=REV-B")
        if status == 200:
            truth["revision_differences"] = comparison.get("positions")
    if case["expected"] in {"kitchen_position", "incompatible_sliding"}:
        kitchen = sliding_probe(product, kitchen=case["expected"] == "kitchen_position")
        compatibility = _engine_copy(client, kitchen, position["design"])
        truth["sliding_compatibility_engine"] = compatibility
        truth["sliding_supported"] = (engine_accepted(compatibility)
            if physical_sliding_supported(kitchen, params) else False)
    production = _claims_context(claims, "production", {})
    truth["blocked_orders"] = [o for o in production.get("work_orders", []) if o.get("status") == "BLOCKED"]
    # Manager-only inventory coverage must not be inferred through estimator RLS.
    purchase = _claims_context(claims, "purchase_plan", {})
    truth["purchase_context"] = purchase
    truth["purchase_shortages"] = purchase.get("uncovered_lines") if purchase.get("coverage_verified") else None
    quotation = _claims_context(claims, "quotation", {"project_id": str(project_id)})
    truth["quotation_context"] = quotation
    status, preparation = _request(client, "get", f"documents/projects/{project_id}/inputs/")
    truth["documentary_preparation"] = preparation if status == 200 else {"http_status": status}
    truth["documentary_missing"] = preparation.get("missing") if status == 200 else None
    if case["view"] == "editor":
        status, engine = _request(client, "post", "engine/assembly/calculate/", {
            "system_id": position["design"]["system_id"], "color": position["design"]["color"],
            "nominal_width_mm": "1500.00", "nominal_height_mm": "1200.00", "product": product,
        })
        truth["engine_http_status"] = status
        truth["engine_blockers"] = engine.get("issues") if status == 200 else None
        truth["right_leaf_weight"] = None
        if status == 200:
            truth["engine_result"] = engine
            for module in engine.get("modules") or []:
                for leaf in (module.get("result") or {}).get("leaf_weights") or []:
                    if leaf.get("bay_id") == "eval-right":
                        truth["right_leaf_weight"] = leaf.get("total_weight_kg")
    return truth


def run_case(case: dict, *, client: Any, claims: dict, provider: str, model: str, project_id: UUID) -> dict:
    from django.db import connection, transaction
    from ai_gateway import agent
    from ai_gateway.handlers import ai_agent_run
    from jobs.registry import JobContext, JobPermanentError

    recorder = Recorder(agent.gateway.invoke)
    started = time.perf_counter()
    output: dict = {"id": case["id"], "view": case["view"], "request": case["request"],
                    "expected": case["expected"], "provider": provider}
    result: dict = {}
    error_code = ""
    before: dict = {}
    after: dict = {}
    truth: dict = {}
    with transaction.atomic():
        try:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE public.ai_routes SET provider=%s, provider_model=%s "
                               "WHERE capability='agent'", [provider, model])
                cursor.execute("UPDATE public.ai_capability_routes SET provider=%s,provider_model=%s WHERE org_id=%s AND capability='agent'", [provider, model, ORG_ID])
            status, project = _request(client, "get", f"projects/{project_id}/")
            if status != 200 or len(project.get("positions") or []) != 12:
                raise RuntimeError("local_fixture_requires_twelve_positions")
            position = project["positions"][0]
            before = _setup_product(position, case.get("setup", "fixed"))
            after, wire = apply_copy(before, [])
            if case["view"] == "editor":
                # Sandbox copy of the position on this uncommitted connection,
                # through the ordinary save/engine path, never actorless SQL.
                status, saved = _request(client, "put", f"positions/{position['id']}/", {
                    "location_tag": position["location_tag"], "quantity": position["quantity"],
                    "expected_updated_at": position["updated_at"], "design": {
                        **position["design"], "nominal_width_mm": "1500.00",
                        "nominal_height_mm": "1200.00", "parametric_tree": before["assembly"]["modules"][0]["tree"],
                    },
                })
                if status != 200:
                    raise RuntimeError("sandbox_position_setup_failed")
                position = saved
            truth = _ground_truth(client, claims, project, position, before, case)
            request = case["request"].replace("[SKU existente]", truth["existing_sku"] or "[SKU existente]")
            request = request.replace("[código]", truth["work_order_code"] or "[código]")
            output["resolved_request"] = request
            surface = {"editor": "position", "project": "project", "factory": "production",
                       "general": "dashboard"}[case["view"]]
            refs = ({"position_id": position["id"]} if surface == "position" else
                    {"project_id": str(project_id)} if surface == "project" else {})
            baseline = _snapshot()
            payload = {"surface": surface, "refs": refs, "goal": request,
                       "operation_key": f"eval:{case['id']}:{uuid4().hex}"}
            if surface == "position":
                payload["product"] = wire
            with patch.object(agent.gateway, "invoke", recorder):
                status, accepted = _request(client, "post", "ai/agent/", payload)
                output["submission_http_status"] = status
                if status == 202:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT id, payload, created_by, max_attempts FROM public.job_runs "
                                       "WHERE org_id=%s AND payload->>'ai_job_id'=%s",
                                       [ORG_ID, accepted["job_id"]])
                        job_id, job_payload, actor, attempts = cursor.fetchone()
                    if isinstance(job_payload, str):
                        job_payload = json.loads(job_payload)
                    context = JobContext(job_id=job_id, org_id=ORG_ID, created_by=actor,
                                         attempt=1, max_attempts=attempts, payload=job_payload)
                    try:
                        ai_agent_run(job_payload, context, lambda _: None)
                    except JobPermanentError as error:
                        error_code = str(error)
                    _, job = _request(client, "get", f"ai/jobs/{accepted['job_id']}/")
                    result = job.get("result") or {}
                    result["state"] = job.get("state")
                    error_code = error_code or job.get("error_code") or ""
                else:
                    error_code = (accepted.get("error") or {}).get("code", "request_failed")
            current = _snapshot()
            changed = [name for name, value in baseline.items() if current.get(name) != value]
            ops = design_step_ops(result)
            try:
                after, _ = apply_copy(before, ops)
                output["sandbox_engine_after"] = _engine_copy(client, after, position["design"])
                batch_ok = True
                batch_results = []
                for step in result.get("steps") or []:
                    if step.get("kind") != "batch_ops":
                        continue
                    for item in step.get("items") or []:
                        source = next(p for p in project["positions"] if p["id"] == item["position_id"])
                        source_tree = source["design"]["parametric_tree"]
                        source_product = (source_tree if source_tree.get("version") == "product-v2" else
                                          {"version": "product-v2", "assembly": {"couplings": [], "modules": [{
                                              "id": "single", "width_mm": source["design"]["nominal_width_mm"],
                                              "height_mm": source["design"]["nominal_height_mm"], "tree": source_tree,
                                          }]}})
                        applied, _ = apply_copy(source_product, item["ops"])
                        engine = _engine_copy(client, applied, source["design"])
                        batch_ok = batch_ok and engine_accepted(engine)
                        batch_results.append({"position_id": item["position_id"], "product": applied,
                                              "engine": engine})
                applied_project = _sandbox_project(client, project, result)
                if applied_project:
                    truth["project_application_ok"] = True
                    truth["project_positions"] = applied_project["positions"]
                    truth["original_position_ids"] = [p["id"] for p in project["positions"]]
                    output["sandbox_project"] = applied_project
                truth["batch_application_ok"] = batch_ok
                output["sandbox_batch_results"] = batch_results
            except (RuntimeError, StopIteration) as error:
                error_code = error_code or str(error) or "sandbox_position_reference_missing"
                truth["batch_application_ok"] = False
            verdict = evaluate(case, before=before, after=after, result=result,
                               truth=truth, changed_tables=changed,
                               engine_after=output.get("sandbox_engine_after") or {})
            if error_code:
                verdict.update(passed=False, failure=classify(error_code, result.get("rejected") or []))
            output.update(verdict)
            output.update({"sandbox_before": before, "sandbox_after": after, "truth": truth,
                           "response": result, "rejected_operations": result.get("rejected") or [],
                           "error_code": error_code, "changed_domain_tables": changed})
        except Exception as error:
            # Infrastructure failures are retained per case so one failure
            # cannot turn a 26-case report into a silently truncated run.
            code = str(getattr(error, "contract_code", None) or
                       getattr(error, "code", None) or type(error).__name__)
            output.update({"passed": False, "failure": "contexto_insuficiente",
                           "error_code": code, "harness_error": str(error)[:160], "checks": [],
                           "harness_frames": [{"file": Path(f.filename).name, "line": f.lineno,
                                               "function": f.name}
                                              for f in traceback.extract_tb(error.__traceback__)[-4:]]})
        finally:
            transaction.set_rollback(True)
    output["latency_ms"] = round((time.perf_counter() - started) * 1000)
    output["rounds"] = recorder.rounds
    output["round_count"] = len(recorder.rounds)
    proposed = []
    for entry in recorder.rounds:
        doc = entry.get("document")
        if isinstance(doc, dict):
            for step in doc.get("steps") or []:
                if isinstance(step, dict):
                    proposed.extend(step.get("ops") or [])
    output["proposed_operations"] = proposed
    output["grounding_rejections"] = sum(r["phase"] == "grounding" for r in recorder.rounds)
    output["grounding_terminal_failure"] = error_code == "ai_agent_ungrounded"
    return redact_report(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", required=True, help="MOCK, configurado, or the configured provider name")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--case", help="One case for diagnosing the harness; omit for the acceptance suite")
    args = parser.parse_args()
    verified_ref = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    source_paths = ["backend", "engine", "frontend/src", "scripts/ai_evals.py"]
    if subprocess.run(["git", "diff", "--quiet", verified_ref, "--", *source_paths],
                      cwd=ROOT, capture_output=True, check=False).returncode:
        parser.error("Commit product/harness sources before recording an evaluation reference")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django
    django.setup()
    from django.conf import settings
    from django.db import connection
    from rest_framework.test import APIClient
    from authentication.jwt_verifier import get_token_verifier
    import httpx

    database = settings.DATABASES["default"]
    if not settings.DEBUG or database.get("HOST") not in {"127.0.0.1", "localhost", "::1"}:
        parser.error("Evaluations are restricted to a DEBUG local PostgreSQL fixture")
    if connection.vendor != "postgresql":
        parser.error("Start the local Supabase stack and run scripts/dev_fixture.py first")
    with connection.cursor() as cursor:
        cursor.execute("SELECT provider, provider_model FROM public.ai_routes WHERE capability='agent' AND enabled")
        route = cursor.fetchone()
    if not route:
        parser.error("The local fixture needs an enabled agent route")
    provider = str(route[0]).upper() if args.provider.lower() == "configurado" else args.provider.upper()
    if provider not in {"MOCK", str(route[0]).upper()}:
        parser.error("Use MOCK or the provider already configured on the local agent route")
    if provider == "MOCK":
        os.environ["AI_GATEWAY_MOCK_ENABLED"] = "1"
    model = "deterministic-eval" if provider == "MOCK" else os.environ.get(
        f"AI_GATEWAY_{provider}_MODEL", str(route[1]))
    response = httpx.post(
        f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/token?grant_type=password",
        headers={"apikey": settings.SUPABASE_ANON_KEY},
        json={"email": "demo-estimator@fixture.dekopen.local", "password": "Demo-Fixture-2026!"}, timeout=15,
    )
    if response.status_code != 200:
        parser.error("Local estimator fixture login failed; run scripts/dev_fixture.py")
    access_token = response.json()["access_token"]
    verified = get_token_verifier().verify(access_token)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}", HTTP_X_ORGANIZATION_ID=str(ORG_ID))
    status, listing = _request(client, "get", "projects/")
    if status != 200:
        parser.error("The estimator fixture cannot read its projects")
    try:
        project_id = fixture_project(listing.get("items") or [])
    except ValueError as error:
        parser.error(str(error))
    cases = load_cases()
    if args.case:
        cases = [c for c in cases if c["id"] == args.case]
        if not cases:
            parser.error("Unknown case id")
    # Initialize a missing budget row before taking the source-state baseline.
    # Existing OWNER budgets and routes are never replaced by the harness.
    with connection.cursor() as cursor:
        cursor.execute("INSERT INTO public.ai_settings(org_id) VALUES(%s) ON CONFLICT DO NOTHING", [ORG_ID])
    snapshot = _snapshot(include_ai=True)
    physical_before = _physical_usage_counts()
    results = []
    for case in cases:
        result = run_case(case, client=client, claims=verified.claims, provider=provider, model=model,
                          project_id=project_id)
        results.append(result)
        print(f"{case['id']}: {'PASA' if result['passed'] else result['failure']} "
              f"({result['round_count']} rounds, {result['latency_ms']} ms)", flush=True)
    unchanged = snapshot == _snapshot(include_ai=True)
    physical_after = _physical_usage_counts()
    source_unchanged = subprocess.run(
        ["git", "diff", "--quiet", verified_ref, "--", *source_paths],
        cwd=ROOT, capture_output=True, check=False,
    ).returncode == 0
    report = {
        "schema_version": 2, "generated_at": datetime.now(timezone.utc).isoformat(),
        "verified_ref": verified_ref, "execution_source_unchanged": source_unchanged,
        "provider": provider, "provider_model": model,
        "fixture": {"org_id": str(ORG_ID), "project_id": str(project_id), "synthetic": True,
                    "manufacturing_authority": False},
        "transport": {"submit": "POST /api/v1/ai/agent/", "read": "GET /api/v1/ai/jobs/{id}/",
                      "worker": "ai_gateway.handlers.ai_agent_run", "transaction": "always rolled back"},
        "persistent_state_unchanged": unchanged, "summary": summarize(results), "cases": results,
        "physical_provider_usage_delta": {key: physical_after[key] - value for key, value in physical_before.items()},
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(redact_report(report), ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"{len(results)} cases recorded; persistent state {'unchanged' if unchanged else 'CHANGED'}.")
    # Product failures are baseline data; a broken harness/isolation is an error.
    return 0 if unchanged and source_unchanged and not any(c.get("harness_error") for c in results) else 1


if __name__ == "__main__":
    sys.exit(main())
