"""Run real Magic Link/MFA against the already-running local Supabase stack."""

from local_gates import run_auth_e2e, running_environment

if __name__ == "__main__":
    run_auth_e2e(running_environment())
