-- Synthetic-system honesty: the three global reference catalogs must be named
-- as what they are — synthetic references, not manufacturer-certified series.
-- GLASS_45 in particular is aluminium-based, so its name states it rather than
-- implying true frameless glass support (also lands the Alumio -> Aluminio fix).
-- Locked catalogs are skipped: a referenced system's identity is frozen
-- authority (guard_referenced_system) — fresh and unreferenced databases get
-- the honest names; locked rows already carry the is_demo marker.
BEGIN;

UPDATE public.profile_systems
SET name = 'Sistema Demo 60mm PVC — referencia sintética'
WHERE code = 'DEMO_60' AND org_id IS NULL AND is_demo AND technical_locked IS NOT TRUE;

UPDATE public.profile_systems
SET name = 'Línea Aluminio 65 — referencia sintética'
WHERE code = 'ALU_65' AND org_id IS NULL AND is_demo AND technical_locked IS NOT TRUE;

UPDATE public.profile_systems
SET name = 'Vidrio-dominante 45 (aluminio) — referencia sintética'
WHERE code = 'GLASS_45' AND org_id IS NULL AND is_demo AND technical_locked IS NOT TRUE;

COMMIT;
