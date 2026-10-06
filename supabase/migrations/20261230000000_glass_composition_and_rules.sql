BEGIN;

CREATE TABLE public.catalog_glass_compositions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    system_id UUID NOT NULL REFERENCES public.profile_systems(id) ON DELETE RESTRICT,
    mapping_id UUID NOT NULL UNIQUE REFERENCES public.glass_purchase_mappings(id) ON DELETE RESTRICT,
    status TEXT NOT NULL CHECK(status IN ('PARSED','UNKNOWN')),
    product JSONB,
    legacy_spec TEXT,
    review_reason TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK((status='PARSED' AND product IS NOT NULL AND jsonb_typeof(product)='object') OR
          (status='UNKNOWN' AND product IS NULL AND length(review_reason)>0))
);

CREATE FUNCTION private.guard_glass_composition_scope() RETURNS TRIGGER
LANGUAGE plpgsql SET search_path='' AS $$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM public.glass_purchase_mappings g
        WHERE g.id=NEW.mapping_id AND g.system_id=NEW.system_id AND g.org_id IS NOT DISTINCT FROM NEW.org_id) THEN
        RAISE EXCEPTION 'glass_composition_scope_invalid' USING ERRCODE='23514';
    END IF;
    IF NEW.product IS NOT NULL AND (jsonb_typeof(NEW.product->'composition'->'layers') IS DISTINCT FROM 'array'
        OR length(btrim(coalesce(NEW.product->>'source','')))=0 OR length(btrim(coalesce(NEW.product->>'name','')))=0) THEN
        RAISE EXCEPTION 'glass_composition_invalid' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION private.guard_glass_composition_scope() FROM PUBLIC;
CREATE TRIGGER glass_composition_scope BEFORE INSERT ON public.catalog_glass_compositions
    FOR EACH ROW EXECUTE FUNCTION private.guard_glass_composition_scope();
CREATE TRIGGER immutable_evidence BEFORE UPDATE OR DELETE ON public.catalog_glass_compositions
    FOR EACH ROW EXECUTE FUNCTION private.reject_immutable_evidence();

-- The backfill reads the legacy notation, never rewrites mappings, positions,
-- commercial operations, sealed snapshots or document hashes. Anything the
-- conservative legacy grammar cannot prove is explicitly UNKNOWN.
CREATE FUNCTION private.legacy_glass_composition(spec TEXT) RETURNS JSONB
LANGUAGE plpgsql STABLE SET search_path='' AS $$
DECLARE tokens TEXT[]; panes TEXT[]; layers JSONB='[]'::JSONB; plies JSONB;
        interlayers JSONB; token TEXT; normalized TEXT;
BEGIN
    normalized=regexp_replace(btrim(coalesce(spec,'')),'^(DVH|TVH|TERMOPANEL)\s*','','i');
    normalized=regexp_replace(normalized,'\s+(float\s+)?incoloro\s*$','','i');
    normalized=replace(replace(regexp_replace(normalized,'\s+','','g'),',','.'),'/','-');
    IF normalized !~ '^\d+(\.\d+)?(\+\d+(\.\d+)?)*(-\d+(\.\d+)?-\d+(\.\d+)?(\+\d+(\.\d+)?)*)*$' THEN
        RETURN NULL;
    END IF;
    tokens=string_to_array(normalized,'-');
    FOR i IN 1..array_length(tokens,1) LOOP
        IF i%2=0 THEN
            IF tokens[i]::NUMERIC<=0 THEN RETURN NULL; END IF;
            layers=layers||jsonb_build_array(jsonb_build_object('kind','CHAMBER','width_mm',tokens[i]));
        ELSE
            panes=string_to_array(tokens[i],'+'); plies='[]'::JSONB; interlayers='[]'::JSONB;
            FOR j IN 1..array_length(panes,1) LOOP
                token=panes[j]; IF token::NUMERIC<=0 THEN RETURN NULL; END IF;
                plies=plies||jsonb_build_array(jsonb_build_object('thickness_mm',token));
                IF j>1 THEN interlayers=interlayers||'[{}]'::JSONB; END IF;
            END LOOP;
            layers=layers||jsonb_build_array(jsonb_build_object('kind','PANE','plies',plies,'interlayers',interlayers));
        END IF;
    END LOOP;
    RETURN jsonb_build_object('layers',layers);
END $$;
REVOKE ALL ON FUNCTION private.legacy_glass_composition(TEXT) FROM PUBLIC;

INSERT INTO public.catalog_glass_compositions(org_id,system_id,mapping_id,status,product,legacy_spec,review_reason)
SELECT g.org_id,g.system_id,g.id,
    CASE WHEN private.legacy_glass_composition(g.glass_spec) IS NULL THEN 'UNKNOWN' ELSE 'PARSED' END,
    CASE WHEN private.legacy_glass_composition(g.glass_spec) IS NULL THEN NULL ELSE
        jsonb_build_object('name',g.glass_spec,'composition',private.legacy_glass_composition(g.glass_spec),
            'source','Notación histórica; datos de proveedor pendientes de revisión','synthetic',s.is_demo) END,
    g.glass_spec,
    CASE WHEN private.legacy_glass_composition(g.glass_spec) IS NULL THEN 'Composición desconocida. Revisar la ficha original.'
         WHEN g.glass_spec LIKE '%+%' THEN 'Faltan espesor y densidad del PVB. Revisar la ficha original.' ELSE '' END
FROM public.glass_purchase_mappings g JOIN public.profile_systems s ON s.id=g.system_id;

ALTER TABLE public.catalog_glass_compositions ENABLE ROW LEVEL SECURITY;
CREATE POLICY glass_composition_read ON public.catalog_glass_compositions FOR SELECT
    TO authenticated,catalog_backend,pricing_backend,documentary_backend
    USING((org_id IN (SELECT private.current_user_org_ids()) OR org_id IS NULL) AND EXISTS
        (SELECT 1 FROM public.glass_purchase_mappings g WHERE g.id=mapping_id));
CREATE POLICY glass_composition_create ON public.catalog_glass_compositions FOR INSERT TO catalog_backend
    WITH CHECK(private.can_manage_catalog(org_id));
REVOKE ALL ON public.catalog_glass_compositions FROM anon,authenticated;
GRANT SELECT ON public.catalog_glass_compositions TO authenticated,catalog_backend,pricing_backend,documentary_backend;
GRANT INSERT,UPDATE(id) ON public.catalog_glass_compositions TO catalog_backend;
GRANT ALL ON public.catalog_glass_compositions TO service_role;
CREATE INDEX catalog_glass_compositions_scope ON public.catalog_glass_compositions(org_id,system_id);

-- A tenant may publish a new glass variant on a visible global series. The
-- original global mapping stays immutable and cannot be written by tenants.
CREATE POLICY glass_catalog_variant_create ON public.glass_purchase_mappings FOR INSERT TO catalog_backend
    WITH CHECK(private.can_manage_catalog(org_id) AND EXISTS(SELECT 1 FROM public.profile_systems s
        WHERE s.id=system_id AND (s.org_id=glass_purchase_mappings.org_id OR (s.org_id IS NULL AND s.is_global))));
CREATE POLICY glass_catalog_variant_read ON public.glass_purchase_mappings FOR SELECT TO catalog_backend
    USING(private.can_manage_catalog(org_id) AND EXISTS(SELECT 1 FROM public.profile_systems s
        WHERE s.id=system_id AND (s.org_id=glass_purchase_mappings.org_id OR (s.org_id IS NULL AND s.is_global))));

CREATE TABLE public.glass_safety_rule_sets (
    org_id UUID PRIMARY KEY REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    payload JSONB NOT NULL CHECK(jsonb_typeof(payload)='array' AND jsonb_array_length(payload)<=200),
    revision INTEGER NOT NULL DEFAULT 1 CHECK(revision>0)
);
CREATE TABLE public.glass_safety_rule_revisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE RESTRICT,
    actor_id UUID NOT NULL,
    revision INTEGER NOT NULL CHECK(revision>0),
    payload JSONB NOT NULL CHECK(jsonb_typeof(payload)='array'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(org_id,revision)
);
ALTER TABLE public.glass_safety_rule_sets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.glass_safety_rule_revisions ENABLE ROW LEVEL SECURITY;
CREATE POLICY glass_rule_sets_read ON public.glass_safety_rule_sets FOR SELECT
    TO authenticated,catalog_backend,pricing_backend,documentary_backend
    USING(org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY glass_rule_sets_write ON public.glass_safety_rule_sets FOR ALL TO catalog_backend
    USING(private.can_manage_catalog(org_id)) WITH CHECK(private.can_manage_catalog(org_id));
CREATE POLICY glass_rule_history_read ON public.glass_safety_rule_revisions FOR SELECT
    TO authenticated,catalog_backend USING(org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY glass_rule_history_create ON public.glass_safety_rule_revisions FOR INSERT TO catalog_backend
    WITH CHECK(private.can_manage_catalog(org_id) AND actor_id=auth.uid());
REVOKE ALL ON public.glass_safety_rule_sets,public.glass_safety_rule_revisions FROM anon,authenticated;
GRANT SELECT ON public.glass_safety_rule_sets TO authenticated,catalog_backend,pricing_backend,documentary_backend;
GRANT INSERT,UPDATE ON public.glass_safety_rule_sets TO catalog_backend;
GRANT SELECT ON public.glass_safety_rule_revisions TO authenticated,catalog_backend;
GRANT INSERT ON public.glass_safety_rule_revisions TO catalog_backend;
GRANT ALL ON public.glass_safety_rule_sets,public.glass_safety_rule_revisions TO service_role;
CREATE TRIGGER immutable_evidence BEFORE UPDATE OR DELETE ON public.glass_safety_rule_revisions
    FOR EACH ROW EXECUTE FUNCTION private.reject_immutable_evidence();

ALTER TABLE public.catalog_demo_prices DROP CONSTRAINT catalog_demo_prices_unit_check;
ALTER TABLE public.catalog_demo_prices ADD CONSTRAINT catalog_demo_prices_unit_check CHECK(unit IN ('BAR','M2','M','KIT','EA'));
INSERT INTO public.glass_purchase_mappings(id,system_id,technical_sku,purchasing_sku,manufacturer_name,purchase_unit,version,glass_spec,provenance) VALUES('ab76c047-8228-5d29-be49-7438f4b4b8a3','4dab0cb1-88a4-599c-b77a-9448e3291c8b','DEMO_60-GLASS-SAFE','DEMO_60-GLASS-SAFE','DEMO · Vidriero sintético','EA',1,'3 + 3 PVB 0,38 / 13.62 aire aluminio / 4 templado','{"source": "DEMO \u00b7 ficha sint\u00e9tica DEKOPEN D02 \u00b7 no certifica NCh 135 ni rendimiento t\u00e9rmico"}'::JSONB);
INSERT INTO public.catalog_glass_compositions(system_id,mapping_id,status,product) VALUES('4dab0cb1-88a4-599c-b77a-9448e3291c8b','ab76c047-8228-5d29-be49-7438f4b4b8a3','PARSED','{"authority_id":null,"name":"DEMO · Termopanel laminado de seguridad","composition":{"layers":[{"kind":"PANE","plies":[{"thickness_mm":"3","type":"FLOAT","color":"CLEAR","coating_face":null,"supplier_sku":null},{"thickness_mm":"3","type":"FLOAT","color":"CLEAR","coating_face":null,"supplier_sku":null}],"interlayers":[{"thickness_mm":"0.38","type":"PVB","density_kg_m3":"1070","source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"}]},{"kind":"CHAMBER","width_mm":"13.62","spacer":"ALUMINIUM","gas":"AIR","sealant":null},{"kind":"PANE","plies":[{"thickness_mm":"4","type":"TEMPERED","color":"CLEAR","coating_face":null,"supplier_sku":null}],"interlayers":[]}]},"source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico","synthetic":true,"properties":{"ug":null,"solar_factor":null,"light_transmittance":null,"safety_class":{"value":"B","source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"},"weight_kg_m2":null},"limits":{"min_width_mm":"100","max_width_mm":"3000","min_height_mm":"100","max_height_mm":"3000","max_area_m2":null,"max_aspect_ratio":"8","source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"},"billing":{"minimum_area_m2":"0.35","tempering_sku":"DEMO_60-GLASS-TEMPER","polishing_sku":"DEMO_60-GLASS-POLISH","drilling_sku":"DEMO_60-GLASS-DRILL","bars_per_m_sku":"DEMO_60-GLASS-BAR","bars_per_crossing_sku":"DEMO_60-GLASS-CROSS","source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"}}'::JSONB);
INSERT INTO public.glass_purchase_mappings(id,system_id,technical_sku,purchasing_sku,manufacturer_name,purchase_unit,version,glass_spec,provenance) VALUES('d5283d99-6e66-5e73-bea3-19fe7b4c1f5e','4dab0cb1-88a4-599c-b77a-9448e3291c8b','DEMO_60-GLASS-LOWE','DEMO_60-GLASS-LOWE','DEMO · Vidriero sintético','EA',1,'4 / 16 Ar borde cálido / 4 Low-E (c3)','{"source": "DEMO \u00b7 ficha sint\u00e9tica DEKOPEN D02 \u00b7 no certifica NCh 135 ni rendimiento t\u00e9rmico"}'::JSONB);
INSERT INTO public.catalog_glass_compositions(system_id,mapping_id,status,product) VALUES('4dab0cb1-88a4-599c-b77a-9448e3291c8b','d5283d99-6e66-5e73-bea3-19fe7b4c1f5e','PARSED','{"authority_id":null,"name":"DEMO · Termopanel Low-E","composition":{"layers":[{"kind":"PANE","plies":[{"thickness_mm":"4","type":"FLOAT","color":"CLEAR","coating_face":null,"supplier_sku":null}],"interlayers":[]},{"kind":"CHAMBER","width_mm":"16","spacer":"WARM_EDGE","gas":"ARGON","sealant":null},{"kind":"PANE","plies":[{"thickness_mm":"4","type":"LOW_E","color":"CLEAR","coating_face":3,"supplier_sku":null}],"interlayers":[]}]},"source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico","synthetic":true,"properties":{"ug":null,"solar_factor":null,"light_transmittance":null,"safety_class":null,"weight_kg_m2":null},"limits":{"min_width_mm":"100","max_width_mm":"3000","min_height_mm":"100","max_height_mm":"3000","max_area_m2":null,"max_aspect_ratio":"8","source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"},"billing":{"minimum_area_m2":"0.35","tempering_sku":"DEMO_60-GLASS-TEMPER","polishing_sku":"DEMO_60-GLASS-POLISH","drilling_sku":"DEMO_60-GLASS-DRILL","bars_per_m_sku":"DEMO_60-GLASS-BAR","bars_per_crossing_sku":"DEMO_60-GLASS-CROSS","source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"}}'::JSONB);
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('4dab0cb1-88a4-599c-b77a-9448e3291c8b','DEMO_60-GLASS-SAFE','M2',45000,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('4dab0cb1-88a4-599c-b77a-9448e3291c8b','DEMO_60-GLASS-LOWE','M2',32000,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('4dab0cb1-88a4-599c-b77a-9448e3291c8b','DEMO_60-GLASS-TEMPER','M2',6000,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('4dab0cb1-88a4-599c-b77a-9448e3291c8b','DEMO_60-GLASS-POLISH','M',2500,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('4dab0cb1-88a4-599c-b77a-9448e3291c8b','DEMO_60-GLASS-DRILL','EA',1800,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('4dab0cb1-88a4-599c-b77a-9448e3291c8b','DEMO_60-GLASS-BAR','M',3500,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('4dab0cb1-88a4-599c-b77a-9448e3291c8b','DEMO_60-GLASS-CROSS','EA',900,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.glass_purchase_mappings(id,system_id,technical_sku,purchasing_sku,manufacturer_name,purchase_unit,version,glass_spec,provenance) VALUES('c8677730-2946-5b45-8431-547347569ecc','c2882ff9-528e-53f9-a9d4-b7ad640c8aec','DEMO_70-GLASS-SAFE','DEMO_70-GLASS-SAFE','DEMO · Vidriero sintético','EA',1,'3 + 3 PVB 0,38 / 13.62 aire aluminio / 4 templado','{"source": "DEMO \u00b7 ficha sint\u00e9tica DEKOPEN D02 \u00b7 no certifica NCh 135 ni rendimiento t\u00e9rmico"}'::JSONB);
INSERT INTO public.catalog_glass_compositions(system_id,mapping_id,status,product) VALUES('c2882ff9-528e-53f9-a9d4-b7ad640c8aec','c8677730-2946-5b45-8431-547347569ecc','PARSED','{"authority_id":null,"name":"DEMO · Termopanel laminado de seguridad","composition":{"layers":[{"kind":"PANE","plies":[{"thickness_mm":"3","type":"FLOAT","color":"CLEAR","coating_face":null,"supplier_sku":null},{"thickness_mm":"3","type":"FLOAT","color":"CLEAR","coating_face":null,"supplier_sku":null}],"interlayers":[{"thickness_mm":"0.38","type":"PVB","density_kg_m3":"1070","source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"}]},{"kind":"CHAMBER","width_mm":"13.62","spacer":"ALUMINIUM","gas":"AIR","sealant":null},{"kind":"PANE","plies":[{"thickness_mm":"4","type":"TEMPERED","color":"CLEAR","coating_face":null,"supplier_sku":null}],"interlayers":[]}]},"source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico","synthetic":true,"properties":{"ug":null,"solar_factor":null,"light_transmittance":null,"safety_class":{"value":"B","source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"},"weight_kg_m2":null},"limits":{"min_width_mm":"100","max_width_mm":"3000","min_height_mm":"100","max_height_mm":"3000","max_area_m2":null,"max_aspect_ratio":"8","source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"},"billing":{"minimum_area_m2":"0.35","tempering_sku":"DEMO_70-GLASS-TEMPER","polishing_sku":"DEMO_70-GLASS-POLISH","drilling_sku":"DEMO_70-GLASS-DRILL","bars_per_m_sku":"DEMO_70-GLASS-BAR","bars_per_crossing_sku":"DEMO_70-GLASS-CROSS","source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"}}'::JSONB);
INSERT INTO public.glass_purchase_mappings(id,system_id,technical_sku,purchasing_sku,manufacturer_name,purchase_unit,version,glass_spec,provenance) VALUES('714cf3bb-3479-5186-bb17-538884015b9b','c2882ff9-528e-53f9-a9d4-b7ad640c8aec','DEMO_70-GLASS-LOWE','DEMO_70-GLASS-LOWE','DEMO · Vidriero sintético','EA',1,'4 / 16 Ar borde cálido / 4 Low-E (c3)','{"source": "DEMO \u00b7 ficha sint\u00e9tica DEKOPEN D02 \u00b7 no certifica NCh 135 ni rendimiento t\u00e9rmico"}'::JSONB);
INSERT INTO public.catalog_glass_compositions(system_id,mapping_id,status,product) VALUES('c2882ff9-528e-53f9-a9d4-b7ad640c8aec','714cf3bb-3479-5186-bb17-538884015b9b','PARSED','{"authority_id":null,"name":"DEMO · Termopanel Low-E","composition":{"layers":[{"kind":"PANE","plies":[{"thickness_mm":"4","type":"FLOAT","color":"CLEAR","coating_face":null,"supplier_sku":null}],"interlayers":[]},{"kind":"CHAMBER","width_mm":"16","spacer":"WARM_EDGE","gas":"ARGON","sealant":null},{"kind":"PANE","plies":[{"thickness_mm":"4","type":"LOW_E","color":"CLEAR","coating_face":3,"supplier_sku":null}],"interlayers":[]}]},"source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico","synthetic":true,"properties":{"ug":null,"solar_factor":null,"light_transmittance":null,"safety_class":null,"weight_kg_m2":null},"limits":{"min_width_mm":"100","max_width_mm":"3000","min_height_mm":"100","max_height_mm":"3000","max_area_m2":null,"max_aspect_ratio":"8","source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"},"billing":{"minimum_area_m2":"0.35","tempering_sku":"DEMO_70-GLASS-TEMPER","polishing_sku":"DEMO_70-GLASS-POLISH","drilling_sku":"DEMO_70-GLASS-DRILL","bars_per_m_sku":"DEMO_70-GLASS-BAR","bars_per_crossing_sku":"DEMO_70-GLASS-CROSS","source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"}}'::JSONB);
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('c2882ff9-528e-53f9-a9d4-b7ad640c8aec','DEMO_70-GLASS-SAFE','M2',45000,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('c2882ff9-528e-53f9-a9d4-b7ad640c8aec','DEMO_70-GLASS-LOWE','M2',32000,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('c2882ff9-528e-53f9-a9d4-b7ad640c8aec','DEMO_70-GLASS-TEMPER','M2',6000,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('c2882ff9-528e-53f9-a9d4-b7ad640c8aec','DEMO_70-GLASS-POLISH','M',2500,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('c2882ff9-528e-53f9-a9d4-b7ad640c8aec','DEMO_70-GLASS-DRILL','EA',1800,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('c2882ff9-528e-53f9-a9d4-b7ad640c8aec','DEMO_70-GLASS-BAR','M',3500,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('c2882ff9-528e-53f9-a9d4-b7ad640c8aec','DEMO_70-GLASS-CROSS','EA',900,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.glass_purchase_mappings(id,system_id,technical_sku,purchasing_sku,manufacturer_name,purchase_unit,version,glass_spec,provenance) VALUES('04b07c20-177d-5682-bb6b-ef8e99a1037d','579c97d2-5ceb-58a3-9be4-72f9a6d6ac11','DEMO_CORREDERA_60-GLASS-SAFE','DEMO_CORREDERA_60-GLASS-SAFE','DEMO · Vidriero sintético','EA',1,'3 + 3 PVB 0,38 / 13.62 aire aluminio / 4 templado','{"source": "DEMO \u00b7 ficha sint\u00e9tica DEKOPEN D02 \u00b7 no certifica NCh 135 ni rendimiento t\u00e9rmico"}'::JSONB);
INSERT INTO public.catalog_glass_compositions(system_id,mapping_id,status,product) VALUES('579c97d2-5ceb-58a3-9be4-72f9a6d6ac11','04b07c20-177d-5682-bb6b-ef8e99a1037d','PARSED','{"authority_id":null,"name":"DEMO · Termopanel laminado de seguridad","composition":{"layers":[{"kind":"PANE","plies":[{"thickness_mm":"3","type":"FLOAT","color":"CLEAR","coating_face":null,"supplier_sku":null},{"thickness_mm":"3","type":"FLOAT","color":"CLEAR","coating_face":null,"supplier_sku":null}],"interlayers":[{"thickness_mm":"0.38","type":"PVB","density_kg_m3":"1070","source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"}]},{"kind":"CHAMBER","width_mm":"13.62","spacer":"ALUMINIUM","gas":"AIR","sealant":null},{"kind":"PANE","plies":[{"thickness_mm":"4","type":"TEMPERED","color":"CLEAR","coating_face":null,"supplier_sku":null}],"interlayers":[]}]},"source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico","synthetic":true,"properties":{"ug":null,"solar_factor":null,"light_transmittance":null,"safety_class":{"value":"B","source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"},"weight_kg_m2":null},"limits":{"min_width_mm":"100","max_width_mm":"3000","min_height_mm":"100","max_height_mm":"3000","max_area_m2":null,"max_aspect_ratio":"8","source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"},"billing":{"minimum_area_m2":"0.35","tempering_sku":"DEMO_CORREDERA_60-GLASS-TEMPER","polishing_sku":"DEMO_CORREDERA_60-GLASS-POLISH","drilling_sku":"DEMO_CORREDERA_60-GLASS-DRILL","bars_per_m_sku":"DEMO_CORREDERA_60-GLASS-BAR","bars_per_crossing_sku":"DEMO_CORREDERA_60-GLASS-CROSS","source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"}}'::JSONB);
INSERT INTO public.glass_purchase_mappings(id,system_id,technical_sku,purchasing_sku,manufacturer_name,purchase_unit,version,glass_spec,provenance) VALUES('6caa7e99-6a11-54ec-8b69-c01547e11f32','579c97d2-5ceb-58a3-9be4-72f9a6d6ac11','DEMO_CORREDERA_60-GLASS-LOWE','DEMO_CORREDERA_60-GLASS-LOWE','DEMO · Vidriero sintético','EA',1,'4 / 16 Ar borde cálido / 4 Low-E (c3)','{"source": "DEMO \u00b7 ficha sint\u00e9tica DEKOPEN D02 \u00b7 no certifica NCh 135 ni rendimiento t\u00e9rmico"}'::JSONB);
INSERT INTO public.catalog_glass_compositions(system_id,mapping_id,status,product) VALUES('579c97d2-5ceb-58a3-9be4-72f9a6d6ac11','6caa7e99-6a11-54ec-8b69-c01547e11f32','PARSED','{"authority_id":null,"name":"DEMO · Termopanel Low-E","composition":{"layers":[{"kind":"PANE","plies":[{"thickness_mm":"4","type":"FLOAT","color":"CLEAR","coating_face":null,"supplier_sku":null}],"interlayers":[]},{"kind":"CHAMBER","width_mm":"16","spacer":"WARM_EDGE","gas":"ARGON","sealant":null},{"kind":"PANE","plies":[{"thickness_mm":"4","type":"LOW_E","color":"CLEAR","coating_face":3,"supplier_sku":null}],"interlayers":[]}]},"source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico","synthetic":true,"properties":{"ug":null,"solar_factor":null,"light_transmittance":null,"safety_class":null,"weight_kg_m2":null},"limits":{"min_width_mm":"100","max_width_mm":"3000","min_height_mm":"100","max_height_mm":"3000","max_area_m2":null,"max_aspect_ratio":"8","source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"},"billing":{"minimum_area_m2":"0.35","tempering_sku":"DEMO_CORREDERA_60-GLASS-TEMPER","polishing_sku":"DEMO_CORREDERA_60-GLASS-POLISH","drilling_sku":"DEMO_CORREDERA_60-GLASS-DRILL","bars_per_m_sku":"DEMO_CORREDERA_60-GLASS-BAR","bars_per_crossing_sku":"DEMO_CORREDERA_60-GLASS-CROSS","source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"}}'::JSONB);
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('579c97d2-5ceb-58a3-9be4-72f9a6d6ac11','DEMO_CORREDERA_60-GLASS-SAFE','M2',45000,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('579c97d2-5ceb-58a3-9be4-72f9a6d6ac11','DEMO_CORREDERA_60-GLASS-LOWE','M2',32000,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('579c97d2-5ceb-58a3-9be4-72f9a6d6ac11','DEMO_CORREDERA_60-GLASS-TEMPER','M2',6000,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('579c97d2-5ceb-58a3-9be4-72f9a6d6ac11','DEMO_CORREDERA_60-GLASS-POLISH','M',2500,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('579c97d2-5ceb-58a3-9be4-72f9a6d6ac11','DEMO_CORREDERA_60-GLASS-DRILL','EA',1800,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('579c97d2-5ceb-58a3-9be4-72f9a6d6ac11','DEMO_CORREDERA_60-GLASS-BAR','M',3500,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('579c97d2-5ceb-58a3-9be4-72f9a6d6ac11','DEMO_CORREDERA_60-GLASS-CROSS','EA',900,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.glass_purchase_mappings(id,system_id,technical_sku,purchasing_sku,manufacturer_name,purchase_unit,version,glass_spec,provenance) VALUES('2b26d47f-bbaf-562b-be6a-ede74bf48548','f2c527c8-6c8c-58b4-b617-fe34a6598fd6','DEMO_ALU_CORREDERA-GLASS-SAFE','DEMO_ALU_CORREDERA-GLASS-SAFE','DEMO · Vidriero sintético','EA',1,'3 + 3 PVB 0,38 / 13.62 aire aluminio / 4 templado','{"source": "DEMO \u00b7 ficha sint\u00e9tica DEKOPEN D02 \u00b7 no certifica NCh 135 ni rendimiento t\u00e9rmico"}'::JSONB);
INSERT INTO public.catalog_glass_compositions(system_id,mapping_id,status,product) VALUES('f2c527c8-6c8c-58b4-b617-fe34a6598fd6','2b26d47f-bbaf-562b-be6a-ede74bf48548','PARSED','{"authority_id":null,"name":"DEMO · Termopanel laminado de seguridad","composition":{"layers":[{"kind":"PANE","plies":[{"thickness_mm":"3","type":"FLOAT","color":"CLEAR","coating_face":null,"supplier_sku":null},{"thickness_mm":"3","type":"FLOAT","color":"CLEAR","coating_face":null,"supplier_sku":null}],"interlayers":[{"thickness_mm":"0.38","type":"PVB","density_kg_m3":"1070","source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"}]},{"kind":"CHAMBER","width_mm":"13.62","spacer":"ALUMINIUM","gas":"AIR","sealant":null},{"kind":"PANE","plies":[{"thickness_mm":"4","type":"TEMPERED","color":"CLEAR","coating_face":null,"supplier_sku":null}],"interlayers":[]}]},"source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico","synthetic":true,"properties":{"ug":null,"solar_factor":null,"light_transmittance":null,"safety_class":{"value":"B","source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"},"weight_kg_m2":null},"limits":{"min_width_mm":"100","max_width_mm":"3000","min_height_mm":"100","max_height_mm":"3000","max_area_m2":null,"max_aspect_ratio":"8","source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"},"billing":{"minimum_area_m2":"0.35","tempering_sku":"DEMO_ALU_CORREDERA-GLASS-TEMPER","polishing_sku":"DEMO_ALU_CORREDERA-GLASS-POLISH","drilling_sku":"DEMO_ALU_CORREDERA-GLASS-DRILL","bars_per_m_sku":"DEMO_ALU_CORREDERA-GLASS-BAR","bars_per_crossing_sku":"DEMO_ALU_CORREDERA-GLASS-CROSS","source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"}}'::JSONB);
INSERT INTO public.glass_purchase_mappings(id,system_id,technical_sku,purchasing_sku,manufacturer_name,purchase_unit,version,glass_spec,provenance) VALUES('04da25d2-a062-5d31-be4a-5597223fccf2','f2c527c8-6c8c-58b4-b617-fe34a6598fd6','DEMO_ALU_CORREDERA-GLASS-LOWE','DEMO_ALU_CORREDERA-GLASS-LOWE','DEMO · Vidriero sintético','EA',1,'4 / 16 Ar borde cálido / 4 Low-E (c3)','{"source": "DEMO \u00b7 ficha sint\u00e9tica DEKOPEN D02 \u00b7 no certifica NCh 135 ni rendimiento t\u00e9rmico"}'::JSONB);
INSERT INTO public.catalog_glass_compositions(system_id,mapping_id,status,product) VALUES('f2c527c8-6c8c-58b4-b617-fe34a6598fd6','04da25d2-a062-5d31-be4a-5597223fccf2','PARSED','{"authority_id":null,"name":"DEMO · Termopanel Low-E","composition":{"layers":[{"kind":"PANE","plies":[{"thickness_mm":"4","type":"FLOAT","color":"CLEAR","coating_face":null,"supplier_sku":null}],"interlayers":[]},{"kind":"CHAMBER","width_mm":"16","spacer":"WARM_EDGE","gas":"ARGON","sealant":null},{"kind":"PANE","plies":[{"thickness_mm":"4","type":"LOW_E","color":"CLEAR","coating_face":3,"supplier_sku":null}],"interlayers":[]}]},"source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico","synthetic":true,"properties":{"ug":null,"solar_factor":null,"light_transmittance":null,"safety_class":null,"weight_kg_m2":null},"limits":{"min_width_mm":"100","max_width_mm":"3000","min_height_mm":"100","max_height_mm":"3000","max_area_m2":null,"max_aspect_ratio":"8","source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"},"billing":{"minimum_area_m2":"0.35","tempering_sku":"DEMO_ALU_CORREDERA-GLASS-TEMPER","polishing_sku":"DEMO_ALU_CORREDERA-GLASS-POLISH","drilling_sku":"DEMO_ALU_CORREDERA-GLASS-DRILL","bars_per_m_sku":"DEMO_ALU_CORREDERA-GLASS-BAR","bars_per_crossing_sku":"DEMO_ALU_CORREDERA-GLASS-CROSS","source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"}}'::JSONB);
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('f2c527c8-6c8c-58b4-b617-fe34a6598fd6','DEMO_ALU_CORREDERA-GLASS-SAFE','M2',45000,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('f2c527c8-6c8c-58b4-b617-fe34a6598fd6','DEMO_ALU_CORREDERA-GLASS-LOWE','M2',32000,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('f2c527c8-6c8c-58b4-b617-fe34a6598fd6','DEMO_ALU_CORREDERA-GLASS-TEMPER','M2',6000,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('f2c527c8-6c8c-58b4-b617-fe34a6598fd6','DEMO_ALU_CORREDERA-GLASS-POLISH','M',2500,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('f2c527c8-6c8c-58b4-b617-fe34a6598fd6','DEMO_ALU_CORREDERA-GLASS-DRILL','EA',1800,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('f2c527c8-6c8c-58b4-b617-fe34a6598fd6','DEMO_ALU_CORREDERA-GLASS-BAR','M',3500,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('f2c527c8-6c8c-58b4-b617-fe34a6598fd6','DEMO_ALU_CORREDERA-GLASS-CROSS','EA',900,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.glass_purchase_mappings(id,system_id,technical_sku,purchasing_sku,manufacturer_name,purchase_unit,version,glass_spec,provenance) VALUES('625de8f4-b7ff-58a4-9827-b0df78b16a0a','e9ee9698-c8a5-5f2b-8cc0-fc1b6ab1a447','DEMO_ALU_PRACTICABLE-GLASS-SAFE','DEMO_ALU_PRACTICABLE-GLASS-SAFE','DEMO · Vidriero sintético','EA',1,'3 + 3 PVB 0,38 / 13.62 aire aluminio / 4 templado','{"source": "DEMO \u00b7 ficha sint\u00e9tica DEKOPEN D02 \u00b7 no certifica NCh 135 ni rendimiento t\u00e9rmico"}'::JSONB);
INSERT INTO public.catalog_glass_compositions(system_id,mapping_id,status,product) VALUES('e9ee9698-c8a5-5f2b-8cc0-fc1b6ab1a447','625de8f4-b7ff-58a4-9827-b0df78b16a0a','PARSED','{"authority_id":null,"name":"DEMO · Termopanel laminado de seguridad","composition":{"layers":[{"kind":"PANE","plies":[{"thickness_mm":"3","type":"FLOAT","color":"CLEAR","coating_face":null,"supplier_sku":null},{"thickness_mm":"3","type":"FLOAT","color":"CLEAR","coating_face":null,"supplier_sku":null}],"interlayers":[{"thickness_mm":"0.38","type":"PVB","density_kg_m3":"1070","source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"}]},{"kind":"CHAMBER","width_mm":"13.62","spacer":"ALUMINIUM","gas":"AIR","sealant":null},{"kind":"PANE","plies":[{"thickness_mm":"4","type":"TEMPERED","color":"CLEAR","coating_face":null,"supplier_sku":null}],"interlayers":[]}]},"source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico","synthetic":true,"properties":{"ug":null,"solar_factor":null,"light_transmittance":null,"safety_class":{"value":"B","source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"},"weight_kg_m2":null},"limits":{"min_width_mm":"100","max_width_mm":"3000","min_height_mm":"100","max_height_mm":"3000","max_area_m2":null,"max_aspect_ratio":"8","source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"},"billing":{"minimum_area_m2":"0.35","tempering_sku":"DEMO_ALU_PRACTICABLE-GLASS-TEMPER","polishing_sku":"DEMO_ALU_PRACTICABLE-GLASS-POLISH","drilling_sku":"DEMO_ALU_PRACTICABLE-GLASS-DRILL","bars_per_m_sku":"DEMO_ALU_PRACTICABLE-GLASS-BAR","bars_per_crossing_sku":"DEMO_ALU_PRACTICABLE-GLASS-CROSS","source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"}}'::JSONB);
INSERT INTO public.glass_purchase_mappings(id,system_id,technical_sku,purchasing_sku,manufacturer_name,purchase_unit,version,glass_spec,provenance) VALUES('4447e2c4-fdd1-53dd-be65-2d3c8a6865d4','e9ee9698-c8a5-5f2b-8cc0-fc1b6ab1a447','DEMO_ALU_PRACTICABLE-GLASS-LOWE','DEMO_ALU_PRACTICABLE-GLASS-LOWE','DEMO · Vidriero sintético','EA',1,'4 / 16 Ar borde cálido / 4 Low-E (c3)','{"source": "DEMO \u00b7 ficha sint\u00e9tica DEKOPEN D02 \u00b7 no certifica NCh 135 ni rendimiento t\u00e9rmico"}'::JSONB);
INSERT INTO public.catalog_glass_compositions(system_id,mapping_id,status,product) VALUES('e9ee9698-c8a5-5f2b-8cc0-fc1b6ab1a447','4447e2c4-fdd1-53dd-be65-2d3c8a6865d4','PARSED','{"authority_id":null,"name":"DEMO · Termopanel Low-E","composition":{"layers":[{"kind":"PANE","plies":[{"thickness_mm":"4","type":"FLOAT","color":"CLEAR","coating_face":null,"supplier_sku":null}],"interlayers":[]},{"kind":"CHAMBER","width_mm":"16","spacer":"WARM_EDGE","gas":"ARGON","sealant":null},{"kind":"PANE","plies":[{"thickness_mm":"4","type":"LOW_E","color":"CLEAR","coating_face":3,"supplier_sku":null}],"interlayers":[]}]},"source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico","synthetic":true,"properties":{"ug":null,"solar_factor":null,"light_transmittance":null,"safety_class":null,"weight_kg_m2":null},"limits":{"min_width_mm":"100","max_width_mm":"3000","min_height_mm":"100","max_height_mm":"3000","max_area_m2":null,"max_aspect_ratio":"8","source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"},"billing":{"minimum_area_m2":"0.35","tempering_sku":"DEMO_ALU_PRACTICABLE-GLASS-TEMPER","polishing_sku":"DEMO_ALU_PRACTICABLE-GLASS-POLISH","drilling_sku":"DEMO_ALU_PRACTICABLE-GLASS-DRILL","bars_per_m_sku":"DEMO_ALU_PRACTICABLE-GLASS-BAR","bars_per_crossing_sku":"DEMO_ALU_PRACTICABLE-GLASS-CROSS","source":"DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico"}}'::JSONB);
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('e9ee9698-c8a5-5f2b-8cc0-fc1b6ab1a447','DEMO_ALU_PRACTICABLE-GLASS-SAFE','M2',45000,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('e9ee9698-c8a5-5f2b-8cc0-fc1b6ab1a447','DEMO_ALU_PRACTICABLE-GLASS-LOWE','M2',32000,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('e9ee9698-c8a5-5f2b-8cc0-fc1b6ab1a447','DEMO_ALU_PRACTICABLE-GLASS-TEMPER','M2',6000,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('e9ee9698-c8a5-5f2b-8cc0-fc1b6ab1a447','DEMO_ALU_PRACTICABLE-GLASS-POLISH','M',2500,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('e9ee9698-c8a5-5f2b-8cc0-fc1b6ab1a447','DEMO_ALU_PRACTICABLE-GLASS-DRILL','EA',1800,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('e9ee9698-c8a5-5f2b-8cc0-fc1b6ab1a447','DEMO_ALU_PRACTICABLE-GLASS-BAR','M',3500,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');
INSERT INTO public.catalog_demo_prices(system_id,sku,unit,unit_cost,seed,source) VALUES('e9ee9698-c8a5-5f2b-8cc0-fc1b6ab1a447','DEMO_ALU_PRACTICABLE-GLASS-CROSS','EA',900,20261230,'DEMO · ficha sintética DEKOPEN D02 · no certifica NCh 135 ni rendimiento térmico');

CREATE OR REPLACE FUNCTION private.guard_referenced_catalog() RETURNS TRIGGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
DECLARE
    payload JSONB;
    target UUID;
    locked BOOLEAN;
BEGIN
    -- A new tenant-only SKU on a global series is additive: no existing
    -- immutable mapping or sealed recipe is superseded. Reusing a SKU or
    -- changing any existing authority still follows the original freeze gate.
    IF TG_OP='INSERT' AND TG_TABLE_NAME='glass_purchase_mappings' THEN
        PERFORM pg_advisory_xact_lock(hashtextextended(NEW.system_id::TEXT||':'||NEW.technical_sku,0));
        IF NEW.org_id IS NOT NULL AND EXISTS(SELECT 1 FROM public.profile_systems
            WHERE id=NEW.system_id AND org_id IS NULL AND is_global)
            AND NOT EXISTS(SELECT 1 FROM public.glass_purchase_mappings
                WHERE system_id=NEW.system_id AND technical_sku=NEW.technical_sku
                AND (org_id=NEW.org_id OR org_id IS NULL)) THEN
            RETURN NEW;
        END IF;
    END IF;
    IF TG_OP='DELETE' AND OLD.org_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM public.tenancy_organizations WHERE id=OLD.org_id
    ) THEN RETURN OLD; END IF;
    FOR payload IN SELECT value FROM jsonb_array_elements(
        CASE WHEN TG_OP='INSERT' THEN jsonb_build_array(to_jsonb(NEW))
             WHEN TG_OP='DELETE' THEN jsonb_build_array(to_jsonb(OLD))
             ELSE jsonb_build_array(to_jsonb(OLD),to_jsonb(NEW)) END
    ) LOOP
        -- Provenance-only edits to locked rows are audit writes, not technical
        -- edits: let review and re-labeling through, keep everything else frozen.
        -- review_pending rides the same exemption: it changes only as part of
        -- a technical edit or a review write.
        IF TG_OP='UPDATE' AND
            to_jsonb(NEW) - '{data_provenance,technical_reviewed_at,technical_reviewed_by,review_pending}'::TEXT[]
            IS NOT DISTINCT FROM
            to_jsonb(OLD) - '{data_provenance,technical_reviewed_at,technical_reviewed_by,review_pending}'::TEXT[]
        THEN CONTINUE; END IF;
        IF TG_TABLE_NAME='profile_purchase_mappings' THEN
            SELECT system_id INTO target FROM public.profile_articles
            WHERE id=(payload->>'profile_article_id')::UUID;
        ELSIF TG_TABLE_NAME='hardware_purchase_mappings' THEN
            SELECT system_id INTO target FROM public.hardware_kits
            WHERE id=(payload->>'hardware_kit_id')::UUID;
        ELSIF TG_TABLE_NAME='panel_purchase_authorities' THEN
            SELECT system_id INTO target FROM public.infill_articles
            WHERE id=(payload->>'infill_article_id')::UUID;
        ELSE
            target := (payload->>'system_id')::UUID;
        END IF;
        -- A real UPDATE creates a conflicting row version, including for unlocked
        -- catalogs: a concurrent save cannot commit calculations from an old snapshot.
        UPDATE public.profile_systems SET technical_locked=technical_locked
        WHERE id=target RETURNING technical_locked INTO locked;
        IF locked THEN
            RAISE EXCEPTION 'catalog_authority_referenced' USING ERRCODE='23514';
        END IF;
    END LOOP;
    RETURN CASE WHEN TG_OP='DELETE' THEN OLD ELSE NEW END;
END;
$$;
REVOKE ALL ON FUNCTION private.guard_referenced_catalog() FROM PUBLIC;


COMMIT;
