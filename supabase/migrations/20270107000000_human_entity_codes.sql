-- Stable tenant-local addresses, separate from immutable historical snapshots.
-- In particular, never rewrite an issued PO's payload, code or hash.
CREATE TABLE public.entity_code_counters (
    org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    kind text NOT NULL CHECK (kind IN ('OC', 'RT', 'REC')),
    last_value bigint NOT NULL CHECK (last_value >= 0),
    PRIMARY KEY (org_id, kind)
);

CREATE TABLE public.entity_codes (
    org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    kind text NOT NULL CHECK (kind IN ('OC', 'RT', 'REC')),
    entity_id uuid NOT NULL,
    sequence_no bigint NOT NULL CHECK (sequence_no > 0),
    code text NOT NULL CHECK (code ~ '^(OC|RT|REC)-[0-9]{6,}$' AND split_part(code, '-', 1) = kind),
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (org_id, kind, entity_id),
    UNIQUE (org_id, code),
    UNIQUE (org_id, kind, sequence_no)
);

ALTER TABLE public.entity_code_counters ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.entity_codes ENABLE ROW LEVEL SECURITY;
CREATE POLICY entity_code_counters_tenant ON public.entity_code_counters
    USING (org_id IN (SELECT private.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT private.current_user_org_ids()));
CREATE POLICY entity_codes_tenant ON public.entity_codes
    USING (org_id IN (SELECT private.current_user_org_ids()))
    WITH CHECK (org_id IN (SELECT private.current_user_org_ids()));
REVOKE ALL ON public.entity_code_counters, public.entity_codes FROM PUBLIC, anon, authenticated, documentary_backend, pricing_backend;
GRANT SELECT ON public.entity_codes TO authenticated, documentary_backend, pricing_backend;
GRANT ALL ON public.entity_code_counters, public.entity_codes TO service_role;

-- Deterministic upgrade: equal timestamps are ordered by the stable UUID.
-- These are presentation aliases; every existing source row remains untouched.
WITH source AS (
    SELECT org_id, 'OC'::text AS kind, id AS entity_id, created_at
    FROM public.orders WHERE order_type <> 'WORKSHOP_OT'
    UNION ALL
    SELECT org_id, 'RT', id, created_at FROM public.inventory_remnants
    UNION ALL
    SELECT org_id, 'REC', id, created_at FROM public.order_receipts
), numbered AS (
    SELECT *, row_number() OVER (PARTITION BY org_id, kind ORDER BY created_at, entity_id) AS n
    FROM source
)
INSERT INTO public.entity_codes(org_id, kind, entity_id, sequence_no, code, created_at)
SELECT org_id, kind, entity_id, n,
       kind || '-' || lpad(n::text, greatest(6, length(n::text)), '0'), created_at
FROM numbered;
INSERT INTO public.entity_code_counters(org_id, kind, last_value)
SELECT org_id, kind, max(sequence_no) FROM public.entity_codes GROUP BY org_id, kind;

CREATE FUNCTION private.assign_entity_code(p_org uuid, p_kind text, p_entity uuid)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
DECLARE
    assigned text;
    n bigint;
BEGIN
    IF p_kind NOT IN ('OC', 'RT', 'REC') OR p_entity IS NULL OR p_org IS NULL THEN
        RAISE EXCEPTION 'invalid_entity_code_identity' USING ERRCODE = '22023';
    END IF;
    IF coalesce(current_setting('role', true), 'none') NOT IN ('none', 'postgres', 'service_role')
       AND NOT p_org IN (SELECT private.current_user_org_ids()) THEN
        RAISE EXCEPTION 'entity_code_org_not_visible' USING ERRCODE = '42501';
    END IF;
    INSERT INTO public.entity_code_counters(org_id, kind, last_value) VALUES (p_org, p_kind, 0)
        ON CONFLICT (org_id, kind) DO NOTHING;
    -- Lock before reading the address: concurrent retries of the same entity
    -- reuse it, and different entities serialize within this org and kind.
    SELECT last_value INTO n FROM public.entity_code_counters
        WHERE org_id = p_org AND kind = p_kind FOR UPDATE;
    SELECT code INTO assigned FROM public.entity_codes
        WHERE org_id = p_org AND kind = p_kind AND entity_id = p_entity;
    IF assigned IS NOT NULL THEN RETURN assigned; END IF;
    n := n + 1;
    assigned := p_kind || '-' || lpad(n::text, greatest(6, length(n::text)), '0');
    UPDATE public.entity_code_counters SET last_value = n WHERE org_id = p_org AND kind = p_kind;
    INSERT INTO public.entity_codes(org_id, kind, entity_id, sequence_no, code)
        VALUES (p_org, p_kind, p_entity, n, assigned);
    RETURN assigned;
END;
$$;
REVOKE ALL ON FUNCTION private.assign_entity_code(uuid, text, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.assign_entity_code(uuid, text, uuid) TO documentary_backend, service_role;

CREATE FUNCTION private.entity_code(p_org uuid, p_kind text, p_entity uuid, p_fallback text DEFAULT NULL)
RETURNS text LANGUAGE sql STABLE SET search_path = '' AS $$
    SELECT coalesce((SELECT code FROM public.entity_codes
                     WHERE org_id = p_org AND kind = p_kind AND entity_id = p_entity), p_fallback);
$$;
REVOKE ALL ON FUNCTION private.entity_code(uuid, text, uuid, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.entity_code(uuid, text, uuid, text)
    TO authenticated, documentary_backend, pricing_backend, service_role;

CREATE FUNCTION private.assign_inserted_entity_code()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
DECLARE kind text;
BEGIN
    IF TG_TABLE_NAME = 'orders' THEN
        IF NEW.order_type = 'WORKSHOP_OT' THEN RETURN NEW; END IF;
        kind := 'OC';
    ELSIF TG_TABLE_NAME = 'inventory_remnants' THEN kind := 'RT';
    ELSIF TG_TABLE_NAME = 'order_receipts' THEN kind := 'REC';
    ELSE RAISE EXCEPTION 'unsupported_entity_code_table';
    END IF;
    PERFORM private.assign_entity_code(NEW.org_id, kind, NEW.id);
    RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION private.assign_inserted_entity_code() FROM PUBLIC;
CREATE TRIGGER assign_order_entity_code AFTER INSERT ON public.orders
    FOR EACH ROW EXECUTE FUNCTION private.assign_inserted_entity_code();
CREATE TRIGGER assign_remnant_entity_code AFTER INSERT ON public.inventory_remnants
    FOR EACH ROW EXECUTE FUNCTION private.assign_inserted_entity_code();
CREATE TRIGGER assign_receipt_entity_code AFTER INSERT ON public.order_receipts
    FOR EACH ROW EXECUTE FUNCTION private.assign_inserted_entity_code();

CREATE FUNCTION private.guard_entity_code()
RETURNS trigger LANGUAGE plpgsql SET search_path = '' AS $$
BEGIN
    -- Preserve ordinary org teardown for disposable fixtures. A surviving org
    -- never loses an address even if its original entity is later removed.
    IF TG_OP = 'DELETE' AND NOT EXISTS (
        SELECT 1 FROM public.tenancy_organizations WHERE id = OLD.org_id
    ) THEN RETURN OLD; END IF;
    RAISE EXCEPTION 'entity_code_immutable' USING ERRCODE = '42501';
END;
$$;
REVOKE ALL ON FUNCTION private.guard_entity_code() FROM PUBLIC;
CREATE TRIGGER entity_code_immutable BEFORE UPDATE OR DELETE ON public.entity_codes
    FOR EACH ROW EXECUTE FUNCTION private.guard_entity_code();
