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

-- Import attestations may quote the private authority. Preserve their history
-- exactly while applying the same permission to that evidence row.
ALTER POLICY catalog_parameter_evidence_select ON public.catalog_parameter_evidence
  USING ((org_id IS NULL OR org_id IN (SELECT private.current_user_org_ids()))
    AND (authority_table<>'profile_systems' OR field_name<>'extra_authority'
         OR private.can_manage_catalog(org_id)));

-- Deferred binding checks need technical fields only. Keep every compatibility
-- predicate intact without requesting the new private tariff column.
CREATE OR REPLACE FUNCTION private.check_opening_catalog_bindings() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path='' AS $$
DECLARE target UUID; targets UUID[]; system_row public.profile_systems%ROWTYPE; cap JSONB; kit_sku TEXT; expected_type TEXT;
BEGIN
    IF TG_TABLE_NAME='profile_systems' THEN targets := ARRAY[NEW.id];
    ELSIF TG_OP='UPDATE' THEN targets := ARRAY[OLD.system_id,NEW.system_id];
    ELSE targets := ARRAY[CASE WHEN TG_OP='DELETE' THEN OLD.system_id ELSE NEW.system_id END]; END IF;
    FOREACH target IN ARRAY targets LOOP
    SELECT is_active,opening_capabilities,org_id
      INTO system_row.is_active,system_row.opening_capabilities,system_row.org_id
      FROM public.profile_systems WHERE id=target;
    IF NOT FOUND OR NOT system_row.is_active OR system_row.opening_capabilities IS NULL THEN CONTINUE; END IF;
    FOR cap IN SELECT value FROM jsonb_array_elements(system_row.opening_capabilities) LOOP
        expected_type := CASE WHEN cap->>'use'='DOOR' THEN 'DOOR'
            WHEN cap->>'movement'='TOP_HUNG' THEN 'AWNING'
            WHEN cap->>'movement'='SLIDE' THEN 'SLIDING' ELSE cap->>'movement' END;
        FOR kit_sku IN SELECT jsonb_array_elements_text(cap->'hardware_kit_skus') LOOP
            IF NOT EXISTS(SELECT 1 FROM public.hardware_kits k WHERE k.system_id=target
                AND k.org_id IS NOT DISTINCT FROM system_row.org_id AND k.sku=kit_sku AND k.is_active
                AND k.opening_type=expected_type
                AND (cap->>'leaf_role'<>'PASSIVE' OR NOT EXISTS(SELECT 1 FROM jsonb_array_elements(k.contents) c
                    WHERE c->>'category'='HANDLE'))) THEN
                RAISE EXCEPTION 'opening_capability_kit_incompatible' USING ERRCODE='23514';
            END IF;
        END LOOP;
        IF cap->>'leaf_role' IN ('ACTIVE','PASSIVE') AND NOT EXISTS(SELECT 1 FROM public.profile_articles a
            WHERE a.system_id=target AND a.org_id IS NOT DISTINCT FROM system_row.org_id AND a.role='INVERSOR') THEN
            RAISE EXCEPTION 'opening_inversor_authority_required' USING ERRCODE='23514';
        END IF;
    END LOOP;
    END LOOP;
    RETURN NULL;
END $$;
COMMIT;
