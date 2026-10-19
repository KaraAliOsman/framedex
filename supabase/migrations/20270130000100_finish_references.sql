-- Business finish references (encargo O15): a company photo of a material,
-- prepared as a repeatable sample and linked to a catalog finish code it
-- represents visually. Presentation only: it never changes the finish
-- authority, its price or any fabrication value. Originals are kept.
CREATE TABLE public.finish_references (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id),
  name varchar(120) NOT NULL CHECK (length(btrim(name)) > 0),
  finish_code varchar(50) NOT NULL CHECK (finish_code ~ '^[A-Z0-9_+.-]+$'),
  original_key text NOT NULL,
  original_sha256 char(64) NOT NULL,
  original_type varchar(20) NOT NULL CHECK (original_type IN ('image/png','image/jpeg','image/webp')),
  prepared_key text NOT NULL,
  prepared_sha256 char(64) NOT NULL,
  tile_mm NUMERIC(8,2) NOT NULL DEFAULT 300 CHECK (tile_mm >= 20 AND tile_mm <= 3000),
  grain varchar(10) NOT NULL DEFAULT 'ALONG' CHECK (grain IN ('ALONG','ACROSS','NONE')),
  version integer NOT NULL DEFAULT 1 CHECK (version >= 1),
  created_by uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  archived_at timestamptz
);
CREATE UNIQUE INDEX finish_reference_active_code ON public.finish_references(org_id, finish_code)
  WHERE archived_at IS NULL;
ALTER TABLE public.finish_references ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.finish_references FROM anon, authenticated;
GRANT SELECT ON public.finish_references TO authenticated;
GRANT SELECT, INSERT, UPDATE ON public.finish_references TO documentary_backend;
CREATE POLICY finish_reference_read ON public.finish_references FOR SELECT TO authenticated
  USING (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY finish_reference_backend ON public.finish_references TO documentary_backend
  USING (org_id IN (SELECT private.current_user_org_ids()))
  WITH CHECK (private.documentary_role(org_id, ARRAY['OWNER','ESTIMATOR']));
