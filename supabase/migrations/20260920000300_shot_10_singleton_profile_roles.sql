CREATE UNIQUE INDEX uk_tenant_system_singleton_profile_role
ON public.profile_articles(system_id,org_id,role)
WHERE org_id IS NOT NULL
  AND role IN ('FRAME','SASH','MULLION_V','MULLION_H','INVERSOR','COUPLER','ADDITIONAL','THRESHOLD');

CREATE UNIQUE INDEX uk_global_system_singleton_profile_role
ON public.profile_articles(system_id,role)
WHERE org_id IS NULL
  AND role IN ('FRAME','SASH','MULLION_V','MULLION_H','INVERSOR','COUPLER','ADDITIONAL','THRESHOLD');
