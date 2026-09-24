-- Catalog trust boundary: stop fabricating manufacturing data.
--
-- profile_articles shipped with invented defaults (6000mm stock length,
-- 6mm welding loss, 15mm reinforcement gap, 1.2/1.7 kg/m weights) that
-- silently materialized on INSERT when a supplier document did not carry
-- the value. Missing data must persist as UNKNOWN (NULL) so downstream
-- consumers — stock authority, weld math, weight estimation — can refuse
-- or flag instead of computing on invented numbers.
--
-- Append-only policy: ALTER COLUMN … DROP DEFAULT and DROP NOT NULL change
-- no stored value and delete nothing; rows that already carry a real value
-- keep it. (Rows written under the old defaults are indistinguishable from
-- reviewed data — their cleanup is a data-quality decision, not schema.)

BEGIN;

ALTER TABLE public.profile_articles
    ALTER COLUMN commercial_length_mm DROP DEFAULT,
    ALTER COLUMN commercial_length_mm DROP NOT NULL,
    ALTER COLUMN welding_loss_mm DROP DEFAULT,
    ALTER COLUMN welding_loss_mm DROP NOT NULL,
    ALTER COLUMN reinforcement_gap_mm DROP DEFAULT,
    ALTER COLUMN reinforcement_gap_mm DROP NOT NULL,
    ALTER COLUMN weight_kg_m DROP DEFAULT,
    ALTER COLUMN weight_kg_m DROP NOT NULL,
    ALTER COLUMN steel_weight_kg_m DROP DEFAULT,
    ALTER COLUMN steel_weight_kg_m DROP NOT NULL;

COMMIT;
