-- A physical remnant may be removed by privileged maintenance under the
-- existing P02 contract. Its address and immutable history must survive.
-- Reference the enduring RT alias instead of deleting or rewriting history.
ALTER TABLE public.inventory_remnant_events
  DROP CONSTRAINT inventory_remnant_events_remnant_id_fkey,
  ADD COLUMN address_kind text NOT NULL DEFAULT 'RT' CHECK (address_kind = 'RT'),
  ADD CONSTRAINT remnant_history_address FOREIGN KEY (org_id, address_kind, remnant_id)
    REFERENCES public.entity_codes(org_id, kind, entity_id);
