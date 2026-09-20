-- Missing manufacturing authority remains absent; confirmed inputs bind to engine identity.
ALTER TABLE public.position_documentary_inputs
    ALTER COLUMN accessory_schedule DROP NOT NULL,
    ADD COLUMN calculation_hash TEXT
        CHECK (calculation_hash ~ '^sha256:[0-9a-f]{64}$');

-- Existing unbound working inputs require reconfirmation. Immutable revision snapshots
-- remain untouched and retain their original documentary authority.
