-- P12f · Workshop documents composed for people from the same sealed
-- revision: «Orden de trabajo» (OT), «Informe de vidrios» (VIDRIOS) and
-- «Listado de montaje» (MONTAJE). Each is stored as its own artifact.
BEGIN;
ALTER TABLE public.document_artifacts DROP CONSTRAINT IF EXISTS document_artifacts_layout_check;
ALTER TABLE public.document_artifacts
  ADD CONSTRAINT document_artifacts_layout_check
  CHECK (layout IN ('STANDARD','ESENCIAL','PROYECTO','ALTERNATIVAS','PLANO','OT','VIDRIOS','MONTAJE',
                    'COMPACTA','VENTANA','OBRA'));
COMMIT;
