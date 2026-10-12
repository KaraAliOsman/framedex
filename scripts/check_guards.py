#!/usr/bin/env python3
"""Fast source guards protecting DEKOPEN's hard invariants.

Run via `make lint`. These are plain greps/regex checks — no orchestration.
The deeper proofs live in the test suites (engine purity tests, pgTAP).
"""

from __future__ import annotations

import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
ENGINE_SRC = ROOT / "engine" / "src"
FRONTEND_SRC = ROOT / "frontend" / "src"
SUPABASE_DIR = ROOT / "supabase"

FAILURES: list[str] = []


def fail(message: str) -> None:
    FAILURES.append(message)
    print(f"  FAIL {message}", flush=True)


def check_no_float_in_engine() -> None:
    """Engine math is Decimal-only; a float literal or call breaks determinism."""
    for path in sorted(ENGINE_SRC.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(source.splitlines(), 1):
            if re.search(r"\bfloat\(", line):
                fail(f"float() in engine source: {path}:{lineno}")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError:
            continue  # syntax errors are reported by the compile/lint tooling
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, float):
                fail(f"float literal in engine source: {path}:{node.lineno}")


def check_no_hex_in_frontend() -> None:
    """UI colors come from semantic tokens, not hardcoded hex.

    `styles/tokens.css` is the token definition file — hex lives there by design.
    """
    pattern = re.compile(r"#[0-9a-fA-F]{6}\b")
    for path in sorted(FRONTEND_SRC.rglob("*")):
        if path.suffix not in {".ts", ".tsx", ".css"} or ".test." in path.name:
            continue
        if path.name == "tokens.css" or "dev" in path.parts:
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "0x" in line or "var(" in line:
                continue
            if pattern.search(line):
                fail(f"hardcoded hex color in frontend: {path}:{lineno}")


def check_database_contract() -> None:
    """Every tenant table keeps RLS; money/dimensions never use float SQL types."""
    migrations = sorted((SUPABASE_DIR / "migrations").glob("*.sql"))
    if not migrations:
        fail("no supabase migrations found")
        return
    migration = "\n".join(p.read_text(encoding="utf-8") for p in migrations)
    normalized = " ".join(migration.lower().split())

    tables = set(
        re.findall(r"CREATE TABLE public\.(\w+)\s*\(", migration, flags=re.IGNORECASE)
    )
    if not tables:
        fail("no public.* tables found in migrations")
    for table in sorted(tables):
        rls = f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY;"
        if rls not in migration:
            fail(f"RLS is not enabled for table: {table}")

    without_literals = re.sub(r"'(?:''|[^'])*'", "''", migration, flags=re.DOTALL)
    executable_sql = re.sub(r"--[^\n]*", "", without_literals)
    match = re.search(r"\b(?:REAL|FLOAT\d*|DOUBLE\s+PRECISION)\b", executable_sql, re.IGNORECASE)
    if match is not None:
        fail(f"floating point SQL type is forbidden: {match.group(0)}")

    for fragment in (
        "create or replace function private.current_user_org_ids()",
        "security definer set search_path = ''",
        "grant execute on function private.current_user_org_ids() to authenticated",
        "revoke all on public.payment_events from anon, authenticated",
    ):
        if fragment not in normalized:
            fail(f"required database security contract is missing: {fragment}")
    if "public.current_user_org_ids" in normalized:
        fail("RLS policies must call private.current_user_org_ids() explicitly")

    seed_path = SUPABASE_DIR / "seed.sql"
    if not seed_path.is_file() or "'DEMO_60'" not in seed_path.read_text(encoding="utf-8"):
        fail("canonical global DEMO_60 seed is missing")


# Heuristic for raw enum render: x.status/state/role/opening_type in JSX.
# A map lookup or domainLabel call is deliberately outside that pattern.
# Ratchets identify path + rule + normalized offending fragment; line moves
# cannot hide a violation, and duplicating an old fragment increases its count.
DESIGN_PATTERNS = {
    "inline-color": r"#[0-9a-fA-F]{3,8}\b|\brgba?\(",
    "gradient": r"(?:linear|radial|conic)-gradient\(",
    "blur": r"backdrop-filter\s*:|filter\s*:\s*blur\(",
    "heavy-weight": r"font-weight\s*:\s*(?:700|bold)\b|fontWeight\s*:\s*(?:700|[\"']bold[\"'])",
    "literal-font-size": r"font-size\s*:\s*[\d.]+px\b|fontSize\s*:\s*(?:\d+|[\"'][\d.]+px[\"'])",
    "literal-layer": r"z-index\s*:\s*\d+\b|zIndex\s*:\s*\d+\b",
    "display-tofixed": r"\.toFixed\(",
    "native-pattern": r"\bpattern\s*=",
    "unvalidated-form": r"<form\b(?![^>]*\bnoValidate\b)[^>]*>",
    "raw-enum-render": r"\{\s*[\w.]+\.(?:status|state|role|opening_type)\s*\}",
}
ENGLISH_COPY = re.compile(
    r"\b(?:Dashboard|Settings|Save|Delete|Loading|Submit|Cancel|Edit|Create|Next|Previous|Coming soon|Success|Something went wrong)\b",
    re.IGNORECASE,
)


def design_violations(path: str, source: str) -> Counter[str]:
    findings: Counter[str] = Counter()

    def record(rule: str, fragment: str) -> None:
        normalized = " ".join(fragment.split())
        digest = hashlib.sha256(normalized.encode()).hexdigest()[:16]
        findings[f"{path}|{rule}|{digest}|{normalized}"] += 1

    for rule, pattern in DESIGN_PATTERNS.items():
        for match in re.finditer(pattern, source):
            record(rule, match.group())
    for match in re.finditer(r"border-radius\s*:\s*([^;}]+)|borderRadius\s*:\s*([^,}\n]+)", source):
        value = (match[1] or match[2]).strip()
        if "var(" in value:
            continue
        dimensions = re.findall(r"([\d.]+)(px|rem|%)?", value)
        if any(float(amount) * (16 if unit == "rem" else 1) > 4 or unit == "%" for amount, unit in dimensions):
            record("radius-over-4", match.group())
    for match in re.finditer(r"box-shadow\s*:\s*([^;}]+)|boxShadow\s*:\s*([^,}\n]+)", source):
        value = (match[1] or match[2]).strip()
        if value != "none" and not re.fullmatch(r"var\(--(?:e[123]|sheet)\)", value):
            record("shadow-outside-scale", match.group())
    for match in re.finditer(r"(?:transition|animation)(?:-duration)?\s*:\s*([^;}]+)", source):
        for amount, unit in re.findall(r"([\d.]+)(ms|s)\b", match[1]):
            if float(amount) * (1000 if unit == "s" else 1) > 280:
                record("motion-over-280", match.group())
                break
    if path.endswith((".ts", ".tsx")):
        visible = []
        if "/i18n/" in f"/{path}":
            visible.extend(match[1] for match in re.finditer(r':\s*"([^"\n]+)"', source))
        visible.extend(match[1] for match in re.finditer(r'(?:label|title|placeholder|message|body|text|aria-label)\s*=\s*"([^"\n]+)"', source))
        visible.extend(match[1] for match in re.finditer(r'>\s*([^<>{}\n]+)\s*<', source))
        visible.extend(match[1] for match in re.finditer(r'(?:notify|setMessage|setError)\(\s*"([^"\n]+)"', source))
        for text in visible:
            if re.search(r"[\U0001F300-\U0001FAFF]", text):
                record("emoji-copy", text)
            if "!" in text or "¡" in text:
                record("exclamation-copy", text)
            if ENGLISH_COPY.search(text):
                record("english-copy", text)
    return findings


def current_design_violations() -> Counter[str]:
    findings: Counter[str] = Counter()
    for path in sorted(FRONTEND_SRC.rglob("*")):
        if path.suffix not in {".ts", ".tsx", ".css"} or ".test." in path.name:
            continue
        if path.name == "tokens.css" or "dev" in path.parts or "generated" in path.parts:
            continue
        findings.update(design_violations(path.relative_to(ROOT).as_posix(), path.read_text(encoding="utf-8")))
    return findings


def check_design_ratchet() -> None:
    path = ROOT / "scripts/design_guard_baseline.json"
    baseline = json.loads(path.read_text(encoding="utf-8"))
    current = current_design_violations()
    for key, count in (current - Counter(baseline["violations"])).items():
        fail(f"new design violation ({count}): {key}")
    # Self-tests run with make lint so a broken detector cannot silently pass.
    from test_design_guards import run_detector_tests
    run_detector_tests()


def main() -> None:
    print("Source guards", flush=True)
    check_no_float_in_engine()
    check_no_hex_in_frontend()
    check_database_contract()
    check_design_ratchet()
    if FAILURES:
        print(f"[FAIL] {len(FAILURES)} guard violation(s)", flush=True)
        sys.exit(1)
    print("[PASS] source guards", flush=True)


if __name__ == "__main__":
    main()
