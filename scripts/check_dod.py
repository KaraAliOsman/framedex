#!/usr/bin/env python3
"""Cross-platform, fail-closed Definition of Done checker for Dekopen."""

from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

import local_gates

ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = ROOT / "engine"
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
SUPABASE_DIR = ROOT / "supabase"
SUPABASE_MIGRATION = (
    SUPABASE_DIR / "migrations" / "20260901000000_initial_schema.sql"
)
SUPABASE_SHOT_03_MIGRATION = (
    SUPABASE_DIR
    / "migrations"
    / "20260902000000_add_glazing_bead_cut_add.sql"
)
SUPABASE_TEST_DIR = SUPABASE_DIR / "tests" / "database"

PYTHON = sys.executable
NPM = shutil.which("npm")
SUPABASE = shutil.which("supabase")

REQUIRED_PATHS = (
    ROOT / "pyproject.toml",
    ENGINE_DIR / "pyproject.toml",
    ENGINE_DIR / "src" / "dekopen_engine" / "__init__.py",
    ENGINE_DIR / "src" / "dekopen_engine" / "models.py",
    ENGINE_DIR / "src" / "dekopen_engine" / "geometry.py",
    ENGINE_DIR / "src" / "dekopen_engine" / "glass.py",
    ENGINE_DIR / "src" / "dekopen_engine" / "bom.py",
    ENGINE_DIR / "tests" / "test_package.py",
    ENGINE_DIR / "tests" / "test_glass.py",
    ENGINE_DIR / "tests" / "test_gold_cases_core.py",
    ENGINE_DIR / "tests" / "test_gold_cases_deferred.py",
    ENGINE_DIR / "tests" / "test_models.py",
    ENGINE_DIR / "tests" / "test_purity.py",
    ENGINE_DIR / "tests" / "test_tree_geometry.py",
    BACKEND_DIR / "manage.py",
    BACKEND_DIR / "tests" / "test_bootstrap.py",
    BACKEND_DIR / "authentication" / "backends.py",
    BACKEND_DIR / "authentication" / "rls.py",
    BACKEND_DIR / "authentication" / "tenancy.py",
    BACKEND_DIR / "engine_api" / "adapter.py",
    BACKEND_DIR / "engine_api" / "repository.py",
    BACKEND_DIR / "openapi.yaml",
    BACKEND_DIR / "tests" / "test_jwt_authentication.py",
    BACKEND_DIR / "tests" / "test_tenancy.py",
    BACKEND_DIR / "tests" / "test_auth_me.py",
    BACKEND_DIR / "tests" / "test_engine_api.py",
    BACKEND_DIR / "tests" / "integration" / "test_rls_context_integration.py",
    FRONTEND_DIR / "package.json",
    FRONTEND_DIR / "package-lock.json",
    FRONTEND_DIR / "tsconfig.json",
    FRONTEND_DIR / "src" / "App.test.tsx",
    FRONTEND_DIR / "src" / "api" / "generated" / "dekopen.ts",
    FRONTEND_DIR / "src" / "auth" / "AuthSessionProvider.tsx",
    FRONTEND_DIR / "src" / "styles" / "tokens.css",
    FRONTEND_DIR / "src" / "telemetry" / "telemetry.ts",
    FRONTEND_DIR / "src" / "features" / "canvas" / "CanvasEditor2DView.tsx",
    FRONTEND_DIR / "src" / "features" / "canvas" / "CADViewportSvg.tsx",
    FRONTEND_DIR / "src" / "features" / "canvas" / "CanvasTechnicalResults.tsx",
    FRONTEND_DIR / "src" / "features" / "canvas" / "EditableDimension.tsx",
    FRONTEND_DIR / "src" / "features" / "canvas" / "canvasStore.ts",
    FRONTEND_DIR / "src" / "features" / "canvas" / "snapping.ts",
    FRONTEND_DIR / "src" / "features" / "canvas" / "useEngineCalculation.ts",
    FRONTEND_DIR / "src" / "features" / "canvas" / "CanvasEditor2DView.test.tsx",
    FRONTEND_DIR / "src" / "features" / "canvas" / "canvasResults.test.tsx",
    FRONTEND_DIR / "src" / "features" / "canvas" / "snapping.test.ts",
    FRONTEND_DIR / "tests" / "e2e" / "auth.spec.ts",
    FRONTEND_DIR / "tests" / "e2e" / "canvas.spec.ts",
    FRONTEND_DIR / "tests" / "e2e" / "support" / "mailpit.ts",
    FRONTEND_DIR / "tests" / "contracts" / "mailpit.test.ts",
    ROOT / "docs" / "plans" / "PLAN_SHOT-04.md",
    ROOT / "docs" / "plans" / "PLAN_SHOT-05.md",
    ROOT / "docs" / "PRD" / "PRD-DESIGN-SYSTEM-ADOBE.md",
    ROOT / "docs" / "PRD" / "PRD-WEB-MOBILE-ESSENTIAL.md",
    ROOT / "scripts" / "check_generated_api.py",
    ROOT / "scripts" / "local_gates.py",
    ROOT / "scripts" / "check_auth_e2e.py",
)

REQUIRED_DATABASE_PATHS = (
    SUPABASE_DIR / "config.toml",
    SUPABASE_MIGRATION,
    SUPABASE_SHOT_03_MIGRATION,
    SUPABASE_DIR / "seed.sql",
    SUPABASE_TEST_DIR / "000_schema.test.sql",
    SUPABASE_TEST_DIR / "010_rls_isolation.test.sql",
    SUPABASE_TEST_DIR / "020_global_catalog.test.sql",
    SUPABASE_TEST_DIR / "030_billing_idempotency.test.sql",
    SUPABASE_DIR / "compat" / "postgres16_bootstrap.sql",
    SUPABASE_DIR / "compat" / "postgres16_verify.sql",
    BACKEND_DIR / "tests" / "test_database_contract.py",
)

EXPECTED_DATABASE_TABLES = {
    "tenancy_organizations",
    "tenancy_memberships",
    "profile_systems",
    "profile_articles",
    "glazing_bead_matrix",
    "hardware_kits",
    "cost_lists",
    "cost_list_items",
    "pricing_rules",
    "price_audit_logs",
    "projects",
    "project_positions",
    "project_versions",
    "orders",
    "offcut_inventory",
    "ai_audit_logs",
    "payment_customers",
    "subscriptions",
    "payments",
    "payment_events",
    "credit_ledger",
}

EXPECTED_G_CASES = {
    "G1",
    "G2",
    "G3",
    "G4",
    "G5",
    "G6",
    "G7",
    "G8",
    "G9",
    "G10",
    "G11",
    "G12",
    "G-Pro1",
}

EXPECTED_G_CASE_STATUSES = {
    "G1": "pass",
    "G2": "pass",
    "G3": "pass",
    "G4": "pass",
    "G5": "pending",
    "G6": "pending",
    "G7": "pending",
    "G8": "xfail",
    "G9": "xfail",
    "G10": "xfail",
    "G11": "xfail",
    "G12": "xfail",
    "G-Pro1": "pending",
}

EXPECTED_G_CASE_TARGET_SHOTS = {
    "G1": "SHOT-03",
    "G2": "SHOT-03",
    "G3": "SHOT-03",
    "G4": "SHOT-03",
    "G5": "SHOT-06",
    "G6": "SHOT-06",
    "G7": "SHOT-06",
    "G8": "SHOT-06B",
    "G9": "SHOT-06B",
    "G10": "SHOT-24",
    "G11": "SHOT-06B",
    "G12": "SHOT-06B",
    "G-Pro1": "SHOT-12",
}

EXPECTED_G3_DEFERRED_ASSERTIONS = {
    "hardware_kit_resolution": {
        "status": "xfail",
        "target_shot": "SHOT-06",
        "reason": "SHOT-06: hardware_kits resolution",
    }
}


def configure_output() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def fail(message: str, exit_code: int = 1) -> None:
    print(f"[FAIL] {message}", file=sys.stderr, flush=True)
    if os.environ.get("GITHUB_ACTIONS") == "true":
        annotation = (
            message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        )
        print(
            f"::error title=Dekopen SHOT-04 gate::{annotation}",
            file=sys.stderr,
            flush=True,
        )
    raise SystemExit(exit_code)


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix() or "."
    except ValueError:
        return str(path)


def run_command(
    command: Sequence[str], *, cwd: Path = ROOT, env: Mapping[str, str] | None = None
) -> None:
    rendered = shlex.join(command)
    print(f"  [{display_path(cwd)}] $ {rendered}", flush=True)

    try:
        result = subprocess.run(command, cwd=cwd, env=env, check=False)
    except FileNotFoundError:
        fail(f"Required executable is missing: {command[0]}", 127)

    if result.returncode != 0:
        fail(f"Command exited with code {result.returncode}: {rendered}", result.returncode)


def npm_command(*arguments: str) -> list[str]:
    if NPM is None:
        fail("Required executable is missing: npm", 127)
    return [NPM, *arguments]


def check_required_paths() -> None:
    missing = [display_path(path) for path in REQUIRED_PATHS if not path.exists()]
    if missing:
        fail("Required SHOT-01 paths are missing: " + ", ".join(missing))
    print("  Required SHOT-01 paths: present", flush=True)


def check_required_database_paths() -> None:
    missing = [display_path(path) for path in REQUIRED_DATABASE_PATHS if not path.exists()]
    if missing:
        fail("Required SHOT-02 database paths are missing: " + ", ".join(missing))

    misplaced = sorted((SUPABASE_DIR / "tests").glob("postgres16_*.sql"))
    if misplaced:
        fail(
            "PostgreSQL compatibility scripts must be outside pgTAP discovery: "
            + ", ".join(display_path(path) for path in misplaced)
        )
    print("  Required SHOT-02 database paths: present", flush=True)


def check_python_ast_guards() -> None:
    engine_source = ENGINE_DIR / "src"
    for path in sorted(engine_source.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as error:
            fail(f"Invalid Python syntax in {display_path(path)}: {error}")

        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == "float":
                fail(
                    "Constitution Rule 3 forbids float in engine: "
                    f"{display_path(path)}:{node.lineno}"
                )
            if isinstance(node, ast.Constant) and isinstance(node.value, float):
                fail(
                    "Constitution Rule 3 forbids float literals in engine: "
                    f"{display_path(path)}:{node.lineno}"
                )


def check_frontend_hex_guard() -> None:
    hex_pattern = re.compile(r"#[0-9a-fA-F]{6}\b")
    source_extensions = {".css", ".js", ".jsx", ".scss", ".ts", ".tsx"}
    tokens_path = FRONTEND_DIR / "src" / "styles" / "tokens.css"

    for path in sorted((FRONTEND_DIR / "src").rglob("*")):
        if not path.is_file() or path.suffix not in source_extensions:
            continue
        if path == tokens_path:
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if hex_pattern.search(line):
                fail(
                    "Raw hexadecimal color is forbidden in frontend source: "
                    f"{display_path(path)}:{line_number}"
                )

    tokens = tokens_path.read_text(encoding="utf-8")
    expected_tokens = {
        "--theme-bg-canvas",
        "--theme-surface-panel",
        "--theme-surface-card",
        "--theme-surface-hover",
        "--theme-border-subtle",
        "--theme-text-primary",
        "--theme-text-secondary",
        "--theme-text-muted",
        "--theme-cyan-tool",
        "--theme-amber-opening",
        "--theme-emerald-action",
        "--theme-crimson-alert",
        "--theme-glass-tint",
    }
    for token in expected_tokens:
        if tokens.count(token) != 2:
            fail(f"ADOBE token must have exactly light/dark definitions: {token}")


def check_shot_04_contract() -> None:
    canonical_design = ROOT / "docs" / "PRD" / "PRD-DESIGN-SYSTEM-ADOBE.md"
    misplaced_design = ROOT / "docs" / "PRD-DESIGN-SYSTEM-ADOBE.md"
    if misplaced_design.exists():
        fail("ADOBE design system must have one authority under docs/PRD")
    if "LIGHT STUDIO / DARK GRAPHITE" not in canonical_design.read_text(encoding="utf-8"):
        fail("Canonical ADOBE design authority does not contain the dual theme")

    secret_pattern = re.compile(
        r"VITE_[A-Z0-9_]*(?:SERVICE_ROLE|JWT_SECRET|DATABASE_URL|PASSWORD|SECRET_KEY)"
    )
    secret_surfaces = [
        ROOT / ".env.example",
        ROOT / ".github" / "workflows" / "ci.yml",
        *sorted((FRONTEND_DIR / "src").rglob("*")),
    ]
    for path in secret_surfaces:
        if path.is_file() and secret_pattern.search(path.read_text(encoding="utf-8")):
            fail(f"Forbidden browser secret variable found: {display_path(path)}")

    package = json.loads((FRONTEND_DIR / "package.json").read_text(encoding="utf-8"))
    expected_packages = {
        "@supabase/supabase-js": "2.112.4",
        "react-router-dom": "7.18.3",
        "@tanstack/react-query": "5.102.8",
        "zustand": "5.0.15",
        "posthog-js": "1.422.5",
        "orval": "8.27.0",
        "@playwright/test": "1.62.1",
        "jsdom": "30.0.1",
        "otpauth": "9.5.1",
        "@types/react": "18.3.28",
        "@types/react-dom": "18.3.7",
    }
    declared = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    for name, version in expected_packages.items():
        if declared.get(name) != version:
            fail(f"SHOT-04 dependency must be exactly {name}@{version}")

    openapi = (BACKEND_DIR / "openapi.yaml").read_text(encoding="utf-8")
    for future_field in ("calculation_hash", "inspector"):
        if future_field in openapi:
            fail(f"SHOT-04 OpenAPI exposes future field: {future_field}")
    for endpoint in ("/api/v1/auth/me/", "/api/v1/engine/calculate/"):
        if endpoint not in openapi:
            fail(f"SHOT-04 OpenAPI endpoint is missing: {endpoint}")

    e2e = (FRONTEND_DIR / "tests" / "e2e" / "auth.spec.ts").read_text(
        encoding="utf-8"
    )
    for evidence in ("requireMailpitHealthy", "waitForMagicLink", "mfa_required", "OTPAuth.TOTP", "accessToken"):
        if evidence not in e2e:
            fail(f"Real Magic Link/TOTP E2E evidence is missing: {evidence}")
    mailpit = (FRONTEND_DIR / "tests" / "e2e" / "support" / "mailpit.ts").read_text(
        encoding="utf-8"
    )
    for evidence in ("/readyz", "/api/v1/messages", "/api/v1/message/", "excludedMessageIds", "deadline"):
        if evidence not in mailpit:
            fail(f"Mailpit fail-closed evidence is missing: {evidence}")
    if "/api/v1/mailbox/" in e2e + mailpit:
        fail("SHOT-04 E2E must use Mailpit rather than the historical Inbucket API")
    if re.search(r"\btest\.(?:skip|fixme)\s*\(", e2e):
        fail("Real auth E2E must not contain skipped tests")

    checker_source = Path(__file__).read_text(encoding="utf-8")
    forbidden_fail_open = "allow" + "_fail"
    if forbidden_fail_open in checker_source:
        fail("Mandatory gauntlet gates must not use fail-open placeholders")
    print("  SHOT-04 auth/API/design drift guards: passed", flush=True)


def check_shot_05_contract() -> None:
    openapi = (BACKEND_DIR / "openapi.yaml").read_text(encoding="utf-8")
    if "/api/v1/engine/systems/" not in openapi:
        fail("SHOT-05 OpenAPI system discovery endpoint is missing")

    generated = (FRONTEND_DIR / "src" / "api" / "generated" / "dekopen.ts").read_text(
        encoding="utf-8"
    )
    for evidence in ("engineSystems", "EngineSystemsResponse", "/api/v1/engine/systems/"):
        if evidence not in generated:
            fail(f"SHOT-05 generated discovery client evidence is missing: {evidence}")

    canvas_dir = FRONTEND_DIR / "src" / "features" / "canvas"
    production_paths = sorted(
        path
        for path in canvas_dir.rglob("*")
        if path.is_file()
        and path.suffix in {".ts", ".tsx", ".css"}
        and ".test." not in path.name
    )
    production = "\n".join(path.read_text(encoding="utf-8") for path in production_paths)
    for forbidden_output in ("1006.00", "970.00", "910.00", "919.00"):
        if forbidden_output in production:
            fail(
                "G1 engine output must not be hardcoded in canvas production source: "
                f"{forbidden_output}"
            )
    if "3067da09-3119-5ad0-a1d5-498cd2dfd753" in production:
        fail("DEMO_60 UUID must be discovered at runtime rather than hardcoded")
    for future_surface in ("calculation_hash", "inspector"):
        if future_surface in production.lower():
            fail(f"SHOT-05 canvas exposes future surface: {future_surface}")
    if "EngineCalculateResponse" in (
        canvas_dir / "canvasStore.ts"
    ).read_text(encoding="utf-8"):
        fail("Zustand must not duplicate the TanStack-owned engine response")

    snapping = (canvas_dir / "snapping.ts").read_text(encoding="utf-8")
    for evidence in ("SNAP_RADIUS_PX = 12n", "FIFTY_MM_CENTI", "TEN_MM_CENTI"):
        if evidence not in snapping:
            fail(f"SHOT-05 exact snapping evidence is missing: {evidence}")
    if "Math.round(" in snapping:
        fail("Math.round() must not define SHOT-05 HALF_UP snapping")

    app = (FRONTEND_DIR / "src" / "App.tsx").read_text(encoding="utf-8")
    dashboard = (FRONTEND_DIR / "src" / "app" / "DashboardPage.tsx").read_text(
        encoding="utf-8"
    )
    if "/projects/:id/positions/:posId/edit" not in app:
        fail("Canonical S06 editor route is missing")
    if "/projects/demo/positions/g1/edit" not in dashboard:
        fail("Dashboard demo bootstrap route is missing")
    messages = (FRONTEND_DIR / "src" / "i18n" / "es-CL.ts").read_text(encoding="utf-8")
    if '"canvas.openDemo": "Abrir Demo G1"' not in messages:
        fail("Dashboard demo action copy is missing")

    hook = (canvas_dir / "useEngineCalculation.ts").read_text(encoding="utf-8")
    editor = (canvas_dir / "CanvasEditor2DView.tsx").read_text(encoding="utf-8")
    for evidence in ("performance.now()", "fetchQuery", "acceptDimension"):
        if evidence not in hook:
            fail(f"SHOT-05 transactional timing evidence is missing: {evidence}")
    if "requestAnimationFrame" not in editor:
        fail("SHOT-05 timing must end on the first painted animation frame")

    sentinel = (canvas_dir / "canvasResults.test.tsx").read_text(encoding="utf-8")
    for value in ("1111.25", "1066.60", "876.54", "777.75"):
        if value not in sentinel:
            fail(f"Canvas anti-hardcode sentinel is missing: {value}")

    e2e = (FRONTEND_DIR / "tests" / "e2e" / "canvas.spec.ts").read_text(
        encoding="utf-8"
    )
    for evidence in (
        "waitForMagicLink",
        "engine/systems/",
        "data-last-commit-ms",
        "toBeLessThan(300)",
        '["1070", "1080", "1090", "1100", "1110"]',
        "snap-guide",
    ):
        if evidence not in e2e:
            fail(f"Real SHOT-05 E2E evidence is missing: {evidence}")
    if re.search(r"\btest\.(?:skip|fixme)\s*\(", e2e):
        fail("Real canvas E2E must not contain skipped tests")

    animations = (
        ROOT / "docs" / "PRD" / "PRD-ANIMATIONS-INTERACTIONS.md"
    ).read_text(encoding="utf-8")
    if "gate de snapping exclusivamente al redimensionar las cotas" not in animations:
        fail("ANIM must separate SHOT-05 outer snapping from future division snapping")
    print("  SHOT-05 canvas/discovery/performance drift guards: passed", flush=True)


def check_constitutional_guards() -> None:
    print("[1/6] Constitutional guards", flush=True)
    check_required_paths()
    check_required_database_paths()
    check_python_ast_guards()
    check_frontend_hex_guard()
    check_shot_04_contract()
    check_shot_05_contract()
    print("  Constitutional source guards: passed", flush=True)


def check_linters() -> None:
    print("[2/6] Linters and formatting", flush=True)
    run_command([PYTHON, "-m", "ruff", "check", "."])
    run_command(npm_command("run", "lint"), cwd=FRONTEND_DIR)
    run_command(npm_command("run", "format:check"), cwd=FRONTEND_DIR)
    run_command([PYTHON, "scripts/check_generated_api.py"])


def check_typechecks() -> None:
    print("[3/6] Strict type checks", flush=True)
    run_command([PYTHON, "-m", "mypy", "engine/"])
    run_command([PYTHON, "backend/manage.py", "check"])
    run_command(npm_command("run", "typecheck"), cwd=FRONTEND_DIR)


def load_g_case_manifest() -> dict[str, object]:
    manifest_path = ENGINE_DIR / "tests" / "GOLD_CASES_MANIFEST.json"
    if not manifest_path.is_file():
        fail(f"G-case manifest is missing: {display_path(manifest_path)}")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        fail(f"G-case manifest is invalid: {error}")

    if not isinstance(manifest, dict):
        fail("G-case manifest root must be an object")
    return manifest


def check_g_case_manifest() -> None:
    manifest = load_g_case_manifest()
    if "version" in manifest:
        fail("G-case manifest must not contain an ambiguous version field")
    if manifest.get("normative_source") != "docs/PRD/PLAN_SHOTS.md":
        fail("G-case manifest normative_source must be docs/PRD/PLAN_SHOTS.md")
    if manifest.get("tolerance_mm") != "0.00":
        fail("G-case manifest tolerance_mm must be the exact string '0.00'")

    cases = manifest.get("cases")
    if not isinstance(cases, dict) or set(cases) != EXPECTED_G_CASES:
        fail("G-case manifest must contain exactly G1-G12 and G-Pro1")

    actual_statuses: dict[str, object] = {}
    actual_target_shots: dict[str, object] = {}
    for case_id, case_contract in cases.items():
        if not isinstance(case_contract, dict):
            fail(f"G-case {case_id} contract must be an object")
        actual_statuses[case_id] = case_contract.get("status")
        actual_target_shots[case_id] = case_contract.get("target_shot")
        if case_contract.get("status") == "xfail":
            reason = case_contract.get("reason")
            if not isinstance(reason, str) or not reason.strip():
                fail(f"Deferred xfail G-case {case_id} must have a non-empty reason")
    if actual_statuses != EXPECTED_G_CASE_STATUSES:
        fail(
            "G-case manifest status mismatch; "
            f"expected={EXPECTED_G_CASE_STATUSES}, actual={actual_statuses}"
        )
    if actual_target_shots != EXPECTED_G_CASE_TARGET_SHOTS:
        fail(
            "G-case manifest target_shot mismatch; "
            f"expected={EXPECTED_G_CASE_TARGET_SHOTS}, actual={actual_target_shots}"
        )

    g3_contract = cases["G3"]
    if not isinstance(g3_contract, dict):
        fail("G-case G3 contract must be an object")
    if g3_contract.get("deferred_assertions") != EXPECTED_G3_DEFERRED_ASSERTIONS:
        fail(
            "G3 deferred assertions must declare hardware kit resolution for SHOT-06"
        )

    print(
        "  G-case manifest contract: statuses, targets, and deferred reasons passed",
        flush=True,
    )


def check_tests(env: Mapping[str, str]) -> None:
    print("[4/6] Test suites", flush=True)
    check_g_case_manifest()
    run_command([PYTHON, "-m", "pytest", "engine/", "-q", "-W", "error"], env=env)
    run_command([PYTHON, "-m", "pytest", "backend/", "-q", "-W", "error"], env=env)
    run_command(npm_command("run", "test"), cwd=FRONTEND_DIR)


def check_build() -> None:
    print("[5/6] Frontend production build", flush=True)
    run_command(npm_command("run", "build"), cwd=FRONTEND_DIR)


def sql_without_literals_or_comments(sql: str) -> str:
    without_literals = re.sub(r"'(?:''|[^'])*'", "''", sql, flags=re.DOTALL)
    return re.sub(r"--[^\n]*", "", without_literals)


def check_database_contract() -> None:
    print("[6/6] Database source contract", flush=True)
    check_required_database_paths()

    migration = SUPABASE_MIGRATION.read_text(encoding="utf-8")
    normalized_migration = " ".join(migration.lower().split())
    actual_tables = set(
        re.findall(r"CREATE TABLE public\.(\w+)\s*\(", migration, flags=re.IGNORECASE)
    )
    if actual_tables != EXPECTED_DATABASE_TABLES:
        missing = sorted(EXPECTED_DATABASE_TABLES - actual_tables)
        unexpected = sorted(actual_tables - EXPECTED_DATABASE_TABLES)
        fail(f"Database table contract mismatch; missing={missing}, unexpected={unexpected}")

    for table in sorted(EXPECTED_DATABASE_TABLES):
        rls_statement = f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY;"
        if rls_statement not in migration:
            fail(f"RLS is not enabled for required table: {table}")

    shot_03_migration = SUPABASE_SHOT_03_MIGRATION.read_text(encoding="utf-8")
    normalized_shot_03_migration = " ".join(shot_03_migration.lower().split())
    executable_sql = sql_without_literals_or_comments(
        migration + "\n" + shot_03_migration
    )
    forbidden_type = re.compile(
        r"\b(?:REAL|FLOAT\d*|DOUBLE\s+PRECISION)\b",
        flags=re.IGNORECASE,
    )
    match = forbidden_type.search(executable_sql)
    if match is not None:
        fail(f"Floating point SQL type is forbidden: {match.group(0)}")

    required_security_fragments = (
        "create schema if not exists private",
        "create or replace function private.current_user_org_ids()",
        "security definer set search_path = ''",
        "from public.tenancy_memberships as membership",
        "grant usage on schema private to authenticated",
        "revoke all on function private.current_user_org_ids() from public",
        "grant execute on function private.current_user_org_ids() to authenticated",
        "revoke all on public.payment_events from anon, authenticated",
    )
    for fragment in required_security_fragments:
        if fragment not in normalized_migration:
            fail(f"Required database security contract is missing: {fragment}")
    if "public.current_user_org_ids" in normalized_migration:
        fail("RLS policies must call private.current_user_org_ids() explicitly")

    required_shot_03_fragments = (
        "add column cut_add_mm numeric(6, 2)",
        "set cut_add_mm = 9.00",
        "profile_system.code = 'demo_60'",
        "alter column cut_add_mm set not null",
    )
    for fragment in required_shot_03_fragments:
        if fragment not in normalized_shot_03_migration:
            fail(f"Required SHOT-03 database contract is missing: {fragment}")
    if "cut_add_mm numeric(6, 2) not null default" in normalized_shot_03_migration:
        fail("glazing_bead_matrix.cut_add_mm must not invent a catalog default")

    seed = (SUPABASE_DIR / "seed.sql").read_text(encoding="utf-8")
    if "'DEMO_60'" not in seed or "is_global" not in seed or "TRUE" not in seed:
        fail("Canonical global DEMO_60 seed is missing")
    if "40.00" not in seed:
        fail("Canonical DEMO_60 central overlap 40.00 is missing")
    for fragment in ("75.00", "80.00", "15.00", "5.00", "cut_add_mm", "9.00"):
        if fragment not in seed:
            fail(f"Canonical DEMO_60 SHOT-03 seed value is missing: {fragment}")

    print("  DDL/RLS/seed source contract: passed", flush=True)


def check_live_gates(*, tests: bool, database: bool) -> None:
    check_database_contract()
    try:
        env = local_gates.start_clean_stack()
        if tests:
            check_tests(env)
            local_gates.run_auth_e2e(env)
        if database:
            supabase = local_gates.executable("supabase")
            local_gates.run([supabase, "db", "lint", "--level", "warning", "--fail-on", "warning"])
            local_gates.run([supabase, "test", "db"])
            if not tests:
                local_gates.run(
                    [PYTHON, "-m", "pytest", "backend/tests/integration/", "-q", "-W", "error"],
                    env=env,
                )
            local_gates.verify_postgres16()
    except (RuntimeError, ValueError) as error:
        fail(str(error))
    finally:
        local_gates.stop_stack()


def main() -> None:
    configure_output()
    target = sys.argv[1] if len(sys.argv) == 2 else "all"
    allowed_targets = {
        "lint",
        "typecheck",
        "test",
        "build",
        "database",
        "all",
        "gauntlet",
    }
    if len(sys.argv) > 2 or target not in allowed_targets:
        fail(
            "Usage: python scripts/check_dod.py "
            "[lint|typecheck|test|build|database|all|gauntlet]",
            2,
        )

    print("Dekopen SHOT-05 fail-closed checker", flush=True)

    if target == "database":
        check_live_gates(tests=False, database=True)
        print("[PASS] SHOT-05 live database gate completed with exit code 0", flush=True)
        return

    if target in {"lint", "all", "gauntlet"}:
        check_constitutional_guards()
        check_linters()
    if target in {"typecheck", "all", "gauntlet"}:
        check_typechecks()
    if target in {"test", "all", "gauntlet"}:
        check_live_gates(tests=True, database=target in {"all", "gauntlet"})
    if target in {"build", "all", "gauntlet"}:
        check_build()

    print(f"[PASS] SHOT-05 checker target '{target}' completed with exit code 0", flush=True)


if __name__ == "__main__":
    main()
