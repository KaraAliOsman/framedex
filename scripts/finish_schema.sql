-- Typed JSON schema plus cross-field constraints; NUMERIC on PostgreSQL 16/17.
CREATE FUNCTION public.finish_authority_valid(a JSONB, material TEXT, finishes JSONB) RETURNS BOOLEAN
LANGUAGE plpgsql IMMUTABLE SET search_path=pg_catalog,public AS $$
DECLARE c JSONB; f JSONB; channel TEXT; key TEXT; n NUMERIC;
BEGIN
  IF a IS NULL THEN RETURN TRUE; END IF;
  IF NOT public.hardware_schema_valid(a,'__SCHEMA__'::JSONB,'__SCHEMA__'::JSONB)
     OR a->>'material'<>material THEN RETURN FALSE; END IF;
  IF (SELECT COUNT(DISTINCT x->>'code') FROM jsonb_array_elements(a->'colors') x)<>jsonb_array_length(a->'colors')
     OR (SELECT COUNT(DISTINCT x->>'code') FROM jsonb_array_elements(a->'combinations') x)<>jsonb_array_length(a->'combinations')
     OR (SELECT COUNT(DISTINCT (x->>'interior',x->>'exterior')) FROM jsonb_array_elements(a->'combinations') x)<>jsonb_array_length(a->'combinations')
     OR jsonb_array_length(finishes)<>jsonb_array_length(a->'combinations')
     OR EXISTS(SELECT 1 FROM jsonb_array_elements(a->'combinations') x WHERE NOT finishes ? (x->>'code')) THEN RETURN FALSE; END IF;
  IF (SELECT COUNT(DISTINCT x->>'code') FROM jsonb_array_elements(COALESCE(a->'handle_colors','[]')) x)<>jsonb_array_length(COALESCE(a->'handle_colors','[]')) THEN RETURN FALSE; END IF;
  FOR c IN SELECT value FROM jsonb_array_elements(a->'colors') LOOP
    IF (material='PVC' AND c->>'kind' NOT IN ('MASS','FOIL','COEXTRUDED'))
       OR (material='ALUMINIUM' AND c->>'kind' NOT IN ('RAL','ANODIZED','WOOD_EFFECT')) THEN RETURN FALSE; END IF;
  END LOOP;
  FOR c IN SELECT value FROM jsonb_array_elements((a->'colors') || COALESCE(a->'handle_colors','[]')) LOOP
    IF EXISTS(SELECT 1 FROM jsonb_array_elements(c->'linear_rgb') channel_value WHERE jsonb_typeof(channel_value)<>'string')
       OR (c->>'gloss' IS NOT NULL AND jsonb_typeof(c->'gloss')<>'string') THEN RETURN FALSE; END IF;
    FOR channel IN SELECT jsonb_array_elements_text(c->'linear_rgb') LOOP
      n:=channel::NUMERIC; IF n<0 OR n>1 THEN RETURN FALSE; END IF;
    END LOOP;
    n:=(c->>'gloss')::NUMERIC;
    IF n<0 OR n>1 OR (c->>'texture_path') ~ '(^|/)\.\.(/|$)' THEN RETURN FALSE; END IF;
  END LOOP;
  FOR f IN SELECT value FROM jsonb_array_elements(a->'combinations') LOOP
    IF jsonb_array_length(COALESCE(a->'handle_colors','[]'))>0 AND EXISTS(SELECT 1 FROM jsonb_array_elements_text(f->'allowed_handle_colors') h WHERE NOT EXISTS(SELECT 1 FROM jsonb_array_elements(a->'handle_colors') hc WHERE hc->>'code'=h)) THEN RETURN FALSE; END IF;
    IF NOT EXISTS(SELECT 1 FROM jsonb_array_elements(a->'colors') color_entry WHERE color_entry->>'code'=f->>'interior')
       OR NOT EXISTS(SELECT 1 FROM jsonb_array_elements(a->'colors') color_entry WHERE color_entry->>'code'=f->>'exterior') THEN RETURN FALSE; END IF;
    IF material='PVC' THEN
      IF NOT EXISTS(SELECT 1 FROM jsonb_array_elements(a->'colors') color_entry WHERE color_entry->>'code'=f->>'base' AND color_entry->>'kind'='MASS')
         OR EXISTS(SELECT 1 FROM jsonb_array_elements(a->'colors') color_entry WHERE color_entry->>'code' IN (f->>'interior',f->>'exterior')
             AND color_entry->>'kind'='MASS' AND color_entry->>'code'<>f->>'base') THEN RETURN FALSE; END IF;
    ELSIF f->>'base' IS NOT NULL THEN RETURN FALSE; END IF;
    FOREACH key IN ARRAY ARRAY['max_position_width_mm','max_position_height_mm','max_leaf_width_mm','max_leaf_height_mm'] LOOP
      IF f->>key IS NOT NULL AND jsonb_typeof(f->key)<>'string' THEN RETURN FALSE; END IF;
      IF (f->>key)::NUMERIC<=0 THEN RETURN FALSE; END IF;
    END LOOP;
    IF jsonb_typeof(f->'glass_clearance_mm')<>'string' OR jsonb_typeof(f->'surcharge'->'amount')<>'string' THEN RETURN FALSE; END IF;
    IF (f->>'glass_clearance_mm')::NUMERIC<0 OR (f->'surcharge'->>'amount')::NUMERIC<0
       OR (f->'surcharge'->>'kind'='NONE' AND (f->'surcharge'->>'amount')::NUMERIC<>0) THEN RETURN FALSE; END IF;
  END LOOP;
  RETURN TRUE;
EXCEPTION WHEN OTHERS THEN RETURN FALSE;
END; $$;
ALTER TABLE public.profile_systems ADD COLUMN finish_authority JSONB;
ALTER TABLE public.profile_systems ADD CONSTRAINT finish_authority_contract
  CHECK (public.finish_authority_valid(finish_authority,material::TEXT,finishes));
GRANT SELECT(finish_authority) ON public.profile_systems TO authenticated,catalog_backend,pricing_backend,documentary_backend;
COMMENT ON COLUMN public.profile_systems.finish_authority IS
  'D05 optional sourced face/base/clearance/size/surcharge authority. NULL preserves historical math and sealed bytes.';

ALTER TABLE public.catalog_color_skus ALTER COLUMN org_id DROP NOT NULL;
ALTER TABLE public.catalog_color_skus DROP CONSTRAINT catalog_color_skus_profile_article_id_finish_key;
CREATE UNIQUE INDEX catalog_color_skus_scope_unique ON public.catalog_color_skus
  (profile_article_id,finish,COALESCE(org_id,'00000000-0000-0000-0000-000000000000'::UUID));
ALTER TABLE public.catalog_color_skus
  ADD COLUMN manufacturer_name TEXT CHECK(length(btrim(manufacturer_name))>0),
  ADD COLUMN supplier_name TEXT,
  ADD COLUMN stock_color TEXT,
  ADD COLUMN cutting_profile_id UUID REFERENCES public.cutting_profiles(id) ON DELETE RESTRICT,
  ADD COLUMN binding_version INTEGER CHECK(binding_version>0),
  ADD COLUMN purchase_unit TEXT CHECK(purchase_unit='BAR'),
  ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE public.catalog_color_skus ADD CONSTRAINT finish_stock_identity
  CHECK(stock_color IS NULL OR stock_color=finish);

CREATE OR REPLACE FUNCTION private.guard_catalog_color_sku() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path='' AS $$ BEGIN
    IF NOT EXISTS(SELECT 1 FROM public.profile_articles a JOIN public.profile_systems s ON s.id=a.system_id
        WHERE a.id=NEW.profile_article_id AND a.system_id=NEW.system_id
        AND a.org_id IS NOT DISTINCT FROM NEW.org_id AND s.org_id IS NOT DISTINCT FROM NEW.org_id
        AND s.finishes ? NEW.finish AND (NEW.org_id IS NOT NULL OR s.is_global)) THEN
        RAISE EXCEPTION 'catalog_color_scope_invalid' USING ERRCODE='23514';
    END IF;
    IF EXISTS(SELECT 1 FROM public.profile_systems WHERE id=NEW.system_id AND finish_authority IS NOT NULL)
       AND (NEW.manufacturer_name IS NULL OR NEW.stock_color IS NULL OR NEW.cutting_profile_id IS NULL
            OR NEW.binding_version IS NULL OR NEW.purchase_unit IS NULL) THEN
        RAISE EXCEPTION 'finish_stock_authority_required' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END $$;
DROP POLICY catalog_color_skus_read ON public.catalog_color_skus;
CREATE POLICY catalog_color_skus_read ON public.catalog_color_skus FOR SELECT
  TO authenticated,catalog_backend,pricing_backend,documentary_backend
  USING(org_id IN (SELECT private.current_user_org_ids()) OR
    (org_id IS NULL AND EXISTS(SELECT 1 FROM public.profile_systems s WHERE s.id=system_id AND s.is_global)));
GRANT SELECT ON public.catalog_color_skus TO pricing_backend,documentary_backend;
