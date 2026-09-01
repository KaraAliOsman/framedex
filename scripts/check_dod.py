#!/usr/bin/env python3
"""Cross-platform, fail-closed Definition of Done checker for Dekopen."""

from __future__ import annotations

import ast
from collections.abc import Sequence
import json
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

PYTHON = sys.executable
NPM = shutil.which("npm")

REQUIRED_PATHS = (
    ROOT / "pyproject.toml",
    ENGINE_DIR / "pyproject.toml",
    ENGINE_DIR / "src" / "dekopen_engine" / "__init__.py",
    ENGINE_DIR / "tests" / "test_package.py",
    BACKEND_DIR / "manage.py",
    BACKEND_DIR / "tests" / "test_bootstrap.py",
    FRONTEND_DIR / "package.json",
    FRONTEND_DIR / "package-lock.json",
    FRONTEND_DIR / "tsconfig.json",
    FRONTEND_DIR / "src" / "App.test.tsx",
)

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


def configure_output() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def fail(message: str, exit_code: int = 1) -> None:
    print(f"[FAIL] {message}", file=sys.stderr, flush=True)
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
    print("[1/5] Constitutional guards", flush=True)
    check_required_paths()
    check_python_ast_guards()
    check_frontend_hex_guard()
    print("  Constitutional source guards: passed", flush=True)


def check_linters() -> None:
    print("[2/5] Linters and formatting", flush=True)
    run_command([PYTHON, "-m", "ruff", "check", "."])
    run_command(npm_command("run", "lint"), cwd=FRONTEND_DIR)
    run_command(npm_command("run", "format:check"), cwd=FRONTEND_DIR)


def check_typechecks() -> None:
    print("[3/5] Strict type checks", flush=True)
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

    print("  G-case manifest contract: passed (calculation cases remain deferred)", flush=True)


def check_tests() -> None:
    print("[4/5] Test suites", flush=True)
    check_g_case_manifest()
    run_command([PYTHON, "-m", "pytest", "engine/", "-q"])
    run_command([PYTHON, "-m", "pytest", "backend/", "-q"])
    run_command(npm_command("run", "test"), cwd=FRONTEND_DIR)


def check_build() -> None:
    print("[5/5] Frontend production build", flush=True)
    run_command(npm_command("run", "build"), cwd=FRONTEND_DIR)


def main() -> None:
    configure_output()
    target = sys.argv[1] if len(sys.argv) == 2 else "all"
    allowed_targets = {"lint", "typecheck", "test", "build", "all", "gauntlet"}
    if len(sys.argv) > 2 or target not in allowed_targets:
        fail("Usage: python scripts/check_dod.py [lint|typecheck|test|build|all|gauntlet]", 2)

    print("Dekopen SHOT-01 fail-closed checker", flush=True)

    if target in {"lint", "all", "gauntlet"}:
        check_constitutional_guards()
        check_linters()
    if target in {"typecheck", "all", "gauntlet"}:
        check_typechecks()
    if target in {"test", "all", "gauntlet"}:
        check_tests()
    if target in {"build", "all", "gauntlet"}:
        check_build()

    print(f"[PASS] SHOT-01 checker target '{target}' completed with exit code 0", flush=True)


if __name__ == "__main__":
    main()
