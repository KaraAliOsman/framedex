-- Commercial quotation numbering and editable document composition (v1 06).
--
-- Numbering: each company numbers its quotations N.º 1, 2, 3… with an
-- editable prefix and next number. A work receives its number once, when its
-- first issuable preview is prepared (that PDF is the one that gets issued);
-- revisions keep it. Issued snapshots keep whatever number they sealed; older
-- revisions without a commercial number keep their technical folio.
ALTER TABLE public.tenancy_organizations
  ADD COLUMN quotation_number_prefix varchar(20) NOT NULL DEFAULT 'N.º '
    CHECK (quotation_number_prefix !~ '[<>{}]'),
  ADD COLUMN quotation_next_number integer NOT NULL DEFAULT 1
    CHECK (quotation_next_number >= 1 AND quotation_next_number <= 999999999);
GRANT SELECT (quotation_number_prefix, quotation_next_number)
  ON public.tenancy_organizations TO authenticated, documentary_backend;
GRANT UPDATE (quotation_number_prefix, quotation_next_number)
  ON public.tenancy_organizations TO documentary_backend;

ALTER TABLE public.projects
  ADD COLUMN commercial_number integer CHECK (commercial_number IS NULL OR commercial_number >= 1);
CREATE UNIQUE INDEX projects_commercial_number_per_org
  ON public.projects(org_id, commercial_number) WHERE commercial_number IS NOT NULL;
GRANT UPDATE (commercial_number) ON public.projects TO documentary_backend;

-- Editable composition of this work's quotation draft: template family,
-- visible/ordered blocks, editorial texts and presentation options. Numbers
-- never live here; they come from the sealed calculation.
ALTER TABLE public.project_documentary_inputs
  ADD COLUMN document_layout jsonb NOT NULL DEFAULT '{}'::jsonb
    CHECK (jsonb_typeof(document_layout)='object');

-- Workshop and purchasing documents can be produced in more than one
-- composition from the same sealed data; each composition is its own
-- immutable artifact.
ALTER TABLE public.document_artifacts
  ADD COLUMN layout text NOT NULL DEFAULT 'STANDARD'
    CHECK (layout IN ('STANDARD','ESENCIAL','PROYECTO','ALTERNATIVAS','COMPACTA','VENTANA','OBRA'));
ALTER TABLE public.document_artifacts
  DROP CONSTRAINT document_artifacts_artifact_scope_id_document_type_format_key;
ALTER TABLE public.document_artifacts
  ADD CONSTRAINT document_artifacts_slot_layout_key UNIQUE (artifact_scope_id, document_type, format, layout);
