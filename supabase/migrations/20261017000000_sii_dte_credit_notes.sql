-- DTE-61: a nota de crédito electrónica is stamped from the same CAF pool
-- machinery (tipo_dte=61) and references the parent factura's folio in its
-- <Referencia> block. project_dtes gains a credit_note_id so the NC's sealed
-- artifact anchors to its counter-document; invoice_id still points at the
-- parent factura — the NC-DTE belongs to that invoice's documentary chain.
ALTER TABLE public.project_dtes
    ADD COLUMN credit_note_id UUID
        REFERENCES public.project_credit_notes(id) ON DELETE RESTRICT;

ALTER TABLE public.project_dtes
    ADD CONSTRAINT uk_org_dte_credit_note UNIQUE (org_id, credit_note_id);

CREATE INDEX idx_project_dtes_credit_note
    ON public.project_dtes (org_id, credit_note_id)
    WHERE credit_note_id IS NOT NULL;
