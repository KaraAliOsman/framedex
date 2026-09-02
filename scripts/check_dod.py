#!/usr/bin/env python3
"""Cross-platform, fail-closed Definition of Done checker for Dekopen."""

from __future__ import annotations

import ast
from collections.abc import Sequence
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

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
    FRONTEND_DIR / "package.json",
    FRONTEND_DIR / "package-lock.json",
    FRONTEND_DIR / "tsconfig.json",
    FRONTEND_DIR / "src" / "App.test.tsx",
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
            f"::error title=Dekopen SHOT-03 gate::{annotation}",
            file=sys.stderr,
            flush=True,
        )
    raise SystemExit(exit_code)


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix() or "."
    except ValueError:
        return str(path)


def run_command(command: Sequence[str], *, cwd: Path = ROOT) -> None:
    rendered = shlex.join(command)
    print(f"  [{display_path(cwd)}] $ {rendered}", flush=True)

    try:
        result = subprocess.run(command, cwd=cwd, check=False)
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

    for path in sorted((FRONTEND_DIR / "src").rglob("*")):
        if not path.is_file() or path.suffix not in source_extensions:
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if hex_pattern.search(line):
                fail(
                    "Raw hexadecimal color is forbidden in frontend source: "
                    f"{display_path(path)}:{line_number}"
                )


def check_constitutional_guards() -> None:
    print("[1/6] Constitutional guards", flush=True)
    check_required_paths()
    check_required_database_paths()
    check_python_ast_guards()
    check_frontend_hex_guard()
    print("  Constitutional source guards: passed", flush=True)


def check_linters() -> None:
    print("[2/6] Linters and formatting", flush=True)
    run_command([PYTHON, "-m", "ruff", "check", "."])
    run_command(npm_command("run", "lint"), cwd=FRONTEND_DIR)
    run_command(npm_command("run", "format:check"), cwd=FRONTEND_DIR)


def check_typechecks() -> None:
    print("[3/6] Strict type checks", flush=True)
    run_command([PYTHON, "-m", "mypy", "engine/"])
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
    if manifest.get("tolerance_mm") != "0.00":
        fail("G-case manifest tolerance_mm must be the exact string '0.00'")

    cases = manifest.get("cases")
    if not isinstance(cases, dict) or set(cases) != EXPECTED_G_CASES:
        fail("G-case manifest must contain exactly G1-G12 and G-Pro1")

    actual_statuses: dict[str, object] = {}
    for case_id, case_contract in cases.items():
        if not isinstance(case_contract, dict):
            fail(f"G-case {case_id} contract must be an object")
        actual_statuses[case_id] = case_contract.get("status")
    if actual_statuses != EXPECTED_G_CASE_STATUSES:
        fail(
            "G-case manifest status mismatch; "
            f"expected={EXPECTED_G_CASE_STATUSES}, actual={actual_statuses}"
        )

    print(
        "  G-case manifest contract: G1-G4 pass; G8/G9/G11/G12 xfail",
        flush=True,
    )


def check_tests() -> None:
    print("[4/6] Test suites", flush=True)
    check_g_case_manifest()
    run_command([PYTHON, "-m", "pytest", "engine/", "-q"])
    run_command([PYTHON, "-m", "pytest", "backend/", "-q"])
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


def stop_local_supabase() -> None:
    if SUPABASE is None:
        return
    command = [SUPABASE, "stop", "--no-backup"]
    rendered = shlex.join(command)
    print(f"  [{display_path(ROOT)}] $ {rendered}", flush=True)
    result = subprocess.run(command, cwd=ROOT, check=False)
    if result.returncode != 0 and sys.exc_info()[0] is None:
        fail(f"Command exited with code {result.returncode}: {rendered}", result.returncode)


def run_database_command(command: Sequence[str]) -> None:
    rendered = shlex.join(command)
    print(f"  [{display_path(ROOT)}] $ {rendered}", flush=True)

    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        fail(f"Required executable is missing: {command[0]}", 127)

    output = result.stdout.rstrip()
    if output:
        print(output, flush=True)
    if result.returncode != 0:
        output_tail = "\n".join(output.splitlines()[-40:])
        fail(
            f"Command exited with code {result.returncode}: {rendered}\n"
            f"Output tail:\n{output_tail}",
            result.returncode,
        )


def check_live_database() -> None:
    if SUPABASE is None:
        fail("Required executable is missing: supabase", 127)

    check_database_contract()
    try:
        run_database_command([SUPABASE, "--version"])
        run_database_command([SUPABASE, "start"])
        run_database_command([SUPABASE, "db", "reset"])
        run_database_command([SUPABASE, "db", "lint", "--level", "warning"])
        run_database_command([SUPABASE, "test", "db"])
    finally:
        stop_local_supabase()


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

    print("Dekopen SHOT-03 fail-closed checker", flush=True)

    if target == "database":
        check_live_database()
        print("[PASS] SHOT-03 live database gate completed with exit code 0", flush=True)
        return

    if target in {"lint", "all", "gauntlet"}:
        check_constitutional_guards()
        check_linters()
    if target in {"typecheck", "all", "gauntlet"}:
        check_typechecks()
    if target in {"test", "all", "gauntlet"}:
        check_tests()
    if target in {"build", "all", "gauntlet"}:
        check_build()
    if target in {"all", "gauntlet"}:
        check_database_contract()

    print(f"[PASS] SHOT-03 checker target '{target}' completed with exit code 0", flush=True)


if __name__ == "__main__":
    main()
