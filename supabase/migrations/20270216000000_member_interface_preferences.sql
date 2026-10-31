-- P14 · How the interface looks for one person in one workshop: density,
-- text size, motion, the tab a work opens on, the side rail. Kept on
-- the server so the assistant can change it for the person (with undo) and it
-- follows them across devices. Presentation only: it never reaches a work, a
-- price, a document or another person.
BEGIN;

CREATE TABLE public.member_interface_preferences (
    org_id uuid NOT NULL REFERENCES public.tenancy_organizations(id) ON DELETE CASCADE,
    user_id uuid NOT NULL,
    preferences jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(preferences) = 'object'),
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (org_id, user_id)
);

ALTER TABLE public.member_interface_preferences ENABLE ROW LEVEL SECURITY;
CREATE POLICY member_interface_preferences_own ON public.member_interface_preferences
    FOR ALL TO authenticated
    USING (user_id = auth.uid() AND org_id IN (SELECT private.current_user_org_ids()))
    WITH CHECK (user_id = auth.uid() AND org_id IN (SELECT private.current_user_org_ids()));
REVOKE ALL ON public.member_interface_preferences FROM anon, authenticated;
GRANT SELECT, INSERT, UPDATE ON public.member_interface_preferences TO authenticated;
GRANT ALL ON public.member_interface_preferences TO service_role;

COMMIT;
