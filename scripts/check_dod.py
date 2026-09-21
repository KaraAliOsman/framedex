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
    ROOT / "scripts" / "check_core_mutations.py",
    ENGINE_DIR / "scripts" / "regenerate_golden.py",
    ENGINE_DIR / "tests" / "golden_example.json",
    ENGINE_DIR / "tests" / "test_shot06_core.py",
    ENGINE_DIR / "tests" / "test_hardware_weight.py",
    ENGINE_DIR / "tests" / "test_snapshot.py",
    ENGINE_DIR / "tests" / "test_pricing.py",
    ROOT / "docs" / "plans" / "PLAN_SHOT-06.md",
    ROOT / "docs" / "plans" / "PLAN_SHOT-07.md",
    ENGINE_DIR / "src" / "dekopen_engine" / "cutting.py",
    ENGINE_DIR / "src" / "dekopen_engine" / "inspection_models.py",
    ENGINE_DIR / "src" / "dekopen_engine" / "inspector.py",
    ENGINE_DIR / "src" / "dekopen_engine" / "technical_facts.py",
    ENGINE_DIR / "tests" / "test_cutting.py",
    ENGINE_DIR / "tests" / "test_inspector.py",
    BACKEND_DIR / "engine_api" / "cutting_repository.py",
    BACKEND_DIR / "engine_api" / "inspection_repository.py",
    BACKEND_DIR / "engine_api" / "derivative_serializers.py",
    BACKEND_DIR / "engine_api" / "derivative_views.py",
    BACKEND_DIR / "tests" / "test_engine_derivatives.py",
    BACKEND_DIR / "tests" / "integration" / "test_shot07_catalog.py",
    FRONTEND_DIR / "src" / "features" / "inspector" / "InspectorModal.tsx",
    FRONTEND_DIR / "src" / "features" / "inspector" / "InspectorModal.test.tsx",
    FRONTEND_DIR / "src" / "features" / "inspector" / "inspectorDraft.ts",
    ROOT / "docs" / "plans" / "PLAN_SHOT-09.md",
    ENGINE_DIR / "src" / "dekopen_engine" / "documentary_canonical.py",
    ENGINE_DIR / "src" / "dekopen_engine" / "manufacturing.py",
    ENGINE_DIR / "src" / "dekopen_engine" / "manufacturing_trace.py",
    ENGINE_DIR / "src" / "dekopen_engine" / "purchasing.py",
    ENGINE_DIR / "tests" / "test_documentary_canonical.py",
    ENGINE_DIR / "tests" / "test_manufacturing.py",
    ENGINE_DIR / "tests" / "test_purchasing.py",
    BACKEND_DIR / "documents" / "service.py",
    BACKEND_DIR / "documents" / "repository.py",
    BACKEND_DIR / "documents" / "views.py",
    BACKEND_DIR / "documents" / "artifacts.py",
    BACKEND_DIR / "documents" / "renderers.py",
    BACKEND_DIR / "documents" / "xlsx.py",
    BACKEND_DIR / "documents" / "storage.py",
    BACKEND_DIR / "documents" / "serializers.py",
    BACKEND_DIR / "documents" / "urls.py",
    BACKEND_DIR / "purchasing" / "service.py",
    BACKEND_DIR / "purchasing" / "views.py",
    BACKEND_DIR / "purchasing" / "urls.py",
    BACKEND_DIR / "purchasing" / "serializers.py",
    BACKEND_DIR / "tests" / "test_documents_contract.py",
    BACKEND_DIR / "tests" / "integration" / "test_shot09_documentary.py",
    FRONTEND_DIR / "src" / "features" / "purchasing" / "PurchasingPage.tsx",
    FRONTEND_DIR / "src" / "features" / "purchasing" / "PurchasingPage.test.tsx",
    FRONTEND_DIR / "src" / "features" / "purchasing" / "purchasing.css",
)

REQUIRED_DATABASE_PATHS = (
    SUPABASE_DIR / "config.toml",
    SUPABASE_MIGRATION,
    SUPABASE_SHOT_03_MIGRATION,
    SUPABASE_DIR / "migrations" / "20260905000000_shot_06_catalog_authorities.sql",
    SUPABASE_DIR / "migrations" / "20260905000100_shot_06_demo_catalog.sql",
    SUPABASE_TEST_DIR / "040_shot_06_catalog.test.sql",
    SUPABASE_DIR / "migrations" / "20260906000000_shot_07_authorities.sql",
    SUPABASE_DIR / "migrations" / "20260906000100_shot_07_demo_catalog.sql",
    SUPABASE_TEST_DIR / "050_shot_07_catalog.test.sql",
    SUPABASE_DIR / "seed.sql",
    SUPABASE_TEST_DIR / "000_schema.test.sql",
    SUPABASE_TEST_DIR / "010_rls_isolation.test.sql",
    SUPABASE_TEST_DIR / "020_global_catalog.test.sql",
    SUPABASE_TEST_DIR / "030_billing_idempotency.test.sql",
    SUPABASE_DIR / "compat" / "postgres16_bootstrap.sql",
    SUPABASE_DIR / "compat" / "postgres16_verify.sql",
    ROOT / "scripts" / "check_migration_upgrades.py",
    ROOT / "scripts" / "check_shot09_upgrade.py",
    BACKEND_DIR / "tests" / "test_database_contract.py",
    SUPABASE_DIR / "migrations" / "20260914000000_shot_09_documentary.sql",
    SUPABASE_DIR / "migrations" / "20260914000100_shot_09_demo_authorities.sql",
    SUPABASE_TEST_DIR / "070_shot_09_documentary.test.sql",
)

EXPECTED_DATABASE_TABLES = {
    "credit_lot_movements",
    "billing_periods",
    "billing_lifecycle_events",
    "flow_lifecycle_operations",
    "credit_lots",
    "billing_orders",
    "billing_credit_grants",
    "flow_subscription_intents",
    "flow_customer_operations",
    "pricing_configurations",
    "pricing_matrix_cells",
    "pricing_fx_snapshots",
    "pricing_operations",
    "profile_purchase_mappings",
    "reinforcement_articles",
    "cutting_profiles",
    "inspector_rule_configs",
    "tenancy_organizations",
    "tenancy_memberships",
    "profile_systems",
    "profile_articles",
    "glazing_bead_matrix",
    "hardware_kits",
    "infill_articles",
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
    "manufacturing_placement_policies",
    "handle_requirement_policies",
    "reinforcement_cut_policies",
    "glass_purchase_mappings",
    "hardware_purchase_mappings",
    "panel_purchase_authorities",
    "project_documentary_inputs",
    "position_documentary_inputs",
    "purchase_projections",
    "purchase_requirement_lines",
    "supplier_eligibility_versions",
    "purchase_allocations",
    "order_allocation_batches",
    "order_requirement_lines",
    "document_artifacts",
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
    "G5": "pass",
    "G6": "pass",
    "G7": "pass",
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

EXPECTED_G3_RESOLVED_ASSERTIONS = {
    "hardware_kit_resolution": {"status": "pass", "resolved_in": "SHOT-06"}
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
            f"::error title=Dekopen gate::{annotation}",
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
    for endpoint in ("/api/v1/engine/inspect/", "/api/v1/engine/optimize-cut/"):
        if endpoint not in openapi:
            fail(f"SHOT-07 derivative endpoint is missing: {endpoint}")
    if "calculation_hash" not in openapi:
        fail("SHOT-06 OpenAPI must include calculation_hash")
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
    store_source = (canvas_dir / "canvasStore.ts").read_text(encoding="utf-8")
    for remote_result in ("EngineCalculateResponse", "EngineInspectResponse", "EngineOptimizeResponse"):
        if remote_result in store_source:
            fail("Zustand must not duplicate TanStack-owned engine responses")

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


def check_shot_09_contract() -> None:
    plan_path = ROOT / "docs" / "plans" / "PLAN_SHOT-09.md"
    plan = plan_path.read_text(encoding="utf-8")
    for decision in (
        "PD-09-01",
        "PD-09-05",
        "PD-09-10",
        "PD-09-15",
        "PD-09-19",
    ):
        if decision not in plan:
            fail(f"SHOT-09 plan is missing decision record: {decision}")
    if re.search(
        r"^\s*(?:#+\s*|[-*]\s*|>\s*)?\[PENDIENTE-DECISIÓN\]", plan, flags=re.MULTILINE
    ):
        fail("SHOT-09 plan must not keep an unresolved material decision")

    canonical = (
        ENGINE_DIR / "src" / "dekopen_engine" / "documentary_canonical.py"
    ).read_text(encoding="utf-8")
    for evidence in (
        "DOCUMENTARY_CANONICAL_V1",
        "def bom_hash_v1(",
        "def snapshot_sha256_v1(",
        "def file_sha256(",
    ):
        if evidence not in canonical:
            fail(f"SHOT-09 documentary canonicalization evidence is missing: {evidence}")

    purchasing_source = (
        ENGINE_DIR / "src" / "dekopen_engine" / "purchasing.py"
    ).read_text(encoding="utf-8")
    for evidence in ("PhysicalStockBindingV1", "AccessoryScheduleV1", "SupplierOrderType"):
        if evidence not in purchasing_source:
            fail(f"SHOT-09 purchase projection evidence is missing: {evidence}")

    openapi = (BACKEND_DIR / "openapi.yaml").read_text(encoding="utf-8")
    for endpoint in (
        "/api/v1/documents/projects/{project_id}/freeze/",
        "/api/v1/documents/projects/{project_id}/inputs/",
        "/api/v1/documents/artifacts/",
        "/api/v1/documents/artifacts/{artifact_id}/access/",
        "/api/v1/purchasing/versions/",
        "/api/v1/purchasing/versions/{version_id}/",
        "/api/v1/purchasing/versions/{version_id}/eligibilities/",
        "/api/v1/purchasing/versions/{version_id}/confirm/",
        "/api/v1/purchasing/requirements/{requirement_id}/allocation/",
        "/api/v1/purchasing/orders/{order_id}/send/",
    ):
        if endpoint not in openapi:
            fail(f"SHOT-09 OpenAPI endpoint is missing: {endpoint}")

    generated = (FRONTEND_DIR / "src" / "api" / "generated" / "dekopen.ts").read_text(
        encoding="utf-8"
    )
    for evidence in (
        "purchasingVersionState",
        "purchasingConfirmOrderType",
        "purchasingAllocateRequirement",
        "purchasingCreateEligibility",
        "purchasingSendOrder",
        "documentaryGenerateArtifact",
        "documentaryArtifactAccess",
        "documentaryFreezeRevisionA",
        "documentarySaveInputs",
    ):
        if evidence not in generated:
            fail(f"SHOT-09 generated client evidence is missing: {evidence}")

    app = (FRONTEND_DIR / "src" / "App.tsx").read_text(encoding="utf-8")
    if '"/purchasing"' not in app:
        fail("Canonical S19 purchasing route is missing")
    shell = (FRONTEND_DIR / "src" / "app" / "AppShell.tsx").read_text(encoding="utf-8")
    if '"/purchasing"' not in shell or "WORKSHOP_MANAGER" not in shell:
        fail("S19 navigation must preserve WORKSHOP_MANAGER operational access")

    messages = (FRONTEND_DIR / "src" / "i18n" / "es-CL.ts").read_text(encoding="utf-8")
    for key in (
        '"purchasing.title"',
        '"purchasing.confirmCheckbox"',
        '"purchasing.sendCheckbox"',
        '"purchasing.immutable"',
        '"purchasing.doc07"',
    ):
        if key not in messages:
            fail(f"S19 i18n key is missing: {key}")

    page = (
        FRONTEND_DIR / "src" / "features" / "purchasing" / "PurchasingPage.tsx"
    ).read_text(encoding="utf-8")
    if 'name="quantity"' in page or re.search(r'input[^>]*quantity', page):
        fail("S19 must not expose editable requirement quantities")
    for evidence in ("SUPPLIER_GLASS_PO", "confirmCheckbox", "sendCheckbox", "trace"):
        if evidence not in page:
            fail(f"S19 UI evidence is missing: {evidence}")

    migration = (
        SUPABASE_DIR / "migrations" / "20260914000000_shot_09_documentary.sql"
    ).read_text(encoding="utf-8")
    normalized = " ".join(migration.lower().split())
    for fragment in (
        "documentary_backend nologin nosuperuser nobypassrls",
        "applied_pricing_authority_required",
        "sealed_pricing_operation_immutable",
        "sealed_documentary_inputs_immutable",
        "documentary_evidence_immutable",
        "documentary_position_update_forbidden",
        "shot09_project_version_operation unique (pricing_operation_id)",
        "grant update (location_tag, updated_at) on public.project_positions to documentary_backend",
        "for update to documentary_backend",
        "unique nulls not distinct (system_id, org_id, version)",
        "authority_version in ('pre_shot09', 'shot09_v1')",
        "update public.project_versions set authority_version = 'pre_shot09'",
        "legacy_version_insert_forbidden",
    ):
        if fragment not in normalized:
            fail(f"SHOT-09 database contract fragment is missing: {fragment}")
    if "empty pre-authority project_versions" in normalized:
        fail("SHOT-09 migration must support populated pre-authority project_versions")
    if re.search(r"grant\s+(?:all|insert|update|delete)[^;]*document_artifacts\s+to\s+authenticated", normalized):
        fail("document_artifacts must not grant member writes")

    pgtap = (SUPABASE_TEST_DIR / "070_shot_09_documentary.test.sql").read_text(
        encoding="utf-8"
    )
    for evidence in (
        "applied_pricing_authority_required",
        "documentary_evidence_immutable",
        "documentary_backend",
        "document_artifacts",
        "purchase_requirement_lines",
        "legacy_version_insert_forbidden",
        "authority_version",
    ):
        if evidence not in pgtap:
            fail(f"SHOT-09 pgTAP evidence is missing: {evidence}")

    print("  SHOT-09 documentary/purchasing/S19 drift guards: passed", flush=True)


def check_constitutional_guards() -> None:
    print("[1/6] Constitutional guards", flush=True)
    check_required_paths()
    check_required_database_paths()
    check_python_ast_guards()
    check_frontend_hex_guard()
    check_shot_04_contract()
    check_shot_05_contract()
    check_shot_09_contract()
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
    if g3_contract.get("resolved_assertions") != EXPECTED_G3_RESOLVED_ASSERTIONS or "deferred_assertions" in g3_contract:
        fail(
            "G3 must declare hardware kit resolution completed in SHOT-06"
        )

    print(
        "  G-case manifest contract: statuses, targets, and deferred reasons passed",
        flush=True,
    )


def check_tests(env: Mapping[str, str]) -> None:
    print("[4/6] Test suites", flush=True)
    check_g_case_manifest()
    run_command(
        [
            PYTHON,
            "-m",
            "unittest",
            "discover",
            "-s",
            "scripts/tests",
            "-p",
            "test_*.py",
            "-v",
        ],
        env=env,
    )
    run_command([PYTHON, "-m", "engine.scripts.regenerate_golden", "--check"], env=env)
    run_command([PYTHON, "scripts/check_core_mutations.py"], env=env)
    run_command(
        [
            PYTHON, "-m", "pytest", "engine/", "-q", "-W", "error",
            "-W", "ignore:'asyncio.iscoroutinefunction' is deprecated:DeprecationWarning",
        ],
        env=env,
    )
    run_command(
        [
            PYTHON, "-m", "pytest", "backend/", "-q", "-W", "error",
            "-W", "ignore:'asyncio.iscoroutinefunction' is deprecated:DeprecationWarning",
        ],
        env=env,
    )
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

    migration = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((SUPABASE_DIR / "migrations").glob("*.sql"))
    )
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
                    [
                        PYTHON, "-m", "pytest", "backend/tests/integration/", "-q", "-W", "error",
                        "-W", "ignore:'asyncio.iscoroutinefunction' is deprecated:DeprecationWarning",
                    ],
                    env=env,
                )
            local_gates.verify_postgres16()
    except (RuntimeError, ValueError) as error:
        fail(str(error))
    finally:
        local_gates.stop_stack()


def main(argv: list[str] | None = None) -> None:
    configure_output()
    arguments = sys.argv[1:] if argv is None else argv
    requested_target = arguments[0] if len(arguments) == 1 else "all"
    allowed_targets = {
        "lint",
        "typecheck",
        "test",
        "build",
        "database",
        "all",
        "gauntlet",
    }
    if len(arguments) > 1 or requested_target not in allowed_targets:
        fail(
            "Usage: python scripts/check_dod.py "
            "[lint|typecheck|test|build|database|all|gauntlet]",
            2,
        )

    target = "all" if requested_target == "gauntlet" else requested_target
    print("Dekopen canonical repository fail-closed checker", flush=True)
    if requested_target == "gauntlet":
        print(
            "[COMPAT] Target 'gauntlet' is an alias for 'all'; it produces the same "
            "evidence. Do not run both.",
            flush=True,
        )

    if target == "database":
        check_live_gates(tests=False, database=True)
        print("[PASS] Repository live database gate completed with exit code 0", flush=True)
        return

    if target in {"lint", "all"}:
        check_constitutional_guards()
        check_linters()
    if target in {"typecheck", "all"}:
        check_typechecks()
    if target in {"test", "all"}:
        check_live_gates(tests=True, database=target == "all")
    if target in {"build", "all"}:
        check_build()

    print(f"[PASS] Repository checker target '{target}' completed with exit code 0", flush=True)


if __name__ == "__main__":
    main()
