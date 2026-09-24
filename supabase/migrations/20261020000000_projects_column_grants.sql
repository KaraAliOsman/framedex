-- projects columns added after the shot-08 column-grant enumeration were never
-- granted to authenticated: reads of project rows (and anything running
-- project_public) failed with SQLSTATE 42501 on every correctly migrated DB.
-- Grant the five new columns; the privileged columns (cost/price fields) stay
-- ungranted by design.
GRANT SELECT (client_id, client_giro, client_comuna, client_address, pricing_reset_at)
    ON public.projects TO authenticated;
