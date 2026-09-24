-- SII DTE-33 required-field carrier columns.
-- A schema-valid factura needs the emisor's activity code (Acteco) and the
-- receptor's trade, commune and legal address. The CAF pool row carries the
-- emisor's Acteco alongside its other identity fields; projects and the
-- client registry carry the receptor fields so the freeze snapshot — and
-- therefore the sealed invoice payload — can freeze them.

ALTER TABLE public.projects
    ADD COLUMN client_giro VARCHAR(80),
    ADD COLUMN client_comuna VARCHAR(60),
    ADD COLUMN client_address TEXT;

ALTER TABLE public.clients
    ADD COLUMN giro VARCHAR(80),
    ADD COLUMN comuna VARCHAR(60);

ALTER TABLE public.sii_cafs
    ADD COLUMN acteco INTEGER;
