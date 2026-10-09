-- Minimal Supabase role/auth contract for applying the canonical schema to PostgreSQL 16.

CREATE ROLE anon NOLOGIN;
CREATE ROLE authenticated NOLOGIN;
CREATE ROLE service_role NOLOGIN BYPASSRLS;

CREATE SCHEMA auth;

-- Supabase owns this table. The independent schema gate needs its key
-- contract so domain foreign keys are exercised rather than removed.
CREATE TABLE auth.users (id UUID PRIMARY KEY);

CREATE FUNCTION auth.uid()
RETURNS UUID
LANGUAGE SQL
STABLE
AS $$
    SELECT NULLIF(current_setting('request.jwt.claim.sub', TRUE), '')::UUID;
$$;

CREATE FUNCTION auth.jwt()
RETURNS JSONB
LANGUAGE SQL
STABLE
AS $$
    SELECT COALESCE(
        NULLIF(current_setting('request.jwt.claims', TRUE), '')::JSONB,
        '{}'::JSONB
    );
$$;
