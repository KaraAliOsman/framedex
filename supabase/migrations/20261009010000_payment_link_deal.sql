-- Freeze the commercial deal on payment links.
--
-- A customer can pay a link after the project's pricing was reset (or before it
-- was ever priced). The verified settlement must still land in the ledger and
-- seal a comprobante: the link carries the deal snapshot it was created under,
-- so the receipt can always describe the trato the payer agreed to. Columns
-- stay nullable — links minted before this migration simply have no snapshot
-- and their receipts render "—" for the deal totals.

ALTER TABLE public.project_payment_links
    ADD COLUMN IF NOT EXISTS deal_total NUMERIC(14,2),
    ADD COLUMN IF NOT EXISTS deal_currency TEXT;
