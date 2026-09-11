BEGIN;

-- A backend-only role still evaluates tenant RLS. It cannot log in and is not
-- granted to authenticated/anon/authenticator; only the trusted DB session may
-- assume it after JWT verification to calculate an estimator's derived price.
DO $$ BEGIN
  IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='pricing_backend') THEN
    CREATE ROLE pricing_backend NOLOGIN NOSUPERUSER NOBYPASSRLS;
  END IF;
END $$;
GRANT pricing_backend TO postgres;
GRANT USAGE ON SCHEMA public, private, auth TO pricing_backend;
GRANT EXECUTE ON FUNCTION private.current_user_org_ids() TO pricing_backend;
GRANT EXECUTE ON FUNCTION auth.uid() TO pricing_backend;
GRANT SELECT ON public.tenancy_memberships, public.tenancy_organizations TO pricing_backend;
GRANT SELECT ON public.profile_systems,public.profile_articles,public.glazing_bead_matrix,
  public.hardware_kits,public.infill_articles,public.profile_purchase_mappings,
  public.reinforcement_articles TO pricing_backend;

CREATE FUNCTION private.pricing_role(target_org UUID, allowed_roles TEXT[])
RETURNS BOOLEAN LANGUAGE sql STABLE SECURITY DEFINER SET search_path = '' AS $$
  SELECT EXISTS (SELECT 1 FROM public.tenancy_memberships
    WHERE org_id=target_org AND user_id=auth.uid() AND is_active
      AND role::text=ANY(allowed_roles));
$$;
REVOKE ALL ON FUNCTION private.pricing_role(UUID,TEXT[]) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.pricing_role(UUID,TEXT[]) TO authenticated, pricing_backend;

ALTER TABLE public.price_audit_logs
  ALTER COLUMN old_value TYPE NUMERIC(16,4),
  ALTER COLUMN new_value TYPE NUMERIC(16,4),
  ADD COLUMN old_record JSONB,
  ADD COLUMN new_record JSONB;

CREATE TABLE public.pricing_configurations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
  context_code TEXT NOT NULL CHECK (length(btrim(context_code))>0),
  typology TEXT NOT NULL,
  pricing_mode TEXT NOT NULL CHECK (pricing_mode IN ('COST_PLUS_MARGIN',
    'PRICE_PER_M2_BY_TYPOLOGY','FIXED_PRICE_MATRIX_DIMENSIONAL',
    'TARGET_GROSS_MARGIN_PROJECT','COMMERCIAL_LIST_WITH_DISCOUNTS')),
  currency public.currency_code NOT NULL,
  rate_per_m2 NUMERIC(14,4) CHECK (rate_per_m2>=0 AND rate_per_m2<'Infinity'::numeric),
  base_glass_sku TEXT,
  catalog_price NUMERIC(14,4) CHECK (catalog_price>=0 AND catalog_price<'Infinity'::numeric),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  revision BIGINT NOT NULL DEFAULT 1,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(id,org_id),
  CHECK (pricing_mode<>'PRICE_PER_M2_BY_TYPOLOGY' OR
    (rate_per_m2 IS NOT NULL AND base_glass_sku IS NOT NULL AND length(btrim(base_glass_sku))>0)),
  CHECK (pricing_mode<>'COMMERCIAL_LIST_WITH_DISCOUNTS' OR catalog_price IS NOT NULL)
);
CREATE TABLE public.pricing_matrix_cells (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
  configuration_id UUID NOT NULL,
  width_mm INTEGER NOT NULL CHECK (width_mm BETWEEN 600 AND 2400 AND width_mm%200=0),
  height_mm INTEGER NOT NULL CHECK (height_mm BETWEEN 600 AND 2400 AND height_mm%200=0),
  price NUMERIC(14,4) NOT NULL CHECK (price>=0 AND price<'Infinity'::numeric),
  FOREIGN KEY(configuration_id,org_id) REFERENCES public.pricing_configurations(id,org_id) ON DELETE CASCADE,
  UNIQUE(configuration_id,width_mm,height_mm)
);
CREATE TABLE public.pricing_fx_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
  base_currency public.currency_code NOT NULL CHECK (base_currency='USD'),
  quote_currency public.currency_code NOT NULL CHECK (quote_currency='CLP'),
  observed_rate NUMERIC(20,8) NOT NULL CHECK (observed_rate>0 AND observed_rate<'Infinity'::numeric),
  observed_date DATE NOT NULL,
  effective_date DATE NOT NULL,
  source TEXT NOT NULL CHECK (length(btrim(source))>0),
  captured_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(id,org_id)
);
CREATE TABLE public.pricing_operations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
  project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  requested_by UUID NOT NULL,
  request JSONB NOT NULL,
  input_snapshot JSONB NOT NULL,
  result JSONB NOT NULL,
  source_revision TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('PREVIEW','PENDING','APPLIED','REJECTED')),
  approved_by UUID,
  approved_at TIMESTAMPTZ,
  reason TEXT NOT NULL CHECK (length(btrim(reason))>0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(id,org_id)
);

ALTER TABLE public.cost_lists ADD CONSTRAINT cost_list_dates CHECK(valid_to IS NULL OR valid_to>=valid_from);
ALTER TABLE public.cost_list_items ADD COLUMN description TEXT NOT NULL DEFAULT '';
ALTER TABLE public.pricing_rules ADD CONSTRAINT pricing_rules_numeric_domain CHECK(
  default_margin_pct>=0 AND default_margin_pct<1 AND tax_rate_pct>=0 AND tax_rate_pct<=1
  AND waste_factor_pct=0.08 AND labor_rate_per_m2>=0 AND installation_rate_per_m2>=0
  AND labor_rate_per_m2<'Infinity'::numeric AND installation_rate_per_m2<'Infinity'::numeric);
ALTER TABLE public.cost_list_items ADD CONSTRAINT cost_item_finite_nonnegative
  CHECK(unit_cost>=0 AND unit_cost<'Infinity'::numeric);
ALTER TABLE public.cost_lists ADD CONSTRAINT cost_list_tenant_key UNIQUE(id,org_id);
ALTER TABLE public.cost_list_items ADD CONSTRAINT cost_item_parent_tenant
  FOREIGN KEY(cost_list_id,org_id) REFERENCES public.cost_lists(id,org_id) ON DELETE CASCADE;
ALTER TABLE public.projects ADD CONSTRAINT pricing_project_tenant_key UNIQUE(id,org_id);
ALTER TABLE public.pricing_operations ADD CONSTRAINT pricing_operation_project_tenant
  FOREIGN KEY(project_id,org_id) REFERENCES public.projects(id,org_id) ON DELETE CASCADE;
ALTER TABLE public.project_positions ADD CONSTRAINT pricing_position_project_tenant
  FOREIGN KEY(project_id,org_id) REFERENCES public.projects(id,org_id) ON DELETE CASCADE;

ALTER TABLE public.pricing_configurations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pricing_matrix_cells ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pricing_fx_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pricing_operations ENABLE ROW LEVEL SECURITY;

-- The trigger inserts the immutable evidence BEFORE changing the business row.
-- JSONB records preserve nonnumeric configuration and exact numeric field values.
CREATE FUNCTION private.audit_pricing_mutation() RETURNS TRIGGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE prior JSONB; following JSONB; target UUID; actor UUID; why TEXT;
BEGIN
  prior := CASE WHEN TG_OP='INSERT' THEN NULL ELSE to_jsonb(OLD) END;
  following := CASE WHEN TG_OP='DELETE' THEN NULL ELSE to_jsonb(NEW) END;
  target := (COALESCE(following,prior)->>'org_id')::UUID;
  actor := auth.uid();
  -- Organization teardown by the privileged maintenance session follows the
  -- existing tenant cascade. Its parent no longer exists for the audit FK.
  IF TG_OP='DELETE' AND pg_trigger_depth()>1 AND actor IS NULL
    AND (session_user IN ('postgres','supabase_admin') OR
      (session_user='authenticator' AND current_setting('role')='service_role'))
    AND NOT EXISTS(SELECT 1 FROM public.tenancy_organizations WHERE id=target) THEN
    RETURN OLD;
  END IF;
  why := nullif(btrim(current_setting('app.pricing_reason',true)),'');
  IF actor IS NOT NULL AND why IS NULL THEN
    RAISE EXCEPTION 'pricing_audit_reason_required' USING ERRCODE='23514';
  END IF;
  IF actor IS NULL AND session_user NOT IN ('postgres','supabase_admin') THEN
    RAISE EXCEPTION 'pricing_audit_actor_required' USING ERRCODE='42501';
  END IF;
  IF prior IS NOT NULL AND following IS NOT NULL AND prior=following THEN RETURN NEW; END IF;
  INSERT INTO public.price_audit_logs(org_id,entity,entity_id,field,old_value,new_value,
      actor_type,actor_user_id,reason,old_record,new_record)
  VALUES(target,TG_TABLE_NAME,(COALESCE(following,prior)->>'id')::UUID,TG_OP,
    (prior->>'unit_cost')::numeric,(following->>'unit_cost')::numeric,
    CASE WHEN actor IS NULL THEN 'SYSTEM' ELSE 'HUMAN' END,actor,
    COALESCE(why,'Privileged database maintenance'),prior,following);
  IF TG_OP='DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END; $$;
REVOKE ALL ON FUNCTION private.audit_pricing_mutation() FROM PUBLIC;

CREATE FUNCTION private.immutable_price_audit() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path='' AS $$
BEGIN
  -- Explicit privileged tenant cleanup is outside application authorization.
  IF (session_user IN ('postgres','supabase_admin') OR
      (session_user='authenticator' AND current_setting('role')='service_role'))
     AND auth.uid() IS NULL AND pg_trigger_depth()>1
     AND NOT EXISTS(SELECT 1 FROM public.tenancy_organizations WHERE id=OLD.org_id)
     THEN RETURN OLD; END IF;
  RAISE EXCEPTION 'price_audit_append_only' USING ERRCODE='42501';
END; $$;
CREATE TRIGGER price_audit_append_only BEFORE UPDATE OR DELETE ON public.price_audit_logs
FOR EACH ROW EXECUTE FUNCTION private.immutable_price_audit();

DROP POLICY cost_lists_isolation ON public.cost_lists;
DROP POLICY cost_list_items_isolation ON public.cost_list_items;
DROP POLICY pricing_rules_isolation ON public.pricing_rules;
DROP POLICY price_audit_logs_isolation ON public.price_audit_logs;
REVOKE ALL ON public.price_audit_logs FROM authenticated;
GRANT SELECT ON public.price_audit_logs TO authenticated;
CREATE POLICY price_audit_owner_read ON public.price_audit_logs FOR SELECT TO authenticated
USING(private.pricing_role(org_id,ARRAY['OWNER']));

DO $$
DECLARE table_name TEXT;
BEGIN
  FOREACH table_name IN ARRAY ARRAY['cost_lists','cost_list_items','pricing_rules',
    'pricing_configurations','pricing_matrix_cells','pricing_fx_snapshots','pricing_operations'] LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY',table_name);
    EXECUTE format('REVOKE ALL ON public.%I FROM anon,authenticated',table_name);
    EXECUTE format('GRANT SELECT,INSERT,UPDATE,DELETE ON public.%I TO authenticated',table_name);
    EXECUTE format('GRANT SELECT ON public.%I TO pricing_backend',table_name);
    EXECUTE format('CREATE POLICY pricing_owner_write ON public.%I FOR ALL TO authenticated USING(private.pricing_role(org_id,ARRAY[''OWNER''])) WITH CHECK(private.pricing_role(org_id,ARRAY[''OWNER'']))',table_name);
    EXECUTE format('CREATE POLICY pricing_manager_read ON public.%I FOR SELECT TO authenticated USING(private.pricing_role(org_id,ARRAY[''WORKSHOP_MANAGER'']))',table_name);
    EXECUTE format('CREATE POLICY pricing_backend_read ON public.%I FOR SELECT TO pricing_backend USING(org_id IN (SELECT private.current_user_org_ids()) AND private.pricing_role(org_id,ARRAY[''OWNER'',''ESTIMATOR'',''WORKSHOP_MANAGER'']))',table_name);
    EXECUTE format('CREATE TRIGGER pricing_audit_before BEFORE INSERT OR UPDATE OR DELETE ON public.%I FOR EACH ROW EXECUTE FUNCTION private.audit_pricing_mutation()',table_name);
  END LOOP;
END $$;
REVOKE INSERT,UPDATE,DELETE ON public.pricing_operations FROM authenticated;
REVOKE UPDATE,DELETE ON public.pricing_fx_snapshots FROM authenticated;
GRANT INSERT,UPDATE ON public.pricing_operations TO pricing_backend;
CREATE POLICY pricing_operation_service_write ON public.pricing_operations FOR ALL TO pricing_backend
USING(private.pricing_role(org_id,ARRAY['OWNER','ESTIMATOR']))
WITH CHECK(private.pricing_role(org_id,ARRAY['OWNER','ESTIMATOR']));
GRANT SELECT,UPDATE ON public.projects,public.project_positions TO pricing_backend;
CREATE POLICY pricing_project_service ON public.projects FOR ALL TO pricing_backend
USING(private.pricing_role(org_id,ARRAY['OWNER','ESTIMATOR']))
WITH CHECK(private.pricing_role(org_id,ARRAY['OWNER','ESTIMATOR']));
CREATE POLICY pricing_position_service ON public.project_positions FOR ALL TO pricing_backend
USING(private.pricing_role(org_id,ARRAY['OWNER','ESTIMATOR']))
WITH CHECK(private.pricing_role(org_id,ARRAY['OWNER','ESTIMATOR']));
CREATE TRIGGER pricing_position_audit BEFORE UPDATE OF price_net,cost_net,discount_pct
ON public.project_positions FOR EACH ROW EXECUTE FUNCTION private.audit_pricing_mutation();
CREATE TRIGGER pricing_project_audit BEFORE UPDATE OF total_cost_net,total_price_net,total_price_tax,total_price_gross
ON public.projects FOR EACH ROW EXECUTE FUNCTION private.audit_pricing_mutation();

-- Existing broad SELECT grants must not expose cost columns through PostgREST.
REVOKE SELECT ON public.projects,public.project_positions FROM authenticated;
DO $$
DECLARE pricing_table_name TEXT; safe_columns TEXT;
BEGIN
  FOREACH pricing_table_name IN ARRAY ARRAY['projects','project_positions'] LOOP
    SELECT string_agg(quote_ident(column_name),',') INTO safe_columns
      FROM information_schema.columns WHERE table_schema='public'
      AND information_schema.columns.table_name=pricing_table_name
      AND column_name NOT IN ('cost_net','total_cost_net');
    EXECUTE format('GRANT SELECT(%s) ON public.%I TO authenticated',safe_columns,pricing_table_name);
  END LOOP;
END $$;

CREATE FUNCTION private.guard_commercial_write() RETURNS TRIGGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
BEGIN
  IF current_setting('role')='pricing_backend' THEN RETURN NEW; END IF;
  IF TG_TABLE_NAME='project_positions' THEN
    IF TG_OP='INSERT' AND (NEW.cost_net<>0 OR NEW.price_net<>0 OR NEW.discount_pct<>0) THEN
      RAISE EXCEPTION 'pricing_service_required' USING ERRCODE='42501';
    ELSIF TG_OP='UPDATE' AND (NEW.cost_net,NEW.price_net,NEW.discount_pct)
       IS DISTINCT FROM (OLD.cost_net,OLD.price_net,OLD.discount_pct) THEN
      RAISE EXCEPTION 'pricing_service_required' USING ERRCODE='42501';
    END IF;
  ELSE
    IF TG_OP='INSERT' AND (NEW.total_cost_net<>0 OR NEW.total_price_net<>0
       OR NEW.total_price_tax<>0 OR NEW.total_price_gross<>0) THEN
      RAISE EXCEPTION 'pricing_service_required' USING ERRCODE='42501';
    ELSIF TG_OP='UPDATE' AND (NEW.total_cost_net,NEW.total_price_net,NEW.total_price_tax,NEW.total_price_gross)
       IS DISTINCT FROM (OLD.total_cost_net,OLD.total_price_net,OLD.total_price_tax,OLD.total_price_gross) THEN
      RAISE EXCEPTION 'pricing_service_required' USING ERRCODE='42501';
    END IF;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER guard_commercial_write BEFORE INSERT OR UPDATE ON public.projects
FOR EACH ROW EXECUTE FUNCTION private.guard_commercial_write();

REVOKE ALL ON FUNCTION private.guard_commercial_write() FROM PUBLIC;
CREATE TRIGGER guard_commercial_write BEFORE INSERT OR UPDATE ON public.project_positions
FOR EACH ROW EXECUTE FUNCTION private.guard_commercial_write();

COMMIT;
