-- Glass purchase authority gains its physical composition: the technical SKU
-- now carries the pane recipe the BOM weighs, so a client can no longer
-- conflate the glazing-bead slot thickness with the glass itself.
ALTER TABLE public.glass_purchase_mappings
    ADD COLUMN glass_spec VARCHAR(200) NULL;
