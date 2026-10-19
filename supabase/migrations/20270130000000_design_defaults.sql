-- Usual design values inherited company → project → window (v1 encargo O05).
-- They only seed new windows; existing positions and issued revisions keep
-- their frozen designs. Values are validated by the backend against the
-- catalog the organization can read.
ALTER TABLE public.tenancy_organizations
  ADD COLUMN design_defaults jsonb NOT NULL DEFAULT '{}'::jsonb
  CHECK (jsonb_typeof(design_defaults)='object');
GRANT SELECT (design_defaults) ON public.tenancy_organizations TO authenticated, documentary_backend;
GRANT UPDATE (design_defaults) ON public.tenancy_organizations TO documentary_backend;

ALTER TABLE public.projects
  ADD COLUMN design_defaults jsonb NOT NULL DEFAULT '{}'::jsonb
  CHECK (jsonb_typeof(design_defaults)='object');
