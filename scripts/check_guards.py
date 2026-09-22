#!/usr/bin/env python3
"""Fast source guards protecting DEKOPEN's hard invariants.

Run via `make lint`. These are plain greps/regex checks — no orchestration.
The deeper proofs live in the test suites (engine purity tests, pgTAP).
"""

from __future__ import annotations

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
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"\bfloat\(", line):
                fail(f"float() in engine source: {path}:{lineno}")


def check_no_hex_in_frontend() -> None:
    """UI colors come from semantic tokens, not hardcoded hex.

    `styles/tokens.css` is the token definition file — hex lives there by design.
    """
    pattern = re.compile(r"#[0-9a-fA-F]{6}\b")
    for path in sorted(FRONTEND_SRC.rglob("*")):
        if path.suffix not in {".ts", ".tsx", ".css"} or ".test." in path.name:
            continue
        if path.name == "tokens.css":
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


def main() -> None:
    print("Source guards", flush=True)
    check_no_float_in_engine()
    check_no_hex_in_frontend()
    check_database_contract()
    if FAILURES:
        print(f"[FAIL] {len(FAILURES)} guard violation(s)", flush=True)
        sys.exit(1)
    print("[PASS] source guards", flush=True)


if __name__ == "__main__":
    main()
