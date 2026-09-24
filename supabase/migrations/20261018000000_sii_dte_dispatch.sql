-- SII DTE-52 (guía de despacho electrónica): DTEs that stamp a sealed
-- dispatch note. A guía DTE is its own documentary family — it never shares
-- an invoice or credit-note chain, so dispatch_note_id requires both to be
-- NULL. Replays resolve through UNIQUE (org_id, dispatch_note_id).

ALTER TABLE public.project_dtes
    ADD COLUMN dispatch_note_id UUID
        REFERENCES public.dispatch_notes(id) ON DELETE RESTRICT;

ALTER TABLE public.project_dtes
    ADD CONSTRAINT chk_dte_dispatch_family CHECK (
        dispatch_note_id IS NULL
        OR (invoice_id IS NULL AND credit_note_id IS NULL)
    );

ALTER TABLE public.project_dtes
    ADD CONSTRAINT uk_org_dispatch_note_dte UNIQUE (org_id, dispatch_note_id);

CREATE INDEX idx_project_dtes_dispatch_note
    ON public.project_dtes (dispatch_note_id) WHERE dispatch_note_id IS NOT NULL;

ALTER TABLE public.project_dtes
    ALTER COLUMN invoice_id DROP NOT NULL;

ALTER TABLE public.project_dtes
    ADD CONSTRAINT chk_dte_anchor CHECK (
        invoice_id IS NOT NULL
        OR credit_note_id IS NOT NULL
        OR dispatch_note_id IS NOT NULL
    );
