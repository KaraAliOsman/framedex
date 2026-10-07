-- Purchase tariffs are backend authority, not a member-readable catalog field.
BEGIN;
-- A table grant would override a column revocation. Preserve every existing
-- public field while explicitly excluding this private authority.
REVOKE SELECT ON public.profile_systems FROM authenticated;
REVOKE SELECT(extra_authority) ON public.profile_systems FROM authenticated;
DO $$ DECLARE columns TEXT;
BEGIN
  SELECT string_agg(quote_ident(attname),',') INTO columns FROM pg_attribute
    WHERE attrelid='public.profile_systems'::regclass AND attnum>0
      AND NOT attisdropped AND attname<>'extra_authority';
  EXECUTE 'GRANT SELECT(' || columns || ') ON public.profile_systems TO authenticated';
END; $$;

CREATE FUNCTION public.catalog_extra_authority(system_id UUID, target_org UUID DEFAULT NULL) RETURNS JSONB
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = '' AS $$
DECLARE authority JSONB; owner_org UUID; definition JSONB; zone TEXT; rate JSONB;
        definitions JSONB := '[]'::JSONB; zones JSONB;
BEGIN
  -- The function owner is NOBYPASSRLS: the existing catalog policies evaluate
  -- the caller's verified claims, including visibility of global authorities.
  SELECT s.extra_authority,s.org_id INTO authority,owner_org FROM public.profile_systems s WHERE s.id=system_id;
  IF authority IS NULL THEN RETURN NULL; END IF;
  IF current_setting('role') IN ('catalog_backend','pricing_backend','documentary_backend') THEN
    RETURN authority;
  END IF;
  IF (owner_org IS NULL OR owner_org=target_org) AND private.can_manage_catalog(target_org) THEN
    RETURN authority;
  END IF;
  FOR definition IN SELECT value FROM jsonb_array_elements(authority->'definitions') LOOP
    zones := '{}'::JSONB;
    FOR zone,rate IN SELECT key,value FROM jsonb_each(COALESCE(definition->'zones','{}'::JSONB)) LOOP
      zones := zones || jsonb_build_object(zone,rate-'cost_rate');
    END LOOP;
    definitions := definitions || jsonb_build_array((definition-'cost_rate') || jsonb_build_object('zones',zones));
  END LOOP;
  RETURN authority || jsonb_build_object('definitions',definitions);
END; $$;
GRANT CREATE ON SCHEMA public TO catalog_backend;
ALTER FUNCTION public.catalog_extra_authority(UUID,UUID) OWNER TO catalog_backend;
REVOKE CREATE ON SCHEMA public FROM catalog_backend;
REVOKE ALL ON FUNCTION public.catalog_extra_authority(UUID,UUID) FROM PUBLIC,anon;
GRANT EXECUTE ON FUNCTION public.catalog_extra_authority(UUID,UUID)
  TO authenticated,catalog_backend,pricing_backend,documentary_backend;
COMMIT;
