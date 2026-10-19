-- Dirección final 04: technical drawing composition of DOC-03 (one sheet per
-- position, same sealed revision data). Each composition stays its own
-- immutable artifact; issued artifacts are untouched.
BEGIN;
ALTER TABLE public.document_artifacts DROP CONSTRAINT IF EXISTS document_artifacts_layout_check;
ALTER TABLE public.document_artifacts
  ADD CONSTRAINT document_artifacts_layout_check
  CHECK (layout IN ('STANDARD','ESENCIAL','PROYECTO','ALTERNATIVAS','PLANO','COMPACTA','VENTANA','OBRA'));
COMMIT;
