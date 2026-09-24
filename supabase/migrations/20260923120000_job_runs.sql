-- Durable tenant job queue (platform track).
-- Jobs are claimed by backend workers via FOR UPDATE SKIP LOCKED; every row is
-- owned by one org and only readable through the Django API as the service
-- role. Authenticated users never touch this table directly.

CREATE TABLE public.job_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL
        REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'QUEUED'
        CHECK (state IN ('QUEUED', 'RUNNING', 'SUCCEEDED', 'FAILED', 'CANCELED')),
    progress NUMERIC(5, 2) NOT NULL DEFAULT 0.00
        CHECK (progress >= 0.00 AND progress <= 100.00),
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    result JSONB,
    error JSONB,
    attempt INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3 CHECK (max_attempts >= 1),
    run_after TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    locked_by TEXT,
    locked_at TIMESTAMPTZ,
    idempotency_key TEXT,
    created_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- At most one live job per (org, type, idempotency_key): reusing a key returns
-- the existing row instead of duplicating expensive work.
CREATE UNIQUE INDEX uk_org_job_idempotency
    ON public.job_runs (org_id, type, idempotency_key)
    WHERE idempotency_key IS NOT NULL;

CREATE INDEX job_runs_claim_idx
    ON public.job_runs (run_after)
    WHERE state = 'QUEUED';

CREATE INDEX job_runs_org_recent_idx
    ON public.job_runs (org_id, created_at DESC);

ALTER TABLE public.job_runs ENABLE ROW LEVEL SECURITY;

-- Workers claim rows inside org-explicit transactions as the table owner; the
-- service_role policy exists so Supabase-side tooling sees consistent access.
CREATE POLICY job_runs_service_role
    ON public.job_runs
    FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role')
    WITH CHECK (auth.jwt() ->> 'role' = 'service_role');

REVOKE ALL ON public.job_runs FROM anon, authenticated;
GRANT SELECT, INSERT, UPDATE ON public.job_runs TO service_role;
