-- P18: immutable scoped reports and revision-bound human envelope inputs.
BEGIN;
CREATE TABLE public.catalog_thermal_authorities (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 org_id UUID REFERENCES public.tenancy_organizations(id),
 system_id UUID NOT NULL REFERENCES public.profile_systems(id),
 kind TEXT NOT NULL CHECK(kind IN ('FRAME','GLASS','SPACER','PERFORMANCE')),
 profile_skus TEXT[] NOT NULL DEFAULT '{}', glass_sku TEXT, glass_fingerprint TEXT,
 spacer_code TEXT, catalog_fingerprint TEXT NOT NULL, construction_fingerprint TEXT,
 uf NUMERIC CHECK(uf>0), ug NUMERIC CHECK(ug>0), solar_factor NUMERIC CHECK(solar_factor BETWEEN 0 AND 1),
 psi_g NUMERIC CHECK(psi_g>=0), air_class SMALLINT CHECK(air_class BETWEEN 0 AND 4),
 air_pressure_pa NUMERIC CHECK(air_pressure_pa=100), water_class TEXT, wind_class TEXT,
 min_width_mm NUMERIC NOT NULL CHECK(min_width_mm>0), max_width_mm NUMERIC NOT NULL,
 min_height_mm NUMERIC NOT NULL CHECK(min_height_mm>0), max_height_mm NUMERIC NOT NULL,
 opening_types TEXT[] NOT NULL CHECK(cardinality(opening_types)>0),
 source_document TEXT NOT NULL CHECK(length(trim(source_document))>0),
 source_url TEXT NOT NULL CHECK(source_url ~ '^https?://'),
 source_page TEXT NOT NULL CHECK(length(trim(source_page))>0),
 laboratory TEXT NOT NULL CHECK(length(trim(laboratory))>0),
 laboratory_registration TEXT NOT NULL DEFAULT '',
 report_date DATE NOT NULL, valid_until DATE NOT NULL,
 standard TEXT NOT NULL CHECK(length(trim(standard))>0),
 applicability TEXT NOT NULL CHECK(length(trim(applicability))>0),
 synthetic BOOLEAN NOT NULL DEFAULT FALSE,
 review_state TEXT NOT NULL DEFAULT 'PENDING' CHECK(review_state IN ('PENDING','REVIEWED','REJECTED','REVOKED')),
 declared_by UUID NOT NULL, declared_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
 reviewed_by UUID, reviewed_at TIMESTAMPTZ,
 CHECK(max_width_mm>=min_width_mm AND max_height_mm>=min_height_mm AND valid_until>=report_date),
 CHECK(uf::text NOT IN ('NaN','Infinity','-Infinity') AND ug::text NOT IN ('NaN','Infinity','-Infinity')
   AND solar_factor::text NOT IN ('NaN','Infinity','-Infinity') AND psi_g::text NOT IN ('NaN','Infinity','-Infinity')
   AND min_width_mm::text NOT IN ('NaN','Infinity','-Infinity') AND max_width_mm::text NOT IN ('NaN','Infinity','-Infinity')
   AND min_height_mm::text NOT IN ('NaN','Infinity','-Infinity') AND max_height_mm::text NOT IN ('NaN','Infinity','-Infinity')),
 CHECK(air_class IS NULL OR air_pressure_pa=100),
 CHECK(air_class IS NULL OR (length(trim(laboratory_registration))>0
   AND standard ~* 'NCh[[:space:]]*3296' AND standard ~* 'NCh[[:space:]]*3297')),
 CHECK((kind='FRAME' AND uf IS NOT NULL AND ug IS NULL AND solar_factor IS NULL AND psi_g IS NULL AND air_class IS NULL AND air_pressure_pa IS NULL AND water_class IS NULL AND wind_class IS NULL)
    OR (kind='GLASS' AND ug IS NOT NULL AND glass_sku IS NOT NULL AND glass_fingerprint IS NOT NULL AND uf IS NULL AND psi_g IS NULL AND air_class IS NULL AND air_pressure_pa IS NULL AND water_class IS NULL AND wind_class IS NULL)
    OR (kind='SPACER' AND psi_g IS NOT NULL AND glass_sku IS NOT NULL AND glass_fingerprint IS NOT NULL AND spacer_code IS NOT NULL AND uf IS NULL AND ug IS NULL AND solar_factor IS NULL AND air_class IS NULL AND air_pressure_pa IS NULL AND water_class IS NULL AND wind_class IS NULL)
    OR (kind='PERFORMANCE' AND (air_class IS NOT NULL OR water_class IS NOT NULL OR wind_class IS NOT NULL) AND uf IS NULL AND ug IS NULL AND solar_factor IS NULL AND psi_g IS NULL)),
 CHECK(kind='GLASS' OR cardinality(profile_skus)>0),
 CHECK(kind<>'PERFORMANCE' OR (construction_fingerprint IS NOT NULL AND length(trim(construction_fingerprint))>0)),
 CHECK((review_state='PENDING' AND reviewed_by IS NULL AND reviewed_at IS NULL)
       OR (review_state<>'PENDING' AND reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL))
);
CREATE INDEX catalog_thermal_lookup ON public.catalog_thermal_authorities(system_id,org_id,kind,review_state);
ALTER TABLE public.catalog_thermal_authorities ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.catalog_thermal_authorities FROM anon,authenticated;
GRANT SELECT ON public.catalog_thermal_authorities TO authenticated,catalog_backend,documentary_backend;
GRANT INSERT,UPDATE ON public.catalog_thermal_authorities TO catalog_backend;
GRANT ALL ON public.catalog_thermal_authorities TO service_role;
CREATE POLICY thermal_report_read ON public.catalog_thermal_authorities FOR SELECT
 TO authenticated,catalog_backend,documentary_backend USING (
 (org_id IS NULL OR org_id IN(SELECT private.current_user_org_ids())) AND EXISTS(
 SELECT 1 FROM public.profile_systems s WHERE s.id=system_id AND
 (s.org_id IN(SELECT private.current_user_org_ids()) OR (s.org_id IS NULL AND s.is_global))));
CREATE POLICY thermal_report_write ON public.catalog_thermal_authorities FOR ALL TO catalog_backend
 USING(org_id IS NOT NULL AND private.can_manage_catalog(org_id))
 WITH CHECK(org_id IS NOT NULL AND private.can_manage_catalog(org_id) AND EXISTS(
 SELECT 1 FROM public.profile_systems s WHERE s.id=system_id AND
 (s.org_id=catalog_thermal_authorities.org_id OR (s.org_id IS NULL AND s.is_global))));
CREATE FUNCTION private.guard_thermal_report() RETURNS TRIGGER LANGUAGE plpgsql SET search_path='' AS $$
BEGIN
 IF TG_OP='DELETE' THEN RAISE EXCEPTION 'thermal_report_immutable' USING ERRCODE='23514'; END IF;
 IF current_user='catalog_backend' AND (NEW.org_id IS NULL OR NOT private.can_manage_catalog(NEW.org_id)
    OR (TG_OP='INSERT' AND (NEW.declared_by IS DISTINCT FROM NULLIF(current_setting('request.jwt.claim.sub',true),'')::uuid OR NEW.review_state<>'PENDING'))
    OR (TG_OP='UPDATE' AND NEW.reviewed_by IS DISTINCT FROM NULLIF(current_setting('request.jwt.claim.sub',true),'')::uuid)) THEN
  RAISE EXCEPTION 'thermal_reviewer_required' USING ERRCODE='42501';
 END IF;
 IF TG_OP='UPDATE' AND (
    NOT ((OLD.review_state='PENDING' AND NEW.review_state IN ('REVIEWED','REJECTED'))
      OR (OLD.review_state='REVIEWED' AND NEW.review_state='REVOKED'))
    OR (to_jsonb(NEW)-ARRAY['review_state','reviewed_by','reviewed_at']) IS DISTINCT FROM
       (to_jsonb(OLD)-ARRAY['review_state','reviewed_by','reviewed_at'])) THEN
  RAISE EXCEPTION 'thermal_report_immutable' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION private.guard_thermal_report() FROM PUBLIC;
CREATE TRIGGER guard_thermal_report BEFORE INSERT OR UPDATE OR DELETE ON public.catalog_thermal_authorities
 FOR EACH ROW EXECUTE FUNCTION private.guard_thermal_report();

CREATE TABLE public.project_thermal_inputs (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(), org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id),
 project_id UUID NOT NULL, revision_code TEXT NOT NULL,
 inputs JSONB NOT NULL CHECK(jsonb_typeof(inputs)='object'),
 declared_by UUID NOT NULL, updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
 UNIQUE(project_id,revision_code), FOREIGN KEY(project_id,org_id) REFERENCES public.projects(id,org_id)
);
ALTER TABLE public.project_thermal_inputs ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.project_thermal_inputs FROM anon,authenticated;
GRANT SELECT ON public.project_thermal_inputs TO authenticated,documentary_backend;
GRANT INSERT,UPDATE ON public.project_thermal_inputs TO documentary_backend;
GRANT ALL ON public.project_thermal_inputs TO service_role;
CREATE POLICY thermal_input_read ON public.project_thermal_inputs FOR SELECT TO authenticated,documentary_backend
 USING(private.pricing_role(org_id,ARRAY['OWNER','ESTIMATOR','WORKSHOP_MANAGER']));
CREATE POLICY thermal_input_write ON public.project_thermal_inputs FOR ALL TO documentary_backend
 USING(private.pricing_role(org_id,ARRAY['OWNER','ESTIMATOR']))
 WITH CHECK(private.pricing_role(org_id,ARRAY['OWNER','ESTIMATOR']) AND declared_by=auth.uid());
CREATE FUNCTION private.guard_thermal_input() RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE p public.projects;
BEGIN
 IF TG_OP='DELETE' THEN RAISE EXCEPTION 'thermal_input_immutable' USING ERRCODE='23514'; END IF;
 IF TG_OP='UPDATE' AND (NEW.id,NEW.org_id,NEW.project_id,NEW.revision_code) IS DISTINCT FROM
                       (OLD.id,OLD.org_id,OLD.project_id,OLD.revision_code) THEN
  RAISE EXCEPTION 'thermal_input_identity_immutable' USING ERRCODE='23514';
 END IF;
 SELECT * INTO p FROM public.projects WHERE id=NEW.project_id AND org_id=NEW.org_id FOR UPDATE;
 IF p.id IS NULL OR p.status<>'DRAFT' OR p.current_revision<>NEW.revision_code OR EXISTS(
    SELECT 1 FROM public.project_versions v WHERE v.project_id=p.id AND v.org_id=p.org_id AND v.revision_code=NEW.revision_code) THEN
  RAISE EXCEPTION 'thermal_input_revision_required' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION private.guard_thermal_input() FROM PUBLIC;
CREATE TRIGGER guard_thermal_input BEFORE INSERT OR UPDATE OR DELETE ON public.project_thermal_inputs
 FOR EACH ROW EXECUTE FUNCTION private.guard_thermal_input();
COMMIT;
