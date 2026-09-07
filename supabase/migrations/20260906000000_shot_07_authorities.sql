BEGIN;
ALTER TABLE public.profile_systems ADD COLUMN chamber_clearance_mm NUMERIC(10,2)
    CHECK (chamber_clearance_mm > 0);
ALTER TABLE public.hardware_kits ADD COLUMN carriage_capacity_kg NUMERIC(8,2)
    CHECK (carriage_capacity_kg > 0);
CREATE TABLE public.profile_purchase_mappings (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 profile_article_id UUID NOT NULL REFERENCES public.profile_articles(id) ON DELETE CASCADE,
 org_id UUID REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
 commercial_sku VARCHAR(150) NOT NULL CHECK (length(trim(commercial_sku)) > 0),
 manufacturer_name VARCHAR(255) NOT NULL,
 supplier_name VARCHAR(255),
 purchase_unit VARCHAR(10) NOT NULL CHECK (purchase_unit = 'BAR'),
 is_active BOOLEAN NOT NULL DEFAULT TRUE,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE public.reinforcement_articles (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 system_id UUID NOT NULL REFERENCES public.profile_systems(id) ON DELETE CASCADE,
 org_id UUID REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
 parent_profile_article_id UUID NOT NULL REFERENCES public.profile_articles(id) ON DELETE CASCADE,
 sku VARCHAR(150) NOT NULL, commercial_sku VARCHAR(150) NOT NULL,
 name VARCHAR(255) NOT NULL, manufacturer_name VARCHAR(255), supplier_name VARCHAR(255),
 stock_length_mm NUMERIC(10,2) NOT NULL CHECK (stock_length_mm > 0),
 thickness_mm NUMERIC(6,2) CHECK (thickness_mm > 0),
 ix_cm4 NUMERIC(12,4) CHECK (ix_cm4 > 0),
 purchase_unit VARCHAR(10) NOT NULL CHECK (purchase_unit = 'BAR'),
 is_default BOOLEAN NOT NULL DEFAULT FALSE, is_active BOOLEAN NOT NULL DEFAULT TRUE,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE public.cutting_profiles (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 org_id UUID REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
 code VARCHAR(100) NOT NULL, name VARCHAR(255) NOT NULL,
 kerf_mm NUMERIC(10,2) NOT NULL CHECK (kerf_mm >= 0),
 head_trim_mm NUMERIC(10,2) NOT NULL CHECK (head_trim_mm >= 0),
 tail_trim_mm NUMERIC(10,2) NOT NULL CHECK (tail_trim_mm >= 0),
 is_default BOOLEAN NOT NULL DEFAULT FALSE, is_active BOOLEAN NOT NULL DEFAULT TRUE,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE public.inspector_rule_configs (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 system_id UUID NOT NULL REFERENCES public.profile_systems(id) ON DELETE CASCADE,
 org_id UUID REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
 rule_id VARCHAR(3) NOT NULL CHECK (rule_id ~ '^R(0[1-9]|1[0-4])$'),
 params JSONB NOT NULL CHECK (jsonb_typeof(params) = 'object'),
 is_active BOOLEAN NOT NULL DEFAULT TRUE,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 UNIQUE NULLS NOT DISTINCT (system_id, org_id, rule_id)
);

ALTER TABLE public.profile_purchase_mappings ENABLE ROW LEVEL SECURITY;
CREATE POLICY profile_purchase_mappings_select ON public.profile_purchase_mappings
 FOR SELECT TO authenticated USING (
 auth.uid() IS NOT NULL AND (profile_article_id IN (SELECT id FROM public.profile_articles))
 AND (org_id IS NULL OR org_id IN (SELECT private.current_user_org_ids()))
 );
CREATE POLICY profile_purchase_mappings_modify ON public.profile_purchase_mappings
 FOR ALL TO authenticated
 USING (org_id IN (SELECT private.current_user_org_ids()) AND (profile_article_id IN (SELECT id FROM public.profile_articles)))
 WITH CHECK (org_id IN (SELECT private.current_user_org_ids()) AND (profile_article_id IN (SELECT id FROM public.profile_articles)));
REVOKE ALL ON public.profile_purchase_mappings FROM anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.profile_purchase_mappings TO authenticated;
GRANT ALL ON public.profile_purchase_mappings TO service_role;

ALTER TABLE public.reinforcement_articles ENABLE ROW LEVEL SECURITY;
CREATE POLICY reinforcement_articles_select ON public.reinforcement_articles
 FOR SELECT TO authenticated USING (
 auth.uid() IS NOT NULL AND (system_id IN (SELECT id FROM public.profile_systems))
 AND (org_id IS NULL OR org_id IN (SELECT private.current_user_org_ids()))
 );
CREATE POLICY reinforcement_articles_modify ON public.reinforcement_articles
 FOR ALL TO authenticated
 USING (org_id IN (SELECT private.current_user_org_ids()) AND (system_id IN (SELECT id FROM public.profile_systems)))
 WITH CHECK (org_id IN (SELECT private.current_user_org_ids()) AND (system_id IN (SELECT id FROM public.profile_systems)));
REVOKE ALL ON public.reinforcement_articles FROM anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.reinforcement_articles TO authenticated;
GRANT ALL ON public.reinforcement_articles TO service_role;

ALTER TABLE public.cutting_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY cutting_profiles_select ON public.cutting_profiles
 FOR SELECT TO authenticated USING (
 auth.uid() IS NOT NULL AND (TRUE)
 AND (org_id IS NULL OR org_id IN (SELECT private.current_user_org_ids()))
 );
CREATE POLICY cutting_profiles_modify ON public.cutting_profiles
 FOR ALL TO authenticated
 USING (org_id IN (SELECT private.current_user_org_ids()) AND (TRUE))
 WITH CHECK (org_id IN (SELECT private.current_user_org_ids()) AND (TRUE));
REVOKE ALL ON public.cutting_profiles FROM anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.cutting_profiles TO authenticated;
GRANT ALL ON public.cutting_profiles TO service_role;

ALTER TABLE public.inspector_rule_configs ENABLE ROW LEVEL SECURITY;
CREATE POLICY inspector_rule_configs_select ON public.inspector_rule_configs
 FOR SELECT TO authenticated USING (
 auth.uid() IS NOT NULL AND (system_id IN (SELECT id FROM public.profile_systems))
 AND (org_id IS NULL OR org_id IN (SELECT private.current_user_org_ids()))
 );
CREATE POLICY inspector_rule_configs_modify ON public.inspector_rule_configs
 FOR ALL TO authenticated
 USING (org_id IN (SELECT private.current_user_org_ids()) AND (system_id IN (SELECT id FROM public.profile_systems)))
 WITH CHECK (org_id IN (SELECT private.current_user_org_ids()) AND (system_id IN (SELECT id FROM public.profile_systems)));
REVOKE ALL ON public.inspector_rule_configs FROM anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.inspector_rule_configs TO authenticated;
GRANT ALL ON public.inspector_rule_configs TO service_role;

-- A system cannot publish inspector config without its explicit clearance authority.
CREATE FUNCTION private.check_inspector_clearance() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path = '' AS $$
BEGIN
 IF NEW.is_active AND NOT EXISTS (
  SELECT 1 FROM public.profile_systems WHERE id=NEW.system_id AND chamber_clearance_mm IS NOT NULL
 ) THEN RAISE EXCEPTION 'Inspector requires explicit chamber clearance'; END IF;
 RETURN NEW;
END;
$$;
CREATE TRIGGER inspector_clearance_required BEFORE INSERT OR UPDATE
 ON public.inspector_rule_configs FOR EACH ROW EXECUTE FUNCTION private.check_inspector_clearance();
CREATE FUNCTION private.preserve_inspector_clearance() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path = '' AS $$
BEGIN
 IF NEW.chamber_clearance_mm IS NULL AND EXISTS (
  SELECT 1 FROM public.inspector_rule_configs WHERE system_id=NEW.id AND is_active
 ) THEN RAISE EXCEPTION 'Active Inspector requires chamber clearance'; END IF;
 RETURN NEW;
END;
$$;
CREATE TRIGGER preserve_inspector_clearance BEFORE UPDATE OF chamber_clearance_mm
 ON public.profile_systems FOR EACH ROW EXECUTE FUNCTION private.preserve_inspector_clearance();
COMMIT;
