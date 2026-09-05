"""Run real Magic Link/MFA against the already-running local Supabase stack."""

import sys

from local_gates import run_auth_e2e, running_environment


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


if __name__ == "__main__":
    run_auth_e2e(running_environment())
