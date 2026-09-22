#!/usr/bin/env python3
"""Live database gate: clean Supabase stack → pgTAP + RLS integration + lint.

Requires Docker and the Supabase CLI. Run via `make test-db`.
"""

from __future__ import annotations

import subprocess
import sys

import local_gates

PYTHON = sys.executable


def main() -> None:
    env = local_gates.start_clean_stack()
    try:
        supabase = local_gates.executable("supabase")
        local_gates.run([supabase, "db", "lint", "--level", "warning", "--fail-on", "warning"])
        local_gates.run([supabase, "test", "db"])
        local_gates.run(
            [
                PYTHON,
                "-m",
                "pytest",
                "backend/tests/integration/",
                "-q",
                "-W",
                "error",
                "-W",
                "ignore:'asyncio.iscoroutinefunction' is deprecated:DeprecationWarning",
            ],
            env=env,
        )
        local_gates.run_auth_e2e(env)
        local_gates.verify_postgres16()
    except (RuntimeError, ValueError, subprocess.CalledProcessError) as error:
        print(f"[FAIL] database gate: {error}", flush=True)
        sys.exit(1)
    finally:
        local_gates.stop_stack()
    print("[PASS] database gate", flush=True)


if __name__ == "__main__":
    main()
