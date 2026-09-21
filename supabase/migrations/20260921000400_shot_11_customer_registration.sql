BEGIN;

CREATE TABLE public.flow_customer_operations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
  provider_environment TEXT NOT NULL CHECK(provider_environment IN ('sandbox','production')),
  name TEXT NOT NULL CHECK(length(trim(name))>0),
  email TEXT NOT NULL CHECK(length(trim(email))>0),
  state TEXT NOT NULL DEFAULT 'prepared' CHECK(state IN ('prepared','dispatching','uncertain','created')),
  customer_id UUID,
  registration_state TEXT NOT NULL DEFAULT 'none' CHECK(registration_state IN
    ('none','dispatching','uncertain','pending','registered','failed')),
  registration_token_hash TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(org_id,provider_environment),
  FOREIGN KEY(org_id,customer_id) REFERENCES public.payment_customers(org_id,id) ON DELETE RESTRICT
);
ALTER TABLE public.flow_customer_operations ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.flow_customer_operations FROM PUBLIC,anon,authenticated;
GRANT ALL ON public.flow_customer_operations TO service_role;
GRANT SELECT,INSERT ON public.flow_customer_operations TO billing_backend;
GRANT UPDATE(state,customer_id,registration_state,registration_token_hash)
  ON public.flow_customer_operations TO billing_backend;
CREATE POLICY billing_backend_scope ON public.flow_customer_operations FOR ALL TO billing_backend
  USING(private.billing_scope(org_id)) WITH CHECK(private.billing_scope(org_id));

CREATE FUNCTION private.flow_customer_operation_immutable() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path='' AS $$
BEGIN
  IF (to_jsonb(NEW)-ARRAY['state','customer_id','registration_state','registration_token_hash']) IS DISTINCT FROM
     (to_jsonb(OLD)-ARRAY['state','customer_id','registration_state','registration_token_hash'])
    OR (OLD.customer_id IS NOT NULL AND NEW.customer_id IS DISTINCT FROM OLD.customer_id)
    OR (OLD.state='created' AND NEW.state<>'created') THEN
    RAISE EXCEPTION 'flow_customer_operation_immutable' USING ERRCODE='23514';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER flow_customer_operation_immutable BEFORE UPDATE ON public.flow_customer_operations
  FOR EACH ROW EXECUTE FUNCTION private.flow_customer_operation_immutable();
REVOKE ALL ON FUNCTION private.flow_customer_operation_immutable() FROM PUBLIC;

COMMIT;
