BEGIN;

-- Presentation references are tenant-owned and never grant technical authority.
CREATE TABLE public.catalog_visual_references (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id),
 system_id uuid NOT NULL REFERENCES public.profile_systems(id),
 kind text NOT NULL CHECK(kind IN ('PROFILE','TEXTURE')),
 target_key text NOT NULL CHECK(length(target_key) BETWEEN 1 AND 100),
 actor_id uuid NOT NULL,
 file_name text NOT NULL CHECK(length(file_name) <= 200),
 storage_path text,
 content_sha256 text CHECK(content_sha256 ~ '^[a-f0-9]{64}$'),
 width_px integer CHECK(width_px BETWEEN 1 AND 2048),
 height_px integer CHECK(height_px BETWEEN 1 AND 2048),
 cleared boolean NOT NULL DEFAULT false,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 CHECK((cleared AND storage_path IS NULL AND content_sha256 IS NULL) OR
       (NOT cleared AND storage_path IS NOT NULL AND content_sha256 IS NOT NULL
        AND width_px IS NOT NULL AND height_px IS NOT NULL)),
 CHECK(storage_path IS NULL OR storage_path LIKE 'catalog-visuals/' || org_id::text || '/%')
);
CREATE INDEX catalog_visual_references_latest ON public.catalog_visual_references
 (org_id, system_id, kind, target_key, created_at DESC, id DESC);
ALTER TABLE public.catalog_visual_references ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.catalog_visual_references FROM PUBLIC,anon,authenticated;
GRANT SELECT ON public.catalog_visual_references TO authenticated;
GRANT SELECT,INSERT ON public.catalog_visual_references TO catalog_backend;
GRANT ALL ON public.catalog_visual_references TO service_role;
CREATE POLICY catalog_visual_references_read ON public.catalog_visual_references FOR SELECT
 TO authenticated USING(private.documentary_role(org_id,ARRAY['OWNER','ESTIMATOR','WORKSHOP_MANAGER']));
-- The backend needs SELECT for INSERT ... RETURNING, and already has the
-- catalog-management helper. Keep its reads under the same manager predicate
-- as its writes rather than granting it another domain's role helper.
CREATE POLICY catalog_visual_references_backend_read ON public.catalog_visual_references FOR SELECT
 TO catalog_backend USING(private.can_manage_catalog(org_id));
CREATE POLICY catalog_visual_references_write ON public.catalog_visual_references FOR INSERT
 TO catalog_backend WITH CHECK(private.can_manage_catalog(org_id) AND actor_id=auth.uid()
 AND EXISTS(SELECT 1 FROM public.profile_systems s WHERE s.id=system_id AND (s.org_id IS NULL OR s.org_id=catalog_visual_references.org_id)));
CREATE FUNCTION private.validate_catalog_visual_target() RETURNS trigger
LANGUAGE plpgsql SET search_path='' AS $$
BEGIN
 IF NEW.kind='PROFILE' AND NOT EXISTS(SELECT 1 FROM public.profile_articles a
  WHERE a.id::text=NEW.target_key AND a.system_id=NEW.system_id
  AND (a.org_id IS NULL OR a.org_id=NEW.org_id)) THEN
  RAISE EXCEPTION 'visual_target_invalid' USING ERRCODE='23514';
 END IF;
 IF NEW.kind='TEXTURE' AND NOT EXISTS(SELECT 1 FROM public.profile_systems s,
  jsonb_array_elements(coalesce(s.finish_authority->'colors','[]'::jsonb)) color
  WHERE s.id=NEW.system_id AND color->>'code'=NEW.target_key) THEN
  RAISE EXCEPTION 'visual_target_invalid' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION private.validate_catalog_visual_target() FROM PUBLIC;
CREATE TRIGGER catalog_visual_references_target BEFORE INSERT ON public.catalog_visual_references
 FOR EACH ROW EXECUTE FUNCTION private.validate_catalog_visual_target();
CREATE TRIGGER catalog_visual_references_immutable BEFORE UPDATE OR DELETE ON public.catalog_visual_references
 FOR EACH ROW EXECUTE FUNCTION private.reject_immutable_evidence();
CREATE TRIGGER catalog_visual_references_no_truncate BEFORE TRUNCATE ON public.catalog_visual_references
 FOR EACH STATEMENT EXECUTE FUNCTION private.reject_immutable_evidence();

COMMIT;
