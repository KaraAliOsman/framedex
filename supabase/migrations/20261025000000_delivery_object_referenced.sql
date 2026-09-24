-- The post-rollback compensation purge runs outside any request: it opens
-- a fresh documentary_backend transaction with no JWT claims, so
-- current_user_org_ids() is empty and every org-scoped read policy hides
-- committed rows. A failed request racing a successful retry would then see
-- the retry's row as "unreferenced" and delete its object. This narrowly
-- scoped check answers exactly one question — does any committed
-- confirmation or receipt of this org reference this object key — running
-- as the definer so it sees committed rows independent of claims.
CREATE FUNCTION private.delivery_object_referenced(p_org UUID, p_key TEXT)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.delivery_confirmations
        WHERE org_id = p_org
          AND (storage_object_key = p_key OR signature_object_key = p_key)
    ) OR EXISTS (
        SELECT 1
        FROM public.payment_receipts
        WHERE org_id = p_org
          AND storage_object_key = p_key
    );
$$;
REVOKE ALL ON FUNCTION private.delivery_object_referenced(UUID, TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION private.delivery_object_referenced(UUID, TEXT) TO documentary_backend;
