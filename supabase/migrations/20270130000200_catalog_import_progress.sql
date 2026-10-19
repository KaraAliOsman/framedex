-- Long and mixed catalog PDFs are processed in internal page batches. The
-- import keeps the page inventory and each batch's state so a failed batch is
-- retried alone and a resumed import never re-processes finished pages.
ALTER TABLE public.catalog_imports
  ADD COLUMN progress jsonb NOT NULL DEFAULT '{}'::jsonb
  CHECK (jsonb_typeof(progress)='object');
